#!/usr/bin/env python3
"""
Text and Subtitle Management Module for CapCut API

提供文本和字幕管理功能，支持添加、编辑和管理文字内容
"""

import os
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from pyJianYingDraft import Draft, TextSegment, SubtitleSegment
from pyJianYingDraft.utils import generate_uuid, format_duration
import logging

logger = logging.getLogger(__name__)

def add_text(
    draft_folder: str,
    text: str,
    start: float = 0,
    duration: float = 5,
    x: float = 540,
    y: float = 960,
    font_size: int = 32,
    font_family: str = "PingFang SC",
    font_weight: str = "normal",
    color: str = "#FFFFFF",
    background_color: Optional[str] = None,
    stroke_color: Optional[str] = None,
    stroke_width: int = 0,
    shadow_color: Optional[str] = None,
    shadow_offset_x: int = 0,
    shadow_offset_y: int = 0,
    shadow_blur: int = 0,
    opacity: float = 1.0,
    rotation: float = 0,
    scale_x: float = 1,
    scale_y: float = 1,
    alignment: str = "center",
    line_spacing: float = 1.2,
    letter_spacing: float = 0,
    track_name: str = "main",
    animation_type: Optional[str] = None,
    animation_duration: float = 1.0
) -> Dict[str, Any]:
    """
    添加文本到草稿
    
    Args:
        draft_folder: 草稿文件夹路径
        text: 文本内容
        start: 开始时间（秒）
        duration: 持续时间（秒）
        x: X坐标位置
        y: Y坐标位置
        font_size: 字体大小
        font_family: 字体族
        font_weight: 字体粗细
        color: 文字颜色
        background_color: 背景颜色
        stroke_color: 描边颜色
        stroke_width: 描边宽度
        shadow_color: 阴影颜色
        shadow_offset_x: 阴影X偏移
        shadow_offset_y: 阴影Y偏移
        shadow_blur: 阴影模糊
        opacity: 透明度 (0-1)
        rotation: 旋转角度（度）
        scale_x: X轴缩放
        scale_y: Y轴缩放
        alignment: 对齐方式 (left, center, right)
        line_spacing: 行间距
        letter_spacing: 字间距
        track_name: 轨道名称
        animation_type: 动画类型
        animation_duration: 动画时长
        
    Returns:
        操作结果字典
    """
    try:
        # 验证输入参数
        if not os.path.exists(draft_folder):
            return {"success": False, "error": f"Draft folder does not exist: {draft_folder}"}
            
        if not text:
            return {"success": False, "error": "Text content is required"}
            
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
        
        # 创建文本素材
        text_material = {
            "id": material_id,
            "type": "text",
            "content": text,
            "font": {
                "family": font_family,
                "size": font_size,
                "weight": font_weight,
                "color": color
            },
            "background": {
                "color": background_color,
                "opacity": opacity
            } if background_color else None,
            "stroke": {
                "color": stroke_color,
                "width": stroke_width
            } if stroke_color else None,
            "shadow": {
                "color": shadow_color,
                "offset_x": shadow_offset_x,
                "offset_y": shadow_offset_y,
                "blur": shadow_blur
            } if shadow_color else None,
            "alignment": alignment,
            "line_spacing": line_spacing,
            "letter_spacing": letter_spacing,
            "animation": {
                "type": animation_type,
                "duration": animation_duration
            } if animation_type else None
        }
        
        # 创建文本片段
        text_segment = {
            "id": segment_id,
            "material_id": material_id,
            "start": start,
            "duration": duration,
            "position": {
                "x": x,
                "y": y
            },
            "transform": {
                "rotation": rotation,
                "scale_x": scale_x,
                "scale_y": scale_y
            },
            "opacity": opacity
        }
        
        # 添加素材到草稿
        draft_data["materials"]["texts"].append(text_material)
        
        # 查找或创建文本轨道
        text_track = None
        for track in draft_data["tracks"]["text"]:
            if track["name"] == track_name:
                text_track = track
                break
                
        if not text_track:
            text_track = {
                "id": generate_uuid(),
                "name": track_name,
                "type": "text",
                "segments": []
            }
            draft_data["tracks"]["text"].append(text_track)
        
        # 添加片段到轨道
        text_track["segments"].append(text_segment)
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Added text: '{text[:50]}...' to draft: {draft_folder}")
        
        return {
            "success": True,
            "material_id": material_id,
            "segment_id": segment_id,
            "text": text,
            "duration": duration,
            "track_name": track_name
        }
        
    except Exception as e:
        logger.error(f"Error adding text: {str(e)}")
        return {"success": False, "error": str(e)}

def add_subtitle(
    draft_folder: str,
    text: str,
    start: float,
    end: float,
    x: float = 540,
    y: float = 1700,
    font_size: int = 24,
    font_family: str = "PingFang SC",
    color: str = "#FFFFFF",
    background_color: str = "#000000",
    background_opacity: float = 0.7,
    stroke_color: str = "#000000",
    stroke_width: int = 2,
    alignment: str = "center",
    track_name: str = "subtitles"
) -> Dict[str, Any]:
    """
    添加字幕到草稿
    
    Args:
        draft_folder: 草稿文件夹路径
        text: 字幕内容
        start: 开始时间（秒）
        end: 结束时间（秒）
        x: X坐标位置
        y: Y坐标位置
        font_size: 字体大小
        font_family: 字体族
        color: 文字颜色
        background_color: 背景颜色
        background_opacity: 背景透明度
        stroke_color: 描边颜色
        stroke_width: 描边宽度
        alignment: 对齐方式
        track_name: 轨道名称
        
    Returns:
        操作结果字典
    """
    duration = end - start
    
    return add_text(
        draft_folder=draft_folder,
        text=text,
        start=start,
        duration=duration,
        x=x,
        y=y,
        font_size=font_size,
        font_family=font_family,
        color=color,
        background_color=background_color,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        alignment=alignment,
        track_name=track_name
    )

