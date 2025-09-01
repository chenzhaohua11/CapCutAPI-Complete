"""
优化管理器
整合所有优化模块，提供统一的配置和监控接口
实现端到端的性能优化解决方案
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import threading

from .performance_monitor import metrics_collector, tracker, dashboard
from .resource_scheduler import scheduler, auto_scaler
from .cache_optimizer import optimizer
from .async_media_processor import AsyncMediaProcessor
from .intelligent_cache import IntelligentCache

logger = logging.getLogger(__name__)

@dataclass
class OptimizationConfig:
    """优化配置"""
    # 性能监控配置
    enable_monitoring: bool = True
    monitoring_interval: int = 5
    alert_thresholds: Dict[str, float] = None
    
    # 资源调度配置
    enable_auto_scaling: bool = True
    max_concurrent_tasks: int = 10
    scaling_interval: int = 30
    
    # 缓存优化配置
    enable_cache_optimization: bool = True
    cache_max_size: int = 1000
    cache_ttl: int = 300
    
    # 媒体处理配置
    enable_async_processing: bool = True
    max_concurrent_downloads: int = 5
    download_timeout: int = 30
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                'error_rate': 5.0,
                'response_time': 10.0,
                'memory_usage': 80.0,
                'cpu_usage': 90.0
            }

class OptimizationManager:
    """优化管理器主类"""
    
    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.is_running = False
        self.optimization_thread = None
        self.media_processor = None
        
        # 状态监控
        self.status = {
            'monitoring': False,
            'resource_scheduling': False,
            'cache_optimization': False,
            'media_processing': False,
            'start_time': None,
            'uptime': 0
        }
        
        # 性能指标
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'cache_hit_rate': 0.0,
            'resource_utilization': 0.0
        }
    
    def initialize(self):
        """初始化优化系统"""
        try:
            logger.info("Initializing optimization system...")
            
            # 初始化媒体处理器
            if self.config.enable_async_processing:
                self.media_processor = AsyncMediaProcessor()
                self.status['media_processing'] = True
                logger.info("Async media processor initialized")
            
            # 配置资源调度器
            if self.config.enable_auto_scaling:
                scheduler.max_concurrent_tasks = self.config.max_concurrent_tasks
                scheduler.start()
                auto_scaler.start_monitoring(self.config.scaling_interval)
                self.status['resource_scheduling'] = True
                logger.info("Resource scheduler configured")
            
            # 配置缓存优化器
            if self.config.enable_cache_optimization:
                optimizer.max_size = self.config.cache_max_size
                optimizer.start()
                self.status['cache_optimization'] = True
                logger.info("Cache optimizer configured")
            
            # 启动性能监控
            if self.config.enable_monitoring:
                metrics_collector.start()
                self.status['monitoring'] = True
                logger.info("Performance monitoring started")
            
            self.status['start_time'] = time.time()
            self.is_running = True
            
            logger.info("Optimization system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize optimization system: {e}")
            raise
    
    def shutdown(self):
        """关闭优化系统"""
        try:
            logger.info("Shutting down optimization system...")
            
            if self.config.enable_monitoring:
                metrics_collector.stop()
                self.status['monitoring'] = False
            
            if self.config.enable_auto_scaling:
                auto_scaler.stop_monitoring()
                scheduler.stop()
                self.status['resource_scheduling'] = False
            
            if self.config.enable_cache_optimization:
                optimizer.stop()
                self.status['cache_optimization'] = False
            
            if self.media_processor:
                self.media_processor = None
                self.status['media_processing'] = False
            
            self.is_running = False
            logger.info("Optimization system shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        current_time = time.time()
        
        status = {
            'optimization_status': self.status,
            'uptime': current_time - self.status['start_time'] if self.status['start_time'] else 0,
            'config': asdict(self.config),
            'performance_metrics': self.performance_metrics
        }
        
        # 添加各模块状态
        if self.status['monitoring']:
            status['monitoring_stats'] = dashboard.get_realtime_stats()
        
        if self.status['resource_scheduling']:
            status['scheduler_stats'] = scheduler.get_scheduler_stats()
        
        if self.status['cache_optimization']:
            status['cache_stats'] = optimizer.get_stats()
        
        return status
    
    def optimize_endpoint(self, endpoint_name: str, optimization_type: str = "balanced"):
        """优化特定端点"""
        optimizations = {
            "balanced": {
                "cache_ttl": 300,
                "max_concurrent": 5,
                "priority": "normal"
            },
            "performance": {
                "cache_ttl": 600,
                "max_concurrent": 10,
                "priority": "high"
            },
            "memory_efficient": {
                "cache_ttl": 120,
                "max_concurrent": 3,
                "priority": "low"
            }
        }
        
        config = optimizations.get(optimization_type, optimizations["balanced"])
        
        # 应用优化配置
        if self.config.enable_cache_optimization:
            optimizer.strategy = AdaptiveTTLStrategy(base_ttl=config["cache_ttl"])
        
        if self.config.enable_auto_scaling:
            scheduler.adjust_concurrency(config["max_concurrent"])
        
        logger.info(f"Applied {optimization_type} optimization to {endpoint_name}")
        return config
    
    def get_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        report = {
            'timestamp': time.time(),
            'summary': {
                'total_requests': self.performance_metrics['total_requests'],
                'success_rate': (
                    self.performance_metrics['successful_requests'] / 
                    max(self.performance_metrics['total_requests'], 1)
                ) * 100,
                'average_response_time': self.performance_metrics['average_response_time'],
                'cache_hit_rate': self.performance_metrics['cache_hit_rate'],
                'resource_utilization': self.performance_metrics['resource_utilization']
            },
            'recommendations': self._generate_recommendations()
        }
        
        # 添加详细分析
        if self.status['monitoring']:
            report['detailed_analysis'] = dashboard.get_realtime_stats()
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 基于缓存命中率
        if self.performance_metrics['cache_hit_rate'] < 70:
            recommendations.append("考虑增加缓存大小或调整TTL策略")
        
        # 基于响应时间
        if self.performance_metrics['average_response_time'] > 5.0:
            recommendations.append("考虑增加并发处理任务数")
        
        # 基于资源使用
        if self.performance_metrics['resource_utilization'] > 90:
            recommendations.append("系统资源使用过高，考虑扩容或优化算法")
        
        # 基于错误率
        error_rate = (
            (self.performance_metrics['total_requests'] - 
             self.performance_metrics['successful_requests']) /
            max(self.performance_metrics['total_requests'], 1)
        ) * 100
        
        if error_rate > 5:
            recommendations.append("错误率较高，建议检查错误日志和异常处理")
        
        return recommendations
    
    def reset_metrics(self):
        """重置性能指标"""
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'cache_hit_rate': 0.0,
            'resource_utilization': 0.0
        }
        
        if self.config.enable_cache_optimization:
            optimizer.metrics = CacheMetrics()
        
        logger.info("Performance metrics reset")
    
    def export_config(self, filename: str = None) -> str:
        """导出优化配置"""
        config_data = {
            'optimization_config': asdict(self.config),
            'system_status': self.get_system_status(),
            'performance_report': self.get_performance_report(),
            'export_time': time.time()
        }
        
        if filename is None:
            filename = f"optimization_config_{int(time.time())}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Optimization configuration exported to {filename}")
        return filename
    
    def import_config(self, filename: str):
        """导入优化配置"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 应用配置
            new_config = OptimizationConfig(**config_data['optimization_config'])
            self.config = new_config
            
            # 重新初始化
            self.shutdown()
            self.initialize()
            
            logger.info(f"Optimization configuration imported from {filename}")
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            raise

