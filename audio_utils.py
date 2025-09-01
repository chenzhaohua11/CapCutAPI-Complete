#!/usr/bin/env python3
"""
Audio Processing Utilities for CapCut API

提供音频处理相关的实用工具函数，包括音频格式转换、音量调整、音频提取等
"""

import os
import json
import numpy as np
import librosa
import soundfile as sf
from typing import Optional, Dict, Any, List, Tuple
import logging
from pathlib import Path
import subprocess
import tempfile

logger = logging.getLogger(__name__)

class AudioProcessor:
    """音频处理工具类"""
    
    def __init__(self):
        self.supported_formats = ['.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg']
        self.sample_rates = [8000, 16000, 22050, 44100, 48000]
        
    def convert_audio_format(
        self,
        input_file: str,
        output_file: str,
        target_format: str = 'mp3',
        sample_rate: int = 44100,
        bitrate: str = '192k',
        channels: int = 2
    ) -> Dict[str, Any]:
        """
        转换音频格式
        
        Args:
            input_file: 输入音频文件路径
            output_file: 输出音频文件路径
            target_format: 目标格式 (mp3, wav, flac, aac, ogg)
            sample_rate: 采样率
            bitrate: 比特率
            channels: 声道数
            
        Returns:
            转换结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            # 使用ffmpeg进行格式转换
            cmd = [
                'ffmpeg', '-i', input_file,
                '-ar', str(sample_rate),
                '-ac', str(channels),
                '-b:a', bitrate,
                '-y',  # 覆盖输出文件
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
                
            return {
                "success": True,
                "output_file": output_file,
                "format": target_format,
                "sample_rate": sample_rate,
                "bitrate": bitrate
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def adjust_volume(
        self,
        input_file: str,
        output_file: str,
        volume_change: float,
        normalize: bool = False
    ) -> Dict[str, Any]:
        """
        调整音频音量
        
        Args:
            input_file: 输入音频文件路径
            output_file: 输出音频文件路径
            volume_change: 音量变化倍数 (>1 增加, <1 减少)
            normalize: 是否标准化音量
            
        Returns:
            调整结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            # 加载音频
            y, sr = librosa.load(input_file, sr=None)
            
            # 调整音量
            y_adjusted = y * volume_change
            
            # 标准化音量
            if normalize:
                y_adjusted = librosa.util.normalize(y_adjusted)
            
            # 保存调整后的音频
            sf.write(output_file, y_adjusted, sr)
            
            return {
                "success": True,
                "output_file": output_file,
                "volume_change": volume_change,
                "original_volume": float(np.max(np.abs(y))),
                "new_volume": float(np.max(np.abs(y_adjusted)))
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def extract_audio_from_video(
        self,
        video_file: str,
        output_file: str,
        audio_format: str = 'mp3',
        quality: str = '192k'
    ) -> Dict[str, Any]:
        """
        从视频中提取音频
        
        Args:
            video_file: 输入视频文件路径
            output_file: 输出音频文件路径
            audio_format: 音频格式
            quality: 音频质量
            
        Returns:
            提取结果字典
        """
        try:
            if not os.path.exists(video_file):
                return {"success": False, "error": f"Video file not found: {video_file}"}
                
            cmd = [
                'ffmpeg', '-i', video_file,
                '-vn',  # 禁用视频
                '-acodec', 'libmp3lame' if audio_format == 'mp3' else 'copy',
                '-b:a', quality,
                '-y',
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
                
            return {
                "success": True,
                "output_file": output_file,
                "format": audio_format,
                "quality": quality
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def trim_audio(
        self,
        input_file: str,
        output_file: str,
        start_time: float,
        duration: float
    ) -> Dict[str, Any]:
        """
        裁剪音频片段
        
        Args:
            input_file: 输入音频文件路径
            output_file: 输出音频文件路径
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            
        Returns:
            裁剪结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            cmd = [
                'ffmpeg', '-i', input_file,
                '-ss', str(start_time),
                '-t', str(duration),
                '-acodec', 'copy',
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
                "duration": duration
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def fade_in_out(
        self,
        input_file: str,
        output_file: str,
        fade_in: float = 0.0,
        fade_out: float = 0.0
    ) -> Dict[str, Any]:
        """
        添加淡入淡出效果
        
        Args:
            input_file: 输入音频文件路径
            output_file: 输出音频文件路径
            fade_in: 淡入时长（秒）
            fade_out: 淡出时长（秒）
            
        Returns:
            处理结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            # 获取音频时长
            y, sr = librosa.load(input_file, sr=None)
            duration = len(y) / sr
            
            # 构建ffmpeg命令
            filters = []
            if fade_in > 0:
                filters.append(f"afade=t=in:st=0:d={fade_in}")
            if fade_out > 0:
                filters.append(f"afade=t=out:st={duration-fade_out}:d={fade_out}")
            
            if not filters:
                return {"success": False, "error": "No fade effects specified"}
                
            filter_str = ",".join(filters)
            
            cmd = [
                'ffmpeg', '-i', input_file,
                '-af', filter_str,
                '-y',
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
                
            return {
                "success": True,
                "output_file": output_file,
                "fade_in": fade_in,
                "fade_out": fade_out,
                "duration": duration
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_background_music(
        self,
        main_audio: str,
        background_audio: str,
        output_file: str,
        background_volume: float = 0.3,
        loop_background: bool = True
    ) -> Dict[str, Any]:
        """
        添加背景音乐
        
        Args:
            main_audio: 主音频文件路径
            background_audio: 背景音乐文件路径
            output_file: 输出音频文件路径
            background_volume: 背景音乐音量
            loop_background: 是否循环背景音乐
            
        Returns:
            处理结果字典
        """
        try:
            if not os.path.exists(main_audio):
                return {"success": False, "error": f"Main audio file not found: {main_audio}"}
            if not os.path.exists(background_audio):
                return {"success": False, "error": f"Background audio file not found: {background_audio}"}
                
            # 获取主音频时长
            y_main, sr_main = librosa.load(main_audio, sr=None)
            main_duration = len(y_main) / sr_main
            
            # 处理背景音乐
            if loop_background:
                # 循环背景音乐以匹配主音频时长
                cmd = [
                    'ffmpeg', '-i', main_audio, '-i', background_audio,
                    '-filter_complex',
                    f"[1:a]volume={background_volume},apad=pad_dur={main_duration}[bg];[0:a][bg]amix=inputs=2:duration=first",
                    '-y',
                    output_file
                ]
            else:
                # 不循环，直接混合
                cmd = [
                    'ffmpeg', '-i', main_audio, '-i', background_audio,
                    '-filter_complex',
                    f"[1:a]volume={background_volume}[bg];[0:a][bg]amix=inputs=2:duration=first",
                    '-y',
                    output_file
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
                
            return {
                "success": True,
                "output_file": output_file,
                "background_volume": background_volume,
                "loop_background": loop_background
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def normalize_audio(
        self,
        input_file: str,
        output_file: str,
        target_lufs: float = -16.0
    ) -> Dict[str, Any]:
        """
        标准化音频音量
        
        Args:
            input_file: 输入音频文件路径
            output_file: 输出音频文件路径
            target_lufs: 目标LUFS值
            
        Returns:
            标准化结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            cmd = [
                'ffmpeg', '-i', input_file,
                '-af', f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
                '-y',
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
                
            return {
                "success": True,
                "output_file": output_file,
                "target_lufs": target_lufs
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_audio_info(self, audio_file: str) -> Dict[str, Any]:
        """
        获取音频文件信息
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            音频信息字典
        """
        try:
            if not os.path.exists(audio_file):
                return {"success": False, "error": f"Audio file not found: {audio_file}"}
                
            # 使用ffprobe获取音频信息
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                audio_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
                
            info = json.loads(result.stdout)
            
            # 提取音频流信息
            audio_stream = None
            for stream in info.get('streams', []):
                if stream['codec_type'] == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                return {"success": False, "error": "No audio stream found"}
            
            # 获取时长
            duration = float(info['format']['duration'])
            
            # 获取音频信息
            audio_info = {
                "success": True,
                "duration": duration,
                "sample_rate": int(audio_stream.get('sample_rate', 0)),
                "channels": int(audio_stream.get('channels', 0)),
                "bitrate": info['format'].get('bit_rate', 'unknown'),
                "format": info['format']['format_name'],
                "codec": audio_stream['codec_name'],
                "size": int(info['format']['size'])
            }
            
            return audio_info
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def detect_silence(
        self,
        audio_file: str,
        threshold: float = -30.0,
        min_duration: float = 0.5
    ) -> Dict[str, Any]:
        """
        检测音频中的静音段
        
        Args:
            audio_file: 音频文件路径
            threshold: 静音阈值（dB）
            min_duration: 最小静音时长（秒）
            
        Returns:
            静音段信息字典
        """
        try:
            if not os.path.exists(audio_file):
                return {"success": False, "error": f"Audio file not found: {audio_file}"}
                
            # 加载音频
            y, sr = librosa.load(audio_file, sr=None)
            
            # 计算短时能量
            frame_length = int(0.025 * sr)  # 25ms帧长
            hop_length = int(0.010 * sr)    # 10ms帧移
            
            # 计算RMS能量
            rms = librosa.feature.rms(
                y=y,
                frame_length=frame_length,
                hop_length=hop_length
            )[0]
            
            # 转换为dB
            rms_db = librosa.power_to_db(rms**2, ref=np.max)
            
            # 检测静音段
            silence_mask = rms_db < threshold
            
            # 找出静音段
            silence_segments = []
            current_start = None
            
            for i, is_silent in enumerate(silence_mask):
                if is_silent and current_start is None:
                    current_start = i * hop_length / sr
                elif not is_silent and current_start is not None:
                    end = i * hop_length / sr
                    if end - current_start >= min_duration:
                        silence_segments.append({
                            "start": current_start,
                            "end": end,
                            "duration": end - current_start
                        })
                    current_start = None
            
            # 处理结尾的静音
            if current_start is not None:
                end = len(y) / sr
                if end - current_start >= min_duration:
                    silence_segments.append({
                        "start": current_start,
                        "end": end,
                        "duration": end - current_start
                    })
            
            return {
                "success": True,
                "silence_segments": silence_segments,
                "total_silence_duration": sum(s["duration"] for s in silence_segments),
                "silence_ratio": sum(s["duration"] for s in silence_segments) / (len(y) / sr)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def remove_silence(
        self,
        input_file: str,
        output_file: str,
        threshold: float = -30.0,
        min_duration: float = 0.5,
        padding: float = 0.1
    ) -> Dict[str, Any]:
        """
        移除音频中的静音段
        
        Args:
            input_file: 输入音频文件路径
            output_file: 输出音频文件路径
            threshold: 静音阈值（dB）
            min_duration: 最小静音时长（秒）
            padding: 保留的静音边缘（秒）
            
        Returns:
            处理结果字典
        """
        try:
            # 检测静音段
            silence_info = self.detect_silence(input_file, threshold, min_duration)
            
            if not silence_info["success"]:
                return silence_info
            
            # 加载音频
            y, sr = librosa.load(input_file, sr=None)
            
            # 构建保留的音频段
            keep_segments = []
            last_end = 0
            
            for segment in silence_info["silence_segments"]:
                # 添加静音段前的音频
                if segment["start"] - padding > last_end:
                    keep_segments.append({
                        "start": last_end,
                        "end": max(last_end, segment["start"] - padding)
                    })
                last_end = segment["end"] + padding
            
            # 添加最后一段音频
            if last_end < len(y) / sr:
                keep_segments.append({
                    "start": last_end,
                    "end": len(y) / sr
                })
            
            # 合并音频段
            audio_parts = []
            for segment in keep_segments:
                start_sample = int(segment["start"] * sr)
                end_sample = int(segment["end"] * sr)
                audio_parts.append(y[start_sample:end_sample])
            
            # 合并所有音频段
            result_audio = np.concatenate(audio_parts)
            
            # 保存结果
            sf.write(output_file, result_audio, sr)
            
            original_duration = len(y) / sr
            new_duration = len(result_audio) / sr
            
            return {
                "success": True,
                "output_file": output_file,
                "original_duration": original_duration,
                "new_duration": new_duration,
                "removed_duration": original_duration - new_duration,
                "removed_segments": len(silence_info["silence_segments"])
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def split_audio_by_silence(
        self,
        input_file: str,
        output_dir: str,
        min_segment_duration: float = 1.0,
        threshold: float = -30.0
    ) -> Dict[str, Any]:
        """
        根据静音段分割音频
        
        Args:
            input_file: 输入音频文件路径
            output_dir: 输出目录
            min_segment_duration: 最小段时长（秒）
            threshold: 静音阈值（dB）
            
        Returns:
            分割结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            os.makedirs(output_dir, exist_ok=True)
            
            # 检测静音段
            silence_info = self.detect_silence(input_file, threshold, min_segment_duration)
            
            if not silence_info["success"]:
                return silence_info
            
            # 加载音频
            y, sr = librosa.load(input_file, sr=None)
            
            # 创建分割点
            split_points = [0]
            for segment in silence_info["silence_segments"]:
                split_points.extend([segment["start"], segment["end"]])
            split_points.append(len(y) / sr)
            
            # 生成分割段
            segments = []
            for i in range(0, len(split_points) - 1, 2):
                start = split_points[i]
                end = split_points[i + 1]
                
                if end - start >= min_segment_duration:
                    segment_name = f"segment_{len(segments) + 1:03d}.wav"
                    segment_path = os.path.join(output_dir, segment_name)
                    
                    start_sample = int(start * sr)
                    end_sample = int(end * sr)
                    segment_audio = y[start_sample:end_sample]
                    
                    sf.write(segment_path, segment_audio, sr)
                    
                    segments.append({
                        "file": segment_path,
                        "start": start,
                        "end": end,
                        "duration": end - start
                    })
            
            return {
                "success": True,
                "segments": segments,
                "total_segments": len(segments),
                "output_dir": output_dir
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def change_speed(
        self,
        input_file: str,
        output_file: str,
        speed_factor: float,
        preserve_pitch: bool = True
    ) -> Dict[str, Any]:
        """
        改变音频播放速度
        
        Args:
            input_file: 输入音频文件路径
            output_file: 输出音频文件路径
            speed_factor: 速度倍数 (>1 加速, <1 减速)
            preserve_pitch: 是否保持音调
            
        Returns:
            处理结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            if preserve_pitch:
                # 使用sox或ffmpeg的atempo滤镜
                cmd = [
                    'ffmpeg', '-i', input_file,
                    '-filter_complex',
                    f"atempo={speed_factor}",
                    '-y',
                    output_file
                ]
            else:
                # 直接改变采样率
                y, sr = librosa.load(input_file, sr=None)
                new_sr = int(sr * speed_factor)
                sf.write(output_file, y, new_sr)
                return {
                    "success": True,
                    "output_file": output_file,
                    "speed_factor": speed_factor,
                    "preserve_pitch": preserve_pitch,
                    "original_duration": len(y) / sr,
                    "new_duration": len(y) / new_sr
                }
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
                
            return {
                "success": True,
                "output_file": output_file,
                "speed_factor": speed_factor,
                "preserve_pitch": preserve_pitch
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_effects(
        self,
        input_file: str,
        output_file: str,
        effects: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        添加音频效果
        
        Args:
            input_file: 输入音频文件路径
            output_file: 输出音频文件路径
            effects: 效果配置字典
            
        Returns:
            处理结果字典
        """
        try:
            if not os.path.exists(input_file):
                return {"success": False, "error": f"Input file not found: {input_file}"}
                
            filter_chain = []
            
            # 回声效果
            if "echo" in effects:
                echo = effects["echo"]
                delay = echo.get("delay", 1000)
                decay = echo.get("decay", 0.5)
                filter_chain.append(f"aecho=0.8:0.9:{delay}:{decay}")
            
            # 混响效果
            if "reverb" in effects:
                reverb = effects["reverb"]
                room_size = reverb.get("room_size", 0.5)
                decay = reverb.get("decay", 0.5)
                filter_chain.append(f"aecho=0.8:0.9:1000:0.3")
            
            # 均衡器
            if "eq" in effects:
                eq = effects["eq"]
                # 简单的低音增强
                if "bass" in eq:
                    gain = eq["bass"]
                    filter_chain.append(f"bass=g={gain}")
                
                # 高音增强
                if "treble" in eq:
                    gain = eq["treble"]
                    filter_chain.append(f"treble=g={gain}")
            
            # 压缩器
            if "compressor" in effects:
                comp = effects["compressor"]
                ratio = comp.get("ratio", 2.0)
                threshold = comp.get("threshold", -20)
                attack = comp.get("attack", 10)
                release = comp.get("release", 100)
                filter_chain.append(
                    f"compand=attacks={attack}:decays={release}:points=-90/-90|-70/-70|-30/-{30+ratio}|0/0"
                )
            
            if not filter_chain:
                return {"success": False, "error": "No effects specified"}
            
            filter_str = ",".join(filter_chain)
            
            cmd = [
                'ffmpeg', '-i', input_file,
                '-af', filter_str,
                '-y',
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
                
            return {
                "success": True,
                "output_file": output_file,
                "effects": effects
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# 快捷函数
def convert_audio(input_file: str, output_file: str, **kwargs) -> Dict[str, Any]:
    """快捷音频格式转换函数"""
    processor = AudioProcessor()
    return processor.convert_audio_format(input_file, output_file, **kwargs)

def adjust_audio_volume(input_file: str, output_file: str, volume: float, **kwargs) -> Dict[str, Any]:
    """快捷音量调整函数"""
    processor = AudioProcessor()
    return processor.adjust_volume(input_file, output_file, volume, **kwargs)

def extract_audio(video_file: str, output_file: str, **kwargs) -> Dict[str, Any]:
    """快捷音频提取函数"""
    processor = AudioProcessor()
    return processor.extract_audio_from_video(video_file, output_file, **kwargs)

def trim_audio_file(input_file: str, output_file: str, start: float, duration: float) -> Dict[str, Any]:
    """快捷音频裁剪函数"""
    processor = AudioProcessor()
    return processor.trim_audio(input_file, output_file, start, duration)

def get_audio_duration(audio_file: str) -> float:
    """获取音频时长"""
    processor = AudioProcessor()
    info = processor.get_audio_info(audio_file)
    return info.get("duration", 0.0) if info.get("success") else 0.0

if __name__ == "__main__":
    # 测试功能
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试音频文件
        test_audio = os.path.join(temp_dir, "test.wav")
        sr = 44100
        duration = 5.0
        t = np.linspace(0, duration, int(sr * duration))
        y = np.sin(2 * np.pi * 440 * t)  # 440Hz正弦波
        sf.write(test_audio, y, sr)
        
        processor = AudioProcessor()
        
        # 测试获取音频信息
        info = processor.get_audio_info(test_audio)
        print("Audio info:", info)
        
        # 测试音量调整
        output = os.path.join(temp_dir, "adjusted.wav")
        result = processor.adjust_volume(test_audio, output, 0.5)
        print("Volume adjustment:", result)
        
        # 测试格式转换
        mp3_output = os.path.join(temp_dir, "converted.mp3")
        result = processor.convert_audio_format(test_audio, mp3_output, 'mp3')
        print("Format conversion:", result)