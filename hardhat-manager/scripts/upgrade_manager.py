#!/usr/bin/env python3
"""
Hardhat Contract Upgrade Manager

Manages upgrades for upgradeable smart contracts using OpenZeppelin.
Supports proxy patterns, implementation upgrades, and storage compatibility checks.

Usage:
    python3 upgrade_manager.py --contract <contract-name> --new-implementation <address>
    python3 upgrade_manager.py --check-compatibility <old-impl> <new-impl>
    python3 upgrade_manager.py --deploy-upgradeable --contract <contract-name>
"""

import os
import sys
import argparse
import subprocess
import json
import time
from pathlib import Path


class UpgradeManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.deployments_dir = self.project_root / "deployments"
        self.deployments_dir.mkdir(exist_ok=True)
        self.upgrades_dir = self.project_root / "upgrades"
        self.upgrades_dir.mkdir(exist_ok=True)

    def check_hardhat_project(self):
        """Check if current directory is a Hardhat project with OpenZeppelin."""
        required_files = ['hardhat.config.js', 'package.json']

        for file in required_files:
            if not (self.project_root / file).exists():
                raise ValueError(f"Not a valid Hardhat project. Missing {file}")

        # Check for OpenZeppelin contracts
        package_json = self.project_root / "package.json"
        with open(package_json, 'r') as f:
            package_data = json.load(f)

        dependencies = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}

        oz_contracts = '@openzeppelin/contracts'
        oz_upgrades = '@openzeppelin/contracts-upgradeable'
        oz_hardhat = '@openzeppelin/hardhat-upgrades'

        if oz_contracts not in dependencies:
            print("⚠️  Warning: OpenZeppelin contracts not found. Install with:")
            print("   npm install @openzeppelin/contracts")

        if oz_upgrades not in dependencies:
            print("⚠️  Warning: OpenZeppelin upgradeable contracts not found. Install with:")
            print("   npm install @openzeppelin/contracts-upgradeable")

        if oz_hardhat not in dependencies:
            print("⚠️  Warning: OpenZeppelin Hardhat upgrades not found. Install with:")
            print("   npm install --save-dev @openzeppelin/hardhat-upgrades")

        return True

    def find_proxy_deployments(self):
        """Find existing proxy deployments."""
        deployments = {}

        # Look for deployment files that might contain proxy information
        for deployment_file in self.deployments_dir.rglob("*.json"):
            try:
                with open(deployment_file, 'r') as f:
                    data = json.load(f)

                # Look for proxy-related information
                if 'proxies' in data or 'proxy' in data:
                    network = deployment_file.stem.replace('-deployment', '')
                    deployments[network] = data

            except (json.JSONDecodeError, KeyError):
                continue

        return deployments

    def check_upgradeability(self, contract_name):
        """Check if a contract is upgradeable."""
        contracts_dir = self.project_root / "contracts"

        if not contracts_dir.exists():
            return False

        # Look for contract files
        contract_files = list(contracts_dir.rglob(f"{contract_name}.sol"))

        if not contract_files:
            return False

        # Check contract content for upgradeability patterns
        for contract_file in contract_files:
            with open(contract_file, 'r') as f:
                content = f.read()

            # Look for upgradeable patterns
            upgradeable_patterns = [
                '@openzeppelin/contracts-upgradeable',
                'Initializable',
                'UUPSUpgradeable',
                'TransparentUpgradeableProxy'
            ]

            for pattern in upgradeable_patterns:
                if pattern in content:
                    return True

        return False

    def validate_address(self, address):
        """Validate Ethereum address format."""
        if not address.startswith('0x') or len(address) != 42:
            raise ValueError("Invalid Ethereum address format")

        try:
            int(address, 16)
            return True
        except ValueError:
            raise ValueError("Invalid Ethereum address")

    def check_storage_compatibility(self, old_impl_address, new_impl_address, network):
        """Check storage compatibility between implementations."""
        try:
            print(f"🔍 Checking storage compatibility between {old_impl_address} and {new_impl_address}")

            # Use OpenZeppelin's upgradeability checker
            cmd = ['npx', 'hardhat', 'validate-upgrade',
                   f'{old_impl_address} {new_impl_address}',
                   '--network', network]

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                print("✅ Storage layouts are compatible!")
                return True
            else:
                print("❌ Storage compatibility issues found:")
                print(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print("❌ Compatibility check timed out")
            return False
        except Exception as e:
            print(f"❌ Compatibility check failed: {e}")
            return False

    def deploy_upgradeable_contract(self, contract_name, network, initializer_args=None):
        """Deploy a new upgradeable contract."""
        try:
            print(f"🚀 Deploying upgradeable contract {contract_name} to {network}")

            if not self.check_upgradeability(contract_name):
                raise ValueError(f"Contract {contract_name} is not upgradeable")

            # Find deployment script
            deploy_script = self.project_root / "scripts" / f"deploy-{contract_name.lower()}.js"
            if not deploy_script.exists():
                deploy_script = self.project_root / "scripts" / "deploy-upgradeable.js"

            if not deploy_script.exists():
                raise Exception("No deployment script found for upgradeable contract")

            # Deploy using Hardhat
            cmd = ['npx', 'hardhat', 'run', str(deploy_script), '--network', network]

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                print("✅ Upgradeable contract deployed successfully!")
                print("📋 Deployment output:")
                print(result.stdout)

                # Extract deployment info
                deployment_info = self.extract_deployment_info(result.stdout)
                self.save_upgrade_info(contract_name, network, deployment_info, 'deploy')

                return deployment_info
            else:
                print(f"❌ Deployment failed: {result.stderr}")
                return None

        except Exception as e:
            print(f"❌ Upgradeable deployment failed: {e}")
            return None

    def upgrade_implementation(self, contract_name, new_impl_address, network):
        """Upgrade contract implementation."""
        try:
            print(f"🔧 Upgrading {contract_name} to new implementation {new_impl_address}")

            self.validate_address(new_impl_address)

            # Find existing proxy
            proxy_info = self.find_proxy_for_contract(contract_name, network)
            if not proxy_info:
                raise ValueError(f"No proxy found for {contract_name} on {network}")

            proxy_address = proxy_info['address']

            # Check compatibility
            old_impl_address = proxy_info.get('implementation')
            if old_impl_address:
                if not self.check_storage_compatibility(old_impl_address, new_impl_address, network):
                    response = input("⚠️  Storage compatibility issues found. Continue anyway? (y/N): ")
                    if response.lower() != 'y':
                        print("❌ Upgrade cancelled")
                        return None

            # Perform upgrade
            cmd = ['npx', 'hardhat', 'upgrade',
                   f'{proxy_address} {new_impl_address}',
                   '--network', network]

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                print("✅ Contract upgraded successfully!")
                print("📋 Upgrade output:")
                print(result.stdout)

                # Save upgrade info
                upgrade_info = {
                    'proxy_address': proxy_address,
                    'old_implementation': old_impl_address,
                    'new_implementation': new_impl_address,
                    'network': network,
                    'timestamp': time.time(),
                    'output': result.stdout
                }

                self.save_upgrade_info(contract_name, network, upgrade_info, 'upgrade')
                return upgrade_info
            else:
                print(f"❌ Upgrade failed: {result.stderr}")
                return None

        except Exception as e:
            print(f"❌ Upgrade failed: {e}")
            return None

    def find_proxy_for_contract(self, contract_name, network):
        """Find proxy address for a contract."""
        deployment_file = self.deployments_dir / f"{network}-deployment.json"

        if not deployment_file.exists():
            return None

        try:
            with open(deployment_file, 'r') as f:
                data = json.load(f)

            # Look for proxy information
            contracts = data.get('contracts', {})

            for contract, info in contracts.items():
                if contract_name.lower() in contract.lower():
                    if 'proxy' in info or 'Proxy' in contract:
                        return {
                            'address': info if isinstance(info, str) else info.get('address'),
                            'implementation': info.get('implementation') if isinstance(info, dict) else None
                        }

        except (json.JSONDecodeError, KeyError):
            pass

        return None

    def extract_deployment_info(self, output):
        """Extract deployment information from output."""
        info = {}
        lines = output.split('\n')

        for line in lines:
            if 'deployed to' in line.lower() or 'contract address' in line.lower():
                import re
                address_pattern = r'0x[a-fA-F0-9]{40}'
                matches = re.findall(address_pattern, line)

                if matches:
                    info['address'] = matches[0]

        return info

    def save_upgrade_info(self, contract_name, network, info, action_type):
        """Save upgrade information."""
        upgrade_file = self.upgrades_dir / f"{contract_name}-{network}-upgrades.json"

        try:
            # Load existing upgrades
            upgrades = []
            if upgrade_file.exists():
                with open(upgrade_file, 'r') as f:
                    upgrades = json.load(f)

            # Add new upgrade
            info['action'] = action_type
            info['contract_name'] = contract_name
            info['network'] = network
            info['timestamp'] = time.time()

            upgrades.append(info)

            # Save updated list
            with open(upgrade_file, 'w') as f:
                json.dump(upgrades, f, indent=2)

            print(f"💾 Upgrade info saved to {upgrade_file}")

        except Exception as e:
            print(f"⚠️  Could not save upgrade info: {e}")

    def list_upgrades(self, contract_name=None, network=None):
        """List upgrade history."""
        print("📋 Upgrade History:")

        for upgrade_file in self.upgrades_dir.rglob("*.json"):
            try:
                with open(upgrade_file, 'r') as f:
                    upgrades = json.load(f)

                for upgrade in upgrades:
                    if contract_name and contract_name.lower() not in upgrade.get('contract_name', '').lower():
                        continue
                    if network and network.lower() not in upgrade.get('network', '').lower():
                        continue

                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(upgrade['timestamp']))
                    action = upgrade.get('action', 'unknown')

                    print(f"\n  {action.upper()}: {upgrade.get('contract_name', 'Unknown')}")
                    print(f"    Network: {upgrade.get('network', 'Unknown')}")
                    print(f"    Time: {timestamp}")

                    if action == 'upgrade':
                        print(f"    Proxy: {upgrade.get('proxy_address', 'Unknown')}")
                        print(f"    Old Impl: {upgrade.get('old_implementation', 'Unknown')}")
                        print(f"    New Impl: {upgrade.get('new_implementation', 'Unknown')}")
                    elif action == 'deploy':
                        print(f"    Address: {upgrade.get('address', 'Unknown')}")

            except (json.JSONDecodeError, KeyError):
                continue

    def validate_contract_upgrade(self, old_impl, new_impl, network):
        """Validate that an upgrade is safe."""
        try:
            print(f"🔍 Validating upgrade safety...")

            # Check addresses
            self.validate_address(old_impl)
            self.validate_address(new_impl)

            # Check storage compatibility
            compatible = self.check_storage_compatibility(old_impl, new_impl, network)

            if compatible:
                print("✅ Upgrade appears safe!")
                return True
            else:
                print("⚠️  Upgrade has potential issues")
                return False

        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False

    def manage_upgrade(self, contract_name, new_impl_address=None, network='localhost',
                      deploy_upgradeable=False, check_compatibility=None):
        """Main upgrade management function."""
        try:
            self.check_hardhat_project()

            if deploy_upgradeable:
                return self.deploy_upgradeable_contract(contract_name, network)
            elif check_compatibility:
                return self.validate_contract_upgrade(check_compatibility[0], check_compatibility[1], network)
            elif new_impl_address:
                return self.upgrade_implementation(contract_name, new_impl_address, network)
            else:
                self.list_upgrades(contract_name, network)
                return True

        except Exception as e:
            print(f"❌ Upgrade management failed: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Manage contract upgrades")
    parser.add_argument("--contract", required=False, help="Contract name")
    parser.add_argument("--new-implementation", help="New implementation address")
    parser.add_argument("--network", default="localhost", help="Target network")
    parser.add_argument("--deploy-upgradeable", action="store_true",
                       help="Deploy new upgradeable contract")
    parser.add_argument("--check-compatibility", nargs=2, metavar=('OLD_IMPL', 'NEW_IMPL'),
                       help="Check storage compatibility between implementations")
    parser.add_argument("--list-upgrades", action="store_true",
                       help="List upgrade history")

    args = parser.parse_args()

    manager = UpgradeManager()

    try:
        success = manager.manage_upgrade(
            contract_name=args.contract,
            new_impl_address=args.new_implementation,
            network=args.network,
            deploy_upgradeable=args.deploy_upgradeable,
            check_compatibility=args.check_compatibility
        )

        if success:
            print("\n🎉 Upgrade operation completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Upgrade operation failed!")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Upgrade operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()