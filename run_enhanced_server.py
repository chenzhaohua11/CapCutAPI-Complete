"""增强版CapCut API服务器启动脚本

提供命令行参数支持，用于启动增强版CapCut API服务器。
支持配置主机、端口、调试模式等参数。

使用方法：
    python run_enhanced_server.py [选项]

选项：
    --host HOST       指定服务器主机地址，默认为0.0.0.0
    --port PORT       指定服务器端口，默认为5000
    --debug           启用调试模式
    --help            显示帮助信息
"""

import os
import sys
import argparse
import logging
from enhanced_server import app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'run_enhanced_server.log'))
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description='启动增强版CapCut API服务器')
    parser.add_argument('--host', default=os.environ.get('CAPCUT_HOST', '0.0.0.0'),
                        help='服务器主机地址，默认为0.0.0.0')
    parser.add_argument('--port', type=int, default=int(os.environ.get('CAPCUT_PORT', 5000)),
                        help='服务器端口，默认为5000')
    parser.add_argument('--debug', action='store_true',
                        help='启用调试模式')
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 设置环境变量
    os.environ['CAPCUT_HOST'] = args.host
    os.environ['CAPCUT_PORT'] = str(args.port)
    os.environ['CAPCUT_DEBUG'] = 'true' if args.debug else 'false'
    
    # 打印启动信息
    logger.info(f"启动增强版CapCut API服务器")
    logger.info(f"主机: {args.host}")
    logger.info(f"端口: {args.port}")
    logger.info(f"调试模式: {'启用' if args.debug else '禁用'}")
    
    # 启动服务器
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("接收到键盘中断，正在关闭服务器...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"启动服务器时发生错误: {str(e)}", exc_info=True)
        sys.exit(1)