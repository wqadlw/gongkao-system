"""
复习算法引擎 v3：FSRS（Free Spaced Repetition Scheduler）优先，艾宾浩斯固定周期兜底
FSRS 基于 DSR 记忆模型（难度/稳定性/可提取性），按每题记忆状态动态安排复习时间
"""
import json
from datetime import datetime, timedelta, timezone

REVIEW_CYCLES = [0, 1, 2, 4, 7, 15, 30, 60]

REVIEW_RESULT_IMPACT = {
    "again": -2, "hard": 0, "good": 1, "easy": 2,
}

# ===== FSRS 接入（pip install fsrs），不可用时自动回退固定周期 =====
try:
    from fsrs import Scheduler, Card, Rating
    FSRS_AVAILABLE = True
except ImportError:
    FSRS_AVAILABLE = False

FSRS_RATING_MAP = {"again": "Again", "hard": "Hard", "good": "Good", "easy": "Easy"}

DEFAULT_RETENTION = 0.9


def get_scheduler(desired_retention: float = DEFAULT_RETENTION, parameters=None):
    """学习期步长 1/10 分钟，再学习 10 分钟；阶段内短间隔，毕业后进入 FSRS 长间隔调度

    parameters 传入个性化权重（None 时用库内默认值）
    """
    kwargs = {}
    if parameters:
        kwargs["parameters"] = list(parameters)
    return Scheduler(
        desired_retention=desired_retention,
        learning_steps=(timedelta(minutes=1), timedelta(minutes=10)),
        relearning_steps=(timedelta(minutes=10),),
        **kwargs,
    )


def schedule_fsrs(card_dict: dict | None, result: str, desired_retention: float = DEFAULT_RETENTION,
                  cost_time: int = 0, parameters=None):
    """对单张 FSRS 卡执行一次复习调度

    card_dict 为 None 表示首次复习（新建卡片）。
    返回 (new_card_dict, due_local_naive, interval_days)
    """
    rating = getattr(Rating, FSRS_RATING_MAP.get(result, "Good"))
    scheduler = get_scheduler(desired_retention, parameters)
    card = Card.from_dict(card_dict) if card_dict else Card()
    # py-fsrs 要求 review_datetime 为 UTC 时区感知时间
    new_card, _ = scheduler.review_card(card, rating, review_datetime=datetime.now(timezone.utc), review_duration=cost_time or None)

    due = new_card.due
    due_local = due.astimezone().replace(tzinfo=None) if due.tzinfo else due
    interval_days = max(0.0, (due_local - datetime.now()).total_seconds() / 86400)
    return new_card.to_dict(), due_local, interval_days


def fsrs_card_summary(card_dict: dict) -> dict:
    """提炼卡片记忆状态供前端展示"""
    if not card_dict:
        return {}
    return {
        "stability": round(card_dict.get("stability") or 0, 2),
        "difficulty": round(card_dict.get("difficulty") or 0, 2),
        "reps": card_dict.get("reps") or 0,
        "lapses": card_dict.get("lapses") or 0,
    }


def calculate_next_review(review_count: int, master_level: int, last_result: str = "good") -> dict:
    base_index = min(review_count, len(REVIEW_CYCLES) - 1)

    if last_result == "again":
        cycle_index = 0
        next_count = review_count
    elif last_result == "hard":
        cycle_index = max(0, base_index - 1)
        next_count = review_count + 1
    elif last_result == "easy" and master_level >= 4:
        cycle_index = min(base_index + 2, len(REVIEW_CYCLES) - 1)
        next_count = review_count + 1
    else:
        cycle_index = min(base_index + 1, len(REVIEW_CYCLES) - 1)
        next_count = review_count + 1

    mastery_bonus = (master_level - 1) * 0.2
    base_days = REVIEW_CYCLES[cycle_index]
    actual_days = int(base_days * (1 + mastery_bonus))
    next_time = datetime.now() + timedelta(days=actual_days)

    return {
        "next_review_time": next_time,
        "review_count": next_count,
        "review_cycle": actual_days,
        "days_until_next": actual_days,
    }


def update_master_level(current_level: int, result: str) -> int:
    impact = REVIEW_RESULT_IMPACT.get(result, 0)
    new_level = max(1, min(5, current_level + impact))
    return new_level


def get_review_status(question) -> str:
    if question.review_count == 0:
        return "new"
    if question.master_level >= 5 and question.review_count >= 5:
        return "mastered"
    now = datetime.now()
    if question.next_review_time and question.next_review_time <= now:
        return "due"
    return "learning"


def calculate_review_stats(questions: list) -> dict:
    now = datetime.now()
    today_end = now.replace(hour=23, minute=59, second=59)
    stats = {"total": len(questions), "new": 0, "learning": 0, "due_today": 0, "overdue": 0, "mastered": 0}
    for q in questions:
        status = get_review_status(q)
        if status == "new":
            stats["new"] += 1
        elif status == "learning":
            stats["learning"] += 1
        elif status == "due":
            # 到期但早于今天 0 点的算"逾期"，其余算"今日到期"
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if q.next_review_time and q.next_review_time < today_start:
                stats["overdue"] += 1
            else:
                stats["due_today"] += 1
        elif status == "mastered":
            stats["mastered"] += 1
    return stats
