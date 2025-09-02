"""CapCut API 服务器启动脚本

简化版启动脚本，用于启动API服务器，提供环境检查和依赖验证。

功能：
- 环境检查：验证Python版本和工作目录
- 依赖检查：确保所有必要的模块和文件存在
- 配置加载：从环境变量和配置文件加载设置
- 服务器启动：启动CapCut API服务器

使用方法：
    python run_server.py [--debug] [--host HOST] [--port PORT]

参数：
    --debug     启用调试模式
    --host      指定主机地址，默认为0.0.0.0
    --port      指定端口号，默认为5000
"""

import os
import sys
import time
import logging
import argparse
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any

# 配置日志
def setup_logging(debug: bool = False) -> logging.Logger:
    """设置日志配置
    
    Args:
        debug: 是否启用调试模式
        
    Returns:
        配置好的日志记录器
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"capcut_api_{time.strftime('%Y%m%d')}.log"
    
    # 设置日志级别
    log_level = logging.DEBUG if debug else logging.INFO
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建处理器
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 创建应用日志记录器
    logger = logging.getLogger(__name__)
    logger.info(f"日志文件: {log_file}")
    
    return logger

# 初始化默认日志记录器
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def check_environment() -> Tuple[bool, List[str]]:
    """检查运行环境
    
    检查Python版本、操作系统和工作目录
    
    Returns:
        Tuple[bool, List[str]]: 检查结果和警告信息列表
    """
    warnings = []
    
    # 检查Python版本
    python_version = sys.version_info
    logger.info(f"Python版本: {sys.version}")
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        warnings.append(f"Python版本过低: {python_version.major}.{python_version.minor}, 推荐使用Python 3.7+")
    
    # 检查操作系统
    os_info = platform.platform()
    logger.info(f"操作系统: {os_info}")
    
    # 检查工作目录
    cwd = os.getcwd()
    logger.info(f"当前工作目录: {cwd}")
    
    # 检查是否在项目根目录
    if not os.path.exists(os.path.join(cwd, 'capcut_api.py')):
        warnings.append(f"当前目录可能不是项目根目录，未找到capcut_api.py")
    
    return len(warnings) == 0, warnings


def check_dependencies() -> Tuple[bool, List[str]]:
    """检查项目依赖
    
    检查必要的文件和Python模块
    
    Returns:
        Tuple[bool, List[str]]: 检查结果和错误信息列表
    """
    errors = []
    
    # 检查必要文件
    required_files = [
        'capcut_api.py', 
        'config.py', 
        'create_draft.py', 
        'media_processor.py',
        'utils.py'
    ]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        error_msg = f"缺少必要文件: {', '.join(missing_files)}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    # 检查必要模块
    required_modules = {
        'flask': "Flask框架",
        'werkzeug': "Werkzeug WSGI工具库",
        'requests': "HTTP请求库",
        'pillow': "图像处理库"
    }
    
    logger.info("检查必要模块...")
    for module_name, description in required_modules.items():
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', '未知')
            logger.info(f"{description} ({module_name}) 版本: {version}")
        except ImportError:
            error_msg = f"缺少{description} ({module_name})，请安装: pip install {module_name}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    return len(errors) == 0, errors


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description="CapCut API服务器启动脚本")
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=5000, help='服务器端口')
    parser.add_argument('--config', type=str, help='配置文件路径')
    
    return parser.parse_args()


def main() -> int:
    """主函数，启动服务器
    
    Returns:
        int: 退出代码，0表示成功，非0表示失败
    """
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 设置日志
        global logger
        logger = setup_logging(args.debug)
        
        # 打印启动信息
        logger.info("="*50)
        logger.info("CapCut API服务器启动中...")
        logger.info("="*50)
        
        # 检查环境
        logger.info("检查运行环境...")
        env_ok, warnings = check_environment()
        for warning in warnings:
            logger.warning(warning)
        
        # 检查依赖
        logger.info("检查项目依赖...")
        deps_ok, errors = check_dependencies()
        if not deps_ok:
            for error in errors:
                logger.error(error)
            logger.error("依赖检查失败，无法启动服务器")
            return 1
        
        # 构建启动命令
        cmd = [
            sys.executable,
            "capcut_api.py"
        ]
        
        if args.debug:
            cmd.append("--debug")
        
        cmd.extend(["--host", args.host])
        cmd.extend(["--port", str(args.port)])
        
        if args.config:
            cmd.extend(["--config", args.config])
        
        # 启动服务器
        logger.info(f"启动CapCut API服务器: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)
        
        # 等待服务器启动
        time.sleep(2)
        if process.poll() is not None:
            logger.error(f"服务器启动失败，退出代码: {process.returncode}")
            return process.returncode
        
        logger.info(f"服务器已启动，访问地址: http://{args.host}:{args.port}/")
        logger.info("按Ctrl+C停止服务器")
        
        # 等待服务器进程结束
        process.wait()
        return process.returncode
    
    except KeyboardInterrupt:
        logger.info("接收到中断信号，停止服务器")
        return 0
    except Exception as e:
        logger.exception(f"启动失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())