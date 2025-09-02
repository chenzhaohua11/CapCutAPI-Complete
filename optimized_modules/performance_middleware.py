"""性能监控中间件模块

为Flask应用提供性能监控中间件，自动跟踪所有请求的性能指标。
包括请求时间、响应状态、资源使用情况等。
"""

import time
import logging
import traceback
from functools import wraps
from flask import request, g, Flask
from typing import Dict, Any, Callable, Optional

from optimized_modules.performance_monitor import metrics_collector, tracker
from config import config

# 配置日志
logger = logging.getLogger(__name__)

class PerformanceMiddleware:
    """性能监控中间件
    
    自动监控所有Flask请求的性能指标，包括请求时间、响应状态等。
    """
    
    def __init__(self, app: Optional[Flask] = None):
        """初始化中间件
        
        Args:
            app: Flask应用实例，可选
        """
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """初始化应用
        
        Args:
            app: Flask应用实例
        """
        # 请求前钩子
        app.before_request(self.before_request)
        
        # 请求后钩子
        app.after_request(self.after_request)
        
        # 请求异常钩子
        app.teardown_request(self.teardown_request)
        
        # 启用性能跟踪
        self.enable_performance_tracking = config.optimization.enable_performance_tracking
        self.log_slow_requests = config.optimization.log_slow_requests
        self.slow_request_threshold = config.optimization.slow_request_threshold
        
        logger.info("性能监控中间件已初始化")
    
    def before_request(self) -> None:
        """请求前处理
        
        记录请求开始时间和相关信息
        """
        if not self.enable_performance_tracking:
            return
        
        # 记录请求开始时间
        g.start_time = time.time()
        
        # 记录请求信息
        g.request_info = {
            'method': request.method,
            'path': request.path,
            'endpoint': request.endpoint,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'content_length': request.content_length or 0,
        }
        
        # 添加到活跃请求列表
        if hasattr(metrics_collector, 'add_active_request'):
            metrics_collector.add_active_request(g.request_info)
    
    def after_request(self, response):
        """请求后处理
        
        记录请求结束时间和响应信息
        
        Args:
            response: Flask响应对象
            
        Returns:
            Flask响应对象
        """
        if not self.enable_performance_tracking or not hasattr(g, 'start_time'):
            return response
        
        # 计算请求处理时间
        end_time = time.time()
        duration = end_time - g.start_time
        
        # 记录响应信息
        response_info = {
            'status_code': response.status_code,
            'content_length': response.content_length or 0,
            'duration': duration,
        }
        
        # 合并请求和响应信息
        request_data = {**g.request_info, **response_info}
        
        # 记录性能指标
        operation = f"{request.method}:{request.path}"
        metrics_collector.record_operation(operation, duration, response.status_code < 400)
        
        # 从活跃请求列表中移除
        if hasattr(metrics_collector, 'remove_active_request'):
            metrics_collector.remove_active_request(g.request_info)
        
        # 记录慢请求
        if self.log_slow_requests and duration > self.slow_request_threshold:
            if hasattr(metrics_collector, 'add_slow_request'):
                metrics_collector.add_slow_request(request_data)
            logger.warning(f"慢请求: {request.method} {request.path} - {duration:.2f}秒")
        
        return response
    
    def teardown_request(self, exception):
        """请求异常处理
        
        记录请求异常信息
        
        Args:
            exception: 异常对象
        """
        if not self.enable_performance_tracking or not hasattr(g, 'start_time') or not exception:
            return
        
        # 计算请求处理时间
        end_time = time.time()
        duration = end_time - g.start_time
        
        # 记录异常信息
        error_info = {
            'error': str(exception),
            'traceback': traceback.format_exc(),
            'duration': duration,
        }
        
        # 合并请求和异常信息
        request_data = {**g.request_info, **error_info}
        
        # 记录性能指标
        operation = f"{request.method}:{request.path}"
        metrics_collector.record_operation(operation, duration, False)
        
        # 从活跃请求列表中移除
        if hasattr(metrics_collector, 'remove_active_request'):
            metrics_collector.remove_active_request(g.request_info)
        
        # 记录错误请求
        if hasattr(metrics_collector, 'add_error_request'):
            metrics_collector.add_error_request(request_data)
        
        logger.error(f"请求异常: {request.method} {request.path} - {str(exception)}")

# 性能监控装饰器
def monitor_endpoint(operation: str = None, metadata: Dict[str, Any] = None):
    """端点性能监控装饰器
    
    用于监控特定端点的性能指标
    
    Args:
        operation: 操作名称，默认为None（使用端点名称）
        metadata: 元数据，默认为None
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 确定操作名称
            op_name = operation or f"{request.endpoint}"
            
            # 使用性能追踪器
            with tracker.track_operation(op_name, metadata):
                return func(*args, **kwargs)
        return wrapper
    return decorator

# 创建中间件实例
performance_middleware = PerformanceMiddleware()

# 注册中间件的函数
def register_performance_middleware(app: Flask) -> None:
    """注册性能监控中间件
    
    Args:
        app: Flask应用实例
    """
    performance_middleware.init_app(app)
    logger.info("性能监控中间件已注册")