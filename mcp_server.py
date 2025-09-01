#!/usr/bin/env python3
"""
CapCut API MCP Server (Complete Version)

完整版本的MCP服务器，集成所有CapCut API接口
"""

import sys
import os
import json
import traceback
import io
import contextlib
from typing import Any, Dict, List, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入CapCut API功能
try:
    from create_draft import get_or_create_draft
    from add_text_impl import add_text_impl
    from add_video_track import add_video_track
    from add_audio_track import add_audio_track
    from add_image_impl import add_image_impl
    from add_subtitle_impl import add_subtitle_impl
    from add_effect_impl import add_effect_impl
    from add_sticker_impl import add_sticker_impl
    from add_video_keyframe_impl import add_video_keyframe_impl
    from get_duration_impl import get_video_duration
    from save_draft_impl import save_draft_impl
    from pyJianYingDraft.text_segment import TextStyleRange
    CAPCUT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import CapCut modules: {e}", file=sys.stderr)
    CAPCUT_AVAILABLE = False

# 完整的工具定义
TOOLS = [
    {
        "name": "create_draft",
        "description": "创建新的CapCut草稿",
        "inputSchema": {
            "type": "object",
            "properties": {
                "width": {"type": "integer", "default": 1080, "description": "视频宽度"},
                "height": {"type": "integer", "default": 1920, "description": "视频高度"}
            }
        }
    },
    {
        "name": "add_video",
        "description": "添加视频到草稿，支持转场、蒙版、背景模糊等效果",
        "inputSchema": {
            "type": "object",
            "properties": {
                "video_url": {"type": "string", "description": "视频URL"},
                "draft_id": {"type": "string", "description": "草稿ID"},
                "start": {"type": "number", "default": 0, "description": "开始时间（秒）"},
                "end": {"type": "number", "description": "结束时间（秒）"},
                "target_start": {"type": "number", "default": 0, "description": "目标开始时间（秒）"},
                "width": {"type": "integer", "default": 1080, "description": "视频宽度"},
                "height": {"type": "integer", "default": 1920, "description": "视频高度"},
                "transform_x": {"type": "number", "default": 0, "description": "X轴位置"},
                "transform_y": {"type": "number", "default": 0, "description": "Y轴位置"},
                "scale_x": {"type": "number", "default": 1, "description": "X轴缩放"},
                "scale_y": {"type": "number", "default": 1, "description": "Y轴缩放"},
                "speed": {"type": "number", "default": 1.0, "description": "播放速度"},
                "track_name": {"type": "string", "default": "main", "description": "轨道名称"},
                "volume": {"type": "number", "default": 1.0, "description": "音量"},
                "transition": {"type": "string", "description": "转场类型"},
                "transition_duration": {"type": "number", "default": 0.5, "description": "转场时长"},
                "mask_type": {"type": "string", "description": "蒙版类型"},
                "background_blur": {"type": "integer", "description": "背景模糊级别(1-4)"}
            },
            "required": ["video_url"]
        }
    },
    {
        "name": "add_audio",
        "description": "添加音频到草稿，支持音效处理",
        "inputSchema": {
            "type": "object",
            "properties": {
                "audio_url": {"type": "string", "description": "音频URL"},
                "draft_id": {"type": "string", "description": "草稿ID"},
                "start": {"type": "number", "default": 0, "description": "开始时间（秒）"},
                "end": {"type": "number", "description": "结束时间（秒）"},
                "target_start": {"type": "number", "default": 0, "description": "目标开始时间（秒）"},
                "volume": {"type": "number", "default": 1.0, "description": "音量"},
                "speed": {"type": "number", "default": 1.0, "description": "播放速度"},
                "track_name": {"type": "string", "default": "audio_main", "description": "轨道名称"},
                "width": {"type": "integer", "default": 1080, "description": "视频宽度"},
                "height": {"type": "integer", "default": 1920, "description": "视频高度"}
            },
            "required": ["audio_url"]
        }
    },
    {
        "name": "add_image",
        "description": "添加图片到草稿，支持动画、转场、蒙版等效果",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_url": {"type": "string", "description": "图片URL"},
                "draft_id": {"type": "string", "description": "草稿ID"},
                "start": {"type": "number", "default": 0, "description": "开始时间（秒）"},
                "end": {"type": "number", "default": 3.0, "description": "结束时间（秒）"},
                "width": {"type": "integer", "default": 1080, "description": "视频宽度"},
                "height": {"type": "integer", "default": 1920, "description": "视频高度"},
                "transform_x": {"type": "number", "default": 0, "description": "X轴位置"},
                "transform_y": {"type": "number", "default": 0, "description": "Y轴位置"},
                "scale_x": {"type": "number", "default": 1, "description": "X轴缩放"},
                "scale_y": {"type": "number", "default": 1, "description": "Y轴缩放"},
                "track_name": {"type": "string", "default": "main", "description": "轨道名称"},
                "intro_animation": {"type": "string", "description": "入场动画"},
                "outro_animation": {"type": "string", "description": "出场动画"},
                "transition": {"type": "string", "description": "转场类型"},
                "mask_type": {"type": "string", "description": "蒙版类型"}
            },
            "required": ["image_url"]
        }
    },
    {
        "name": "add_text",
        "description": "添加文本到草稿，支持文本多样式、文字阴影和文字背景",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "文本内容"},
                "start": {"type": "number", "description": "开始时间（秒）"},
                "end": {"type": "number", "description": "结束时间（秒）"},
                "draft_id": {"type": "string", "description": "草稿ID"},
                "font_color": {"type": "string", "default": "#ffffff", "description": "字体颜色"},
                "font_size": {"type": "integer", "default": 24, "description": "字体大小"},
                "shadow_enabled": {"type": "boolean", "default": False, "description": "是否启用文字阴影"},
                "shadow_color": {"type": "string", "default": "#000000", "description": "阴影颜色"},
                "shadow_alpha": {"type": "number", "default": 0.8, "description": "阴影透明度"},
                "shadow_angle": {"type": "number", "default": 315.0, "description": "阴影角度"},
                "shadow_distance": {"type": "number", "default": 5.0, "description": "阴影距离"},
                "shadow_smoothing": {"type": "number", "default": 0.0, "description": "阴影平滑度"},
                "background_color": {"type": "string", "description": "背景颜色"},
                "background_alpha": {"type": "number", "default": 1.0, "description": "背景透明度"},
                "background_style": {"type": "integer", "default": 0, "description": "背景样式"},
                "background_round_radius": {"type": "number", "default": 0.0, "description": "背景圆角半径"},
                "text_styles": {"type": "array", "description": "文本多样式配置列表"}
            },
            "required": ["text", "start", "end"]
        }
    },
    {
        "name": "add_subtitle",
        "description": "添加字幕到草稿，支持SRT文件和样式设置",
        "inputSchema": {
            "type": "object",
            "properties": {
                "srt_path": {"type": "string", "description": "SRT字幕文件路径或URL"},
                "draft_id": {"type": "string", "description": "草稿ID"},
                "track_name": {"type": "string", "default": "subtitle", "description": "轨道名称"},
                "time_offset": {"type": "number", "default": 0, "description": "时间偏移（秒）"},
                "font": {"type": "string", "description": "字体"},
                "font_size": {"type": "number", "default": 8.0, "description": "字体大小"},
                "font_color": {"type": "string", "default": "#FFFFFF", "description": "字体颜色"},
                "bold": {"type": "boolean", "default": False, "description": "是否粗体"},
                "italic": {"type": "boolean", "default": False, "description": "是否斜体"},
                "underline": {"type": "boolean", "default": False, "description": "是否下划线"},
                "border_width": {"type": "number", "default": 0.0, "description": "边框宽度"},
                "border_color": {"type": "string", "default": "#000000", "description": "边框颜色"},
                "background_color": {"type": "string", "default": "#000000", "description": "背景颜色"},
                "background_alpha": {"type": "number", "default": 0.0, "description": "背景透明度"},
                "transform_x": {"type": "number", "default": 0.0, "description": "X轴位置"},
                "transform_y": {"type": "number", "default": -0.8, "description": "Y轴位置"},
                "width": {"type": "integer", "default": 1080, "description": "视频宽度"},
                "height": {"type": "integer", "default": 1920, "description": "视频高度"}
            },
            "required": ["srt_path"]
        }
    },
    {
        "name": "add_effect",
        "description": "添加特效到草稿",
        "inputSchema": {
            "type": "object",
            "properties": {
                "effect_type": {"type": "string", "description": "特效类型名称"},
                "draft_id": {"type": "string", "description": "草稿ID"},
                "start": {"type": "number", "default": 0, "description": "开始时间（秒）"},
                "end": {"type": "number", "default": 3.0, "description": "结束时间（秒）"},
                "track_name": {"type": "string", "default": "effect_01", "description": "轨道名称"},
                "params": {"type": "array", "description": "特效参数列表"},
                "width": {"type": "integer", "default": 1080, "description": "视频宽度"},
                "height": {"type": "integer", "default": 1920, "description": "视频高度"}
            },
            "required": ["effect_type"]
        }
    },
    {
        "name": "add_sticker",
        "description": "添加贴纸到草稿",
        "inputSchema": {
            "type": "object", 
            "properties": {
                "sticker_url": {"type": "string", "description": "贴纸URL"},
                "draft_id": {"type": "string", "description": "草稿ID"},
                "start": {"type": "number", "default": 0, "description": "开始时间（秒）"},
                "end": {"type": "number", "default": 3.0, "description": "结束时间（秒）"},
                "width": {"type": "integer", "default": 1080, "description": "视频宽度"},
                "height": {"type": "integer", "default": 1920, "description": "视频高度"},
                "transform_x": {"type": "number", "default": 0, "description": "X轴位置"},
                "transform_y": {"type": "number", "default": 0, "description": "Y轴位置"},
                "scale_x": {"type": "number", "default": 1, "description": "X轴缩放"},
                "scale_y": {"type": "number", "default": 1, "description": "Y轴缩放"},
                "rotation": {"type": "number", "default": 0, "description": "旋转角度"},
                "track_name": {"type": "string", "default": "sticker_main", "description": "轨道名称"}
            },
            "required": ["sticker_url"]
        }
    },
    {
        "name": "save_draft",
        "description": "保存草稿并生成最终视频",
        "inputSchema": {
            "type": "object",
            "properties": {
                "draft_id": {"type": "string", "description": "草稿ID"}
            },
            "required": ["draft_id"]
        }
    }
]

