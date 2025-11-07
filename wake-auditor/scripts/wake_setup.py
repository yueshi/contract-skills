#!/usr/bin/env python3
"""
Wake 环境设置和初始化脚本
用于配置 Wake Printer 审计环境
"""

import os
import subprocess
import json
from pathlib import Path

def check_wake_installation():
    """检查 Wake 是否已安装"""
    try:
        result = subprocess.run(['wake', '--version'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Wake 已安装: {result.stdout.strip()}")
            return True
        else:
            print("❌ Wake 未安装或无法访问")
            return False
    except FileNotFoundError:
        print("❌ Wake 命令未找到")
        return False

def install_wake():
    """安装 Wake 工具"""
    print("正在安装 Wake...")
    try:
        # 假设通过 pip 安装
        subprocess.run(['pip', 'install', 'py-wake'], check=True)
        print("✅ Wake 安装完成")
        return True
    except subprocess.CalledProcessError:
        print("❌ Wake 安装失败，请手动安装")
        return False

def setup_project_structure(project_path):
    """设置项目审计结构"""
    project = Path(project_path)

    # 创建必要的目录
    dirs_to_create = [
        'audit_results',
        'custom_printers',
        'reports',
        'contracts_analysis'
    ]

    for dir_name in dirs_to_create:
        dir_path = project / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"✅ 创建目录: {dir_path}")

def create_config_file(project_path):
    """创建审计配置文件"""
    config = {
        "audit_settings": {
            "scan_depth": "deep",
            "check_patterns": [
                "reentrancy",
                "access_control",
                "integer_overflow",
                "unchecked_call",
                "logic_vulnerabilities"
            ],
            "output_formats": ["json", "html", "markdown"],
            "exclude_patterns": ["test/", "mock/"]
        },
        "wake_config": {
            "solc_version": "auto",
            "optimizer_enabled": True,
            "evm_version": "paris"
        }
    }

    config_path = Path(project_path) / "wake_audit_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✅ 配置文件已创建: {config_path}")

def main():
    """主函数"""
    print("🔍 Wake Auditor 环境设置")
    print("=" * 40)

    # 检查当前目录
    current_dir = Path.cwd()
    print(f"当前工作目录: {current_dir}")

    # 检查 Wake 安装
    if not check_wake_installation():
        install_choice = input("是否尝试自动安装 Wake? (y/n): ")
        if install_choice.lower() == 'y':
            if not install_wake():
                return

    # 设置项目结构
    setup_project_structure(current_dir)

    # 创建配置文件
    create_config_file(current_dir)

    print("\n🎉 Wake Auditor 环境设置完成!")
    print("你现在可以开始使用 Wake 进行智能合约审计了。")

if __name__ == "__main__":
    main()