"""性能监控API模块

提供性能监控数据的REST API接口，包括系统健康状态、性能指标、资源使用情况等。
支持实时监控、历史数据查询和告警配置。
"""

from flask import Blueprint, jsonify, request, current_app
import logging
import time
from typing import Dict, Any, List

from optimized_modules.performance_monitor import (
    metrics_collector, dashboard, alert_manager, tracker
)
from utils import ResponseFormatter

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
performance_api = Blueprint('performance_api', __name__, url_prefix='/api/v1/performance')

@performance_api.route('/health', methods=['GET'])
def get_health():
    """获取系统健康状态
    
    Returns:
        JSON响应，包含系统健康状态信息
    """
    try:
        health_data = metrics_collector.get_system_health()
        return ResponseFormatter.success(health_data, "系统健康状态获取成功")
    except Exception as e:
        logger.error(f"获取系统健康状态失败: {e}", exc_info=True)
        return ResponseFormatter.error(f"获取系统健康状态失败: {str(e)}", status_code=500)

@performance_api.route('/stats', methods=['GET'])
def get_stats():
    """获取性能统计信息
    
    Query Parameters:
        time_range: 时间范围，可选值为 5m, 15m, 1h, 6h, 24h，默认为 1h
        
    Returns:
        JSON响应，包含性能统计信息
    """
    try:
        time_range = request.args.get('time_range', '1h')
        
        # 将时间范围转换为分钟
        range_mapping = {
            '5m': 5,
            '15m': 15,
            '1h': 60,
            '6h': 360,
            '24h': 1440
        }
        
        minutes = range_mapping.get(time_range, 60)
        stats = metrics_collector.get_metrics_summary(last_n_minutes=minutes)
        
        return ResponseFormatter.success(stats, f"过去{time_range}的性能统计获取成功")
    except Exception as e:
        logger.error(f"获取性能统计信息失败: {e}", exc_info=True)
        return ResponseFormatter.error(f"获取性能统计信息失败: {str(e)}", status_code=500)

@performance_api.route('/dashboard', methods=['GET'])
def get_dashboard():
    """获取性能仪表板数据
    
    Returns:
        JSON响应，包含性能仪表板数据
    """
    try:
        dashboard_data = dashboard.get_realtime_stats()
        return ResponseFormatter.success(dashboard_data, "性能仪表板数据获取成功")
    except Exception as e:
        logger.error(f"获取性能仪表板数据失败: {e}", exc_info=True)
        return ResponseFormatter.error(f"获取性能仪表板数据失败: {str(e)}", status_code=500)

@performance_api.route('/operations', methods=['GET'])
def get_operations():
    """获取操作性能分解
    
    Returns:
        JSON响应，包含各操作的性能数据
    """
    try:
        operations_data = dashboard.get_operation_breakdown()
        return ResponseFormatter.success(operations_data, "操作性能数据获取成功")
    except Exception as e:
        logger.error(f"获取操作性能数据失败: {e}", exc_info=True)
        return ResponseFormatter.error(f"获取操作性能数据失败: {str(e)}", status_code=500)

@performance_api.route('/alerts/thresholds', methods=['GET', 'POST'])
def manage_alert_thresholds():
    """获取或更新告警阈值
    
    Methods:
        GET: 获取当前告警阈值
        POST: 更新告警阈值
        
    Returns:
        JSON响应，包含告警阈值信息
    """
    try:
        if request.method == 'GET':
            return ResponseFormatter.success(alert_manager.alert_thresholds, "告警阈值获取成功")
        else:  # POST
            data = request.get_json()
            if not data:
                return ResponseFormatter.error("无效的请求数据", status_code=400)
            
            # 更新阈值
            for key, value in data.items():
                if key in alert_manager.alert_thresholds:
                    try:
                        alert_manager.alert_thresholds[key] = float(value)
                    except (ValueError, TypeError):
                        return ResponseFormatter.error(f"无效的阈值: {key}={value}", status_code=400)
            
            return ResponseFormatter.success(alert_manager.alert_thresholds, "告警阈值更新成功")
    except Exception as e:
        logger.error(f"管理告警阈值失败: {e}", exc_info=True)
        return ResponseFormatter.error(f"管理告警阈值失败: {str(e)}", status_code=500)

@performance_api.route('/active-requests', methods=['GET'])
def get_active_requests():
    """获取当前活跃请求
    
    Returns:
        JSON响应，包含当前活跃请求列表
    """
    try:
        active_requests = metrics_collector.get_active_requests() if hasattr(metrics_collector, 'get_active_requests') else []
        return ResponseFormatter.success(active_requests, "活跃请求获取成功")
    except Exception as e:
        logger.error(f"获取活跃请求失败: {e}", exc_info=True)
        return ResponseFormatter.error(f"获取活跃请求失败: {str(e)}", status_code=500)

@performance_api.route('/slow-requests', methods=['GET'])
def get_slow_requests():
    """获取慢请求列表
    
    Query Parameters:
        limit: 返回的最大记录数，默认为20
        
    Returns:
        JSON响应，包含慢请求列表
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        slow_requests = metrics_collector.get_slow_requests()[:limit] if hasattr(metrics_collector, 'get_slow_requests') else []
        return ResponseFormatter.success(slow_requests, "慢请求列表获取成功")
    except Exception as e:
        logger.error(f"获取慢请求列表失败: {e}", exc_info=True)
        return ResponseFormatter.error(f"获取慢请求列表失败: {str(e)}", status_code=500)

@performance_api.route('/resource-usage', methods=['GET'])
def get_resource_usage():
    """获取资源使用情况
    
    Returns:
        JSON响应，包含资源使用情况
    """
    try:
        resource_usage = metrics_collector.get_resource_usage() if hasattr(metrics_collector, 'get_resource_usage') else {}
        return ResponseFormatter.success(resource_usage, "资源使用情况获取成功")
    except Exception as e:
        logger.error(f"获取资源使用情况失败: {e}", exc_info=True)
        return ResponseFormatter.error(f"获取资源使用情况失败: {str(e)}", status_code=500)

# 注册蓝图的函数
def register_performance_api(app):
    """注册性能监控API蓝图
    
    Args:
        app: Flask应用实例
    """
    app.register_blueprint(performance_api)
    logger.info("性能监控API已注册")