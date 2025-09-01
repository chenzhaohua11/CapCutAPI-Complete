#!/usr/bin/env python3
"""
Video Track Management Module for CapCut API

提供视频轨道管理功能，支持添加、编辑和管理视频片段
"""

import os
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from pyJianYingDraft import Draft, VideoSegment, Effect, TransitionEffect
from pyJianYingDraft.utils import generate_uuid, format_duration
import logging

logger = logging.getLogger(__name__)

def add_video_track(
    draft_folder: str,
    video_url: str,
    start: float = 0,
    end: Optional[float] = None,
    target_start: float = 0,
    width: int = 1080,
    height: int = 1920,
    transform_x: float = 0,
    transform_y: float = 0,
    scale_x: float = 1,
    scale_y: float = 1,
    speed: float = 1.0,
    track_name: str = "main",
    volume: float = 1.0,
    transition: Optional[str] = None,
    transition_duration: float = 0.5,
    mask_type: Optional[str] = None,
    background_blur: Optional[int] = None
) -> Dict[str, Any]:
    """
    添加视频轨道到草稿
    
    Args:
        draft_folder: 草稿文件夹路径
        video_url: 视频URL或本地路径
        start: 视频开始时间（秒）
        end: 视频结束时间（秒）
        target_start: 在时间轴上的开始位置（秒）
        width: 视频宽度
        height: 视频高度
        transform_x: X轴位置偏移
        transform_y: Y轴位置偏移
        scale_x: X轴缩放比例
        scale_y: Y轴缩放比例
        speed: 播放速度
        track_name: 轨道名称
        volume: 音量大小
        transition: 转场类型
        transition_duration: 转场时长
        mask_type: 蒙版类型
        background_blur: 背景模糊级别
        
    Returns:
        操作结果字典
    """
    try:
        # 验证输入参数
        if not os.path.exists(draft_folder):
            return {"success": False, "error": f"Draft folder does not exist: {draft_folder}"}
            
        if not video_url:
            return {"success": False, "error": "Video URL is required"}
            
        # 加载草稿
        draft_file = os.path.join(draft_folder, "draft.json")
        if os.path.exists(draft_file):
            with open(draft_file, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
        else:
            draft_data = {
                "canvas_config": {
                    "width": width,
                    "height": height,
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
        
        # 处理视频文件
        video_path = video_url
        if video_url.startswith('http'):
            # 下载视频文件
            import requests
            video_filename = f"video_{material_id}.mp4"
            video_path = os.path.join(draft_folder, "videos", video_filename)
            
            try:
                response = requests.get(video_url, stream=True)
                response.raise_for_status()
                
                with open(video_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                logger.info(f"Downloaded video: {video_url}")
            except Exception as e:
                return {"success": False, "error": f"Failed to download video: {str(e)}"}
        
        # 获取视频时长
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_duration = frame_count / fps if fps > 0 else 0
            cap.release()
        except Exception:
            video_duration = 10  # 默认时长
            
        # 设置结束时间
        if end is None:
            end = video_duration
            
        duration = end - start
        
        # 创建视频素材
        video_material = {
            "id": material_id,
            "type": "video",
            "name": os.path.basename(video_path),
            "path": video_path,
            "duration": video_duration,
            "width": width,
            "height": height,
            "fps": 30,
            "volume": volume,
            "speed": speed
        }
        
        # 创建视频片段
        video_segment = {
            "id": segment_id,
            "material_id": material_id,
            "start": start,
            "duration": duration,
            "target_start": target_start,
            "target_duration": duration / speed,
            "transform": {
                "x": transform_x,
                "y": transform_y,
                "scale_x": scale_x,
                "scale_y": scale_y
            },
            "effects": []
        }
        
        # 添加转场效果
        if transition:
            transition_effect = {
                "id": generate_uuid(),
                "type": "transition",
                "name": transition,
                "duration": transition_duration,
                "target_segment": segment_id
            }
            video_segment["effects"].append(transition_effect)
            
        # 添加蒙版效果
        if mask_type:
            mask_effect = {
                "id": generate_uuid(),
                "type": "mask",
                "name": mask_type,
                "target_segment": segment_id
            }
            video_segment["effects"].append(mask_effect)
            
        # 添加背景模糊效果
        if background_blur:
            blur_effect = {
                "id": generate_uuid(),
                "type": "background_blur",
                "level": background_blur,
                "target_segment": segment_id
            }
            video_segment["effects"].append(blur_effect)
        
        # 添加素材到草稿
        draft_data["materials"]["videos"].append(video_material)
        
        # 查找或创建视频轨道
        video_track = None
        for track in draft_data["tracks"]["video"]:
            if track["name"] == track_name:
                video_track = track
                break
                
        if not video_track:
            video_track = {
                "id": generate_uuid(),
                "name": track_name,
                "type": "video",
                "segments": []
            }
            draft_data["tracks"]["video"].append(video_track)
        
        # 添加片段到轨道
        video_track["segments"].append(video_segment)
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Added video track: {video_url} to draft: {draft_folder}")
        
        return {
            "success": True,
            "material_id": material_id,
            "segment_id": segment_id,
            "video_path": video_path,
            "duration": duration,
            "track_name": track_name
        }
        
    except Exception as e:
        logger.error(f"Error adding video track: {str(e)}")
        return {"success": False, "error": str(e)}

def remove_video_track(draft_folder: str, segment_id: str) -> Dict[str, Any]:
    """
    从草稿中移除视频轨道
    
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
        
        # 移除对应的视频片段
        for track in draft_data["tracks"]["video"]:
            track["segments"] = [
                segment for segment in track["segments"]
                if segment["id"] != segment_id
            ]
        
        # 移除对应的视频素材
        draft_data["materials"]["videos"] = [
            material for material in draft_data["materials"]["videos"]
            if not any(segment["material_id"] == material["id"] 
                      for track in draft_data["tracks"]["video"] 
                      for segment in track["segments"])
        ]
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        return {"success": True, "message": f"Removed video segment: {segment_id}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_video_track(
    draft_folder: str,
    segment_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    更新视频轨道参数
    
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
        
        # 查找并更新视频片段
        updated = False
        for track in draft_data["tracks"]["video"]:
            for segment in track["segments"]:
                if segment["id"] == segment_id:
                    # 更新transform参数
                    if "transform_x" in kwargs or "transform_y" in kwargs:
                        segment["transform"]["x"] = kwargs.get("transform_x", segment["transform"]["x"])
                        segment["transform"]["y"] = kwargs.get("transform_y", segment["transform"]["y"])
                    
                    # 更新缩放参数
                    if "scale_x" in kwargs or "scale_y" in kwargs:
                        segment["transform"]["scale_x"] = kwargs.get("scale_x", segment["transform"]["scale_x"])
                        segment["transform"]["scale_y"] = kwargs.get("scale_y", segment["transform"]["scale_y"])
                    
                    # 更新其他参数
                    if "start" in kwargs:
                        segment["start"] = kwargs["start"]
                    if "duration" in kwargs:
                        segment["duration"] = kwargs["duration"]
                    if "target_start" in kwargs:
                        segment["target_start"] = kwargs["target_start"]
                    
                    updated = True
                    break
            if updated:
                break
        
        if not updated:
            return {"success": False, "error": "Video segment not found"}
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        return {"success": True, "message": f"Updated video segment: {segment_id}"}
        
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
        
        # 测试添加视频轨道
        result = add_video_track(
            draft_folder=draft_folder,
            video_url="test_video.mp4",
            start=0,
            end=10,
            target_start=0,
            width=1080,
            height=1920
        )
        
        print("Test result:", result)