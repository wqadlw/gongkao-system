"""
艾宾浩斯复习算法引擎 v2
"""
from datetime import datetime, timedelta

REVIEW_CYCLES = [0, 1, 2, 4, 7, 15, 30, 60]

REVIEW_RESULT_IMPACT = {
    "again": -2, "hard": 0, "good": 1, "easy": 2,
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
            if q.next_review_time and q.next_review_time <= today_end:
                stats["due_today"] += 1
            else:
                stats["overdue"] += 1
        elif status == "mastered":
            stats["mastered"] += 1
    return stats
