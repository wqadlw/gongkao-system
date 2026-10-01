# 设计文档：收藏中心（跨对象统一收藏体系）

状态：已实现 | 日期：2026-10-01

## 背景

此前只有资料库有收藏（resources.is_favorite），题目有 is_favorite 字段但无切换接口，
知识库/解题库完全没有。收藏是高频学习动作，升级为**跨对象统一收藏体系**。

## 模型

新表 `favorites`（create_all 自动建表）：

| 列 | 说明 |
|----|------|
| id | PK |
| obj_type | question / resource / knowledge / solve_item |
| obj_id | 对象 ID |
| note | 收藏备注（可选） |
| create_time | 收藏时间 |

唯一性：同 (obj_type, obj_id) 只一条。题目原有的 `questions.is_favorite`
保留（已有列表筛选体系），与 favorites 表双向同步。

## 接口

| 接口 | 说明 |
|------|------|
| POST /api/favorites/toggle | {obj_type, obj_id, note?} → {favorited} |
| GET /api/favorites?obj_type= | 分页收藏列表（按类型联表取标题/摘要/跳转路径） |
| POST /api/favorites/status | {obj_type, ids:[...]} → {id: bool} 批量星标态 |

展示数据：question→题干截断+答案；resource→标题+sub_path；knowledge/solve→标题+模块。

## 前端

- 新页 `/favorites`（侧栏「复习巩固」组，星形图标）：tab 切换四类，卡片列表点击跳详情
- 资料库/题目详情/知识库/解题库的星标调用统一 toggle 接口
- 资料库原收藏迁移：resources.is_favorite=1 的记录插入 favorites(obj_type=resource)

## 兼容

- 资源库收藏按钮继续可用（toggle 时同步两处）；
- 题目收藏走 favorites 表并同步 questions.is_favorite（列表筛选不受影响）。
