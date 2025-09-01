#!/usr/bin/env python3
"""
通用工具函数模块

提供CapCut API项目中常用的工具函数，包括文件操作、路径处理、日志配置、错误处理等
"""

import os
import json
import logging
import hashlib
import uuid
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import time
import re
import requests
from urllib.parse import urlparse, unquote
import zipfile
import tarfile

logger = logging.getLogger(__name__)

class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def ensure_dir(directory: str) -> bool:
        """确保目录存在"""
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            return False
    
    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = 'md5') -> Optional[str]:
        """计算文件哈希值"""
        try:
            hash_obj = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return None
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """获取文件大小（字节）"""
        try:
            return os.path.getsize(file_path)
        except Exception:
            return 0
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """获取文件详细信息"""
        try:
            stat = os.stat(file_path)
            return {
                "path": file_path,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "extension": Path(file_path).suffix.lower(),
                "filename": Path(file_path).name,
                "directory": str(Path(file_path).parent)
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return {}
    
    @staticmethod
    def safe_move(src: str, dst: str) -> bool:
        """安全移动文件"""
        try:
            FileUtils.ensure_dir(str(Path(dst).parent))
            shutil.move(src, dst)
            return True
        except Exception as e:
            logger.error(f"Failed to move {src} to {dst}: {e}")
            return False
    
    @staticmethod
    def safe_copy(src: str, dst: str) -> bool:
        """安全复制文件"""
        try:
            FileUtils.ensure_dir(str(Path(dst).parent))
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            logger.error(f"Failed to copy {src} to {dst}: {e}")
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")
            return False
    
    @staticmethod
    def list_files(
        directory: str,
        pattern: str = "*",
        recursive: bool = False,
        extensions: Optional[List[str]] = None
    ) -> List[str]:
        """列出文件"""
        try:
            path = Path(directory)
            if recursive:
                files = path.rglob(pattern)
            else:
                files = path.glob(pattern)
            
            file_list = [str(f) for f in files if f.is_file()]
            
            if extensions:
                extensions = [ext.lower() for ext in extensions]
                file_list = [f for f in file_list if Path(f).suffix.lower() in extensions]
            
            return sorted(file_list)
        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {e}")
            return []
    
    @staticmethod
    def create_temp_dir(prefix: str = "capcut_") -> str:
        """创建临时目录"""
        return tempfile.mkdtemp(prefix=prefix)
    
    @staticmethod
    def create_temp_file(suffix: str = "", prefix: str = "capcut_") -> str:
        """创建临时文件"""
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)
        return path
    
    @staticmethod
    def extract_archive(archive_path: str, extract_to: str) -> bool:
        """解压归档文件"""
        try:
            FileUtils.ensure_dir(extract_to)
            
            if archive_path.endswith(('.zip', '.ZIP')):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
            elif archive_path.endswith(('.tar', '.tar.gz', '.tgz')):
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_to)
            else:
                logger.error(f"Unsupported archive format: {archive_path}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to extract {archive_path}: {e}")
            return False
    
    @staticmethod
    def create_archive(files: List[str], archive_path: str, format: str = 'zip') -> bool:
        """创建归档文件"""
        try:
            FileUtils.ensure_dir(str(Path(archive_path).parent))
            
            if format == 'zip':
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                    for file in files:
                        if os.path.exists(file):
                            arcname = os.path.basename(file)
                            zip_ref.write(file, arcname)
            elif format == 'tar':
                with tarfile.open(archive_path, 'w') as tar_ref:
                    for file in files:
                        if os.path.exists(file):
                            arcname = os.path.basename(file)
                            tar_ref.add(file, arcname)
            else:
                logger.error(f"Unsupported archive format: {format}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to create archive {archive_path}: {e}")
            return False

