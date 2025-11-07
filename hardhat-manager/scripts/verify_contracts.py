#!/usr/bin/env python3
"""
Hardhat Contract Verification Script

Automates the verification of smart contracts on various block explorers.
Supports Etherscan, Polygonscan, Arbiscan, and other explorers.

Usage:
    python3 verify_contracts.py --network <network-name> --address <contract-address>

Examples:
    python3 verify_contracts.py --network ethereum --address 0x1234567890123456789012345678901234567890
    python3 verify_contracts.py --network polygon --address 0xabcdef1234567890abcdef1234567890abcdef12
"""

import os
import sys
import argparse
import subprocess
import json
import time
from pathlib import Path


class ContractVerifier:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.explorer_urls = {
            'ethereum': 'https://api.etherscan.io/api',
            'goerli': 'https://api-goerli.etherscan.io/api',
            'sepolia': 'https://api-sepolia.etherscan.io/api',
            'polygon': 'https://api.polygonscan.com/api',
            'mumbai': 'https://api-testnet.polygonscan.com/api',
            'arbitrum': 'https://api.arbiscan.io/api',
            'arbitrum-goerli': 'https://api-goerli.arbiscan.io/api',
            'optimism': 'https://api-optimistic.etherscan.io/api',
            'optimism-goerli': 'https://api-goerli.optimistic.etherscan.io/api',
            'bsc': 'https://api.bscscan.com/api',
            'bsc-testnet': 'https://api-testnet.bscscan.com/api'
        }

    def validate_network(self, network):
        """Validate network and return corresponding explorer."""
        if network.lower() not in self.explorer_urls:
            raise ValueError(f"Network '{network}' not supported for verification")

        return network.lower()

    def validate_address(self, address):
        """Validate Ethereum address format."""
        if not address.startswith('0x') or len(address) != 42:
            raise ValueError("Invalid Ethereum address format")

        # Check if address contains only valid hex characters
        try:
            int(address, 16)
            return True
        except ValueError:
            raise ValueError("Invalid Ethereum address")

    def check_hardhat_project(self):
        """Check if current directory is a Hardhat project."""
        required_files = ['hardhat.config.js', 'package.json']

        for file in required_files:
            if not (self.project_root / file).exists():
                raise ValueError(f"Not a valid Hardhat project. Missing {file}")

        return True

    def get_api_key(self, network):
        """Get API key for the specified network."""
        env_keys = {
            'ethereum': 'ETHERSCAN_API_KEY',
            'goerli': 'ETHERSCAN_API_KEY',
            'sepolia': 'ETHERSCAN_API_KEY',
            'polygon': 'POLYGONSCAN_API_KEY',
            'mumbai': 'POLYGONSCAN_API_KEY',
            'arbitrum': 'ARBISCAN_API_KEY',
            'arbitrum-goerli': 'ARBISCAN_API_KEY',
            'optimism': 'OPTIMISM_API_KEY',
            'optimism-goerli': 'OPTIMISM_API_KEY',
            'bsc': 'BSCSCAN_API_KEY',
            'bsc-testnet': 'BSCSCAN_API_KEY'
        }

        env_key = env_keys.get(network, 'ETHERSCAN_API_KEY')
        api_key = os.getenv(env_key)

        if not api_key:
            print(f"⚠️  Warning: {env_key} not found in environment variables")
            print("   You may need to set this variable for verification to work")

        return api_key

    def find_contract_source(self, address):
        """Try to find the contract source file based on address."""
        # This is a simplified approach - in practice, you'd need a more robust method
        contracts_dir = self.project_root / "contracts"

        if not contracts_dir.exists():
            return None

        # Look for contract files
        contract_files = list(contracts_dir.rglob("*.sol"))

        if not contract_files:
            return None

        # For now, return the first contract file found
        # In a real implementation, you'd need to match addresses to contracts
        return contract_files[0]

    def get_compiler_settings(self, contract_file):
        """Extract compiler settings from Hardhat config or artifacts."""
        artifacts_dir = self.project_root / "artifacts"

        if not artifacts_dir.exists():
            return {}

        # Try to find contract artifact
        contract_name = contract_file.stem
        artifact_dirs = list(artifacts_dir.rglob(f"{contract_name}.json"))

        if artifact_dirs:
            try:
                with open(artifact_dirs[0], 'r') as f:
                    artifact = json.load(f)

                return {
                    'solc': {
                        'version': artifact.get('compiler', {}).get('version', 'auto'),
                        'settings': artifact.get('compiler', {}).get('settings', {})
                    }
                }
            except Exception as e:
                print(f"⚠️  Could not extract compiler settings: {e}")

        return {}

    def verify_with_hardhat(self, network, address, contract_file=None):
        """Use Hardhat's built-in verification plugin."""
        try:
            print(f"🔍 Verifying contract {address} on {network}...")

            # Build verification command
            cmd = ['npx', 'hardhat', 'verify', '--network', network, address]

            # Add constructor arguments if available (simplified)
            # In practice, you'd need to extract actual constructor args

            print(f"📋 Verification command: {' '.join(cmd)}")

            # Execute verification
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                print("✅ Contract verified successfully!")
                print("📋 Verification output:")
                print(result.stdout)
                return True
            else:
                print(f"❌ Verification failed: {result.stderr}")

                # Check if it's already verified
                if "Already Verified" in result.stderr or "Contract source code already verified" in result.stderr:
                    print("✅ Contract is already verified!")
                    return True

                return False

        except subprocess.TimeoutExpired:
            print("❌ Verification timed out")
            return False
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False

    def verify_with_api(self, network, address, contract_file):
        """Direct API verification (fallback method)."""
        try:
            print(f"🔍 Attempting API verification for {address} on {network}...")

            # Get API key
            api_key = self.get_api_key(network)
            if not api_key:
                print("❌ No API key available for API verification")
                return False

            # This is a simplified API verification
            # In practice, you'd need to implement the full verification API
            explorer_url = self.explorer_urls[network]

            # For now, just suggest using Hardhat plugin
            print("💡 For API verification, install and configure etherscan plugin:")
            print("   npm install --save-dev @nomiclabs/hardhat-etherscan")
            print("   Add etherscan config to hardhat.config.js")

            return False

        except Exception as e:
            print(f"❌ API verification error: {e}")
            return False

    def check_verification_status(self, network, address):
        """Check if contract is already verified."""
        try:
            api_key = self.get_api_key(network)
            if not api_key:
                return False

            explorer_url = self.explorer_urls[network]

            # Build API URL for checking verification status
            params = {
                'module': 'contract',
                'action': 'getsourcecode',
                'contractaddress': address,
                'apikey': api_key
            }

            import urllib.parse
            import urllib.request

            url = f"{explorer_url}?{urllib.parse.urlencode(params)}"

            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())

            if data['status'] == '1' and data['result']:
                result = data['result'][0]
                if result.get('SourceCode') and result.get('SourceCode') != '':
                    print("✅ Contract is already verified!")
                    print(f"   Contract Name: {result.get('ContractName', 'Unknown')}")
                    print(f"   Compiler Version: {result.get('CompilerVersion', 'Unknown')}")
                    return True

            return False

        except Exception as e:
            print(f"⚠️  Could not check verification status: {e}")
            return False

    def verify_contract(self, network, address, contract_file=None, force=False):
        """Main verification function."""
        try:
            # Validate inputs
            network = self.validate_network(network)
            self.validate_address(address)
            self.check_hardhat_project()

            print(f"🔍 Starting verification for contract {address} on {network}")

            # Check if already verified
            if not force and self.check_verification_status(network, address):
                return True

            # Try to find contract source if not provided
            if not contract_file:
                contract_file = self.find_contract_source(address)
                if contract_file:
                    print(f"📄 Found contract source: {contract_file}")
                else:
                    print("⚠️  Could not automatically find contract source")

            # Try Hardhat verification first
            if self.verify_with_hardhat(network, address, contract_file):
                return True

            # Fallback to API verification
            if contract_file and self.verify_with_api(network, address, contract_file):
                return True

            print("❌ Verification failed")
            print("\n💡 Troubleshooting tips:")
            print("1. Ensure the contract was deployed from this project")
            print("2. Check that constructor arguments are correct")
            print("3. Verify compiler version matches deployment")
            print("4. Ensure API keys are set in environment variables")
            print("5. Try with --force flag to ignore existing verification")

            return False

        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False

    def verify(self, network, address, contract_file=None, force=False):
        """Public verification method."""
        return self.verify_contract(network, address, contract_file, force)


def main():
    parser = argparse.ArgumentParser(description="Verify smart contracts on block explorers")
    parser.add_argument("--network", required=True,
                       help="Network where contract is deployed")
    parser.add_argument("--address", required=True,
                       help="Contract address to verify")
    parser.add_argument("--contract",
                       help="Path to contract source file (optional)")
    parser.add_argument("--force", action="store_true",
                       help="Force verification even if already verified")

    args = parser.parse_args()

    verifier = ContractVerifier()
    success = verifier.verify(
        network=args.network,
        address=args.address,
        contract_file=args.contract,
        force=args.force
    )

    if success:
        print("\n🎉 Verification completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Verification failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()