"""
AI文本解析器 v4 - 干货教学式 Markdown 结构解析（保留 Markdown / LaTeX）
纯本地字符串处理，无任何AI调用

设计要点（与提示词完美耦合）：
- AI 现在输出的是「一~五节」的干货 Markdown，公式用 $...$ / $$...$$。
- 解析时按 #### 一/二/三/四/五 分节，逐字段抽取，且【完整保留 Markdown 与 LaTeX 公式】，不再剥离 * 等符号。
- 「考点定位」行用 ` > ` 连接完整题型树路径 → 解析为 level1~level5（自动补齐二级"全部"）。
- 兼容旧的 JSON 结构化输出（category_path / levelN 字段）。
"""
import re
import json


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def parse_ai_content(content: str) -> dict:
    """解析用户粘贴的 AI 返回文本。
    优先级：含 #### 标题 → Markdown 干货结构；否则 JSON；否则纯文本兜底。
    """
    result = _empty_result(content)
    if not content:
        return result

    has_headers = bool(re.search(r'####\s*[一二三四五]', content))
    if has_headers:
        return parse_markdown(content, result)

    json_data = extract_json(content)
    if json_data:
        return merge_json_to_result(json_data, result, content)

    # 兜底：仍尝试 Markdown（可能标题格式不标准），否则原样留存
    return parse_markdown(content, result)


def _empty_result(content: str) -> dict:
    return {
        "sub_point": "", "exam_intent": "", "difficulty_label": "",
        "exam_priority": "", "suggested_time": 60, "option_feature": "",
        "break_logic": "", "trap_read": "", "trap_calc": "", "trap_thought": "",
        "error_path": "", "normal_solve": "", "quick_solve": "", "identify_signal": "",
        "step_detail": "", "practice_question": "", "practice_answer": "", "answer": "",
        "background_knowledge": "",
        "level1": "", "level2": "", "level3": "", "level4": "", "level5": "",
        "question_raw": "",
        "knowledge_items": [],
        "solve_items": [],
        "kb_decision": None,
        "sl_decision": None,
        "solve_method_judgment": "",
        "card_title": "",
        "card_tags": "",
        "card_summary": "",
        "ai_raw_content": content or "",
    }


# ---------------------------------------------------------------------------
# 题型树路径 → level1~5
# ---------------------------------------------------------------------------
def _category_index():
    """构建题型树索引：模块集合 / 父子关系 / 节点表。"""
    try:
        from services.data_init import get_categories_data
        cats = get_categories_data()
    except Exception:
        cats = []
    modules = set()
    children = {}
    nodes = {}
    for c in cats:
        modules.add(c["level1"])
        nodes[c["id"]] = c
        children.setdefault(c["parent_id"], []).append(c["id"])
    return modules, children, nodes


def _find_descendant(root_id, name, children, nodes):
    """在 root_id 的子树中按名称 BFS 查找节点（支持 AI 跳过中间层级）。"""
    import collections
    q = collections.deque(children.get(root_id, []))
    while q:
        nid = q.popleft()
        n = nodes[nid]
        if n["name"] == name:
            return n
        for ch in children.get(nid, []):
            q.append(ch)
    return None


def path_to_levels(path_str: str) -> list:
    """将 '模块 > 二级 > 三级 ...' 解析为 [level1..level5]，按题型树逐层下钻匹配。

    不再强制插入"全部"节点；若 AI 跳过中间层级，会在子树中按名称就近匹配。
    """
    if not path_str:
        return []
    path_str = path_str.strip().strip('`').strip()
    segs = [s.strip().strip('`').strip() for s in re.split(r'\s*[>›»＞→/]\s*', path_str) if s.strip()]
    if not segs:
        return []
    modules, children, nodes = _category_index()
    # 模块必须为第一段；若 AI 把模块写在中段，截取
    if segs[0] not in modules:
        mod = next((s for s in segs if s in modules), None)
        if mod:
            segs = segs[segs.index(mod):]
    if not segs or segs[0] not in modules:
        return segs[:5]  # 无法判定模块，原样返回（best-effort）
    result = [segs[0]]
    current = next((nid for nid, n in nodes.items()
                    if n["level"] == 1 and n["name"] == segs[0]), None)
    for seg in segs[1:]:
        if current is None:
            result.append(seg)
            continue
        child = _find_descendant(current, seg, children, nodes)
        if child:
            result.append(child["name"])
            current = child["id"]
        else:
            # 不在当前子树：作为占位层级保留，停止继续下钻
            result.append(seg)
            current = None
    return result[:5]


