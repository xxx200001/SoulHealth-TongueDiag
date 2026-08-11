# SoulHealth 前端 · 中医辨证溯源

Vue 3 + Vite + Pinia。设计语言「宣纸墨韵」：墨绿 `#2D5F4B` · 金 `#C9A86C` · 米白 `#F5F0E8`，浅/深双主题。

## 运行

```bash
# 1. 先启动后端
cd d:\桌面\ai2
uvicorn pipeline:app --host 0.0.0.0 --port 8000

# 2. 再启动前端
npm install
npm run dev   # http://localhost:5173
```

`/api` 与 `/health` 已在 `vite.config.js` 中代理到 `localhost:8000`，无需处理跨域。
生产部署时设置环境变量 `VITE_API_BASE` 指向后端地址。

## 交付阶段

| 阶段 | 内容 | 状态 |
|---|---|---|
| 1 | 骨架 / 设计系统 / API层 / 状态管理 / 首页 | ✅ 本包 |
| 2 | 体检上传（25类指标） + 个人信息&用药 | 待交付 |
| 3 | 智能问诊（动态量表） + 舌面诊 | 待交付 |
| 4 | 组方详情页 ⭐（10段结构 / 雷达图 / Markdown / BLOCKED） | 待交付 |
| 5 | 病历时间轴 + 导出 + 收尾 | 待交付 |

## 结构

```
src/
├── api/index.js        # 三个后端接口封装
├── store/patient.js    # 跨页面采集 → full_report 请求体，localStorage 持久化
├── router/index.js     # 7 页面路由（未交付页挂占位组件）
├── styles/theme.css    # 设计令牌 / 双主题 / 共用组件类
├── components/         # AppHeader（在线状态+主题切换）/ BottomNav
└── pages/              # HomePage / PlaceholderPage / …后续阶段追加
```
