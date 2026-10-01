"""
FSRS 参数个性化优化服务
基于用户 review_logs 训练专属 FSRS 权重（fsrs-rs-python，官方 Rust 实现的零依赖绑定）。
设计文档见 docs/dev/fsrs-optimization.md。

数据量门槛（Anki 最佳实践）：
- 长期复习条目 < MIN_LONG_TERM_ITEMS：拒绝优化
- 20 ~ 400：允许训练，结果标注"样本较少"
- >= 400：正常优化
"""
import json
from datetime import datetime

from database import ReviewLog, AppSetting

FSRS_PARAM_KEY = "fsrs_parameters"
MIN_LONG_TERM_ITEMS = 20

RATING_MAP = {"again": 1, "hard": 2, "good": 3, "easy": 4}

try:
    from fsrs_rs_python import DEFAULT_PARAMETERS, FSRS, FSRSItem, FSRSReview
    FSRS_RS_AVAILABLE = True
except ImportError:
    FSRS_RS_AVAILABLE = False


def get_fsrs_parameters(db):
    """读取个性化参数（未设置时返回 None，调度器走默认权重）"""
    row = db.query(AppSetting).filter(AppSetting.key == FSRS_PARAM_KEY).first()
    if not row or not row.value:
        return None
    try:
        params = json.loads(row.value)
        if isinstance(params, list) and len(params) == len(DEFAULT_PARAMETERS):
            return [float(p) for p in params]
    except (ValueError, TypeError):
        pass
    return None


def set_fsrs_parameters(db, params):
    row = db.query(AppSetting).filter(AppSetting.key == FSRS_PARAM_KEY).first()
    if not row:
        row = AppSetting(key=FSRS_PARAM_KEY)
        db.add(row)
    row.value = json.dumps([float(p) for p in params])
    row.update_time = datetime.now()
    db.commit()


def clear_fsrs_parameters(db):
    db.query(AppSetting).filter(AppSetting.key == FSRS_PARAM_KEY).delete()
    db.commit()


def collect_review_histories(db):
    """把 review_logs 按 (题目, 日期) 聚成每卡有序的 [(date, rating 1-4)] 历史"""
    logs = db.query(ReviewLog).order_by(ReviewLog.question_id, ReviewLog.review_time).all()
    histories = {}
    for log in logs:
        rating = RATING_MAP.get(log.review_result)
        if rating is None or not log.review_time:
            continue
        histories.setdefault(log.question_id, []).append((log.review_time.date(), rating))
    # 同一天多次复习合并为一条（取当天最后一次评分），避免 delta_t=0 重复
    merged = {}
    for qid, entries in histories.items():
        day_map = {}
        for d, rating in entries:
            day_map[d] = rating  # 后写覆盖：保留当天最后一次评分
        merged[qid] = sorted(day_map.items())
    return merged


def convert_to_fsrs_items(histories):
    """按 fsrs-rs 官方示例把每卡历史转换为 FSRSItem 序列，仅保留进入长期复习的条目"""
    items = []
    for history in histories.values():
        if len(history) < 2:
            continue
        reviews, card_items, last_date = [], [], history[0][0]
        for d, rating in history:
            reviews.append(FSRSReview(rating=rating, delta_t=(d - last_date).days))
            items.append(FSRSItem(reviews=reviews.copy()))
            last_date = d
        items = [x for x in items if x.long_term_review_cnt() > 0]
    return items


def optimize_parameters(db):
    """执行参数优化；返回结果字典（不直接抛异常，调用方直接返回给前端）"""
    if not FSRS_RS_AVAILABLE:
        return {"ok": False, "message": "未安装 fsrs-rs-python：请在后端 venv 执行 pip install fsrs-rs-python"}

    histories = collect_review_histories(db)
    review_count = sum(len(h) for h in histories.values())
    card_count = len(histories)
    items = convert_to_fsrs_items(histories)
    long_term_count = len(items)

    if long_term_count < MIN_LONG_TERM_ITEMS:
        return {
            "ok": False,
            "message": f"复习记录不足：当前长期复习条目 {long_term_count} 条，至少需要 {MIN_LONG_TERM_ITEMS} 条才能训练出可靠参数。继续正常复习即可自动积累。",
            "review_count": review_count,
            "card_count": card_count,
            "long_term_count": long_term_count,
        }

    try:
        fsrs = FSRS(parameters=list(DEFAULT_PARAMETERS))
        new_params = fsrs.compute_parameters(items)
        if len(new_params) != len(DEFAULT_PARAMETERS) or any(
            p != p or abs(p) > 1e6 for p in new_params
        ):
            raise ValueError("训练结果异常")
    except Exception as e:
        return {
            "ok": False,
            "message": f"训练失败：{e}",
            "review_count": review_count,
            "card_count": card_count,
            "long_term_count": long_term_count,
        }

    set_fsrs_parameters(db, new_params)
    sample_note = "样本较少（官方建议 400 条以上），参数仅供参考" if long_term_count < 400 else "样本充足"
    return {
        "ok": True,
        "message": f"优化完成：基于 {card_count} 张卡片的 {long_term_count} 条长期复习记录（{sample_note}）",
        "review_count": review_count,
        "card_count": card_count,
        "long_term_count": long_term_count,
        "old_parameters": list(DEFAULT_PARAMETERS),
        "new_parameters": [round(p, 4) for p in new_params],
    }
