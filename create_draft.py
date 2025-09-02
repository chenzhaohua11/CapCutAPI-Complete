"""草稿创建模块 - 优化版
提供草稿创建、获取和管理功能
"""

import uuid
import pyJianYingDraft as draft
import time
import logging
from typing import Tuple, Optional, Any
from draft_cache import DRAFT_CACHE, update_cache

# 配置日志
logger = logging.getLogger(__name__)

def create_draft(width: int = 1080, height: int = 1920) -> Tuple[Any, str]:
    """
    创建新的CapCut草稿
    
    Args:
        width: 视频宽度，默认1080
        height: 视频高度，默认1920
        
    Returns:
        Tuple[Script_file, str]: 返回草稿对象和草稿ID
        
    Raises:
        ValueError: 当宽度或高度参数无效时
        RuntimeError: 当草稿创建失败时
    """
    # 参数验证
    if width <= 0 or height <= 0:
        raise ValueError(f"无效的视频尺寸: {width}x{height}")
    
    try:
        # 生成时间戳和草稿ID
        unix_time = int(time.time())
        unique_id = uuid.uuid4().hex[:8]  # 取UUID的前8位
        draft_id = f"dfd_cat_{unix_time}_{unique_id}"  # 使用时间戳和UUID组合
        
        logger.info(f"创建新草稿: {draft_id}, 分辨率: {width}x{height}")
        
        # 创建指定分辨率的CapCut草稿
        script = draft.Script_file(width, height)
        
        # 存储到全局缓存
        update_cache(draft_id, script)
        
        return script, draft_id
    except Exception as e:
        logger.error(f"创建草稿失败: {str(e)}")
        raise RuntimeError(f"创建草稿失败: {str(e)}") from e

def get_or_create_draft(draft_id: Optional[str] = None, width: int = 1080, height: int = 1920) -> Tuple[str, Any]:
    """
    获取或创建CapCut草稿
    
    Args:
        draft_id: 草稿ID，如果为None或对应的草稿不存在，则创建新草稿
        width: 视频宽度，默认1080
        height: 视频高度，默认1920
        
    Returns:
        Tuple[str, Script_file]: 返回草稿ID和草稿对象
        
    Raises:
        ValueError: 当宽度或高度参数无效时
        RuntimeError: 当草稿创建失败时
    """
    global DRAFT_CACHE  # 声明使用全局变量
    
    try:
        if draft_id is not None and draft_id in DRAFT_CACHE:
            # 从缓存获取现有草稿信息
            logger.info(f"从缓存获取草稿: {draft_id}")
            # 更新最后访问时间
            update_cache(draft_id, DRAFT_CACHE[draft_id])
            return draft_id, DRAFT_CACHE[draft_id]

        # 创建新草稿逻辑
        logger.info(f"未找到现有草稿，创建新草稿，分辨率: {width}x{height}")
        script, generated_draft_id = create_draft(
            width=width,
            height=height,
        )
        return generated_draft_id, script
    except Exception as e:
        logger.error(f"获取或创建草稿失败: {str(e)}")
        raise RuntimeError(f"获取或创建草稿失败: {str(e)}") from e
    