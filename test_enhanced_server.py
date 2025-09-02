"""增强版CapCut API服务器测试脚本

用于测试增强版服务器的性能监控功能。
该脚本会向服务器发送多个请求，并检查性能监控API的响应。

使用方法：
    python test_enhanced_server.py [选项]

选项：
    --host HOST       指定服务器主机地址，默认为localhost
    --port PORT       指定服务器端口，默认为5000
    --requests N      指定发送的请求数量，默认为100
    --concurrency N   指定并发请求数量，默认为10
    --help            显示帮助信息
"""

import os
import sys
import time
import json
import random
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List

import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'test_enhanced_server.log'))
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description='测试增强版CapCut API服务器')
    parser.add_argument('--host', default='localhost',
                        help='服务器主机地址，默认为localhost')
    parser.add_argument('--port', type=int, default=5000,
                        help='服务器端口，默认为5000')
    parser.add_argument('--requests', type=int, default=100,
                        help='发送的请求数量，默认为100')
    parser.add_argument('--concurrency', type=int, default=10,
                        help='并发请求数量，默认为10')
    return parser.parse_args()

def send_request(url: str, session: requests.Session, request_id: int) -> Dict[str, Any]:
    """发送请求到服务器
    
    Args:
        url (str): 请求URL
        session (requests.Session): 请求会话
        request_id (int): 请求ID
        
    Returns:
        Dict[str, Any]: 请求结果
    """
    start_time = time.time()
    try:
        # 随机选择请求类型
        request_type = random.choice(['echo', 'health', 'status', 'dashboard'])
        
        if request_type == 'echo':
            # 发送POST请求到/echo端点
            payload = {
                'request_id': request_id,
                'timestamp': time.time(),
                'data': f"测试数据 {request_id}",
                'random_value': random.randint(1, 1000)
            }
            response = session.post(f"{url}/echo", json=payload)
        elif request_type == 'health':
            # 发送GET请求到/health端点
            response = session.get(f"{url}/health")
        elif request_type == 'status':
            # 发送GET请求到/status端点
            response = session.get(f"{url}/status")
        else:  # dashboard
            # 发送GET请求到性能监控仪表板端点
            response = session.get(f"{url}/api/v1/performance/dashboard")
        
        # 计算请求时间
        elapsed_time = time.time() - start_time
        
        # 检查响应状态码
        if response.status_code == 200:
            return {
                'request_id': request_id,
                'request_type': request_type,
                'status': 'success',
                'status_code': response.status_code,
                'elapsed_time': elapsed_time,
                'response_size': len(response.text)
            }
        else:
            return {
                'request_id': request_id,
                'request_type': request_type,
                'status': 'error',
                'status_code': response.status_code,
                'elapsed_time': elapsed_time,
                'error': response.text[:100]  # 只取前100个字符
            }
    except Exception as e:
        # 计算请求时间
        elapsed_time = time.time() - start_time
        
        return {
            'request_id': request_id,
            'request_type': request_type if 'request_type' in locals() else 'unknown',
            'status': 'exception',
            'elapsed_time': elapsed_time,
            'error': str(e)
        }

def check_performance_api(url: str, session: requests.Session) -> Dict[str, Any]:
    """检查性能监控API
    
    Args:
        url (str): 服务器URL
        session (requests.Session): 请求会话
        
    Returns:
        Dict[str, Any]: 检查结果
    """
    results = {}
    
    # 检查性能监控API端点
    endpoints = [
        '/api/v1/performance/health',
        '/api/v1/performance/stats',
        '/api/v1/performance/dashboard',
        '/api/v1/performance/operations',
        '/api/v1/performance/alerts/thresholds',
        '/api/v1/performance/active-requests',
        '/api/v1/performance/slow-requests',
        '/api/v1/performance/resource-usage'
    ]
    
    for endpoint in endpoints:
        try:
            response = session.get(f"{url}{endpoint}")
            results[endpoint] = {
                'status_code': response.status_code,
                'status': 'success' if response.status_code == 200 else 'error',
                'response_size': len(response.text) if response.status_code == 200 else 0
            }
        except Exception as e:
            results[endpoint] = {
                'status': 'exception',
                'error': str(e)
            }
    
    return results

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 构建服务器URL
    url = f"http://{args.host}:{args.port}"
    
    logger.info(f"开始测试增强版CapCut API服务器: {url}")
    logger.info(f"请求数量: {args.requests}")
    logger.info(f"并发请求数量: {args.concurrency}")
    
    # 创建会话
    session = requests.Session()
    
    # 检查服务器是否在线
    try:
        response = session.get(f"{url}/health")
        if response.status_code != 200:
            logger.error(f"服务器未正常响应，状态码: {response.status_code}")
            return
        logger.info("服务器在线，开始测试")
    except Exception as e:
        logger.error(f"无法连接到服务器: {str(e)}")
        return
    
    # 发送请求
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(send_request, url, session, i) for i in range(args.requests)]
        for future in futures:
            results.append(future.result())
    
    # 计算总耗时
    total_time = time.time() - start_time
    
    # 统计结果
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = sum(1 for r in results if r['status'] == 'error')
    exception_count = sum(1 for r in results if r['status'] == 'exception')
    
    # 计算平均响应时间
    avg_time = sum(r['elapsed_time'] for r in results) / len(results) if results else 0
    
    # 按请求类型分组
    by_type = {}
    for r in results:
        request_type = r.get('request_type', 'unknown')
        if request_type not in by_type:
            by_type[request_type] = []
        by_type[request_type].append(r)
    
    # 输出结果摘要
    logger.info("测试完成，结果摘要:")
    logger.info(f"总请求数: {len(results)}")
    logger.info(f"成功请求数: {success_count}")
    logger.info(f"错误请求数: {error_count}")
    logger.info(f"异常请求数: {exception_count}")
    logger.info(f"总耗时: {total_time:.2f}秒")
    logger.info(f"平均响应时间: {avg_time*1000:.2f}毫秒")
    logger.info(f"请求吞吐量: {len(results)/total_time:.2f}请求/秒")
    
    # 输出按请求类型的统计
    logger.info("按请求类型统计:")
    for request_type, type_results in by_type.items():
        type_count = len(type_results)
        type_success = sum(1 for r in type_results if r['status'] == 'success')
        type_avg_time = sum(r['elapsed_time'] for r in type_results) / type_count if type_count else 0
        logger.info(f"  {request_type}: 总数={type_count}, 成功率={type_success/type_count*100:.1f}%, 平均响应时间={type_avg_time*1000:.2f}毫秒")
    
    # 检查性能监控API
    logger.info("检查性能监控API:")
    api_results = check_performance_api(url, session)
    
    for endpoint, result in api_results.items():
        status = result.get('status', 'unknown')
        if status == 'success':
            logger.info(f"  {endpoint}: 状态码={result['status_code']}, 响应大小={result['response_size']}字节")
        else:
            logger.info(f"  {endpoint}: {status}, 错误={result.get('error', 'unknown')}")
    
    # 保存详细结果到文件
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_requests': len(results),
                'success_count': success_count,
                'error_count': error_count,
                'exception_count': exception_count,
                'total_time': total_time,
                'avg_response_time': avg_time,
                'throughput': len(results)/total_time
            },
            'by_type': {k: [r for r in v if r['status'] == 'success'][:5] for k, v in by_type.items()},
            'performance_api': api_results
        }, f, indent=2, ensure_ascii=False)
    
    logger.info("详细结果已保存到test_results.json")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}", exc_info=True)
        sys.exit(1)