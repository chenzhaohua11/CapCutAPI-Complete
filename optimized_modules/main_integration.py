"""
主应用集成模块
将优化系统无缝集成到现有的CapCutAPI应用中
提供配置、监控和性能优化的一体化解决方案
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import json
from datetime import datetime

# 添加优化模块路径
sys.path.insert(0, str(Path(__file__).parent))

from optimization_manager import optimization_manager, OptimizationConfig
from performance_monitor import metrics_collector, tracker
from resource_scheduler import scheduler, auto_scaler
from cache_optimizer import optimizer
from intelligent_cache import cache
from async_media_processor import AsyncMediaProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimization.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class CapCutAPIOptimizer:
    """CapCutAPI优化集成器"""
    
    def __init__(self):
        self.config = None
        self.is_initialized = False
        self.media_processor = None
        self.original_functions = {}
    
    def load_config(self, config_path: str = None) -> OptimizationConfig:
        """加载优化配置"""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'optimization.json')
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return OptimizationConfig(**config_data)
            else:
                # 创建默认配置
                config = OptimizationConfig()
                self.save_config(config, config_path)
                return config
                
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            return OptimizationConfig()
    
    def save_config(self, config: OptimizationConfig, config_path: str):
        """保存优化配置"""
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config.__dict__, f, indent=2, ensure_ascii=False)
            logger.info(f"Optimization config saved to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def initialize(self, config_path: str = None):
        """初始化优化系统"""
        try:
            logger.info("Initializing CapCutAPI optimization system...")
            
            # 加载配置
            self.config = self.load_config(config_path)
            optimization_manager.config = self.config
            
            # 初始化优化管理器
            optimization_manager.initialize()
            
            # 初始化媒体处理器
            self.media_processor = AsyncMediaProcessor()
            
            self.is_initialized = True
            logger.info("CapCutAPI optimization system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize optimization system: {e}")
            raise
    
    def shutdown(self):
        """关闭优化系统"""
        try:
            logger.info("Shutting down CapCutAPI optimization system...")
            
            optimization_manager.shutdown()
            
            if self.media_processor:
                self.media_processor = None
            
            self.is_initialized = False
            logger.info("CapCutAPI optimization system shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        if not self.is_initialized:
            return {'status': 'not_initialized', 'error': 'System not initialized'}
        
        try:
            status = optimization_manager.get_system_status()
            
            health = {
                'status': 'healthy' if status.get('optimization_status', {}).get('monitoring') else 'warning',
                'timestamp': datetime.now().isoformat(),
                'uptime': status.get('uptime', 0),
                'performance': status.get('performance_metrics', {}),
                'recommendations': optimization_manager.get_performance_report().get('recommendations', [])
            }
            
            return health
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def optimize_endpoint(self, endpoint_name: str, optimization_type: str = "balanced"):
        """优化特定端点"""
        if not self.is_initialized:
            logger.warning("System not initialized, skipping optimization")
            return
        
        try:
            config = optimization_manager.optimize_endpoint(endpoint_name, optimization_type)
            logger.info(f"Applied {optimization_type} optimization to {endpoint_name}")
            return config
        except Exception as e:
            logger.error(f"Failed to optimize endpoint {endpoint_name}: {e}")
    
    def get_performance_dashboard(self) -> Dict[str, Any]:
        """获取性能仪表板数据"""
        if not self.is_initialized:
            return {'error': 'System not initialized'}
        
        try:
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'system_health': self.get_system_health(),
                'performance_report': optimization_manager.get_performance_report(),
                'optimization_status': optimization_manager.get_system_status(),
                'cache_stats': optimizer.get_stats() if self.config.enable_cache_optimization else None,
                'scheduler_stats': scheduler.get_scheduler_stats() if self.config.enable_auto_scaling else None
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to get performance dashboard: {e}")
            return {'error': str(e)}

# 全局优化器实例
api_optimizer = CapCutAPIOptimizer()

# 集成装饰器
def optimize_async_endpoint(endpoint_name: str = None, optimization_type: str = "balanced"):
    """优化异步端点的装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not api_optimizer.is_initialized:
                return await func(*args, **kwargs)
            
            endpoint = endpoint_name or func.__name__
            
            # 应用优化配置
            api_optimizer.optimize_endpoint(endpoint, optimization_type)
            
            # 使用优化管理器包装
            from optimization_manager import optimized_async
            optimized_func = optimized_async(func, endpoint)
            
            return await optimized_func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator

def optimize_sync_endpoint(endpoint_name: str = None, optimization_type: str = "balanced"):
    """优化同步端点的装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not api_optimizer.is_initialized:
                return func(*args, **kwargs)
            
            endpoint = endpoint_name or func.__name__
            
            # 应用优化配置
            api_optimizer.optimize_endpoint(endpoint, optimization_type)
            
            # 使用优化管理器包装
            from optimization_manager import optimized_sync
            optimized_func = optimized_sync(func, endpoint)
            
            return optimized_func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator

# 集成到现有系统的辅助函数
def integrate_with_capcutapi():
    """集成到现有CapCutAPI系统"""
    try:
        from capcut_server import app
        
        # 初始化优化系统
        api_optimizer.initialize()
        
        # 添加健康检查端点
        @app.route('/api/health/optimization', methods=['GET'])
        def optimization_health():
            return api_optimizer.get_system_health()
        
        # 添加性能仪表板端点
        @app.route('/api/dashboard/performance', methods=['GET'])
        def performance_dashboard():
            return api_optimizer.get_performance_dashboard()
        
        # 添加配置管理端点
        @app.route('/api/config/optimization', methods=['GET', 'POST'])
        def optimization_config():
            if request.method == 'GET':
                return api_optimizer.get_performance_dashboard()
            elif request.method == 'POST':
                # 更新配置
                config_data = request.json
                new_config = OptimizationConfig(**config_data)
                api_optimizer.save_config(new_config)
                return {'status': 'success', 'message': 'Configuration updated'}
        
        logger.info("CapCutAPI optimization integration completed")
        
    except ImportError:
        logger.warning("CapCut server not found, skipping integration")
    except Exception as e:
        logger.error(f"Failed to integrate with CapCutAPI: {e}")

# 启动脚本
def main():
    """主启动函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CapCutAPI Optimization System')
    parser.add_argument('--config', type=str, help='Path to optimization config file')
    parser.add_argument('--init-only', action='store_true', help='Initialize and exit')
    parser.add_argument('--health-check', action='store_true', help='Run health check and exit')
    
    args = parser.parse_args()
    
    try:
        if args.health_check:
            # 运行健康检查
            api_optimizer.initialize(args.config)
            health = api_optimizer.get_system_health()
            print(json.dumps(health, indent=2, ensure_ascii=False))
            api_optimizer.shutdown()
            
        elif args.init_only:
            # 仅初始化
            api_optimizer.initialize(args.config)
            print("Optimization system initialized successfully")
            api_optimizer.shutdown()
            
        else:
            # 完整启动
            api_optimizer.initialize(args.config)
            integrate_with_capcutapi()
            
            print("CapCutAPI optimization system is running...")
            print("Health endpoint: /api/health/optimization")
            print("Dashboard endpoint: /api/dashboard/performance")
            
            # 保持运行
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                print("\nShutting down optimization system...")
                api_optimizer.shutdown()
                
    except Exception as e:
        logger.error(f"Failed to start optimization system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()