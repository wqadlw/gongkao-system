"""分类管理路由 v2"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, Category

router = APIRouter(prefix="/api/categories", tags=["分类管理"])


@router.get("/tree")
def get_category_tree(db: Session = Depends(get_db)):
    cats = db.query(Category).order_by(Category.sort, Category.id).all()
    return build_tree(cats, 0)


def build_tree(cats, parent_id):
    tree = []
    for c in cats:
        if c.parent_id == parent_id:
            node = {
                "id": c.id, "level": c.level, "name": c.name, "parent_id": c.parent_id,
                "level1": c.level1, "level2": c.level2, "level3": c.level3,
                "level4": c.level4, "level5": c.level5,
                "module": c.module, "question_count": c.question_count, "error_count": c.error_count,
                "children": build_tree(cats, c.id)
            }
            tree.append(node)
    return tree


@router.get("/list")
def get_category_list(db: Session = Depends(get_db)):
    cats = db.query(Category).order_by(Category.sort, Category.id).all()
    return [{
        "id": c.id, "level": c.level, "name": c.name, "parent_id": c.parent_id,
        "level1": c.level1, "level2": c.level2, "level3": c.level3,
        "level4": c.level4, "level5": c.level5,
        "module": c.module,
    } for c in cats]


@router.get("/modules")
def get_modules(db: Session = Depends(get_db)):
    """获取六大模块及其下二级考点（用于快速选择）"""
    modules = {}
    cats = db.query(Category).filter(Category.level == 2).order_by(Category.sort).all()
    for c in cats:
        if c.level1 not in modules:
            modules[c.level1] = {"name": c.level1, "level3_list": []}
        modules[c.level1]["level3_list"].append({"id": c.id, "name": c.name})
    return list(modules.values())


@router.get("/node/{node_id}")
def get_category_node(node_id: int, db: Session = Depends(get_db)):
    """获取单个分类节点（含完整路径），供前端按题型树节点过滤题目"""
    c = db.query(Category).filter(Category.id == node_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="节点不存在")
    return {
        "id": c.id, "level": c.level, "name": c.name, "parent_id": c.parent_id,
        "level1": c.level1, "level2": c.level2, "level3": c.level3,
        "level4": c.level4, "level5": c.level5, "module": c.module,
        "question_count": c.question_count, "error_count": c.error_count,
    }
