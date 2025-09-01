#!/usr/bin/env python3
"""
Video Processing Utilities for CapCut API

提供视频处理相关的实用工具函数，包括视频格式转换、分辨率调整、帧率转换、视频剪辑等
"""

import os
import json
import cv2
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
import logging
from pathlib import Path
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont
import ffmpeg

logger = logging.getLogger(__name__)

class VideoProcessor:
    """视频处理工具类"""
    
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']
        self.common_resolutions = {
            '720p': (1280, 720),
            '1080p': (1920, 1080),
            '4K': (3840, 2160),
            '8K': (7680, 4320),
            'square': (1080, 1080),
            'vertical': (1080, 1920)
        }
        self.common_fps = [24, 25, 30, 50, 60]
    
    def get_video_info(self, video_file: str) -> Dict[str, Any]:
        """
        获取视频文件信息
        
        Args:
            video_file: 视频文件路径
            
        Returns:
            视频信息字典
        """
        try:
            if not os.path.exists(video_file):
                return {"success": False, "error": f"Video file not found: {video_file}"}
                
            # 使用ffprobe获取视频信息
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
                
            info = json.loads(result.stdout)
            
            # 提取视频流信息
            video_stream = None
            audio_stream = None
            
            for stream in info.get('streams', []):
                if stream['codec_type'] == 'video':
                    video_stream = stream
                elif stream['codec_type'] == 'audio':
                    audio_stream = stream
            
            if not video_stream:
                return {"success": False, "error": "No video stream found"}
            
            # 获取基本信息
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            duration = float(info['format']['duration'])
            fps = eval(video_stream.get('r_frame_rate', '0/1'))
            
            video_info = {
                "success": True,
                "duration": duration,
                "width": width,
                "height": height,
                "fps": fps,
                "format": info['format']['format_name'],
                "codec": video_stream['codec_name'],
                "size": int(info['format']['size']),
                "bitrate": int(info['format'].get('bit_rate', 0)),
                "has_audio": audio_stream is not None
            }
            
            if audio_stream:
                video_info.update({
                    "audio_codec": audio_stream['codec_name'],
                    "audio_sample_rate": int(audio_stream.get('sample_rate', 0)),
                    "audio_channels": int(audio_stream.get('channels', 0))
                })
            
            return video_info
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def convert_video_format(
        self,
        input_file: str,
        output_file: str,
        target_format: str = 'mp4',
        codec: str = 'libx264',
        quality: str = '23',
        preset: str = 'medium'
    ) -> Dict[str, Any]:
        """
        转换视频格式
        
        Args:
            input_file: 输入视频文件路径
            output_file: 输出视频文件路径
            target_format: 目标格式
            codec: 视频编码器
            quality: 质量参数（CRF值，越小质量越好）
            preset: 编码预设
            
        Returns:
            转换结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            cmd = [
                'ffmpeg', '-i', input_file,
                '-c:v', codec,
                '-crf', str(quality),
                '-preset', preset,
                '-c:a', 'aac',
                '-b:a', '128k',
                '-y',
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
                
            return {
                "success": True,
                "output_file": output_file,
                "format": target_format,
                "codec": codec,
                "quality": quality,
                "preset": preset
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def resize_video(
        self,
        input_file: str,
        output_file: str,
        width: int,
        height: int,
        keep_aspect: bool = True,
        interpolation: str = 'lanczos'
    ) -> Dict[str, Any]:
        """
        调整视频分辨率
        
        Args:
            input_file: 输入视频文件路径
            output_file: 输出视频文件路径
            width: 目标宽度
            height: 目标高度
            keep_aspect: 是否保持宽高比
            interpolation: 插值方法
            
        Returns:
            调整结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            # 获取原始视频信息
            info = self.get_video_info(input_file)
            if not info["success"]:
                return info
            
            original_width = info["width"]
            original_height = info["height"]
            
            if keep_aspect:
                # 计算保持宽高比的尺寸
                aspect_ratio = original_width / original_height
                if width / height > aspect_ratio:
                    width = int(height * aspect_ratio)
                else:
                    height = int(width / aspect_ratio)
            
            # 使用ffmpeg调整分辨率
            cmd = [
                'ffmpeg', '-i', input_file,
                '-vf', f'scale={width}:{height}:flags={interpolation}',
                '-c:a', 'copy',
                '-y',
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
                
            return {
                "success": True,
                "output_file": output_file,
                "width": width,
                "height": height,
                "original_width": original_width,
                "original_height": original_height
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def change_fps(
        self,
        input_file: str,
        output_file: str,
        target_fps: int,
        method: str = 'fps'
    ) -> Dict[str, Any]:
        """
        改变视频帧率
        
        Args:
            input_file: 输入视频文件路径
            output_file: 输出视频文件路径
            target_fps: 目标帧率
            method: 转换方法（fps或minterpolate）
            
        Returns:
            转换结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            if method == 'fps':
                # 简单帧率转换
                cmd = [
                    'ffmpeg', '-i', input_file,
                    '-r', str(target_fps),
                    '-c:v', 'libx264',
                    '-c:a', 'copy',
                    '-y',
                    output_file
                ]
            elif method == 'minterpolate':
                # 使用插值进行平滑转换
                cmd = [
                    'ffmpeg', '-i', input_file,
                    '-vf', f'minterpolate=fps={target_fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1',
                    '-c:v', 'libx264',
                    '-c:a', 'copy',
                    '-y',
                    output_file
                ]
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
                
            return {
                "success": True,
                "output_file": output_file,
                "target_fps": target_fps,
                "method": method
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def trim_video(
        self,
        input_file: str,
        output_file: str,
        start_time: float,
        duration: float,
        accurate: bool = True
    ) -> Dict[str, Any]:
        """
        裁剪视频片段
        
        Args:
            input_file: 输入视频文件路径
            output_file: 输出视频文件路径
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            accurate: 是否精确裁剪
            
        Returns:
            裁剪结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            if accurate:
                # 精确裁剪，重新编码
                cmd = [
                    'ffmpeg', '-ss', str(start_time), '-i', input_file,
                    '-t', str(duration),
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-avoid_negative_ts', 'make_zero',
                    '-y',
                    output_file
                ]
            else:
                # 快速裁剪，不重新编码
                cmd = [
                    'ffmpeg', '-ss', str(start_time), '-i', input_file,
                    '-t', str(duration),
                    '-c', 'copy',
                    '-avoid_negative_ts', 'make_zero',
                    '-y',
                    output_file
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
                
            return {
                "success": True,
                "output_file": output_file,
                "start_time": start_time,
                "duration": duration,
                "accurate": accurate
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def merge_videos(
        self,
        input_files: List[str],
        output_file: str,
        transition: Optional[str] = None,
        transition_duration: float = 1.0
    ) -> Dict[str, Any]:
        """
        合并多个视频
        
        Args:
            input_files: 输入视频文件列表
            output_file: 输出视频文件路径
            transition: 转场效果（fade, dissolve等）
            transition_duration: 转场持续时间
            
        Returns:
            合并结果字典
        """
        try:
            for file in input_files:
                if not os.path.exists(file):
                    return {"success": False, "error": f"Input file not found: {file}"}
            
            if len(input_files) == 1:
                # 单个文件直接复制
                cmd = ['ffmpeg', '-i', input_files[0], '-c', 'copy', '-y', output_file]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    return {"success": False, "error": result.stderr}
                
                return {
                    "success": True,
                    "output_file": output_file,
                    "input_files": len(input_files),
                    "transition": None
                }
            
            # 创建临时文件列表
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for file in input_files:
                    f.write(f"file '{file}'\n")
                list_file = f.name
            
            try:
                if transition:
                    # 使用转场效果合并
                    # 这里简化处理，实际转场需要更复杂的处理
                    cmd = [
                        'ffmpeg', '-f', 'concat', '-safe', '0',
                        '-i', list_file,
                        '-c:v', 'libx264',
                        '-c:a', 'aac',
                        '-y',
                        output_file
                    ]
                else:
                    # 直接合并
                    cmd = [
                        'ffmpeg', '-f', 'concat', '-safe', '0',
                        '-i', list_file,
                        '-c', 'copy',
                        '-y',
                        output_file
                    ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    return {"success": False, "error": result.stderr}
                
                return {
                    "success": True,
                    "output_file": output_file,
                    "input_files": len(input_files),
                    "transition": transition
                }
                
            finally:
                os.unlink(list_file)
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def extract_frames(
        self,
        input_file: str,
        output_dir: str,
        fps: Optional[int] = None,
        quality: int = 2
    ) -> Dict[str, Any]:
        """
        提取视频帧为图片
        
        Args:
            input_file: 输入视频文件路径
            output_dir: 输出目录
            fps: 提取帧率（None表示提取所有帧）
            quality: 图片质量（1-31，越小质量越好）
            
        Returns:
            提取结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            os.makedirs(output_dir, exist_ok=True)
            
            # 构建输出路径格式
            output_pattern = os.path.join(output_dir, 'frame_%06d.jpg')
            
            cmd = [
                'ffmpeg', '-i', input_file
            ]
            
            if fps:
                cmd.extend(['-vf', f'fps={fps}'])
            
            cmd.extend([
                '-q:v', str(quality),
                '-y',
                output_pattern
            ])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            # 计算提取的帧数
            frame_files = [f for f in os.listdir(output_dir) if f.startswith('frame_') and f.endswith('.jpg')]
            frame_count = len(frame_files)
            
            return {
                "success": True,
                "output_dir": output_dir,
                "frame_count": frame_count,
                "fps": fps
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_watermark(
        self,
        input_file: str,
        output_file: str,
        watermark_file: str,
        position: str = 'bottom-right',
        opacity: float = 0.7,
        scale: float = 0.1
    ) -> Dict[str, Any]:
        """
        添加水印
        
        Args:
            input_file: 输入视频文件路径
            output_file: 输出视频文件路径
            watermark_file: 水印图片路径
            position: 水印位置（top-left, top-right, bottom-left, bottom-right）
            opacity: 透明度（0-1）
            scale: 缩放比例（相对于视频宽度）
            
        Returns:
            处理结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
            if not os.path.exists(watermark_file):
                return {"success": False, "error": f"Watermark file not found: {watermark_file}"}
            
            # 计算水印位置
            position_map = {
                'top-left': '10:10',
                'top-right': 'main_w-overlay_w-10:10',
                'bottom-left': '10:main_h-overlay_h-10',
                'bottom-right': 'main_w-overlay_w-10:main_h-overlay_h-10'
            }
            
            pos = position_map.get(position, position_map['bottom-right'])
            
            cmd = [
                'ffmpeg', '-i', input_file, '-i', watermark_file,
                '-filter_complex',
                f"[1:v]scale=iw*{scale}:-1[watermark];[0:v][watermark]overlay={pos}:format=auto,format=yuv420p",
                '-c:a', 'copy',
                '-y',
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            return {
                "success": True,
                "output_file": output_file,
                "position": position,
                "opacity": opacity,
                "scale": scale
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_text_overlay(
        self,
        input_file: str,
        output_file: str,
        text: str,
        position: str = 'bottom',
        font_size: int = 24,
        font_color: str = 'white',
        background_color: Optional[str] = None,
        duration: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        添加文字覆盖
        
        Args:
            input_file: 输入视频文件路径
            output_file: 输出视频文件路径
            text: 文字内容
            position: 文字位置（top, center, bottom）
            font_size: 字体大小
            font_color: 字体颜色
            background_color: 背景颜色（可选）
            duration: 显示时间段（开始，结束）
            
        Returns:
            处理结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
            
            # 获取视频信息
            info = self.get_video_info(input_file)
            if not info["success"]:
                return info
            
            # 计算文字位置
            if position == 'top':
                y_pos = 'h/10'
            elif position == 'center':
                y_pos = 'h/2-text_h/2'
            else:  # bottom
                y_pos = 'h-text_h-10'
            
            # 构建滤镜
            filter_parts = [f"drawtext=text='{text}'"]
            filter_parts.append(f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
            filter_parts.append(f"fontsize={font_size}")
            filter_parts.append(f"fontcolor={font_color}")
            filter_parts.append(f"x=(w-text_w)/2")
            filter_parts.append(f"y={y_pos}")
            
            if background_color:
                filter_parts.append(f"box=1:boxcolor={background_color}@0.5")
            
            if duration:
                filter_parts.append(f"enable='between(t,{duration[0]},{duration[1]})'")
            
            filter_str = ":".join(filter_parts)
            
            cmd = [
                'ffmpeg', '-i', input_file,
                '-vf', filter_str,
                '-c:v', 'libx264',
                '-c:a', 'copy',
                '-y',
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            return {
                "success": True,
                "output_file": output_file,
                "text": text,
                "position": position,
                "font_size": font_size
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_thumbnail(
        self,
        input_file: str,
        output_file: str,
        time: float = 1.0,
        width: int = 320,
        height: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        创建视频缩略图
        
        Args:
            input_file: 输入视频文件路径
            output_file: 输出缩略图文件路径
            time: 截取时间点（秒）
            width: 缩略图宽度
            height: 缩略图高度（可选）
            
        Returns:
            创建结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
            
            # 获取视频信息
            info = self.get_video_info(input_file)
            if not info["success"]:
                return info
            
            # 计算高度保持宽高比
            if height is None:
                aspect_ratio = info["width"] / info["height"]
                height = int(width / aspect_ratio)
            
            cmd = [
                'ffmpeg', '-i', input_file,
                '-ss', str(time),
                '-vframes', '1',
                '-vf', f'scale={width}:{height}',
                '-y',
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            return {
                "success": True,
                "output_file": output_file,
                "width": width,
                "height": height,
                "time": time
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def stabilize_video(
        self,
        input_file: str,
        output_file: str,
        smoothing: float = 10.0,
        crop: bool = True
    ) -> Dict[str, Any]:
        """
        视频防抖处理
        
        Args:
            input_file: 输入视频文件路径
            output_file: 输出视频文件路径
            smoothing: 平滑参数
            crop: 是否裁剪边缘
            
        Returns:
            处理结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
            
            # 使用vidstabdetect和vidstabtransform滤镜
            filter_chain = f"vidstabdetect=shakiness=10:accuracy=15:stepsize=6:mincontrast=0.3"
            
            if crop:
                filter_chain += ",vidstabtransform=smoothing={}:crop=black:zoom=0:optzoom=1".format(smoothing)
            else:
                filter_chain += ",vidstabtransform=smoothing={}:crop=keep:zoom=0:optzoom=1".format(smoothing)
            
            cmd = [
                'ffmpeg', '-i', input_file,
                '-vf', filter_chain,
                '-c:v', 'libx264',
                '-c:a', 'copy',
                '-y',
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            return {
                "success": True,
                "output_file": output_file,
                "smoothing": smoothing,
                "crop": crop
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_transition(
        self,
        input_file1: str,
        input_file2: str,
        output_file: str,
        transition_type: str = 'fade',
        duration: float = 1.0
    ) -> Dict[str, Any]:
        """
        添加视频转场效果
        
        Args:
            input_file1: 第一个视频文件路径
            input_file2: 第二个视频文件路径
            output_file: 输出视频文件路径
            transition_type: 转场类型（fade, dissolve, wipe等）
            duration: 转场持续时间
            
        Returns:
            处理结果字典
        """
        try:
            for file in [input_file1, input_file2]:
                if not os.path.exists(file):
                    return {"success": False, "error": f"Input file not found: {file}"}
            
            if transition_type == 'fade':
                # 淡入淡出转场
                filter_complex = (
                    f"[0:v][1:v]xfade=transition=fade:duration={duration}:offset=0[v];"
                    f"[0:a][1:a]acrossfade=duration={duration}[a]"
                )
            elif transition_type == 'dissolve':
                # 溶解转场
                filter_complex = (
                    f"[0:v][1:v]xfade=transition=dissolve:duration={duration}:offset=0[v];"
                    f"[0:a][1:a]acrossfade=duration={duration}[a]"
                )
            else:
                return {"success": False, "error": f"Unsupported transition type: {transition_type}"}
            
            cmd = [
                'ffmpeg', '-i', input_file1, '-i', input_file2,
                '-filter_complex', filter_complex,
                '-map', '[v]',
                '-map', '[a]',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-y',
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            return {
                "success": True,
                "output_file": output_file,
                "transition_type": transition_type,
                "duration": duration
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_gif(
        self,
        input_file: str,
        output_file: str,
        start_time: float = 0.0,
        duration: float = 3.0,
        fps: int = 10,
        width: int = 320,
        optimize: bool = True
    ) -> Dict[str, Any]:
        """
        创建GIF动画
        
        Args:
            input_file: 输入视频文件路径
            output_file: 输出GIF文件路径
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            fps: 帧率
            width: 宽度
            optimize: 是否优化GIF
            
        Returns:
            创建结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
            
            # 获取视频信息
            info = self.get_video_info(input_file)
            if not info["success"]:
                return info
            
            # 计算高度保持宽高比
            height = int(width * info["height"] / info["width"])
            
            # 创建调色板
            palette_file = output_file.replace('.gif', '_palette.png')
            
            cmd1 = [
                'ffmpeg', '-ss', str(start_time), '-t', str(duration),
                '-i', input_file,
                '-vf', f'fps={fps},scale={width}:{height}:flags=lanczos,palettegen',
                '-y',
                palette_file
            ]
            
            result1 = subprocess.run(cmd1, capture_output=True, text=True)
            
            if result1.returncode != 0:
                return {"success": False, "error": result1.stderr}
            
            # 创建GIF
            cmd2 = [
                'ffmpeg', '-ss', str(start_time), '-t', str(duration),
                '-i', input_file, '-i', palette_file,
                '-filter_complex',
                f'fps={fps},scale={width}:{height}:flags=lanczos[x];[x][1:v]paletteuse',
                '-y',
                output_file
            ]
            
            result2 = subprocess.run(cmd2, capture_output=True, text=True)
            
            # 清理调色板文件
            if os.path.exists(palette_file):
                os.unlink(palette_file)
            
            if result2.returncode != 0:
                return {"success": False, "error": result2.stderr}
            
            return {
                "success": True,
                "output_file": output_file,
                "width": width,
                "height": height,
                "fps": fps,
                "duration": duration
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def compress_video(
        self,
        input_file: str,
        output_file: str,
        target_size: Optional[int] = None,
        quality: int = 23,
        max_bitrate: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        压缩视频文件
        
        Args:
            input_file: 输入视频文件路径
            output_file: 输出视频文件路径
            target_size: 目标文件大小（MB）
            quality: 质量参数
            max_bitrate: 最大比特率
            
        Returns:
            压缩结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
            
            # 获取视频信息
            info = self.get_video_info(input_file)
            if not info["success"]:
                return info
            
            if target_size:
                # 计算目标比特率
                duration = info["duration"]
                target_bitrate = int((target_size * 8192) / duration)  # kbps
                max_bitrate = f"{target_bitrate}k"
            
            cmd = [
                'ffmpeg', '-i', input_file,
                '-c:v', 'libx264',
                '-crf', str(quality)
            ]
            
            if max_bitrate:
                cmd.extend(['-maxrate', max_bitrate, '-bufsize', f"{int(max_bitrate.replace('k', '')) * 2}k"])
            
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', '128k',
                '-y',
                output_file
            ])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            return {
                "success": True,
                "output_file": output_file,
                "compression_ratio": os.path.getsize(input_file) / os.path.getsize(output_file)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# 快捷函数
def convert_video(input_file: str, output_file: str, **kwargs) -> Dict[str, Any]:
    """快捷视频格式转换函数"""
    processor = VideoProcessor()
    return processor.convert_video_format(input_file, output_file, **kwargs)

def resize_video_file(input_file: str, output_file: str, width: int, height: int, **kwargs) -> Dict[str, Any]:
    """快捷视频尺寸调整函数"""
    processor = VideoProcessor()
    return processor.resize_video(input_file, output_file, width, height, **kwargs)

def trim_video_file(input_file: str, output_file: str, start: float, duration: float, **kwargs) -> Dict[str, Any]:
    """快捷视频裁剪函数"""
    processor = VideoProcessor()
    return processor.trim_video(input_file, output_file, start, duration, **kwargs)

def get_video_duration(video_file: str) -> float:
    """获取视频时长"""
    processor = VideoProcessor()
    info = processor.get_video_info(video_file)
    return info.get("duration", 0.0) if info.get("success") else 0.0

def create_video_thumbnail(video_file: str, output_file: str, **kwargs) -> Dict[str, Any]:
    """快捷创建缩略图函数"""
    processor = VideoProcessor()
    return processor.create_thumbnail(video_file, output_file, **kwargs)

if __name__ == "__main__":
    # 测试功能
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 这里应该有一个测试视频文件
        # 由于创建测试视频较复杂，这里仅展示结构
        
        processor = VideoProcessor()
        
        # 示例：获取视频信息
        # info = processor.get_video_info("test.mp4")
        # print("Video info:", info)
        
        print("Video processing utilities loaded successfully!")