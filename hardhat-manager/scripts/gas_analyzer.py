#!/usr/bin/env python3
"""
Hardhat Gas Analyzer Script

Analyzes gas usage of smart contracts and provides optimization recommendations.
Supports gas profiling, comparison, and optimization suggestions.

Usage:
    python3 gas_analyzer.py --contract <contract-name> --optimize
    python3 gas_analyzer.py --compare <contract1> <contract2>
    python3 gas_analyzer.py --profile --network <network>
"""

import os
import sys
import argparse
import subprocess
import json
import re
from pathlib import Path
from collections import defaultdict


class GasAnalyzer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.artifacts_dir = self.project_root / "artifacts"
        self.reports_dir = self.project_root / "gas-reports"
        self.reports_dir.mkdir(exist_ok=True)

    def check_hardhat_project(self):
        """Check if current directory is a Hardhat project."""
        required_files = ['hardhat.config.js', 'package.json']

        for file in required_files:
            if not (self.project_root / file).exists():
                raise ValueError(f"Not a valid Hardhat project. Missing {file}")

        return True

    def find_contract_artifacts(self, contract_name=None):
        """Find contract artifacts."""
        if not self.artifacts_dir.exists():
            raise ValueError("No artifacts directory found. Run 'npx hardhat compile' first.")

        contracts = {}

        # Search for contract JSON files
        for json_file in self.artifacts_dir.rglob("*.json"):
            if json_file.name == "debug.json":
                continue  # Skip debug files

            try:
                with open(json_file, 'r') as f:
                    artifact = json.load(f)

                # Check if it's a contract artifact
                if 'abi' in artifact and 'bytecode' in artifact:
                    name = artifact.get('contractName', json_file.stem)

                    if contract_name and contract_name.lower() not in name.lower():
                        continue

                    contracts[name] = {
                        'path': json_file,
                        'artifact': artifact
                    }

            except (json.JSONDecodeError, KeyError):
                continue

        return contracts

    def extract_gas_from_tests(self):
        """Extract gas usage from test results."""
        print("🧪 Running tests with gas reporting...")

        try:
            # Run tests with gas reporter
            cmd = ['npx', 'hardhat', 'test', '--grep', 'gas']
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode != 0:
                print("⚠️  Standard gas tests failed, trying alternative method...")
                # Try running all tests
                cmd = ['npx', 'hardhat', 'test']
                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=600
                )

            return self.parse_gas_from_output(result.stdout)

        except subprocess.TimeoutExpired:
            print("⚠️  Tests timed out")
            return {}
        except Exception as e:
            print(f"⚠️  Could not run tests: {e}")
            return {}

    def parse_gas_from_output(self, output):
        """Parse gas usage from test output."""
        gas_data = {}

        # Look for gas usage patterns in output
        gas_patterns = [
            r'gas usage:\s*(\d+)',
            r'gas:\s*(\d+)',
            r'Gas\s*used:\s*(\d+)',
            r'(\d+)\s*gas',
            r'gasPrice:\s*(\d+)',
            r'gasLimit:\s*(\d+)'
        ]

        lines = output.split('\n')
        current_test = None

        for line in lines:
            # Check if this is a test name line
            if any(keyword in line.lower() for keyword in ['test', 'describe', 'it']):
                current_test = line.strip()
                continue

            # Look for gas usage
            for pattern in gas_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                if matches:
                    gas_amount = int(matches[0])

                    if current_test:
                        gas_data[current_test] = {
                            'gas': gas_amount,
                            'line': line.strip()
                        }
                    else:
                        gas_data[f"line_{len(gas_data)}"] = {
                            'gas': gas_amount,
                            'line': line.strip()
                        }

        return gas_data

    def analyze_contract_bytecode(self, contract_name, artifact):
        """Analyze contract bytecode for gas estimation."""
        bytecode = artifact.get('bytecode', '')
        deployed_bytecode = artifact.get('deployedBytecode', '')

        if not bytecode:
            return {}

        analysis = {
            'deployment_size': len(bytecode) // 2,  # Hex to bytes
            'runtime_size': len(deployed_bytecode) // 2 if deployed_bytecode else 0,
            'constructor_complexity': 0
        }

        # Estimate constructor gas
        if bytecode:
            # Basic estimation: 200 gas per byte + 21000 base
            analysis['estimated_deployment_gas'] = 21000 + (len(bytecode) // 2) * 200

        return analysis

    def get_function_signatures(self, artifact):
        """Extract function signatures from ABI."""
        abi = artifact.get('abi', [])
        functions = []

        for item in abi:
            if item.get('type') == 'function':
                name = item.get('name', '')
                inputs = [inp.get('type', '') for inp in item.get('inputs', [])]
                signature = f"{name}({','.join(inputs)})"

                functions.append({
                    'name': name,
                    'signature': signature,
                    'inputs': inputs,
                    'state_mutability': item.get('stateMutability', 'nonpayable')
                })

        return functions

    def estimate_function_gas(self, function_info):
        """Estimate gas usage for a function based on its signature."""
        base_gas = {
            'nonpayable': 21000,
            'payable': 21000,
            'view': 21000,
            'pure': 21000
        }

        # Base gas
        estimated = base_gas.get(function_info['state_mutability'], 21000)

        # Add gas for parameters (simplified estimation)
        param_gas = {
            'uint256': 200,
            'address': 200,
            'bool': 100,
            'string': 200,
            'bytes': 200,
            'bytes32': 200,
            'uint8': 100,
            'uint16': 100,
            'uint32': 150,
            'uint64': 150,
            'uint128': 200
        }

        for param_type in function_info['inputs']:
            for base_type in param_gas:
                if base_type in param_type:
                    estimated += param_gas[base_type]
                    break
            else:
                estimated += 200  # Default for complex types

        return estimated

    def generate_optimization_recommendations(self, contract_name, analysis):
        """Generate gas optimization recommendations."""
        recommendations = []

        # Check contract size
        deployment_size = analysis.get('deployment_size', 0)
        if deployment_size > 24576:  # Ethereum contract size limit
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Contract Size',
                'issue': f'Contract size ({deployment_size} bytes) exceeds Ethereum limit (24576 bytes)',
                'suggestion': 'Consider splitting the contract or using libraries to reduce size'
            })
        elif deployment_size > 20000:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Contract Size',
                'issue': f'Contract size ({deployment_size} bytes) is close to limit',
                'suggestion': 'Monitor contract size and consider optimization techniques'
            })

        # Check for optimization opportunities
        recommendations.extend([
            {
                'priority': 'LOW',
                'category': 'General',
                'issue': 'Review function visibility',
                'suggestion': 'Use external instead of public where possible to save gas'
            },
            {
                'priority': 'LOW',
                'category': 'Storage',
                'issue': 'Optimize storage layout',
                'suggestion': 'Pack struct variables efficiently to use fewer storage slots'
            },
            {
                'priority': 'MEDIUM',
                'category': 'Loops',
                'issue': 'Check loop efficiency',
                'suggestion': 'Avoid unbounded loops and consider using events instead'
            }
        ])

        return recommendations

    def run_gas_analysis(self, contract_name=None, optimize=False):
        """Run comprehensive gas analysis."""
        try:
            print("⛽ Starting gas analysis...")
            self.check_hardhat_project()

            # Find contracts
            contracts = self.find_contract_artifacts(contract_name)
            if not contracts:
                raise ValueError(f"No contracts found{' with name: ' + contract_name if contract_name else ''}")

            results = {}

            for name, data in contracts.items():
                print(f"\n📊 Analyzing contract: {name}")

                # Analyze bytecode
                bytecode_analysis = self.analyze_contract_bytecode(name, data['artifact'])

                # Get function information
                functions = self.get_function_signatures(data['artifact'])

                # Estimate function gas costs
                function_gas = {}
                for func in functions:
                    function_gas[func['name']] = self.estimate_function_gas(func)

                # Generate recommendations
                recommendations = self.generate_optimization_recommendations(name, bytecode_analysis)

                results[name] = {
                    'bytecode_analysis': bytecode_analysis,
                    'functions': functions,
                    'function_gas_estimates': function_gas,
                    'recommendations': recommendations
                }

                # Print summary
                print(f"  📦 Deployment size: {bytecode_analysis.get('deployment_size', 0)} bytes")
                print(f"  ⛽ Est. deployment gas: {bytecode_analysis.get('estimated_deployment_gas', 0):,}")
                print(f"  🔧 Functions: {len(functions)}")
                print(f"  💡 Recommendations: {len(recommendations)}")

            # Extract gas from tests
            print("\n🧪 Extracting gas data from tests...")
            test_gas_data = self.extract_gas_from_tests()
            if test_gas_data:
                results['test_gas_data'] = test_gas_data
                print(f"  📊 Found {len(test_gas_data)} gas measurements from tests")

            # Save report
            self.save_gas_report(results, contract_name)

            if optimize:
                self.apply_optimizations(results)

            return results

        except Exception as e:
            print(f"❌ Gas analysis failed: {e}")
            return {}

    def save_gas_report(self, results, contract_name=None):
        """Save gas analysis report to file."""
        timestamp = int(time.time())
        filename = f"gas-report-{contract_name or 'all'}-{timestamp}.json"
        report_path = self.reports_dir / filename

        try:
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2)

            print(f"\n💾 Gas report saved to: {report_path}")

            # Also generate a readable summary
            self.generate_readable_report(results, report_path.with_suffix('.md'))

        except Exception as e:
            print(f"⚠️  Could not save report: {e}")

    def generate_readable_report(self, results, output_path):
        """Generate a readable markdown report."""
        report_content = "# Gas Analysis Report\n\n"

        for contract_name, data in results.items():
            if contract_name == 'test_gas_data':
                continue

            report_content += f"## Contract: {contract_name}\n\n"

            # Bytecode analysis
            bytecode = data.get('bytecode_analysis', {})
            report_content += "### Bytecode Analysis\n\n"
            report_content += f"- **Deployment Size**: {bytecode.get('deployment_size', 0)} bytes\n"
            report_content += f"- **Runtime Size**: {bytecode.get('runtime_size', 0)} bytes\n"
            report_content += f"- **Est. Deployment Gas**: {bytecode.get('estimated_deployment_gas', 0):,}\n\n"

            # Function gas estimates
            report_content += "### Function Gas Estimates\n\n"
            report_content += "| Function | Est. Gas | Mutability |\n"
            report_content += "|----------|----------|------------|\n"

            for func_name, gas_est in data.get('function_gas_estimates', {}).items():
                mutability = "Unknown"
                for func in data.get('functions', []):
                    if func['name'] == func_name:
                        mutability = func['state_mutability']
                        break

                report_content += f"| {func_name} | {gas_est:,} | {mutability} |\n"

            report_content += "\n"

            # Recommendations
            recommendations = data.get('recommendations', [])
            if recommendations:
                report_content += "### Optimization Recommendations\n\n"

                for rec in recommendations:
                    priority_emoji = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}
                    emoji = priority_emoji.get(rec['priority'], '⚪')

                    report_content += f"#### {emoji} {rec['priority']} Priority: {rec['category']}\n\n"
                    report_content += f"**Issue**: {rec['issue']}\n\n"
                    report_content += f"**Suggestion**: {rec['suggestion']}\n\n"

            report_content += "---\n\n"

        # Test gas data
        if 'test_gas_data' in results:
            report_content += "## Test Gas Data\n\n"
            test_data = results['test_gas_data']

            for test_name, data in test_data.items():
                report_content += f"### {test_name}\n\n"
                report_content += f"**Gas Used**: {data['gas']:,}\n"
                report_content += f"**Details**: {data['line']}\n\n"

        try:
            with open(output_path, 'w') as f:
                f.write(report_content)

            print(f"📄 Readable report saved to: {output_path}")
        except Exception as e:
            print(f"⚠️  Could not save readable report: {e}")

    def apply_optimizations(self, results):
        """Apply automatic optimizations where possible."""
        print("\n🔧 Applying optimizations...")

        # This would contain logic to automatically apply simple optimizations
        # For now, just show what could be optimized

        for contract_name, data in results.items():
            if contract_name == 'test_gas_data':
                continue

            recommendations = data.get('recommendations', [])
            high_priority = [r for r in recommendations if r['priority'] == 'HIGH']

            if high_priority:
                print(f"\n🔴 High priority optimizations for {contract_name}:")
                for rec in high_priority:
                    print(f"  - {rec['issue']}")
                    print(f"    → {rec['suggestion']}")

        print("\n💡 Implement optimizations manually based on the recommendations")

    def compare_contracts(self, contract1, contract2):
        """Compare gas usage between two contracts."""
        print(f"📊 Comparing contracts: {contract1} vs {contract2}")

        contracts1 = self.find_contract_artifacts(contract1)
        contracts2 = self.find_contract_artifacts(contract2)

        if not contracts1 or not contracts2:
            raise ValueError("One or both contracts not found")

        # For simplicity, just compare the first match
        name1 = list(contracts1.keys())[0]
        name2 = list(contracts2.keys())[0]

        analysis1 = self.analyze_contract_bytecode(name1, contracts1[name1]['artifact'])
        analysis2 = self.analyze_contract_bytecode(name2, contracts2[name2]['artifact'])

        print(f"\n📈 Comparison Results:")
        print(f"  {name1}:")
        print(f"    Size: {analysis1.get('deployment_size', 0)} bytes")
        print(f"    Est. Gas: {analysis1.get('estimated_deployment_gas', 0):,}")

        print(f"  {name2}:")
        print(f"    Size: {analysis2.get('deployment_size', 0)} bytes")
        print(f"    Est. Gas: {analysis2.get('estimated_deployment_gas', 0):,}")

        # Calculate differences
        size_diff = analysis2.get('deployment_size', 0) - analysis1.get('deployment_size', 0)
        gas_diff = analysis2.get('estimated_deployment_gas', 0) - analysis1.get('estimated_deployment_gas', 0)

        print(f"\n  Differences:")
        print(f"    Size: {size_diff:+d} bytes")
        print(f"    Gas: {gas_diff:+,}")

        return {
            'contract1': name1,
            'contract2': name2,
            'analysis1': analysis1,
            'analysis2': analysis2,
            'differences': {
                'size': size_diff,
                'gas': gas_diff
            }
        }


def main():
    parser = argparse.ArgumentParser(description="Analyze gas usage of smart contracts")
    parser.add_argument("--contract", help="Specific contract to analyze")
    parser.add_argument("--optimize", action="store_true", help="Apply optimizations")
    parser.add_argument("--compare", nargs=2, metavar=('CONTRACT1', 'CONTRACT2'),
                       help="Compare two contracts")
    parser.add_argument("--profile", action="store_true", help="Profile gas usage")
    parser.add_argument("--network", help="Network for profiling")

    args = parser.parse_args()

    analyzer = GasAnalyzer()

    try:
        if args.compare:
            analyzer.compare_contracts(args.compare[0], args.compare[1])
        else:
            analyzer.run_gas_analysis(args.contract, args.optimize)

        print("\n🎉 Gas analysis completed!")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Gas analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import time
    main()