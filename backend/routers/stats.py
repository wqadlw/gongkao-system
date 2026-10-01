"""统计分析路由 v2"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.stats_engine import (
    get_dashboard_stats, get_module_radar, get_error_distribution,
    get_trend_data, get_heatmap_data, get_mock_analysis, get_recommendation,
    get_weak_points, get_exam_countdowns
)

router = APIRouter(prefix="/api/stats", tags=["统计分析"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return get_dashboard_stats(db)


@router.get("/radar")
def radar(db: Session = Depends(get_db)):
    return get_module_radar(db)


@router.get("/error-distribution")
def error_distribution(db: Session = Depends(get_db)):
    return get_error_distribution(db)


@router.get("/trend")
def trend(days: int = 30, db: Session = Depends(get_db)):
    return get_trend_data(db, days)


@router.get("/heatmap")
def heatmap(year: int = None, db: Session = Depends(get_db)):
    return {"data": get_heatmap_data(db, year)}


@router.get("/mock-analysis")
def mock_analysis(db: Session = Depends(get_db)):
    return get_mock_analysis(db)


@router.get("/weak-points")
def weak_points(top: int = 10, db: Session = Depends(get_db)):
    return get_weak_points(db, top)


@router.get("/recommendation")
def recommendation(db: Session = Depends(get_db)):
    return get_recommendation(db)


@router.get("/exam-countdown")
def exam_countdown(db: Session = Depends(get_db)):
    """获取公考倒计时"""
    return get_exam_countdowns(db)


@router.get("/all")
def all_stats(db: Session = Depends(get_db)):
    # 扁平化：聚合端点直接返回数组，供前端可视化大屏按数组消费
    # 题目全量只查一次，各统计函数复用，避免重复加载整表
    from database import Question
    questions = db.query(Question).all()
    return {
        "dashboard": get_dashboard_stats(db, questions),
        "radar": get_module_radar(db, questions).get("radar", []),
        "error_distribution": get_error_distribution(db, questions).get("distribution", []),
        "trend": get_trend_data(db, 30).get("trend", []),
        "heatmap": get_heatmap_data(db, questions=questions),
        "mock_analysis": get_mock_analysis(db),
        "weak_points": get_weak_points(db, 10, questions),
        "recommendation": get_recommendation(db),
        "exam_countdown": get_exam_countdowns(db),
    }
