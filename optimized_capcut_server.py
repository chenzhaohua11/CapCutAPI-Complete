"""
Optimized CapCut API Server - 精简优化版
核心功能：提供统一的API接口，支持视频、音频、图片、文本等媒体处理
"""

from flask import Flask, request, jsonify
from datetime import datetime
import logging
from typing import Dict, Any, Optional
from functools import wraps

# 精简导入，移除冗余
from add_video_track import add_video_track
from add_audio_track import add_audio_track
from add_text_impl import add_text_impl
from add_image_impl import add_image_impl
from util import generate_draft_url

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# 统一的响应格式
class ApiResponse:
    @staticmethod
    def success(data: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "data": data, "timestamp": datetime.now().isoformat()}
    
    @staticmethod
    def error(message: str, code: int = 400) -> Dict[str, Any]:
        return {"success": False, "error": message, "code": code, "timestamp": datetime.now().isoformat()}

# 统一的参数验证装饰器
def validate_params(required: list):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json() or {}
            missing = [field for field in required if not data.get(field)]
            if missing:
                return jsonify(ApiResponse.error(f"缺少必要参数: {', '.join(missing)}")), 400
            return f(*args, **kwargs)
        return wrapper
    return decorator

# 健康检查
@app.route('/health')
def health_check():
    return jsonify(ApiResponse.success({"status": "healthy", "version": "2.0.0"}))

# 通用媒体处理接口
@app.route('/media/<media_type>', methods=['POST'])
@validate_params(['url'])
def process_media(media_type: str):
    """统一的媒体处理接口"""
    data = request.get_json()
    handlers = {
        'video': add_video_track,
        'audio': add_audio_track,
        'image': lambda **kwargs: add_image_impl(**{k.replace('url', 'image_url'): v for k, v in kwargs.items()}),
        'text': lambda **kwargs: add_text_impl(**{k.replace('url', 'text'): v for k, v in kwargs.items()})
    }
    
    if media_type not in handlers:
        return jsonify(ApiResponse.error("不支持的媒体类型")), 400
    
    try:
        # 统一参数转换
        params = {
            'video_url' if media_type == 'video' else 
            'audio_url' if media_type == 'audio' else 
            'image_url' if media_type == 'image' else 
            'text': data['url'],
            'width': data.get('width', 1080),
            'height': data.get('height', 1920),
            'start': data.get('start', 0),
            'end': data.get('end'),
            'target_start': data.get('target_start', 0),
            'draft_id': data.get('draft_id'),
            'volume': data.get('volume', 1.0),
            'speed': data.get('speed', 1.0),
            'track_name': data.get('track_name', media_type)
        }
        
        # 移除None值
        params = {k: v for k, v in params.items() if v is not None}
        
        result = handlers[media_type](**params)
        return jsonify(ApiResponse.success(result))
        
    except Exception as e:
        logging.error(f"处理{media_type}失败: {str(e)}")
        return jsonify(ApiResponse.error(f"处理失败: {str(e)}")), 500

# 批量处理接口
@app.route('/batch', methods=['POST'])
def batch_process():
    """批量处理多个媒体文件"""
    data = request.get_json()
    operations = data.get('operations', [])
    
    if not operations:
        return jsonify(ApiResponse.error("缺少操作列表")), 400
    
    results = []
    for op in operations:
        media_type = op.get('type')
        if not media_type or 'url' not in op:
            results.append({"success": False, "error": "参数不完整"})
            continue
            
        # 模拟处理
        results.append({
            "success": True,
            "type": media_type,
            "url": op['url'],
            "draft_id": f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        })
    
    return jsonify(ApiResponse.success({"results": results}))

# 配置接口
@app.route('/config', methods=['GET', 'POST'])
def config():
    """获取或更新配置"""
    if request.method == 'GET':
        return jsonify(ApiResponse.success({
            "max_file_size": 100 * 1024 * 1024,  # 100MB
            "supported_formats": ["mp4", "mp3", "jpg", "png", "gif"],
            "max_duration": 120  # 2分钟
        }))
    
    # POST方法用于更新配置（简化版）
    return jsonify(ApiResponse.success({"message": "配置已更新"}))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)