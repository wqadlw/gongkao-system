# 公考行测个人结构化知识库系统 v2.0

> **纯本地离线 · JSON结构化解析 · 零AI联网 · 个人备考仓库**

## v2.0 核心升级

- 🚀 **JSON结构化解析**：AI返回JSON代码，系统直接解析，零字段填写
- 🎯 **极简录入流程**：选考点→复制提示词→粘贴JSON→入库，4步完成
- 🧹 **考点树优化**：删除"全部"冗余节点，直接展开题型
- 📓 **备考笔记追问**：支持AI二次生成结构化笔记
- 🎨 **现代UI设计**：明暗双主题，高级视觉体验
- ⏰ **公考倒计时**：国考/省考倒计时，备考阶段建议
- 📊 **18个结构化字段**：新增细分考点/考察意图/难度标签/考场优先级

## 快速开始

### Windows
1. 解压压缩包
2. 双击 `install.bat`（首次安装）
3. 双击 `start.bat` 启动
4. 浏览器访问 `http://localhost:7080`

### Linux/Mac
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && npm run build && cd ..
./start.sh
```

## 使用流程

```
粉笔APP刷题截图 → 系统选考点复制提示词 → 
外部AI粘贴提示词+发截图 → AI返回JSON → 
系统粘贴JSON自动解析入库 → 复习/复盘/统计
```

## 目录结构

```
gongkao-system-v2/
├── backend/              # FastAPI后端
│   ├── main.py          # 入口
│   ├── database.py      # 数据库模型（含ExamCountdown）
│   ├── routers/         # API路由（8个模块）
│   ├── services/        # 业务逻辑（解析器/复习引擎/统计）
│   └── requirements.txt
├── frontend/            # Vue3前端
│   ├── src/
│   │   ├── views/       # 14个页面
│   │   ├── api/         # API封装
│   │   ├── stores/      # Pinia
│   │   ├── router/      # 路由
│   │   └── styles/      # 现代设计系统
│   └── dist/            # 构建产物
├── data/                # 数据目录
├── docs/                # 文档
├── install.bat          # 首次安装
├── start.bat            # 一键启动
├── stop.bat             # 停止
└── backup.bat           # 备份
```

详细使用说明请阅读 `docs/使用指南.md`
