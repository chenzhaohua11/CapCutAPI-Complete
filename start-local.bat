@echo off
echo Starting CapCutAPI locally...
echo.

REM 检查Python版本
python --version
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM 创建虚拟环境（如果不存在）
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM 激活虚拟环境
echo Activating virtual environment...
call venv\Scripts\activate

REM 安装依赖
echo Installing dependencies...
pip install -r requirements.txt
pip install -r requirements-mcp.txt

REM 复制配置文件（如果不存在）
if not exist "config.json" (
    echo Creating config.json from example...
    copy config.json.example config.json
)

REM 创建必要的目录
if not exist "drafts" mkdir drafts
if not exist "media" mkdir media
if not exist "logs" mkdir logs

echo.
echo Starting HTTP API server on port 9001...
start "CapCut HTTP API" cmd /k "python capcut_server.py"

timeout /t 2

echo.
echo Starting MCP server...
start "CapCut MCP Server" cmd /k "python mcp_server.py"

echo.
echo Services started!
echo HTTP API: http://localhost:9001
echo Health Check: http://localhost:9001/health
echo.
echo Press any key to exit...
pause > nul