def _apply_path(result: dict, path_str: str):
    levels = path_to_levels(path_str)
    for i, key in enumerate(["level1", "level2", "level3", "level4", "level5"]):
        if i < len(levels):
            result[key] = levels[i]


# ---------------------------------------------------------------------------
# Markdown 干货结构解析
# ---------------------------------------------------------------------------
def parse_markdown(content: str, result: dict) -> dict:
    # 抽取「题目 / 题干」：首个 #### 一~六 分节标题之前的正文，去除"题目/题干"标签前缀
    first_header = re.search(r'(?m)^\s*#{2,4}\s*[一二三四五六七八九十]+', content)
    if first_header:
        prefix = content[: first_header.start()].strip()
        prefix = re.sub(r'^\s*\*{0,2}(?:题目|题干)\*{0,2}\s*[:：]?\s*', '', prefix).strip()
        if prefix:
            result["question_raw"] = prefix

    sections = split_by_headers(content)

    # ---------- 一、题型与考场价值判定 ----------
    sec1 = sections.get("一", "")
    if sec1:
        kaodian = _grab(sec1, "考点定位") or _grab(sec1, "考点")
        if kaodian:
            _apply_path(result, kaodian)
        result["sub_point"] = _grab(sec1, "细分考点")

        intent_raw = _grab(sec1, "考察意图")
        if intent_raw:
            # 可能形如 "xxx；难度：基础题"
            m = re.split(r'[；;，,]?\s*难度\s*[:：]', intent_raw)
            result["exam_intent"] = _clean(m[0])
            if len(m) > 1:
                result["difficulty_label"] = _clean(m[1])
        if not result["difficulty_label"]:
            dm = re.search(r'难度\s*[:：]\s*([基础中档拔高]+题)', sec1)
            if dm:
                result["difficulty_label"] = dm.group(1)

        prio_raw = _grab(sec1, "考场优先级")
        if prio_raw:
            pm = re.search(r'(必做|选做|可放弃)', prio_raw)
            result["exam_priority"] = pm.group(1) if pm else _clean(prio_raw)
        tm = re.search(r'(\d+)\s*秒', sec1)
        if tm:
            try:
                result["suggested_time"] = int(tm.group(1))
            except ValueError:
                pass
        result["option_feature"] = _clean_small(_grab(sec1, "选项特征"))

    # ---------- 二、核心解题思路与避坑提醒 ----------
    sec2 = sections.get("二", "")
    if sec2:
        result["break_logic"] = _grab(sec2, "破题逻辑链") or _grab(sec2, "破题逻辑")
        result["trap_read"] = _clean_small(_grab(sec2, "读题陷阱"))
        result["trap_calc"] = _clean_small(_grab(sec2, "计算陷阱"))
        result["trap_thought"] = _clean_small(_grab(sec2, "思维误区"))
        result["error_path"] = _grab(sec2, "常见错误路径")

    # ---------- 三、通用技巧与考场速算方法 ----------
    sec3 = sections.get("三", "")
    if sec3:
        result["normal_solve"] = _grab(sec3, "常规通用解法") or _grab(sec3, "常规解法")
        result["quick_solve"] = (_grab(sec3, "速算/秒杀技巧") or _grab(sec3, "速算")
                                 or _grab(sec3, "秒杀") or _grab(sec3, "快速解题法"))
        result["identify_signal"] = _grab(sec3, "题型识别信号") or _grab(sec3, "识别信号")

    # ---------- 四、详细解题步骤 ----------
    sec4 = sections.get("四", "")
    if sec4:
        result["step_detail"] = _clean(sec4)
        am = re.search(r'答案\s*[:：]\s*\*{0,2}\s*([A-DＡ-Ｄ√×对错正确错误]+)', sec4)
        if am:
            result["answer"] = am.group(1).strip()

    # ---------- 五、同考点巩固练习 ----------
    sec5 = sections.get("五", "")
    if sec5:
        # 去掉末尾"是否需要整理该考点的备考笔记？"触发问句
        sec5 = re.sub(r'\n*\s*>?\s*是否需要整理.*?备考笔记.*$', '', sec5, flags=re.DOTALL).strip()
        parts = re.split(r'【\s*练习答案解析\s*】', sec5)
        pq = parts[0]
        pq = re.sub(r'^\s*(?:\d+[\.、]\s*)?题干\s*[:：]?\s*', '', pq.strip())
        result["practice_question"] = _clean(pq)
        if len(parts) > 1:
            result["practice_answer"] = _clean(parts[1])

    # ---------- 六、思维模型和知识背景 ----------
    sec6 = sections.get("六", "")
    if sec6:
        result["background_knowledge"] = _clean(sec6)

    # 兜底答案（全文搜索）
    if not result["answer"]:
        am = re.search(r'答案\s*[:：]\s*\*{0,2}\s*([A-DＡ-Ｄ√×对错]+)', content)
        if am:
            result["answer"] = am.group(1).strip()

    # 第七节：考点沉淀 —— 由【出题人意图】驱动，AI 先判定「是否需要」再单独输出结构化条目
    # （不再盲目从二/三节字段硬抽，避免常识/政治等记忆型模块产生垃圾解题条目）
    levels = {f"level{n}": result.get(f"level{n}", "") or "" for n in range(1, 6)}
    dep = parse_deposit_section(content, levels)
    result["knowledge_items"] = dep["knowledge_items"]
    result["solve_items"] = dep["solve_items"]
    result["kb_decision"] = dep["kb_decision"]
    result["sl_decision"] = dep["sl_decision"]
    result["solve_method_judgment"] = dep["solve_method_judgment"]
    # §7 的【出题人意图】更完整（点明出题人真正考察的能力与干扰），覆盖 §1.3 的简短"考察意图"
    if dep["exam_intent"]:
        result["exam_intent"] = dep["exam_intent"]

    # 第八节：卡片缩略信息（列表卡片精简展示，不写整题/完整路径）
    sec8 = sections.get("八", "")
    if sec8:
        card = _parse_card_block(sec8)
        result["card_title"] = card["card_title"]
        result["card_tags"] = card["card_tags"]
        result["card_summary"] = card["card_summary"]

    result["ai_raw_content"] = content
    return result