def add_title(
    draft_folder: str,
    title: str,
    subtitle: Optional[str] = None,
    start: float = 0,
    duration: float = 5,
    x: float = 540,
    y: float = 300,
    font_size: int = 48,
    subtitle_font_size: int = 24,
    color: str = "#FFFFFF",
    subtitle_color: str = "#CCCCCC",
    track_name: str = "titles"
) -> Dict[str, Any]:
    """
    添加标题到草稿
    
    Args:
        draft_folder: 草稿文件夹路径
        title: 主标题
        subtitle: 副标题（可选）
        start: 开始时间（秒）
        duration: 持续时间（秒）
        x: X坐标位置
        y: Y坐标位置
        font_size: 主标题字体大小
        subtitle_font_size: 副标题字体大小
        color: 主标题颜色
        subtitle_color: 副标题颜色
        track_name: 轨道名称
        
    Returns:
        操作结果字典
    """
    try:
        # 先添加主标题
        title_result = add_text(
            draft_folder=draft_folder,
            text=title,
            start=start,
            duration=duration,
            x=x,
            y=y,
            font_size=font_size,
            color=color,
            track_name=track_name
        )
        
        if subtitle and title_result["success"]:
            # 添加副标题
            subtitle_result = add_text(
                draft_folder=draft_folder,
                text=subtitle,
                start=start,
                duration=duration,
                x=x,
                y=y + 60,  # 副标题位置在主标题下方
                font_size=subtitle_font_size,
                color=subtitle_color,
                track_name=track_name
            )
            
            return {
                "success": True,
                "title_id": title_result["segment_id"],
                "subtitle_id": subtitle_result.get("segment_id"),
                "message": "Added title and subtitle"
            }
        
        return title_result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def remove_text(draft_folder: str, segment_id: str) -> Dict[str, Any]:
    """
    从草稿中移除文本
    
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
        
        # 移除对应的文本片段
        for track in draft_data["tracks"]["text"]:
            track["segments"] = [
                segment for segment in track["segments"]
                if segment["id"] != segment_id
            ]
        
        # 移除对应的文本素材
        draft_data["materials"]["texts"] = [
            material for material in draft_data["materials"]["texts"]
            if not any(segment["material_id"] == material["id"] 
                      for track in draft_data["tracks"]["text"] 
                      for segment in track["segments"])
        ]
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        return {"success": True, "message": f"Removed text segment: {segment_id}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_text(
    draft_folder: str,
    segment_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    更新文本参数
    
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
        
        # 查找并更新文本素材
        updated = False
        for material in draft_data["materials"]["texts"]:
            for track in draft_data["tracks"]["text"]:
                for segment in track["segments"]:
                    if segment["id"] == segment_id and segment["material_id"] == material["id"]:
                        # 更新文本内容
                        if "text" in kwargs:
                            material["content"] = kwargs["text"]
                        
                        # 更新字体参数
                        if "font_size" in kwargs:
                            material["font"]["size"] = kwargs["font_size"]
                        if "font_family" in kwargs:
                            material["font"]["family"] = kwargs["font_family"]
                        if "color" in kwargs:
                            material["font"]["color"] = kwargs["color"]
                        
                        # 更新位置参数
                        if "x" in kwargs or "y" in kwargs:
                            segment["position"]["x"] = kwargs.get("x", segment["position"]["x"])
                            segment["position"]["y"] = kwargs.get("y", segment["position"]["y"])
                        
                        # 更新时间参数
                        if "start" in kwargs:
                            segment["start"] = kwargs["start"]
                        if "duration" in kwargs:
                            segment["duration"] = kwargs["duration"]
                        
                        updated = True
                        break
                if updated:
                    break
            if updated:
                break
        
        if not updated:
            return {"success": False, "error": "Text segment not found"}
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        return {"success": True, "message": f"Updated text segment: {segment_id}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def add_subtitle_track(
    draft_folder: str,
    subtitles: List[Dict[str, Any]],
    track_name: str = "subtitles"
) -> Dict[str, Any]:
    """
    批量添加字幕轨道
    
    Args:
        draft_folder: 草稿文件夹路径
        subtitles: 字幕列表，每个字幕包含 text, start, end 等参数
        track_name: 轨道名称
        
    Returns:
        操作结果字典
    """
    try:
        results = []
        for subtitle in subtitles:
            result = add_subtitle(
                draft_folder=draft_folder,
                text=subtitle["text"],
                start=subtitle["start"],
                end=subtitle["end"],
                x=subtitle.get("x", 540),
                y=subtitle.get("y", 1700),
                font_size=subtitle.get("font_size", 24),
                track_name=track_name
            )
            results.append(result)
        
        success_count = sum(1 for r in results if r["success"])
        return {
            "success": True,
            "message": f"Added {success_count} subtitles",
            "results": results
        }
        
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
        
        # 测试添加文本
        result = add_text(
            draft_folder=draft_folder,
            text="Hello, World!",
            start=0,
            duration=3,
            x=540,
            y=960,
            font_size=32,
            color="#FFFFFF"
        )
        
        print("Test result:", result)