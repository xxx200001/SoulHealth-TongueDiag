@echo off
chcp 65001 >nul 2>&1
title SoulHealth TongueDiag - 一键公网穿透

echo.
echo ==================================================
echo   SoulHealth 舌苔诊平台 - 开启公网临时穿透
echo ==================================================
echo.
echo [*] 正在开启公网访问 (端口 5173)...
echo [*] 稍后终端中输出的 https://xxxx.trycloudflare.com 即为公网链接
echo.

npx cloudflared tunnel --url http://localhost:5173
pause
