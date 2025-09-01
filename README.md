# Connect AI generates via CapCutAPI [Try it online](https://www.capcutapi.top)

## Project Overview
**CapCutAPI** is a powerful editing API that empowers you to take full control of your AI-generated assets, including images, audio, video, and text. It provides the precision needed to refine and customize raw AI output, such as adjusting video speed or mirroring an image. This capability effectively solves the lack of control often found in AI video generation, allowing you to easily transform your creative ideas into polished videos.

All these features are designed to mirror the functionalities of the CapCut software, ensuring a familiar and efficient editing experience in the cloud.

Enjoy It!  😀😀😀

[中文说明](README-zh.md) 

### Advantages

1. **API-Powered Editing:** Access all CapCut/Jianying editing features, including multi-track editing and keyframe animation, through a powerful API.

2. **Real-Time Cloud Preview:** Instantly preview your edits on a webpage without downloads, dramatically improving your workflow.

3. **Flexible Local Editing:** Export projects as drafts to import into CapCut or Jianying for further refinement.

4. **Automated Cloud Generation:** Use the API to render and generate final videos directly in the cloud.

## Demos

<div align="center">

**MCP, create your own editing Agent**

[![AI Cut](https://img.youtube.com/vi/fBqy6WFC78E/hqdefault.jpg)](https://www.youtube.com/watch?v=fBqy6WFC78E)

**Combine AI-generated images and videos using CapCutAPI**

[More](pattern)

[![Airbnb](https://img.youtube.com/vi/1zmQWt13Dx0/hqdefault.jpg)](https://www.youtube.com/watch?v=1zmQWt13Dx0)

[![Horse](https://img.youtube.com/vi/IF1RDFGOtEU/hqdefault.jpg)](https://www.youtube.com/watch?v=IF1RDFGOtEU)

[![Song](https://img.youtube.com/vi/rGNLE_slAJ8/hqdefault.jpg)](https://www.youtube.com/watch?v=rGNLE_slAJ8)


</div>

## Key Features

| Feature Module | API | MCP Protocol | Description |
|---------|----------|----------|------|
| **Draft Management** | ✅ | ✅ | Create and save Jianying/CapCut draft files |
| **Video Processing** | ✅ | ✅ | Import, clip, transition, and apply effects to multiple video formats |
| **Audio Editing** | ✅ | ✅ | Audio tracks, volume control, sound effects processing |
| **Image Processing** | ✅ | ✅ | Image import, animation, masks, filters |
| **Text Editing** | ✅ | ✅ | Multi-style text, shadows, backgrounds, animations |
| **Subtitle System** | ✅ | ✅ | SRT subtitle import, style settings, time synchronization |
| **Effects Engine** | ✅ | ✅ | Visual effects, filters, transition animations |
| **Sticker System** | ✅ | ✅ | Sticker assets, position control, animation effects |
| **Keyframes** | ✅ | ✅ | Property animation, timeline control, easing functions |
| **Media Analysis** | ✅ | ✅ | Get video duration, detect format |

## Quick Start

### 1\. System Requirements

  - Python 3.10+
  - Jianying or CapCut International version
  - FFmpeg

### 2\. Installation and Deployment

```bash
# 1. Clone the project
git clone https://github.com/sun-guannan/CapCutAPI.git
cd CapCutAPI

# 2. Create a virtual environment (recommended)
python -m venv venv-capcut
source venv-capcut/bin/activate  # Linux/macOS
# or venv-capcut\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt      # HTTP API basic dependencies
pip install -r requirements-mcp.txt  # MCP protocol support (optional)

# 4. Configuration file
cp config.json.example config.json
# Edit config.json as needed
```

### 3\. Start the service

```bash
python capcut_server.py # Start the HTTP API server, default port: 9001

python mcp_server.py # Start the MCP protocol service, supports stdio communication
```

## MCP Integration Guide

[MCP 中文文档](https://www.google.com/search?q=./MCP_%E6%96%87%E6%A1%A3_%E4%B8%AD%E6%96%87.md) • [MCP English Guide](https://www.google.com/search?q=./MCP_Documentation_English.md)

### 1\. Client Configuration

Create or update the `mcp_config.json` configuration file:

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

### 2\. Connection Test

```bash
# Test MCP connection
python test_mcp_client.py

# Expected output
✅ MCP server started successfully
✅ Got 11 available tools
✅ Draft creation test passed
```

## Usage Examples

### 1\. API Example

Add video material

```python
import requests

# Add background video
response = requests.post("http://localhost:9001/add_video", json={
    "video_url": "https://example.com/background.mp4",
    "start": 0,
    "end": 10
    "volume": 0.8,
    "transition": "fade_in"
})

print(f"Video addition result: {response.json()}")
```

Create stylized text

```python
import requests

# Add title text
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

print(f"Text addition result: {response.json()}")
```

More examples can be found in the `example.py` file.

### 2\. MCP Protocol Example

Complete workflow

```python
# 1. Create a new project
draft = mcp_client.call_tool("create_draft", {
    "width": 1080,
    "height": 1920
})
draft_id = draft["result"]["draft_id"]

# 2. Add background video
mcp_client.call_tool("add_video", {
    "video_url": "https://example.com/bg.mp4",
    "draft_id": draft_id,
    "start": 0,
    "end": 10,
    "volume": 0.6
})

# 3. Add title text
mcp_client.call_tool("add_text", {
    "text": "AI-Driven Video Production",
    "draft_id": draft_id,
    "start": 1,
    "end": 9,
    "font_size": 64,
    "font_color": "#FFFFFF",
    "position": {"x": 540, "y": 300}
})
```

## Project Structure

```
CapCutAPI/
├── capcut_server.py          # HTTP API server
├── mcp_server.py             # MCP protocol server
├── example.py               # Usage examples
├── requirements.txt         # Python dependencies
├── requirements-mcp.txt     # MCP protocol dependencies
├── config.json.example    # Configuration template
├── Dockerfile              # Docker container configuration
├── docker-compose.yml      # Docker Compose configuration
├── k8s/                    # Kubernetes deployment files
│   ├── deployment.yaml
│   └── service.yaml
├── media/                  # Media processing modules
│   ├── video_processor.py
│   ├── audio_processor.py
│   ├── image_processor.py
│   ├── text_processor.py
│   ├── subtitle_processor.py
│   ├── effect_processor.py
│   └── sticker_processor.py
├── utils/                  # Utility modules
│   ├── logger.py
│   ├── config.py
│   ├── file_utils.py
│   └── draft_manager.py
├── pyJianYingDraft/        # Jianying draft file format library
├── examples/               # Example configurations
├── templates/              # Template files
└── nginx.conf             # Nginx configuration
```

## API Documentation

### HTTP API Endpoints

#### Draft Management
- `POST /create_draft` - Create new draft
- `GET /get_draft/{draft_id}` - Get draft details
- `POST /update_draft` - Update draft
- `DELETE /delete_draft/{draft_id}` - Delete draft
- `GET /list_drafts` - List all drafts

#### Media Processing
- `POST /add_video` - Add video material
- `POST /add_audio` - Add audio material
- `POST /add_image` - Add image material
- `POST /add_text` - Add text material
- `POST /add_subtitle` - Add subtitle
- `POST /add_effect` - Add effect
- `POST /add_sticker` - Add sticker

### MCP Protocol Tools

The MCP server provides the following tools:

1. `create_draft` - Create new draft
2. `get_draft` - Get draft information
3. `update_draft` - Update draft
4. `add_video` - Add video material
5. `add_audio` - Add audio material
6. `add_image` - Add image material
7. `add_text` - Add text material
8. `add_subtitle` - Add subtitle
9. `add_effect` - Add effect
10. `add_sticker` - Add sticker
11. `export_draft` - Export draft file

## Configuration

### Environment Variables

- `DEBUG`: Debug mode (0/1)
- `PORT`: Server port (default: 9001)
- `HOST`: Server host (default: 0.0.0.0)
- `LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR)

### Configuration File (config.json)

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 9001,
    "debug": false
  },
  "media": {
    "max_file_size": 104857600,
    "allowed_extensions": ["mp4", "mov", "avi", "jpg", "png", "mp3", "wav"],
    "temp_dir": "./temp"
  },
  "logging": {
    "level": "INFO",
    "file": "capcut_api.log"
  }
}
```

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t capcut-api .

# Run container
docker run -p 9001:9001 capcut-api
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Check status
kubectl get pods
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: support@capcutapi.com
- 💬 Discord: [Join our community](https://discord.gg/capcutapi)
- 📖 Documentation: [Full documentation](https://docs.capcutapi.com)

## Acknowledgments

- Thanks to the CapCut team for providing inspiration
- Thanks to all contributors and community members
- Special thanks to the open-source community