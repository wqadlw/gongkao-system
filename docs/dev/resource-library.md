# 设计文档：资料库（行测/公考资料中心）

状态：已实现 | 日期：2026-10-01

## 背景

思维导图（kuriv/civil-service-exam，MIT）此前作为知识卡导入「行测知识库」，
但导图本质是**资料**：有 PNG 预览图、emmx 原文件、层级目录（模块/主题/考点），
与"知识卡"形态不同。另有一批高星公考资料（程序员考公指南等）因无明确开源许可，
适合以**外链**形式收录。因此新开「资料库」页面统一承载。

## 数据模型

新增 `resources` 表（create_all 自动建表）：

| 列 | 说明 |
|----|------|
| id | PK |
| category | 一级分类：行测 / 申论 / 面试 / 经验指南 |
| sub_path | 子路径（模块/主题/考点，`/` 连接） |
| title | 资料名 |
| description | 摘要（导图为一级分支列表） |
| resource_type | `mindmap` / `link` |
| image_path | 预览图相对 `data/resources/` 的路径（导图 PNG） |
| file_path | 原文件相对路径（emmx，可下载） |
| source_url | 来源链接（link 类型必填） |
| source | 来源说明（如 `kuriv/civil-service-exam (MIT)`） |
| create_time | |

## 接口

- `GET /api/resources/categories` — 分类树与计数
- `GET /api/resources/list?category=&keyword=&page=` — 分页列表
- `GET /api/resources/image?path=` — 图片服务（realpath + 限定 `data/resources` 内）
- `GET /api/resources/file?path=` — emmx 等原文件下载（同上校验）
- `POST /api/resources/batch` — 批量导入（脚本产出清单后调用）

## 内容来源

| 来源 | 类型 | 说明 |
|------|------|------|
| kuriv/civil-service-exam（MIT） | mindmap | 51 张导图（行测 5 模块 + 申论 + 面试），PNG 预览 + emmx 下载 |
| coder2gwy/coder2gwy（⭐27.7k，无许可证） | link | 程序员考公指南——仅收录外链不拷贝内容 |
| miss-mumu/developer2gwy（⭐11.3k，许可待查） | link | 公务员入门到上岸教程——仅收录外链 |
| ErrRC/xingcezhenti | link | 已接入的真题仓库（2962 份试卷） |

版权原则：**有明确许可的才复制内容，否则只做外链引用。**

## 前端

新页面 `/resource-library`（侧栏「资料库」分组）：左侧分类列表（含计数），
右侧卡片墙（PNG 缩略图 + 标题 + 路径徽标），点击弹出大图预览与 emmx 下载；
外链资源以独立分组展示来源徽标 + 打开链接。
