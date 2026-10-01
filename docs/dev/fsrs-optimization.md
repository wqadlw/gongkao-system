# 设计文档：FSRS 参数个性化优化

状态：已实现 | 日期：2026-10-01

## 背景

系统自 v2.1 起 FSRS 调度使用官方默认权重（py-fsrs 的 DEFAULT_PARAMETERS，21 个参数）。
默认权重来自 Anki 社区海量数据的平均拟合，对个人未必最优。用户的 `review_logs` 表
持续积累真实复习记录（题目、时间、评分、耗时），恰好是参数优化的训练数据。
Roadmap 第 3 条"FSRS 参数按个人复习记录优化"即为此设计。

## 选型

| 候选 | 结论 |
|------|------|
| [fsrs-optimizer](https://github.com/open-spaced-repetition/fsrs-optimizer)（PyPI 官方 Python 包，⭐112） | ❌ 依赖 torch + pandas>=3.0 + scikit-learn + statsmodels + matplotlib，安装体积 GB 级，对本地方单机应用过重 |
| **[fsrs-rs-python](https://github.com/open-spaced-repetition/fsrs-rs-python)**（官方 Rust 实现的 Python 绑定，⭐37） | ✅ **零依赖**（Rust + burn-rs，手写梯度代替 PyTorch），`pip install fsrs-rs-python` 即用，训练速度快，API 与 fsrs-optimizer 等价 |
| 自研参数拟合 | ❌ 复现 FSRS 训练算法成本过高 |

**决策**：采用 `fsrs-rs-python`。这是官方推荐路径（fsrs-rs 即 Anki 新版内置的 Rust FSRS），
Anki 的最佳实践同样是将复习日志转换为 FSRSItem 序列后交给优化器训练。

## 数据契约

fsrs-rs-python 训练输入（来自官方 examples/optimize.py）：

```python
from fsrs_rs_python import DEFAULT_PARAMETERS, FSRS, FSRSItem, FSRSReview

# 每张卡：按时间排序的 [(date, rating 1-4), ...]，首条复习 delta_t=0
def convert_to_fsrs_item(history):
    reviews, items = [], []
    last_date = history[0][0]
    for date_, rating in history:
        delta_t = (date_ - last_date).days
        reviews.append(FSRSReview(rating=rating, delta_t=delta_t))
        items.append(FSRSItem(reviews=reviews.copy()))
        last_date = date_
    return [x for x in items if x.long_term_review_cnt() > 0]  # 仅保留进入长期复习的条目

fsrs = FSRS(parameters=DEFAULT_PARAMETERS)
optimized = fsrs.compute_parameters(fsrs_items)
```

本项目数据映射：

- `ReviewLog.question_id` → 卡片 ID（同一题=同一卡）
- `ReviewLog.review_time` → 日期（取 date()，天然本地时区）
- `ReviewLog.review_result` → rating：again=1 / hard=2 / good=3 / easy=4
- 每题按 review_time 升序组成复习历史；delta_t = 相邻两次复习的日期差天数

## 数据量门槛

Anki 的最佳实践：复习日志不足（官方建议 400 条复习）时优化结果不可靠。
fsrs-rs 对极小数据集会训练失败或返回不可用参数。策略：

- 长期复习条目（long_term_review_cnt>0 的 FSRSItem 数）**< 20**：拒绝优化，返回明确提示。
- 20 ~ 400：允许训练，但结果标注"样本较少，仅供参考"。
- ≥ 400：正常优化。

## 接口设计

- `POST /api/review/optimize`
  - 无请求体。
  - 返回：`{ok, message, review_count, card_count, long_term_count, old_parameters, new_parameters}`
  - 优化成功时把新参数写入 `app_settings` 表（key=`fsrs_parameters`，JSON 数组）。
- `GET /api/review/engine`：增加 `custom_parameters: bool` 字段，指示是否启用了个性化参数。
- 调度时：`review.py` 读出参数传给 `schedule_fsrs(parameters=...)` → `Scheduler(parameters=...)`。
- 参数可被反复覆盖；重新优化即更新。提供"恢复默认"能力：删除 `app_settings` 中该键即可（暂不做 UI，留接口语义）。

## 表结构

新增 `app_settings` 表（create_all 自动建表，避免 ALTER）：

| 列 | 类型 | 说明 |
|----|------|------|
| id | Integer PK | |
| key | String(100) 唯一 | 如 `fsrs_parameters` |
| value | Text | JSON 序列化的参数数组（21 个 float） |
| update_time | DateTime | |

## 验证方案

1. 单元级：构造多张合成卡的复习历史 → optimize → 参数应为 21 个有限浮点数。
2. 集成级：真实 review_logs（当前仅个位数条）→ 应返回"记录不足"提示。
3. 调度回归：设置参数后提交复习，engine 接口 `custom_parameters=true`，调度结果与之前一致可比较。
