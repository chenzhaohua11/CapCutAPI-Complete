"""
智能缓存优化器
实现缓存预热、自适应TTL、LRU+LFU混合策略和热点数据识别
大幅提升缓存命中率和系统性能
"""

import asyncio
import time
import logging
import threading
import json
import hashlib
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, OrderedDict
from abc import ABC, abstractmethod
import heapq
import random
import math

from .performance_monitor import tracker
from .intelligent_cache import IntelligentCache

logger = logging.getLogger(__name__)

@dataclass
class CacheMetrics:
    """缓存指标"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    avg_access_time: float = 0.0
    hit_rate: float = 0.0
    miss_rate: float = 0.0
    
    def update_hit_rate(self):
        """更新命中率"""
        if self.total_requests > 0:
            self.hit_rate = self.hits / self.total_requests
            self.miss_rate = self.misses / self.total_requests

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 1
    size: int = 0
    ttl: float = 300.0  # 默认5分钟
    priority: float = 1.0
    
    def __post_init__(self):
        if isinstance(self.value, (str, bytes)):
            self.size = len(self.value)
        elif isinstance(self.value, dict):
            self.size = len(json.dumps(self.value))
        else:
            self.size = 100  # 默认值

class CacheStrategy(ABC):
    """缓存策略基类"""
    
    @abstractmethod
    def should_evict(self, entry: CacheEntry, current_time: float) -> bool:
        """是否应该淘汰"""
        pass
    
    @abstractmethod
    def calculate_priority(self, entry: CacheEntry, current_time: float) -> float:
        """计算优先级"""
        pass

class LRUCacheStrategy(CacheStrategy):
    """LRU缓存策略"""
    
    def should_evict(self, entry: CacheEntry, current_time: float) -> bool:
        return (current_time - entry.last_accessed) > entry.ttl
    
    def calculate_priority(self, entry: CacheEntry, current_time: float) -> float:
        return 1.0 / (current_time - entry.last_accessed + 1)

class LFUStrategy(CacheStrategy):
    """LFU缓存策略"""
    
    def should_evict(self, entry: CacheEntry, current_time: float) -> bool:
        return (current_time - entry.created_at) > entry.ttl
    
    def calculate_priority(self, entry: CacheEntry, current_time: float) -> float:
        return entry.access_count / (current_time - entry.created_at + 1)

class AdaptiveTTLStrategy(CacheStrategy):
    """自适应TTL策略"""
    
    def __init__(self, base_ttl: float = 300.0, max_ttl: float = 3600.0, min_ttl: float = 60.0):
        self.base_ttl = base_ttl
        self.max_ttl = max_ttl
        self.min_ttl = min_ttl
        self.access_patterns: Dict[str, List[float]] = defaultdict(list)
    
    def should_evict(self, entry: CacheEntry, current_time: float) -> bool:
        return (current_time - entry.last_accessed) > entry.ttl
    
    def calculate_priority(self, entry: CacheEntry, current_time: float) -> float:
        # 基于访问模式调整TTL
        access_pattern = self.access_patterns.get(entry.key, [])
        
        if len(access_pattern) >= 3:
            # 计算访问频率
            intervals = [access_pattern[i+1] - access_pattern[i] 
                        for i in range(len(access_pattern)-1)]
            avg_interval = sum(intervals) / len(intervals)
            
            # 调整TTL：频繁访问的延长TTL，稀疏访问的缩短TTL
            if avg_interval < 60:  # 每分钟访问
                entry.ttl = min(self.max_ttl, entry.ttl * 1.5)
            elif avg_interval > 1800:  # 每30分钟访问
                entry.ttl = max(self.min_ttl, entry.ttl * 0.8)
        
        # 混合LRU和LFU
        lru_factor = 1.0 / (current_time - entry.last_accessed + 1)
        lfu_factor = entry.access_count / (current_time - entry.created_at + 1)
        
        return lru_factor * 0.6 + lfu_factor * 0.4
    
    def record_access(self, key: str, timestamp: float):
        """记录访问模式"""
        self.access_patterns[key].append(timestamp)
        
        # 限制历史记录大小
        if len(self.access_patterns[key]) > 10:
            self.access_patterns[key] = self.access_patterns[key][-10:]

class HotspotDetector:
    """热点数据识别器"""
    
    def __init__(self, window_size: int = 100, hotspot_threshold: int = 5):
        self.window_size = window_size
        self.hotspot_threshold = hotspot_threshold
        self.access_log: List[Tuple[str, float]] = []
        self.hotspots: Set[str] = set()
        self.key_frequencies: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()
    
    def record_access(self, key: str, timestamp: float = None):
        """记录访问"""
        if timestamp is None:
            timestamp = time.time()
        
        with self._lock:
            self.access_log.append((key, timestamp))
            self.key_frequencies[key] += 1
            
            # 限制日志大小
            if len(self.access_log) > self.window_size:
                old_key, old_time = self.access_log.pop(0)
                self.key_frequencies[old_key] -= 1
                if self.key_frequencies[old_key] <= 0:
                    del self.key_frequencies[old_key]
            
            # 更新热点
            self._update_hotspots()
    
    def _update_hotspots(self):
        """更新热点集合"""
        current_time = time.time()
        recent_window = int(self.window_size * 0.3)  # 最近30%的访问
        
        if len(self.access_log) >= recent_window:
            recent_keys = [k for k, t in self.access_log[-recent_window:]]
            key_counts = defaultdict(int)
            
            for key in recent_keys:
                key_counts[key] += 1
            
            new_hotspots = {
                key for key, count in key_counts.items() 
                if count >= self.hotspot_threshold
            }
            
            self.hotspots = new_hotspots
    
    def is_hotspot(self, key: str) -> bool:
        """判断是否为热点数据"""
        with self._lock:
            return key in self.hotspots
    
    def get_hotspots(self) -> List[str]:
        """获取当前热点列表"""
        with self._lock:
            return list(self.hotspots)
    
    def get_access_statistics(self) -> Dict[str, Any]:
        """获取访问统计"""
        with self._lock:
            total_accesses = len(self.access_log)
            key_distribution = dict(self.key_frequencies)
            
            return {
                'total_accesses': total_accesses,
                'unique_keys': len(key_distribution),
                'hotspots': list(self.hotspots),
                'key_distribution': key_distribution,
                'hotspot_ratio': len(self.hotspots) / max(len(key_distribution), 1)
            }

class CachePreheater:
    """缓存预热器"""
    
    def __init__(self, cache: IntelligentCache):
        self.cache = cache
        self.preheat_patterns: Dict[str, List[str]] = defaultdict(list)
        self.preheat_schedule: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def add_preheat_pattern(self, pattern: str, related_keys: List[str]):
        """添加预热模式"""
        with self._lock:
            self.preheat_patterns[pattern] = related_keys
    
    def schedule_preheat(self, key: str, preheat_time: float = None):
        """调度预热"""
        if preheat_time is None:
            preheat_time = time.time() + 300  # 5分钟后预热
        
        with self._lock:
            self.preheat_schedule[key] = preheat_time
    
    async def run_preheat(self):
        """执行预热"""
        while True:
            try:
                current_time = time.time()
                
                with self._lock:
                    keys_to_preheat = [
                        key for key, preheat_time in self.preheat_schedule.items()
                        if preheat_time <= current_time
                    ]
                    
                    # 清理已执行的预热
                    for key in keys_to_preheat:
                        del self.preheat_schedule[key]
                
                # 预热相关数据
                for key in keys_to_preheat:
                    await self._preheat_related_data(key)
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"Preheating error: {e}")
                await asyncio.sleep(300)
    
    async def _preheat_related_data(self, key: str):
        """预热相关数据"""
        # 这里可以实现具体的预热逻辑
        logger.info(f"Preheating data for key: {key}")

class CacheOptimizer:
    """缓存优化器主类"""
    
    def __init__(self, cache: IntelligentCache, max_size: int = 1000):
        self.cache = cache
        self.max_size = max_size
        self.cache_data: Dict[str, CacheEntry] = {}
        self.strategy = AdaptiveTTLStrategy()
        self.hotspot_detector = HotspotDetector()
        self.preheater = CachePreheater(cache)
        self.metrics = CacheMetrics()
        self._lock = threading.RLock()
        self.cleanup_thread = None
        self.is_running = False
        
    def start(self):
        """启动缓存优化器"""
        if not self.is_running:
            self.is_running = True
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_loop, daemon=True
            )
            self.cleanup_thread.start()
            logger.info("Cache optimizer started")
    
    def stop(self):
        """停止缓存优化器"""
        self.is_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
        logger.info("Cache optimizer stopped")
    
    def _cleanup_loop(self):
        """清理循环"""
        while self.is_running:
            try:
                self._evict_expired()
                self._evict_lru()
                time.sleep(60)  # 每分钟清理一次
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def _evict_expired(self):
        """淘汰过期数据"""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, entry in self.cache_data.items():
                if self.strategy.should_evict(entry, current_time):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache_data[key]
                self.metrics.evictions += 1
    
    def _evict_lru(self):
        """LRU淘汰"""
        with self._lock:
            if len(self.cache_data) > self.max_size:
                # 按优先级排序并淘汰
                entries = [
                    (key, self.strategy.calculate_priority(entry, time.time()))
                    for key, entry in self.cache_data.items()
                ]
                
                entries.sort(key=lambda x: x[1])
                
                # 淘汰最低优先级的10%
                to_evict = entries[:max(1, len(entries) // 10)]
                
                for key, _ in to_evict:
                    if key in self.cache_data:
                        del self.cache_data[key]
                        self.metrics.evictions += 1
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with tracker.track_operation("cache_get", metadata={'key': key}):
            with self._lock:
                entry = self.cache_data.get(key)
                
                if entry is None:
                    self.metrics.misses += 1
                    self.metrics.total_requests += 1
                    self.metrics.update_hit_rate()
                    return None
                
                # 更新访问信息
                entry.last_accessed = time.time()
                entry.access_count += 1
                
                # 记录热点
                self.hotspot_detector.record_access(key)
                
                # 更新策略
                if isinstance(self.strategy, AdaptiveTTLStrategy):
                    self.strategy.record_access(key, time.time())
                
                self.metrics.hits += 1
                self.metrics.total_requests += 1
                self.metrics.update_hit_rate()
                
                return entry.value
    
    def set(self, key: str, value: Any, ttl: float = None) -> bool:
        """设置缓存值"""
        with tracker.track_operation("cache_set", metadata={'key': key, 'size': len(str(value))}):
            with self._lock:
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=time.time(),
                    last_accessed=time.time(),
                    ttl=ttl or 300.0
                )
                
                # 热点数据延长TTL
                if self.hotspot_detector.is_hotspot(key):
                    entry.ttl *= 2
                
                self.cache_data[key] = entry
                
                # 触发清理
                if len(self.cache_data) > self.max_size:
                    self._evict_lru()
                
                return True
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self.cache_data:
                del self.cache_data[key]
                return True
            return False
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self.cache_data.clear()
            self.metrics = CacheMetrics()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            stats = asdict(self.metrics)
            stats.update({
                'cache_size': len(self.cache_data),
                'total_size_mb': sum(entry.size for entry in self.cache_data.values()) / (1024 * 1024),
                'hotspots': self.hotspot_detector.get_hotspots(),
                'access_patterns': self.hotspot_detector.get_access_statistics()
            })
            return stats
    
    def optimize_for_pattern(self, pattern: str):
        """基于访问模式优化"""
        if pattern == "video_processing":
            # 视频处理模式：大文件，长TTL
            self.strategy = AdaptiveTTLStrategy(base_ttl=1800, max_ttl=7200)
        elif pattern == "api_responses":
            # API响应模式：小数据，短TTL
            self.strategy = AdaptiveTTLStrategy(base_ttl=60, max_ttl=300)
        elif pattern == "user_sessions":
            # 用户会话模式：中等TTL
            self.strategy = AdaptiveTTLStrategy(base_ttl=600, max_ttl=3600)

# 全局实例
optimizer = CacheOptimizer(IntelligentCache())

# 使用示例
async def example_usage():
    """使用示例"""
    
    # 启动优化器
    optimizer.start()
    
    # 设置一些测试数据
    for i in range(100):
        key = f"video_{i}"
        value = {"url": f"http://example.com/video_{i}.mp4", "duration": 120}
        optimizer.set(key, value)
    
    # 模拟访问模式
    for i in range(50):
        # 热点数据
        for j in range(5):
            optimizer.get("video_1")
            optimizer.get("video_2")
        
        # 普通数据
        optimizer.get(f"video_{i % 10 + 3}")
    
    # 获取统计信息
    stats = optimizer.get_stats()
    print("缓存统计:", json.dumps(stats, indent=2, default=str))
    
    # 停止优化器
    optimizer.stop()

if __name__ == "__main__":
    asyncio.run(example_usage())