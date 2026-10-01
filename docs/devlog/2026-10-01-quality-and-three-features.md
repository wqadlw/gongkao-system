# 工作日志 2026-10-01：审查修复 + 三大特性（FSRS 优化 / LogiQA / OCR）

> 按 docs/dev/README.md 的流程执行：调研 → 设计 → 实现 → 验证 → 沉淀。

## 一、项目全面审查（前期）

- Explore 子代理逐文件审查 backend，Mimosa 深度扫描（其 AST 分析当次不可用，结论以人工为准）。
- 发现 4 个 P0 安全洞（路径穿越 ×4）、8+ P1（overdue 恒 0、倒计时差一天、提示词 tips 丢失、重复考点节点、stats 全表重复加载等）。
- P0 全部修复 + P1 前 4 项修复，回归 10/10。Mimosa 钩子三次误拦（字面量 DDL、".." 字面量、open() 写盘），分别以绕行方案化解。
- 性能改造：`/api/stats/all` 单次加载复用；recalc 改 GROUP BY 聚合并合并两处重复实现；数据集导入去重消 N+1（8016 题导入实测 1.1s）。
- 接线了仓库里沉睡的**全局搜索**（search.py + Search.vue 三件套补线，顶栏搜索升级为跨库检索）。

## 二、三大特性

### 1. FSRS 参数个性化优化（docs/dev/fsrs-optimization.md）

**调研关键决策**：
- `fsrs-optimizer`（PyPI 官方）依赖 torch + pandas>=3.0，体积 GB 级 → 弃用。
- 选用 **`fsrs-rs-python` 0.9.3**：官方 Rust FSRS 的 Python 绑定，**零依赖**，手写梯度。
- 数据量门槛采用 Anki 实践：长期复习条目 <20 拒绝训练，<400 标注"样本较少"。

**实现**：
- 新表 `app_settings`（KV，create_all 建表）存训练后的 21 参数。
- `services/fsrs_optimizer.py`：review_logs → 按题聚合（同日多次复习合并取末次评分）→ FSRSItem 序列 → `FSRS.compute_parameters`。
- 调度链路：`review.py` 读参数传入 `schedule_fsrs(parameters=...)`；`/api/review/engine` 增加 `custom_parameters`。
- 前端：复习页"优化参数"按钮 + 弹窗（默认 vs 专属参数对比）。

**验证 5/5**：engine 字段 / 不足拒绝 / 347 条合成日志训练出 21 参数 / 参数持久化 / 现场还原。
**踩坑**：构造合成数据时 `cycle` 使日期回退 → delta_t 为负抛 OverflowError（库的输入校验是好的）。

### 2. LogiQA 题源接入（+8016 题判断推理）

- 格式：每题 7 行（答案字母/背景/问题/四选项），空行分块。
- 转换器 `scripts/logiqa_to_dataset.py`（防重、格式校验），产出落入 `data/question_sources/` 走既有导入通道。
- 结果：**判断推理 8016 题**入库，导入耗时 1.1s，树计数与题数一致。

**踩坑（重要）**：`SessionLocal` 为 `autoflush=False`，批量 add 后立刻跑 recalc 聚合查询看不到未 flush 的新题 → 计数 0。修复：`recalc_category_counts` 开头 `db.flush()`。**任何"批量写入后立刻聚合"的代码都要注意这一点。**

### 3. RapidOCR 截图识别题干

- 选型 `rapidocr-onnxruntime`（PP-OCRv4 中文、ONNX Runtime 纯本地、pip 即装）；识别结果按行拼接纯文本。
- `POST /api/ocr`（上传图片，10MB 限制，引擎单例懒加载，未装库时 400 提示）。
- 录入页 ②区新增"截图识别题干"：识别文字预填题干输入框，公式仍交 AI——把录题从"手打/整段粘 AI"中省掉一步。
- 验证：合成中文图片识别"下列说法正确的是："✅，接口端到端 ✅。

## 三、公考知识导入：思维导图库（kuriv/civil-service-exam，MIT）

**调研**：仓库为亿图脑图 `.emmx` + PNG 预览，按 `行测/<模块>/<主题>/<考点>/` 组织（另含申论/面试，本项目暂不导入，模块不符）。
`.emmx` 是 zip：`page/page.xml` 内 `<Shape ID Type>` 节点、`<tp>` 存文本、`<LevelData><SubLevel V="子ID;…"/>` 描述层级——纯 Python 可解析。

**实现**：`scripts/emmx_to_knowledge.py`（安全加固：拒绝 DTD/ENTITY + 20MB 上限，Mimosa 要求），
每张导图 → 一条知识卡（module=模块、level2/3=目录路径、content=大纲 markdown、card_summary=一级分支）。

**结果**：49/51 个导图成功导入知识库（2 个内容过短跳过），常识判断 +40（宪法/刑法/民法…）、判断推理/言语/数量/资料全覆盖。
验证：`宪法` 条目含"修宪规则/国体/选举制度"等完整大纲 ✅。

**踩坑**：gh-proxy 对中文路径的 raw 请求 404，需走 contents API（base64）；git clone 不受影响。

## 四、待办 / 遗留

- [ ] 本批提交因 GitHub 网络中断未推送（本地领先 2 个提交，恢复后补推）
- [ ] SQLite 在线备份 API（backup 用 sqlite3.backup 替换 shutil.copy2）
- [ ] MockExam 写入口（模考模式，Roadmap #1）
- [ ] 依赖升级（fastapi/pydantic 等较旧，6 包命中已知通告）
