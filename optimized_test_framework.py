"""
统一测试框架 - 精简优化版
整合所有测试用例到单一框架中
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试配置
TEST_CONFIG = {
    "temp_dir": tempfile.gettempdir(),
    "max_file_size": 1024 * 1024,  # 1MB for testing
    "timeout": 5
}

class TestBase:
    """测试基类"""
    
    @pytest.fixture
    def temp_dir(self):
        """临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def mock_draft(self):
        """模拟草稿对象"""
        mock = Mock()
        mock.width = 1080
        mock.height = 1920
        mock.add_video = Mock(return_value=True)
        mock.add_audio = Mock(return_value=True)
        mock.add_text = Mock(return_value=True)
        return mock

class TestDraftManager(TestBase):
    """草稿管理器测试"""
    
    def test_create_draft(self, temp_dir):
        """测试创建草稿"""
        from optimized_create_draft import draft_manager
        
        draft_id, script = draft_manager.create_draft(1080, 1920)
        
        assert draft_id.startswith("draft_")
        assert len(draft_id) > 10
        assert draft_id in draft_manager._cache
        assert len(draft_manager._access_order) == 1
    
    def test_get_or_create_draft_existing(self):
        """测试获取已存在的草稿"""
        from optimized_create_draft import draft_manager
        
        draft_id, script1 = draft_manager.create_draft()
        draft_id2, script2 = draft_manager.get_or_create_draft(draft_id)
        
        assert draft_id == draft_id2
        assert script1 is script2
    
    def test_cache_lru_behavior(self):
        """测试LRU缓存行为"""
        from optimized_create_draft import draft_manager
        
        # 设置小缓存大小
        draft_manager.max_cache_size = 2
        
        # 创建3个草稿，应该淘汰第一个
        id1, _ = draft_manager.create_draft()
        id2, _ = draft_manager.create_draft()
        id3, _ = draft_manager.create_draft()
        
        assert id1 not in draft_manager._cache
        assert id2 in draft_manager._cache
        assert id3 in draft_manager._cache
        assert len(draft_manager._cache) == 2
    
    def test_cache_stats(self):
        """测试缓存统计"""
        from optimized_create_draft import draft_manager
        
        draft_manager.create_draft()
        stats = draft_manager.cache_stats()
        
        assert stats["cached_items"] == 1
        assert stats["max_size"] == 1000

class TestConfigManager(TestBase):
    """配置管理器测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        from optimized_config import config
        
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 5000
        assert config.media.max_file_size == 100 * 1024 * 1024
    
    def test_env_override(self, monkeypatch):
        """测试环境变量覆盖"""
        monkeypatch.setenv("CAPCUT_PORT", "8080")
        monkeypatch.setenv("CAPCUT_DEBUG", "true")
        
        from optimized_config import config
        config._load_from_env()
        
        assert config.server.port == 8080
        assert config.server.debug is True
    
    def test_config_to_dict(self):
        """测试配置转字典"""
        from optimized_config import config
        
        config_dict = config.to_dict()
        assert "server" in config_dict
        assert "media" in config_dict
        assert config_dict["server"]["host"] == "0.0.0.0"

class TestUtils(TestBase):
    """工具函数测试"""
    
    def test_file_utils_save_load_json(self, temp_dir):
        """测试JSON文件读写"""
        from optimized_utils import FileUtils
        
        test_data = {"key": "value", "number": 123}
        filepath = os.path.join(temp_dir, "test.json")
        
        assert FileUtils.save_json(test_data, filepath) is True
        loaded_data = FileUtils.load_json(filepath)
        
        assert loaded_data == test_data
    
    def test_validation_utils_validate_media_params(self):
        """测试媒体参数验证"""
        from optimized_utils import ValidationUtils
        
        # 有效参数
        valid_params = {
            "timeline": {"start": 0, "duration": 10},
            "transform": {"scale": 1.0},
            "speed": 1.0
        }
        errors = ValidationUtils.validate_media_params(valid_params)
        assert len(errors) == 0
        
        # 无效参数
        invalid_params = {
            "timeline": {"start": -1, "duration": 0},
            "transform": {"scale": 0},
            "speed": -1
        }
        errors = ValidationUtils.validate_media_params(invalid_params)
        assert "start" in errors
        assert "duration" in errors
        assert "scale" in errors
        assert "speed" in errors
    
    def test_time_utils_format_duration(self):
        """测试时长格式化"""
        from optimized_utils import TimeUtils
        
        assert TimeUtils.format_duration(30.5) == "30.5s"
        assert TimeUtils.format_duration(90) == "1m 30s"
        assert TimeUtils.format_duration(3661) == "61m 1s"
    
    def test_response_utils(self):
        """测试响应工具"""
        from optimized_utils import ResponseUtils
        
        success = ResponseUtils.success({"data": "test"})
        assert success["code"] == 200
        assert success["success"] is True
        
        error = ResponseUtils.error("测试错误")
        assert error["code"] == 400
        assert error["success"] is False

class TestMediaHandler(TestBase):
    """媒体处理器测试"""
    
    def test_process_media_video(self, mock_draft):
        """测试视频处理"""
        from optimized_media_handler import MediaHandler
        
        handler = MediaHandler()
        params = {
            "type": "video",
            "path": "test.mp4",
            "timeline": {"start": 0, "duration": 10}
        }
        
        with patch('optimized_create_draft.draft_manager') as mock_manager:
            mock_manager.get_or_create_draft.return_value = ("test_id", mock_draft)
            result = handler.process_media(params)
            
            assert result is not None
            mock_draft.add_video.assert_called_once()
    
    def test_process_media_audio(self, mock_draft):
        """测试音频处理"""
        from optimized_media_handler import MediaHandler
        
        handler = MediaHandler()
        params = {
            "type": "audio",
            "path": "test.mp3",
            "timeline": {"start": 0, "duration": 5}
        }
        
        with patch('optimized_create_draft.draft_manager') as mock_manager:
            mock_manager.get_or_create_draft.return_value = ("test_id", mock_draft)
            result = handler.process_media(params)
            
            assert result is not None
            mock_draft.add_audio.assert_called_once()

class TestAsyncIntegration(TestBase):
    """异步集成测试"""
    
    @pytest.mark.asyncio
    async def test_async_media_processing(self):
        """测试异步媒体处理"""
        try:
            from optimized_modules.async_media_processor import AsyncMediaProcessor
            
            processor = AsyncMediaProcessor(max_concurrent=2)
            
            # 模拟异步任务
            async def mock_task():
                await asyncio.sleep(0.1)
                return {"status": "success"}
            
            result = await processor.process_media_async("test.mp4", mock_task)
            assert result is not None
            
        except ImportError:
            pytest.skip("异步模块未完全实现")

# 测试运行器
def run_tests():
    """运行所有测试"""
    pytest.main([
        "-v",
        "--tb=short",
        "--cov=.",
        "--cov-report=html:tests/coverage",
        "--cov-report=term-missing",
        __file__
    ])

if __name__ == "__main__":
    run_tests()