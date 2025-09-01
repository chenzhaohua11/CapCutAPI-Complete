#!/usr/bin/env python3
"""
Effects and Transitions Management Module for CapCut API

提供特效和转场管理功能，支持添加、编辑和管理各种视觉效果
"""

import os
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from pyJianYingDraft import Draft, Effect, TransitionEffect, FilterEffect
from pyJianYingDraft.utils import generate_uuid, format_duration
import logging

logger = logging.getLogger(__name__)

# 特效类型定义
EFFECT_TYPES = {
    "transition": ["fade", "slide", "wipe", "zoom", "dissolve", "push", "cover"],
    "filter": ["vintage", "black_white", "sepia", "cold", "warm", "sharpen", "blur"],
    "adjust": ["brightness", "contrast", "saturation", "hue", "exposure", "gamma"],
    "animation": ["scale", "rotate", "position", "opacity"],
    "mask": ["circle", "rectangle", "heart", "star", "custom"],
    "particle": ["snow", "rain", "fireworks", "sparkle", "bubbles"],
    "distortion": ["wave", "ripple", "twirl", "bulge"]
}

def add_transition(
    draft_folder: str,
    transition_type: str,
    duration: float = 0.5,
    target_segment_id: Optional[str] = None,
    position: str = "end",
    easing: str = "ease_in_out"
) -> Dict[str, Any]:
    """
    添加转场效果
    
    Args:
        draft_folder: 草稿文件夹路径
        transition_type: 转场类型
        duration: 转场时长（秒）
        target_segment_id: 目标片段ID
        position: 转场位置 (start, end, between)
        easing: 缓动函数
        
    Returns:
        操作结果字典
    """
    try:
        if not os.path.exists(draft_folder):
            return {"success": False, "error": f"Draft folder does not exist: {draft_folder}"}
            
        if transition_type not in EFFECT_TYPES["transition"]:
            return {"success": False, "error": f"Invalid transition type: {transition_type}"}
            
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
        effect_id = generate_uuid()
        
        # 创建转场效果
        transition_effect = {
            "id": effect_id,
            "type": "transition",
            "name": transition_type,
            "duration": duration,
            "target_segment": target_segment_id,
            "position": position,
            "easing": easing,
            "parameters": {
                "direction": "left_to_right",
                "softness": 0.5
            }
        }
        
        # 添加效果到草稿
        draft_data["materials"]["effects"].append(transition_effect)
        
        # 查找或创建效果轨道
        effect_track = None
        for track in draft_data["tracks"]["effect"]:
            if track["name"] == "transitions":
                effect_track = track
                break
                
        if not effect_track:
            effect_track = {
                "id": generate_uuid(),
                "name": "transitions",
                "type": "effect",
                "segments": []
            }
            draft_data["tracks"]["effect"].append(effect_track)
        
        # 添加效果到轨道
        effect_track["segments"].append({
            "id": generate_uuid(),
            "effect_id": effect_id,
            "start": 0,
            "duration": duration,
            "target_segment": target_segment_id
        })
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Added transition: {transition_type} to draft: {draft_folder}")
        
        return {
            "success": True,
            "effect_id": effect_id,
            "transition_type": transition_type,
            "duration": duration
        }
        
    except Exception as e:
        logger.error(f"Error adding transition: {str(e)}")
        return {"success": False, "error": str(e)}

