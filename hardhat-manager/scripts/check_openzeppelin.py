#!/usr/bin/env python3
"""
OpenZeppelin Installation Check Script

This script checks if OpenZeppelin contracts are properly installed and configured
in a Hardhat project. It also provides guidance for installation if missing.

Usage:
    python3 check_openzeppelin.py [--project-dir <directory>]
"""

import os
import sys
import json
import subprocess
from pathlib import Path


class OpenZeppelinChecker:
    def __init__(self):
        self.current_dir = Path.cwd()

    def check_package_json(self, project_dir):
        """Check if package.json includes OpenZeppelin dependencies."""
        package_json_path = project_dir / "package.json"

        if not package_json_path.exists():
            return False, "package.json not found"

        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)

            # Check dependencies
            deps = package_data.get('dependencies', {})
            dev_deps = package_data.get('devDependencies', {})

            has_contracts = '@openzeppelin/contracts' in deps or '@openzeppelin/contracts' in dev_deps
            has_upgradeable = '@openzeppelin/contracts-upgradeable' in deps or '@openzeppelin/contracts-upgradeable' in dev_deps

            if has_contracts and has_upgradeable:
                return True, "Both standard and upgradeable OpenZeppelin contracts found"
            elif has_contracts:
                return True, "Standard OpenZeppelin contracts found (upgradeable contracts missing)"
            else:
                return False, "OpenZeppelin contracts not found in dependencies"

        except Exception as e:
            return False, f"Error reading package.json: {e}"

    def check_node_modules(self, project_dir):
        """Check if OpenZeppelin is installed in node_modules."""
        node_modules_path = project_dir / "node_modules"

        contracts_path = node_modules_path / "@openzeppelin" / "contracts"
        upgradeable_path = node_modules_path / "@openzeppelin" / "contracts-upgradeable"

        has_contracts = contracts_path.exists()
        has_upgradeable = upgradeable_path.exists()

        if has_contracts and has_upgradeable:
            return True, "Both standard and upgradeable OpenZeppelin contracts installed"
        elif has_contracts:
            return True, "Standard OpenZeppelin contracts installed (upgradeable contracts missing)"
        else:
            return False, "OpenZeppelin contracts not installed"

    def check_imports_in_contracts(self, project_dir):
        """Check if any contracts import OpenZeppelin libraries."""
        contracts_dir = project_dir / "contracts"

        if not contracts_dir.exists():
            return False, "No contracts directory found"

        openzeppelin_imports = []

        for contract_file in contracts_dir.rglob("*.sol"):
            try:
                with open(contract_file, 'r') as f:
                    content = f.read()

                # Look for OpenZeppelin imports
                if '@openzeppelin/contracts' in content:
                    openzeppelin_imports.append(contract_file.relative_to(project_dir))

            except Exception as e:
                print(f"⚠️  Error reading {contract_file}: {e}")

        if openzeppelin_imports:
            return True, f"Found {len(openzeppelin_imports)} contract(s) using OpenZeppelin"
        else:
            return False, "No contracts using OpenZeppelin found"

    def check_hardhat_config(self, project_dir):
        """Check if hardhat.config.js is properly configured for OpenZeppelin."""
        config_files = [
            project_dir / "hardhat.config.js",
            project_dir / "hardhat.config.ts"
        ]

        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config_content = f.read()

                    # Check for OpenZeppelin references
                    if '@openzeppelin' in config_content:
                        return True, f"Hardhat config references OpenZeppelin ({config_file.name})"

                except Exception as e:
                    print(f"⚠️  Error reading {config_file}: {e}")

        return False, "No OpenZeppelin references found in Hardhat config"

    def install_openzeppelin(self, project_dir):
        """Install OpenZeppelin contracts."""
        print("🔧 Installing OpenZeppelin contracts...")

        try:
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(project_dir)

            # Install standard contracts
            print("   Installing @openzeppelin/contracts...")
            result1 = subprocess.run(
                ["npm", "install", "@openzeppelin/contracts"],
                capture_output=True,
                text=True,
                timeout=300
            )

            # Install upgradeable contracts
            print("   Installing @openzeppelin/contracts-upgradeable...")
            result2 = subprocess.run(
                ["npm", "install", "@openzeppelin/contracts-upgradeable"],
                capture_output=True,
                text=True,
                timeout=300
            )

            os.chdir(original_cwd)

            if result1.returncode == 0 and result2.returncode == 0:
                print("✅ OpenZeppelin contracts installed successfully")
                return True
            else:
                print(f"❌ Installation failed:")
                if result1.returncode != 0:
                    print(f"   Standard contracts: {result1.stderr}")
                if result2.returncode != 0:
                    print(f"   Upgradeable contracts: {result2.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Installation timed out")
            return False
        except Exception as e:
            print(f"❌ Installation error: {e}")
            return False

    def create_sample_contract(self, project_dir):
        """Create a sample contract using OpenZeppelin."""
        contracts_dir = project_dir / "contracts"
        contracts_dir.mkdir(exist_ok=True)

        sample_contract = '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title SampleToken
 * @dev Sample ERC20 token using OpenZeppelin libraries
 */
