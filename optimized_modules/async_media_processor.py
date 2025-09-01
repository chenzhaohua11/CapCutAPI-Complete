"""
异步媒体处理模块
提供高性能的媒体文件下载、处理和缓存功能
"""

import asyncio
import aiohttp
import aiofiles
import hashlib
import os
import time
from typing import Dict, Optional, Any, List
from pathlib import Path
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import tempfile
import mimetypes

import cv2
import numpy as np
from PIL import Image
import imageio

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MediaMetadata:
    """媒体文件元数据"""
    url: str
    file_hash: str
    file_size: int
    mime_type: str
    width: int
    height: int
    duration: Optional[float] = None
    fps: Optional[float] = None
    bitrate: Optional[int] = None

class AsyncMediaCache:
    """异步媒体缓存系统"""
    
    def __init__(self, cache_dir: str = "./media_cache", max_size_gb: float = 5.0):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_size_bytes = max_size_gb * 1024 * 1024 * 1024
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """加载缓存元数据"""
        try:
            import json
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache metadata: {e}")
    
    def _save_metadata(self):
        """保存缓存元数据"""
        try:
            import json
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def _get_file_hash(self, url: str) -> str:
        """计算URL的哈希值作为文件名"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _cleanup_cache(self):
        """清理过期缓存"""
        try:
            total_size = 0
            files_to_remove = []
            
            for file_path in self.cache_dir.glob("*"):
                if file_path.is_file() and file_path.name != "cache_metadata.json":
                    stat = file_path.stat()
                    total_size += stat.st_size
                    
                    # 检查文件年龄
                    file_age = time.time() - stat.st_mtime
                    if file_age > 7 * 24 * 3600:  # 7天过期
                        files_to_remove.append(file_path)
            
            # 如果总大小超过限制，删除最旧的文件
            if total_size > self.max_size_bytes:
                files = [(f, f.stat().st_mtime) for f in self.cache_dir.glob("*") 
                        if f.is_file() and f.name != "cache_metadata.json"]
                files.sort(key=lambda x: x[1])
                
                for file_path, _ in files:
                    if total_size <= self.max_size_bytes * 0.8:  # 清理到80%容量
                        break
                    file_path.unlink()
                    total_size -= file_path.stat().st_size
            
            # 删除标记的文件
            for file_path in files_to_remove:
                file_path.unlink()
                
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
    
    async def get_cached_media(self, url: str) -> Optional[Path]:
        """获取缓存的媒体文件路径"""
        file_hash = self._get_file_hash(url)
        cached_file = self.cache_dir / file_hash
        
        if cached_file.exists():
            # 更新访问时间
            cached_file.touch()
            return cached_file
        
        return None
    
    async def cache_media(self, url: str, content: bytes, metadata: Dict[str, Any]) -> Path:
        """缓存媒体文件"""
        file_hash = self._get_file_hash(url)
        cached_file = self.cache_dir / file_hash
        
        try:
            async with aiofiles.open(cached_file, 'wb') as f:
                await f.write(content)
            
            # 更新元数据
            self.metadata[file_hash] = {
                'url': url,
                'size': len(content),
                'timestamp': time.time(),
                **metadata
            }
            self._save_metadata()
            
            # 异步清理缓存
            await asyncio.get_event_loop().run_in_executor(None, self._cleanup_cache)
            
            return cached_file
            
        except Exception as e:
            logger.error(f"Failed to cache media: {e}")
            if cached_file.exists():
                cached_file.unlink()
            raise

class AsyncMediaProcessor:
    """异步媒体处理器"""
    
    def __init__(self, 
                 max_concurrent_downloads: int = 10,
                 chunk_size: int = 8192,
                 timeout: int = 30):
        self.max_concurrent = max_concurrent_downloads
        self.chunk_size = chunk_size
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.cache = AsyncMediaCache()
        self.session: Optional[aiohttp.ClientSession] = None
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers={'User-Agent': 'CapCutAPI/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def download_media(self, url: str, progress_callback=None) -> bytes:
        """异步下载媒体文件"""
        if not self.session:
            raise RuntimeError("Use async context manager")
        
        # 检查缓存
        cached_path = await self.cache.get_cached_media(url)
        if cached_path:
            logger.info(f"Using cached media: {url}")
            async with aiofiles.open(cached_path, 'rb') as f:
                return await f.read()
        
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunks = []
                
                async for chunk in response.content.iter_chunked(self.chunk_size):
                    chunks.append(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = (downloaded / total_size) * 100
                        await progress_callback(progress)
                
                content = b''.join(chunks)
                
                # 缓存下载的内容
                metadata = {
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': len(content),
                    'etag': response.headers.get('etag', ''),
                    'last_modified': response.headers.get('last-modified', '')
                }
                
                await self.cache.cache_media(url, content, metadata)
                
                return content
                
        except aiohttp.ClientError as e:
            logger.error(f"Failed to download {url}: {e}")
            raise
    
    async def analyze_media(self, content: bytes, url: str) -> MediaMetadata:
        """异步分析媒体文件"""
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.tmp', delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            # 在后台线程中分析媒体
            metadata = await asyncio.get_event_loop().run_in_executor(
                self.executor, self._analyze_media_sync, tmp_path, url
            )
            
            # 清理临时文件
            Path(tmp_path).unlink(missing_ok=True)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to analyze media: {e}")
            raise
    
    def _analyze_media_sync(self, file_path: str, url: str) -> MediaMetadata:
        """同步媒体分析（在后台线程中运行）"""
        file_hash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
        file_size = os.path.getsize(file_path)
        mime_type, _ = mimetypes.guess_type(url)
        
        try:
            # 使用 OpenCV 分析视频
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else None
                cap.release()
            else:
                # 尝试使用 PIL 分析图片
                with Image.open(file_path) as img:
                    width, height = img.size
                    fps = None
                    duration = None
            
            return MediaMetadata(
                url=url,
                file_hash=file_hash,
                file_size=file_size,
                mime_type=mime_type or 'application/octet-stream',
                width=width,
                height=height,
                duration=duration,
                fps=fps
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze media file: {e}")
            return MediaMetadata(
                url=url,
                file_hash=file_hash,
                file_size=file_size,
                mime_type=mime_type or 'application/octet-stream',
                width=0,
                height=0
            )
    
    async def process_media_with_progress(self, url: str, progress_callback=None) -> Dict[str, Any]:
        """带进度回调的完整媒体处理"""
        try:
            # 下载媒体
            if progress_callback:
                await progress_callback("开始下载", 0)
            
            content = await self.download_media(url, 
                lambda p: progress_callback(f"下载中... {p:.1f}%", p * 0.3))
            
            # 分析媒体
            if progress_callback:
                await progress_callback("分析媒体信息", 30)
            
            metadata = await self.analyze_media(content, url)
            
            if progress_callback:
                await progress_callback("处理完成", 100)
            
            return {
                'success': True,
                'metadata': metadata.__dict__,
                'cached': await self.cache.get_cached_media(url) is not None,
                'size': len(content)
            }
            
        except Exception as e:
            logger.error(f"Media processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'cached': False
            }

class MediaProcessorPool:
    """媒体处理器池，管理多个并发处理器"""
    
    def __init__(self, pool_size: int = 3):
        self.pool_size = pool_size
        self.processors: List[AsyncMediaProcessor] = []
        self.current_index = 0
    
    async def initialize(self):
        """初始化处理器池"""
        for _ in range(self.pool_size):
            processor = AsyncMediaProcessor()
            await processor.__aenter__()
            self.processors.append(processor)
    
    async def cleanup(self):
        """清理处理器池"""
        for processor in self.processors:
            await processor.__aexit__(None, None, None)
        self.processors.clear()
    
    def get_processor(self) -> AsyncMediaProcessor:
        """轮询获取处理器"""
        processor = self.processors[self.current_index]
        self.current_index = (self.current_index + 1) % self.pool_size
        return processor
    
    async def process_batch(self, urls: List[str], progress_callback=None) -> List[Dict[str, Any]]:
        """批量处理多个媒体文件"""
        semaphore = asyncio.Semaphore(self.pool_size)
        
        async def process_single(url):
            async with semaphore:
                processor = self.get_processor()
                return await processor.process_media_with_progress(url, progress_callback)
        
        tasks = [process_single(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

# 使用示例
async def main():
    """使用示例"""
    urls = [
        "https://example.com/video1.mp4",
        "https://example.com/video2.mp4",
        "https://example.com/image1.jpg"
    ]
    
    async def progress_handler(message: str, percentage: float):
        print(f"{message}: {percentage:.1f}%")
    
    pool = MediaProcessorPool(pool_size=3)
    await pool.initialize()
    
    try:
        results = await pool.process_batch(urls, progress_handler)
        
        for url, result in zip(urls, results):
            if isinstance(result, dict) and result.get('success'):
                print(f"✅ 成功处理: {url}")
                print(f"   尺寸: {result['metadata']['width']}x{result['metadata']['height']}")
                if result['metadata']['duration']:
                    print(f"   时长: {result['metadata']['duration']:.2f}s")
            else:
                print(f"❌ 处理失败: {url}")
                print(f"   错误: {result}")
    
    finally:
        await pool.cleanup()

if __name__ == "__main__":
    asyncio.run(main())