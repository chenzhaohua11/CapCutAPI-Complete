"""统一工具模块 - 精简优化版

整合所有工具函数到一个文件中，提供文件操作、验证、时间处理、响应格式化和缓存管理等功能。
本模块采用类组织方式，便于功能扩展和维护。

主要功能：
1. FileUtils: 文件操作工具，包括目录创建、JSON读写、文件名处理等
2. ValidationUtils: 参数验证工具，用于检查API输入参数
3. TimeUtils: 时间处理工具，格式化时间和获取时间戳
4. ResponseUtils: API响应格式化工具，统一返回格式
5. CacheUtils: 缓存管理工具，生成缓存键和清理临时文件

使用示例：
    from utils import FileUtils, ResponseUtils
    
    # 保存JSON数据
    FileUtils.save_json({"key": "value"}, "data.json")
    
    # 返回成功响应
    response = ResponseUtils.success(data={"result": "ok"})
"""

import os
import json
import uuid
import time
import hashlib
import shutil
import logging
import traceback
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional, List, Callable, Union, Tuple
from pathlib import Path

# 配置日志
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

class ResponseFormatter:
    """响应格式化工具类
    
    提供统一的API响应格式化功能，包括成功响应、错误响应、分页响应等。
    确保所有API返回格式一致，便于前端处理。
    """
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
        """格式化成功响应
        
        Args:
            data: 响应数据
            message: 成功消息
            
        Returns:
            Dict[str, Any]: 格式化的成功响应
        """
        return {
            "status": "success",
            "message": message,
            "data": data,
            "timestamp": time.time(),
            "server_time": datetime.now().isoformat()
        }
    
    @staticmethod
    def error(message: str, code: int = 400, details: Any = None) -> Tuple[Dict[str, Any], int]:
        """格式化错误响应
        
        Args:
            message: 错误消息
            code: HTTP状态码
            details: 错误详情
            
        Returns:
            Tuple[Dict[str, Any], int]: 格式化的错误响应和HTTP状态码
        """
        response = {
            "status": "error",
            "message": message,
            "code": code,
            "timestamp": time.time(),
            "server_time": datetime.now().isoformat()
        }
        
        if details:
            response["details"] = details
            
        return response, code
    
    @staticmethod
    def paginated(items: List[Any], page: int, page_size: int, total: int, 
                 message: str = "获取成功") -> Dict[str, Any]:
        """格式化分页响应
        
        Args:
            items: 当前页的数据项
            page: 当前页码
            page_size: 每页大小
            total: 总数据量
            message: 成功消息
            
        Returns:
            Dict[str, Any]: 格式化的分页响应
        """
        return {
            "status": "success",
            "message": message,
            "data": {
                "items": items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "pages": (total + page_size - 1) // page_size
                }
            },
            "timestamp": time.time(),
            "server_time": datetime.now().isoformat()
        }


class RequestValidator:
    """请求验证工具类
    
    提供API请求参数验证功能，包括必填参数检查、类型检查、范围检查等。
    帮助API接口快速验证输入参数的有效性。
    """
    
    @staticmethod
    def validate_required(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, Optional[str]]:
        """验证必填字段
        
        Args:
            data: 请求数据
            required_fields: 必填字段列表
            
        Returns:
            Tuple[bool, Optional[str]]: (是否通过验证, 错误消息)
        """
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return False, f"缺少必填字段: {', '.join(missing_fields)}"
        
        return True, None
    
    @staticmethod
    def validate_type(data: Dict[str, Any], field_types: Dict[str, type]) -> Tuple[bool, Optional[str]]:
        """验证字段类型
        
        Args:
            data: 请求数据
            field_types: 字段类型映射，格式为 {字段名: 类型}
            
        Returns:
            Tuple[bool, Optional[str]]: (是否通过验证, 错误消息)
        """
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                return False, f"字段 {field} 类型错误，应为 {expected_type.__name__}"
        
        return True, None
    
    @staticmethod
    def validate_range(data: Dict[str, Any], ranges: Dict[str, Tuple[Any, Any]]) -> Tuple[bool, Optional[str]]:
        """验证字段值范围
        
        Args:
            data: 请求数据
            ranges: 字段范围映射，格式为 {字段名: (最小值, 最大值)}
            
        Returns:
            Tuple[bool, Optional[str]]: (是否通过验证, 错误消息)
        """
        for field, (min_val, max_val) in ranges.items():
            if field in data:
                value = data[field]
                if value < min_val or value > max_val:
                    return False, f"字段 {field} 超出范围，应在 {min_val} 和 {max_val} 之间"
        
        return True, None


