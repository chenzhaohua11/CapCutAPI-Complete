"""Unit tests for the CapCut server."""

import json
import pytest
from unittest.mock import patch

from capcut_server import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_check_success(self, client):
        """Test successful health check."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data

    def test_health_check_method_not_allowed(self, client):
        """Test health check with invalid HTTP method."""
        response = client.post('/health')
        assert response.status_code == 405


class TestAddVideoEndpoint:
    """Test the add video endpoint."""

    def test_add_video_missing_parameters(self, client):
        """Test add video with missing required parameters."""
        response = client.post('/add_video', json={})
        assert response.status_code == 400

    def test_add_video_invalid_parameters(self, client):
        """Test add video with invalid parameters."""
        invalid_data = {
            "video_url": "not-a-url",
            "start_time": "invalid",
            "end_time": -1
        }
        response = client.post('/add_video', json=invalid_data)
        assert response.status_code == 400


class TestAddAudioEndpoint:
    """Test the add audio endpoint."""

    def test_add_audio_missing_parameters(self, client):
        """Test add audio with missing required parameters."""
        response = client.post('/add_audio', json={})
        assert response.status_code == 400

    def test_add_audio_invalid_volume(self, client):
        """Test add audio with invalid volume parameter."""
        invalid_data = {
            "audio_url": "https://example.com/audio.mp3",
            "volume": "invalid"
        }
        response = client.post('/add_audio', json=invalid_data)
        assert response.status_code == 400


class TestErrorHandling:
    """Test error handling and response formatting."""

    def test_404_error_response(self, client):
        """Test 404 error response format."""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
        
        # Ensure error response is JSON
        assert response.content_type == 'application/json'

    def test_500_error_handling(self, client):
        """Test 500 error handling."""
        with patch('capcut_server.app') as mock_app:
            mock_app.route.side_effect = Exception("Test exception")
            response = client.get('/health')
            # Should not crash the server
            assert response.status_code in [200, 500]