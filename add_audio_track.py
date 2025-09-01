#!/usr/bin/env python3
"""
Audio Track Management Module for CapCut API

提供音频轨道管理功能，支持添加、编辑和管理音频片段
"""

import os
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from pyJianYingDraft import Draft, AudioSegment, Effect
from pyJianYingDraft.utils import generate_uuid, format_duration
import logging
import requests

logger = logging.getLogger(__name__)

def add_audio_track(
    draft_folder: str,
    audio_url: str,
    start: float = 0,
    end: Optional[float] = None,
    target_start: float = 0,
    volume: float = 1.0,
    speed: float = 1.0,
    fade_in: float = 0,
    fade_out: float = 0,
    track_name: str = "main",
    audio_type: str = "music",
    normalize: bool = True,
    loop: bool = False
) -> Dict[str, Any]:
    """
    添加音频轨道到草稿
    
    Args:
        draft_folder: 草稿文件夹路径
        audio_url: 音频URL或本地路径
        start: 音频开始时间（秒）
        end: 音频结束时间（秒）
        target_start: 在时间轴上的开始位置（秒）
        volume: 音量大小 (0-2)
        speed: 播放速度 (0.5-2.0)
        fade_in: 淡入时长（秒）
        fade_out: 淡出时长（秒）
        track_name: 轨道名称
        audio_type: 音频类型 (music, sound_effect, voice_over)
        normalize: 是否标准化音量
        loop: 是否循环播放
        
    Returns:
        操作结果字典
    """
    try:
        # 验证输入参数
        if not os.path.exists(draft_folder):
            return {"success": False, "error": f"Draft folder does not exist: {draft_folder}"}
            
        if not audio_url:
            return {"success": False, "error": "Audio URL is required"}
            
        # 加载草稿
        draft_file = os.path.join(draft_folder, "draft.json")
        if os.path.exists(draft_file):
            with open(draft_file, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
        else:
            draft_data = {
                "canvas_config": {
                    "width": 1080,
                    "height": 1920,
                    "fps": 30
                },
                "materials": {
                    "videos": [],
                    "audios": [],
                    "images": [],
                    "texts": [],
                    "effects": []
                },
                "tracks": {
                    "video": [],
                    "audio": [],
                    "text": [],
                    "effect": []
                }
            }
        
        # 生成唯一ID
        material_id = generate_uuid()
        segment_id = generate_uuid()
        
        # 处理音频文件
        audio_path = audio_url
        if audio_url.startswith('http'):
            # 下载音频文件
            audio_filename = f"audio_{material_id}.mp3"
            audio_path = os.path.join(draft_folder, "audios", audio_filename)
            
            try:
                response = requests.get(audio_url, stream=True)
                response.raise_for_status()
                
                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                with open(audio_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                logger.info(f"Downloaded audio: {audio_url}")
            except Exception as e:
                return {"success": False, "error": f"Failed to download audio: {str(e)}"}
        
        # 获取音频时长
        try:
            from pydub import AudioSegment as AudioFile
            audio = AudioFile.from_file(audio_path)
            audio_duration = len(audio) / 1000.0  # 转换为秒
        except Exception:
            audio_duration = 30  # 默认时长
            
        # 设置结束时间
        if end is None:
            end = audio_duration
            
        duration = end - start
        
        # 创建音频素材
        audio_material = {
            "id": material_id,
            "type": "audio",
            "name": os.path.basename(audio_path),
            "path": audio_path,
            "duration": audio_duration,
            "audio_type": audio_type,
            "volume": volume,
            "speed": speed,
            "fade_in": fade_in,
            "fade_out": fade_out,
            "normalize": normalize,
            "loop": loop
        }
        
        # 创建音频片段
        audio_segment = {
            "id": segment_id,
            "material_id": material_id,
            "start": start,
            "duration": duration,
            "target_start": target_start,
            "target_duration": duration / speed,
            "volume": volume,
            "speed": speed,
            "fade_in": fade_in,
            "fade_out": fade_out,
            "loop": loop
        }
        
        # 添加素材到草稿
        draft_data["materials"]["audios"].append(audio_material)
        
        # 查找或创建音频轨道
        audio_track = None
        for track in draft_data["tracks"]["audio"]:
            if track["name"] == track_name:
                audio_track = track
                break
                
        if not audio_track:
            audio_track = {
                "id": generate_uuid(),
                "name": track_name,
                "type": "audio",
                "segments": []
            }
            draft_data["tracks"]["audio"].append(audio_track)
        
        # 添加片段到轨道
        audio_track["segments"].append(audio_segment)
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Added audio track: {audio_url} to draft: {draft_folder}")
        
        return {
            "success": True,
            "material_id": material_id,
            "segment_id": segment_id,
            "audio_path": audio_path,
            "duration": duration,
            "track_name": track_name,
            "audio_type": audio_type
        }
        
    except Exception as e:
        logger.error(f"Error adding audio track: {str(e)}")
        return {"success": False, "error": str(e)}

def add_sound_effect(
    draft_folder: str,
    effect_url: str,
    target_start: float = 0,
    volume: float = 1.0,
    fade_in: float = 0,
    fade_out: float = 0,
    track_name: str = "effects"
) -> Dict[str, Any]:
    """
    添加音效到草稿
    
    Args:
        draft_folder: 草稿文件夹路径
        effect_url: 音效URL或本地路径
        target_start: 在时间轴上的开始位置（秒）
        volume: 音量大小
        fade_in: 淡入时长（秒）
        fade_out: 淡出时长（秒）
        track_name: 轨道名称
        
    Returns:
        操作结果字典
    """
    return add_audio_track(
        draft_folder=draft_folder,
        audio_url=effect_url,
        target_start=target_start,
        volume=volume,
        fade_in=fade_in,
        fade_out=fade_out,
        track_name=track_name,
        audio_type="sound_effect"
    )

def add_voice_over(
    draft_folder: str,
    voice_url: str,
    target_start: float = 0,
    volume: float = 1.0,
    fade_in: float = 0.1,
    fade_out: float = 0.1,
    track_name: str = "voice_over"
) -> Dict[str, Any]:
    """
    添加旁白到草稿
    
    Args:
        draft_folder: 草稿文件夹路径
        voice_url: 旁白URL或本地路径
        target_start: 在时间轴上的开始位置（秒）
        volume: 音量大小
        fade_in: 淡入时长（秒）
        fade_out: 淡出时长（秒）
        track_name: 轨道名称
        
    Returns:
        操作结果字典
    """
    return add_audio_track(
        draft_folder=draft_folder,
        audio_url=voice_url,
        target_start=target_start,
        volume=volume,
        fade_in=fade_in,
        fade_out=fade_out,
        track_name=track_name,
        audio_type="voice_over"
    )

def remove_audio_track(draft_folder: str, segment_id: str) -> Dict[str, Any]:
    """
    从草稿中移除音频轨道
    
    Args:
        draft_folder: 草稿文件夹路径
        segment_id: 片段ID
        
    Returns:
        操作结果字典
    """
    try:
        draft_file = os.path.join(draft_folder, "draft.json")
        if not os.path.exists(draft_file):
            return {"success": False, "error": "Draft file not found"}
            
        with open(draft_file, 'r', encoding='utf-8') as f:
            draft_data = json.load(f)
        
        # 移除对应的音频片段
        for track in draft_data["tracks"]["audio"]:
            track["segments"] = [
                segment for segment in track["segments"]
                if segment["id"] != segment_id
            ]
        
        # 移除对应的音频素材
        draft_data["materials"]["audios"] = [
            material for material in draft_data["materials"]["audios"]
            if not any(segment["material_id"] == material["id"] 
                      for track in draft_data["tracks"]["audio"] 
                      for segment in track["segments"])
        ]
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        return {"success": True, "message": f"Removed audio segment: {segment_id}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_audio_track(
    draft_folder: str,
    segment_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    更新音频轨道参数
    
    Args:
        draft_folder: 草稿文件夹路径
        segment_id: 片段ID
        **kwargs: 要更新的参数
        
    Returns:
        操作结果字典
    """
    try:
        draft_file = os.path.join(draft_folder, "draft.json")
        if not os.path.exists(draft_file):
            return {"success": False, "error": "Draft file not found"}
            
        with open(draft_file, 'r', encoding='utf-8') as f:
            draft_data = json.load(f)
        
        # 查找并更新音频片段
        updated = False
        for track in draft_data["tracks"]["audio"]:
            for segment in track["segments"]:
                if segment["id"] == segment_id:
                    # 更新音量
                    if "volume" in kwargs:
                        segment["volume"] = kwargs["volume"]
                    
                    # 更新速度
                    if "speed" in kwargs:
                        segment["speed"] = kwargs["speed"]
                    
                    # 更新淡入淡出
                    if "fade_in" in kwargs:
                        segment["fade_in"] = kwargs["fade_in"]
                    if "fade_out" in kwargs:
                        segment["fade_out"] = kwargs["fade_out"]
                    
                    # 更新时间参数
                    if "target_start" in kwargs:
                        segment["target_start"] = kwargs["target_start"]
                    
                    updated = True
                    break
            if updated:
                break
        
        if not updated:
            return {"success": False, "error": "Audio segment not found"}
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        return {"success": True, "message": f"Updated audio segment: {segment_id}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def adjust_audio_levels(draft_folder: str, track_name: str, volume: float) -> Dict[str, Any]:
    """
    调整整个音频轨道的音量
    
    Args:
        draft_folder: 草稿文件夹路径
        track_name: 轨道名称
        volume: 音量大小 (0-2)
        
    Returns:
        操作结果字典
    """
    try:
        draft_file = os.path.join(draft_folder, "draft.json")
        if not os.path.exists(draft_file):
            return {"success": False, "error": "Draft file not found"}
            
        with open(draft_file, 'r', encoding='utf-8') as f:
            draft_data = json.load(f)
        
        # 查找并更新轨道音量
        updated = 0
        for track in draft_data["tracks"]["audio"]:
            if track["name"] == track_name:
                for segment in track["segments"]:
                    segment["volume"] = volume
                    updated += 1
        
        if updated == 0:
            return {"success": False, "error": f"Audio track not found: {track_name}"}
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        return {"success": True, "message": f"Updated {updated} audio segments in track: {track_name}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # 测试功能
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试草稿
        draft_id = "test_draft"
        draft_folder = os.path.join(temp_dir, draft_id)
        os.makedirs(draft_folder, exist_ok=True)
        
        # 测试添加音频轨道
        result = add_audio_track(
            draft_folder=draft_folder,
            audio_url="test_audio.mp3",
            target_start=0,
            volume=0.8,
            fade_in=0.5,
            fade_out=0.5
        )
        
        print("Test result:", result)