def add_filter(
    draft_folder: str,
    filter_type: str,
    intensity: float = 1.0,
    target_segment_id: Optional[str] = None,
    start: float = 0,
    duration: Optional[float] = None
) -> Dict[str, Any]:
    """
    添加滤镜效果
    
    Args:
        draft_folder: 草稿文件夹路径
        filter_type: 滤镜类型
        intensity: 强度 (0-1)
        target_segment_id: 目标片段ID
        start: 开始时间（秒）
        duration: 持续时间（秒）
        
    Returns:
        操作结果字典
    """
    try:
        if not os.path.exists(draft_folder):
            return {"success": False, "error": f"Draft folder does not exist: {draft_folder}"}
            
        if filter_type not in EFFECT_TYPES["filter"]:
            return {"success": False, "error": f"Invalid filter type: {filter_type}"}
            
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
        effect_id = generate_uuid()
        
        # 创建滤镜效果
        filter_effect = {
            "id": effect_id,
            "type": "filter",
            "name": filter_type,
            "intensity": intensity,
            "target_segment": target_segment_id,
            "start": start,
            "duration": duration,
            "parameters": {
                "intensity": intensity,
                "blend_mode": "normal"
            }
        }
        
        # 添加效果到草稿
        draft_data["materials"]["effects"].append(filter_effect)
        
        # 查找或创建效果轨道
        effect_track = None
        for track in draft_data["tracks"]["effect"]:
            if track["name"] == "filters":
                effect_track = track
                break
                
        if not effect_track:
            effect_track = {
                "id": generate_uuid(),
                "name": "filters",
                "type": "effect",
                "segments": []
            }
            draft_data["tracks"]["effect"].append(effect_track)
        
        # 添加效果到轨道
        effect_track["segments"].append({
            "id": generate_uuid(),
            "effect_id": effect_id,
            "start": start,
            "duration": duration or 10,
            "target_segment": target_segment_id
        })
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Added filter: {filter_type} to draft: {draft_folder}")
        
        return {
            "success": True,
            "effect_id": effect_id,
            "filter_type": filter_type,
            "intensity": intensity
        }
        
    except Exception as e:
        logger.error(f"Error adding filter: {str(e)}")
        return {"success": False, "error": str(e)}

def add_adjustment(
    draft_folder: str,
    adjustment_type: str,
    value: float,
    target_segment_id: Optional[str] = None,
    start: float = 0,
    duration: Optional[float] = None
) -> Dict[str, Any]:
    """
    添加调整效果
    
    Args:
        draft_folder: 草稿文件夹路径
        adjustment_type: 调整类型
        value: 调整值
        target_segment_id: 目标片段ID
        start: 开始时间（秒）
        duration: 持续时间（秒）
        
    Returns:
        操作结果字典
    """
    try:
        if not os.path.exists(draft_folder):
            return {"success": False, "error": f"Draft folder does not exist: {draft_folder}"}
            
        if adjustment_type not in EFFECT_TYPES["adjust"]:
            return {"success": False, "error": f"Invalid adjustment type: {adjustment_type}"}
            
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
        effect_id = generate_uuid()
        
        # 创建调整效果
        adjustment_effect = {
            "id": effect_id,
            "type": "adjustment",
            "name": adjustment_type,
            "value": value,
            "target_segment": target_segment_id,
            "start": start,
            "duration": duration,
            "parameters": {
                "value": value,
                "interpolation": "linear"
            }
        }
        
        # 添加效果到草稿
        draft_data["materials"]["effects"].append(adjustment_effect)
        
        # 查找或创建效果轨道
        effect_track = None
        for track in draft_data["tracks"]["effect"]:
            if track["name"] == "adjustments":
                effect_track = track
                break
                
        if not effect_track:
            effect_track = {
                "id": generate_uuid(),
                "name": "adjustments",
                "type": "effect",
                "segments": []
            }
            draft_data["tracks"]["effect"].append(effect_track)
        
        # 添加效果到轨道
        effect_track["segments"].append({
            "id": generate_uuid(),
            "effect_id": effect_id,
            "start": start,
            "duration": duration or 10,
            "target_segment": target_segment_id
        })
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Added adjustment: {adjustment_type}={value} to draft: {draft_folder}")
        
        return {
            "success": True,
            "effect_id": effect_id,
            "adjustment_type": adjustment_type,
            "value": value
        }
        
    except Exception as e:
        logger.error(f"Error adding adjustment: {str(e)}")
        return {"success": False, "error": str(e)}

