#!/usr/bin/env python3
"""
Hardhat Contract Deployment Script

Automates the deployment of smart contracts to various networks with optional verification.
Supports gas price optimization, deployment confirmation, and verification.

Usage:
    python3 deploy_contracts.py --network <network-name> --verify --gas-price <auto|fast|standard>

Examples:
    python3 deploy_contracts.py --network ethereum --verify --gas-price auto
    python3 deploy_contracts.py --network polygon --confirm
    python3 deploy_contracts.py --network localhost --gas-price standard
"""

import os
import sys
import argparse
import subprocess
import json
import time
from pathlib import Path


class ContractDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.deployments_dir = self.project_root / "deployments"
        self.deployments_dir.mkdir(exist_ok=True)

    def validate_network(self, network):
        """Validate network configuration."""
        supported_networks = [
            'ethereum', 'polygon', 'arbitrum', 'optimism', 'bsc',
            'goerli', 'sepolia', 'mumbai', 'localhost', 'hardhat'
        ]

        if network.lower() not in supported_networks:
            raise ValueError(f"Network '{network}' not supported. Supported networks: {supported_networks}")

        return network.lower()

    def check_hardhat_project(self):
        """Check if current directory is a Hardhat project."""
        required_files = ['hardhat.config.js', 'package.json']

        for file in required_files:
            if not (self.project_root / file).exists():
                raise ValueError(f"Not a valid Hardhat project. Missing {file}")

        return True

    def load_hardhat_config(self):
        """Load Hardhat configuration to extract contract information."""
        try:
            # Check if contracts exist
            contracts_dir = self.project_root / "contracts"
            if not contracts_dir.exists():
                raise ValueError("No contracts directory found")

            # Get contract files
            contract_files = list(contracts_dir.rglob("*.sol"))
            if not contract_files:
                raise ValueError("No Solidity contracts found")

            return contract_files

        except Exception as e:
            print(f"⚠️  Warning: Could not load contract information: {e}")
            return []

    def compile_contracts(self):
        """Compile contracts before deployment."""
        print("🔨 Compiling contracts...")

        try:
            result = subprocess.run(
                ['npx', 'hardhat', 'compile'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                print("✅ Contracts compiled successfully")
                return True
            else:
                print(f"❌ Compilation failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Compilation timed out")
            return False
        except FileNotFoundError:
            print("❌ npx or hardhat not found")
            return False

    def run_tests(self, skip_tests=False):
        """Run tests before deployment."""
        if skip_tests:
            print("⏭️  Skipping tests as requested")
            return True

        print("🧪 Running tests...")

        try:
            result = subprocess.run(
                ['npx', 'hardhat', 'test'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                print("✅ All tests passed")
                return True
            else:
                print(f"❌ Some tests failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Tests timed out")
            return False

    def get_gas_price(self, gas_option):
        """Get gas price based on option."""
        gas_prices = {
            'auto': None,  # Let Hardhat decide
            'fast': '20000000000',  # 20 gwei
            'standard': '15000000000',  # 15 gwei
            'slow': '10000000000'  # 10 gwei
        }

        return gas_prices.get(gas_option, None)

    def deploy_contracts(self, network, verify=False, gas_price_option='auto', confirm=False):
        """Deploy contracts to specified network."""
        try:
            print(f"🚀 Deploying contracts to {network}...")

            # Check Hardhat project
            self.check_hardhat_project()

            # Compile contracts
            if not self.compile_contracts():
                raise Exception("Contract compilation failed")

            # Run tests
            if not self.run_tests(skip_tests=confirm):
                raise Exception("Tests failed. Use --confirm to skip tests.")

            # Get gas price
            gas_price = self.get_gas_price(gas_price_option)
            gas_arg = []
            if gas_price:
                gas_arg = ['--gas-price', gas_price]

            # Find deployment script
            deploy_script = self.project_root / "scripts" / "deploy.js"
            if not deploy_script.exists():
                deploy_script = self.project_root / "scripts" / "deploy.ts"

            if not deploy_script.exists():
                raise Exception("No deployment script found in scripts/ directory")

            # Prepare deployment command
            cmd = ['npx', 'hardhat', 'run', str(deploy_script), '--network', network]
            if gas_arg:
                cmd.extend(gas_arg)

            print(f"📋 Deployment command: {' '.join(cmd)}")

            # Confirm deployment if not on localhost
            if network not in ['localhost', 'hardhat'] and not confirm:
                response = input(f"\n⚠️  About to deploy to {network}. Continue? (y/N): ")
                if response.lower() != 'y':
                    print("❌ Deployment cancelled")
                    return False

            # Execute deployment
            print("🚀 Starting deployment...")
            start_time = time.time()

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )

            deployment_time = time.time() - start_time

            if result.returncode == 0:
                print(f"✅ Deployment completed in {deployment_time:.2f} seconds")
                print("📋 Deployment output:")
                print(result.stdout)

                # Save deployment information
                self.save_deployment_info(network, result.stdout, deployment_time)

                # Verify contracts if requested
                if verify and network not in ['localhost', 'hardhat']:
                    print("\n🔍 Starting contract verification...")
                    self.verify_contracts(network)

                return True
            else:
                print(f"❌ Deployment failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Deployment timed out")
            return False
        except Exception as e:
            print(f"❌ Deployment error: {e}")
            return False

    def save_deployment_info(self, network, output, deployment_time):
        """Save deployment information to file."""
        deployment_info = {
            'network': network,
            'timestamp': time.time(),
            'deployment_time': deployment_time,
            'output': output,
            'contracts': self.extract_contract_addresses(output)
        }

        # Create network-specific deployment file
        deployment_file = self.deployments_dir / f"{network}-deployment.json"

        with open(deployment_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)

        print(f"💾 Deployment info saved to {deployment_file}")

    def extract_contract_addresses(self, output):
        """Extract contract addresses from deployment output."""
        addresses = {}
        lines = output.split('\n')

        for line in lines:
            if 'deployed to' in line.lower() or 'contract address' in line.lower():
                # Try to extract address from line
                import re
                address_pattern = r'0x[a-fA-F0-9]{40}'
                matches = re.findall(address_pattern, line)

                for match in matches:
                    # Try to get contract name from line
                    contract_name = 'Unknown'
                    if 'deployed' in line.lower():
                        parts = line.split('deployed')
                        if parts:
                            contract_name = parts[0].strip()

                    addresses[contract_name] = match

        return addresses

    def verify_contracts(self, network):
        """Verify deployed contracts on block explorer."""
        try:
            # Load deployment info to get contract addresses
            deployment_file = self.deployments_dir / f"{network}-deployment.json"

            if not deployment_file.exists():
                print("⚠️  No deployment info found for verification")
                return False

            with open(deployment_file, 'r') as f:
                deployment_info = json.load(f)

            contracts = deployment_info.get('contracts', {})
            if not contracts:
                print("⚠️  No contracts found to verify")
                return False

            # Call verification script for each contract
            for contract_name, address in contracts.items():
                print(f"🔍 Verifying {contract_name} at {address}")

                cmd = ['python3', str(Path(__file__).parent / 'verify_contracts.py'),
                       '--network', network, '--address', address]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    print(f"✅ {contract_name} verified successfully")
                else:
                    print(f"❌ {contract_name} verification failed: {result.stderr}")

            return True

        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False

    def deploy(self, network, verify=False, gas_price='auto', confirm=False):
        """Main deployment function."""
        try:
            network = self.validate_network(network)
            return self.deploy_contracts(network, verify, gas_price, confirm)
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Deploy smart contracts")
    parser.add_argument("--network", required=True,
                       help="Target network for deployment")
    parser.add_argument("--verify", action="store_true",
                       help="Verify contracts on block explorer after deployment")
    parser.add_argument("--gas-price", default="auto",
                       choices=['auto', 'fast', 'standard', 'slow'],
                       help="Gas price strategy")
    parser.add_argument("--confirm", action="store_true",
                       help="Skip test confirmation and deployment confirmation")

    args = parser.parse_args()

    deployer = ContractDeployer()
    success = deployer.deploy(
        network=args.network,
        verify=args.verify,
        gas_price=args.gas_price,
        confirm=args.confirm
    )

    if success:
        print("\n🎉 Deployment completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Deployment failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()