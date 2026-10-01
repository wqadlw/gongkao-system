# 开发流程规范（多 Agent 协作）

> 本项目采用"调研 → 设计 → 实现 → 验证 → 沉淀"的正规开发流程。
> 每个 feature 一个分支式的工作单元，所有产出沉淀在 `docs/dev/`（设计文档）与 `docs/devlog/`（工作日志）。

## 流程

1. **调研（Research）**
   - 摸清现状：通读涉及的现有代码，确认数据模型、API 契约、依赖。
   - 摸清目标：外部库/数据集的真实 API 与数据格式（以官方 README / 源码 / PyPI 元数据为准，不凭印象）。
   - 找最佳实践：官方 examples、同类项目（如 Anki）的做法、已知坑。
   - 产出：调研结论写入当期 devlog 的「调研」小节。

2. **设计（Design）**
   - 明确接口契约（新增/修改的 API、表结构）、与现有代码的集成点、风险与回退策略。
   - 有外部依赖时必须先做最小验证（pip 装上跑通 hello world）再写业务代码。
   - 产出：`docs/dev/<feature>.md` 设计文档。

3. **实现（Implement）**
   - 遵守项目既有约定：
     - 加新字段优先建新表（`create_all` 自动建表），**禁止 ALTER 旧表**（Mimosa 钩子会拦截且风险高）。
     - 所有文件/路径操作必须 basename + 规范化 + 目录前缀校验。
     - 后端端口 7080，前端构建产物 `frontend/dist`，改前端后必须 `npm run build`。
     - 全站禁 emoji，图标用 `@element-plus/icons-vue`；动画用 animate.css。
   - 可选依赖（重库）一律 try-import 优雅降级，缺库时功能隐藏并提示安装。

4. **验证（Verify）**
   - 后端：启动 uvicorn 后用脚本打真实接口做回归断言（参考 `docs/devlog/` 中的验证脚本模式）。
   - 前端：浏览器端到端走一遍核心路径。
   - 回归不通过不提交。

5. **沉淀（Document）**
   - `docs/devlog/YYYY-MM-DD-<slug>.md`：记录调研结论、关键决策（为什么选 A 不选 B）、踩坑记录。
   - 用户可见的功能更新 README 的「核心特性」；体验类更新更新截图。
   - 提交信息用 `type: 摘要` 格式（feat/fix/docs/perf/style/refactor）。

6. **交付（Ship）**
   - `git add -A && git commit && git push`；推送失败（网络）时本地保留提交并记录待推状态。

## 多 Agent 分工约定

- **主 Agent**：规划、集成、前后端实现、验证、交付。
- **Explore Agent**：只读的代码审查/大规模检索，输出结论不落盘。
- **子 Agent 产出**必须由主 Agent 校验后才能进入代码库。

## 代码红线

- 用户数据（`data/gongkao.db`）永不入库；`.gitignore` 是防线，改动需谨慎评审。
- 任何接口不接受未校验的文件路径。
- SQLite 不支持并发写：长任务（训练、批量导入）注意事务时长。
