@echo off
title CapCutAPI Windows自动部署脚本
chcp 65001 >nul

echo.
echo ========================================
echo 🚀 CapCutAPI Windows自动部署脚本
echo ========================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ 请以管理员身份运行此脚本
    pause
    exit /b 1
)

REM 设置变量
set PROJECT_DIR=%~dp0
set PYTHON_VERSION=3.9
set SERVICE_PORT=9001

echo 📁 项目目录: %PROJECT_DIR%

REM 检查Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ 未检测到Python，请先安装Python %PYTHON_VERSION%+
    echo 📥 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python环境检测通过

REM 创建虚拟环境
if not exist "venv" (
    echo 🔄 创建虚拟环境...
    python -m venv venv
)

echo ✅ 虚拟环境准备完成

REM 激活虚拟环境
echo 🔄 激活虚拟环境...
call venv\Scripts\activate

REM 安装依赖
echo 🔄 安装Python依赖...
pip install --upgrade pip
pip install -r requirements.txt

if %errorLevel% neq 0 (
    echo ❌ 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)

echo ✅ 依赖安装完成

REM 检查FFmpeg
ffmpeg -version >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️ 未检测到FFmpeg，正在自动安装...
    
    REM 下载FFmpeg
    if not exist "ffmpeg" (
        mkdir ffmpeg
        curl -L -o ffmpeg.zip https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
        tar -xf ffmpeg.zip -C ffmpeg --strip-components=1
        del ffmpeg.zip
    )
    
    REM 添加到PATH
    set PATH=%PROJECT_DIR%ffmpeg\bin;%PATH%
    echo ✅ FFmpeg安装完成
) else (
    echo ✅ FFmpeg已安装
)

REM 创建必要目录
if not exist "drafts" mkdir drafts
if not exist "media" mkdir media
if not exist "logs" mkdir logs
if not exist "config" mkdir config

REM 复制配置文件模板
if not exist "config.json" (
    if exist "config.json.example" (
        copy config.json.example config.json >nul
        echo ✅ 配置文件已创建
    )
)

echo.
echo ========================================
echo 🎉 部署完成！
echo ========================================
echo.
echo 🚀 启动方式:
echo   1. 开发模式: python capcut_server.py
echo   2. 生产模式: python capcut_server.py --production
echo   3. Docker模式: docker-compose up -d

echo.
echo 📡 服务地址:
echo   - HTTP API: http://localhost:%SERVICE_PORT%
echo   - 健康检查: http://localhost:%SERVICE_PORT%/health

echo.
echo 🔧 常用命令:
echo   - 启动服务: start-local.bat

echo.
choice /C YN /M "是否立即启动服务?"
if %errorlevel%==1 (
    echo 🚀 正在启动服务...
    start cmd /k "python capcut_server.py"
)

echo.
echo ✅ 部署脚本执行完成！
pause