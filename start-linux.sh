#!/bin/bash

# CapCutAPI Linux一键启动脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}🚀 正在启动CapCutAPI服务...${NC}"

# 检查虚拟环境
if [[ ! -d "venv" ]]; then
    echo -e "${BLUE}📦 虚拟环境不存在，开始部署...${NC}"
    chmod +x deploy-linux.sh
    ./deploy-linux.sh
fi

# 激活虚拟环境
source venv/bin/activate

# 检查配置文件
if [[ ! -f "config.json" ]] && [[ -f "config.json.example" ]]; then
    cp config.json.example config.json
    echo -e "${GREEN}✅ 配置文件已创建${NC}"
fi

# 创建必要目录
mkdir -p drafts media logs

# 启动服务
echo -e "${BLUE}🌐 服务即将在 http://localhost:9001 启动${NC}"
echo -e "${BLUE}📊 健康检查: http://localhost:9001/health${NC}"
echo -e "${BLUE}📝 日志文件: logs/capcut.log${NC}"
echo

python capcut_server.py