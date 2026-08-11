# SoulHealth AI 中医辨证溯源平台

## 🚀 快速部署（3 步完成）

### 前提条件
在目标电脑上需要预装：
1. **Python 3.10+**：[下载](https://python.org/downloads/) — 安装时勾选 "Add to PATH"
2. **Node.js 18+**：[下载](https://nodejs.org/) — 选 LTS 版本
3. **cloudflared**（可选，用于公网穿透）：[下载](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)

### 一键启动
```
双击 start.bat
```
脚本会自动完成：
- ✅ 检查 Python / Node.js 环境
- ✅ 安装 Python 后端依赖（`pip install -r requirements.txt`）
- ✅ 安装前端依赖（首次会 `npm install`）
- ✅ 启动后端 API 服务（端口 8000）
- ✅ 启动前端 Web 服务（端口 5173）
- ✅ 自动开启 Cloudflare 公网穿透（如已安装 cloudflared）

启动完成后浏览器访问：**http://localhost:5173**

### 停止服务
```
双击 stop.bat
```

---

## 📁 项目结构
```
ai2/
├── start.bat                 ← 一键启动（双击即可）
├── stop.bat                  ← 一键停止
├── requirements.txt          ← Python 依赖清单
├── pipeline.py               ← 后端主入口 (FastAPI)
├── auth_module.py            ← JWT 认证模块
├── consultation_engine.py    ← 智能问诊引擎
├── drug_interaction.py       ← 中西药冲突检测
├── lab_indicator_mapper.py   ← 体检指标分级
├── lifestyle_advisor.py      ← 生活方式建议
├── medical_record.py         ← 病历管理
├── toxicology_report.py      ← 毒理学报告
├── users.db                  ← 用户数据库 (SQLite, 自动创建)
└── soulhealth-frontend-stage1/
    └── soulhealth-frontend/  ← Vue 3 前端
        ├── package.json
        ├── vite.config.js
        └── src/
```

## ⚙️ 手动启动（如果 bat 脚本不适用）

**终端 1 — 后端：**
```bash
cd ai2
pip install -r requirements.txt
python -m uvicorn pipeline:app --host 0.0.0.0 --port 8000
```

**终端 2 — 前端：**
```bash
cd ai2/soulhealth-frontend-stage1/soulhealth-frontend
npm install    # 首次需要
npm run dev
```

**终端 3 — 公网穿透（可选）：**
```bash
cloudflared tunnel --url http://localhost:5173
```

## 🔑 默认配置
- 后端端口：`8000`
- 前端端口：`5173`
- JWT 密钥：可通过环境变量 `JWT_SECRET` 自定义
- AI OCR 密钥：可通过环境变量 `ANTHROPIC_API_KEY` 自定义
