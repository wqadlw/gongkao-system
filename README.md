# 公考行测个人结构化知识库系统 v2.0

> **纯本地离线 · Markdown 结构化解析 · 零 AI 联网 · 个人备考仓库**

一个**完全本地、离线**的公务员考试（行测）个人结构化备考系统。你只需把外部 AI 工具生成的**结构化解析文本**粘贴进来，系统即可自动解析为结构化题库、行测知识库与解题库，支撑错题复盘、艾宾浩斯复习、备考笔记与可视化统计。**系统不做任何 AI 联网调用，AI 完全解耦。**

---

## ✨ 核心特性

- 🧩 **七大模块驱动**：政治理论 / 常识判断 / 言语理解与表达 / 数量关系 / 判断推理 / 资料分析；按性质分为「记忆积累型」与「解题思路型」两类，贯穿提示词、录入、知识沉淀与统计。
- 📥 **极简三步录入**：① 选考点复制提示词 → ② 粘贴 AI 返回的结构化文本 → ③ 解析预览 / 校正考点 / 确认入库。
- 📚 **行测知识库**：独立知识卡片，按「模块 / 类型 / 考点」三维导航；含考点定位面包屑与「来源题目」一键溯源。
- 🛠️ **行测解题库**：可复用的解题模板（破题逻辑 / 易错提醒 / 解题方法 / 速算技巧 / 题型识别）。
- 🗂️ **题库与详情**：按题型树分类、错题 / 掌握度筛选；题目详情展示 18 个结构化字段。
- 📝 **备考笔记**：支持 AI 追问生成结构化笔记，卡片内完整展示题干与选项。
- 🔁 **智能复习**：艾宾浩斯复习算法（公考适配版）、沉浸式复习模式、4 档反馈。
- 📊 **可视化大屏**：雷达图（模块掌握度）、趋势图、错题分布饼图、学习日历热力图。
- 💾 **纯本地数据**：SQLite 单文件存储，可一键备份 / 导出 Markdown 与 JSON。

---

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus + Pinia + vue-echarts |
| 后端 | Python FastAPI + SQLAlchemy |
| 数据库 | SQLite（单文件，`data/gongkao.db`） |
| 解析引擎 | 本地 **Markdown（`####` 分节）优先** + JSON 兜底，零联网 |
| 部署 | 后端直接托管构建后的前端（`frontend/dist`），单进程即可运行 |

---

## 📁 目录结构

```
gongkao-system-v2/
├── backend/                 # FastAPI 后端
│   ├── main.py              # 入口（同时托管前端 dist）
│   ├── database.py          # 数据库模型与迁移
│   ├── routers/             # API 路由（题目/提示词/笔记/复习/统计/知识库/解题库…）
│   ├── services/            # 业务逻辑（Markdown 解析器 / 复习引擎 / 统计）
│   └── requirements.txt
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── views/           # 页面
│   │   ├── api/             # API 封装
│   │   ├── stores/          # Pinia 状态
│   │   ├── router/          # 路由
│   │   └── utils/           # 模块常量（单一事实源）
│   └── dist/                # 构建产物（git 忽略）
├── data/                    # 本地数据目录（git 忽略，仅保留 .gitkeep）
├── docs/                    # 使用指南等文档
├── .github/workflows/       # CI（后端导入检查 + 前端构建）
├── install.bat / start.bat / stop.bat   # Windows 一键脚本
├── start.sh / restart_backend.sh       # Linux / macOS 脚本
├── .gitignore / .editorconfig / .gitattributes / .python-version
├── LICENSE                  # MIT
└── README.md
```

---

## 🚀 快速开始

### Windows
1. 双击 `install.bat`（首次：创建虚拟环境 + 安装依赖 + 构建前端）
2. 双击 `start.bat` 启动
3. 浏览器访问 `http://localhost:7080`

### Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && npm run build && cd ..
./start.sh
```

---

## 🔄 使用流程

```
粉笔 APP 刷题截图 → 系统选考点并复制提示词 →
外部 AI 粘贴提示词 + 发送截图 → AI 返回「带 #### 分节的结构化 Markdown」→
系统粘贴 AI 返回 → 解析预览 → 校正考点 → 确认入库 → 复习 / 复盘 / 统计
```

> 提示词模板要求 AI 以 `#### 一、…` `#### 二、…` 的结构化 Markdown 输出；系统按分节解析，未识别到分节时自动尝试 JSON 兜底。

---

## 🔒 数据与隐私

- 所有数据保存在本地 `data/gongkao.db`（SQLite），**不联网、不上传、无遥测**。
- `data/` 目录已被 `.gitignore` 忽略，**你的数据库与导出文件不会被提交到仓库**。
- 迁移 / 备份：直接复制整个项目目录或仅 `data/gongkao.db` 即可。

---

## 🧑‍💻 开发

- 后端运行：`cd backend && python main.py`（默认 `http://127.0.0.1:7080`）
- 前端开发：`cd frontend && npm run dev`（Vite 开发服务器 `:3000`，`/api` 代理到 `:7080`）
- 前端构建：`cd frontend && npm run build` → 输出到 `frontend/dist/`
- 质量保障：`.github/workflows/ci.yml` 在每次 push/PR 验证后端可导入 + 前端可构建。

---

## 📄 许可证

[MIT](./LICENSE) © 2026 Name67