class FileUtils:
    """文件工具类
    
    提供文件和目录操作的工具方法，包括目录创建、文件复制、JSON读写、
    文件哈希计算、文件名处理等功能。
    """
    
    @staticmethod
    def ensure_dir(path: str) -> bool:
        """确保目录存在
        
        Args:
            path: 目录路径
            
        Returns:
            bool: 操作是否成功
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"创建目录失败: {path}, 错误: {e}")
            return False
    
    @staticmethod
    def save_json(data: Dict[str, Any], filepath: str, atomic: bool = True) -> bool:
        """保存JSON文件
        
        Args:
            data: 要保存的数据
            filepath: 文件路径
            atomic: 是否原子写入（先写临时文件再重命名）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            FileUtils.ensure_dir(os.path.dirname(filepath))
            
            if atomic:
                # 原子写入，防止写入过程中文件损坏
                temp_file = f"{filepath}.tmp"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(temp_file, filepath)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
            return True
        except Exception as e:
            logger.error(f"保存JSON失败: {filepath}, 错误: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    @staticmethod
    def load_json(filepath: str, default: Any = None) -> Any:
        """加载JSON文件
        
        Args:
            filepath: 文件路径
            default: 文件不存在或加载失败时的默认值
            
        Returns:
            加载的JSON数据或默认值
        """
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"JSON格式错误: {filepath}, 错误: {e}")
            logger.debug(traceback.format_exc())
        except Exception as e:
            logger.error(f"加载JSON失败: {filepath}, 错误: {e}")
            logger.debug(traceback.format_exc())
        return default
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """获取文件扩展名
        
        Args:
            filename: 文件名
            
        Returns:
            str: 小写的文件扩展名（不含点）
        """
        return os.path.splitext(filename)[1].lower().lstrip('.')
    
    @staticmethod
    def get_file_size(filepath: str) -> int:
        """获取文件大小
        
        Args:
            filepath: 文件路径
            
        Returns:
            int: 文件大小（字节）
        """
        try:
            return os.path.getsize(filepath)
        except Exception as e:
            logger.error(f"获取文件大小失败: {filepath}, 错误: {e}")
            return 0
    
    @staticmethod
    def get_file_hash(filepath: str, algorithm: str = 'md5', block_size: int = 65536) -> Optional[str]:
        """计算文件哈希值
        
        Args:
            filepath: 文件路径
            algorithm: 哈希算法，支持'md5'、'sha1'、'sha256'
            block_size: 读取块大小
            
        Returns:
            Optional[str]: 文件哈希值，失败返回None
        """
        if not os.path.exists(filepath):
            return None
            
        try:
            hash_obj = None
            if algorithm == 'md5':
                hash_obj = hashlib.md5()
            elif algorithm == 'sha1':
                hash_obj = hashlib.sha1()
            elif algorithm == 'sha256':
                hash_obj = hashlib.sha256()
            else:
                raise ValueError(f"不支持的哈希算法: {algorithm}")
                
            with open(filepath, 'rb') as f:
                for block in iter(lambda: f.read(block_size), b''):
                    hash_obj.update(block)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败: {filepath}, 错误: {e}")
            return None
    
    @staticmethod
    def copy_file(src: str, dst: str, overwrite: bool = False) -> bool:
        """复制文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if os.path.exists(dst) and not overwrite:
                logger.warning(f"目标文件已存在且不允许覆盖: {dst}")
                return False
                
            FileUtils.ensure_dir(os.path.dirname(dst))
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            logger.error(f"复制文件失败: {src} -> {dst}, 错误: {e}")
            return False
    
    @staticmethod
    def generate_unique_filename(prefix: str = "", extension: str = "") -> str:
        """生成唯一文件名
        
        Args:
            prefix: 文件名前缀
            extension: 文件扩展名
            
        Returns:
            str: 唯一文件名
        """
        timestamp = int(time.time())
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{prefix}_{timestamp}_{unique_id}" if prefix else f"{timestamp}_{unique_id}"
        if extension:
            filename = f"{filename}.{extension.lstrip('.')}"
        return filename

class ValidationUtils:
    """验证工具类
    
    提供参数验证和数据清理的工具方法，用于检查API输入参数的有效性，
    确保数据符合预期格式和范围。
    """
    
    @staticmethod
    def validate_media_params(params: Dict[str, Any]) -> Dict[str, str]:
        """验证媒体参数
        
        Args:
            params: 媒体参数字典
            
        Returns:
            Dict[str, str]: 错误信息字典，键为参数名，值为错误描述
        """
        errors = {}
        
        # 验证必要参数
        required_fields = ['draft_id']
        for field in required_fields:
            if field not in params or not params[field]:
                errors[field] = f"{field}是必填参数"
        
        # 验证时间参数
        timeline = params.get('timeline', {})
        if timeline:
            if 'start' in timeline and not isinstance(timeline['start'], (int, float)):
                errors['timeline.start'] = "开始时间必须是数字"
            elif 'start' in timeline and timeline['start'] < 0:
                errors['timeline.start'] = "开始时间不能为负"
                
            if 'duration' in timeline and not isinstance(timeline['duration'], (int, float)):
                errors['timeline.duration'] = "持续时间必须是数字"
            elif 'duration' in timeline and timeline['duration'] <= 0:
                errors['timeline.duration'] = "持续时间必须大于0"
        
        # 验证变换参数
        transform = params.get('transform', {})
        if transform:
            # 验证缩放
            if 'scale' in transform:
                scale = transform['scale']
                if not isinstance(scale, (int, float)):
                    errors['transform.scale'] = "缩放比例必须是数字"
                elif scale <= 0:
                    errors['transform.scale'] = "缩放比例必须为正数"
            
            # 验证旋转
            if 'rotation' in transform:
                rotation = transform['rotation']
                if not isinstance(rotation, (int, float)):
                    errors['transform.rotation'] = "旋转角度必须是数字"
            
            # 验证位置
            if 'position' in transform:
                position = transform['position']
                if not isinstance(position, list) or len(position) != 2:
                    errors['transform.position'] = "位置必须是包含两个元素的数组[x,y]"
                elif not all(isinstance(p, (int, float)) for p in position):
                    errors['transform.position'] = "位置坐标必须是数字"
        
        # 验证速度参数
        if 'speed' in params:
            speed = params['speed']
            if not isinstance(speed, (int, float)):
                errors['speed'] = "速度必须是数字"
            elif speed <= 0:
                errors['speed'] = "速度必须为正数"
        
        # 验证音量参数
        if 'volume' in params:
            volume = params['volume']
            if not isinstance(volume, (int, float)):
                errors['volume'] = "音量必须是数字"
            elif volume < 0 or volume > 100:
                errors['volume'] = "音量必须在0-100范围内"
        
        return errors
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """验证URL格式
        
        Args:
            url: 要验证的URL
            
        Returns:
            bool: URL是否有效
        """
        if not url:
            return False
            
        # 简单验证URL格式
        valid_schemes = ['http', 'https', 'ftp']
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return result.scheme in valid_schemes and result.netloc
        except Exception:
            return False
    
    @staticmethod
    def validate_range(value: Union[int, float], min_value: Union[int, float], 
                       max_value: Union[int, float], inclusive: bool = True) -> bool:
        """验证数值范围
        
        Args:
            value: 要验证的值
            min_value: 最小值
            max_value: 最大值
            inclusive: 是否包含边界值
            
        Returns:
            bool: 值是否在范围内
        """
        if not isinstance(value, (int, float)):
            return False
            
        if inclusive:
            return min_value <= value <= max_value
        else:
            return min_value < value < max_value
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名，移除不允许的字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        if not filename:
            return "untitled"
            
        # 移除不允许的字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
            
        # 移除前后空白
        filename = filename.strip()
        
        # 如果文件名为空，使用默认名称
        if not filename:
            return "untitled"
            
        # 限制长度
        max_length = 255
        if len(filename) > max_length:
            extension = FileUtils.get_file_extension(filename)
            name_part = os.path.splitext(filename)[0]
            if extension:
                # 保留扩展名，截断名称部分
                max_name_length = max_length - len(extension) - 1  # 减去点和扩展名长度
                return f"{name_part[:max_name_length]}.{extension}"
            else:
                return name_part[:max_length]
                
        return filename

class TimeUtils:
    """时间工具类
    
    提供时间和时长相关的工具方法，用于格式化时间、计算时间差异、
    获取时间戳等操作。
    """
    
    @staticmethod
    def format_duration(seconds: float, format_type: str = "human") -> str:
        """格式化时长为可读字符串
        
        Args:
            seconds: 秒数
            format_type: 格式类型，可选值：
                - "human": 人类可读格式，如 "5m 30s"
                - "colon": 冒号分隔格式，如 "5:30"
                - "full": 完整格式，如 "00:05:30"
            
        Returns:
            str: 格式化后的时长字符串
        """
        if seconds < 0:
            seconds = 0
            
        if format_type == "human":
            if seconds < 60:
                return f"{seconds:.1f}s"
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            if minutes < 60:
                return f"{minutes}m {secs}s"
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours}h {minutes}m {secs}s"
            
        elif format_type == "colon":
            minutes, secs = divmod(int(seconds), 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                return f"{hours}:{minutes:02d}:{secs:02d}"
            else:
                return f"{minutes}:{secs:02d}"
                
        elif format_type == "full":
            minutes, secs = divmod(int(seconds), 60)
            hours, minutes = divmod(minutes, 60)
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            
        else:
            logger.warning(f"未知的时长格式类型: {format_type}，使用默认human格式")
            if seconds < 60:
                return f"{seconds:.1f}s"
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
    
    @staticmethod
    def parse_duration(duration_str: str) -> float:
        """解析时长字符串为秒数
        
        Args:
            duration_str: 时长字符串，支持以下格式：
                - "5m 30s" (人类可读格式)
                - "5:30" (冒号分隔格式)
                - "00:05:30" (完整格式)
                - "5.5s" (秒格式)
            
        Returns:
            float: 解析后的秒数
            
        Raises:
            ValueError: 如果时长字符串格式无效
        """
        try:
            # 尝试解析冒号格式 (00:05:30 或 5:30)
            if ":" in duration_str:
                parts = duration_str.split(':') 
                seconds = 0.0
                
                if len(parts) == 3:  # HH:MM:SS
                    hours, minutes, seconds_part = parts
                    seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds_part)
                elif len(parts) == 2:  # MM:SS
                    minutes, seconds_part = parts
                    seconds = int(minutes) * 60 + float(seconds_part)
                else:
                    raise ValueError(f"无效的冒号分隔时长格式: {duration_str}")
                    
                return seconds
                
            # 尝试解析人类可读格式 (5h 30m 15s 或 5m 30s 或 45s)
            total_seconds = 0.0
            
            # 提取小时
            hour_match = re.search(r'(\d+(\.\d+)?)h', duration_str)
            if hour_match:
                total_seconds += float(hour_match.group(1)) * 3600
                
            # 提取分钟
            minute_match = re.search(r'(\d+(\.\d+)?)m', duration_str)
            if minute_match:
                total_seconds += float(minute_match.group(1)) * 60
                
            # 提取秒
            second_match = re.search(r'(\d+(\.\d+)?)s', duration_str)
            if second_match:
                total_seconds += float(second_match.group(1))
                
            if total_seconds > 0 or duration_str.strip() == "0s":
                return total_seconds
                
            # 尝试直接解析为秒数
            return float(duration_str)
            
        except (ValueError, TypeError) as e:
            logger.error(f"解析时长字符串失败: {duration_str}, 错误: {str(e)}")
            raise ValueError(f"无效的时长格式: {duration_str}")
    
    @staticmethod
    def get_timestamp(ms: bool = False) -> Union[int, float]:
        """获取当前时间戳
        
        Args:
            ms: 是否返回毫秒级时间戳
            
        Returns:
            Union[int, float]: 当前时间戳，整数（秒）或浮点数（毫秒）
        """
        if ms:
            return time.time()
        else:
            return int(time.time())
    
    @staticmethod
    def timestamp_to_str(timestamp: Union[int, float], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """将时间戳转换为格式化的日期时间字符串
        
        Args:
            timestamp: 时间戳（秒）
            format_str: 日期时间格式字符串
            
        Returns:
            str: 格式化的日期时间字符串
        """
        try:
            dt = datetime.datetime.fromtimestamp(timestamp)
            return dt.strftime(format_str)
        except (ValueError, TypeError, OverflowError) as e:
            logger.error(f"时间戳转换失败: {timestamp}, 错误: {str(e)}")
            return ""
    
    @staticmethod
    def get_formatted_now(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """获取当前时间的格式化字符串
        
        Args:
            format_str: 日期时间格式字符串
            
        Returns:
            str: 当前时间的格式化字符串
        """
        return datetime.datetime.now().strftime(format_str)

class ResponseUtils:
    """响应工具类
    
    提供统一的API响应格式化工具，确保所有API返回一致的响应结构，
    包括成功响应、错误响应、分页响应等。
    """
    
    @staticmethod
    def success(data: Any = None, message: str = "success") -> Dict[str, Any]:
        """生成标准成功响应
        
        Args:
            data: 响应数据
            message: 成功消息
            
        Returns:
            Dict[str, Any]: 标准成功响应字典
        """
        response = {
            "code": 200,
            "message": message,
            "success": True,
            "timestamp": TimeUtils.get_timestamp()
        }
        
        if data is not None:
            response["data"] = data
            
        return response
    
    @staticmethod
    def error(message: str = "error", code: int = 400, data: Any = None, 
              error_type: str = None) -> Dict[str, Any]:
        """生成标准错误响应
        
        Args:
            message: 错误消息
            code: 错误代码
            data: 错误相关数据
            error_type: 错误类型
            
        Returns:
            Dict[str, Any]: 标准错误响应字典
        """
        response = {
            "code": code,
            "message": message,
            "success": False,
            "timestamp": TimeUtils.get_timestamp()
        }
        
        if data is not None:
            response["data"] = data
            
        if error_type:
            response["error_type"] = error_type
            
        # 记录错误日志
        logger.error(f"API错误: {code} - {message}")
        
        return response
    
    @staticmethod
    def paginated(items: List[Any], total: int, page: int = 1, page_size: int = 20, 
                 message: str = "success") -> Dict[str, Any]:
        """生成分页响应
        
        Args:
            items: 当前页的数据项列表
            total: 总数据项数量
            page: 当前页码
            page_size: 每页大小
            message: 成功消息
            
        Returns:
            Dict[str, Any]: 标准分页响应字典
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        
        return {
            "code": 200,
            "message": message,
            "success": True,
            "timestamp": TimeUtils.get_timestamp(),
            "data": {
                "items": items,
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        }
    
    @staticmethod
    def with_meta(data: Any, meta: Dict[str, Any], message: str = "success") -> Dict[str, Any]:
        """生成带元数据的响应
        
        Args:
            data: 主要响应数据
            meta: 元数据字典
            message: 成功消息
            
        Returns:
            Dict[str, Any]: 带元数据的标准响应字典
        """
        return {
            "code": 200,
            "message": message,
            "success": True,
            "timestamp": TimeUtils.get_timestamp(),
            "data": data,
            "meta": meta
        }

class CacheUtils:
    """缓存工具类
    
    提供缓存管理相关的工具方法，包括缓存键生成、临时文件管理、
    缓存过期控制等功能。
    """
    
    @staticmethod
    def get_cache_key(*args) -> str:
        """生成缓存键
        
        将多个参数组合成一个缓存键，用于唯一标识缓存项。
        
        Args:
            *args: 用于生成缓存键的参数列表
            
        Returns:
            str: 生成的缓存键
            
        Examples:
            >>> CacheUtils.get_cache_key("draft", 123, "video")
            'draft:123:video'
        """
        return ":".join(str(arg) for arg in args)
    
    @staticmethod
    def hash_cache_key(*args) -> str:
        """生成哈希缓存键
        
        将多个参数组合并哈希化，生成固定长度的缓存键。
        适用于参数较长或包含特殊字符的情况。
        
        Args:
            *args: 用于生成缓存键的参数列表
            
        Returns:
            str: 生成的哈希缓存键
        """
        key_str = ":".join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    @staticmethod
    def clear_temp_files(temp_dir: str, max_age: int = 3600, pattern: str = None) -> int:
        """清理临时文件
        
        删除指定目录中超过最大保存时间的临时文件。
        
        Args:
            temp_dir: 临时文件目录
            max_age: 最大保存时间（秒），默认1小时
            pattern: 文件名匹配模式（支持通配符），如 "*.tmp"
            
        Returns:
            int: 已清理的文件数量
            
        Raises:
            OSError: 如果目录操作失败
        """
        cleared = 0
        try:
            temp_path = Path(temp_dir)
            if not temp_path.exists():
                logger.warning(f"临时目录不存在: {temp_dir}")
                return 0
                
            current_time = time.time()
            
            # 获取文件列表
            if pattern:
                import glob
                file_paths = glob.glob(str(temp_path / pattern))
                file_paths = [Path(p) for p in file_paths if Path(p).is_file()]
            else:
                file_paths = [p for p in temp_path.iterdir() if p.is_file()]
            
            # 清理过期文件
            for file_path in file_paths:
                try:
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age:
                        file_path.unlink()
                        logger.debug(f"已清理临时文件: {file_path.name}")
                        cleared += 1
                except (OSError, PermissionError) as e:
                    logger.warning(f"无法删除文件 {file_path}: {e}")
                    
            if cleared > 0:
                logger.info(f"已清理 {cleared} 个临时文件，目录: {temp_dir}")
                
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
            logger.debug(traceback.format_exc())
            
        return cleared
    
    @staticmethod
    def create_temp_dir(base_dir: str, prefix: str = "temp_") -> str:
        """创建临时目录
        
        在指定的基础目录下创建一个临时目录。
        
        Args:
            base_dir: 基础目录
            prefix: 临时目录名称前缀
            
        Returns:
            str: 创建的临时目录路径
            
        Raises:
            OSError: 如果目录创建失败
        """
        try:
            # 确保基础目录存在
            FileUtils.ensure_dir(base_dir)
            
            # 创建临时目录
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix=prefix, dir=base_dir)
            logger.debug(f"已创建临时目录: {temp_dir}")
            return temp_dir
            
        except Exception as e:
            logger.error(f"创建临时目录失败: {e}")
            logger.debug(traceback.format_exc())
            raise OSError(f"创建临时目录失败: {e}")

