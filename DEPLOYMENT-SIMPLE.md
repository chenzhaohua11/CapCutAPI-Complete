# CapCutAPI 精简部署指南

## 🎯 部署目标

本指南提供Windows和Linux系统的快速部署方案，去除冗余功能，专注于核心视频编辑API服务。

## 📋 系统要求

### Windows
- Windows 10 或更高版本
- Python 3.8+ 
- 2GB RAM
- 1GB 磁盘空间

### Linux
- Ubuntu 18.04+ / CentOS 7+
- Python 3.8+
- 2GB RAM
- 1GB 磁盘空间

## 🚀 一键部署

### Windows部署

#### 方式1：自动部署脚本
```batch
# 双击运行
deploy-windows.bat

# 或者一键启动
start-windows.bat
```

#### 方式2：手动部署
```batch
# 1. 安装Python 3.8+
# 2. 运行命令
python -m venv venv
venv\Scripts\activate
pip install -r requirements-simple.txt
python capcut_server.py
```

### Linux部署

#### 方式1：自动部署脚本
```bash
# 一键部署
chmod +x deploy-linux.sh
./deploy-linux.sh

# 一键启动
chmod +x start-linux.sh
./start-linux.sh
```

#### 方式2：手动部署
```bash
# 1. 安装依赖
sudo apt update && sudo apt install -y python3 python3-pip ffmpeg
# 或
sudo yum install -y python3 python3-pip ffmpeg

# 2. 部署项目
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-simple.txt
python capcut_server.py
```

## 🐳 Docker部署（可选）

### 快速启动
```bash
# 使用精简配置
docker-compose -f docker-compose-simple.yml up -d

# 停止服务
docker-compose -f docker-compose-simple.yml down
```

### 手动构建
```bash
docker build -t capcut-api .
docker run -p 9001:9001 capcut-api
```

## 📁 项目结构（精简版）

```
CapCutAPI/
├── capcut_server.py          # 主服务
├── create_draft.py          # 草稿管理
├── add_video_track.py       # 视频处理
├── add_audio_track.py       # 音频处理
├── add_text.py             # 文字处理
├── util.py                 # 工具函数
├── requirements-simple.txt # 精简依赖
├── deploy-windows.bat      # Windows部署脚本
├── deploy-linux.sh         # Linux部署脚本
├── start-windows.bat       # Windows启动脚本
├── start-linux.sh          # Linux启动脚本
├── docker-compose-simple.yml # 精简Docker配置
├── config.json.example     # 配置模板
└── DEPLOYMENT-SIMPLE.md    # 本指南
```

## 🔧 配置文件

### config.json（必需）
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 9001,
    "debug": false
  },
  "media": {
    "upload_dir": "./media",
    "draft_dir": "./drafts",
    "max_file_size": "100MB"
  }
}
```

## 📡 服务验证

部署完成后，访问以下地址验证服务：

- **健康检查**: http://localhost:9001/health
- **API文档**: http://localhost:9001/docs
- **示例接口**: http://localhost:9001/api/hello

## 🛠️ 故障排除

### 常见问题

1. **端口占用**
   ```bash
   # Windows
   netstat -ano | findstr :9001
   
   # Linux
   sudo lsof -i :9001
   ```

2. **FFmpeg未安装**
   ```bash
   # Windows: 下载并添加到PATH
   # https://ffmpeg.org/download.html
   
   # Linux
   sudo apt install ffmpeg
   # 或
   sudo yum install ffmpeg
   ```

3. **权限问题**
   ```bash
   # Linux
   chmod +x *.sh
   sudo chown -R $USER:$USER .
   ```

## 📊 性能优化

### 系统配置建议
- **内存**: 2GB基础，4GB推荐
- **CPU**: 2核心基础，4核心推荐
- **存储**: SSD推荐，提高IO性能

### Python优化
```bash
# 使用精简依赖
pip install -r requirements-simple.txt

# 生产环境
export PYTHONOPTIMIZE=1
python capcut_server.py --production
```

## 🔍 监控与日志

### 日志文件
- **应用日志**: logs/capcut.log
- **错误日志**: logs/error.log
- **访问日志**: logs/access.log

### 系统监控
```bash
# Windows任务管理器
# Linux系统监控
top -p $(pgrep python)
df -h                    # 磁盘空间
free -h                  # 内存使用
```

## 🆘 技术支持

- **GitHub Issues**: https://github.com/chenzhaohua11/CapCutAPI/issues
- **文档**: https://github.com/chenzhaohua11/CapCutAPI/wiki

---

**部署完成！** 🎉 现在您可以通过简单的命令在Windows或Linux上快速部署CapCutAPI服务。