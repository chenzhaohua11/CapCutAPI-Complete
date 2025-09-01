"""
统一工具模块 - 精简优化版
整合所有工具函数到一个文件中
"""

import os
import json
import uuid
import time
from typing import Any, Dict, Optional, List
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileUtils:
    """文件工具类"""
    
    @staticmethod
    def ensure_dir(path: str) -> None:
        """确保目录存在"""
        Path(path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def save_json(data: Dict[str, Any], filepath: str) -> bool:
        """保存JSON文件"""
        try:
            FileUtils.ensure_dir(os.path.dirname(filepath))
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存JSON失败: {e}")
            return False
    
    @staticmethod
    def load_json(filepath: str) -> Optional[Dict[str, Any]]:
        """加载JSON文件"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载JSON失败: {e}")
        return None
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """获取文件扩展名"""
        return os.path.splitext(filename)[1].lower().lstrip('.')
    
    @staticmethod
    def generate_unique_filename(prefix: str = "", extension: str = "") -> str:
        """生成唯一文件名"""
        timestamp = int(time.time())
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{prefix}_{timestamp}_{unique_id}"
        if extension:
            filename = f"{filename}.{extension.lstrip('.')}"
        return filename

class ValidationUtils:
    """验证工具类"""
    
    @staticmethod
    def validate_media_params(params: Dict[str, Any]) -> Dict[str, str]:
        """验证媒体参数"""
        errors = {}
        
        # 验证时间参数
        timeline = params.get('timeline', {})
        if 'start' in timeline and 'duration' in timeline:
            if timeline['start'] < 0:
                errors['start'] = "开始时间不能为负"
            if timeline['duration'] <= 0:
                errors['duration'] = "持续时间必须大于0"
        
        # 验证变换参数
        transform = params.get('transform', {})
        if 'scale' in transform:
            scale = transform['scale']
            if not isinstance(scale, (int, float)) or scale <= 0:
                errors['scale'] = "缩放比例必须为正数"
        
        # 验证速度参数
        speed = params.get('speed', 1.0)
        if not isinstance(speed, (int, float)) or speed <= 0:
            errors['speed'] = "速度必须为正数"
        
        return errors
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()

class TimeUtils:
    """时间工具类"""
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    
    @staticmethod
    def get_timestamp() -> int:
        """获取当前时间戳"""
        return int(time.time())

class ResponseUtils:
    """响应工具类"""
    
    @staticmethod
    def success(data: Any = None, message: str = "success") -> Dict[str, Any]:
        """成功响应"""
        return {
            "code": 200,
            "message": message,
            "data": data,
            "success": True
        }
    
    @staticmethod
    def error(message: str = "error", code: int = 400, data: Any = None) -> Dict[str, Any]:
        """错误响应"""
        return {
            "code": code,
            "message": message,
            "data": data,
            "success": False
        }

class CacheUtils:
    """缓存工具类"""
    
    @staticmethod
    def get_cache_key(*args) -> str:
        """生成缓存键"""
        return ":".join(str(arg) for arg in args)
    
    @staticmethod
    def clear_temp_files(temp_dir: str, max_age: int = 3600) -> int:
        """清理临时文件"""
        cleared = 0
        try:
            temp_path = Path(temp_dir)
            if temp_path.exists():
                current_time = time.time()
                for file_path in temp_path.iterdir():
                    if file_path.is_file():
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > max_age:
                            file_path.unlink()
                            cleared += 1
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
        return cleared

# 统一导出所有工具
utils = {
    'file': FileUtils,
    'validation': ValidationUtils,
    'time': TimeUtils,
    'response': ResponseUtils,
    'cache': CacheUtils
}

# 向后兼容的快捷函数
ensure_dir = FileUtils.ensure_dir
save_json = FileUtils.save_json
load_json = FileUtils.load_json
format_duration = TimeUtils.format_duration
success_response = ResponseUtils.success
error_response = ResponseUtils.error