# 知识库 / 解题库 条目类型集合（单一事实源：须与前端 constants.js 的 KG_TYPES / SOLVE_TYPES 的 key 一致）
KG_TYPE_SET = {"概念", "公式", "技巧", "陷阱", "易混点", "方法", "背景"}
SOLVE_TYPE_SET = {"破题逻辑", "易错提醒", "解题方法", "速算技巧", "题型识别"}
# 解析正则用的类型列表：按长度降序，避免「技巧」误匹配「速算技巧」等更长短语
_DEPOSIT_TYPES = sorted(KG_TYPE_SET | SOLVE_TYPE_SET, key=len, reverse=True)
_DEPOSIT_TYPE_RE = "|".join(_DEPOSIT_TYPES)


def parse_deposit_section(content: str, levels: dict = None):
    """从『七、考点沉淀』解析 AI 的「判定 + 单独结构化输出」。

    返回 dict：
    - knowledge_items: 行测知识库条目列表，每条 {kg_type, title, content, level1..5}
    - solve_items:      行测解题库条目列表，每条 {solve_type, title, content, level1..5}
    - exam_intent:      【出题人意图】文本（驱动两库分工；可能为空）
    - kb_decision:      '需要' / '不需要' / None（AI 对知识库的判定；None=未显式判定）
    - sl_decision:      '需要' / '不需要' / None（AI 对解题库的判定）

    解析策略（与提示词 §7 强耦合）：
    1. 提取【出题人意图】。
    2. 读取【行测知识库 判定】【行测解题库 判定】的「需要/不需要」。
    3. 仅当判「需要」（或虽未判但存在条目）时，才在各自独立的【行测知识库】/【行测解题库】条目块中解析条目；
       判「不需要」的库即使误带条目也被忽略，绝不进库。
    4. 每条条目继承本题「考点定位」(levels)，落到题库对应位置、可关联来源题目。
    """
    if levels is None:
        levels = {f"level{n}": "" for n in range(1, 6)}
    sections = split_by_headers(content)
    sec7 = sections.get("七", "")
    if not sec7:
        return {"knowledge_items": [], "solve_items": [], "exam_intent": "",
                "kb_decision": None, "sl_decision": None, "solve_method_judgment": ""}

    # 1) 出题人意图（截止于下一个【行测知识库/解题库】标记）
    intent_m = re.search(
        r'【\s*出题人意图\s*】\s*(.*?)(?=\n\s*【\s*(?:行测知识库|行测解题库)' + r'|$)',
        sec7, re.DOTALL,
    )
    exam_intent = _clean(intent_m.group(1)) if intent_m else ""

    # 2) 判定行
    kb_j = re.search(r'【\s*行测知识库[\s·\-]*判定\s*】\s*(需要|不需要)', sec7)
    sl_j = re.search(r'【\s*行测解题库[\s·\-]*判定\s*】\s*(需要|不需要)', sec7)
    kb_decision = kb_j.group(1) if kb_j else None
    sl_decision = sl_j.group(1) if sl_j else None

    # 顶层「题型解法判定」：知识积累型 / 解题运算型 / 综合型（本题靠什么做出来的）
    sm_j = re.search(r'【\s*题型解法判定\s*】\s*(知识积累型|解题运算型|综合型)', sec7)
    solve_method_judgment = sm_j.group(1) if sm_j else ""

    # 3) 解析条目：直接扫描整段第七节，按「条目类型」归属到对应库
    #    —— 不再依赖【行测知识库】/【行测解题库】包裹头（AI 真实产出常省略），由类型集合决定归属，
    #       知识型条目(概念/公式/技巧/陷阱/易混点/方法/背景)→ 行测知识库，
    #       解题型条目(破题逻辑/易错提醒/解题方法/速算技巧/题型识别)→ 行测解题库。
    #       这样无论 AI 是否写包裹头、条目顺序如何，都能正确捕获候选卡片。
    knowledge_items = _parse_entries(sec7, KG_TYPE_SET, levels)
    solve_items = _parse_entries(sec7, SOLVE_TYPE_SET, levels)

    # 4) 决策修正（条目优先于「判定」提示，避免 AI 误写「不需要」却产出卡片时系统悄无声息丢卡）：
    #    - 只要实际解析出条目 → 决策修正为「需要」（卡片是否真正入库仍由用户在页面勾选决定）。
    #    - 显式判「不需要」且没有条目 → 维持「不需要」（不进库）。
    #    - 未显式判定时，以「是否有条目」推断决策（向后兼容旧格式）。
    if kb_decision is None or kb_decision == "不需要":
        kb_decision = "需要" if knowledge_items else kb_decision
    if sl_decision is None or sl_decision == "不需要":
        sl_decision = "需要" if solve_items else sl_decision

    return {
        "knowledge_items": knowledge_items,
        "solve_items": solve_items,
        "exam_intent": exam_intent,
        "kb_decision": kb_decision,
        "sl_decision": sl_decision,
        "solve_method_judgment": solve_method_judgment,
    }


