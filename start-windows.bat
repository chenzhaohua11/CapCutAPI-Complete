@echo off
title CapCutAPI 一键启动
cd /d "%~dp0"

echo 🚀 正在启动CapCutAPI服务...

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 虚拟环境不存在，开始部署...
    call deploy-windows.bat
    if %errorlevel% neq 0 (
        echo ❌ 部署失败
        pause
        exit /b 1
    )
)

REM 激活虚拟环境
call venv\Scripts\activate

REM 检查配置文件
if not exist "config.json" (
    if exist "config.json.example" (
        copy config.json.example config.json >nul
        echo ✅ 配置文件已创建
    )
)

REM 创建必要目录
if not exist "drafts" mkdir drafts
if not exist "media" mkdir media
if not exist "logs" mkdir logs

REM 启动服务
echo 🌐 服务即将在 http://localhost:9001 启动
echo 📊 健康检查: http://localhost:9001/health
echo 📝 日志文件: logs\capcut.log
echo.

python capcut_server.py

if %errorlevel% neq 0 (
    echo ❌ 服务启动失败，请检查日志
    pause
) else (
    echo ✅ 服务已启动
)