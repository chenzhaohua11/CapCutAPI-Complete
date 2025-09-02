"""统一配置管理 - 精简优化版

整合所有配置到一个文件中，提供类型安全和默认值。
支持从环境变量、配置文件加载配置，并提供类型转换和验证。

使用示例:
    from config import config
    
    # 获取配置
    port = config.server.port
    debug = config.server.debug
    
    # 获取配置字典
    server_config = config.get('server')
    
    # 更新配置
    config.update('server', 'port', 8080)
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import os

@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    max_workers: int = 4

@dataclass
class MediaConfig:
    """媒体处理配置"""
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_duration: int = 120  # 2分钟
    supported_formats: list = None
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ["mp4", "mp3", "jpg", "png", "gif", "mov", "avi"]

@dataclass
class CacheConfig:
    """缓存配置"""
    max_cache_size: int = 1000
    cache_ttl: int = 3600  # 1小时
    enable_redis: bool = False
    redis_url: str = "redis://localhost:6379"

@dataclass
class CapCutConfig:
    """剪映配置"""
    is_capcut_env: bool = True
    draft_domain: str = "http://localhost:5000"
    preview_router: str = "/preview"
    default_width: int = 1080
    default_height: int = 1920

@dataclass
class OptimizationConfig:
    """优化配置
    
    控制API的性能和行为优化选项。
    """
    # 异步处理选项
    enable_async: bool = True                # 启用异步处理
    max_concurrent_tasks: int = 10           # 最大并发任务数
    thread_pool_size: int = 8                # 线程池大小
    task_queue_size: int = 100               # 任务队列大小
    large_file_threshold: int = 5 * 1024 * 1024  # 大文件阈值（5MB）
    
    # 缓存选项
    enable_cache: bool = True                # 启用缓存
    cache_ttl: int = 3600                    # 缓存生存时间（秒）
    max_cache_size: int = 1000               # 最大缓存项数
    cache_cleanup_interval: int = 300        # 缓存清理间隔（秒）
    
    # 性能优化选项
    enable_compression: bool = True          # 启用响应压缩
    compression_level: int = 6               # 压缩级别（1-9）
    compression_min_size: int = 1024         # 最小压缩大小（字节）
    
    # 超时和重试选项
    timeout: int = 30                        # 请求超时（秒）
    retry_count: int = 3                     # 重试次数
    retry_delay: int = 1                     # 重试延迟（秒）
    
    # 限流选项
    enable_rate_limiting: bool = False       # 启用请求限流
    rate_limit_per_minute: int = 60          # 每分钟请求限制
    rate_limit_burst: int = 10               # 突发请求限制
    
    # 监控和日志选项
    enable_performance_tracking: bool = True  # 启用性能跟踪
    log_slow_requests: bool = True           # 记录慢请求
    slow_request_threshold: float = 1.0      # 慢请求阈值（秒）

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.server = ServerConfig()
        self.media = MediaConfig()
        self.cache = CacheConfig()
        self.capcut = CapCutConfig()
        self.optimization = OptimizationConfig()
        
        # 从环境变量加载配置
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        env_mappings = {
            'CAPCUT_HOST': ('server', 'host'),
            'CAPCUT_PORT': ('server', 'port', int),
            'CAPCUT_DEBUG': ('server', 'debug', bool),
            'MAX_FILE_SIZE': ('media', 'max_file_size', int),
            'MAX_DURATION': ('media', 'max_duration', int),
            'REDIS_URL': ('cache', 'redis_url'),
            'IS_CAPCUT_ENV': ('capcut', 'is_capcut_env', bool),
        }
        
        for env_key, (section, key, *type_conv) in env_mappings.items():
            if env_key in os.environ:
                value = os.environ[env_key]
                if type_conv:
                    if type_conv[0] == bool:
                        value = value.lower() in ('true', '1', 'yes')
                    else:
                        value = type_conv[0](value)
                
                section_obj = getattr(self, section)
                setattr(section_obj, key, value)
    
    def get(self, section: str, key: Optional[str] = None) -> Any:
        """获取配置值"""
        if key is None:
            return asdict(getattr(self, section))
        return getattr(getattr(self, section), key)
    
    def update(self, section: str, key: str, value: Any):
        """更新配置值"""
        setattr(getattr(self, section), key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'server': asdict(self.server),
            'media': asdict(self.media),
            'cache': asdict(self.cache),
            'capcut': asdict(self.capcut),
            'optimization': asdict(self.optimization)
        }

# 全局配置实例
config = ConfigManager()

# 向后兼容的常量
IS_CAPCUT_ENV = config.capcut.is_capcut_env
DRAFT_DOMAIN = config.capcut.draft_domain
PREVIEW_ROUTER = config.capcut.preview_router
PORT = config.server.port

# 简化的本地设置（可删除旧的local.py）
if os.path.exists('settings/local.py'):
    try:
        from settings.local import *
    except ImportError:
        pass