def _parse_entries(region: str, type_set, levels: dict) -> list:
    """在某一库的条目区域内，按【类型】标题：/内容：解析条目，继承考点定位 levels。"""
    items = []
    parts = re.split(r'\n\s*【\s*(' + _DEPOSIT_TYPE_RE + r')\s*】', region)
    for i in range(1, len(parts), 2):
        dtype = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        tm = re.search(r'标题\s*[:：]\s*(.+?)(?:\n|$)', body)
        if tm:
            title = tm.group(1).strip()
            cm = re.search(r'内容\s*[:：]\s*(.*)', body, re.DOTALL)
            cbody = cm.group(1).strip() if cm else body.strip()
        else:
            # 容错：未写「标题/内容」时，按首行「xxx：yyy」拆出标题与内容
            first_line = body.strip().split('\n', 1)
            head = first_line[0].strip()
            rest = first_line[1].strip() if len(first_line) > 1 else ""
            if '：' in head or ':' in head:
                sp = re.split(r'[:：]', head, maxsplit=1)
                title = sp[0].strip()
                cbody = (sp[1].strip() + ('\n' + rest if rest else '')).strip()
            else:
                title = head
                cbody = rest
        # 关键修复：每条末尾的「列表缩略 / 卡片标题 / 考点标签 / 卡片摘要」属于卡片
        # 缩略信息，必须剥离出正文，否则会以「卡片标题：xxx 考点标签：…」字样原样
        # 泄露进 content，在知识卡详情里显示成难看的元数据标签。
        cbody = _strip_card_meta(cbody)
        cbody = _clean(cbody)
        if not title or not cbody:
            continue
        # 跳过「无」类占位（短内容）
        if cbody in ("无", "无。", "none", "None", "暂无", "无（本题无可复用解题技巧）"):
            continue
        if dtype in type_set:
            key = "kg_type" if type_set is KG_TYPE_SET else "solve_type"
            # 条目级卡片缩略信息（提示词 §7 每条附带的【卡片标题】【考点标签】【卡片摘要】）
            ecard = _parse_card_block(body)
            item = {
                key: dtype, "title": title, "content": cbody,
                "card_title": ecard["card_title"],
                "card_tags": ecard["card_tags"],
                "card_summary": ecard["card_summary"],
            }
            # 条目自有【分类】优先：让知识/解题条目落到题库的「对应多级分类」位置，
            # 而非继承题目本身的（往往较浅的）考点路径。无分类时回退继承题目 levels。
            cat = _parse_category(body)
            if cat.get("level1"):
                item.update(cat)
            else:
                item.update(levels)
            items.append(item)
    return items


