#!/usr/bin/env python3
"""
智能合约扫描器
使用 Wake 系统进行基础安全扫描
"""

import os
import subprocess
import json
import argparse
from pathlib import Path

class ContractScanner:
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.config_file = self.project_path / "wake_audit_config.json"
        self.load_config()

    def load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = self.get_default_config()

    def get_default_config(self):
        """获取默认配置"""
        return {
            "audit_settings": {
                "scan_depth": "standard",
                "check_patterns": [
                    "reentrancy",
                    "access_control",
                    "integer_overflow",
                    "unchecked_call"
                ]
            }
        }

    def find_solidity_files(self):
        """查找项目中的 Solidity 文件"""
        solidity_files = []
        for pattern in ["**/*.sol", "**/*.vy"]:
            solidity_files.extend(self.project_path.rglob(pattern))
        return solidity_files

    def run_wake_analysis(self, contract_path):
        """运行 Wake 分析单个合约"""
        cmd = [
            'wake', 'analyze',
            str(contract_path),
            '--format', 'json',
            '--output', str(self.project_path / 'audit_results' / f'{contract_path.stem}_analysis.json')
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    def scan_contract(self, contract_path):
        """扫描单个合约"""
        print(f"🔍 正在扫描: {contract_path}")

        success, output = self.run_wake_analysis(contract_path)

        if success:
            print(f"✅ {contract_path.name} 扫描完成")
            return {"file": str(contract_path), "status": "success", "message": output}
        else:
            print(f"❌ {contract_path.name} 扫描失败: {output}")
            return {"file": str(contract_path), "status": "error", "message": output}

    def scan_project(self):
        """扫描整个项目"""
        print("🚀 开始项目扫描...")

        # 确保结果目录存在
        results_dir = self.project_path / 'audit_results'
        results_dir.mkdir(exist_ok=True)

        # 查找所有合约文件
        contracts = self.find_solidity_files()

        if not contracts:
            print("❌ 未找到 Solidity 合约文件")
            return []

        print(f"📁 找到 {len(contracts)} 个合约文件")

        # 扫描结果
        scan_results = []

        for contract in contracts:
            result = self.scan_contract(contract)
            scan_results.append(result)

        # 生成扫描报告
        self.generate_scan_report(scan_results)

        return scan_results

    def generate_scan_report(self, results):
        """生成扫描报告"""
        report = {
            "scan_summary": {
                "total_files": len(results),
                "successful_scans": len([r for r in results if r["status"] == "success"]),
                "failed_scans": len([r for r in results if r["status"] == "error"]),
                "timestamp": str(Path.cwd())
            },
            "scan_results": results
        }

        report_path = self.project_path / 'audit_results' / 'scan_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📊 扫描报告已生成: {report_path}")

        # 打印摘要
        print(f"\n📈 扫描摘要:")
        print(f"   总文件数: {report['scan_summary']['total_files']}")
        print(f"   成功扫描: {report['scan_summary']['successful_scans']}")
        print(f"   失败扫描: {report['scan_summary']['failed_scans']}")

def main():
    parser = argparse.ArgumentParser(description='Wake 智能合约扫描器')
    parser.add_argument('--path', default='.', help='项目路径 (默认: 当前目录)')
    parser.add_argument('--contract', help='扫描特定合约文件')

    args = parser.parse_args()

    scanner = ContractScanner(args.path)

    if args.contract:
        # 扫描单个合约
        contract_path = Path(args.contract)
        if contract_path.exists():
            scanner.scan_contract(contract_path)
        else:
            print(f"❌ 合约文件不存在: {contract_path}")
    else:
        # 扫描整个项目
        scanner.scan_project()

if __name__ == "__main__":
    main()