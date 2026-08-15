@echo off
chcp 65001 >nul

echo ========================================
echo  SOULHEALTH AI 健康科研平台 — 一键启动
echo  后端: http://127.0.0.1:9000/docs
echo  前端: http://localhost:5173
echo ========================================

REM — 启动后端 —
echo [1/2] 启动后端 server.py (端口 9000) ...
start "SOULHEALTH-Backend" cmd /c "cd /d %~dp0 && python server.py"

REM — 等待后端就绪 —
ping 127.0.0.1 -n 3 >nul

REM — 启动前端 —
echo [2/2] 启动前端 Vite dev server (端口 5173) ...
start "SOULHEALTH-Frontend" cmd /c "cd /d %~dp0soulhealth-frontend-stage1\soulhealth-frontend && npm run dev"

echo.
echo 两个服务已在后台启动，关闭此窗口不影响运行。
echo 浏览器访问 http://localhost:5173
echo.
pause