def _parse_category(sec: str) -> dict:
    """解析条目的多级分类路径（提示词 §7 每条附带的【分类】或 分类：）。

    支持分隔符：「-」「/」「>」「｜」「、」「—」；支持到 5 级；未给出则各 level 为空。
    例：常识判断-地理国情-自然地理、政治理论 / 马克思主义 / 哲学。
    返回 {level1..level5}。
    """
    out = {f"level{i}": "" for i in range(1, 6)}
    m = re.search(r'【\s*分类\s*】\s*(.*?)(?=\n\s*【|$)', sec, re.DOTALL)
    if not m:
        m = re.search(
            r'(?m)^\s*分类\s*[:：]\s*(.+?)(?=\s*(?:卡片标题|考点标签|卡片摘要)\s*[:：]|\n|$)',
            sec, re.DOTALL,
        )
    if not m:
        return out
    raw = _clean(m.group(1))
    parts = [p.strip() for p in re.split(r'[-/>、|—]+', raw) if p.strip()]
    parts = [p for p in parts if p not in ("无", "无。", "none")]
    for i, p in enumerate(parts[:5]):
        out[f"level{i + 1}"] = p
    return out


def _extract_stem(raw: str) -> str:
    """从题目原始文本中抽取「题干」（去掉选项行与答案行），供笔记卡片只显示题干。

    判断逻辑：保留选项行（A./B. 或 (A) 形式）之前的所有内容；再剔除末尾独立的答案行。
    若无选项行，则回退返回去除了答案行的整段文本。
    """
    if not raw:
        return ""
    lines = raw.split("\n")
    opt_re = re.compile(r'^\s*[A-Ha-h][\.\、。]|^\s*[\(（][A-Ha-h][\)）]\s')
    out = []
    for ln in lines:
        if opt_re.match(ln):
            break
        out.append(ln)
    stem = "\n".join(out).strip()
    # 去掉末尾可能的答案行（如 答案：B / **答案：B**）
    stem = re.sub(r'\n?\*?\*?答案\s*[:：].*', '', stem).strip()
    return stem


