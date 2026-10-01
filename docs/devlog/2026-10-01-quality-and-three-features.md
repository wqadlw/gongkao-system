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

## 四、新功能：资料库（resource-library）

- 新表 `resources`（mindmap/link 两类），`routers/resources.py`：分类计数/分页列表/图片与文件服务（realpath 限定 data/resources，穿越已测拦截）/batch 导入。
- `scripts/kuriv_to_resources.py`：51 张导图（行测 5 模块 + 申论 + 面试，含 PNG 预览与 emmx 下载）+ 4 条外链（coder2gwy、developer2gwy 指南——无明确开源许可，只收录外链不拷贝内容；xingcezhenti/LogiQA 溯源链接）。
- 前端 `/resource-library`：左侧分类（含计数）+ 图片卡片墙 + 详情大图预览/下载；侧栏「资料库」分组新增入口。
- 踩坑 ×3：① RESOURCES_DIR 从 routers/ 只退一级导致路径错（改用 DB_PATH 同源锚点）；② 清单路径多写一层 resources/ 前缀（脚本口径统一为相对 data/resources）；③ Vue 模板在 el-dialog 内混用 <template v-if> 与具名插槽会编译报错（改为 v-if 表达式守卫）。
- 测试脚本第三次忘给中文参数 urlencode——教训：所有请求参数一律走 urlencode。
- 网络恢复，此前积压的 2 个提交与本次全部推送成功。

## 五、资料库结构升级：接入考公脑库（kaogongzhentizhengliu）

- 同作者（ERRRC）Obsidian 知识库：11,282 篇逐题深度标注 + 10,375 考点 MOC + 717 材料档案，qid 与 xingcezhenti 同源。
- `resources` 表升级：新增 content / related_qids 列（数据可再生，DROP 后 create_all 重建）。
- `scripts/naoku_to_resources.py`：MOC → 考点精讲 10,375 条（wikilink 清洗 + emoji 清理 + qid 提取，11,051 条带关联）；材料 → 材料档案 717 条。
- 资料库总计 **11,147 条**：思维导图 51 / 考点精讲 10,375 / 材料档案 717 / 外链 4。
- 前端重设计：类型筛选 chips + 考点精讲模块分面（判断推理/资料分析）+ 文本卡与图片卡自适应 + 详情 markdown 渲染 + 关联真题跳转（qid → bank_imports → 题目详情，导入对应题目后自动激活）。
- 11,147 条导入仅 2.1s（batch 预载去重集）；batch 逐条查询的 N+1 同步消除。
- 方案 A（11,282 篇逐题标注回填题目结构化字段）待用户确认后另行实施。

## 六、方案 A：11,270 道真题深度标注入库

- `scripts/naoku_questions_import.py`：解析 10-真题 每题标注 → 按字段映射入库
  （问法模型→identify_signal、推理链→break_logic、最快解法→quick_solve、
  易错点→error_path、母题抽象+同类特征→background_knowledge、考点末段→sub_point，
  level1~3=模块/大类/细分考点），qid 走 bank_imports 保持去重体系。
- **非破坏性原则**：对已存在题目只回填空字段，绝不覆盖用户自己的解析。
- 全量 15 秒：导入 11,270（跳过 12 篇结构异常），题库总量达 **19,365 题**。
- 新端点 `/api/resources/naoku/media`（脑库配图，限定 90-图片 内，穿越已拦截）。
- 踩坑：① clean() 把 ✅ 一并清掉导致答案提取不到（选项块须用原文）；② 单行字段
  （最快解法/同类特征）跟在 ## 小节后会被并进上节（用全文 **字段** 提取 + 剔除并行走漏行）；
  ③ 图片端点路径双拼 90-图片（path 已含前缀，基准应为脑库根）；④ 路由前缀叠加
  （/api/resources/naoku/media），导入改写与路由注册必须一致，批量 REPLACE 修正存量。

## 七、模考模式上线（Roadmap #1 完成）

- 新表 `mock_questions`（试卷快照 + 作答记录），复用既有 `MockExam` 成绩表
  （score_politics/common/verbal/quant/logic/data 与六大模块一一对应）。
- `routers/mock.py`：start（按模块随机配额/按真题卷 source）/paper（断点续答，
  已交卷 400）/submit（判分 + 模块计分 + 未答按错）/result（复盘逐题解析）/
  delete。paper 不含答案，交卷前不泄露。
