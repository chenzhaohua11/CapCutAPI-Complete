# CapCutAPI 部署指南

## 项目概述

CapCutAPI 是一个强大的云端剪辑API，提供对标剪映/CapCut的剪辑能力，支持视频、音频、图片、文本等多种媒体处理功能。

## 系统要求

- Python 3.10+
- FFmpeg
- Docker & Docker Compose (用于容器化部署)

## 本地部署

### 1. 环境准备

```bash
# 安装Python 3.10+ (推荐使用Anaconda或pyenv)
# 安装FFmpeg
# Windows: 下载安装包并添加到PATH
# macOS: brew install ffmpeg
# Linux: sudo apt-get install ffmpeg
```

### 2. 项目克隆与依赖安装

```bash
# 克隆项目
git clone https://github.com/sun-guannan/CapCutAPI.git
cd CapCutAPI

# 创建虚拟环境
python -m venv venv-capcut

# 激活虚拟环境
# Windows:
venv-capcut\Scripts\activate
# macOS/Linux:
source venv-capcut/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-mcp.txt  # 可选，MCP协议支持
```

### 3. 配置文件

```bash
# 复制配置文件模板
cp config.json.example config.json

# 编辑配置文件
# 主要配置项：
# - is_capcut_env: 是否使用CapCut环境(true)或剪映环境(false)
# - port: 服务端口，默认9001
# - draft_domain: 草稿操作的基础域名
```

### 4. 启动服务

```bash
# 启动HTTP API服务器 (端口9001)
python capcut_server.py

# 启动MCP协议服务 (支持stdio通信)
python mcp_server.py

# 测试服务
python test_mcp_client.py
```

## Docker部署

### 1. 快速启动

```bash
# 构建并启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f capcut-api
```

### 2. 使用Nginx反向代理

```bash
# 使用nginx作为反向代理启动
docker-compose --profile with-nginx up -d

# 访问地址：http://localhost
```

### 3. 自定义配置

```bash
# 编辑docker-compose.yml
# 可以修改：
# - 端口映射
# - 卷挂载
# - 环境变量

# 重新部署
docker-compose down
docker-compose up -d
```

### 4. 数据持久化

Docker容器中的以下数据会被持久化：
- `./config.json:/app/config.json` - 配置文件
- `./drafts:/app/drafts` - 草稿文件
- `./media:/app/media` - 媒体文件

## 验证部署

### 1. 健康检查

```bash
# 检查HTTP API服务
curl http://localhost:9001/health

# 预期返回：
# {
#   "status": "healthy",
#   "timestamp": "2024-01-01T12:00:00",
#   "service": "capcut-api",
#   "version": "1.0.0"
# }
```

### 2. MCP连接测试

```bash
# 测试MCP连接
python test_mcp_client.py

# 预期输出：
# ✅ MCP 服务器启动成功
# ✅ 获取到 11 个可用工具
# ✅ 草稿创建测试通过
```

### 3. API测试

```bash
# 测试创建草稿
curl -X POST http://localhost:9001/create_draft \
  -H "Content-Type: application/json" \
  -d '{"width": 1080, "height": 1920}'
```

## 生产环境部署

### 1. 环境变量配置

创建 `.env` 文件：

```bash
# 服务配置
PORT=9001
DEBUG=0
PYTHONPATH=/app

# OSS配置（可选）
OSS_BUCKET_NAME=your-bucket
OSS_ACCESS_KEY_ID=your-key-id
OSS_ACCESS_KEY_SECRET=your-secret
OSS_ENDPOINT=https://your-endpoint
```

### 2. 使用Docker Swarm

```bash
# 初始化Swarm
docker swarm init

# 部署服务
docker stack deploy -c docker-compose.yml capcut-api

# 查看服务
docker service ls
```

### 3. 使用Kubernetes

```bash
# 应用配置
kubectl apply -f k8s/

# 查看状态
kubectl get pods
kubectl get services
```

## 故障排除

### 1. 端口冲突

```bash
# 检查端口占用
netstat -tulnp | grep 9001

# 修改docker-compose.yml中的端口映射
ports:
  - "9002:9001"  # 映射到主机的9002端口
```

### 2. 权限问题

```bash
# 修复文件权限
sudo chown -R $USER:$USER ./drafts ./media

# Docker权限
sudo usermod -aG docker $USER
```

### 3. 内存不足

```bash
# 检查资源限制
docker stats

# 增加内存限制
docker-compose.yml:
services:
  capcut-api:
    deploy:
      resources:
        limits:
          memory: 2G
```

## 监控与日志

### 1. 日志查看

```bash
# Docker日志
docker-compose logs -f capcut-api

# 系统日志
journalctl -u docker.service
```

### 2. 性能监控

```bash
# 使用Prometheus + Grafana
# 查看docker-compose-with-monitoring.yml
```

## 更新部署

### 1. 更新代码

```bash
# 拉取最新代码
git pull origin main

# 重新构建
docker-compose build --no-cache

# 重启服务
docker-compose up -d
```

### 2. 零停机更新

```bash
# 使用滚动更新
docker-compose up -d --no-deps capcut-api
```

## 安全建议

1. **网络隔离**: 使用Docker网络隔离
2. **访问控制**: 配置防火墙规则
3. **数据加密**: 敏感数据使用环境变量
4. **定期更新**: 保持镜像和依赖更新
5. **监控告警**: 设置健康检查告警

## 支持

如有问题，请查看：
- [项目GitHub](https://github.com/sun-guannan/CapCutAPI)
- [中文文档](README-zh.md)
- [MCP文档](MCP_文档_中文.md)