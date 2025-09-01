#!/bin/bash

# CapCutAPI Docker启动脚本
# 支持自动重启和优雅关闭

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting CapCutAPI Docker deployment...${NC}"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# 构建镜像
echo -e "${YELLOW}Building Docker image...${NC}"
docker-compose build

# 启动服务
echo -e "${YELLOW}Starting services...${NC}"
docker-compose up -d

# 等待服务启动
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# 检查服务状态
echo -e "${YELLOW}Checking service health...${NC}"
if curl -f http://localhost:9001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ CapCutAPI is running successfully!${NC}"
    echo -e "${GREEN}  HTTP API: http://localhost:9001${NC}"
    echo -e "${GREEN}  Health Check: http://localhost:9001/health${NC}"
else
    echo -e "${RED}✗ Service health check failed${NC}"
    echo -e "${YELLOW}Checking logs...${NC}"
    docker-compose logs
    exit 1
fi

echo -e "${GREEN}Deployment completed!${NC}"
echo ""
echo "Useful commands:"
echo "  docker-compose logs -f    # View logs"
echo "  docker-compose stop       # Stop services"
echo "  docker-compose restart    # Restart services"
echo "  docker-compose down       # Stop and remove containers"