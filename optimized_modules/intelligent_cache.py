"""
智能缓存系统
提供多级缓存（本地内存 + Redis + 磁盘）的草稿数据管理
支持缓存预热、自动失效、数据同步等功能
"""

import asyncio
import json
import pickle
import time
import hashlib
from typing import Any, Optional, Dict, List, Tuple
from pathlib import Path
import logging
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import redis
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CacheMetadata:
    """缓存元数据"""
    key: str
    size: int
    created_at: float
    accessed_at: float
    access_count: int
    ttl: Optional[int] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class LocalCache:
    """本地内存缓存（LRU + TTL）"""
    
    def __init__(self, max_size_mb: int = 100, default_ttl: int = 3600):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.data: Dict[str, Any] = {}
        self.metadata: Dict[str, CacheMetadata] = {}
        self.total_size = 0
        self.lock = threading.RLock()
        
        # 启动清理线程
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def _get_size(self, obj: Any) -> int:
        """估算对象内存大小"""
        try:
            return len(pickle.dumps(obj))
        except:
            return 1024  # 默认估算
    
    def _cleanup_worker(self):
        """后台清理线程"""
        while True:
            time.sleep(60)  # 每分钟检查一次
            self._cleanup()
    
    def _cleanup(self):
        """清理过期和LRU数据"""
        with self.lock:
            current_time = time.time()
            keys_to_remove = []
            
            # 清理过期数据
            for key, meta in self.metadata.items():
                if meta.ttl and current_time - meta.created_at > meta.ttl:
                    keys_to_remove.append(key)
            
            # 如果仍然超出限制，按LRU清理
            if self.total_size > self.max_size_bytes:
                sorted_items = sorted(
                    self.metadata.items(),
                    key=lambda x: (x[1].access_count, x[1].access_at)
                )
                
                for key, meta in sorted_items:
                    if self.total_size <= self.max_size_bytes * 0.8:
                        break
                    keys_to_remove.append(key)
            
            # 执行清理
            for key in set(keys_to_remove):
                self._remove_key(key)
    
    def _remove_key(self, key: str):
        """移除指定key"""
        if key in self.data:
            meta = self.metadata[key]
            self.total_size -= meta.size
            del self.data[key]
            del self.metadata[key]
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key in self.data:
                meta = self.metadata[key]
                
                # 检查TTL
                if meta.ttl and time.time() - meta.created_at > meta.ttl:
                    self._remove_key(key)
                    return None
                
                # 更新访问统计
                meta.accessed_at = time.time()
                meta.access_count += 1
                
                return self.data[key]
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, tags: List[str] = None):
        """设置缓存值"""
        with self.lock:
            # 计算大小
            size = self._get_size(value)
            
            # 如果已存在，先移除旧值
            if key in self.data:
                self._remove_key(key)
            
            # 检查是否有足够空间
            while self.total_size + size > self.max_size_bytes and self.data:
                # 移除最久未使用的数据
                oldest_key = min(self.metadata.items(), key=lambda x: x[1].accessed_at)[0]
                self._remove_key(oldest_key)
            
            # 添加新数据
            self.data[key] = value
            self.metadata[key] = CacheMetadata(
                key=key,
                size=size,
                created_at=time.time(),
                accessed_at=time.time(),
                access_count=1,
                ttl=ttl or self.default_ttl,
                tags=tags or []
            )
            
            self.total_size += size
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self.lock:
            if key in self.data:
                self._remove_key(key)
                return True
        return False
    
    def delete_by_tags(self, tags: List[str]) -> int:
        """根据标签删除缓存"""
        with self.lock:
            keys_to_remove = [
                key for key, meta in self.metadata.items()
                if any(tag in meta.tags for tag in tags)
            ]
            
            for key in keys_to_remove:
                self._remove_key(key)
            
            return len(keys_to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.lock:
            return {
                'total_items': len(self.data),
                'total_size_mb': self.total_size / (1024 * 1024),
                'max_size_mb': self.max_size_bytes / (1024 * 1024),
                'hit_rate': self._calculate_hit_rate(),
                'oldest_item_age': self._get_oldest_age()
            }
    
    def _calculate_hit_rate(self) -> float:
        """计算缓存命中率"""
        if not self.metadata:
            return 0.0
        
        total_accesses = sum(meta.access_count for meta in self.metadata.values())
        if total_accesses == 0:
            return 0.0
        
        # 假设第一次访问是miss，其余是hit
        total_hits = total_accesses - len(self.metadata)
        return total_hits / total_accesses if total_accesses > 0 else 0.0
    
    def _get_oldest_age(self) -> float:
        """获取最旧数据的年龄（小时）"""
        if not self.metadata:
            return 0.0
        
        oldest_time = min(meta.created_at for meta in self.metadata.values())
        return (time.time() - oldest_time) / 3600

class RedisCache:
    """Redis分布式缓存"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", db: int = 0):
        self.redis_client = redis.from_url(redis_url, db=db, decode_responses=False)
        self.default_ttl = 3600
    
    def _make_key(self, key: str) -> str:
        """生成Redis键名"""
        return f"capcut:cache:{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            value = self.redis_client.get(self._make_key(key))
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        try:
            ttl = ttl or self.default_ttl
            serialized = pickle.dumps(value)
            self.redis_client.setex(self._make_key(key), ttl, serialized)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            return bool(self.redis_client.delete(self._make_key(key)))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def delete_by_pattern(self, pattern: str) -> int:
        """根据模式删除缓存"""
        try:
            keys = self.redis_client.keys(self._make_key(pattern))
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis delete pattern error: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return bool(self.redis_client.exists(self._make_key(key)))
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

class DiskCache:
    """磁盘持久化缓存"""
    
    def __init__(self, cache_dir: str = "./disk_cache", max_size_gb: float = 10.0):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_size_bytes = max_size_gb * 1024 * 1024 * 1024
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """加载元数据"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load disk cache metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """保存元数据"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save disk cache metadata: {e}")
    
    def _get_file_path(self, key: str) -> Path:
        """获取文件路径"""
        # 使用两级目录结构避免单目录文件过多
        hash_prefix = key[:2]
        sub_dir = self.cache_dir / hash_prefix
        sub_dir.mkdir(exist_ok=True)
        return sub_dir / key
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            file_path = self._get_file_path(key)
            if not file_path.exists():
                return None
            
            # 检查元数据
            if key in self.metadata:
                meta = self.metadata[key]
                if meta.get('ttl') and time.time() - meta['created_at'] > meta['ttl']:
                    file_path.unlink(missing_ok=True)
                    del self.metadata[key]
                    self._save_metadata()
                    return None
            
            # 读取缓存
            with open(file_path, 'rb') as f:
                return pickle.load(f)
                
        except Exception as e:
            logger.error(f"Disk cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        try:
            file_path = self._get_file_path(key)
            
            # 序列化并保存
            serialized = pickle.dumps(value)
            with open(file_path, 'wb') as f:
                f.write(serialized)
            
            # 更新元数据
            self.metadata[key] = {
                'size': len(serialized),
                'created_at': time.time(),
                'ttl': ttl
            }
            
            self._save_metadata()
            
            # 清理旧文件
            self._cleanup()
            
        except Exception as e:
            logger.error(f"Disk cache set error: {e}")
    
    def _cleanup(self):
        """清理磁盘缓存"""
        try:
            total_size = 0
            files_to_remove = []
            
            for file_path in self.cache_dir.rglob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    total_size += stat.st_size
                    
                    # 检查过期
                    key = file_path.name
                    if key in self.metadata:
                        meta = self.metadata[key]
                        if meta.get('ttl') and time.time() - meta['created_at'] > meta['ttl']:
                            files_to_remove.append(file_path)
            
            # 如果超出限制，清理最旧的文件
            if total_size > self.max_size_bytes:
                all_files = []
                for file_path in self.cache_dir.rglob("*"):
                    if file_path.is_file():
                        key = file_path.name
                        if key in self.metadata:
                            all_files.append((file_path, self.metadata[key]))
                
                all_files.sort(key=lambda x: x[1]['created_at'])
                
                for file_path, meta in all_files:
                    if total_size <= self.max_size_bytes * 0.8:
                        break
                    file_path.unlink(missing_ok=True)
                    if file_path.name in self.metadata:
                        del self.metadata[file_path.name]
                    total_size -= meta['size']
            
            # 删除标记的文件
            for file_path in files_to_remove:
                file_path.unlink(missing_ok=True)
                if file_path.name in self.metadata:
                    del self.metadata[file_path.name]
            
            self._save_metadata()
            
        except Exception as e:
            logger.error(f"Disk cache cleanup error: {e}")

class IntelligentCache:
    """智能多级缓存系统"""
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379",
                 local_cache_size_mb: int = 100,
                 disk_cache_size_gb: float = 10.0,
                 default_ttl: int = 3600):
        
        self.local_cache = LocalCache(local_cache_size_mb, default_ttl)
        self.redis_cache = RedisCache(redis_url)
        self.disk_cache = DiskCache("./disk_cache", disk_cache_size_gb)
        self.default_ttl = default_ttl
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """生成缓存键"""
        return f"{prefix}:{hashlib.md5(identifier.encode()).hexdigest()}"
    
    async def get(self, key: str, level: str = "all") -> Optional[Any]:
        """获取缓存值，支持多级查询"""
        
        # 1. 本地缓存
        if level in ["all", "local"]:
            value = self.local_cache.get(key)
            if value is not None:
                return value
        
        # 2. Redis缓存
        if level in ["all", "redis"]:
            value = await self.redis_cache.get(key)
            if value is not None:
                # 回填到本地缓存
                self.local_cache.set(key, value)
                return value
        
        # 3. 磁盘缓存
        if level in ["all", "disk"]:
            value = await self.disk_cache.get(key)
            if value is not None:
                # 回填到Redis和本地缓存
                await self.redis_cache.set(key, value)
                self.local_cache.set(key, value)
                return value
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                  tags: List[str] = None, level: str = "all"):
        """设置缓存值，支持多级存储"""
        ttl = ttl or self.default_ttl
        
        if level in ["all", "local"]:
            self.local_cache.set(key, value, ttl, tags)
        
        if level in ["all", "redis"]:
            await self.redis_cache.set(key, value, ttl)
        
        if level in ["all", "disk"]:
            await self.disk_cache.set(key, value, ttl)
    
    async def delete(self, key: str, level: str = "all") -> bool:
        """删除缓存值"""
        success = True
        
        if level in ["all", "local"]:
            success &= self.local_cache.delete(key)
        
        if level in ["all", "redis"]:
            success &= await self.redis_cache.delete(key)
        
        if level in ["all", "disk"]:
            await self.disk_cache.set(key, None, 0)  # 设置为空值
        
        return success
    
    async def delete_by_tags(self, tags: List[str], level: str = "all") -> int:
        """根据标签删除缓存"""
        count = 0
        
        if level in ["all", "local"]:
            count += self.local_cache.delete_by_tags(tags)
        
        if level in ["all", "redis"]:
            # Redis需要特殊处理标签删除
            pattern = "capcut:cache:*"
            keys = await self.redis_cache.delete_by_pattern(pattern)
            count += keys
        
        if level in ["all", "disk"]:
            # 磁盘缓存的标签删除需要遍历
            pass  # 简化实现
        
        return count
    
    async def cache_draft(self, draft_id: str, draft_data: dict, ttl: int = 3600):
        """缓存草稿数据"""
        key = self._generate_key("draft", draft_id)
        await self.set(key, draft_data, ttl, tags=["draft", draft_id])
    
    async def get_draft(self, draft_id: str) -> Optional[dict]:
        """获取草稿数据"""
        key = self._generate_key("draft", draft_id)
        return await self.get(key)
    
    async def cache_media_metadata(self, url: str, metadata: dict, ttl: int = 7200):
        """缓存媒体元数据"""
        key = self._generate_key("media_meta", url)
        await self.set(key, metadata, ttl, tags=["media", "metadata"])
    
    async def get_media_metadata(self, url: str) -> Optional[dict]:
        """获取媒体元数据"""
        key = self._generate_key("media_meta", url)
        return await self.get(key)
    
    async def cache_export_result(self, export_id: str, result: dict, ttl: int = 86400):
        """缓存导出结果"""
        key = self._generate_key("export", export_id)
        await self.set(key, result, ttl, tags=["export", export_id])
    
    async def get_export_result(self, export_id: str) -> Optional[dict]:
        """获取导出结果"""
        key = self._generate_key("export", export_id)
        return await self.get(key)
    
    async def warmup_cache(self, warmup_data: List[Tuple[str, Any, Optional[int]]]):
        """缓存预热"""
        tasks = []
        for key, value, ttl in warmup_data:
            task = self.set(key, value, ttl)
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取各级缓存统计"""
        return {
            'local_cache': self.local_cache.get_stats(),
            'redis_cache': {
                'connected': self.redis_cache.redis.ping() if hasattr(self.redis_cache.redis, 'ping') else False
            },
            'disk_cache': {
                'cache_dir': str(self.disk_cache.cache_dir),
                'max_size_gb': self.disk_cache.max_size_bytes / (1024**3)
            }
        }

# 全局缓存实例
cache = IntelligentCache()

# 使用示例
async def main():
    """使用示例"""
    
    # 缓存草稿数据
    draft_data = {
        'id': 'draft_123',
        'name': '测试草稿',
        'duration': 30.5,
        'tracks': [...]
    }
    
    await cache.cache_draft('draft_123', draft_data)
    
    # 获取草稿数据
    cached_draft = await cache.get_draft('draft_123')
    print(f"获取到的草稿: {cached_draft}")
    
    # 缓存媒体元数据
    media_meta = {
        'width': 1920,
        'height': 1080,
        'duration': 60.0,
        'fps': 30.0
    }
    
    await cache.cache_media_metadata('https://example.com/video.mp4', media_meta)
    
    # 获取统计信息
    stats = cache.get_stats()
    print(f"缓存统计: {stats}")

if __name__ == "__main__":
    asyncio.run(main())