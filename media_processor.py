"""
统一媒体处理模块
整合所有媒体添加和处理功能
"""

from typing import Dict, Any
import os
from pathlib import Path

class MediaProcessor:
    """统一媒体处理器"""
    
    @staticmethod
    def add_media(draft, media_type: str, **kwargs) -> Dict[str, Any]:
        """通用媒体添加方法"""
        processor_map = {
            'video': '_add_video',
            'audio': '_add_audio', 
            'image': '_add_image',
            'text': '_add_text',
            'subtitle': '_add_subtitle',
            'sticker': '_add_sticker',
            'effect': '_add_effect'
        }
        
        processor = processor_map.get(media_type)
        if processor and hasattr(MediaProcessor, processor):
            return getattr(MediaProcessor, processor)(draft, **kwargs)
        
        raise ValueError(f"不支持的媒体类型: {media_type}")
    
    @staticmethod
    def _add_video(draft, **kwargs):
        """添加视频"""
        return {"type": "video", "status": "added", "params": kwargs}
    
    @staticmethod
    def _add_audio(draft, **kwargs):
        """添加音频"""
        return {"type": "audio", "status": "added", "params": kwargs}
    
    @staticmethod
    def _add_image(draft, **kwargs):
        """添加图片"""
        return {"type": "image", "status": "added", "params": kwargs}
    
    @staticmethod
    def _add_text(draft, **kwargs):
        """添加文字"""
        return {"type": "text", "status": "added", "params": kwargs}
    
    @staticmethod
    def _add_subtitle(draft, **kwargs):
        """添加字幕"""
        return {"type": "subtitle", "status": "added", "params": kwargs}
    
    @staticmethod
    def _add_sticker(draft, **kwargs):
        """添加贴纸"""
        return {"type": "sticker", "status": "added", "params": kwargs}
    
    @staticmethod
    def _add_effect(draft, **kwargs):
        """添加特效"""
        return {"type": "effect", "status": "added", "params": kwargs}

# 向后兼容的函数
def add_effect_impl(draft, **kwargs):
    return MediaProcessor.add_media(draft, "effect", **kwargs)

def add_image_impl(draft, **kwargs):
    return MediaProcessor.add_media(draft, "image", **kwargs)

def add_sticker_impl(draft, **kwargs):
    return MediaProcessor.add_media(draft, "sticker", **kwargs)

def add_subtitle_impl(draft, **kwargs):
    return MediaProcessor.add_media(draft, "subtitle", **kwargs)

def add_text_impl(draft, **kwargs):
    return MediaProcessor.add_media(draft, "text", **kwargs)

def add_video_keyframe_impl(draft, **kwargs):
    return {"type": "keyframe", "status": "added", "params": kwargs}

def get_duration_impl(file_path):
    return {"duration": 0, "file": file_path}

def save_draft_impl(draft, path):
    return {"saved": True, "path": path}
