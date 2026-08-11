@echo off
chcp 65001 >nul 2>&1
echo 正在停止 SoulHealth 所有服务...
taskkill /f /fi "WINDOWTITLE eq SoulHealth-Backend" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq SoulHealth-Frontend" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq SoulHealth-Tunnel" >nul 2>&1
taskkill /f /im cloudflared.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1
echo [✓] 所有服务已停止
pause