def _strip_card_meta(text: str) -> str:
    """从条目正文中剥离「列表缩略 / 卡片标题 / 考点标签 / 卡片摘要」等卡片缩略信息。

    提示词要求 AI 把这些缩略信息写在每条「内容」之后（或合并在「列表缩略」行），
    它们属于列表卡片快速浏览用的元数据，不应进入知识/解题卡的 Markdown 正文——
    否则详情页会把「卡片标题：xxx 考点标签：a｜b 卡片摘要：…」原样渲染出来。
    本函数截断到首个缩略标记之前，保留前面的真实知识正文。
    """
    if not text:
        return text
    m = re.search(r'\n?\s*[【\[]?\s*(?:列表缩略|卡片标题|考点标签|卡片摘要)\s*[】\]]?\s*[:：]', text)
    if m:
        return text[:m.start()].strip()
    return text


def _parse_card_block(sec: str) -> dict:
    """解析卡片缩略信息：【卡片标题】【考点标签】【卡片摘要】。

    兼容三种写法（与提示词 §7 条目 / §8 题目级一致）：
      - 带【】括号独占：  【卡片标题】zzz
      - 标签行：          卡片标题：zzz（可与其他卡片字段同行或独立成行）
      - 合并「列表缩略」行：列表缩略：卡片标题：a｜考点标签：b｜卡片摘要：c
    返回 {card_title, card_tags(｜分隔), card_summary}；标签按 ｜|/、 归一化为 ｜ 连接。
    """
    out = {"card_title": "", "card_tags": "", "card_summary": ""}
    labels = [("card_title", "卡片标题"), ("card_tags", "考点标签"), ("card_summary", "卡片摘要")]
    # 前置允许「列表缩略：」引导，允许【】包裹；值到下一个标记 / 行尾 / 文末为止
    marker = r'(?:列表缩略\s*[:：])?\s*[【\[]?\s*'
    close = r'\s*[】\]]?\s*[:：]?'
    for key, label in labels:
        pat = re.compile(
            marker + re.escape(label) + close + r'(.*?)'
            r'(?=(?:\s*(?:列表缩略\s*[:：])?\s*[【\[]?\s*(?:卡片标题|考点标签|卡片摘要)\s*[】\]]?\s*[:：])|\n|$)',
            re.DOTALL,
        )
        m = pat.search(sec)
        if m:
            out[key] = _clean(m.group(1)).rstrip('｜|/、').strip()
    if out["card_tags"]:
        tags = [t.strip() for t in re.split(r'[｜|/、]+', out["card_tags"]) if t.strip()]
        out["card_tags"] = "｜".join(tags)
    return out


def split_by_headers(content: str) -> dict:
    """按 #### 一/二/三…（也兼容 ### / ##）切割为 {中文序号: 正文}。"""
    header_re = re.compile(r'(?m)^\s*#{2,4}\s*([一二三四五六七八九十]+)\s*[、\.\s]')
    matches = list(header_re.finditer(content))
    sections = {}
    for i, mo in enumerate(matches):
        num = mo.group(1)
        start = mo.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        # 丢弃本节标题行的剩余文字（节名），只保留标题行之后的正文
        body = content[start:end]
        nl = body.find('\n')
        rest = body[nl + 1:] if nl != -1 else ""
        sections[num] = rest.strip()
    return sections


def _grab(text: str, label: str) -> str:
    """从文本中抽取某标签的值，完整保留 Markdown / LaTeX。
    标签可被 数字序号 / 项目符号 / **加粗** 包裹；值可跨多行，
    直到遇到：下一个数字序号项 / 下一个"符号+中文标签："行 / #### 标题 / 文末。
    """
    pat = re.compile(
        r'(?:^|\n)[ \t]*(?:\d+[\.、]\s*)?(?:[-*·]\s*)?\*{0,2}' + re.escape(label) + r'\*{0,2}\s*[:：]\s*'
        r'(.*?)'
        r'(?=\n[ \t]*\d+[\.、]\s'
        r'|\n[ \t]*[-*·]\s*\*{0,2}[\u4e00-\u9fa5A-Za-z]{2,10}\*{0,2}\s*[:：]'
        r'|\n#{2,4}\s'
        r'|\Z)',
        re.DOTALL,
    )
    m = pat.search(text)
    return _clean(m.group(1)) if m else ""


