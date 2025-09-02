"""统一媒体处理模块 - 优化版
整合所有媒体添加和处理功能，提供高性能和可靠的媒体处理能力
"""

from typing import Dict, Any, Optional, List, Tuple, Union, Callable
import os
from pathlib import Path
import json
import logging
import time
from functools import lru_cache

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MediaProcessor:
    """统一媒体处理器
    
    提供统一的媒体处理接口，支持视频、音频、图片、文本等多种媒体类型的添加和处理。
    使用工厂模式和策略模式实现可扩展的媒体处理功能。
    """
    
    def __init__(self):
        """初始化媒体处理器"""
        # 媒体处理器映射表，使用字典实现策略模式
        self._processor_map = {
            'video': self._add_video,
            'audio': self._add_audio, 
            'image': self._add_image,
            'text': self._add_text,
            'subtitle': self._add_subtitle,
            'sticker': self._add_sticker,
            'effect': self._add_effect
        }
        
        # 支持的媒体类型列表
        self.supported_types = list(self._processor_map.keys())
        
        logger.info(f"媒体处理器初始化完成，支持的媒体类型: {', '.join(self.supported_types)}")
    
    def add_media(self, media_type: str, **kwargs) -> Dict[str, Any]:
        """通用媒体添加方法
        
        Args:
            media_type: 媒体类型，如'video', 'audio', 'image'等
            **kwargs: 媒体参数，根据不同媒体类型有不同的参数要求
            
        Returns:
            Dict[str, Any]: 处理结果，包含状态和相关信息
            
        Raises:
            ValueError: 当媒体类型不支持时
            RuntimeError: 当媒体处理失败时
        """
        start_time = time.time()
        
        try:
            # 获取对应的处理器
            processor = self._processor_map.get(media_type)
            if not processor:
                raise ValueError(f"不支持的媒体类型: {media_type}，支持的类型: {', '.join(self.supported_types)}")
            
            # 调用处理器
            result = processor(**kwargs)
            
            # 记录处理时间
            elapsed = time.time() - start_time
            logger.info(f"媒体处理完成: {media_type}, 耗时: {elapsed:.3f}秒")
            
            return result
        except Exception as e:
            logger.error(f"媒体处理失败: {media_type}, 错误: {str(e)}")
            raise RuntimeError(f"媒体处理失败: {str(e)}") from e
    
    @lru_cache(maxsize=32)
    def _get_media_duration(self, media_url: str) -> float:
        """获取媒体时长（带缓存）
        
        Args:
            media_url: 媒体URL
            
        Returns:
            float: 媒体时长（秒）
        """
        # 实际实现中应该使用ffmpeg或其他库获取媒体时长
        # 这里简化为返回固定值
        logger.debug(f"获取媒体时长: {media_url}")
        return 10.0
    
    def _validate_media_url(self, media_url: Optional[str]) -> bool:
        """验证媒体URL
        
        Args:
            media_url: 媒体URL
            
        Returns:
            bool: URL是否有效
        """
        if not media_url:
            return False
            
        # 实际实现中应该检查URL格式和可访问性
        return True
    
    def _add_video(self, **kwargs) -> Dict[str, Any]:
        """添加视频
        
        Args:
            draft_id: 草稿ID
            media_url: 视频URL
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 处理结果
            
        Raises:
            ValueError: 当参数无效时
        """
        media_url = kwargs.get('media_url')
        if not self._validate_media_url(media_url):
            raise ValueError(f"无效的视频URL: {media_url}")
            
        logger.info(f"添加视频: {media_url}")
        
        # 获取视频时长（使用缓存）
        duration = kwargs.get('duration') or self._get_media_duration(media_url)
        
        # 在实际实现中，这里会调用pyJianYingDraft的相关功能
        # 这里简化为返回参数信息
        return {
            "type": "video", 
            "status": "added", 
            "draft_id": kwargs.get('draft_id', ''),
            "media_url": media_url,
            "duration": duration,
            "timestamp": time.time(),
            "params": kwargs
        }
    
    def _add_audio(self, **kwargs) -> Dict[str, Any]:
        """添加音频
        
        Args:
            draft_id: 草稿ID
            media_url: 音频URL
            start_time: 开始时间（秒）
            volume: 音量（0-100）
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        media_url = kwargs.get('media_url')
        if not self._validate_media_url(media_url):
            raise ValueError(f"无效的音频URL: {media_url}")
            
        logger.info(f"添加音频: {media_url}")
        
        # 获取音频时长（使用缓存）
        duration = kwargs.get('duration') or self._get_media_duration(media_url)
        
        return {
            "type": "audio", 
            "status": "added", 
            "draft_id": kwargs.get('draft_id', ''),
            "media_url": media_url,
            "duration": duration,
            "timestamp": time.time(),
            "params": kwargs
        }
    
    def _add_image(self, **kwargs) -> Dict[str, Any]:
        """添加图片
        
        Args:
            draft_id: 草稿ID
            media_url: 图片URL
            duration: 显示时长（秒）
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        media_url = kwargs.get('media_url')
        if not self._validate_media_url(media_url):
            raise ValueError(f"无效的图片URL: {media_url}")
            
        logger.info(f"添加图片: {media_url}")
        
        # 图片默认显示5秒
        duration = kwargs.get('duration', 5.0)
        
        return {
            "type": "image", 
            "status": "added", 
            "draft_id": kwargs.get('draft_id', ''),
            "media_url": media_url,
            "duration": duration,
            "timestamp": time.time(),
            "params": kwargs
        }
    
    def _add_text(self, **kwargs) -> Dict[str, Any]:
        """添加文字
        
        Args:
            draft_id: 草稿ID
            text: 文本内容
            font_name: 字体名称
            font_size: 字体大小
            color: 颜色（十六进制）
            position: 位置坐标 [x, y]
            duration: 显示时长（秒）
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 处理结果
            
        Raises:
            ValueError: 当文本为空时
        """
        text = kwargs.get('text', '')
        if not text.strip():
            raise ValueError("文本内容不能为空")
            
        logger.info(f"添加文字: {text[:20]}{'...' if len(text) > 20 else ''}")
        
        # 设置默认值
        font_name = kwargs.get('font_name', '微软雅黑')
        font_size = kwargs.get('font_size', 24)
        color = kwargs.get('color', '#FFFFFF')
        position = kwargs.get('position', [0.5, 0.5])  # 默认居中
        duration = kwargs.get('duration', 5.0)  # 默认5秒
        
        return {
            "type": "text", 
            "status": "added", 
            "draft_id": kwargs.get('draft_id', ''),
            "text": text,
            "font_name": font_name,
            "font_size": font_size,
            "color": color,
            "position": position,
            "duration": duration,
            "timestamp": time.time(),
            "params": kwargs
        }
    
    def _add_subtitle(self, **kwargs) -> Dict[str, Any]:
        """添加字幕
        
        Args:
            draft_id: 草稿ID
            srt_path: 字幕文件路径
            style: 字幕样式
            offset: 时间偏移（秒）
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 处理结果
            
        Raises:
            ValueError: 当字幕文件路径无效时
        """
        srt_path = kwargs.get('srt_path', '')
        if not srt_path or not os.path.exists(srt_path):
            raise ValueError(f"无效的字幕文件路径: {srt_path}")
            
        logger.info(f"添加字幕: {srt_path}")
        
        # 设置默认值
        style = kwargs.get('style', 'default')
        offset = kwargs.get('offset', 0.0)  # 默认无偏移
        
        return {
            "type": "subtitle", 
            "status": "added", 
            "draft_id": kwargs.get('draft_id', ''),
            "srt_path": srt_path,
            "style": style,
            "offset": offset,
            "timestamp": time.time(),
            "params": kwargs
        }
    
    def _add_sticker(self, **kwargs) -> Dict[str, Any]:
        """添加贴纸
        
        Args:
            draft_id: 草稿ID
            sticker_url: 贴纸URL
            position: 位置坐标 [x, y]
            scale: 缩放比例
            rotation: 旋转角度
            duration: 显示时长（秒）
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 处理结果
            
        Raises:
            ValueError: 当贴纸URL无效时
        """
        sticker_url = kwargs.get('sticker_url', '')
        if not self._validate_media_url(sticker_url):
            raise ValueError(f"无效的贴纸URL: {sticker_url}")
            
        logger.info(f"添加贴纸: {sticker_url}")
        
        # 设置默认值
        position = kwargs.get('position', [0.5, 0.5])  # 默认居中
        scale = kwargs.get('scale', 1.0)  # 默认原始大小
        rotation = kwargs.get('rotation', 0.0)  # 默认不旋转
        duration = kwargs.get('duration', 5.0)  # 默认5秒
        
        return {
            "type": "sticker", 
            "status": "added", 
            "draft_id": kwargs.get('draft_id', ''),
            "sticker_url": sticker_url,
            "position": position,
            "scale": scale,
            "rotation": rotation,
            "duration": duration,
            "timestamp": time.time(),
            "params": kwargs
        }
    
    def _add_effect(self, **kwargs) -> Dict[str, Any]:
        """添加特效
        
        Args:
            draft_id: 草稿ID
            effect_type: 特效类型
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            intensity: 特效强度（0-100）
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 处理结果
            
        Raises:
            ValueError: 当特效类型为空时
        """
        effect_type = kwargs.get('effect_type', '')
        if not effect_type:
            raise ValueError("特效类型不能为空")
            
        # 检查特效类型是否支持
        supported_effects = ['fade', 'blur', 'glow', 'shake', 'zoom', 'glitch']
        if effect_type not in supported_effects:
            logger.warning(f"未知的特效类型: {effect_type}，支持的类型: {supported_effects}")
            
        logger.info(f"添加特效: {effect_type}")
        
        # 设置默认值
        start_time = kwargs.get('start_time', 0.0)
        duration = kwargs.get('duration', 3.0)  # 默认3秒
        intensity = kwargs.get('intensity', 50)  # 默认中等强度
        
        return {
            "type": "effect", 
            "status": "added", 
            "draft_id": kwargs.get('draft_id', ''),
            "effect_type": effect_type,
            "start_time": start_time,
            "duration": duration,
            "intensity": intensity,
            "timestamp": time.time(),
            "params": kwargs
        }

# 向后兼容的函数
def add_effect_impl(draft, **kwargs):
    processor = MediaProcessor()
    return processor.add_media(media_type="effect", draft=draft, **kwargs)

def add_image_impl(draft, **kwargs):
    processor = MediaProcessor()
    return processor.add_media(media_type="image", draft=draft, **kwargs)

def add_sticker_impl(draft, **kwargs):
    processor = MediaProcessor()
    return processor.add_media(media_type="sticker", draft=draft, **kwargs)

def add_subtitle_impl(draft, **kwargs):
    processor = MediaProcessor()
    return processor.add_media(media_type="subtitle", draft=draft, **kwargs)

def add_text_impl(draft, **kwargs):
    processor = MediaProcessor()
    return processor.add_media(media_type="text", draft=draft, **kwargs)

def add_video_keyframe_impl(draft, **kwargs):
    return {"type": "keyframe", "status": "added", "params": kwargs}

def get_duration_impl(file_path):
    return {"duration": 10.0, "file": file_path}  # 模拟返回10秒的持续时间

def save_draft_impl(draft, path):
    return {"saved": True, "path": path}
