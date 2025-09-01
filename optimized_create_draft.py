"""
优化的草稿创建模块 - 精简版
提供高效的草稿管理和缓存机制
"""

import uuid
import time
from typing import Optional, Tuple
import pyJianYingDraft as draft

class DraftManager:
    """高效的草稿管理器"""
    
    def __init__(self, max_cache_size: int = 1000):
        self._cache = {}
        self._access_order = []
        self.max_cache_size = max_cache_size
    
    def _update_cache(self, draft_id: str, script) -> None:
        """更新LRU缓存"""
        if draft_id in self._cache:
            self._access_order.remove(draft_id)
        elif len(self._cache) >= self.max_cache_size:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]
        
        self._cache[draft_id] = script
        self._access_order.append(draft_id)
    
    def _get_from_cache(self, draft_id: str) -> Optional[draft.Script_file]:
        """从缓存获取草稿"""
        if draft_id in self._cache:
            self._access_order.remove(draft_id)
            self._access_order.append(draft_id)
            return self._cache[draft_id]
        return None
    
    def create_draft(self, width: int = 1080, height: int = 1920) -> Tuple[str, draft.Script_file]:
        """创建新草稿"""
        draft_id = f"draft_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        script = draft.Script_file(width, height)
        
        self._update_cache(draft_id, script)
        return draft_id, script
    
    def get_or_create_draft(self, draft_id: Optional[str] = None, 
                           width: int = 1080, height: int = 1920) -> Tuple[str, draft.Script_file]:
        """获取或创建草稿"""
        if draft_id and draft_id in self._cache:
            return draft_id, self._get_from_cache(draft_id)
        
        return self.create_draft(width, height)
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()
    
    def cache_stats(self) -> dict:
        """获取缓存统计"""
        return {
            "cached_items": len(self._cache),
            "max_size": self.max_cache_size,
            "hit_rate": 0  # 简化版，实际可添加命中率计算
        }

# 全局草稿管理器实例
draft_manager = DraftManager()

# 向后兼容的接口
def create_draft(width: int = 1080, height: int = 1920) -> Tuple[draft.Script_file, str]:
    """兼容原接口"""
    draft_id, script = draft_manager.create_draft(width, height)
    return script, draft_id

def get_or_create_draft(draft_id: Optional[str] = None, 
                       width: int = 1080, height: int = 1920) -> Tuple[str, draft.Script_file]:
    """兼容原接口"""
    return draft_manager.get_or_create_draft(draft_id, width, height)

# 清理旧的缓存模块引用（可选）
try:
    from draft_cache import DRAFT_CACHE
    # 迁移旧缓存到新管理器
    if hasattr(DRAFT_CACHE, '_data'):
        for draft_id, script in DRAFT_CACHE._data.items():
            draft_manager._cache[draft_id] = script
            draft_manager._access_order.append(draft_id)
except ImportError:
    pass  # 旧缓存不存在，忽略