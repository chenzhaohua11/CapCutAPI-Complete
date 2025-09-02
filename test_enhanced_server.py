import requests
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    url = "http://127.0.0.1:5000"
    logger.info(f"向 {url}/health 发送单个请求...")
    
    try:
        response = requests.get(f"{url}/health")
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.json()}")
        if response.status_code == 200:
            logger.info("测试成功！")
        else:
            logger.error("测试失败！")
    except Exception as e:
        logger.error(f"请求失败: {str(e)}", exc_info=True)

if __name__ == '__main__':
    main()