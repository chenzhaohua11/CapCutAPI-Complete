#!/usr/bin/env python3
"""
一键测试运行器 - 精简版
支持快速运行所有测试用例
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """运行所有测试"""
    print("🧪 开始运行 CapCutAPI 测试...")
    
    # 检查pytest是否安装
    try:
        import pytest
    except ImportError:
        print("❌ pytest 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio", "pytest-cov"])
    
    # 运行测试
    cmd = [
        sys.executable, "-m", "pytest",
        "optimized_test_framework.py",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    # 如果有coverage，添加覆盖率报告
    try:
        import pytest_cov
        cmd.extend([
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:tests/coverage"
        ])
    except ImportError:
        pass
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查输出")
    
    return result.returncode

def run_specific_test(test_name):
    """运行特定测试"""
    print(f"🎯 运行特定测试: {test_name}")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "optimized_test_framework.py::" + test_name,
        "-v"
    ]
    
    result = subprocess.run(cmd)
    return result.returncode

def setup_test_env():
    """设置测试环境"""
    print("🔧 设置测试环境...")
    
    # 创建测试目录
    test_dirs = ["tests", "tests/coverage", "tests/fixtures"]
    for dir_path in test_dirs:
        Path(dir_path).mkdir(exist_ok=True)
    
    # 创建测试fixture
    fixture_content = '''{
  "test_video": {
    "path": "test.mp4",
    "width": 1080,
    "height": 1920,
    "duration": 10
  },
  "test_audio": {
    "path": "test.mp3",
    "duration": 5
  }
}'''
    
    with open("tests/fixtures/test_data.json", "w") as f:
        f.write(fixture_content)
    
    print("✅ 测试环境设置完成")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CapCutAPI 测试运行器")
    parser.add_argument("--setup", action="store_true", help="设置测试环境")
    parser.add_argument("--test", type=str, help="运行特定测试")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_test_env()
    elif args.test:
        sys.exit(run_specific_test(args.test))
    else:
        setup_test_env()
        sys.exit(run_tests())