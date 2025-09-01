"""
项目清理和优化脚本
用于移除冗余文件并整合项目结构
"""

import os
import shutil
from pathlib import Path
import sys

def backup_file(filepath):
    """备份文件"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup"
        shutil.copy2(filepath, backup_path)
        print(f"已备份: {filepath} -> {backup_path}")

def remove_redundant_files():
    """移除冗余文件"""
    redundant_patterns = [
        "draft_cache.py",
        "local.py",
        "config.py",
        "utils.py",
        "file_utils.py",
        "validation_utils.py",
        "time_utils.py",
        "response_utils.py",
        "cache_utils.py",
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".pytest_cache"
    ]
    
    for pattern in redundant_patterns:
        if pattern.startswith('*'):
            for file in Path('.').glob(pattern):
                if file.is_file():
                    backup_file(str(file))
                    file.unlink()
                    print(f"已删除: {file}")
        else:
            if os.path.exists(pattern):
                backup_file(pattern)
                if os.path.isfile(pattern):
                    os.remove(pattern)
                else:
                    shutil.rmtree(pattern)
                print(f"已删除: {pattern}")

def create_optimized_structure():
    """创建优化后的目录结构"""
    directories = [
        "optimized_modules",
        "config",
        "tests",
        "logs",
        "temp"
    ]
    
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"已创建目录: {dir_name}")

def move_optimized_files():
    """移动优化后的文件"""
    moves = [
        ("optimized_create_draft.py", "optimized_modules/create_draft.py"),
        ("optimized_config.py", "config/config.py"),
        ("optimized_utils.py", "optimized_modules/utils.py"),
        ("optimized_requirements.txt", "requirements.txt"),
    ]
    
    for src, dst in moves:
        if os.path.exists(src):
            backup_file(dst)
            shutil.move(src, dst)
            print(f"已移动: {src} -> {dst}")

def main():
    """主函数"""
    print("=== CapCutAPI 项目清理和优化 ===")
    
    # 确认操作
    response = input("此操作将备份并移除冗余文件，是否继续？(y/N): ")
    if response.lower() != 'y':
        print("操作已取消")
        return
    
    try:
        print("\n1. 移除冗余文件...")
        remove_redundant_files()
        
        print("\n2. 创建优化目录结构...")
        create_optimized_structure()
        
        print("\n3. 移动优化文件...")
        move_optimized_files()
        
        print("\n4. 清理完成！")
        print("\n下一步建议：")
        print("- 运行: pip install -r requirements.txt")
        print("- 测试: python -m pytest tests/")
        print("- 启动: python optimized_capcut_server.py")
        
    except Exception as e:
        print(f"清理过程中出现错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()