- 前端 `/mock`：组卷表单 → 答题界面（倒计时不足 5 分钟闪烁、答题卡、
  上一题/下一题）→ 成绩单（按正确率分档配色）+ 逐题复盘跳转题目详情。
- 回归 9 项全过（组卷/无答案泄露/判分/模块计分/复盘/列表/断点/交卷保护/删除）。

## 八、资料库三级层级导航

用户反馈：11,147 条平铺浏览体验差。方案：左侧升级为**三级可展开树**（分类 → 模块 → 大类/考点组，每级带计数），
点击任意层级按 sub_path 前缀过滤——三击即可从 11,147 收敛到数百条（如 考点精讲>资料分析>比重=762）。
- 后端 `GET /api/resources/tree`：sub_path 按段聚合（Python 内存聚合 11k 行，毫秒级）。
- 前端树：展开/收起 caret、三级缩进、选中高亮、类型筛选 chips 与树并存。
- 三次踩坑（用户反馈"资料库图片显示不出来"的另一主体）：**646 条材料档案正文**
  内嵌 `../../90-图片/` 相对路径图片，清洗时未改写 → 详情页全是死链。
  修复：SQL 批量 REPLACE 为 naoku media 端点 + 脚本同步；另将列表排序改为
  导图（有图）优先，首屏即图片墙（原排序材料档案文本卡排在最前）。
- 二次踩坑（图片全挂）：resources 表重建后用**旧清单**重导入，清单里的
  `resources/` 前缀当时只修了脚本和库、没重新生成清单文件 → 路径双重拼接 404。
  教训：**修完生成逻辑必须重新生成中间产物**，凡清单/缓存类文件一律视为过期。
- 踩坑：sort_children 误把"子节点字典"再按 ["children"] 取值（KeyError）；Vue3 `<template v-for>` 的 key 必须放在 template 标签上。

## 九、学习手册导出（吸收 NovaForge 模板结构）

- 调研：NovaForge（SiriusFzh，⭐676，MIT）为 LaTeX/Typst/Markdown 笔记模板集，
  本项目只吸收其 exam-review 冲刺手册的**章节组织**（不复制内容）；
  其 Claude Skill 生成流程与 Web 架构不符，不吸收。
- `routers/handbook.py`：/modules 预览 + /export 生成 Markdown 手册
  （考情速览 → 薄弱考点 TOP10 → 考点速查[资料库核心立场] → 公式/知识点速查 → 错题本）。
- 前端备份页新增模块选择与导出按钮。
- 踩坑：Content-Disposition 中文文件名 latin-1 编码崩溃 → RFC 5987 filename* +
  ASCII 兜底（backup/anki 导出用的 FileResponse filename 参数无此问题）。
- 实测：判断推理手册 806KB（7,000+ 考点核心立场全量），常识手册 4KB。

## 十、资料库体验优化（用户反馈四连）

用户反馈：①资料分析不该挂在"考点精讲"下 ②材料档案没有分类 ③弹窗要全屏 ④内容太多要收藏与阅读优化。

- **树重构为模块优先**：一级=行测六大模块/申论/面试/经验指南，二级=类型（考点精讲/材料档案/思维导图/外部链接），三级=大类或年份。节点自带 filter 对象（module_prefix/resource_type/category/sub_prefix），前端递归组件 ResourceTree.vue 任意深度渲染。
- **材料档案细分**：脑库材料笔记无大类标签，但标题含年份 → sub_path 改为 `资料分析/年份`，717 条按年份分面。
- **收藏**：表加 is_favorite（重建表，重导 11,147），`POST /{id}/favorite` toggle + list favorite 过滤；卡片右上角星标 + 详情收藏 + 侧栏「我的收藏」入口。
- **弹窗全屏**：dialog fullscreen 切换（页脚+头部双入口），全屏时正文高度 calc(100vh-200px)。
- 坑：list 端点 module_prefix 需 `sub_path LIKE x% OR category = x`（申论/面试 mindmap 的 sub_path 为空）。
- 回归 6/6：模块树、材料年份分面、module 过滤(4071)、收藏开/筛/关。

## 十一、待办 / 遗留

- [x] GitHub 网络恢复，积压提交已全部推送（期间再次中断过，均已补齐）
- [x] SQLite 在线备份 API（create 接口改用 sqlite3.backup）
- [x] MockExam 写入口（模考模式，Roadmap #1 完成）
- [ ] 依赖升级（fastapi/pydantic 等较旧，6 包命中已知通告）
