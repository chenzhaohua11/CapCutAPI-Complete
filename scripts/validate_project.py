#!/usr/bin/env python3
"""
项目结构验证脚本
用于检查项目配置、依赖和文件结构的完整性
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any


class ProjectValidator:
    """项目验证器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.errors = []
        self.warnings = []
    
    def validate(self) -> bool:
        """执行所有验证"""
        print("🔍 开始验证项目结构...")
        
        validators = [
            self._check_required_files,
            self._check_python_version,
            self._check_dependencies,
            self._check_configuration,
            self._check_directory_structure,
            self._check_security_configs,
            self._check_documentation,
        ]
        
        for validator in validators:
            try:
                validator()
            except Exception as e:
                self.errors.append(f"验证器 {validator.__name__} 失败: {e}")
        
        self._print_results()
        return len(self.errors) == 0
    
    def _check_required_files(self):
        """检查必需文件"""
        required_files = [
            "pyproject.toml",
            "requirements-dev.txt",
            "Dockerfile",
            "docker-compose.yml",
            "pytest.ini",
            ".pre-commit-config.yaml",
            "SECURITY.md",
            "CONTRIBUTING.md",
            "README.md",
        ]
        
        for file_name in required_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                self.errors.append(f"缺少必需文件: {file_name}")
            else:
                print(f"✅ 找到文件: {file_name}")
    
    def _check_python_version(self):
        """检查Python版本"""
        version = sys.version_info
        if version < (3, 10):
            self.errors.append(f"Python版本过低: {version.major}.{version.minor}, 需要 >= 3.10")
        else:
            print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    
    def _check_dependencies(self):
        """检查依赖项"""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                config = tomllib.load(f)
            
            # 检查核心依赖
            deps = config.get("project", {}).get("dependencies", [])
            if not deps:
                self.warnings.append("未找到核心依赖项")
            
            # 检查可选依赖
            optional_deps = config.get("project", {}).get("optional-dependencies", {})
            if "dev" not in optional_deps:
                self.warnings.append("缺少开发依赖配置")
            if "mcp" not in optional_deps:
                self.warnings.append("缺少MCP依赖配置")
            
            print(f"✅ 依赖配置检查完成")
    
    def _check_configuration(self):
        """检查配置文件"""
        config_files = ["config.json", ".env"]
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                print(f"✅ 找到配置文件: {config_file}")
                
                if config_file.endswith('.json'):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            json.load(f)
                    except json.JSONDecodeError as e:
                        self.errors.append(f"配置文件 {config_file} JSON格式错误: {e}")
    
    def _check_directory_structure(self):
        """检查目录结构"""
        required_dirs = [
            "tests",
            "tests/unit",
            "tests/integration",
            "tests/e2e",
            "tests/fixtures",
            "scripts",
            "docs",
            "logs",
        ]
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.is_dir():
                print(f"✅ 找到目录: {dir_name}")
            else:
                self.warnings.append(f"缺少目录: {dir_name}")
    
    def _check_security_configs(self):
        """检查安全配置"""
        security_files = [
            "SECURITY.md",
            ".pre-commit-config.yaml",
            "Dockerfile",
        ]
        
        for file_name in security_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                print(f"✅ 找到安全配置: {file_name}")
                
                # 检查Dockerfile中的安全实践
                if file_name == "Dockerfile":
                    content = file_path.read_text(encoding='utf-8')
                    if "USER" not in content:
                        self.warnings.append("Dockerfile中未设置非root用户")
                    if "HEALTHCHECK" not in content:
                        self.warnings.append("Dockerfile中缺少健康检查")
    
    def _check_documentation(self):
        """检查文档完整性"""
        doc_files = ["README.md", "CONTRIBUTING.md"]
        
        for doc_file in doc_files:
            doc_path = self.project_root / doc_file
            if doc_path.exists():
                content = doc_path.read_text(encoding='utf-8')
                if len(content.strip()) < 100:
                    self.warnings.append(f"文档 {doc_file} 内容过于简短")
                else:
                    print(f"✅ 文档检查完成: {doc_file}")
    
    def _print_results(self):
        """打印验证结果"""
        print("\n" + "="*50)
        print("📊 验证结果:")
        
        if self.errors:
            print("❌ 错误:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("⚠️  警告:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("🎉 项目结构验证通过！")
        elif not self.errors:
            print("✅ 项目结构基本正确，但有需要改进的地方")
        else:
            print("❌ 项目结构存在问题，需要修复")
        
        print("="*50)


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    
    validator = ProjectValidator(project_root)
    success = validator.validate()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()