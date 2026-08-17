"""
数据库模型 v2 - 新增结构化字段，支持JSON解析
纯本地SQLite单文件存储，零联网
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Text, String, Boolean, DateTime, Float, text
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "gongkao.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== 表1：题库分类表（五级树形结构，无"全部"节点） ==========
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, default=1)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, default=0)
    level1 = Column(String(200), default="")
    level2 = Column(String(200), default="")
    level3 = Column(String(200), default="")
    level4 = Column(String(200), default="")
    level5 = Column(String(200), default="")
    sort = Column(Integer, default=0)
    question_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    module = Column(String(50), default="")


# ========== 表2：提示词模板表 ==========
class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(50), default="")
    tag = Column(String(100), default="")
    content = Column(Text, default="")
    is_default = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    remark = Column(Text, default="")
    create_time = Column(DateTime, default=datetime.now)


# ========== 表3：题目母题库（v2新增结构化字段） ==========
class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    create_time = Column(DateTime, default=datetime.now)
    first_study_time = Column(DateTime, default=datetime.now)

    # 五级考点
    level1 = Column(String(200), default="")
    level2 = Column(String(200), default="")
    level3 = Column(String(200), default="")
    level4 = Column(String(200), default="")
    level5 = Column(String(200), default="")

    # 题目基本信息
    question_raw = Column(Text, default="")
    source = Column(String(200), default="")
    difficulty = Column(Integer, default=3)
    priority = Column(Integer, default=2)
    cost_time = Column(Integer, default=60)

    # v2新增：AI结构化字段（对应提示词JSON）
    sub_point = Column(Text, default="")           # 细分考点
    exam_intent = Column(Text, default="")          # 考察意图
    difficulty_label = Column(String(50), default="")  # 难度标签
    exam_priority = Column(String(50), default="")  # 考场优先级
    suggested_time = Column(Integer, default=60)    # 建议耗时
    option_feature = Column(Text, default="")       # 选项特征

    # 解题思路与避坑
    break_logic = Column(Text, default="")          # 破题逻辑链
    trap_read = Column(Text, default="")            # 读题陷阱
    trap_calc = Column(Text, default="")            # 计算陷阱
    trap_thought = Column(Text, default="")         # 思维误区
    error_path = Column(Text, default="")           # 常见错误路径

    # 通用技巧与速算
    normal_solve = Column(Text, default="")         # 常规通用解法
    quick_solve = Column(Text, default="")          # 速算/秒杀技巧
    identify_signal = Column(Text, default="")      # 题型识别信号

    # 详细步骤与练习
    step_detail = Column(Text, default="")          # 详细解题步骤
    practice_question = Column(Text, default="")    # 巩固练习题
    practice_answer = Column(Text, default="")      # 练习答案
    answer = Column(String(50), default="")         # 正确答案
    background_knowledge = Column(Text, default="") # 思维模型和知识背景（提示词第六节）

    # 卡片缩略信息（提示词第八节生成，供题目列表卡片精简展示，不写整题/完整路径）
    card_title = Column(String(200), default="")    # 卡片标题：AI 一句话概括本题（如「科举制度·朝代对应」）
    card_tags = Column(Text, default="")            # 考点短标签：｜分隔 1~3 个（如「科举制度｜历史常识」）
    card_summary = Column(Text, default="")         # 卡片摘要：2~3 句，复习时快速回忆（含关键结论）

    # 学习状态
    master_level = Column(Integer, default=1)
    is_error = Column(Boolean, default=False)
    error_reason = Column(String(50), default="")       # 错因标记：计算错误/概念模糊/粗心大意/方法不当
    tags = Column(Text, default="")
    stage_id = Column(Integer, default=0)
    mock_id = Column(Integer, default=0)

    # AI原始内容
    ai_raw_content = Column(Text, default="")

    # 沉淀状态：是否已将本题 AI 解析的候选条目核对并入库（解析沉淀独立页使用）
    deposited = Column(Boolean, default=False)

    # 复习管理
    review_cycle = Column(Integer, default=0)
    next_review_time = Column(DateTime, default=datetime.now)
    review_count = Column(Integer, default=0)
    review_status = Column(String(50), default="new")

    # 三态标记
    question_type_tag = Column(String(50), default="")  # 母题/错题/普通
    speed_status = Column(String(50), default="")       # 快/慢/正常
    error_reason = Column(String(200), default="")      # 错误原因
    thinking_proficiency = Column(Integer, default=1)   # 思维熟练度
    is_favorite = Column(Boolean, default=False)        # 收藏标记


# ========== 表X：行测知识库（模块→知识点；与提示词/题目耦合） ==========
class Knowledge(Base):
    __tablename__ = "knowledge"
    id = Column(Integer, primary_key=True, index=True)
    module = Column(String(200), default="", index=True)   # 关联模块（= 提示词 type）
    kg_type = Column(String(50), default="概念")            # 概念/公式/技巧/陷阱/易混点/方法/背景
    title = Column(String(300), default="")
    content = Column(Text, default="")                       # Markdown 正文
    tags = Column(Text, default="")
    related_prompt = Column(String(200), default="")         # 关联提示词（模块名）
    source = Column(String(200), default="")
    difficulty = Column(Integer, default=2)
    # 考点定位（= 题目考点路径，使知识点落到题库「对应位置」，支持按考点检索/分组）
    level1 = Column(String(200), default="")
    level2 = Column(String(200), default="")
    level3 = Column(String(200), default="")
    level4 = Column(String(200), default="")
    level5 = Column(String(200), default="")
    source_question_id = Column(Integer, default=0)          # 来源题目 ID（可追溯）
    # 卡片缩略信息（提示词 §7 每条附带，供知识库列表卡片精简展示）
    card_title = Column(String(200), default="")
    card_tags = Column(Text, default="")
    card_summary = Column(Text, default="")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now)


# ========== 表X：行测解题库（解题思路/技巧/方法模板/易错提醒，按模块归类） ==========
class SolveItem(Base):
    __tablename__ = "solve_items"
    id = Column(Integer, primary_key=True, index=True)
    module = Column(String(200), default="", index=True)       # 关联模块
    solve_type = Column(String(50), default="解题方法")         # 破题逻辑/易错提醒/解题方法/速算技巧/题型识别
    title = Column(String(300), default="")
    content = Column(Text, default="")                           # Markdown 正文
    tags = Column(Text, default="")
    source_question_id = Column(Integer, default=0)              # 来源题目ID
    source = Column(String(200), default="")                     # AI解析沉淀/手动录入/批量导入
    difficulty = Column(Integer, default=2)
    # 适用考点定位（= 题目考点路径，使解题条目落到题库「对应位置」）
    level1 = Column(String(200), default="")
    level2 = Column(String(200), default="")
    level3 = Column(String(200), default="")
    level4 = Column(String(200), default="")
    level5 = Column(String(200), default="")
    # 卡片缩略信息（提示词 §7 每条附带，供解题库列表卡片精简展示）
    card_title = Column(String(200), default="")
    card_tags = Column(Text, default="")
    card_summary = Column(Text, default="")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now)


# ========== 表4：考点笔记表（v2支持结构化笔记） ==========
class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, default=0)
    level1 = Column(String(200), default="")
    level2 = Column(String(200), default="")
    level3 = Column(String(200), default="")
    level4 = Column(String(200), default="")
    level5 = Column(String(200), default="")
    note_content = Column(Text, default="")
    # v2新增：结构化笔记字段
    question_display = Column(Text, default="")
    question_stem = Column(Text, default="")  # 仅题干（去掉选项与答案），卡片区用 markdown 渲染
    type_judgment = Column(Text, default="")
    knowledge_points = Column(Text, default="")
    logic_chain = Column(Text, default="")
    solve_steps = Column(Text, default="")
    pitfalls = Column(Text, default="")
    speed_tips = Column(Text, default="")
    # 卡片缩略信息（列表卡片精简展示；一键生成笔记时由系统派生或 AI 附带）
    card_title = Column(String(200), default="")
    card_tags = Column(Text, default="")
    card_summary = Column(Text, default="")
    create_time = Column(DateTime, default=datetime.now)
    is_collect = Column(Boolean, default=False)


# ========== 表5：备考阶段 & 模考记录表 ==========
class StudyStage(Base):
    __tablename__ = "study_stages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    goal = Column(Text, default="")
    daily_target = Column(Integer, default=20)
    is_active = Column(Boolean, default=False)
    remark = Column(Text, default="")
    create_time = Column(DateTime, default=datetime.now)


class MockExam(Base):
    __tablename__ = "mock_exams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    mock_date = Column(DateTime)
    total_score = Column(Float, default=0)
    score_politics = Column(Float, default=0)
    score_common = Column(Float, default=0)
    score_verbal = Column(Float, default=0)
    score_quant = Column(Float, default=0)
    score_logic = Column(Float, default=0)
    score_data = Column(Float, default=0)
    loss_knowledge = Column(Float, default=0)
    loss_skill = Column(Float, default=0)
    loss_careless = Column(Float, default=0)
    loss_time = Column(Float, default=0)
    remark = Column(Text, default="")
    create_time = Column(DateTime, default=datetime.now)


# ========== 表6：复习记录 & 每日统计 ==========
class ReviewLog(Base):
    __tablename__ = "review_logs"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer)
    review_time = Column(DateTime, default=datetime.now)
    review_result = Column(String(50))
    master_before = Column(Integer, default=1)
    master_after = Column(Integer, default=1)
    cost_time = Column(Integer, default=0)


class DailyStat(Base):
    __tablename__ = "daily_stats"
    id = Column(Integer, primary_key=True, index=True)
    stat_date = Column(String(20))
    new_count = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    study_time = Column(Integer, default=0)
    mock_count = Column(Integer, default=0)


# ========== 表7：公考倒计时配置表（v2新增） ==========
class ExamCountdown(Base):
    __tablename__ = "exam_countdowns"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    exam_type = Column(String(50))  # 国考/省考
    exam_date = Column(DateTime)
    remark = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    create_time = Column(DateTime, default=datetime.now)


# ========== 初始化函数 ==========
def init_database():
    Base.metadata.create_all(bind=engine)
    _migrate_columns()


def _migrate_columns():
    """为已存在的库补充新增列（SQLite 不支持 create_all 自动加列）"""
    try:
        inspector = __import__("sqlalchemy").inspect(engine)
        cats_cols = [c["name"] for c in inspector.get_columns("categories")]
        if "level2" not in cats_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE categories ADD COLUMN level2 VARCHAR(200) DEFAULT ''"))
                conn.commit()
        q_cols = [c["name"] for c in inspector.get_columns("questions")]
        if "level2" not in q_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE questions ADD COLUMN level2 VARCHAR(200) DEFAULT ''"))
                conn.commit()
        note_cols = [c["name"] for c in inspector.get_columns("notes")]
        if "level1" not in note_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE notes ADD COLUMN level1 VARCHAR(200) DEFAULT ''"))
                conn.commit()
        if "level2" not in note_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE notes ADD COLUMN level2 VARCHAR(200) DEFAULT ''"))
                conn.commit()
        if "level5" not in note_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE notes ADD COLUMN level5 VARCHAR(200) DEFAULT ''"))
                conn.commit()
        if "error_reason" not in q_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE questions ADD COLUMN error_reason VARCHAR(50) DEFAULT ''"))
                conn.commit()
        if "is_favorite" not in q_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE questions ADD COLUMN is_favorite BOOLEAN DEFAULT 0"))
                conn.commit()
        if "deposited" not in q_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE questions ADD COLUMN deposited BOOLEAN DEFAULT 0"))
                conn.commit()
        if "background_knowledge" not in q_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE questions ADD COLUMN background_knowledge TEXT DEFAULT ''"))
                conn.commit()
        # 卡片缩略信息：card_title / card_tags / card_summary
        if "card_title" not in q_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE questions ADD COLUMN card_title VARCHAR(200) DEFAULT ''"))
                conn.commit()
        if "card_tags" not in q_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE questions ADD COLUMN card_tags TEXT DEFAULT ''"))
                conn.commit()
        if "card_summary" not in q_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE questions ADD COLUMN card_summary TEXT DEFAULT ''"))
                conn.commit()
        # 行测知识库：新增考点定位 level1~5 + 来源题目 source_question_id
        kb_cols = [c["name"] for c in inspector.get_columns("knowledge")]
        for lvl in range(1, 6):
            col = f"level{lvl}"
            if col not in kb_cols:
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE knowledge ADD COLUMN {col} VARCHAR(200) DEFAULT ''"))
                    conn.commit()
        if "source_question_id" not in kb_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE knowledge ADD COLUMN source_question_id INTEGER DEFAULT 0"))
                conn.commit()
        # 行测解题库：新增适用考点定位 level1~5
        sl_cols = [c["name"] for c in inspector.get_columns("solve_items")]
        for lvl in range(1, 6):
            col = f"level{lvl}"
            if col not in sl_cols:
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE solve_items ADD COLUMN {col} VARCHAR(200) DEFAULT ''"))
                    conn.commit()
        # 知识库 / 解题库：新增卡片缩略信息字段
        for tbl, cols in (("knowledge", kb_cols), ("solve_items", sl_cols)):
            for col in ("card_title", "card_tags", "card_summary"):
                if col not in cols:
                    with engine.connect() as conn:
                        dtype = "VARCHAR(200)" if col == "card_title" else "TEXT"
                        conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN {col} {dtype} DEFAULT ''"))
                        conn.commit()
        # 笔记：新增卡片缩略信息字段
        note_cols = [c["name"] for c in inspector.get_columns("notes")]
        for col in ("card_title", "card_tags", "card_summary"):
            if col not in note_cols:
                with engine.connect() as conn:
                    dtype = "VARCHAR(200)" if col == "card_title" else "TEXT"
                    conn.execute(text(f"ALTER TABLE notes ADD COLUMN {col} {dtype} DEFAULT ''"))
                    conn.commit()
        if "question_stem" not in note_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE notes ADD COLUMN question_stem TEXT DEFAULT ''"))
                conn.commit()
    except Exception as e:
        print(f"[迁移列失败] {e}")


def recalc_category_counts(db):
    """根据 questions 表重新统计每个分类节点的题目数与错题数（按路径前缀匹配）"""
    cats = db.query(Category).all()
    questions = db.query(Question).all()
    for c in cats:
        c.question_count = 0
        c.error_count = 0
    for q in questions:
        qpath = {1: q.level1, 2: q.level2, 3: q.level3, 4: q.level4, 5: q.level5}
        for c in cats:
            cpath = {1: c.level1, 2: c.level2, 3: c.level3, 4: c.level4, 5: c.level5}
            match = True
            for lvl in range(1, 6):
                cv = cpath.get(lvl)
                if cv:
                    if (qpath.get(lvl) or "") != cv:
                        match = False
                        break
            if match:
                c.question_count = (c.question_count or 0) + 1
                if q.is_error:
                    c.error_count = (c.error_count or 0) + 1
    db.commit()


def _migrate_questions_remove_all(db):
    """旧结构题目 level2=="全部" → 上移一层，去掉"全部"容器节点。"""
    try:
        qs = db.query(Question).filter(Question.level2 == "全部").all()
        for q in qs:
            q.level2 = q.level3
            q.level3 = q.level4
            q.level4 = q.level5
            q.level5 = ""
        if qs:
            db.commit()
            print(f"[迁移] 已上移 {len(qs)} 道题目的层级（去除全部节点）")
    except Exception as e:
        print(f"[迁移题目层级失败] {e}")


def init_categories():
    from services.data_init import get_categories_data
    db = SessionLocal()
    try:
        # 数据迁移：旧结构题目 level2=="全部" → 上移一层（去除"全部"容器节点）
        _migrate_questions_remove_all(db)

        existing = db.query(Category).count()
        # 检测旧结构：存在名为"全部"的节点 → 需清空按新结构重灌
        has_all = db.query(Category).filter(Category.name == "全部").count() > 0
        if existing > 0 and not has_all:
            return  # 已是新结构，不再动
        # 结构变更（去除二级"全部"节点、关键层级上移一层）：清空后按新结构重灌
        if existing > 0:
            db.query(Category).delete()
            db.commit()
        categories = get_categories_data()
        for cat in categories:
            c = Category(
                id=cat["id"], level=cat["level"], name=cat["name"],
                parent_id=cat["parent_id"],
                level1=cat.get("level1", ""),
                level2=cat.get("level2", ""),
                level3=cat.get("level3", ""),
                level4=cat.get("level4", ""),
                level5=cat.get("level5", ""),
                sort=cat.get("sort", 0),
                module=cat.get("module", ""),
            )
            db.add(c)
        db.commit()
        print(f"[初始化] 已导入 {len(categories)} 个分类节点")
        recalc_category_counts(db)
    except Exception as e:
        db.rollback()
        print(f"[初始化分类失败] {e}")
    finally:
        db.close()


def init_prompts():
    from services.data_init import get_prompts_data
    db = SessionLocal()
    try:
        seeds = get_prompts_data()
        # 内置模板整体刷新：先删除全部锁定模板再按种子重建，保证内置集与种子一致（用户自定义模板不受影响）
        db.query(PromptTemplate).filter(PromptTemplate.is_locked == True).delete()
        db.commit()
        existing = {p.name: p for p in db.query(PromptTemplate).all()}
        for s in seeds:
            if s["name"] in existing:
                p = existing[s["name"]]
                # 内置锁定模板：内容有更新时同步刷新，用户自定义模板不受影响
                if p.is_locked and p.content != s["content"]:
                    p.content = s["content"]
                    p.remark = s.get("remark", "")
                    p.tag = s.get("tag", "")
            else:
                pt = PromptTemplate(
                    name=s["name"], type=s["type"], tag=s.get("tag", ""),
                    content=s["content"], is_default=True, is_locked=True,
                    is_pinned=s.get("is_pinned", False), remark=s.get("remark", ""),
                )
                db.add(pt)
        db.commit()
        print(f"[初始化] 提示词模板已就绪（{len(seeds)} 个内置）")
    except Exception as e:
        db.rollback()
        print(f"[初始化提示词失败] {e}")
    finally:
        db.close()


def init_exam_countdowns():
    from services.data_init import get_exam_dates_data
    db = SessionLocal()
    try:
        if db.query(ExamCountdown).count() > 0:
            return
        dates = get_exam_dates_data()
        for d in dates:
            ec = ExamCountdown(
                name=d["name"], exam_type=d["exam_type"],
                exam_date=datetime.strptime(d["exam_date"], "%Y-%m-%d"),
                remark=d.get("remark", ""), is_active=True,
            )
            db.add(ec)
        db.commit()
        print(f"[初始化] 已导入 {len(dates)} 个考试倒计时")
    except Exception as e:
        db.rollback()
        print(f"[初始化倒计时失败] {e}")
    finally:
        db.close()


def init_knowledge():
    from services.data_init import get_knowledge_data
    db = SessionLocal()
    try:
        if db.query(Knowledge).count() > 0:
            return
        seeds = get_knowledge_data()
        for s in seeds:
            k = Knowledge(
                module=s["module"], kg_type=s.get("kg_type", "概念"), title=s["title"],
                content=s["content"], tags=s.get("tags", ""),
                related_prompt=s.get("related_prompt", s["module"]),
                source=s.get("source", ""), difficulty=s.get("difficulty", 2),
            )
            db.add(k)
        db.commit()
        print(f"[初始化] 行测知识库已播种（{len(seeds)} 条知识点）")
    except Exception as e:
        db.rollback()
        print(f"[初始化知识库失败] {e}")
    finally:
        db.close()


def init_all():
    init_database()
    init_categories()
    init_prompts()
    init_exam_countdowns()
    init_knowledge()
    print("[初始化完成] 数据库就绪")
