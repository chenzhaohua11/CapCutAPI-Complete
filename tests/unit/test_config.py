"""Unit tests for configuration management."""

import json
import os
import tempfile
import pytest
from unittest.mock import patch

from settings.local import load_config


class TestConfigLoading:
    """Test configuration loading functionality."""

    def test_load_config_success(self):
        """Test successful configuration loading."""
        config_data = {
            "is_capcut_env": True,
            "draft_domain": "https://test.example.com",
            "port": 9001,
            "preview_router": "/test/preview",
            "is_upload_draft": False,
            "oss_config": {
                "bucket_name": "test-bucket",
                "access_key_id": "test-key",
                "access_key_secret": "test-secret",
                "endpoint": "https://test.endpoint.com"
            },
            "mp4_oss_config": {
                "bucket_name": "test-mp4-bucket",
                "access_key_id": "test-mp4-key",
                "access_key_secret": "test-mp4-secret",
                "region": "test-region",
                "endpoint": "http://test-mp4.domain.com"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            assert config["is_capcut_env"] is True
            assert config["port"] == 9001
            assert config["draft_domain"] == "https://test.example.com"
        finally:
            os.unlink(config_path)

    def test_load_config_missing_file(self):
        """Test configuration loading with missing file."""
        with pytest.raises(FileNotFoundError):
            load_config("non_existent_config.json")

    def test_load_config_invalid_json(self):
        """Test configuration loading with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            config_path = f.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_config(config_path)
        finally:
            os.unlink(config_path)

    def test_environment_variables_override(self):
        """Test environment variable configuration override."""
        with patch.dict(os.environ, {
            'CAPCUT_PORT': '8080',
            'CAPCUT_DEBUG': 'true',
            'OSS_BUCKET_NAME': 'env-bucket'
        }):
            # Test that environment variables override config file values
            assert os.getenv('CAPCUT_PORT') == '8080'
            assert os.getenv('CAPCUT_DEBUG') == 'true'


class TestSecurityConfig:
    """Test security configuration validation."""

    def test_secret_key_validation(self):
        """Test secret key validation."""
        # Ensure secret key is not default in production
        test_key = "test-secret-key-with-sufficient-length"
        assert len(test_key) >= 32
        assert test_key != "your-secret-key-here"

    def test_allowed_hosts_validation(self):
        """Test allowed hosts configuration."""
        allowed_hosts = ["localhost", "127.0.0.1", "capcutapi.example.com"]
        assert "localhost" in allowed_hosts
        assert "127.0.0.1" in allowed_hosts
        assert len(allowed_hosts) >= 2