contract SampleToken is ERC20, Ownable, ReentrancyGuard {
    constructor(
        string memory name,
        string memory symbol,
        uint256 initialSupply
    ) ERC20(name, symbol) {
        _mint(msg.sender, initialSupply);
    }

    /**
     * @dev Mint new tokens (only owner)
     */
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    /**
     * @dev Burn tokens (reentrancy protected)
     */
    function burn(uint256 amount) external nonReentrant {
        _burn(msg.sender, amount);
    }
}
'''

        sample_path = contracts_dir / "SampleToken.sol"

        try:
            with open(sample_path, 'w') as f:
                f.write(sample_contract)

            print(f"✅ Sample contract created: {sample_path}")
            return True

        except Exception as e:
            print(f"❌ Error creating sample contract: {e}")
            return False

    def run_check(self, project_dir=None):
        """Run comprehensive OpenZeppelin check."""
        if project_dir is None:
            project_dir = self.current_dir
        else:
            project_dir = Path(project_dir)

        print(f"🔍 Checking OpenZeppelin installation in: {project_dir}")
        print()

        results = []

        # Check package.json
        print("📦 Checking package.json...")
        pkg_ok, pkg_msg = self.check_package_json(project_dir)
        results.append(("package.json", pkg_ok, pkg_msg))
        print(f"   {'✅' if pkg_ok else '❌'} {pkg_msg}")
        print()

        # Check node_modules
        print("📂 Checking node_modules...")
        nm_ok, nm_msg = self.check_node_modules(project_dir)
        results.append(("node_modules", nm_ok, nm_msg))
        print(f"   {'✅' if nm_ok else '❌'} {nm_msg}")
        print()

        # Check contract imports
        print("📄 Checking contract imports...")
        ci_ok, ci_msg = self.check_imports_in_contracts(project_dir)
        results.append(("contract_imports", ci_ok, ci_msg))
        print(f"   {'✅' if ci_ok else '❌'} {ci_msg}")
        print()

        # Check hardhat config
        print("⚙️  Checking Hardhat configuration...")
        hc_ok, hc_msg = self.check_hardhat_config(project_dir)
        results.append(("hardhat_config", hc_ok, hc_msg))
        print(f"   {'✅' if hc_ok else '❌'} {hc_msg}")
        print()

        # Summary
        print("=" * 50)
        print("📊 OPENZEPELIN INSTALLATION SUMMARY")
        print("=" * 50)

        all_good = all(result[1] for result in results)

        if all_good:
            print("🎉 OpenZeppelin is properly installed and configured!")
            print()
            print("✅ Benefits:")
            print("   • Access to audited, secure contract libraries")
            print("   • Standard token implementations (ERC20, ERC721, etc.)")
            print("   • Security utilities (ReentrancyGuard, AccessControl)")
            print("   • Upgradeable contract patterns")
            print("   • Gas optimization utilities")
        else:
            print("⚠️  OpenZeppelin installation needs attention")
            print()
            print("❌ Issues found:")
            for check_name, ok, msg in results:
                if not ok:
                    print(f"   • {check_name}: {msg}")
            print()

            # Offer to install
            try:
                response = input("🔧 Would you like to install OpenZeppelin contracts? (y/n): ").strip().lower()
                if response in ['y', 'yes']:
                    if self.install_openzeppelin(project_dir):
                        print()
                        print("🎨 Would you like to create a sample contract using OpenZeppelin? (y/n): ", end="")
                        sample_response = input().strip().lower()
                        if sample_response in ['y', 'yes']:
                            self.create_sample_contract(project_dir)
                    else:
                        print("❌ Installation failed. Please run manually:")
                        print("   npm install @openzeppelin/contracts @openzeppelin/contracts-upgradeable")
            except KeyboardInterrupt:
                print("\n❌ Installation cancelled")

        print()
        print("📚 OpenZeppelin Resources:")
        print("   • Documentation: https://docs.openzeppelin.com/contracts")
        print("   • Contracts API: https://docs.openzeppelin.com/contracts/4.x/api")
        print("   • Security: https://docs.openzeppelin.com/contracts/4.x/security")
        print("   • Upgradeable: https://docs.openzeppelin.com/contracts/4.x/upgradeable")
        print("   • Wizard: https://wizard.openzeppelin.com/")

        return all_good


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Check OpenZeppelin installation")
    parser.add_argument("--project-dir", help="Project directory to check (default: current)")

    args = parser.parse_args()

    checker = OpenZeppelinChecker()

    try:
        success = checker.run_check(args.project_dir)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled")
        sys.exit(1)


if __name__ == "__main__":
    main()