def _clean(s: str) -> str:
    """仅清理首尾空白与多余空行，保留 Markdown / LaTeX 原样。"""
    if not s:
        return ""
    s = s.strip()
    # 折叠 3 个以上连续换行为 2 个
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()


def _clean_small(s: str) -> str:
    """用于短字段：'无/不适用/none' 归一为空。"""
    v = _clean(s)
    if v and v.strip().lower() in ['无', '不适用', 'none', 'null', '暂无']:
        return ""
    return v


# ---------------------------------------------------------------------------
# JSON 兼容解析（旧格式 / 结构化输出）
# ---------------------------------------------------------------------------
def extract_json(content: str) -> dict:
    code_block_pattern = r'```(?:json)?\s*\n(.*?)\n\s*```'
    for match in re.findall(code_block_pattern, content, re.DOTALL):
        try:
            data = json.loads(match.strip())
            if isinstance(data, dict) and len(data) > 0:
                return data
        except json.JSONDecodeError:
            continue

    first_brace = content.find('{')
    last_brace = content.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            data = json.loads(content[first_brace:last_brace + 1])
            if isinstance(data, dict) and len(data) > 0:
                return data
        except json.JSONDecodeError:
            pass

    try:
        data = json.loads(content.strip())
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return None


def merge_json_to_result(json_data: dict, result: dict, content: str) -> dict:
    field_map = {
        "sub_point": "sub_point", "exam_intent": "exam_intent",
        "difficulty_label": "difficulty_label", "exam_priority": "exam_priority",
        "option_feature": "option_feature", "break_logic": "break_logic",
        "trap_read": "trap_read", "trap_calc": "trap_calc",
        "trap_thought": "trap_thought", "error_path": "error_path",
        "normal_solve": "normal_solve", "quick_solve": "quick_solve",
        "identify_signal": "identify_signal", "step_detail": "step_detail",
        "practice_question": "practice_question", "practice_answer": "practice_answer",
        "answer": "answer", "background_knowledge": "background_knowledge",
        "question_raw": "question_raw", "question": "question_raw", "题干": "question_raw",
    }
    for json_key, result_key in field_map.items():
        if json_key in json_data and json_data[json_key]:
            val = str(json_data[json_key]).strip()
            if val and val.lower() not in ['无', '不适用', 'none', 'null']:
                result[result_key] = val

    if "suggested_time" in json_data:
        try:
            result["suggested_time"] = int(json_data["suggested_time"])
        except (ValueError, TypeError):
            pass

    if "category_path" in json_data and isinstance(json_data["category_path"], list):
        path = [str(x).strip() for x in json_data["category_path"] if str(x).strip()]
        # 直接按拓扑映射；不再补插"全部"节点
        for i, key in enumerate(["level1", "level2", "level3", "level4", "level5"]):
            if i < len(path):
                result[key] = path[i]
    else:
        for key in ["level1", "level2", "level3", "level4", "level5"]:
            if json_data.get(key):
                result[key] = str(json_data[key]).strip()

    result["ai_raw_content"] = content
    return result


