@echo off
chcp 65001 >nul 2>&1
title SoulHealth AI 中医辨证溯源平台 - 一键启动
color 0A

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   SOULHEALTH AI  中医辨证溯源平台  一键启动     ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ─────────── 1. 检查 Python ───────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+ 并添加到 PATH
    echo        下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [✓] Python 已就绪

:: ─────────── 2. 安装 Python 依赖 ───────────
echo [*] 正在检查/安装 Python 依赖...
pip install -r requirements.txt -q 2>nul
if %errorlevel% neq 0 (
    echo [!] pip install 出现警告，尝试继续...
)
echo [✓] Python 依赖已就绪

:: ─────────── 3. 检查 Node.js ───────────
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Node.js，请先安装 Node.js 18+ 并添加到 PATH
    echo        下载地址: https://nodejs.org/
    pause
    exit /b 1
)
echo [✓] Node.js 已就绪

:: ─────────── 4. 安装前端依赖 ───────────
if not exist "soulhealth-frontend-stage1\soulhealth-frontend\node_modules" (
    echo [*] 首次运行，正在安装前端依赖 (npm install)...
    cd soulhealth-frontend-stage1\soulhealth-frontend
    call npm install
    cd ..\..
) else (
    echo [✓] 前端依赖已存在
)

:: ─────────── 5. 启动后端 (端口 8000) ───────────
echo [*] 启动后端服务 (端口 8001)...
start /b cmd /c "title SoulHealth-Backend && cd /d %~dp0 && set PYTHONIOENCODING=utf-8 && python -m uvicorn pipeline:app --host 0.0.0.0 --port 8001"
timeout /t 2 /nobreak >nul
echo [✓] 后端服务已启动: http://localhost:8001

:: ─────────── 6. 启动前端 (端口 5173) ───────────
echo [*] 启动前端服务 (端口 5173)...
start /b cmd /c "title SoulHealth-Frontend && cd /d %~dp0\soulhealth-frontend-stage1\soulhealth-frontend && npm run dev"
timeout /t 3 /nobreak >nul
echo [✓] 前端服务已启动: http://localhost:5173

:: ─────────── 7. 内网穿透 (可选) ───────────
where cloudflared >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] 检测到 cloudflared，正在开启公网穿透...
    start /b cmd /c "title SoulHealth-Tunnel && cloudflared tunnel --url http://localhost:5173 2>&1 | findstr /C:trycloudflare.com"
    timeout /t 8 /nobreak >nul
    echo [✓] 公网穿透已启动 (URL 见弹出窗口)
) else (
    echo [i] 未安装 cloudflared，跳过公网穿透
    echo     如需外网访问，请安装: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
)

echo.
echo  ┌──────────────────────────────────────────────────┐
echo  │  全部服务已启动!                                 │
echo  │                                                  │
echo  │  本地访问: http://localhost:5173                  │
echo  │  后端API:  http://localhost:8001/health           │
echo  │                                                  │
echo  │  关闭此窗口将停止所有服务                        │
echo  └──────────────────────────────────────────────────┘
echo.
pause
:: 关闭时杀掉所有子进程
taskkill /f /fi "WINDOWTITLE eq SoulHealth-Backend" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq SoulHealth-Frontend" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq SoulHealth-Tunnel" >nul 2>&1