def add_animation(
    draft_folder: str,
    animation_type: str,
    start_value: float,
    end_value: float,
    target_segment_id: str,
    start: float = 0,
    duration: float = 1.0,
    easing: str = "ease_in_out"
) -> Dict[str, Any]:
    """
    添加动画效果
    
    Args:
        draft_folder: 草稿文件夹路径
        animation_type: 动画类型
        start_value: 起始值
        end_value: 结束值
        target_segment_id: 目标片段ID
        start: 开始时间（秒）
        duration: 持续时间（秒）
        easing: 缓动函数
        
    Returns:
        操作结果字典
    """
    try:
        if not os.path.exists(draft_folder):
            return {"success": False, "error": f"Draft folder does not exist: {draft_folder}"}
            
        if animation_type not in EFFECT_TYPES["animation"]:
            return {"success": False, "error": f"Invalid animation type: {animation_type}"}
            
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
        effect_id = generate_uuid()
        
        # 创建动画效果
        animation_effect = {
            "id": effect_id,
            "type": "animation",
            "name": animation_type,
            "start_value": start_value,
            "end_value": end_value,
            "target_segment": target_segment_id,
            "start": start,
            "duration": duration,
            "easing": easing,
            "parameters": {
                "start_value": start_value,
                "end_value": end_value,
                "easing": easing
            }
        }
        
        # 添加效果到草稿
        draft_data["materials"]["effects"].append(animation_effect)
        
        # 查找或创建效果轨道
        effect_track = None
        for track in draft_data["tracks"]["effect"]:
            if track["name"] == "animations":
                effect_track = track
                break
                
        if not effect_track:
            effect_track = {
                "id": generate_uuid(),
                "name": "animations",
                "type": "effect",
                "segments": []
            }
            draft_data["tracks"]["effect"].append(effect_track)
        
        # 添加效果到轨道
        effect_track["segments"].append({
            "id": generate_uuid(),
            "effect_id": effect_id,
            "start": start,
            "duration": duration,
            "target_segment": target_segment_id
        })
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Added animation: {animation_type} to draft: {draft_folder}")
        
        return {
            "success": True,
            "effect_id": effect_id,
            "animation_type": animation_type,
            "start_value": start_value,
            "end_value": end_value
        }
        
    except Exception as e:
        logger.error(f"Error adding animation: {str(e)}")
        return {"success": False, "error": str(e)}

def add_particle_effect(
    draft_folder: str,
    particle_type: str,
    start: float = 0,
    duration: float = 3.0,
    intensity: float = 1.0,
    color: str = "#FFFFFF",
    speed: float = 1.0,
    size: float = 1.0,
    track_name: str = "particles"
) -> Dict[str, Any]:
    """
    添加粒子效果
    
    Args:
        draft_folder: 草稿文件夹路径
        particle_type: 粒子类型
        start: 开始时间（秒）
        duration: 持续时间（秒）
        intensity: 强度 (0-1)
        color: 颜色
        speed: 速度
        size: 大小
        track_name: 轨道名称
        
    Returns:
        操作结果字典
    """
    try:
        if not os.path.exists(draft_folder):
            return {"success": False, "error": f"Draft folder does not exist: {draft_folder}"}
            
        if particle_type not in EFFECT_TYPES["particle"]:
            return {"success": False, "error": f"Invalid particle type: {particle_type}"}
            
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
        effect_id = generate_uuid()
        segment_id = generate_uuid()
        
        # 创建粒子效果
        particle_effect = {
            "id": effect_id,
            "type": "particle",
            "name": particle_type,
            "intensity": intensity,
            "color": color,
            "speed": speed,
            "size": size,
            "parameters": {
                "particle_count": int(100 * intensity),
                "lifetime": 2.0,
                "gravity": 0.1
            }
        }
        
        # 添加效果到草稿
        draft_data["materials"]["effects"].append(particle_effect)
        
        # 查找或创建效果轨道
        effect_track = None
        for track in draft_data["tracks"]["effect"]:
            if track["name"] == track_name:
                effect_track = track
                break
                
        if not effect_track:
            effect_track = {
                "id": generate_uuid(),
                "name": track_name,
                "type": "effect",
                "segments": []
            }
            draft_data["tracks"]["effect"].append(effect_track)
        
        # 添加效果到轨道
        effect_track["segments"].append({
            "id": segment_id,
            "effect_id": effect_id,
            "start": start,
            "duration": duration
        })
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Added particle effect: {particle_type} to draft: {draft_folder}")
        
        return {
            "success": True,
            "effect_id": effect_id,
            "segment_id": segment_id,
            "particle_type": particle_type,
            "duration": duration
        }
        
    except Exception as e:
        logger.error(f"Error adding particle effect: {str(e)}")
        return {"success": False, "error": str(e)}