# 统一导出所有工具
utils = {
    'file': FileUtils,
    'validation': ValidationUtils,
    'time': TimeUtils,
    'response': ResponseUtils,
    'cache': CacheUtils
}

# 向后兼容的快捷函数
# 文件操作
ensure_dir = FileUtils.ensure_dir
save_json = FileUtils.save_json
load_json = FileUtils.load_json
get_file_extension = FileUtils.get_file_extension
generate_unique_filename = FileUtils.generate_unique_filename
get_file_size = FileUtils.get_file_size
get_file_hash = FileUtils.get_file_hash
copy_file = FileUtils.copy_file

# 验证工具
validate_media_params = ValidationUtils.validate_media_params
sanitize_filename = ValidationUtils.sanitize_filename
validate_url = ValidationUtils.validate_url
validate_range = ValidationUtils.validate_range

# 时间工具
format_duration = TimeUtils.format_duration
parse_duration = TimeUtils.parse_duration
get_timestamp = TimeUtils.get_timestamp
timestamp_to_str = TimeUtils.timestamp_to_str
get_formatted_now = TimeUtils.get_formatted_now

# 响应工具
success_response = ResponseUtils.success
error_response = ResponseUtils.error
paginated_response = ResponseUtils.paginated
with_meta_response = ResponseUtils.with_meta

# 缓存工具
get_cache_key = CacheUtils.get_cache_key
hash_cache_key = CacheUtils.hash_cache_key
clear_temp_files = CacheUtils.clear_temp_files
create_temp_dir = CacheUtils.create_temp_dir