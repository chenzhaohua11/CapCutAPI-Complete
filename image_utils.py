#!/usr/bin/env python3
"""
Image Processing Utilities for CapCut API

提供图片处理相关的实用工具函数，包括图片格式转换、尺寸调整、滤镜效果、文字添加等
"""

import os
import json
import numpy as np
from typing import Optional, Dict, Any, List, Tuple, Union
import logging
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import cv2
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

class ImageProcessor:
    """图片处理工具类"""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif']
        self.common_resolutions = {
            'square': (1080, 1080),
            'portrait': (1080, 1920),
            'landscape': (1920, 1080),
            'story': (1080, 1920),
            'reel': (1080, 1920),
            'thumbnail': (320, 180),
            'profile': (400, 400),
            'cover': (1280, 720)
        }
    
    def get_image_info(self, image_file: str) -> Dict[str, Any]:
        """
        获取图片文件信息
        
        Args:
            image_file: 图片文件路径
            
        Returns:
            图片信息字典
        """
        try:
            if not os.path.exists(image_file):
                return {"success": False, "error": f"Image file not found: {image_file}"}
                
            with Image.open(image_file) as img:
                info = {
                    "success": True,
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                    "format": img.format,
                    "size": os.path.getsize(image_file),
                    "has_alpha": img.mode in ('RGBA', 'LA', 'P'),
                    "colors": img.getcolors() if img.mode == 'P' else None
                }
                
                # 获取EXIF信息
                if hasattr(img, '_getexif') and img._getexif():
                    exif = dict(img._getexif())
                    info["exif"] = {
                        "orientation": exif.get(0x0112),
                        "make": exif.get(0x010F),
                        "model": exif.get(0x0110),
                        "software": exif.get(0x0131),
                        "datetime": exif.get(0x0132),
                        "width": exif.get(0xA002),
                        "height": exif.get(0xA003)
                    }
                
                return info
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def convert_format(
        self,
        input_file: str,
        output_file: str,
        format: str = 'PNG',
        quality: int = 95,
        **kwargs
    ) -> Dict[str, Any]:
        """
        转换图片格式
        
        Args:
            input_file: 输入图片文件路径
            output_file: 输出图片文件路径
            format: 目标格式（PNG, JPEG, WebP, etc.）
            quality: 质量（JPEG/WebP: 1-100）
            **kwargs: 其他保存参数
            
        Returns:
            转换结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            with Image.open(input_file) as img:
                # 处理EXIF旋转
                img = self._fix_orientation(img)
                
                # 保存为新格式
                save_kwargs = {'format': format.upper()}
                
                if format.upper() in ['JPEG', 'JPG']:
                    save_kwargs.update({
                        'quality': quality,
                        'optimize': True,
                        'progressive': True
                    })
                elif format.upper() == 'WEBP':
                    save_kwargs.update({
                        'quality': quality,
                        'method': 6
                    })
                elif format.upper() == 'PNG':
                    save_kwargs.update({
                        'optimize': True,
                        'compress_level': 9
                    })
                
                save_kwargs.update(kwargs)
                img.save(output_file, **save_kwargs)
                
                return {
                    "success": True,
                    "output_file": output_file,
                    "format": format.upper(),
                    "quality": quality
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def resize_image(
        self,
        input_file: str,
        output_file: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        keep_aspect: bool = True,
        resample: str = 'LANCZOS',
        background_color: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        调整图片尺寸
        
        Args:
            input_file: 输入图片文件路径
            output_file: 输出图片文件路径
            width: 目标宽度
            height: 目标高度
            keep_aspect: 是否保持宽高比
            resample: 重采样方法
            background_color: 背景颜色（用于填充）
            
        Returns:
            调整结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            with Image.open(input_file) as img:
                img = self._fix_orientation(img)
                
                original_width, original_height = img.size
                
                if width is None and height is None:
                    return {"success": False, "error": "Either width or height must be specified"}
                
                if keep_aspect:
                    if width is None:
                        width = int(original_width * (height / original_height))
                    elif height is None:
                        height = int(original_height * (width / original_width))
                    else:
                        # 计算保持宽高比的尺寸
                        ratio = min(width / original_width, height / original_height)
                        new_width = int(original_width * ratio)
                        new_height = int(original_height * ratio)
                        
                        # 如果需要填充背景
                        if background_color:
                            new_img = Image.new('RGB', (width, height), background_color)
                            paste_x = (width - new_width) // 2
                            paste_y = (height - new_height) // 2
                            img = img.resize((new_width, new_height), getattr(Image, resample))
                            new_img.paste(img, (paste_x, paste_y))
                            img = new_img
                        else:
                            img = img.resize((new_width, new_height), getattr(Image, resample))
                else:
                    img = img.resize((width, height), getattr(Image, resample))
                
                img.save(output_file)
                
                return {
                    "success": True,
                    "output_file": output_file,
                    "original_size": (original_width, original_height),
                    "new_size": img.size,
                    "keep_aspect": keep_aspect
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def crop_image(
        self,
        input_file: str,
        output_file: str,
        left: int,
        top: int,
        right: int,
        bottom: int
    ) -> Dict[str, Any]:
        """
        裁剪图片
        
        Args:
            input_file: 输入图片文件路径
            output_file: 输出图片文件路径
            left: 左边界
            top: 上边界
            right: 右边界
            bottom: 下边界
            
        Returns:
            裁剪结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            with Image.open(input_file) as img:
                img = self._fix_orientation(img)
                
                # 确保裁剪区域在图片范围内
                width, height = img.size
                left = max(0, left)
                top = max(0, top)
                right = min(width, right)
                bottom = min(height, bottom)
                
                if left >= right or top >= bottom:
                    return {"success": False, "error": "Invalid crop dimensions"}
                
                cropped = img.crop((left, top, right, bottom))
                cropped.save(output_file)
                
                return {
                    "success": True,
                    "output_file": output_file,
                    "crop_box": (left, top, right, bottom),
                    "new_size": cropped.size
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def rotate_image(
        self,
        input_file: str,
        output_file: str,
        angle: float,
        expand: bool = True,
        fillcolor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        旋转图片
        
        Args:
            input_file: 输入图片文件路径
            output_file: 输出图片文件路径
            angle: 旋转角度（逆时针）
            expand: 是否扩展画布以适应旋转后的图片
            fillcolor: 填充颜色
            
        Returns:
            旋转结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            with Image.open(input_file) as img:
                img = self._fix_orientation(img)
                
                rotated = img.rotate(
                    angle,
                    expand=expand,
                    fillcolor=fillcolor or 'white'
                )
                rotated.save(output_file)
                
                return {
                    "success": True,
                    "output_file": output_file,
                    "angle": angle,
                    "expand": expand
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def apply_filter(
        self,
        input_file: str,
        output_file: str,
        filter_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        应用滤镜效果
        
        Args:
            input_file: 输入图片文件路径
            output_file: 输出图片文件路径
            filter_type: 滤镜类型
            **kwargs: 滤镜参数
            
        Returns:
            滤镜应用结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            with Image.open(input_file) as img:
                img = self._fix_orientation(img)
                
                if filter_type == 'blur':
                    radius = kwargs.get('radius', 2)
                    filtered = img.filter(ImageFilter.GaussianBlur(radius))
                    
                elif filter_type == 'sharpen':
                    filtered = img.filter(ImageFilter.UnsharpMask(**kwargs))
                    
                elif filter_type == 'edge_enhance':
                    filtered = img.filter(ImageFilter.EDGE_ENHANCE)
                    
                elif filter_type == 'emboss':
                    filtered = img.filter(ImageFilter.EMBOSS)
                    
                elif filter_type == 'contour':
                    filtered = img.filter(ImageFilter.CONTOUR)
                    
                elif filter_type == 'grayscale':
                    filtered = img.convert('L')
                    
                elif filter_type == 'sepia':
                    filtered = self._apply_sepia(img)
                    
                elif filter_type == 'vintage':
                    filtered = self._apply_vintage(img)
                    
                elif filter_type == 'brightness':
                    factor = kwargs.get('factor', 1.2)
                    enhancer = ImageEnhance.Brightness(img)
                    filtered = enhancer.enhance(factor)
                    
                elif filter_type == 'contrast':
                    factor = kwargs.get('factor', 1.2)
                    enhancer = ImageEnhance.Contrast(img)
                    filtered = enhancer.enhance(factor)
                    
                elif filter_type == 'saturation':
                    factor = kwargs.get('factor', 1.2)
                    enhancer = ImageEnhance.Color(img)
                    filtered = enhancer.enhance(factor)
                    
                else:
                    return {"success": False, "error": f"Unsupported filter type: {filter_type}"}
                
                filtered.save(output_file)
                
                return {
                    "success": True,
                    "output_file": output_file,
                    "filter_type": filter_type,
                    "parameters": kwargs
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_text(
        self,
        input_file: str,
        output_file: str,
        text: str,
        position: Tuple[int, int] = (10, 10),
        font_size: int = 20,
        font_color: str = 'white',
        font_path: Optional[str] = None,
        stroke_width: int = 0,
        stroke_color: str = 'black',
        background_color: Optional[str] = None,
        background_padding: int = 5
    ) -> Dict[str, Any]:
        """
        添加文字到图片
        
        Args:
            input_file: 输入图片文件路径
            output_file: 输出图片文件路径
            text: 文字内容
            position: 文字位置（x, y）
            font_size: 字体大小
            font_color: 字体颜色
            font_path: 字体文件路径
            stroke_width: 描边宽度
            stroke_color: 描边颜色
            background_color: 背景颜色
            background_padding: 背景内边距
            
        Returns:
            文字添加结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            with Image.open(input_file) as img:
                img = self._fix_orientation(img)
                
                # 转换为RGB模式（如果需要）
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                draw = ImageDraw.Draw(img)
                
                # 加载字体
                try:
                    if font_path and os.path.exists(font_path):
                        font = ImageFont.truetype(font_path, font_size)
                    else:
                        font = ImageFont.load_default()
                except:
                    font = ImageFont.load_default()
                
                # 计算文字尺寸
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # 计算背景区域
                if background_color:
                    bg_left = position[0] - background_padding
                    bg_top = position[1] - background_padding
                    bg_right = position[0] + text_width + background_padding
                    bg_bottom = position[1] + text_height + background_padding
                    
                    draw.rectangle(
                        [bg_left, bg_top, bg_right, bg_bottom],
                        fill=background_color
                    )
                
                # 添加文字描边
                if stroke_width > 0:
                    for dx in range(-stroke_width, stroke_width + 1):
                        for dy in range(-stroke_width, stroke_width + 1):
                            if dx != 0 or dy != 0:
                                draw.text(
                                    (position[0] + dx, position[1] + dy),
                                    text,
                                    font=font,
                                    fill=stroke_color
                                )
                
                # 添加文字
                draw.text(position, text, font=font, fill=font_color)
                
                img.save(output_file)
                
                return {
                    "success": True,
                    "output_file": output_file,
                    "text": text,
                    "position": position,
                    "font_size": font_size
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
        scale: float = 0.1,
        margin: int = 10
    ) -> Dict[str, Any]:
        """
        添加水印
        
        Args:
            input_file: 输入图片文件路径
            output_file: 输出图片文件路径
            watermark_file: 水印文件路径
            position: 水印位置（top-left, top-right, bottom-left, bottom-right, center）
            opacity: 透明度（0-1）
            scale: 缩放比例（相对于主图宽度）
            margin: 边距
            
        Returns:
            水印添加结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
            if not os.path.exists(watermark_file):
                return {"success": False, "error": f"Watermark file not found: {watermark_file}"}
                
            with Image.open(input_file) as base_img:
                base_img = self._fix_orientation(base_img)
                
                with Image.open(watermark_file) as watermark:
                    # 计算水印尺寸
                    base_width, base_height = base_img.size
                    watermark_width = int(base_width * scale)
                    
                    # 保持水印宽高比
                    aspect_ratio = watermark.height / watermark.width
                    watermark_height = int(watermark_width * aspect_ratio)
                    
                    watermark = watermark.resize(
                        (watermark_width, watermark_height),
                        Image.Resampling.LANCZOS
                    )
                    
                    # 处理透明度
                    if watermark.mode != 'RGBA':
                        watermark = watermark.convert('RGBA')
                    
                    # 调整透明度
                    alpha = watermark.split()[-1]
                    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
                    watermark.putalpha(alpha)
                    
                    # 计算位置
                    positions = {
                        'top-left': (margin, margin),
                        'top-right': (base_width - watermark_width - margin, margin),
                        'bottom-left': (margin, base_height - watermark_height - margin),
                        'bottom-right': (base_width - watermark_width - margin, base_height - watermark_height - margin),
                        'center': (
                            (base_width - watermark_width) // 2,
                            (base_height - watermark_height) // 2
                        )
                    }
                    
                    pos = positions.get(position, positions['bottom-right'])
                    
                    # 添加水印
                    base_img.paste(watermark, pos, watermark)
                    base_img.save(output_file)
                    
                    return {
                        "success": True,
                        "output_file": output_file,
                        "position": position,
                        "opacity": opacity,
                        "scale": scale
                    }
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_collage(
        self,
        input_files: List[str],
        output_file: str,
        layout: str = 'grid',
        cols: int = 2,
        spacing: int = 10,
        background_color: str = 'white',
        border_width: int = 0,
        border_color: str = 'black'
    ) -> Dict[str, Any]:
        """
        创建图片拼贴
        
        Args:
            input_files: 输入图片文件列表
            output_file: 输出图片文件路径
            layout: 布局类型（grid, horizontal, vertical）
            cols: 列数（grid布局）
            spacing: 间距
            background_color: 背景颜色
            border_width: 边框宽度
            border_color: 边框颜色
            
        Returns:
            拼贴创建结果字典
        """
        try:
            if len(input_files) == 0:
                return {"success": False, "error": "No input files provided"}
                
            images = []
            for file in input_files:
                if not os.path.exists(file):
                    return {"success": False, "error": f"Input file not found: {file}"}
                    
                with Image.open(file) as img:
                    img = self._fix_orientation(img)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    images.append(img)
            
            if layout == 'grid':
                return self._create_grid_collage(
                    images, output_file, cols, spacing, background_color, border_width, border_color
                )
            elif layout == 'horizontal':
                return self._create_horizontal_collage(
                    images, output_file, spacing, background_color, border_width, border_color
                )
            elif layout == 'vertical':
                return self._create_vertical_collage(
                    images, output_file, spacing, background_color, border_width, border_color
                )
            else:
                return {"success": False, "error": f"Unsupported layout: {layout}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_meme(
        self,
        input_file: str,
        output_file: str,
        top_text: str = "",
        bottom_text: str = "",
        font_size: int = 40,
        font_color: str = 'white',
        stroke_color: str = 'black',
        stroke_width: int = 2
    ) -> Dict[str, Any]:
        """
        创建表情包
        
        Args:
            input_file: 输入图片文件路径
            output_file: 输出图片文件路径
            top_text: 顶部文字
            bottom_text: 底部文字
            font_size: 字体大小
            font_color: 字体颜色
            stroke_color: 描边颜色
            stroke_width: 描边宽度
            
        Returns:
            表情包创建结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            with Image.open(input_file) as img:
                img = self._fix_orientation(img)
                
                # 添加顶部和底部边框用于文字
                width, height = img.size
                border_height = max(100, int(height * 0.15))
                
                new_height = height + 2 * border_height
                new_img = Image.new('RGB', (width, new_height), 'black')
                new_img.paste(img, (0, border_height))
                
                draw = ImageDraw.Draw(new_img)
                
                # 加载字体
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                # 添加顶部文字
                if top_text:
                    bbox = draw.textbbox((0, 0), top_text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    x = (width - text_width) // 2
                    y = (border_height - text_height) // 2
                    
                    # 添加描边
                    for dx in range(-stroke_width, stroke_width + 1):
                        for dy in range(-stroke_width, stroke_width + 1):
                            if dx != 0 or dy != 0:
                                draw.text((x + dx, y + dy), top_text, font=font, fill=stroke_color)
                    
                    draw.text((x, y), top_text, font=font, fill=font_color)
                
                # 添加底部文字
                if bottom_text:
                    bbox = draw.textbbox((0, 0), bottom_text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    x = (width - text_width) // 2
                    y = height + border_height + (border_height - text_height) // 2
                    
                    # 添加描边
                    for dx in range(-stroke_width, stroke_width + 1):
                        for dy in range(-stroke_width, stroke_width + 1):
                            if dx != 0 or dy != 0:
                                draw.text((x + dx, y + dy), bottom_text, font=font, fill=stroke_color)
                    
                    draw.text((x, y), bottom_text, font=font, fill=font_color)
                
                new_img.save(output_file)
                
                return {
                    "success": True,
                    "output_file": output_file,
                    "top_text": top_text,
                    "bottom_text": bottom_text
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def image_to_base64(self, image_file: str, format: str = 'PNG') -> Dict[str, Any]:
        """
        将图片转换为base64编码
        
        Args:
            image_file: 图片文件路径
            format: 输出格式
            
        Returns:
            base64编码结果字典
        """
        try:
            if not os.path.exists(image_file):
                return {"success": False, "error": f"Image file not found: {image_file}"}
                
            with Image.open(image_file) as img:
                img = self._fix_orientation(img)
                
                buffer = BytesIO()
                img.save(buffer, format=format)
                img_str = base64.b64encode(buffer.getvalue()).decode()
                
                return {
                    "success": True,
                    "base64": f"data:image/{format.lower()};base64,{img_str}",
                    "format": format
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def base64_to_image(self, base64_str: str, output_file: str) -> Dict[str, Any]:
        """
        将base64编码转换为图片
        
        Args:
            base64_str: base64编码字符串
            output_file: 输出图片文件路径
            
        Returns:
            转换结果字典
        """
        try:
            # 移除data URL前缀
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]
            
            image_data = base64.b64decode(base64_str)
            
            with open(output_file, 'wb') as f:
                f.write(image_data)
            
            return {
                "success": True,
                "output_file": output_file,
                "size": len(image_data)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _fix_orientation(self, img: Image.Image) -> Image.Image:
        """修正图片方向"""
        try:
            if hasattr(img, '_getexif') and img._getexif():
                exif = dict(img._getexif())
                orientation = exif.get(0x0112)
                
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
                        
        except (AttributeError, KeyError, IndexError):
            pass
        
        return img
    
    def _apply_sepia(self, img: Image.Image) -> Image.Image:
        """应用棕褐色滤镜"""
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 棕褐色转换矩阵
        sepia_filter = (
            0.393, 0.769, 0.189, 0,
            0.349, 0.686, 0.168, 0,
            0.272, 0.534, 0.131, 0
        )
        
        return img.convert('RGB', sepia_filter)
    
    def _apply_vintage(self, img: Image.Image) -> Image.Image:
        """应用复古滤镜"""
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 降低饱和度
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.7)
        
        # 增加对比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        # 添加暖色调
        r, g, b = img.split()
        r = r.point(lambda i: min(255, int(i * 1.1)))
        b = b.point(lambda i: max(0, int(i * 0.9)))
        
        return Image.merge('RGB', (r, g, b))
    
    def _create_grid_collage(
        self,
        images: List[Image.Image],
        output_file: str,
        cols: int,
        spacing: int,
        background_color: str,
        border_width: int,
        border_color: str
    ) -> Dict[str, Any]:
        """创建网格拼贴"""
        if len(images) == 0:
            return {"success": False, "error": "No images provided"}
        
        # 计算网格尺寸
        rows = (len(images) + cols - 1) // cols
        
        # 获取最大图片尺寸
        max_width = max(img.width for img in images)
        max_height = max(img.height for img in images)
        
        # 计算画布尺寸
        total_width = cols * max_width + (cols + 1) * spacing + cols * 2 * border_width
        total_height = rows * max_height + (rows + 1) * spacing + rows * 2 * border_width
        
        # 创建画布
        canvas = Image.new('RGB', (total_width, total_height), background_color)
        
        # 放置图片
        for idx, img in enumerate(images):
            row = idx // cols
            col = idx % cols
            
            x = spacing + col * (max_width + spacing + 2 * border_width)
            y = spacing + row * (max_height + spacing + 2 * border_width)
            
            # 添加边框
            if border_width > 0:
                border_img = Image.new('RGB', 
                    (max_width + 2 * border_width, max_height + 2 * border_width), 
                    border_color)
                border_img.paste(img.resize((max_width, max_height)), (border_width, border_width))
                canvas.paste(border_img, (x, y))
            else:
                canvas.paste(img.resize((max_width, max_height)), (x, y))
        
        canvas.save(output_file)
        
        return {
            "success": True,
            "output_file": output_file,
            "layout": "grid",
            "images": len(images),
            "cols": cols,
            "rows": rows
        }
    
    def _create_horizontal_collage(
        self,
        images: List[Image.Image],
        output_file: str,
        spacing: int,
        background_color: str,
        border_width: int,
        border_color: str
    ) -> Dict[str, Any]:
        """创建水平拼贴"""
        if len(images) == 0:
            return {"success": False, "error": "No images provided"}
        
        # 计算画布尺寸
        max_height = max(img.height for img in images)
        total_width = sum(img.width for img in images) + (len(images) + 1) * spacing + len(images) * 2 * border_width
        
        canvas = Image.new('RGB', (total_width, max_height), background_color)
        
        x = spacing
        for img in images:
            y = (max_height - img.height) // 2
            
            if border_width > 0:
                border_img = Image.new('RGB', 
                    (img.width + 2 * border_width, max_height), 
                    border_color)
                border_img.paste(img, (border_width, y))
                canvas.paste(border_img, (x, 0))
            else:
                canvas.paste(img, (x, y))
            
            x += img.width + spacing + 2 * border_width
        
        canvas.save(output_file)
        
        return {
            "success": True,
            "output_file": output_file,
            "layout": "horizontal",
            "images": len(images)
        }
    
    def _create_vertical_collage(
        self,
        images: List[Image.Image],
        output_file: str,
        spacing: int,
        background_color: str,
        border_width: int,
        border_color: str
    ) -> Dict[str, Any]:
        """创建垂直拼贴"""
        if len(images) == 0:
            return {"success": False, "error": "No images provided"}
        
        # 计算画布尺寸
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images) + (len(images) + 1) * spacing + len(images) * 2 * border_width
        
        canvas = Image.new('RGB', (max_width, total_height), background_color)
        
        y = spacing
        for img in images:
            x = (max_width - img.width) // 2
            
            if border_width > 0:
                border_img = Image.new('RGB', 
                    (max_width, img.height + 2 * border_width), 
                    border_color)
                border_img.paste(img, (x, border_width))
                canvas.paste(border_img, (0, y))
            else:
                canvas.paste(img, (x, y))
            
            y += img.height + spacing + 2 * border_width
        
        canvas.save(output_file)
        
        return {
            "success": True,
            "output_file": output_file,
            "layout": "vertical",
            "images": len(images)
        }

# 快捷函数
def resize_image_file(input_file: str, output_file: str, width: int, height: int, **kwargs) -> Dict[str, Any]:
    """快捷图片尺寸调整函数"""
    processor = ImageProcessor()
    return processor.resize_image(input_file, output_file, width, height, **kwargs)

def convert_image_format(input_file: str, output_file: str, format: str, **kwargs) -> Dict[str, Any]:
    """快捷图片格式转换函数"""
    processor = ImageProcessor()
    return processor.convert_format(input_file, output_file, format, **kwargs)

def add_image_text(input_file: str, output_file: str, text: str, **kwargs) -> Dict[str, Any]:
    """快捷图片文字添加函数"""
    processor = ImageProcessor()
    return processor.add_text(input_file, output_file, text, **kwargs)

def create_image_meme(input_file: str, output_file: str, top_text: str, bottom_text: str, **kwargs) -> Dict[str, Any]:
    """快捷表情包创建函数"""
    processor = ImageProcessor()
    return processor.create_meme(input_file, output_file, top_text, bottom_text, **kwargs)

def image_to_base64_str(image_file: str, format: str = 'PNG') -> str:
    """快捷图片转base64函数"""
    processor = ImageProcessor()
    result = processor.image_to_base64(image_file, format)
    return result.get("base64", "") if result.get("success") else ""

if __name__ == "__main__":
    # 测试功能
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 这里应该有一个测试图片文件
        # 由于创建测试图片较复杂，这里仅展示结构
        
        processor = ImageProcessor()
        
        # 示例：获取图片信息
        # info = processor.get_image_info("test.jpg")
        # print("Image info:", info)
        
        print("Image processing utilities loaded successfully!")