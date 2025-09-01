#!/usr/bin/env python3
"""
Create Draft Utility for CapCut API

提供创建和管理CapCut草稿的功能
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

def get_or_create_draft(draft_id: str, width: int = 1080, height: int = 1920) -> str:
    """
    创建或获取草稿文件夹
    
    Args:
        draft_id: 草稿ID
        width: 视频宽度
        height: 视频高度
        
    Returns:
        草稿文件夹路径
    """
    # 获取用户主目录
    home_dir = Path.home()
    
    # 创建草稿目录
    drafts_dir = home_dir / "CapCutDrafts"
    drafts_dir.mkdir(exist_ok=True)
    
    # 创建具体草稿文件夹
    draft_folder = drafts_dir / draft_id
    draft_folder.mkdir(exist_ok=True)
    
    # 创建必要的子目录
    (draft_folder / "videos").mkdir(exist_ok=True)
    (draft_folder / "audios").mkdir(exist_ok=True)
    (draft_folder / "images").mkdir(exist_ok=True)
    (draft_folder / "texts").mkdir(exist_ok=True)
    (draft_folder / "effects").mkdir(exist_ok=True)
    (draft_folder / "stickers").mkdir(exist_ok=True)
    (draft_folder / "subtitles").mkdir(exist_ok=True)
    
    # 返回草稿文件夹路径
    return str(draft_folder)

def list_drafts() -> Dict[str, Any]:
    """
    列出所有草稿
    
    Returns:
        草稿列表信息
    """
    home_dir = Path.home()
    drafts_dir = home_dir / "CapCutDrafts"
    
    if not drafts_dir.exists():
        return {"drafts": [], "count": 0}
    
    drafts = []
    for draft_folder in drafts_dir.iterdir():
        if draft_folder.is_dir():
            draft_info = {
                "id": draft_folder.name,
                "path": str(draft_folder),
                "created": draft_folder.stat().st_ctime,
                "modified": draft_folder.stat().st_mtime,
                "size": sum(f.stat().st_size for f in draft_folder.rglob('*') if f.is_file())
            }
            drafts.append(draft_info)
    
    return {
        "drafts": sorted(drafts, key=lambda x: x["modified"], reverse=True),
        "count": len(drafts)
    }

def delete_draft(draft_id: str) -> Dict[str, Any]:
    """
    删除草稿
    
    Args:
        draft_id: 草稿ID
        
    Returns:
        删除结果
    """
    home_dir = Path.home()
    drafts_dir = home_dir / "CapCutDrafts"
    draft_folder = drafts_dir / draft_id
    
    if draft_folder.exists() and draft_folder.is_dir():
        try:
            shutil.rmtree(draft_folder)
            return {"success": True, "message": f"Draft {draft_id} deleted successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    else:
        return {"success": False, "error": f"Draft {draft_id} not found"}

def get_draft_info(draft_id: str) -> Dict[str, Any]:
    """
    获取草稿详细信息
    
    Args:
        draft_id: 草稿ID
        
    Returns:
        草稿详细信息
    """
    home_dir = Path.home()
    drafts_dir = home_dir / "CapCutDrafts"
    draft_folder = drafts_dir / draft_id
    
    if not draft_folder.exists():
        return {"success": False, "error": f"Draft {draft_id} not found"}
    
    # 统计各类型文件
    video_files = list((draft_folder / "videos").glob("*")) if (draft_folder / "videos").exists() else []
    audio_files = list((draft_folder / "audios").glob("*")) if (draft_folder / "audios").exists() else []
    image_files = list((draft_folder / "images").glob("*")) if (draft_folder / "images").exists() else []
    text_files = list((draft_folder / "texts").glob("*")) if (draft_folder / "texts").exists() else []
    effect_files = list((draft_folder / "effects").glob("*")) if (draft_folder / "effects").exists() else []
    sticker_files = list((draft_folder / "stickers").glob("*")) if (draft_folder / "stickers").exists() else []
    subtitle_files = list((draft_folder / "subtitles").glob("*")) if (draft_folder / "subtitles").exists() else []
    
    return {
        "success": True,
        "draft_id": draft_id,
        "path": str(draft_folder),
        "files": {
            "videos": len(video_files),
            "audios": len(audio_files),
            "images": len(image_files),
            "texts": len(text_files),
            "effects": len(effect_files),
            "stickers": len(sticker_files),
            "subtitles": len(subtitle_files)
        },
        "total_files": len(video_files) + len(audio_files) + len(image_files) + 
                      len(text_files) + len(effect_files) + len(sticker_files) + len(subtitle_files),
        "created": draft_folder.stat().st_ctime,
        "modified": draft_folder.stat().st_mtime,
        "size": sum(f.stat().st_size for f in draft_folder.rglob('*') if f.is_file())
    }

if __name__ == "__main__":
    # 测试功能
    print("=== CapCut Draft Manager ===")
    
    # 创建测试草稿
    test_draft_id = "test_draft_001"
    draft_path = get_or_create_draft(test_draft_id, 1080, 1920)
    print(f"Created draft: {test_draft_id}")
    print(f"Draft path: {draft_path}")
    
    # 列出所有草稿
    drafts = list_drafts()
    print(f"\nTotal drafts: {drafts['count']}")
    
    # 获取草稿信息
    info = get_draft_info(test_draft_id)
    if info["success"]:
        print(f"\nDraft info: {info}")
    
    # 清理测试
    # delete_draft(test_draft_id)
    # print("Test draft cleaned up")