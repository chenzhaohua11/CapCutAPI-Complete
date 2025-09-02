"""增强版CapCut API服务器

提供基本的健康检查和状态监控功能，并集成了性能监控模块。
该服务器包含核心功能和性能监控功能，适用于测试环境或资源受限的部署场景。

功能：
- 健康检查：提供系统状态监控
- 错误处理：统一的异常处理机制
- 环境配置：支持通过环境变量配置
- 性能监控：提供API性能监控和资源使用跟踪

使用方法：
    python enhanced_server.py

环境变量：
    CAPCUT_HOST: 服务器主机地址，默认为0.0.0.0
    CAPCUT_PORT: 服务器端口，默认为5000
    CAPCUT_DEBUG: 调试模式，默认为false
"""

import os
import time
import logging
import socket
import platform
from datetime import datetime
from typing import Dict, Any, Tuple, Union

from flask import Flask, jsonify, request, Response
from werkzeug.exceptions import HTTPException

# 导入性能监控模块
from optimized_modules.performance_api import register_performance_api
from optimized_modules.performance_middleware import register_performance_middleware
from optimized_modules.performance_monitor import metrics_collector, dashboard, alert_manager

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
    """首页端点
    
    返回服务器基本信息和状态
    
    Returns:
        Response: 包含服务器信息的JSON响应
    """
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
    """健康检查端点
    
    提供详细的系统健康状态信息
    
    Returns:
        Response: 包含健康状态信息的JSON响应
    """
    logger.info("健康检查")
    
    # 获取系统健康状态
    system_health = metrics_collector.get_system_health()
    
    # 收集系统信息
    system_info = {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "memory_available": system_health.get("memory_available", "N/A"),
        "cpu_usage": system_health.get("cpu_usage", "N/A"),
        "disk_usage": system_health.get("disk_usage", "N/A")
    }
    
    # 计算运行时间
    uptime = datetime.now() - START_TIME
    
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "uptime_seconds": uptime.total_seconds(),
        "uptime_human": str(uptime).split('.')[0],
        "system_info": system_info,
        "health_status": system_health.get("status", "unknown")
    })

@app.route('/status')
def server_status() -> Response:
    """服务器状态端点
    
    提供详细的服务器运行状态信息
    
    Returns:
        Response: 包含服务器状态信息的JSON响应
    """
    logger.info("查询服务器状态")
    
    # 计算运行时间
    uptime = datetime.now() - START_TIME
    
    # 获取性能指标
    performance_metrics = metrics_collector.get_metrics_summary(last_n_minutes=5)
    
    # 收集环境信息
    env_info = {
        "debug_mode": DEBUG,
        "host": HOST,
        "port": PORT,
        "version": VERSION,
        "python_path": os.path.dirname(os.__file__)
    }
    
    return jsonify({
        "status": "running",
        "timestamp": time.time(),
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "start_time": START_TIME.strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": str(uptime).split('.')[0],
        "environment": env_info,
        "performance": {
            "request_count": performance_metrics.get("total_operations", 0),
            "success_rate": performance_metrics.get("success_rate", 100),
            "avg_response_time": performance_metrics.get("avg_duration", 0),
            "p95_response_time": performance_metrics.get("p95_duration", 0)
        }
    })


@app.route('/echo', methods=['POST'])
def echo() -> Response:
    """回显端点
    
    将接收到的JSON数据回显给客户端，用于测试
    
    Returns:
        Response: 包含接收数据的JSON响应
    """
    logger.info("接收到回显请求")
    
    try:
        data = request.get_json(silent=True) or {}
        return jsonify({
            "status": "success",
            "timestamp": time.time(),
            "echo": data,
            "headers": dict(request.headers),
            "method": request.method,
            "path": request.path
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
    """全局异常处理
    
    统一处理所有异常，返回格式化的JSON响应
    
    Args:
        e (Exception): 捕获的异常
        
    Returns:
        Union[Response, Tuple[Response, int]]: 格式化的错误响应
    """
    # 获取当前时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 处理HTTP异常
    if isinstance(e, HTTPException):
        logger.warning(f"HTTP异常: {e.code} - {e.description} - {str(e)}")
        response = e.get_response()
        response.data = jsonify({
            "status": "error",
            "code": e.code,
            "message": e.description,
            "timestamp": time.time(),
            "server_time": current_time,
            "error_type": e.__class__.__name__
        }).data
        response.content_type = "application/json"
        return response
    
    # 处理其他异常
    error_id = f"{int(time.time())}-{hash(str(e)) % 10000:04d}"
    logger.error(f"未处理异常 [{error_id}]: {str(e)}", exc_info=True)
    
    return jsonify({
        "status": "error",
        "code": 500,
        "message": "服务器内部错误",
        "timestamp": time.time(),
        "server_time": current_time,
        "error_id": error_id,
        "error_type": e.__class__.__name__
    }), 500

def print_server_info() -> None:
    """打印服务器信息到控制台"""
    separator = "=" * 50
    logger.info(separator)
    logger.info(f"增强版CapCut API服务器 v{VERSION}")
    logger.info(separator)
    logger.info(f"服务器地址: http://{HOST}:{PORT}/")
    logger.info(f"健康检查: http://{HOST}:{PORT}/health")
    logger.info(f"服务器状态: http://{HOST}:{PORT}/status")
    logger.info(f"性能监控: http://{HOST}:{PORT}/api/v1/performance/dashboard")
    logger.info(f"调试模式: {'启用' if DEBUG else '禁用'}")
    logger.info(f"启动时间: {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(separator)


if __name__ == '__main__':
    # 注册性能监控API
    register_performance_api(app)
    
    # 注册性能监控中间件
    register_performance_middleware(app)
    
    # 注册信号处理（仅在类Unix系统上）
    try:
        import signal
        def signal_handler(sig, frame):
            logger.info("接收到终止信号，正在关闭服务器...")
            exit(0)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("已注册信号处理器")
    except (ImportError, AttributeError):
        logger.info("当前平台不支持信号处理")
    
    # 打印服务器信息
    print_server_info()
    
    # 启动服务器
    logger.info(f"启动增强版CapCut API服务器在 {HOST}:{PORT}...")
    app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True)