<div align="center">

<img src="frontend/public/favicon.svg" width="72" alt="logo" />

# 公考行测个人结构化知识库系统

**纯本地离线 · FSRS 记忆调度 · 真题库对接 · 零 AI 联网**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![Element Plus](https://img.shields.io/badge/Element_Plus-2.4-409EFF?logo=element&logoColor=white)](https://element-plus.org/)

一套**完全本地、离线运行**的公务员考试（行测）个人结构化备考系统：把外部 AI 生成的结构化解析一键入库，
配合 **FSRS 科学复习**、**2962 份历年真题**、知识库/解题库沉淀与可视化复盘，全程不做任何 AI 联网调用。

[快速开始](#-快速开始) · [界面预览](#-界面预览) · [核心特性](#-核心特性) · [复习算法](#-复习算法-fsrs) · [参与贡献](#-参与贡献)

</div>

---

## 🖼 界面预览

| 首页看板 | 真题库对接 |
| --- | --- |
| ![首页看板](docs/screenshots/dashboard.jpg) | ![真题库对接](docs/screenshots/question-bank.jpg) |
| **智能复习（FSRS 刷卡 + 快捷键）** | **可视化大屏** |
| ![智能复习](docs/screenshots/review.jpg) | ![可视化大屏](docs/screenshots/visualization.jpg) |
| **题目录入** | **行测知识库** |
| ![题目录入](docs/screenshots/question-input.jpg) | ![行测知识库](docs/screenshots/knowledge.jpg) |

> 更多截图见 [docs/screenshots](docs/screenshots/README.md)。

## ✨ 核心特性

### 📚 真题库对接（v2.1 新增）
- 一键克隆并接入 [ERRRC/xingcezhenti](https://github.com/ERRRC/xingcezhenti)：**2016-2026 国考+省考 2962 份试卷、58890+ 道题**
- 按六大模块浏览试卷 → 勾选题目 → 选择考点路径 → 批量入库，按题目 qid 自动去重
- 题目图片（公式图/题目图）经本地媒体接口代理，浏览时直接渲染
- **通用数据集导入**：C-Eval 等公开数据集（JSON/CSV/Parquet）放入 `data/question_sources/` 即可识别入库

### 🧠 FSRS 科学复习（v2.1 新增）
- 接入 [FSRS 记忆调度算法](https://github.com/open-spaced-repetition/py-fsrs)（Anki 同款），按每题独立的稳定性/难度动态安排复习时间
- 沉浸式刷卡界面：空格翻面、`1/2/3/4` 评分，提交后即时反馈下次复习时间
- 未安装 fsrs 库时自动回退经典艾宾浩斯固定周期

### 📤 Anki 牌组导出（v2.1 新增）
- 一键把题库导出为 `.apkg`（题面 / 答案 / 解析 / 考点标签，公式图自动打包）
- 手机安装 AnkiDroid 即可随时随地刷自己的题库

### 📝 极简结构化录入
- 选考点 → 复制内置提示词 → 粘贴给外部 AI（截图 + 提示词）→ 粘贴回 JSON → 自动解析入库
- 18 个结构化字段：细分考点、考察意图、破题逻辑、陷阱标注、速算技巧、卡片摘要……

### 🗂 知识沉淀体系
- **行测知识库**：概念 / 公式 / 技巧 / 陷阱 / 易混点，按考点路径归档可检索
- **行测解题库**：解题方法 / 速算技巧 / 易错提醒模板，与题目考点联动
- **备考笔记**：AI 二次生成结构化笔记，题型判定 / 逻辑链 / 速解一步到位

### 📊 复盘与规划
- 六大模块雷达图、错题分布、录入趋势、学习热力图、薄弱考点 TOP5
- 国考 / 省考倒计时、备考阶段管理、错题本与错因标注
- SQLite 单文件存储，一键备份 / JSON 全量导出

### 🎨 现代界面
- Element Plus 组件 + 自建设计系统，**明暗双主题**、全站统一图标、入场动画
- 侧栏分组导航、全局搜索、真题库侧栏浮动跟随

## 🚀 快速开始

### Windows（推荐）

```bash
git clone https://github.com/wqadlw/gongkao-system.git
cd gongkao-system
```

1. 双击 `install.bat`（首次安装，自动创建 venv 并安装依赖）
2. 双击 `start.bat` 启动
3. 浏览器访问 **http://localhost:7080**

### Linux / macOS

```bash
git clone https://github.com/wqadlw/gongkao-system.git
cd gongkao-system
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && npm run build && cd ..
./start.sh
```

### 可选：启用真题库

```bash
# 项目根目录下克隆真题仓库（约 214MB）
git clone https://github.com/ERRRC/xingcezhenti.git
# 重启后端，侧栏「真题库对接」即自动识别
```

启用 FSRS 只需 `pip install fsrs`（已包含在 requirements.txt 中），无需额外配置。

## 🧠 复习算法 FSRS

系统使用 [FSRS（Free Spaced Repetition Scheduler）](https://github.com/open-spaced-repetition/py-fsrs)调度复习：
基于 DSR 记忆模型（Difficulty / Stability / Retrievability），每道题拥有独立的记忆状态，
答错会压缩间隔、连续答对按遗忘曲线科学拉长周期，相比固定周期显著减少无效复习。
学习期步长 1/10 分钟，目标记忆保持率默认 90%。

## 📁 项目结构

```
gongkao-system/
├── backend/               # FastAPI 后端
│   ├── main.py            # 入口（端口 7080）
│   ├── database.py        # SQLAlchemy 模型（12 张表）
│   ├── routers/           # 题目/复习/真题库/Anki/统计/备份… 13 个路由模块
│   └── services/          # FSRS 引擎 / 真题解析 / 数据集导入 / 统计引擎
├── frontend/              # Vue 3 + Element Plus + ECharts 前端
│   └── src/views/         # 17 个页面
├── data/                  # SQLite 数据库（gitignore，本地生成）
│   └── question_sources/  # 可选：第三方数据集放入此目录
├── docs/                  # 文档与截图
├── install.bat / start.bat / start.sh
└── xingcezhenti/          # 可选：真题仓库克隆（gitignore）
```

## 🗺 Roadmap

- [ ] 模考模式：限时整卷答题 + 答题卡 + 按模块计分
- [ ] 更多公开数据集适配（Xiezhi 等）
- [ ] FSRS 参数按个人复习记录优化

## 🤝 参与贡献

Issue / PR 均欢迎！开发调试：

```bash
cd backend && python -m uvicorn main:app --reload --port 7080
cd frontend && npm run dev
```

## 📄 许可证

[MIT](LICENSE) —— 题目数据版权归原仓库 [ERRRC/xingcezhenti](https://github.com/ERRRC/xingcezhenti) 及相应出题机构所有，仅供个人学习使用。

---

<div align="center">

**如果这个项目对你备考有帮助，欢迎点一个 ⭐**

</div>
