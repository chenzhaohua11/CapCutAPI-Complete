
# CapCutAPI - Connect AI with Professional Video Editing [Try Online](https://www.capcutapi.top)

## Project Overview
CapCutAPI is a powerful editing API that gives you complete control over AI-generated content including images, audio, video, and text. It provides the precision needed to refine raw AI outputs - whether adjusting video speed, mirroring images, or applying complex effects. This solves the common limitation of lacking fine-grained control in AI video generation, enabling you to transform creative concepts into polished, professional videos.

All features mirror the familiar CapCut/JianYing interface, ensuring an intuitive cloud-based editing experience.

🚀 Get started today and bring your AI creations to life!

[中文文档](README-zh.md)

## Why Choose CapCutAPI?

- **Complete API Access**: Full CapCut/JianYing functionality including multi-track editing, keyframe animation, and advanced effects
- **Real-time Cloud Preview**: Instantly preview edits in your browser without downloads
- **Flexible Workflow**: Export as drafts for local editing in CapCut/JianYing or render directly in the cloud
- **Professional Results**: Production-ready outputs with broadcast-quality rendering

## Live Demos

<div align="center">

**Build Your AI Editing Agent with MCP**

[![AI Cut Demo](https://img.youtube.com/vi/fBqy6WFC78E/hqdefault.jpg)](https://www.youtube.com/watch?v=fBqy6WFC78E)

**Seamlessly Combine AI-Generated Assets**

[View More Examples](pattern)

[![Airbnb Showcase](https://img.youtube.com/vi/1zmQWt13Dx0/hqdefault.jpg)](https://www.youtube.com/watch?v=1zmQWt13Dx0)

[![Creative Horse](https://img.youtube.com/vi/IF1RDFGOtEU/hqdefault.jpg)](https://www.youtube.com/watch?v=IF1RDFGOtEU)

[![Music Video](https://img.youtube.com/vi/rGNLE_slAJ8/hqdefault.jpg)](https://www.youtube.com/watch?v=rGNLE_slAJ8)

</div>

## Core Features

| Feature | API | MCP | Capabilities |
|---------|-----|-----|--------------|
| **Draft Management** | ✅ | ✅ | Create, save, and manage CapCut/JianYing draft files |
| **Video Processing** | ✅ | ✅ | Multi-format support, trimming, transitions, effects |
| **Audio Editing** | ✅ | ✅ | Multi-track audio, volume control, sound effects |
| **Image Processing** | ✅ | ✅ | Import, animations, masks, filters, overlays |
| **Text & Titles** | ✅ | ✅ | Rich text styling, animations, shadows, backgrounds |
| **Subtitles** | ✅ | ✅ | SRT import, styling, timing synchronization |
| **Visual Effects** | ✅ | ✅ | Filters, transitions, particle effects, keyframe animations |
| **Stickers & Overlays** | ✅ | ✅ | Asset library, positioning, animation controls |
| **Keyframe Animation** | ✅ | ✅ | Property animation, timeline control, easing curves |
| **Media Analysis** | ✅ | ✅ | Duration detection, format identification, metadata extraction |

## Quick Start Guide

### Prerequisites

- **Python**: 3.10 or higher
- **CapCut/JianYing**: Desktop application for local editing
- **FFmpeg**: For media processing

### Installation

```bash
# Clone repository
git clone https://github.com/sun-guannan/CapCutAPI.git
cd CapCutAPI

# Create virtual environment
python -m venv venv-capcut
source venv-capcut/bin/activate  # Linux/macOS
# or: venv-capcut\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt           # Core HTTP API
pip install -r requirements-mcp.txt      # MCP protocol (optional)

# Configure settings
cp config.json.example config.json
# Edit config.json for your environment
```

### Launch Services

```bash
# Start HTTP API server (Port 9001)
python capcut_server.py

# Start MCP protocol server
python mcp_server.py
```

## MCP Protocol Integration

📖 [MCP Documentation (中文)](./MCP_文档_中文.md) • [MCP Guide (English)](./MCP_Documentation_English.md)

### Configuration

Create `mcp_config.json`:

```json
{
  "mcpServers": {
    "capcut-api": {
      "command": "python3",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/CapCutAPI",
      "env": {
        "PYTHONPATH": "/path/to/CapCutAPI",
        "DEBUG": "0"
      }
    }
  }
}
```

### Test Connection

```bash
# Verify MCP setup
python test_mcp_client.py

# Success indicators:
✅ Server initialization
✅ 11 tools available
✅ Draft creation functional
```

## Usage Examples

### HTTP API Examples

**Add Video**
```python
import requests

response = requests.post("http://localhost:9001/add_video", json={
    "video_url": "https://example.com/background.mp4",
    "start": 0,
    "end": 10,
    "volume": 0.8,
    "transition": "fade_in"
})
print(response.json())
```

**Add Styled Text**
```python
response = requests.post("http://localhost:9001/add_text", json={
    "text": "Welcome to CapCutAPI",
    "start": 0,
    "end": 5,
    "font": "Source Han Sans",
    "font_color": "#FFD700",
    "font_size": 48,
    "shadow_enabled": True,
    "background_color": "#000000"
})
print(response.json())
```

📋 See `example.py` for comprehensive examples.

### MCP Protocol Examples

**Complete Workflow**
```python
# Initialize project
draft = mcp_client.call_tool("create_draft", {
    "width": 1080, "height": 1920
})
draft_id = draft["result"]["draft_id"]

# Add background video
mcp_client.call_tool("add_video", {
    "video_url": "https://example.com/bg.mp4",
    "draft_id": draft_id,
    "start": 0, "end": 10, "volume": 0.6
})

# Add animated title
mcp_client.call_tool("add_text", {
    "text": "AI-Driven Video Production",
    "draft_id": draft_id,
    "start": 1, "end": 6,
    "font_size": 56,
    "shadow_enabled": True,
    "background_color": "#1E1E1E"
})

# Apply keyframe animation
mcp_client.call_tool("add_video_keyframe", {
    "draft_id": draft_id,
    "track_name": "main",
    "property_types": ["scale_x", "scale_y", "alpha"],
    "times": [0, 2, 4],
    "values": ["1.0", "1.2", "0.8"]
})

# Save and export
result = mcp_client.call_tool("save_draft", {
    "draft_id": draft_id
})
print(f"Project ready: {result['result']['draft_url']}")
```

**Advanced Text Effects**
```python
# Multi-color animated text
mcp_client.call_tool("add_text", {
    "text": "Dynamic Color Text",
    "draft_id": draft_id,
    "start": 2, "end": 8,
    "font_size": 42,
    "shadow_enabled": True,
    "text_styles": [
        {"start": 0, "end": 2, "font_color": "#FF6B6B"},
        {"start": 2, "end": 4, "font_color": "#4ECDC4"},
        {"start": 4, "end": 6, "font_color": "#45B7D1"}
    ]
})
```

## Working with Drafts

When you call `save_draft`, a folder prefixed with `dfd_` is created in the `capcut_server.py` directory. Simply copy this folder to your CapCut/JianYing drafts folder to access your project locally.

## Templates & Examples

Explore production-ready templates in the [`pattern`](pattern) directory for common use cases.

## Contributing & Support

We welcome all contributions! Our development workflow:

- **Development**: Submit PRs to the `dev` branch
- **Releases**: Weekly merges from `dev` to `main` every Monday
- **Guidelines**: See [CONTRIBUTING.md](CONTRIBUTING.md) for details

### Get Involved

**🎬 Video Production Partnership**
Need help with batch video production? I provide free consulting to help integrate CapCutAPI into your workflow. In exchange, we open-source your production templates to benefit the community.

**👥 Join the Team**
Help build the future of AI-powered video editing. While the MCP Editing Agent, web client, and cloud rendering modules remain private, core functionality is open for contributions.

**📧 Contact**: sguann2023@gmail.com

## Community & Stats

<div align="center">

[![Star History](https://api.star-history.com/svg?repos=sun-guannan/CapCutAPI&type=Date)](https://www.star-history.com/#sun-guannan/CapCutAPI&Date)

![Repo Size](https://img.shields.io/github/repo-size/sun-guannan/CapCutAPI?style=flat-square)
![Code Size](https://img.shields.io/github/languages/code-size/sun-guannan/CapCutAPI?style=flat-square)
![Issues](https://img.shields.io/github/issues/sun-guannan/CapCutAPI?style=flat-square)
![PRs](https://img.shields.io/github/issues-pr/sun-guannan/CapCutAPI?style=flat-square)
![Last Commit](https://img.shields.io/github/last-commit/sun-guannan/CapCutAPI?style=flat-square)

[![MSeeP Verified](https://mseep.ai/badge.svg)](https://mseep.ai/app/69c38d28-a97c-4397-849d-c3e3d241b800)

</div>

*Crafted with ❤️ by the CapCutAPI community*
