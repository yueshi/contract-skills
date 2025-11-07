#!/usr/bin/env python3
"""
Hardhat-Deploy Integration Script for Hardhat Manager

This script helps integrate hardhat-deploy into an existing Hardhat project.
It modifies configuration files, creates deployment scripts, and sets up
the project for modern deployment management.

Usage:
    python3 integrate_hardhat_deploy.py [--project-dir <directory>]
"""

import os
import sys
import shutil
import argparse
from pathlib import Path


class HardhatDeployIntegrator:
    def __init__(self, project_dir=None):
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.hardhat_manager_dir = Path(__file__).parent.parent

    def check_hardhat_project(self):
        """Check if current directory is a Hardhat project."""
        required_files = ['hardhat.config.js', 'package.json']
        for file in required_files:
            if not (self.project_dir / file).exists():
                raise ValueError(f"Not a valid Hardhat project. Missing {file}")

        return True

    def backup_config(self):
        """Backup existing configuration files."""
        print("📋 Backing up existing configuration files...")

        backup_dir = self.project_dir / "backup-original-configs"
        backup_dir.mkdir(exist_ok=True)

        files_to_backup = ['hardhat.config.js', 'package.json']
        for file in files_to_backup:
            src = self.project_dir / file
            if src.exists():
                dst = backup_dir / file
                shutil.copy2(src, dst)
                print(f"   ✅ Backed up {file}")

        print(f"💾 Backup created in: {backup_dir}")

    def update_package_json(self):
        """Update package.json with hardhat-deploy dependencies."""
        print("\n📦 Updating package.json with hardhat-deploy dependencies...")

        package_json_path = self.project_dir / "package.json"

        try:
            import json
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)

            # Add hardhat-deploy dependencies
            dev_deps = package_data.get("devDependencies", {})

            # Check if hardhat-deploy already exists
            if "hardhat-deploy" not in dev_deps:
                dev_deps["hardhat-deploy"] = "^0.11.34"
                dev_deps["hardhat-deploy-ethers"] = "^0.3.0-beta.13"

                # Add deployment scripts
                scripts = package_data.get("scripts", {})
                scripts["deploy:local"] = "npx hardhat deploy --network localhost --tags all"
                scripts["deploy:testnet"] = "npx hardhat run scripts/deploy.js --network localhost"
                scripts["deploy:mainnet"] = "npx hardhat run scripts/deploy.js --network mainnet"
                scripts["deploy:list"] = "npx hardhat deployments list"
                scripts["deploy:info"] = "npx hardhat deployments list --all"

                package_data["scripts"] = scripts
                package_data["devDependencies"] = dev_deps

                with open(package_json_path, 'w') as f:
                    json.dump(package_data, f, indent=2)

                print("   ✅ Updated package.json")
            else:
                print("   ℹ️ hardhat-deploy already installed")

        except Exception as e:
            print(f"   ⚠️ Error updating package.json: {e}")

    def update_hardhat_config(self):
        """Update hardhat.config.js to include hardhat-deploy."""
        print("\n⚙️ Updating hardhat.config.js...")

        config_path = self.project_dir / "hardhat.config.js"

        if not config_path.exists():
            print("   ⚠️ hardhat.config.js not found, skipping...")
            return

        try:
            with open(config_path, 'r') as f:
                config_content = f.read()

            # Check if hardhat-deploy is already imported
            if "hardhat-deploy" not in config_content:
                # Add require statement
                config_content = config_content.replace(
                    'require("@nomicfoundation/hardhat-toolbox");',
                    'require("@nomicfoundation/hardhat-toolbox");\nrequire("hardhat-deploy");'
                )

                # Add paths configuration if not exists
                if 'paths: {' not in config_content:
                    paths_config = '''
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
    deployments: "./deployments"
  },'''
                    config_content = config_content.replace(
                        '  mocha: {',
                        paths_config + '\n  mocha: {'
                    )

                # Add named accounts if not exists
                if 'namedAccounts: {' not in config_content:
                    accounts_config = '''
  namedAccounts: {
    deployer: {
      default: 0
    }
  }'''
                    config_content = config_content.replace(
                        '  etherscan: {',
                        accounts_config + '\n\n  etherscan: {'
                    )

                with open(config_path, 'w') as f:
                    f.write(config_content)

                print("   ✅ Updated hardhat.config.js")
            else:
                print("   ℹ️ hardhat-deploy already configured")

        except Exception as e:
            print(f"   ⚠️ Error updating hardhat.config.js: {e}")

    def create_deploy_directory(self):
        """Create deploy directory and basic scripts."""
        print("\n📁 Creating deploy directory and scripts...")

        deploy_dir = self.project_dir / "scripts" / "deploy"
        deploy_dir.mkdir(parents=True, exist_ok=True)

        # Create a basic deployment script template
        script_template = '''// Basic deployment script using hardhat-deploy

const { ethers } = require("hardhat");
const { deploy } = require("@openzeppelin/hardhat-upgrades");

module.exports = async ({ getNamedAccounts, deployments, network }) => {
  const { deployer } = await getNamedAccounts();
  const { log } = deployments;

  log(`Deploying to ${network.name} with account: ${deployer}`);

  try {
    // Deploy MyContract
    const myContract = await deploy("MyContract", {
      from: deployer,
      args: [],
      log: true,
      waitConfirmations: network.config.chainId === 31337 ? 1 : 5,
    });

    log(`MyContract deployed at: ${myContract.address}`);

    // Verify contract
    if (network.config.chainId !== 31337) {
      try {
        log("Waiting for block confirmations...");
        await hre.run("verify:verify", {
          address: myContract.address,
          constructorArguments: [],
        });
        log("Contract verified");
      } catch (error) {
        if (error.message.toLowerCase().includes("already verified")) {
          log("Contract is already verified");
        } else {
          log(error);
        }
      }
    }
  } catch (error) {
    log(`Deployment failed: ${error.message}`);
    throw error;
  }
};
'''

        script_path = deploy_dir / "01_deploy_basic.js"
        with open(script_path, 'w') as f:
            f.write(script_template)

        print(f"   ✅ Created deployment script: {script_path}")

    def create_helpers(self):
        """Create helper configuration files."""
        print("\n🛠️ Creating helper configuration files...")

        # Create helper-hardhat-config.js
        helper_config = '''// Helper configuration for Hardhat deployments

const developmentChains = ["hardhat", "localhost"];
const nonLocalChains = ["mainnet", "polygon", "arbitrum", "optimism"];

const VERIFICATION_BLOCK_CONFIRMATIONS = 6;

module.exports = {
  developmentChains,
  nonLocalChains,
  VERIFICATION_BLOCK_CONFIRMATIONS,
};
'''

        helper_path = self.project_dir / "helper-hardhat-config.js"
        with open(helper_path, 'w') as f:
            f.write(helper_config)

        print(f"   ✅ Created helper config: {helper_path}")

        # Create .env.example
        env_example = '''# Network RPC URLs
MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_API_KEY
POLYGON_RPC_URL=https://polygon-rpc.com
ARBITRUM_RPC_URL=https://arbitrum-mainnet.infura.io/v3/YOUR_INFURA_API_KEY

# Private key (NEVER commit real private keys!)
PRIVATE_KEY=your_private_key_here

# Block explorer API keys
ETHERSCAN_API_KEY=your_etherscan_api_key_here
POLYGONSCAN_API_KEY=your_polygonscan_api_key_here
ARBISCAN_API_KEY=your_arbiscan_api_key_here

# Enable/disable features
REPORT_GAS=true
FORK_ENABLED=false
'''

        env_example_path = self.project_dir / ".env.example"
        with open(env_example_path, 'w') as f:
            f.write(env_example)

        print(f"   ✅ Created .env.example: {env_example_path}")

    def create_readme(self):
        """Create README with hardhat-deploy instructions."""
        print("\n📖 Creating README with hardhat-deploy instructions...")

        readme_content = '''# Hardhat Project with Deploy

This project now includes hardhat-deploy for modern contract deployment management.

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Set up Environment

```bash
cp .env.example .env
# Edit .env with your private keys and API keys
```

### 3. Deploy Contracts

```bash
# Deploy to local network
npm run deploy:local

# Deploy to testnet
npx hardhat deploy --network goerli

# Deploy to mainnet
npx hardhat deploy --network mainnet
```

### 4. Check Deployments

```bash
# List all deployments
npm run deploy:list

# Get deployment info
npm run deploy:info
```

## New Features

This integration adds:

- ✅ Automatic deployment history tracking
- ✅ Contract address management
- ✅ Multi-network deployment support
- ✅ Automatic contract verification
- ✅ Deployment information queries

## Directory Structure

```
.
├── deployments/          # Deployment information
├── scripts/deploy/       # Deployment scripts
├── helper-hardhat-config.js  # Helper configurations
└── .env.example          # Environment variables template
```

## Available Commands

- `npm run deploy:local` - Deploy to localhost
- `npx hardhat deploy --network <name>` - Deploy to specific network
- `npx hardhat deployments list` - List deployments
- `npx hardhat deployments list --all` - List all deployments with details

For more information, see the hardhat-deploy documentation.
'''

        readme_path = self.project_dir / "DEPLOY_README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)

        print(f"   ✅ Created README: {readme_path}")

    def integrate(self):
        """Main integration function."""
        try:
            print("🚀 Hardhat-Deploy Integration Script")
            print("=" * 50)
            print(f"Project directory: {self.project_dir}\n")

            # Check if Hardhat project
            self.check_hardhat_project()
            print("✅ Valid Hardhat project found")

            # Backup existing configs
            self.backup_config()

            # Update package.json
            self.update_package_json()

            # Update hardhat.config.js
            self.update_hardhat_config()

            # Create deploy directory
            self.create_deploy_directory()

            # Create helpers
            self.create_helpers()

            # Create README
            self.create_readme()

            print("\n" + "=" * 50)
            print("✅ Integration completed successfully!")
            print("\nNext steps:")
            print("1. Install dependencies: npm install")
            print("2. Set up environment variables: cp .env.example .env")
            print("3. Deploy contracts: npm run deploy:local")
            print("4. Check deployments: npm run deploy:list")
            print("\nFor more information, see DEPLOY_README.md")

        except Exception as e:
            print(f"\n❌ Integration failed: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Integrate hardhat-deploy into Hardhat project")
    parser.add_argument("--project-dir", help="Path to Hardhat project directory")

    args = parser.parse_args()

    integrator = HardhatDeployIntegrator(args.project_dir)
    integrator.integrate()


if __name__ == "__main__":
    main()