# ---------------------------------------------------------------------------
# 备考笔记解析（Markdown 优先，JSON 兼容）
# ---------------------------------------------------------------------------
def parse_note_content(content: str) -> dict:
    result = {
        "question_display": "", "question_stem": "", "type_judgment": "", "knowledge_points": "",
        "logic_chain": "", "solve_steps": "", "pitfalls": "", "speed_tips": "",
        "card_title": "", "card_tags": "", "card_summary": "",
        "note_content": content or "",
    }
    if not content:
        return result

    # JSON 兼容
    json_data = extract_json(content)
    if json_data and any(k in json_data for k in
                         ["question_display", "type_judgment", "knowledge_points",
                          "logic_chain", "solve_steps", "pitfalls", "speed_tips"]):
        for key in ["question_display", "question_stem", "type_judgment", "knowledge_points",
                    "logic_chain", "solve_steps", "pitfalls", "speed_tips",
                    "card_title", "card_tags", "card_summary"]:
            if json_data.get(key):
                result[key] = str(json_data[key]).strip()
        result["note_content"] = content
        return result

    # Markdown：题目取首个代码框；正文完整保留（前端按 Markdown+公式渲染）
    body = content
    cb = re.search(r'```[a-zA-Z]*\s*\n(.*?)\n\s*```', content, re.DOTALL)
    if cb:
        result["question_display"] = cb.group(1).strip()
        result["question_stem"] = _extract_stem(result["question_display"])
        body = content[:cb.start()] + content[cb.end():]  # 从正文中剔除代码框，避免污染字段抽取

    # 笔记字段为「纯标签行」，用已知标签集做互斥分割（保留 Markdown / LaTeX）
    label_groups = [
        ("type_judgment", ["题型判定", "题型"]),
        ("knowledge_points", ["涉及知识点", "知识点"]),
        ("logic_chain", ["解题逻辑链", "逻辑链"]),
        ("solve_steps", ["标准解题步骤", "解题步骤"]),
        ("pitfalls", ["避坑要点", "避坑"]),
        ("speed_tips", ["考场提速技巧", "提速技巧"]),
        ("card_title", ["卡片标题"]),
        ("card_tags", ["卡片标签"]),
        ("card_summary", ["卡片摘要"]),
    ]
    fields = _split_by_labels(body, label_groups)
    for key in ("type_judgment", "knowledge_points", "logic_chain",
                "solve_steps", "pitfalls", "speed_tips",
                "card_title", "card_tags", "card_summary"):
        result[key] = fields.get(key, "")
    result["note_content"] = content
    return result


def _split_by_labels(text: str, label_groups: list) -> dict:
    """按已知标签集把文本切分为 {key: value}，每段值到下一个已知标签为止。
    label_groups: [(key, [别名...]), ...]；标签可被 序号 / 项目符号 / **加粗** 包裹。
    """
    alias_to_key = {}
    all_aliases = []
    for key, aliases in label_groups:
        for a in aliases:
            alias_to_key[a] = key
            all_aliases.append(a)
    # 长别名优先，避免"题型"先于"题型判定"匹配
    all_aliases.sort(key=len, reverse=True)
    alias_pat = "|".join(re.escape(a) for a in all_aliases)
    line_re = re.compile(
        r'(?m)^[ \t]*(?:\d+[\.、]\s*)?(?:[-*·]\s*)?\*{0,2}(' + alias_pat + r')\*{0,2}\s*[:：]\s*'
    )
    matches = list(line_re.finditer(text))
    result = {}
    for i, mo in enumerate(matches):
        key = alias_to_key.get(mo.group(1))
        if not key or key in result:  # 同一字段只取首次出现
            continue
        start = mo.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        val = _clean(text[start:end])
        # 去掉可能残留的分节标题
        val = re.sub(r'\n#{2,4}\s.*$', '', val, flags=re.DOTALL).strip()
        result[key] = val
    return result


# ---------------------------------------------------------------------------
# 校验
# ---------------------------------------------------------------------------
def validate_parsed_content(parsed: dict) -> dict:
    required_fields = {
        "break_logic": "破题逻辑",
        "step_detail": "详细解题步骤",
        "answer": "正确答案",
    }
    missing = [name for field, name in required_fields.items() if not parsed.get(field)]

    warnings = []
    if not parsed.get("level1"):
        warnings.append("未识别到考点分类（考点定位路径），入库后可在录入页手动指定题型树的题项")

    message = "解析成功，核心字段已提取" if not missing else f"以下字段缺失：{', '.join(missing)}，可手动补充"
    if warnings:
        message += "；" + "；".join(warnings)

    return {
        "is_valid": len(missing) == 0,
        "missing_fields": missing,
        "warnings": warnings,
        "message": message,
    }


def build_question_text(question_raw: str, extra_info: str = "") -> str:
    parts = []
    if question_raw:
        parts.append(question_raw)
    if extra_info:
        parts.append(f"\n补充信息：{extra_info}")
    return "\n".join(parts)
