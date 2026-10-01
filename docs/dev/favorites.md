# 设计文档：收藏体系 v2（统一事实源 · 全对象星标 · 独立收藏页）

状态：已实现 | 日期：2026-10-01
前身：docs/dev/favorites.md（v1，只有资料/题目且同步不对称）

## 调研结论（问题清单 → v2 目标）

Explore 代理盘点出 8 个碎片化问题，v2 逐一解决：

| # | v1 问题 | v2 方案 |
|---|---------|---------|
| R1 | 题目收藏走 PUT /questions/{id}，不写 favorites 表 | 收藏**唯一写入口** = `POST /api/favorites/toggle`；questions PUT 中的 is_favorite 字段**下线**（模型保留列但接口忽略） |
| R2 | favorites→resource 不同步 resources.is_favorite | **favorites 表为唯一事实源**；resources.is_favorite 列废弃（查询改造，不再读它） |
| R3 | 资料详情不回传收藏态 | detail/list 全部经 status 查询回传 |
| R4 | status 做并集掩盖矛盾 | status 只读 favorites 表（唯一事实源后无矛盾） |
| R5 | 筛选口径分裂 | 题目列表的 is_favorite 筛选改为联 favorites 表 |
| R6 | favorites 无唯一约束 | 加 (obj_type, obj_id) **唯一索引**（重建表）；toggle 用"查有则删/无则插"，幂等 |
| R7 | knowledge/solve_item 无采集入口 | 两页面加星标（FavoriteStar 组件） |
| R8 | notes.is_collect 第四套体系 | **v2 范围外**：保留不动（语义是"收藏笔记"本身，收藏中心后续版本再合并），devlog 说明 |

## 业界参考

- **GitHub Stars**：唯一 star 动作 + 单一事实源 + Lists 分组 → 我们做唯一 toggle + 类型 tab
- **Anki 旗标**：标旗（过程性学习标记）与 Mark（收藏）互补 → 我们的错题标旗/掌握度体系不变，收藏只做"值得回看"
- **乐观 UI 最佳实践**（remix.guide/robinwieruch.de）：星标是低风险幂等变更，前端立即翻转、失败回滚 + 提示

## 数据模型（v2）

`favorites` 重建，加唯一索引：
```sql
CREATE UNIQUE INDEX ux_favorites_obj ON favorites(obj_type, obj_id)
```
迁移：启动时一次性把 `questions.is_favorite=1` 与 `resources.is_favorite=1`
灌入 favorites（幂等，跳过已存在）。旧列保留但不再作为事实源。

## 接口（v2）

| 接口 | 变化 |
|------|------|
| POST /api/favorites/toggle | 不变（幂等由唯一索引兜底）；resource 也同步旧列至 0 语义作废——改为不写旧列 |
| GET /api/favorites | resource 项 route 精确到 `?keyword=<标题>` 定位；question 跳 `/question/{id}` |
| POST /api/favorites/status | 只读 favorites 表 |
| GET /questions/list | `is_favorite` 筛选改为 EXISTS favorites |
| PUT /questions/{id} | 忽略 is_favorite 字段（禁止旁路写入） |
| GET /resources/list、/detail | is_favorite 由 favorites 表派生 |

## 前端（v2）

- **FavoriteStar 组件**（components/FavoriteStar.vue）：统一星标（props: objType/objId/initial，
  emit change；乐观翻转 + 失败回滚；aria-pressed；阻止冒泡）
- 四页面接入：资料库（替换原内联星标）、题目详情/列表、知识库卡片、解题库卡片
- 收藏页 `/favorites`：保留四 tab；备注编辑（点击备注图标弹输入）；资料项定位到具体资料
- **主侧栏**：移除「资料库」组下的"我的收藏"筛选入口（R 重复），只保留「复习巩固」组的收藏中心
- 资料库页内左栏"我的收藏"改读统一计数（favorites 表 resource 计数）

## 验证计划

1. 迁移幂等：重复启动不重复灌入
2. 四类对象 toggle→list→status 全链路 + 幂等重放
3. 旧路径旁路验证：PUT questions is_favorite 被忽略、题目列表 is_favorite 筛选走新表
4. 前端：四页面星标点选 → 收藏页即时可见（乐观 UI）
5. 回归：题目列表/资料库/收藏页互不破坏
