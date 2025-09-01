# CapCutAPI-Complete

🎬 **CapCut API 完整版** - 功能强大的视频编辑API服务，基于剪映(CapCut/JianYing)核心功能实现

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 项目简介

CapCutAPI-Complete 是一个基于 Python 的完整视频编辑API服务，提供与剪映(CapCut/JianYing)类似的核心功能。通过HTTP API和MCP协议接口，您可以轻松实现：

- 🎞️ 视频剪辑和合并
- 🎵 音频处理和混音
- 📝 文字和字幕添加
- ✨ 特效和转场效果
- 🖼️ 贴纸和装饰元素
- 📦 批量处理和自动化

## ✨ 核心特性

### 🎯 视频处理
- **多轨道编辑**：支持无限视频轨道
- **格式转换**：支持MP4、AVI、MOV、MKV等主流格式
- **分辨率适配**：自动适配1080P、4K等分辨率
- **帧率转换**：24fps、30fps、60fps无缝切换
- **视频压缩**：智能压缩保持画质

### 🎵 音频处理
- **音频提取**：从视频中提取音频轨道
- **音量调节**：精确到毫秒级的音量控制
- **淡入淡出**：平滑的音频过渡效果
- **音频混合**：多轨道音频混音
- **格式支持**：MP3、WAV、AAC、FLAC等

### 📝 文字和字幕
- **动态字幕**：支持SRT、ASS字幕格式
- **字体样式**：丰富的字体和样式选项
- **动画效果**：文字入场和出场动画
- **实时预览**：即时查看字幕效果
- **多语言支持**：中英文等多语言字幕

### ✨ 特效和滤镜
- **转场效果**：100+种专业转场
- **视觉滤镜**：电影级调色滤镜
- **动态特效**：粒子、光效、模糊等
- **自定义特效**：支持自定义特效参数
- **预设模板**：一键应用专业模板

### 🖼️ 贴纸和装饰
- **静态贴纸**：PNG、JPG、SVG格式支持
- **动态贴纸**：GIF和WebP动画贴纸
- **自定义贴纸**：支持用户上传自定义贴纸
- **位置控制**：精确的位置和大小调整
- **层级管理**：灵活的图层顺序控制

## 🏗️ 架构设计

```
CapCutAPI-Complete/
├── capcut_server.py      # HTTP API服务器
├── mcp_server.py         # MCP协议服务器
├── create_draft.py       # 草稿管理
├── add_video_track.py    # 视频轨道管理
├── add_audio_track.py    # 音频轨道管理
├── add_text.py          # 文字和字幕管理
├── add_effects.py       # 特效和滤镜管理
├── add_stickers.py      # 贴纸和装饰管理
├── video_utils.py       # 视频处理工具
├── audio_utils.py       # 音频处理工具
├── image_utils.py       # 图像处理工具
├── utils.py             # 通用工具函数
├── Dockerfile           # Docker容器配置
├── docker-compose.yml   # 多服务编排
└── requirements.txt     # 依赖包列表
```

## 🚀 快速开始

### 📋 系统要求

- **Python**: 3.8 或更高版本
- **FFmpeg**: 最新版本
- **操作系统**: Windows 10+/macOS 10.14+/Ubuntu 18.04+
- **内存**: 最少4GB RAM（推荐8GB+）
- **存储**: 至少10GB可用空间

### 🔧 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/chenzhaohua11/CapCutAPI-Complete.git
cd CapCutAPI-Complete
```

#### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 3. 安装FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
- 下载 [FFmpeg Windows版本](https://ffmpeg.org/download.html)
- 解压并添加到系统PATH

#### 4. 启动服务

```bash
# 启动HTTP API服务器
python capcut_server.py

# 启动MCP服务器
python mcp_server.py
```

### 🐳 Docker部署

#### 1. 使用Docker Compose

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f capcut-api
```

#### 2. 单独构建镜像

```bash
# 构建镜像
docker build -t capcut-api .

# 运行容器
docker run -p 5000:5000 -v $(pwd)/data:/app/data capcut-api
```

## 📖 API使用指南

### 🌐 HTTP API接口

#### 创建项目草稿

```bash
curl -X POST http://localhost:5000/create_draft \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的第一个项目",
    "resolution": "1920x1080",
    "fps": 30,
    "duration": 60
  }'
```

#### 添加视频

```bash
curl -X POST http://localhost:5000/add_video \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "draft_123456",
    "video_url": "https://example.com/video.mp4",
    "start_time": 0,
    "duration": 10,
    "position": {"x": 0, "y": 0},
    "size": {"width": 1920, "height": 1080}
  }'
```

#### 添加音频

```bash
curl -X POST http://localhost:5000/add_audio \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "draft_123456",
    "audio_url": "https://example.com/audio.mp3",
    "start_time": 0,
    "duration": 10,
    "volume": 0.8
  }'
```

#### 添加文字

```bash
curl -X POST http://localhost:5000/add_text \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "draft_123456",
    "content": "Hello, CapCut API!",
    "start_time": 2,
    "duration": 5,
    "position": {"x": 100, "y": 100},
    "font_size": 48,
    "color": "#FFFFFF"
  }'
```

#### 添加特效

```bash
curl -X POST http://localhost:5000/add_effect \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "draft_123456",
    "effect_type": "fade_in",
    "start_time": 0,
    "duration": 2,
    "intensity": 0.8
  }'
```

#### 导出视频

```bash
curl -X POST http://localhost:5000/export_video \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "draft_123456",
    "format": "mp4",
    "quality": "high",
    "fps": 30
  }'
```

### 🔌 MCP协议接口

MCP (Media Control Protocol) 提供更高性能的接口：

```python
from mcp_client import MCPClient

client = MCPClient("localhost", 5001)

# 创建项目
draft = client.create_draft(
    name="MCP项目",
    resolution="1920x1080",
    fps=30
)

# 添加媒体
video_id = client.add_video(draft.id, "video.mp4")
audio_id = client.add_audio(draft.id, "audio.mp3")
text_id = client.add_text(draft.id, "Hello World")

# 应用特效
client.add_transition(video_id, "fade_in")
client.add_filter(video_id, "vintage")

# 导出结果
output_path = client.export(draft.id, "final_video.mp4")
```

## 📁 项目结构

```
CapCutAPI-Complete/
├── 📁 项目根目录
├── 📁 data/                    # 数据存储目录
│   ├── 📁 uploads/            # 上传文件
│   ├── 📁 drafts/             # 项目草稿
│   ├── 📁 exports/            # 导出文件
│   └── 📁 cache/              # 缓存文件
├── 📁 templates/              # 模板文件
├── 📁 config/                 # 配置文件
├── 📁 logs/                   # 日志文件
├── 📁 tests/                  # 测试文件
└── 📁 docs/                   # 文档文件
```

## 📞 联系方式

- **项目维护者**: chenzhaohua11
- **邮箱**: 863654981@qq.com
- **GitHub**: [chenzhaohua11](https://github.com/chenzhaohua11)
- **项目地址**: [CapCutAPI-Complete](https://github.com/chenzhaohua11/CapCutAPI-Complete)

---

<div align="center">
  <p>⭐ 如果这个项目对你有帮助，请给我们一个星标！</p>
  <p><a href="https://github.com/chenzhaohua11/CapCutAPI-Complete">🌟 Star this repo</a></p>
</div>