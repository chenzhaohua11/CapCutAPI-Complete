@echo off
echo Starting CapCutAPI Docker deployment...
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker is not installed. Please install Docker first.
    pause
    exit /b 1
)

REM 检查Docker Compose是否安装
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM 构建镜像
echo Building Docker image...
docker-compose build
if errorlevel 1 (
    echo Failed to build Docker image
    pause
    exit /b 1
)

REM 启动服务
echo Starting services...
docker-compose up -d
if errorlevel 1 (
    echo Failed to start services
    pause
    exit /b 1
)

REM 等待服务启动
echo Waiting for services to start...
timeout /t 10 /nobreak > nul

REM 检查服务状态
echo Checking service health...
curl -f http://localhost:9001/health >nul 2>&1
if errorlevel 1 (
    echo Service health check failed
    echo Checking logs...
    docker-compose logs
    pause
    exit /b 1
) else (
    echo.
    echo ======================================
    echo SUCCESS! CapCutAPI is running!
    echo ======================================
    echo.
    echo HTTP API: http://localhost:9001
    echo Health Check: http://localhost:9001/health
    echo.
    echo Useful commands:
    echo   docker-compose logs -f    View logs
    echo   docker-compose stop       Stop services
    echo   docker-compose restart    Restart services
    echo   docker-compose down       Stop and remove containers
    echo.
    pause
)