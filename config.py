"""
统一配置管理 - 精简优化版
整合所有配置到一个文件中，提供类型安全和默认值
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
    """优化配置"""
    enable_async: bool = True
    enable_cache: bool = True
    enable_compression: bool = True
    max_concurrent_tasks: int = 10
    timeout: int = 30

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