class CapCutMCPServer:
    def __init__(self):
        self.name = "capcut-api"
        self.version = "1.0.0"
        self.drafts = {}
        
    def get_tools(self):
        """返回可用的工具列表"""
        return TOOLS
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用指定的工具"""
        if not CAPCUT_AVAILABLE:
            return {
                "success": False,
                "error": "CapCut modules not available. Please check installation."
            }
            
        try:
            if name == "create_draft":
                return self._create_draft(arguments)
            elif name == "add_video":
                return self._add_video(arguments)
            elif name == "add_audio":
                return self._add_audio(arguments)
            elif name == "add_image":
                return self._add_image(arguments)
            elif name == "add_text":
                return self._add_text(arguments)
            elif name == "add_subtitle":
                return self._add_subtitle(arguments)
            elif name == "add_effect":
                return self._add_effect(arguments)
            elif name == "add_sticker":
                return self._add_sticker(arguments)
            elif name == "save_draft":
                return self._save_draft(arguments)
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {name}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def _create_draft(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """创建新的草稿"""
        width = args.get("width", 1080)
        height = args.get("height", 1920)
        
        draft_id = str(uuid.uuid4())
        draft_folder = get_or_create_draft(draft_id, width, height)
        
        self.drafts[draft_id] = {
            "folder": draft_folder,
            "width": width,
            "height": height
        }
        
        return {
            "success": True,
            "draft_id": draft_id,
            "draft_folder": draft_folder,
            "width": width,
            "height": height
        }
    
    def _add_video(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """添加视频到草稿"""
        draft_id = args.get("draft_id")
        if not draft_id or draft_id not in self.drafts:
            return {"success": False, "error": "Invalid draft_id"}
            
        draft_folder = self.drafts[draft_id]["folder"]
        
        result = add_video_track(
            draft_folder=draft_folder,
            video_url=args["video_url"],
            start=args.get("start", 0),
            end=args.get("end"),
            target_start=args.get("target_start", 0),
            width=args.get("width", 1080),
            height=args.get("height", 1920),
            transform_x=args.get("transform_x", 0),
            transform_y=args.get("transform_y", 0),
            scale_x=args.get("scale_x", 1),
            scale_y=args.get("scale_y", 1),
            speed=args.get("speed", 1.0),
            track_name=args.get("track_name", "main"),
            volume=args.get("volume", 1.0),
            transition=args.get("transition"),
            transition_duration=args.get("transition_duration", 0.5),
            mask_type=args.get("mask_type"),
            background_blur=args.get("background_blur")
        )
        
        return {"success": True, "result": result}
    
    def _add_audio(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """添加音频到草稿"""
        draft_id = args.get("draft_id")
        if not draft_id or draft_id not in self.drafts:
            return {"success": False, "error": "Invalid draft_id"}
            
        draft_folder = self.drafts[draft_id]["folder"]
        
        result = add_audio_track(
            draft_folder=draft_folder,
            audio_url=args["audio_url"],
            start=args.get("start", 0),
            end=args.get("end"),
            target_start=args.get("target_start", 0),
            volume=args.get("volume", 1.0),
            speed=args.get("speed", 1.0),
            track_name=args.get("track_name", "audio_main"),
            width=args.get("width", 1080),
            height=args.get("height", 1920)
        )
        
        return {"success": True, "result": result}
    
    def _add_image(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """添加图片到草稿"""
        draft_id = args.get("draft_id")
        if not draft_id or draft_id not in self.drafts:
            return {"success": False, "error": "Invalid draft_id"}
            
        draft_folder = self.drafts[draft_id]["folder"]
        
        result = add_image_impl(
            draft_folder=draft_folder,
            image_url=args["image_url"],
            start=args.get("start", 0),
            duration=args.get("end", 3.0) - args.get("start", 0),
            width=args.get("width", 1080),
            height=args.get("height", 1920),
            transform_x=args.get("transform_x", 0),
            transform_y=args.get("transform_y", 0),
            scale_x=args.get("scale_x", 1),
            scale_y=args.get("scale_y", 1),
            track_name=args.get("track_name", "main")
        )
        
        return {"success": True, "result": result}
    
    def _add_text(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """添加文本到草稿"""
        draft_id = args.get("draft_id")
        if not draft_id or draft_id not in self.drafts:
            return {"success": False, "error": "Invalid draft_id"}
            
        draft_folder = self.drafts[draft_id]["folder"]
        
        # 处理文本多样式
        text_styles = []
        if "text_styles" in args:
            for style in args["text_styles"]:
                text_styles.append(TextStyleRange(**style))
        
        result = add_text_impl(
            draft_folder=draft_folder,
            text=args["text"],
            start=args["start"],
            duration=args["end"] - args["start"],
            color=args.get("font_color", "#ffffff"),
            font_size=args.get("font_size", 24),
            track_name="text_main",
            width=args.get("width", 1080),
            height=args.get("height", 1920),
            text_styles=text_styles if text_styles else None,
            shadow_enabled=args.get("shadow_enabled", False),
            shadow_color=args.get("shadow_color", "#000000"),
            shadow_alpha=args.get("shadow_alpha", 0.8),
            shadow_angle=args.get("shadow_angle", 315.0),
            shadow_distance=args.get("shadow_distance", 5.0),
            shadow_smoothing=args.get("shadow_smoothing", 0.0),
            background_color=args.get("background_color"),
            background_alpha=args.get("background_alpha", 1.0),
            background_style=args.get("background_style", 0),
            background_round_radius=args.get("background_round_radius", 0.0)
        )
        
        return {"success": True, "result": result}
    
    def _add_subtitle(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """添加字幕到草稿"""
        draft_id = args.get("draft_id")
        if not draft_id or draft_id not in self.drafts:
            return {"success": False, "error": "Invalid draft_id"}
            
        draft_folder = self.drafts[draft_id]["folder"]
        
        result = add_subtitle_impl(
            draft_folder=draft_folder,
            srt_path=args["srt_path"],
            track_name=args.get("track_name", "subtitle"),
            time_offset=args.get("time_offset", 0),
            font=args.get("font"),
            font_size=args.get("font_size", 8.0),
            font_color=args.get("font_color", "#FFFFFF"),
            bold=args.get("bold", False),
            italic=args.get("italic", False),
            underline=args.get("underline", False),
            border_width=args.get("border_width", 0.0),
            border_color=args.get("border_color", "#000000"),
            background_color=args.get("background_color", "#000000"),
            background_alpha=args.get("background_alpha", 0.0),
            transform_x=args.get("transform_x", 0.0),
            transform_y=args.get("transform_y", -0.8),
            width=args.get("width", 1080),
            height=args.get("height", 1920)
        )
        
        return {"success": True, "result": result}
    
    def _add_effect(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """添加特效到草稿"""
        draft_id = args.get("draft_id")
        if not draft_id or draft_id not in self.drafts:
            return {"success": False, "error": "Invalid draft_id"}
            
        draft_folder = self.drafts[draft_id]["folder"]
        
        result = add_effect_impl(
            draft_folder=draft_folder,
            effect_type=args["effect_type"],
            start=args.get("start", 0),
            duration=args.get("end", 3.0) - args.get("start", 0),
            track_name=args.get("track_name", "effect_01"),
            params=args.get("params", []),
            width=args.get("width", 1080),
            height=args.get("height", 1920)
        )
        
        return {"success": True, "result": result}
    
    def _add_sticker(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """添加贴纸到草稿"""
        draft_id = args.get("draft_id")
        if not draft_id or draft_id not in self.drafts:
            return {"success": False, "error": "Invalid draft_id"}
            
        draft_folder = self.drafts[draft_id]["folder"]
        
        result = add_sticker_impl(
            draft_folder=draft_folder,
            sticker_url=args["sticker_url"],
            start=args.get("start", 0),
            duration=args.get("end", 3.0) - args.get("start", 0),
            width=args.get("width", 1080),
            height=args.get("height", 1920),
            transform_x=args.get("transform_x", 0),
            transform_y=args.get("transform_y", 0),
            scale_x=args.get("scale_x", 1),
            scale_y=args.get("scale_y", 1),
            rotation=args.get("rotation", 0),
            track_name=args.get("track_name", "sticker_main")
        )
        
        return {"success": True, "result": result}
    
    def _save_draft(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """保存草稿"""
        draft_id = args.get("draft_id")
        if not draft_id or draft_id not in self.drafts:
            return {"success": False, "error": "Invalid draft_id"}
            
        draft_folder = self.drafts[draft_id]["folder"]
        
        result = save_draft_impl(draft_folder=draft_folder, draft_id=draft_id)
        
        return {"success": True, "result": result}

# 主函数
if __name__ == "__main__":
    import asyncio
    import mcp.types as types
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio

    server = CapCutMCPServer()

    @mcp.server.stdio.server()
    async def handle_call_tool(
        name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> List[types.TextContent]:
        """处理工具调用"""
        if name == "create_draft":
            result = server.call_tool("create_draft", arguments or {})
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        elif name == "add_video":
            result = server.call_tool("add_video", arguments or {})
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        elif name == "add_audio":
            result = server.call_tool("add_audio", arguments or {})
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        elif name == "add_image":
            result = server.call_tool("add_image", arguments or {})
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        elif name == "add_text":
            result = server.call_tool("add_text", arguments or {})
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        elif name == "add_subtitle":
            result = server.call_tool("add_subtitle", arguments or {})
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        elif name == "add_effect":
            result = server.call_tool("add_effect", arguments or {})
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        elif name == "add_sticker":
            result = server.call_tool("add_sticker", arguments or {})
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        elif name == "save_draft":
            result = server.call_tool("save_draft", arguments or {})
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        else:
            return [types.TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    @mcp.server.stdio.server()
    async def handle_list_tools() -> List[types.Tool]:
        """列出可用工具"""
        tools = server.get_tools()
        return [types.Tool(**tool) for tool in tools]

    # 运行服务器
    asyncio.run(mcp.server.stdio.run(
        handle_call_tool,
        handle_list_tools,
        InitializationOptions(
            server_name="capcut-api",
            server_version="1.0.0",
        ),
    ))