# 全局实例
optimization_manager = OptimizationManager()

# 装饰器
async def optimized_async(func, endpoint_name: str = "generic"):
    """优化异步函数的装饰器"""
    async def wrapper(*args, **kwargs):
        optimization_manager.performance_metrics['total_requests'] += 1
        
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            optimization_manager.performance_metrics['successful_requests'] += 1
            
            # 更新响应时间
            duration = time.time() - start_time
            old_avg = optimization_manager.performance_metrics['average_response_time']
            new_avg = (old_avg * (optimization_manager.performance_metrics['total_requests'] - 1) + duration) / optimization_manager.performance_metrics['total_requests']
            optimization_manager.performance_metrics['average_response_time'] = new_avg
            
            return result
            
        except Exception as e:
            optimization_manager.performance_metrics['failed_requests'] += 1
            raise
    
    return wrapper

def optimized_sync(func, endpoint_name: str = "generic"):
    """优化同步函数的装饰器"""
    def wrapper(*args, **kwargs):
        optimization_manager.performance_metrics['total_requests'] += 1
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            optimization_manager.performance_metrics['successful_requests'] += 1
            
            # 更新响应时间
            duration = time.time() - start_time
            old_avg = optimization_manager.performance_metrics['average_response_time']
            new_avg = (old_avg * (optimization_manager.performance_metrics['total_requests'] - 1) + duration) / optimization_manager.performance_metrics['total_requests']
            optimization_manager.performance_metrics['average_response_time'] = new_avg
            
            return result
            
        except Exception as e:
            optimization_manager.performance_metrics['failed_requests'] += 1
            raise
    
    return wrapper

# 使用示例
async def example_usage():
    """使用示例"""
    
    # 配置优化系统
    config = OptimizationConfig(
        enable_monitoring=True,
        enable_auto_scaling=True,
        enable_cache_optimization=True,
        enable_async_processing=True,
        max_concurrent_tasks=8,
        cache_max_size=2000
    )
    
    # 初始化
    optimization_manager.config = config
    optimization_manager.initialize()
    
    try:
        # 获取系统状态
        status = optimization_manager.get_system_status()
        print("系统状态:", json.dumps(status, indent=2, default=str))
        
        # 优化特定端点
        optimization_manager.optimize_endpoint("video_processing", "performance")
        
        # 模拟一些操作
        await asyncio.sleep(2)
        
        # 获取性能报告
        report = optimization_manager.get_performance_report()
        print("性能报告:", json.dumps(report, indent=2, default=str))
        
        # 导出配置
        config_file = optimization_manager.export_config()
        print(f"配置已导出到: {config_file}")
        
    finally:
        # 关闭系统
        optimization_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(example_usage())