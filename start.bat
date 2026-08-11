@echo off
chcp 65001 >nul 2>&1
title SoulHealth AI 中医辨证溯源平台 - 一键启动

echo.
echo ==================================================
echo   SOULHEALTH AI 中医辨证溯源平台 一键启动
echo ==================================================
echo.

:: 1. 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python 已就绪

:: 2. 安装 Python 依赖
echo [*] 正在检查/安装 Python 依赖...
pip install -r requirements.txt -q
echo [OK] Python 依赖已就绪

:: 3. 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)
echo [OK] Node.js 已就绪

:: 4. 检查前端依赖
set "ROOT_DIR=%~dp0"
set "FRONT_DIR=%~dp0soulhealth-frontend-stage1\soulhealth-frontend"

if not exist "%FRONT_DIR%\node_modules" (
    echo [*] 首次运行，正在安装前端依赖 (npm install)...
    pushd "%FRONT_DIR%"
    call npm install
    popd
) else (
    echo [OK] 前端依赖已存在
)

:: 5. 启动后端 (端口 8001)
echo [*] 启动后端服务 (端口 8001)...
start "SoulHealth-Backend" cmd /k "cd /d "%ROOT_DIR%" && python -m uvicorn pipeline:app --host 0.0.0.0 --port 8001"
ping 127.0.0.1 -n 3 >nul
echo [OK] 后端服务已启动: http://localhost:8001

:: 6. 启动前端 (端口 5173)
echo [*] 启动前端服务 (端口 5173)...
start "SoulHealth-Frontend" cmd /k "cd /d "%FRONT_DIR%" && npm run dev"
ping 127.0.0.1 -n 3 >nul
echo [OK] 前端服务已启动: http://localhost:5173

echo.
echo ==================================================
echo   全部服务已启动!
echo   前端访问地址: http://localhost:5173
echo   后端API地址:  http://localhost:8001/health
echo ==================================================
echo.
pause