class URLUtils:
    """URL处理工具类"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """验证URL有效性"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def get_filename_from_url(url: str) -> str:
        """从URL提取文件名"""
        try:
            parsed = urlparse(url)
            filename = unquote(os.path.basename(parsed.path))
            return filename or f"file_{int(time.time())}"
        except Exception:
            return f"file_{int(time.time())}"
    
    @staticmethod
    def download_file(
        url: str,
        output_path: str,
        timeout: int = 30,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """下载文件"""
        try:
            if not URLUtils.is_valid_url(url):
                return {"success": False, "error": "Invalid URL"}
            
            FileUtils.ensure_dir(str(Path(output_path).parent))
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            for attempt in range(max_retries):
                try:
                    response = session.get(url, timeout=timeout, stream=True)
                    response.raise_for_status()
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                    
                    return {
                        "success": True,
                        "file_path": output_path,
                        "file_size": downloaded,
                        "total_size": total_size,
                        "url": url
                    }
                    
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        return {"success": False, "error": str(e)}
                    time.sleep(2 ** attempt)  # 指数退避
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_url_info(url: str) -> Dict[str, Any]:
        """获取URL信息"""
        try:
            response = requests.head(url, timeout=10)
            return {
                "url": url,
                "status_code": response.status_code,
                "content_type": response.headers.get('content-type'),
                "content_length": int(response.headers.get('content-length', 0)),
                "last_modified": response.headers.get('last-modified'),
                "filename": URLUtils.get_filename_from_url(url)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

class StringUtils:
    """字符串处理工具类"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名"""
        # 移除或替换非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = filename.strip('._-')
        
        # 限制长度
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200 - len(ext)] + ext
        
        return filename or "untitled"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """截断文本"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """从文本中提取数字"""
        numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
        return [float(n) for n in numbers]
    
    @staticmethod
    def is_json_string(text: str) -> bool:
        """检查是否为JSON字符串"""
        try:
            json.loads(text)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

class TimeUtils:
    """时间处理工具类"""
    
    @staticmethod
    def get_timestamp() -> int:
        """获取当前时间戳"""
        return int(time.time())
    
    @staticmethod
    def format_timestamp(timestamp: int, format: str = '%Y-%m-%d %H:%M:%S') -> str:
        """格式化时间戳"""
        return datetime.fromtimestamp(timestamp).strftime(format)
    
    @staticmethod
    def parse_duration(duration_str: str) -> float:
        """解析时长字符串"""
        duration_str = duration_str.strip().lower()
        
        # 支持格式：1h30m, 2.5h, 90m, 3600s
        total_seconds = 0
        
        # 匹配小时
        hours = re.findall(r'(\d+(?:\.\d+)?)\s*h', duration_str)
        total_seconds += sum(float(h) * 3600 for h in hours)
        
        # 匹配分钟
        minutes = re.findall(r'(\d+(?:\.\d+)?)\s*m', duration_str)
        total_seconds += sum(float(m) * 60 for m in minutes)
        
        # 匹配秒
        seconds = re.findall(r'(\d+(?:\.\d+)?)\s*s', duration_str)
        total_seconds += sum(float(s) for s in seconds)
        
        # 如果没有单位，假设是秒
        if total_seconds == 0 and duration_str.isdigit():
            total_seconds = float(duration_str)
        
        return total_seconds
    
    @staticmethod
    def get_time_ago(timestamp: int) -> str:
        """获取相对时间描述"""
        now = datetime.now()
        past = datetime.fromtimestamp(timestamp)
        delta = now - past
        
        if delta.days > 365:
            years = delta.days // 365
            return f"{years} year{'s' if years != 1 else ''} ago"
        elif delta.days > 30:
            months = delta.days // 30
            return f"{months} month{'s' if months != 1 else ''} ago"
        elif delta.days > 0:
            return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "just now"

class ValidationUtils:
    """验证工具类"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """验证URL格式"""
        return URLUtils.is_valid_url(url)
    
    @staticmethod
    def is_valid_hex_color(color: str) -> bool:
        """验证十六进制颜色"""
        pattern = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
        return bool(re.match(pattern, color))
    
    @staticmethod
    def is_valid_video_file(file_path: str) -> bool:
        """验证视频文件"""
        valid_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
        return Path(file_path).suffix.lower() in valid_extensions
    
    @staticmethod
    def is_valid_audio_file(file_path: str) -> bool:
        """验证音频文件"""
        valid_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}
        return Path(file_path).suffix.lower() in valid_extensions
    
    @staticmethod
    def is_valid_image_file(file_path: str) -> bool:
        """验证图片文件"""
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        return Path(file_path).suffix.lower() in valid_extensions

class CacheUtils:
    """缓存工具类"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        FileUtils.ensure_dir(cache_dir)
    
    def get_cache_path(self, key: str) -> str:
        """获取缓存文件路径"""
        filename = f"{hashlib.md5(key.encode()).hexdigest()}.cache"
        return os.path.join(self.cache_dir, filename)
    
    def set(self, key: str, data: Any, expire_hours: int = 24) -> bool:
        """设置缓存"""
        try:
            cache_data = {
                "data": data,
                "timestamp": TimeUtils.get_timestamp(),
                "expire_hours": expire_hours
            }
            
            cache_path = self.get_cache_path(key)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to set cache for key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            cache_path = self.get_cache_path(key)
            if not os.path.exists(cache_path):
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查是否过期
            timestamp = cache_data.get("timestamp", 0)
            expire_hours = cache_data.get("expire_hours", 24)
            
            if TimeUtils.get_timestamp() - timestamp > expire_hours * 3600:
                os.remove(cache_path)
                return None
            
            return cache_data.get("data")
        except Exception as e:
            logger.error(f"Failed to get cache for key {key}: {e}")
            return None
    
    def clear_expired(self) -> int:
        """清理过期缓存"""
        try:
            cleared = 0
            for cache_file in os.listdir(self.cache_dir):
                if cache_file.endswith('.cache'):
                    cache_path = os.path.join(self.cache_dir, cache_file)
                    try:
                        with open(cache_path, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        timestamp = cache_data.get("timestamp", 0)
                        expire_hours = cache_data.get("expire_hours", 24)
                        
                        if TimeUtils.get_timestamp() - timestamp > expire_hours * 3600:
                            os.remove(cache_path)
                            cleared += 1
                    except:
                        os.remove(cache_path)
                        cleared += 1
            
            return cleared
        except Exception as e:
            logger.error(f"Failed to clear expired cache: {e}")
            return 0

class ConfigUtils:
    """配置工具类"""
    
    @staticmethod
    def load_json_config(file_path: str) -> Dict[str, Any]:
        """加载JSON配置文件"""
        try:
            if not os.path.exists(file_path):
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config {file_path}: {e}")
            return {}
    
    @staticmethod
    def save_json_config(file_path: str, config: Dict[str, Any]) -> bool:
        """保存JSON配置文件"""
        try:
            FileUtils.ensure_dir(str(Path(file_path).parent))
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save config {file_path}: {e}")
            return False
    
    @staticmethod
    def get_env_var(key: str, default: Any = None) -> Any:
        """获取环境变量"""
        return os.getenv(key, default)
    
    @staticmethod
    def set_env_var(key: str, value: str) -> bool:
        """设置环境变量"""
        try:
            os.environ[key] = value
            return True
        except Exception as e:
            logger.error(f"Failed to set env var {key}: {e}")
            return False

class ProgressTracker:
    """进度追踪器"""
    
    def __init__(self, total: int = 100):
        self.total = total
        self.current = 0
        self.start_time = time.time()
        self.callbacks = []
    
    def update(self, increment: int = 1):
        """更新进度"""
        self.current += increment
        progress = min(self.current / self.total, 1.0)
        
        for callback in self.callbacks:
            try:
                callback(progress, self.current, self.total)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    def add_callback(self, callback):
        """添加回调函数"""
        self.callbacks.append(callback)
    
    def get_progress(self) -> Dict[str, Any]:
        """获取进度信息"""
        elapsed = time.time() - self.start_time
        progress = self.current / self.total if self.total > 0 else 0
        
        if progress > 0:
            eta = (elapsed / progress) * (1 - progress)
        else:
            eta = 0
        
        return {
            "current": self.current,
            "total": self.total,
            "progress": progress,
            "elapsed": elapsed,
            "eta": eta,
            "percentage": f"{progress * 100:.1f}%"
        }

# 快捷函数
def get_file_hash(file_path: str, algorithm: str = 'md5') -> Optional[str]:
    """快捷文件哈希计算"""
    return FileUtils.get_file_hash(file_path, algorithm)

def download_file_from_url(url: str, output_path: str, **kwargs) -> Dict[str, Any]:
    """快捷文件下载"""
    return URLUtils.download_file(url, output_path, **kwargs)

def sanitize_filename(filename: str) -> str:
    """快捷文件名清理"""
    return StringUtils.sanitize_filename(filename)

def format_file_size(size_bytes: int) -> str:
    """快捷文件大小格式化"""
    return StringUtils.format_file_size(size_bytes)

def get_timestamp() -> int:
    """快捷时间戳获取"""
    return TimeUtils.get_timestamp()

def load_config(file_path: str) -> Dict[str, Any]:
    """快捷配置加载"""
    return ConfigUtils.load_json_config(file_path)

def save_config(file_path: str, config: Dict[str, Any]) -> bool:
    """快捷配置保存"""
    return ConfigUtils.save_json_config(file_path, config)

# 日志配置
def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> None:
    """设置日志配置"""
    
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    log_level = level_map.get(level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler()]
    
    if log_file:
        FileUtils.ensure_dir(str(Path(log_file).parent))
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=log_level,
        format=format_string,
        handlers=handlers
    )

if __name__ == "__main__":
    # 测试工具函数
    print("Testing utility functions...")
    
    # 测试文件工具
    test_dir = "test_utils"
    FileUtils.ensure_dir(test_dir)
    
    # 创建测试文件
    test_file = os.path.join(test_dir, "test.txt")
    with open(test_file, 'w') as f:
        f.write("Hello, CapCut API!")
    
    # 测试文件信息
    info = FileUtils.get_file_info(test_file)
    print("File info:", info)
    
    # 测试哈希
    hash_value = FileUtils.get_file_hash(test_file)
    print("File hash:", hash_value)
    
    # 测试字符串工具
    filename = StringUtils.sanitize_filename("test file name with spaces.txt")
    print("Sanitized filename:", filename)
    
    # 测试时间工具
    timestamp = TimeUtils.get_timestamp()
    print("Current timestamp:", timestamp)
    
    # 清理测试
    FileUtils.delete_file(test_file)
    shutil.rmtree(test_dir)
    
    print("All utility tests completed!")