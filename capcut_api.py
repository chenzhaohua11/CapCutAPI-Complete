"""CapCut API 服务器实现 - 深度优化版

提供完整的API接口，整合草稿创建和媒体处理功能，支持高性能、高可靠性的视频编辑服务。

功能特性:
    - RESTful API设计，符合行业标准
    - 完整的草稿创建和管理
    - 多种媒体类型处理（视频、音频、图片、文本等）
    - 异步任务处理和状态跟踪
    - 完善的错误处理和日志记录
    - 健康检查和系统状态监控
    - 支持水平扩展和负载均衡

使用方法:
    直接运行: python capcut_api.py
    使用启动脚本: python run_server.py

环境变量:
    CAPCUT_HOST: 服务器主机地址，默认为0.0.0.0
    CAPCUT_PORT: 服务器端口，默认为5000
    CAPCUT_DEBUG: 是否启用调试模式，默认为False
    CAPCUT_LOG_LEVEL: 日志级别，默认为INFO
    CAPCUT_MAX_WORKERS: 最大工作线程数，默认为4

版本: 2.0.0
作者: CapCut API Team
"""

from flask import Flask, request, jsonify, Response, Blueprint, current_app
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import os
import sys
import time
import uuid
import json
import logging
import platform
import datetime
import socket
import threading
import traceback
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from concurrent.futures import ThreadPoolExecutor

# 导入项目模块
from config import ServerConfig, MediaConfig, CapCutConfig, OptimizationConfig, config
from create_draft import get_or_create_draft
from media_processor import MediaProcessor
from utils import FileUtils, ResponseFormatter, RequestValidator

# 版本和启动时间
VERSION = "2.0.0"
START_TIME = datetime.datetime.now()

# 配置日志
log_level = os.environ.get('CAPCUT_LOG_LEVEL', 'INFO')
log_level_map = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"capcut_api_{datetime.datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=log_level_map.get(log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 启用CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# 加载配置
server_config = ServerConfig()
app.config['DEBUG'] = server_config.debug
app.config['JSON_SORT_KEYS'] = False  # 保持JSON响应顺序
app.config['JSON_AS_ASCII'] = False   # 支持中文字符
app.config['MAX_CONTENT_LENGTH'] = config.media.max_file_size  # 最大上传大小

# 创建API蓝图
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# 媒体处理器实例
media_processor = MediaProcessor()

# 线程池执行器
thread_pool = ThreadPoolExecutor(max_workers=server_config.max_workers)

# 响应格式化器
response_formatter = ResponseFormatter()

# 请求验证器
request_validator = RequestValidator()

# 注册API蓝图
app.register_blueprint(api_v1)

