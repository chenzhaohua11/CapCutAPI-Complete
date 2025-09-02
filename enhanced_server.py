"""增强版CapCut API服务器

提供基本的健康检查和状态监控功能。
"""

import os
import time
import logging
import socket
import platform
from datetime import datetime
from typing import Tuple, Union

from flask import Flask, jsonify, request, Response
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'enhanced_server.log'))
    ]
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 基本配置
DEBUG = os.environ.get('CAPCUT_DEBUG', 'false').lower() in ('true', '1', 'yes')
HOST = os.environ.get('CAPCUT_HOST', '0.0.0.0')
PORT = int(os.environ.get('CAPCUT_PORT', 5000))
VERSION = os.environ.get('CAPCUT_VERSION', '1.0.0')
START_TIME = datetime.now()

@app.route('/')
def index() -> Response:
    """首页端点"""
    logger.info("访问首页")
    return jsonify({
        "message": "Enhanced CapCut API Server is running",
        "version": VERSION,
        "timestamp": time.time(),
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": str(datetime.now() - START_TIME).split('.')[0],
        "environment": "enhanced"
    })

@app.route('/health')
def health_check() -> Response:
    """健康检查端点"""
    logger.info("健康检查")
    uptime = datetime.now() - START_TIME
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "uptime_seconds": uptime.total_seconds(),
    })

@app.route('/status')
def server_status() -> Response:
    """服务器状态端点"""
    logger.info("查询服务器状态")
    uptime = datetime.now() - START_TIME
    return jsonify({
        "status": "running",
        "timestamp": time.time(),
        "start_time": START_TIME.strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": str(uptime).split('.')[0],
    })

@app.route('/echo', methods=['POST'])
def echo() -> Response:
    """回显端点"""
    logger.info("接收到回显请求")
    try:
        data = request.get_json(silent=True) or {}
        return jsonify({
            "status": "success",
            "timestamp": time.time(),
            "echo": data,
        })
    except Exception as e:
        logger.error(f"回显处理错误: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "无法处理请求数据",
            "error": str(e)
        }), 400

@app.errorhandler(Exception)
def handle_exception(e: Exception) -> Union[Response, Tuple[Response, int]]:
    """全局异常处理"""
    if isinstance(e, HTTPException):
        response = e.get_response()
        response.data = jsonify({
            "status": "error",
            "code": e.code,
            "message": e.description,
        }).data
        response.content_type = "application/json"
        return response
    
    error_id = f"{int(time.time())}-{hash(str(e)) % 10000:04d}"
    logger.error(f"未处理异常 [{error_id}]: {str(e)}", exc_info=True)
    
    return jsonify({
        "status": "error",
        "code": 500,
        "message": "服务器内部错误",
        "error_id": error_id,
    }), 500

if __name__ == '__main__':
    logger.info(f"启动增强版CapCut API服务器在 {HOST}:{PORT}...")
    app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True)