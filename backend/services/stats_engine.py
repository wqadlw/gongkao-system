"""
统计引擎 v2
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import Question, MockExam, DailyStat, ReviewLog, Category, Note, ExamCountdown


def get_dashboard_stats(db: Session) -> dict:
    questions = db.query(Question).all()
    modules = {
        "政治理论": {"total": 0, "error": 0, "mastered": 0},
        "常识判断": {"total": 0, "error": 0, "mastered": 0},
        "言语理解与表达": {"total": 0, "error": 0, "mastered": 0},
        "数量关系": {"total": 0, "error": 0, "mastered": 0},
        "判断推理": {"total": 0, "error": 0, "mastered": 0},
        "资料分析": {"total": 0, "error": 0, "mastered": 0},
    }
    for q in questions:
        module = q.level1 or "其他"
        if module in modules:
            modules[module]["total"] += 1
            if q.is_error:
                modules[module]["error"] += 1
            if q.master_level >= 4:
                modules[module]["mastered"] += 1

    now = datetime.now()
    today_end = now.replace(hour=23, minute=59, second=59)
    due_today = sum(1 for q in questions if q.next_review_time and q.next_review_time <= today_end and q.review_count > 0)
    seven_days_ago = now - timedelta(days=7)
    recent_new = sum(1 for q in questions if q.create_time and q.create_time >= seven_days_ago)
    weak_points = get_weak_points(db, top=5)
    total_errors = sum(1 for q in questions if q.is_error)
    total_mastered = sum(1 for q in questions if q.master_level >= 4)
    avg_mastery = sum(q.master_level for q in questions) / len(questions) if questions else 0

    return {
        "total_questions": len(questions),
        "total_errors": total_errors,
        "total_mastered": total_mastered,
        "due_today": due_today,
        "recent_new": recent_new,
        "avg_mastery": round(avg_mastery, 1),
        "modules": modules,
        "weak_points": weak_points,
    }


def get_module_radar(db: Session) -> dict:
    questions = db.query(Question).all()
    modules = ["政治理论", "常识判断", "言语理解与表达", "数量关系", "判断推理", "资料分析"]
    radar_data = []
    for m in modules:
        m_questions = [q for q in questions if q.level1 == m]
        if m_questions:
            mastery = sum(q.master_level for q in m_questions) / len(m_questions)
            error_rate = sum(1 for q in m_questions if q.is_error) / len(m_questions)
            score = (mastery / 5) * 60 + (1 - error_rate) * 40
        else:
            score = 0
        radar_data.append({"module": m.replace("言语理解与表达", "言语").replace("数量关系", "数量"), "score": round(score, 1)})
    return {"radar": radar_data}


def get_error_distribution(db: Session) -> dict:
    questions = db.query(Question).filter(Question.is_error == True).all()
    dist = {}
    for q in questions:
        key = q.level3 or q.level1 or "未分类"
        dist[key] = dist.get(key, 0) + 1
    return {"distribution": [{"name": k, "value": v} for k, v in sorted(dist.items(), key=lambda x: -x[1])]}


def get_trend_data(db: Session, days: int = 30) -> dict:
    now = datetime.now()
    start = now - timedelta(days=days)
    questions = db.query(Question).filter(Question.create_time >= start).all()
    trend = []
    for i in range(days):
        date = start + timedelta(days=i)
        date_str = date.strftime("%m-%d")
        count = sum(1 for q in questions if q.create_time and q.create_time.date() == date.date())
        trend.append({"date": date_str, "count": count})
    return {"trend": trend}


def get_heatmap_data(db: Session, year: int = None) -> list:
    if year is None:
        year = datetime.now().year
    questions = db.query(Question).all()
    stats = db.query(DailyStat).all()

    date_count = {}
    for q in questions:
        if q.create_time and q.create_time.year == year:
            d = q.create_time.strftime("%Y-%m-%d")
            date_count[d] = date_count.get(d, 0) + 1

    return [{"date": k, "count": v} for k, v in date_count.items()]


def get_weak_points(db: Session, top: int = 10) -> list:
    questions = db.query(Question).all()
    point_stats = {}
    for q in questions:
        if q.level3 and q.level4:
            key = f"{q.level3}/{q.level4}"
            if key not in point_stats:
                point_stats[key] = {"level3": q.level3, "level4": q.level4, "total": 0, "error": 0, "mastery_sum": 0}
            point_stats[key]["total"] += 1
            if q.is_error:
                point_stats[key]["error"] += 1
            point_stats[key]["mastery_sum"] += q.master_level

    weak = []
    for key, s in point_stats.items():
        if s["total"] >= 1:
            avg_mastery = s["mastery_sum"] / s["total"]
            error_rate = s["error"] / s["total"]
            weak_score = error_rate * 50 + (5 - avg_mastery) * 10
            weak.append({
                "level3": s["level3"], "level4": s["level4"],
                "total": s["total"], "error": s["error"],
                "avg_mastery": round(avg_mastery, 1),
                "weak_score": round(weak_score, 1),
            })

    weak.sort(key=lambda x: -x["weak_score"])
    return weak[:top]


def get_mock_analysis(db: Session) -> dict:
    mocks = db.query(MockExam).order_by(MockExam.mock_date.desc()).all()
    if not mocks:
        return {"total_mocks": 0, "avg_score": 0, "trend": [], "module_avg": {}}
    total_score = sum(m.total_score for m in mocks)
    avg_score = total_score / len(mocks)
    trend = []
    for m in reversed(mocks):
        trend.append({"name": m.name, "date": m.mock_date.strftime("%Y-%m-%d") if m.mock_date else "", "total_score": m.total_score})
    module_avg = {
        "政治理论": sum(m.score_politics for m in mocks) / len(mocks),
        "常识": sum(m.score_common for m in mocks) / len(mocks),
        "言语": sum(m.score_verbal for m in mocks) / len(mocks),
        "数量": sum(m.score_quant for m in mocks) / len(mocks),
        "判断": sum(m.score_logic for m in mocks) / len(mocks),
        "资料": sum(m.score_data for m in mocks) / len(mocks),
    }
    return {"total_mocks": len(mocks), "avg_score": round(avg_score, 1), "trend": trend, "module_avg": {k: round(v, 1) for k, v in module_avg.items()}}


def update_daily_stat(db: Session, stat_type: str, count: int = 1):
    today = datetime.now().strftime("%Y-%m-%d")
    stat = db.query(DailyStat).filter(DailyStat.stat_date == today).first()
    if not stat:
        stat = DailyStat(stat_date=today, new_count=0, review_count=0, error_count=0, study_time=0, mock_count=0)
        db.add(stat)
    if stat_type == "new":
        stat.new_count += count
    elif stat_type == "review":
        stat.review_count += count
    elif stat_type == "error":
        stat.error_count += count
    elif stat_type == "mock":
        stat.mock_count += count
    db.commit()


def get_recommendation(db: Session) -> list:
    weak_points = get_weak_points(db, top=3)
    recommendations = []
    for wp in weak_points:
        if wp["total"] < 3:
            recommendations.append({"type": "practice", "level3": wp["level3"], "level4": wp["level4"], "message": f"考点【{wp['level3']}/{wp['level4']}】题目较少，建议补充练习", "priority": "high"})
        elif wp["avg_mastery"] < 2.5:
            recommendations.append({"type": "review", "level3": wp["level3"], "level4": wp["level4"], "message": f"考点【{wp['level3']}/{wp['level4']}】掌握度偏低({wp['avg_mastery']}/5)，建议重点复习", "priority": "high"})
        elif wp["error"] > 0:
            recommendations.append({"type": "error_review", "level3": wp["level3"], "level4": wp["level4"], "message": f"考点【{wp['level3']}/{wp['level4']}】有{wp['error']}道错题，建议复盘", "priority": "medium"})
    return recommendations[:5]


def get_exam_countdowns(db: Session) -> list:
    """获取考试倒计时列表"""
    now = datetime.now()
    exams = db.query(ExamCountdown).filter(ExamCountdown.is_active == True).all()
    result = []
    for e in exams:
        days_left = (e.exam_date - now).days if e.exam_date else 0
        result.append({
            "id": e.id, "name": e.name, "exam_type": e.exam_type,
            "exam_date": e.exam_date.strftime("%Y-%m-%d") if e.exam_date else "",
            "days_left": days_left,
            "remark": e.remark,
            "is_passed": days_left < 0,
        })
    result.sort(key=lambda x: x["days_left"])
    return result
