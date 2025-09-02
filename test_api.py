"""CapCut API 测试脚本
用于测试API服务器的基本功能
"""

import requests
import json
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API基础URL
BASE_URL = "http://localhost:5000"

def test_health_check():
    """测试健康检查端点"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"健康检查成功: {data}")
        return True
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return False

def test_create_draft():
    """测试创建草稿端点"""
    try:
        payload = {
            "width": 1080,
            "height": 1920
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/drafts",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"创建草稿成功: {data}")
        return data.get('draft_id')
    except Exception as e:
        logger.error(f"创建草稿失败: {str(e)}")
        return None

def test_get_draft(draft_id):
    """测试获取草稿信息端点"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/drafts/{draft_id}")
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"获取草稿信息成功: {data}")
        return True
    except Exception as e:
        logger.error(f"获取草稿信息失败: {str(e)}")
        return False

def test_add_media(draft_id):
    """测试添加媒体端点"""
    try:
        # 添加视频
        video_payload = {
            "type": "video",
            "media_url": "sample_video.mp4",
            "start_time": 0,
            "duration": 10
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/drafts/{draft_id}/media",
            json=video_payload
        )
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"添加视频成功: {data}")
        
        # 添加文本
        text_payload = {
            "type": "text",
            "text": "测试文本",
            "start_time": 2,
            "duration": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/drafts/{draft_id}/media",
            json=text_payload
        )
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"添加文本成功: {data}")
        
        return True
    except Exception as e:
        logger.error(f"添加媒体失败: {str(e)}")
        return False

def test_export_draft(draft_id):
    """测试导出草稿端点"""
    try:
        payload = {
            "format": "mp4",
            "output_path": f"output/test_export_{int(time.time())}.mp4"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/drafts/{draft_id}/export",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"导出草稿成功: {data}")
        return True
    except Exception as e:
        logger.error(f"导出草稿失败: {str(e)}")
        return False

def run_all_tests():
    """运行所有测试"""
    logger.info("开始测试CapCut API...")
    
    # 测试健康检查
    if not test_health_check():
        logger.error("健康检查测试失败，终止后续测试")
        return False
    
    # 测试创建草稿
    draft_id = test_create_draft()
    if not draft_id:
        logger.error("创建草稿测试失败，终止后续测试")
        return False
    
    # 测试获取草稿信息
    if not test_get_draft(draft_id):
        logger.error("获取草稿信息测试失败，终止后续测试")
        return False
    
    # 测试添加媒体
    if not test_add_media(draft_id):
        logger.error("添加媒体测试失败，终止后续测试")
        return False
    
    # 测试导出草稿
    if not test_export_draft(draft_id):
        logger.error("导出草稿测试失败")
        return False
    
    logger.info("所有测试通过！")
    return True

if __name__ == "__main__":
    run_all_tests()