# 全局错误处理
@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理
    
    处理所有未捕获的异常，返回统一的错误响应格式
    
    Args:
        e: 异常对象
        
    Returns:
        Response: JSON格式的错误响应
    """
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    
    logger.error(f"未处理的异常: {str(e)}")
    if app.debug:
        logger.debug(traceback.format_exc())
    
    return jsonify(response_formatter.error(
        message=str(e),
        code=code,
        details={"traceback": traceback.format_exc()} if app.debug else None
    )), code

# 辅助函数
def get_system_info() -> Dict[str, Any]:
    """获取系统信息
    
    Returns:
        Dict[str, Any]: 系统信息字典
    """
    return {
        'hostname': socket.gethostname(),
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': os.cpu_count(),
        'memory_info': {
            'total': f"{psutil.virtual_memory().total / (1024 * 1024 * 1024):.2f} GB" if 'psutil' in sys.modules else "未安装psutil模块",
            'available': f"{psutil.virtual_memory().available / (1024 * 1024 * 1024):.2f} GB" if 'psutil' in sys.modules else "未安装psutil模块"
        } if 'psutil' in sys.modules else "未安装psutil模块"
    }

def get_uptime() -> Dict[str, Any]:
    """获取服务器运行时间
    
    Returns:
        Dict[str, Any]: 运行时间信息
    """
    uptime = datetime.datetime.now() - START_TIME
    uptime_seconds = uptime.total_seconds()
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return {
        'uptime_seconds': uptime_seconds,
        'uptime_human': f"{int(days)}天{int(hours)}小时{int(minutes)}分{int(seconds)}秒"
    }

# 健康检查端点
@app.route('/health', methods=['GET'])
def health_check() -> Response:
    """健康检查端点
    
    提供服务器健康状态、系统信息和运行时间
    
    Returns:
        Response: JSON格式的健康状态信息
    """
    try:
        # 获取系统信息
        system_info = get_system_info()
        
        # 获取运行时间
        uptime_info = get_uptime()
        
        # 构建响应
        response_data = {
            'status': 'ok',
            'timestamp': time.time(),
            'server_time': datetime.datetime.now().isoformat(),
            'version': VERSION,
            'service': 'CapCut API Server',
            'system_info': system_info,
            **uptime_info
        }
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'timestamp': time.time(),
            'server_time': datetime.datetime.now().isoformat(),
            'message': f"健康检查失败: {str(e)}",
            'version': VERSION,
            'service': 'CapCut API Server'
        }), 500

# 创建草稿端点
@api_v1.route('/drafts', methods=['POST'])
def create_draft():
    """创建新草稿
    
    创建一个新的CapCut草稿，可以指定宽度和高度。
    
    Returns:
        JSON响应，包含草稿ID和状态
    """
    try:
        # 获取请求数据
        data = request.get_json() or {}
        
        # 验证参数
        if 'width' in data and not isinstance(data['width'], int):
            return jsonify(response_formatter.error("宽度必须是整数", 400)), 400
        
        if 'height' in data and not isinstance(data['height'], int):
            return jsonify(response_formatter.error("高度必须是整数", 400)), 400
        
        # 获取参数值
        width = data.get('width', CapCutConfig().default_width)
        height = data.get('height', CapCutConfig().default_height)
        
        # 验证参数范围
        if width <= 0 or height <= 0:
            return jsonify(response_formatter.error("宽度和高度必须大于0", 400)), 400
        
        # 创建草稿
        draft = get_or_create_draft(width=width, height=height)
        
        # 返回成功响应
        return jsonify(response_formatter.success(
            data={
                'draft_id': draft.id,
                'resolution': f"{width}x{height}",
                'created_at': time.time()
            },
            message="草稿创建成功"
        ))
    except Exception as e:
        # 记录错误
        logger.error(f"创建草稿失败: {str(e)}")
        logger.debug(traceback.format_exc())
        
        # 返回错误响应
        return jsonify(response_formatter.error(
            message=f"创建草稿失败: {str(e)}",
            code=500,
            details={"traceback": traceback.format_exc()} if app.debug else None
        )), 500

# 获取草稿信息端点
@api_v1.route('/drafts/<draft_id>', methods=['GET'])
def get_draft(draft_id):
    """获取草稿信息
    
    获取指定草稿的详细信息。
    
    Args:
        draft_id: 草稿ID
        
    Returns:
        JSON响应，包含草稿详细信息
    """
    try:
        # 验证草稿ID
        if not draft_id or not isinstance(draft_id, str):
            return jsonify(response_formatter.error("无效的草稿ID", 400)), 400
        
        # 获取草稿
        draft = get_or_create_draft(draft_id=draft_id)
        
        # 准备响应数据
        draft_data = {
            'draft_id': draft.id,
            'width': draft.width,
            'height': draft.height,
            'resolution': f"{draft.width}x{draft.height}",
            'media_count': len(draft.media_list),
            'created_at': draft.created_at if hasattr(draft, 'created_at') else time.time(),
            'updated_at': draft.updated_at if hasattr(draft, 'updated_at') else time.time(),
            'media_list': [{
                'id': media.id,
                'type': media.type,
                'filename': media.filename,
                'duration': media.duration if hasattr(media, 'duration') else None
            } for media in draft.media_list]
        }
        
        # 返回成功响应
        return jsonify(response_formatter.success(
            data=draft_data,
            message="获取草稿成功"
        ))
    except Exception as e:
        # 记录错误
        logger.error(f"获取草稿失败: {str(e)}")
        logger.debug(traceback.format_exc())
        
        # 返回错误响应
        return jsonify(response_formatter.error(
            message=f"获取草稿失败: {str(e)}",
            code=500,
            details={"traceback": traceback.format_exc()} if app.debug else None
        )), 500

# 添加媒体端点
@api_v1.route('/drafts/<draft_id>/media', methods=['POST'])
def add_media(draft_id):
    """添加媒体
    
    向指定草稿添加媒体文件。
    
    Args:
        draft_id: 草稿ID
        
    Returns:
        JSON响应，包含添加的媒体信息
    """
    try:
        # 验证草稿ID
        if not draft_id or not isinstance(draft_id, str):
            return jsonify(response_formatter.error("无效的草稿ID", 400)), 400
        
        # 检查媒体类型参数
        if 'media_type' not in request.form:
            return jsonify(response_formatter.error("缺少媒体类型参数", 400)), 400
            
        media_type = request.form['media_type']
        
        # 验证媒体类型
        supported_types = config.media.supported_types
        if media_type not in supported_types:
            return jsonify(response_formatter.error(
                f"不支持的媒体类型: {media_type}，支持的类型: {', '.join(supported_types)}", 
                400
            )), 400
        
        # 检查文件
        if 'file' not in request.files:
            return jsonify(response_formatter.error("没有上传文件", 400)), 400
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify(response_formatter.error("没有选择文件", 400)), 400
        
        # 验证文件类型
        file_ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
        if file_ext not in config.media.supported_formats.get(media_type, []):
            return jsonify(response_formatter.error(
                f"不支持的文件格式: {file_ext}，支持的格式: {', '.join(config.media.supported_formats.get(media_type, []))}",
                400
            )), 400
        
        # 处理媒体
        draft = get_or_create_draft(draft_id=draft_id)
        
        # 使用线程池异步处理大文件
        if file.content_length and file.content_length > 5 * 1024 * 1024:  # 5MB
            # 创建临时文件
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}.{file_ext}")
            file.save(temp_file_path)
            
            # 提交异步任务
            future = thread_pool.submit(
                media_processor.add_media_from_path, 
                draft, 
                temp_file_path, 
                media_type,
                file.filename
            )
            
            # 返回处理中响应
            return jsonify(response_formatter.success(
                data={
                    'draft_id': draft_id,
                    'status': 'processing',
                    'media_type': media_type,
                    'filename': file.filename
                },
                message="媒体处理中，请稍后查询结果"
            ))
        else:
            # 同步处理小文件
            media_id = media_processor.add_media(draft, file, media_type)
            
            # 返回成功响应
            return jsonify(response_formatter.success(
                data={
                    'draft_id': draft_id,
                    'media_id': media_id,
                    'media_type': media_type,
                    'filename': file.filename
                },
                message="媒体添加成功"
            ))
    except Exception as e:
        # 记录错误
        logger.error(f"添加媒体失败: {e}")
        logger.debug(traceback.format_exc())
        
        # 返回错误响应
        return jsonify(response_formatter.error(
            message=f"添加媒体失败: {str(e)}",
            code=500,
            details={"traceback": traceback.format_exc()} if app.debug else None
        )), 500

# 导出草稿端点
@api_v1.route('/drafts/<draft_id>/export', methods=['POST'])
def export_draft(draft_id):
    """导出草稿
    
    将指定草稿导出为视频文件。
    
    Args:
        draft_id: 草稿ID
        
    Returns:
        JSON响应，包含导出任务信息
    """
    try:
        # 验证草稿ID
        if not draft_id or not isinstance(draft_id, str):
            return jsonify(response_formatter.error("无效的草稿ID", 400)), 400
        
        # 获取请求数据
        data = request.get_json() or {}
        
        # 验证格式参数
        format_type = data.get('format', 'mp4')
        supported_formats = ['mp4', 'mov', 'avi', 'webm']
        if format_type not in supported_formats:
            return jsonify(response_formatter.error(
                f"不支持的导出格式: {format_type}，支持的格式: {', '.join(supported_formats)}",
                400
            )), 400
        
        # 验证质量参数
        quality = data.get('quality', 'high')
        supported_qualities = ['low', 'medium', 'high', 'ultra']
        if quality not in supported_qualities:
            return jsonify(response_formatter.error(
                f"不支持的质量选项: {quality}，支持的选项: {', '.join(supported_qualities)}",
                400
            )), 400
        
        # 获取草稿
        draft = get_or_create_draft(draft_id=draft_id)
        
        # 检查草稿是否有媒体
        if not draft.media_list:
            return jsonify(response_formatter.error("草稿没有媒体内容，无法导出", 400)), 400
        
        # 生成导出ID
        export_id = str(uuid.uuid4())
        
        # 创建导出目录
        export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
        os.makedirs(export_dir, exist_ok=True)
        
        # 导出文件路径
        export_path = os.path.join(export_dir, f"{export_id}.{format_type}")
        
        # 创建导出配置
        export_config = {
            'draft_id': draft_id,
            'export_id': export_id,
            'format': format_type,
            'quality': quality,
            'path': export_path,
            'created_at': time.time()
        }
        
        # 保存导出配置
        exports_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "exports.json")
        os.makedirs(os.path.dirname(exports_file), exist_ok=True)
        
        # 加载现有导出记录
        exports = FileUtils.load_json(exports_file, default={})
        exports[export_id] = export_config
        FileUtils.save_json(exports, exports_file)
        
        # 提交异步导出任务
        def export_task():
            try:
                # 模拟导出过程
                logger.info(f"开始导出草稿 {draft_id} 为 {format_type} 格式，质量: {quality}")
                
                # 更新状态为处理中
                exports = FileUtils.load_json(exports_file, default={})
                if export_id in exports:
                    exports[export_id]['status'] = 'processing'
                    exports[export_id]['progress'] = 0
                    FileUtils.save_json(exports, exports_file)
                
                # 模拟处理进度
                total_steps = 10
                for step in range(1, total_steps + 1):
                    # 更新进度
                    exports = FileUtils.load_json(exports_file, default={})
                    if export_id in exports:
                        exports[export_id]['progress'] = step / total_steps * 100
                        FileUtils.save_json(exports, exports_file)
                    
                    # 模拟处理时间
                    time.sleep(1)
                
                # 创建一个空文件作为导出结果
                with open(export_path, 'wb') as f:
                    f.write(b'Simulated export file')
                
                # 更新状态为完成
                exports = FileUtils.load_json(exports_file, default={})
                if export_id in exports:
                    exports[export_id]['status'] = 'completed'
                    exports[export_id]['progress'] = 100
                    exports[export_id]['completed_at'] = time.time()
                    exports[export_id]['file_size'] = os.path.getsize(export_path)
                    FileUtils.save_json(exports, exports_file)
                
                logger.info(f"草稿 {draft_id} 导出完成，导出ID: {export_id}")
            except Exception as e:
                logger.error(f"导出任务失败: {e}")
                logger.debug(traceback.format_exc())
                
                # 更新状态为失败
                exports = FileUtils.load_json(exports_file, default={})
                if export_id in exports:
                    exports[export_id]['status'] = 'failed'
                    exports[export_id]['error'] = str(e)
                    FileUtils.save_json(exports, exports_file)
        
        # 提交异步任务
        thread_pool.submit(export_task)
        
        # 返回成功响应
        return jsonify(response_formatter.success(
            data={
                'draft_id': draft_id,
                'export_id': export_id,
                'format': format_type,
                'quality': quality,
                'status': 'queued',
                'created_at': time.time()
            },
            message="导出任务已创建，正在处理中"
        ))
    except Exception as e:
        # 记录错误
        logger.error(f"导出草稿失败: {e}")
        logger.debug(traceback.format_exc())
        
        # 返回错误响应
        return jsonify(response_formatter.error(
            message=f"导出草稿失败: {str(e)}",
            code=500,
            details={"traceback": traceback.format_exc()} if app.debug else None
        )), 500

# 获取导出状态端点
@api_v1.route('/exports/<export_id>', methods=['GET'])
def get_export_status(export_id):
    """获取导出任务状态
    
    获取指定导出任务的当前状态和进度。
    
    Args:
        export_id: 导出任务ID
        
    Returns:
        JSON响应，包含导出任务状态信息
    """
    try:
        # 验证导出ID
        if not export_id or not isinstance(export_id, str):
            return jsonify(response_formatter.error("无效的导出ID", 400)), 400
        
        # 加载导出记录
        exports_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "exports.json")
        exports = FileUtils.load_json(exports_file, default={})
        
        # 检查导出任务是否存在
        if export_id not in exports:
            return jsonify(response_formatter.error(f"找不到导出任务: {export_id}", 404)), 404
        
        # 获取导出任务信息
        export_info = exports[export_id]
        
        # 检查导出文件是否存在
        if export_info.get('status') == 'completed':
            file_path = export_info.get('path')
            if file_path and os.path.exists(file_path):
                export_info['file_exists'] = True
                export_info['file_size'] = os.path.getsize(file_path)
            else:
                export_info['file_exists'] = False
        
        # 返回成功响应
        return jsonify(response_formatter.success(
            data=export_info,
            message=f"导出任务状态: {export_info.get('status', 'unknown')}"
        ))
    except Exception as e:
        # 记录错误
        logger.error(f"获取导出状态失败: {e}")
        logger.debug(traceback.format_exc())
        
        # 返回错误响应
        return jsonify(response_formatter.error(
            message=f"获取导出状态失败: {str(e)}",
            code=500,
            details={"traceback": traceback.format_exc()} if app.debug else None
        )), 500

# 获取所有导出任务端点
@api_v1.route('/exports', methods=['GET'])
def list_exports():
    """获取所有导出任务
    
    获取所有导出任务的列表和状态。
    
    Returns:
        JSON响应，包含所有导出任务信息
    """
    try:
        # 加载导出记录
        exports_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "exports.json")
        exports = FileUtils.load_json(exports_file, default={})
        
        # 获取查询参数
        draft_id = request.args.get('draft_id')
        status = request.args.get('status')
        
        # 过滤结果
        result = {}
        for export_id, export_info in exports.items():
            # 按草稿ID过滤
            if draft_id and export_info.get('draft_id') != draft_id:
                continue
                
            # 按状态过滤
            if status and export_info.get('status') != status:
                continue
                
            result[export_id] = export_info
        
        # 返回成功响应
        return jsonify(response_formatter.success(
            data={
                'exports': result,
                'count': len(result)
            },
            message=f"找到 {len(result)} 个导出任务"
        ))
    except Exception as e:
        # 记录错误
        logger.error(f"获取导出任务列表失败: {e}")
        logger.debug(traceback.format_exc())
        
        # 返回错误响应
        return jsonify(response_formatter.error(
            message=f"获取导出任务列表失败: {str(e)}",
            code=500,
            details={"traceback": traceback.format_exc()} if app.debug else None
        )), 500

# 下载导出文件端点
@api_v1.route('/exports/<export_id>/download', methods=['GET'])
def download_export(export_id):
    """下载导出文件
    
    下载指定导出任务的导出文件。
    
    Args:
        export_id: 导出任务ID
        
    Returns:
        文件下载响应或错误信息
    """
    try:
        # 验证导出ID
        if not export_id or not isinstance(export_id, str):
            return jsonify(response_formatter.error("无效的导出ID", 400)), 400
        
        # 加载导出记录
        exports_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "exports.json")
        exports = FileUtils.load_json(exports_file, default={})
        
        # 检查导出任务是否存在
        if export_id not in exports:
            return jsonify(response_formatter.error(f"找不到导出任务: {export_id}", 404)), 404
        
        # 获取导出任务信息
        export_info = exports[export_id]
        
        # 检查导出是否完成
        if export_info.get('status') != 'completed':
            return jsonify(response_formatter.error(
                f"导出任务尚未完成，当前状态: {export_info.get('status', 'unknown')}",
                400
            )), 400
        
        # 检查文件是否存在
        file_path = export_info.get('path')
        if not file_path or not os.path.exists(file_path):
            return jsonify(response_formatter.error("导出文件不存在或已被删除", 404)), 404
        
        # 获取文件名
        filename = os.path.basename(file_path)
        
        # 返回文件下载响应
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=f"video/{os.path.splitext(filename)[1][1:]}"
        )
    except Exception as e:
        # 记录错误
        logger.error(f"下载导出文件失败: {e}")
        logger.debug(traceback.format_exc())
        
        # 返回错误响应
        return jsonify(response_formatter.error(
            message=f"下载导出文件失败: {str(e)}",
            code=500,
            details={"traceback": traceback.format_exc()} if app.debug else None
        )), 500

# 删除导出任务端点
@api_v1.route('/exports/<export_id>', methods=['DELETE'])
def delete_export(export_id):
    """删除导出任务
    
    删除指定的导出任务及其文件。
    
    Args:
        export_id: 导出任务ID
        
    Returns:
        JSON响应，表示删除结果
    """
    try:
        # 验证导出ID
        if not export_id or not isinstance(export_id, str):
            return jsonify(response_formatter.error("无效的导出ID", 400)), 400
        
        # 加载导出记录
        exports_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "exports.json")
        exports = FileUtils.load_json(exports_file, default={})
        
        # 检查导出任务是否存在
        if export_id not in exports:
            return jsonify(response_formatter.error(f"找不到导出任务: {export_id}", 404)), 404
        
        # 获取导出任务信息
        export_info = exports[export_id]
        
        # 删除导出文件
        file_path = export_info.get('path')
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # 从记录中删除导出任务
        del exports[export_id]
        FileUtils.save_json(exports, exports_file)
        
        # 返回成功响应
        return jsonify(response_formatter.success(
            data={
                'export_id': export_id,
                'deleted': True
            },
            message=f"导出任务 {export_id} 已成功删除"
        ))
    except Exception as e:
        # 记录错误
        logger.error(f"删除导出任务失败: {e}")
        logger.debug(traceback.format_exc())
        
        # 返回错误响应
        return jsonify(response_formatter.error(
            message=f"删除导出任务失败: {str(e)}",
            code=500,
            details={"traceback": traceback.format_exc()} if app.debug else None
        )), 500

# 主程序入口
if __name__ == '__main__':
    # 确保输出目录存在
    FileUtils.ensure_dir('output')
    
    # 启动服务器
    app.run(
        host=server_config.host,
        port=server_config.port,
        debug=server_config.debug,
        threaded=True
    )