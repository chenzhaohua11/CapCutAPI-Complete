#!/bin/bash

# CapCutAPI Linux自动部署脚本
# 支持Ubuntu/Debian/CentOS/RHEL

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "请不要以root用户运行此脚本"
        exit 1
    fi
}

# 检测Linux发行版
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VERSION=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VERSION=$(lsb_release -sr)
    elif [[ -f /etc/redhat-release ]]; then
        OS="CentOS/RHEL"
        VERSION=$(grep -oE '[0-9]+' /etc/redhat-release | head -1)
    else
        OS="Unknown"
        VERSION="Unknown"
    fi
    print_status "检测到系统: $OS $VERSION"
}

# 安装系统依赖
install_system_deps() {
    print_status "安装系统依赖..."
    
    case $OS in
        "Ubuntu"|"Debian"*)
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv ffmpeg curl wget git
            ;;
        "CentOS"|"Red Hat"*)
            sudo yum install -y epel-release
            sudo yum install -y python3 python3-pip python3-venv ffmpeg curl wget git
            ;;
        *)
            print_error "不支持的Linux发行版: $OS"
            exit 1
            ;;
    esac
    
    print_success "系统依赖安装完成"
}

# 检查Python版本
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "未找到Python，请先安装Python 3.8+"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
    print_status "Python版本: $PYTHON_VERSION"
}

# 创建虚拟环境
create_venv() {
    if [[ ! -d "venv" ]]; then
        print_status "创建Python虚拟环境..."
        $PYTHON_CMD -m venv venv
    fi
    print_success "虚拟环境已准备就绪"
}

# 激活虚拟环境
activate_venv() {
    source venv/bin/activate
    print_status "虚拟环境已激活"
}

# 安装Python依赖
install_python_deps() {
    print_status "安装Python依赖..."
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "Python依赖安装完成"
}

# 检查FFmpeg
check_ffmpeg() {
    if command -v ffmpeg &> /dev/null; then
        print_success "FFmpeg已安装"
    else
        print_warning "FFmpeg未安装，将使用系统包管理器安装"
        case $OS in
            "Ubuntu"|"Debian"*)
                sudo apt install -y ffmpeg
                ;;
            "CentOS"|"Red Hat"*)
                sudo yum install -y ffmpeg
                ;;
        esac
    fi
}

# 创建目录结构
create_directories() {
    print_status "创建必要目录..."
    mkdir -p drafts media logs config
    print_success "目录结构创建完成"
}

# 设置配置文件
setup_config() {
    if [[ ! -f "config.json" ]] && [[ -f "config.json.example" ]]; then
        cp config.json.example config.json
        print_success "配置文件已创建"
    fi
}

# 创建systemd服务
create_systemd_service() {
    print_status "创建systemd服务..."
    
    SERVICE_FILE="$HOME/.config/systemd/user/capcut-api.service"
    mkdir -p "$HOME/.config/systemd/user"
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=CapCutAPI Service
After=network.target

[Service]
Type=simple
User=%i
WorkingDirectory=$PWD
Environment=PYTHONPATH=$PWD
ExecStart=$PWD/venv/bin/python capcut_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

    systemctl --user daemon-reload
    print_success "systemd服务已创建"
}

# 主部署函数
main() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}🚀 CapCutAPI Linux自动部署脚本${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    
    check_root
    detect_os
    
    read -p "是否开始部署? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "取消部署"
        exit 0
    fi
    
    install_system_deps
    check_python
    create_venv
    activate_venv
    install_python_deps
    check_ffmpeg
    create_directories
    setup_config
    
    # 询问是否创建systemd服务
    read -p "是否创建systemd服务以便开机自启? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_systemd_service
        print_status "服务管理命令:"
        echo "  启动: systemctl --user start capcut-api"
        echo "  停止: systemctl --user stop capcut-api"
        echo "  状态: systemctl --user status capcut-api"
        echo "  日志: journalctl --user -u capcut-api -f"
    fi
    
    echo
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}🎉 部署完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    echo -e "${BLUE}🚀 启动方式:${NC}"
    echo "  1. 开发模式: source venv/bin/activate && python capcut_server.py"
    echo "  2. 生产模式: source venv/bin/activate && python capcut_server.py --production"
    echo "  3. Docker模式: docker-compose up -d"
    echo
    echo -e "${BLUE}📡 服务地址:${NC}"
    echo "  - HTTP API: http://localhost:9001"
    echo "  - 健康检查: http://localhost:9001/health"
    echo
    
    read -p "是否立即启动服务? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "正在启动服务..."
        source venv/bin/activate
        python capcut_server.py
    fi
    
    print_success "部署脚本执行完成！"
}

# 执行主函数
main "$@"