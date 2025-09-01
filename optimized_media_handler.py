"""
统一媒体处理模块 - 精简优化版
整合视频、音频、图片处理逻辑，消除重复代码
"""

import os
import pyJianYingDraft as draft
from typing import Optional, Dict, Any, List, Tuple
from util import generate_draft_url, is_windows_path, url_to_hash
from pyJianYingDraft import trange, Clip_settings, exceptions
from create_draft import get_or_create_draft
from settings.local import IS_CAPCUT_ENV
import re

class MediaHandler:
    """统一媒体处理器"""
    
    def __init__(self):
        self.supported_media = {
            'video': {'track_type': draft.Track_type.video, 'material_class': draft.Video_material},
            'audio': {'track_type': draft.Track_type.audio, 'material_class': draft.Audio_material}
        }
    
    def _build_draft_path(self, draft_folder: str, draft_id: str, filename: str, media_type: str) -> Optional[str]:
        """构建草稿文件路径"""
        if not draft_folder:
            return None
            
        asset_type = 'video' if media_type == 'video' else 'audio'
        
        if is_windows_path(draft_folder):
            windows_drive, windows_path = re.match(r'([a-zA-Z]:)(.*)', draft_folder).groups()
            parts = [p for p in windows_path.split('\\') if p]
            path = os.path.join(windows_drive, *parts, draft_id, "assets", asset_type, filename)
            return path.replace('/', '\\')
        else:
            return os.path.join(draft_folder, draft_id, "assets", asset_type, filename)
    
    def _ensure_track_exists(self, script, track_type, track_name: str, relative_index: int = 0):
        """确保轨道存在"""
        try:
            script.get_track(track_type, track_name=None)
        except exceptions.TrackNotFound:
            script.add_track(track_type, relative_index=relative_index)
        except NameError:
            pass  # 轨道已存在
    
    def _create_material(self, media_type: str, url: str, local_path: Optional[str], 
                        duration: float, name: str) -> Any:
        """创建媒体素材"""
        material_class = self.supported_media[media_type]['material_class']
        
        if local_path:
            return material_class(
                material_type=media_type, 
                replace_path=local_path, 
                remote_url=url, 
                material_name=name, 
                duration=duration
            )
        else:
            return material_class(
                material_type=media_type, 
                remote_url=url, 
                material_name=name, 
                duration=duration
            )
    
    def _create_segment(self, media_type: str, material: Any, start: float, end: float, 
                       target_start: float, speed: float, volume: float, 
                       transform: Dict[str, float]) -> Any:
        """创建媒体片段"""
        source_duration = end - start
        target_duration = source_duration / speed
        
        if media_type == 'video':
            return draft.Video_segment(
                material,
                target_timerange=trange(f"{target_start}s", f"{target_duration}s"),
                source_timerange=trange(f"{start}s", f"{source_duration}s"),
                speed=speed,
                clip_settings=Clip_settings(**transform),
                volume=volume
            )
        else:  # audio
            return draft.Audio_segment(
                material,
                target_timerange=trange(f"{target_start}s", f"{target_duration}s"),
                source_timerange=trange(f"{start}s", f"{source_duration}s"),
                speed=speed,
                volume=volume
            )
    
    def process_media(self, media_type: str, **kwargs) -> Dict[str, str]:
        """统一媒体处理入口"""
        # 标准化参数
        url = kwargs['url']
        width = kwargs.get('width', 1080)
        height = kwargs.get('height', 1920)
        start = kwargs.get('start', 0)
        end = kwargs.get('end')
        target_start = kwargs.get('target_start', 0)
        draft_id = kwargs.get('draft_id')
        speed = kwargs.get('speed', 1.0)
        volume = kwargs.get('volume', 1.0)
        track_name = kwargs.get('track_name', media_type)
        draft_folder = kwargs.get('draft_folder')
        
        # 获取草稿
        draft_id, script = get_or_create_draft(draft_id=draft_id, width=width, height=height)
        
        # 计算时长
        duration = kwargs.get('duration', 0.0)
        if not end:
            end = duration
        
        # 构建文件名和路径
        ext = 'mp4' if media_type == 'video' else 'mp3'
        filename = f"{media_type}_{url_to_hash(url)}.{ext}"
        local_path = self._build_draft_path(draft_folder, draft_id, filename, media_type)
        
        # 确保轨道存在
        track_type = self.supported_media[media_type]['track_type']
        self._ensure_track_exists(script, track_type, track_name)
        
        # 创建素材和片段
        material = self._create_material(media_type, url, local_path, duration, filename)
        
        transform = {
            'transform_y': kwargs.get('transform_y', 0),
            'scale_x': kwargs.get('scale_x', 1),
            'scale_y': kwargs.get('scale_y', 1),
            'transform_x': kwargs.get('transform_x', 0)
        }
        
        segment = self._create_segment(
            media_type, material, start, end, target_start, speed, volume, transform
        )
        
        # 添加特效（视频专用）
        if media_type == 'video':
            self._add_video_effects(segment, kwargs)
        
        # 添加音效（音频专用）  
        if media_type == 'audio' and kwargs.get('sound_effects'):
            self._add_audio_effects(segment, kwargs['sound_effects'])
        
        # 添加到轨道
        script.add_segment(segment, track_name=track_name)
        
        return {
            "draft_id": draft_id,
            "draft_url": generate_draft_url(draft_id)
        }
    
    def _add_video_effects(self, segment: Any, kwargs: Dict[str, Any]):
        """添加视频特效"""
        transition = kwargs.get('transition')
        if transition:
            try:
                transition_type = getattr(
                    draft.CapCut_Transition_type if IS_CAPCUT_ENV else draft.Transition_type, 
                    transition
                )
                duration_micro = int(kwargs.get('transition_duration', 0.5) * 1e6)
                segment.add_transition(transition_type, duration=duration_micro)
            except AttributeError:
                pass  # 忽略不支持的转场类型
    
    def _add_audio_effects(self, segment: Any, sound_effects: List[Tuple[str, Any]]):
        """添加音频特效"""
        for effect_name, params in sound_effects:
            effect_type = None
            effect_classes = [
                draft.CapCut_Voice_filters_effect_type,
                draft.CapCut_Voice_characters_effect_type,
                draft.CapCut_Speech_to_song_effect_type
            ] if IS_CAPCUT_ENV else [
                draft.Audio_scene_effect_type,
                draft.Tone_effect_type,
                draft.Speech_to_song_type
            ]
            
            for effect_class in effect_classes:
                try:
                    effect_type = getattr(effect_class, effect_name)
                    break
                except AttributeError:
                    continue
            
            if effect_type:
                segment.add_effect(effect_type, params)

# 全局处理器实例
media_handler = MediaHandler()

# 简化后的函数接口
def add_video_track(**kwargs) -> Dict[str, str]:
    """简化版视频处理"""
    kwargs['url'] = kwargs.pop('video_url')
    return media_handler.process_media('video', **kwargs)

def add_audio_track(**kwargs) -> Dict[str, str]:
    """简化版音频处理"""
    kwargs['url'] = kwargs.pop('audio_url')
    return media_handler.process_media('audio', **kwargs)