# -*- coding: utf-8 -*-
"""
server.py —— SOULHEALTH AI 健康科研平台 统一入口
=====================================================================
融合「中医辨证溯源」(tongue) 与「生物计算」(bio) 两大能力模块，
单进程、单端口提供全部 API 服务。

启动：python server.py
访问：http://127.0.0.1:9000/docs （Swagger）
前端：配合 Vue 前端 npm run dev → http://localhost:5173

API 路由分布：
  /api/v1/*           中医辨证溯源（舌诊/面诊/问诊/全流程报告/OCR）
  /api/auth/*          统一认证（登录/注册/用户管理）
  /api/patients/*      健康档案管理
  /api/documents/*     文档上传/视觉抽取
  /api/analyze         AI Agent 分析
  /api/admin/*         管理员操作
  /api/health          运行状态
"""
import os
import sys
import uvicorn

# 确保项目根目录在 sys.path 中
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ── 导入 bio 平台的 FastAPI app（主体）──
from app.main import app

# ── 导入 tongue 路由并挂载到 /api/v1 前缀 ──
from tongue_router import router as tongue_router
app.include_router(tongue_router, prefix="/api/v1")

# ── 更新应用标题 ──
app.title = "SOULHEALTH AI 健康科研平台"
app.version = "1.0.0-dev"

if __name__ == "__main__":
    host = os.getenv("SOULHEALTH_HOST", "0.0.0.0")
    port = int(os.getenv("SOULHEALTH_PORT", "9000"))
    print(f"\n{'='*60}")
    print(f"  SOULHEALTH AI 健康科研平台 — 统一服务")
    print(f"  后端 API:  http://127.0.0.1:{port}/docs")
    print(f"  前端访问:  http://localhost:5173  (Vite dev server)")
    print(f"{'='*60}\n")
    uvicorn.run("server:app", host=host, port=port, reload=False)