def remove_effect(draft_folder: str, effect_id: str) -> Dict[str, Any]:
    """
    从草稿中移除效果
    
    Args:
        draft_folder: 草稿文件夹路径
        effect_id: 效果ID
        
    Returns:
        操作结果字典
    """
    try:
        draft_file = os.path.join(draft_folder, "draft.json")
        if not os.path.exists(draft_file):
            return {"success": False, "error": "Draft file not found"}
            
        with open(draft_file, 'r', encoding='utf-8') as f:
            draft_data = json.load(f)
        
        # 移除对应的效果
        draft_data["materials"]["effects"] = [
            effect for effect in draft_data["materials"]["effects"]
            if effect["id"] != effect_id
        ]
        
        # 移除对应的效果片段
        for track in draft_data["tracks"]["effect"]:
            track["segments"] = [
                segment for segment in track["segments"]
                if segment["effect_id"] != effect_id
            ]
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        return {"success": True, "message": f"Removed effect: {effect_id}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_effect(
    draft_folder: str,
    effect_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    更新效果参数
    
    Args:
        draft_folder: 草稿文件夹路径
        effect_id: 效果ID
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
        
        # 查找并更新效果
        updated = False
        for effect in draft_data["materials"]["effects"]:
            if effect["id"] == effect_id:
                # 更新强度
                if "intensity" in kwargs:
                    effect["intensity"] = kwargs["intensity"]
                
                # 更新时长
                if "duration" in kwargs:
                    effect["duration"] = kwargs["duration"]
                
                # 更新颜色
                if "color" in kwargs:
                    effect["color"] = kwargs["color"]
                
                # 更新参数
                if "parameters" in kwargs:
                    effect["parameters"].update(kwargs["parameters"])
                
                updated = True
                break
        
        if not updated:
            return {"success": False, "error": "Effect not found"}
        
        # 保存草稿
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
        return {"success": True, "message": f"Updated effect: {effect_id}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def apply_preset_effects(
    draft_folder: str,
    preset_name: str,
    target_segment_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    应用预设效果组合
    
    Args:
        draft_folder: 草稿文件夹路径
        preset_name: 预设名称
        target_segment_id: 目标片段ID
        
    Returns:
        操作结果字典
    """
    try:
        presets = {
            "vintage": [
                {"type": "filter", "name": "vintage", "intensity": 0.7},
                {"type": "adjustment", "name": "saturation", "value": 0.8},
                {"type": "adjustment", "name": "contrast", "value": 1.2}
            ],
            "cinematic": [
                {"type": "filter", "name": "black_white", "intensity": 0.3},
                {"type": "adjustment", "name": "contrast", "value": 1.3},
                {"type": "adjustment", "name": "brightness", "value": 0.9}
            ],
            "bright": [
                {"type": "adjustment", "name": "brightness", "value": 1.2},
                {"type": "adjustment", "name": "saturation", "value": 1.1},
                {"type": "adjustment", "name": "contrast", "value": 1.1}
            ],
            "dramatic": [
                {"type": "filter", "name": "cold", "intensity": 0.5},
                {"type": "adjustment", "name": "contrast", "value": 1.4},
                {"type": "adjustment", "name": "saturation", "value": 0.9}
            ]
        }
        
        if preset_name not in presets:
            return {"success": False, "error": f"Preset not found: {preset_name}"}
        
        results = []
        for effect_config in presets[preset_name]:
            if effect_config["type"] == "filter":
                result = add_filter(
                    draft_folder=draft_folder,
                    filter_type=effect_config["name"],
                    intensity=effect_config["intensity"],
                    target_segment_id=target_segment_id
                )
            elif effect_config["type"] == "adjustment":
                result = add_adjustment(
                    draft_folder=draft_folder,
                    adjustment_type=effect_config["name"],
                    value=effect_config["value"],
                    target_segment_id=target_segment_id
                )
            results.append(result)
        
        success_count = sum(1 for r in results if r["success"])
        return {
            "success": True,
            "message": f"Applied preset '{preset_name}' with {success_count} effects",
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
        
        # 测试添加转场
        result = add_transition(
            draft_folder=draft_folder,
            transition_type="fade",
            duration=0.5
        )
        
        print("Test result:", result)