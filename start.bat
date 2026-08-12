@echo off
chcp 65001 >nul 2>&1
title SoulHealth AI - 一键启动

echo.
echo ==================================================
echo   SOULHEALTH AI 中医辨证溯源平台 一键启动
echo ==================================================
echo.

:: 1. 检查 Python
python --version >nul 2>&1
if errorlevel 1 goto NO_PYTHON
echo [OK] Python 已就绪
goto CHECK_PIP

:NO_PYTHON
echo [错误] 未检测到 Python，请先安装 Python 3.10+
echo        下载地址: https://www.python.org/downloads/
echo        安装时务必勾选 Add Python to PATH
pause
exit /b 1

:CHECK_PIP
:: 2. 安装 Python 依赖
echo [*] 正在检查/安装 Python 依赖...
pip install -r "%~dp0requirements.txt" -q 2>nul
echo [OK] Python 依赖已就绪

:: 3. 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 goto NO_NODE
echo [OK] Node.js 已就绪
goto CHECK_FRONTEND

:NO_NODE
echo [错误] 未检测到 Node.js，请先安装 Node.js 18+
echo        下载地址: https://nodejs.org/
pause
exit /b 1

:CHECK_FRONTEND
:: 4. 检查前端依赖
if exist "%~dp0soulhealth-frontend-stage1\soulhealth-frontend\node_modules" goto FRONTEND_READY
echo [*] 首次运行，正在安装前端依赖 (npm install)...
pushd "%~dp0soulhealth-frontend-stage1\soulhealth-frontend"
call npm install
popd
goto START_BACKEND

:FRONTEND_READY
echo [OK] 前端依赖已存在

:START_BACKEND
:: 5. 启动后端 (端口 8001)
echo [*] 启动后端服务 (端口 8001)...
start "SoulHealth-Backend" /D "%~dp0." cmd /k "set PYTHONIOENCODING=utf-8 & python -m uvicorn pipeline:app --host 0.0.0.0 --port 8001"
ping 127.0.0.1 -n 4 >nul
echo [OK] 后端服务已启动: http://localhost:8001

:: 6. 启动前端 (端口 5173)
echo [*] 启动前端服务 (端口 5173)...
start "SoulHealth-Frontend" /D "%~dp0soulhealth-frontend-stage1\soulhealth-frontend" cmd /k "npm run dev"
ping 127.0.0.1 -n 4 >nul
echo [OK] 前端服务已启动: http://localhost:5173

echo.
echo ==================================================
echo   全部服务已启动!
echo   前端访问地址: http://localhost:5173
echo   后端API地址:  http://localhost:8001/health
echo ==================================================
echo.
echo   关闭本窗口不影响已启动的后端和前端。
echo   如需停止全部服务，请运行 stop.bat
echo.
pause
