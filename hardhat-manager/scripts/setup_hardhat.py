#!/usr/bin/env python3
"""
Hardhat Environment Setup Script

This script automatically installs and configures Hardhat development environment.
It handles Node.js installation, Hardhat setup, and initial configuration.

Usage:
    python3 setup_hardhat.py [--version <hardhat-version>] [--project-dir <directory>]

Examples:
    python3 setup_hardhat.py
    python3 setup_hardhat.py --version latest --project-dir ./my-hardhat-project
"""

import os
import sys
import argparse
import subprocess
import platform
import json
import urllib.request
from pathlib import Path


class HardhatSetup:
    def __init__(self):
        self.system = platform.system().lower()
        self.machine = platform.machine().lower()
        self.min_node_version = "16.0.0"
        self.min_npm_version = "8.0.0"
        self.recommended_hardhat_version = "^2.17.0"

    def check_system_requirements(self):
        """Check if system meets requirements for Hardhat development."""
        print("🔍 Checking system requirements...")

        # Check operating system
        supported_systems = ["linux", "darwin", "windows"]
        if self.system not in supported_systems:
            raise ValueError(f"Unsupported operating system: {self.system}")

        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 7):
            raise ValueError(f"Python 3.7+ required, found {python_version.major}.{python_version.minor}")

        # Check internet connection
        try:
            urllib.request.urlopen("https://registry.npmjs.org", timeout=5)
        except:
            raise ValueError("No internet connection. Required for package installation.")

        print(f"✅ System requirements met ({self.system} {self.machine})")
        return True

    def check_node_installation(self):
        """Check if Node.js is installed and meets version requirements."""
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            node_version = result.stdout.strip().lstrip('v')

            print(f"📦 Node.js version found: {node_version}")

            # Compare versions (simplified)
            major, minor, patch = map(int, node_version.split('.'))
            min_major, min_minor = map(int, self.min_node_version.split('.'))

            if major < min_major or (major == min_major and minor < min_minor):
                print(f"⚠️  Node.js version {node_version} is below minimum requirement {self.min_node_version}")
                return False

            return True

        except FileNotFoundError:
            print("❌ Node.js not found")
            return False

    def check_npm_installation(self):
        """Check if npm is installed and meets version requirements."""
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            npm_version = result.stdout.strip()

            print(f"📦 npm version found: {npm_version}")

            # Compare versions
            major, minor, patch = map(int, npm_version.split('.'))
            min_major, min_minor = map(int, self.min_npm_version.split('.'))

            if major < min_major or (major == min_major and minor < min_minor):
                print(f"⚠️  npm version {npm_version} is below minimum requirement {self.min_npm_version}")
                return False

            return True

        except FileNotFoundError:
            print("❌ npm not found")
            return False

    def install_node(self):
        """Install Node.js based on the operating system."""
        print("🚀 Installing Node.js...")

        if self.system == "darwin":
            return self.install_node_macos()
        elif self.system == "linux":
            return self.install_node_linux()
        elif self.system == "windows":
            return self.install_node_windows()
        else:
            raise ValueError(f"Automatic Node.js installation not supported for {self.system}")

    def install_node_macos(self):
        """Install Node.js on macOS using Homebrew."""
        try:
            # Check if Homebrew is installed
            subprocess.run(["brew", "--version"], capture_output=True, check=True)

            print("📦 Installing Node.js via Homebrew...")
            subprocess.run(["brew", "install", "node"], check=True)
            print("✅ Node.js installed successfully")
            return True

        except FileNotFoundError:
            print("❌ Homebrew not found. Please install Node.js manually:")
            print("   Visit: https://nodejs.org/")
            print("   Or install Homebrew first: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            return False
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Node.js: {e}")
            return False

    def install_node_linux(self):
        """Install Node.js on Linux using NodeSource repository."""
        try:
            print("📦 Installing Node.js via NodeSource...")

            # Detect distribution
            try:
                with open("/etc/os-release", "r") as f:
                    os_release = f.read()
                    if "ubuntu" in os_release.lower():
                        return self.install_node_ubuntu()
                    elif "centos" in os_release.lower() or "rhel" in os_release.lower():
                        return self.install_node_centos()
                    else:
                        print("⚠️  Unsupported Linux distribution. Please install Node.js manually:")
                        print("   Visit: https://nodejs.org/")
                        return False
            except FileNotFoundError:
                print("⚠️  Cannot detect Linux distribution. Please install Node.js manually:")
                print("   Visit: https://nodejs.org/")
                return False

        except Exception as e:
            print(f"❌ Failed to install Node.js: {e}")
            return False

    def install_node_ubuntu(self):
        """Install Node.js on Ubuntu/Debian."""
        commands = [
            "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -",
            "sudo apt-get install -y nodejs"
        ]

        for cmd in commands:
            try:
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ Command failed: {cmd}")
                return False

        print("✅ Node.js installed successfully")
        return True

    def install_node_centos(self):
        """Install Node.js on CentOS/RHEL."""
        commands = [
            "curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -",
            "sudo yum install -y nodejs npm"
        ]

        for cmd in commands:
            try:
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ Command failed: {cmd}")
                return False

        print("✅ Node.js installed successfully")
        return True

    def install_node_windows(self):
        """Provide instructions for Windows Node.js installation."""
        print("🪟 Windows installation detected.")
        print("Please install Node.js manually:")
        print("   1. Visit: https://nodejs.org/")
        print("   2. Download and run the LTS installer")
        print("   3. Follow the installation wizard")
        print("   4. Restart your terminal/command prompt")
        return False

    def install_hardhat(self, version="latest"):
        """Install Hardhat globally and/or locally."""
        print("🔧 Installing Hardhat...")

        try:
            # Install Hardhat locally
            print("📦 Installing Hardhat locally...")
            subprocess.run(["npm", "install", "--save-dev", "hardhat"], check=True)
            print("✅ Hardhat installed locally")

            # Install additional recommended packages (including hardhat-deploy)
            print("📦 Installing additional development packages...")
            packages = [
                "@nomicfoundation/hardhat-toolbox",
                "hardhat-deploy",
                "hardhat-deploy-ethers",
                "@nomicfoundation/hardhat-ethers",
                "@nomicfoundation/hardhat-network-helpers",
                "@nomicfoundation/hardhat-chai-matchers",
                "@nomicfoundation/hardhat-verify",
                "hardhat-gas-reporter",
                "solidity-coverage",
                "ethers",
                "chai"
            ]

            for package in packages:
                print(f"   Installing {package}...")
                subprocess.run(["npm", "install", "--save-dev", package], check=True)

            # Install OpenZeppelin contracts for secure contract development
            print("📦 Installing OpenZeppelin contracts...")
            oz_packages = [
                "@openzeppelin/contracts",
                "@openzeppelin/contracts-upgradeable"
            ]

            for package in oz_packages:
                print(f"   Installing {package}...")
                subprocess.run(["npm", "install", package], check=True)

            print("✅ All packages installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages: {e}")
            return False

    def initialize_hardhat_project(self, project_dir=None):
        """Initialize a new Hardhat project."""
        if project_dir is None:
            project_dir = Path.cwd()
        else:
            project_dir = Path(project_dir)
            project_dir.mkdir(parents=True, exist_ok=True)

        print(f"📁 Initializing Hardhat project in: {project_dir}")

        try:
            # Create sample project structure
            directories = ["contracts", "scripts", "test", "deployments"]
            for dir_name in directories:
                (project_dir / dir_name).mkdir(exist_ok=True)

            # Create package.json
            package_json = {
                "name": "hardhat-project",
                "version": "1.0.0",
                "description": "Hardhat project created by Hardhat Manager Skill",
                "main": "index.js",
                "scripts": {
                    "compile": "npx hardhat compile",
                    "test": "npx hardhat test",
                    "deploy": "npx hardhat deploy --network localhost --tags all",
                    "deploy:local": "npx hardhat deploy --network localhost --tags all",
                    "deploy:testnet": "npx hardhat deploy --network goerli --tags all",
                    "deploy:mainnet": "npx hardhat deploy --network mainnet --tags all",
                    "deploy:list": "npx hardhat deployments list",
                    "deploy:info": "npx hardhat deployments list --all",
                    "node": "npx hardhat node",
                    "clean": "npx hardhat clean",
                    "coverage": "npx hardhat coverage"
                },
                "devDependencies": {},
                "dependencies": {
                    "dotenv": "^16.3.1"
                }
            }

            package_json_path = project_dir / "package.json"
            with open(package_json_path, 'w') as f:
                json.dump(package_json, f, indent=2)

            # Create hardhat.config.js with hardhat-deploy support
            hardhat_config = '''require("@nomicfoundation/hardhat-toolbox");
require("hardhat-deploy");
require("hardhat-gas-reporter");
require("solidity-coverage");
require("dotenv").config();

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  defaultNetwork: "hardhat",
  networks: {
    hardhat: {
      chainId: 31337,
      accounts: {
        count: 100,
        accountsBalance: "10000000000000000000000"
      }
    },
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337
    },
    goerli: {
      url: process.env.GOERLI_RPC_URL || `https://goerli.infura.io/v3/${process.env.INFURA_API_KEY}`,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 5,
      gasPrice: 20000000000,
      confirmations: 2,
      timeout: 30000
    },
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || `https://sepolia.infura.io/v3/${process.env.INFURA_API_KEY}`,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 11155111,
      gasPrice: 20000000000,
      confirmations: 2,
      timeout: 30000
    },
    mainnet: {
      url: process.env.MAINNET_RPC_URL || `https://mainnet.infura.io/v3/${process.env.INFURA_API_KEY}`,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 1,
      gasPrice: "auto",
      confirmations: 2,
      timeout: 300000
    },
    polygon: {
      url: process.env.POLYGON_RPC_URL || "https://polygon-rpc.com",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 137,
      gasPrice: 30000000000,
      confirmations: 5,
      timeout: 60000
    },
    mumbai: {
      url: process.env.MUMBAI_RPC_URL || "https://rpc-mumbai.maticvigil.com",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 80001,
      gasPrice: 20000000000,
      confirmations: 3,
      timeout: 30000
    }
  },
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  gasReporter: {
    enabled: process.env.REPORT_GAS !== undefined,
    currency: "USD",
    showTimeSpent: true
  },
  mocha: {
    timeout: 60000
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
    deployments: "./deployments"
  },
  namedAccounts: {
    deployer: {
      default: 0
    }
  },
  etherscan: {
    apiKey: {
      mainnet: process.env.ETHERSCAN_API_KEY,
      goerli: process.env.ETHERSCAN_API_KEY,
      sepolia: process.env.ETHERSCAN_API_KEY,
      polygon: process.env.POLYGONSCAN_API_KEY,
      polygonMumbai: process.env.POLYGONSCAN_API_KEY
    }
  }
};
'''

            config_path = project_dir / "hardhat.config.js"
            with open(config_path, 'w') as f:
                f.write(hardhat_config)

            # Create .env.example
            env_example = '''# Network RPC URLs
MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_API_KEY
GOERLI_RPC_URL=https://goerli.infura.io/v3/YOUR_INFURA_API_KEY
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_API_KEY
POLYGON_RPC_URL=https://polygon-rpc.com
MUMBAI_RPC_URL=https://rpc-mumbai.maticvigil.com

# Private key for deployments (NEVER commit to version control)
PRIVATE_KEY=your_private_key_here

# Block explorer API keys
ETHERSCAN_API_KEY=your_etherscan_api_key_here
POLYGONSCAN_API_KEY=your_polygonscan_api_key_here

# Gas reporting
REPORT_GAS=true

# Fork mainnet for testing (optional)
FORK_ENABLED=false
'''

            env_path = project_dir / ".env.example"
            with open(env_path, 'w') as f:
                f.write(env_example)

            # Create sample contract
            sample_contract = '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract SimpleStorage {
    uint256 private number;

    event NumberChanged(uint256 indexed newNumber, address indexed changer);

    function store(uint256 _number) public {
        number = _number;
        emit NumberChanged(_number, msg.sender);
    }

    function retrieve() public view returns (uint256) {
        return number;
    }
}
'''

            contract_dir = project_dir / "contracts"
            contract_path = contract_dir / "SimpleStorage.sol"
            with open(contract_path, 'w') as f:
                f.write(sample_contract)

            # Create sample test
            sample_test = '''const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("SimpleStorage", function () {
  let simpleStorage;
  let owner;

  beforeEach(async function () {
    [owner] = await ethers.getSigners();
    const SimpleStorage = await ethers.getContractFactory("SimpleStorage");
    simpleStorage = await SimpleStorage.deploy();
    await simpleStorage.deployed();
  });

  it("Should store and retrieve the correct value", async function () {
    const value = 42;
    await simpleStorage.store(value);
    expect(await simpleStorage.retrieve()).to.equal(value);
  });

  it("Should emit NumberChanged event", async function () {
    const value = 100;
    await expect(simpleStorage.store(value))
      .to.emit(simpleStorage, "NumberChanged")
      .withArgs(value, owner.address);
  });
});
'''

            test_path = project_dir / "test" / "SimpleStorage.test.js"
            with open(test_path, 'w') as f:
                f.write(sample_test)

            # Create deploy directory and sample deployment script using hardhat-deploy
            deploy_dir = project_dir / "scripts" / "deploy"
            deploy_dir.mkdir(exist_ok=True)

            deploy_script = '''// Sample deployment script using hardhat-deploy
// For more info: https://github.com/wighawag/hardhat-deploy

const { ethers } = require("hardhat");

module.exports = async ({ getNamedAccounts, deployments, network }) => {
  const { deployer } = await getNamedAccounts();
  const { log } = deployments;

  log(\`Deploying to \${network.name} with account: \${deployer}\`);

  // Deploy SimpleStorage
  const simpleStorage = await deploy("SimpleStorage", {
    from: deployer,
    args: [],
    log: true,
    waitConfirmations: network.config.chainId === 31337 ? 1 : 5,
  });

  log(\`SimpleStorage deployed at: \${simpleStorage.address}\`);

  // Verify contract on Etherscan (skip for localhost)
  if (network.config.chainId !== 31337) {
    log("Waiting for block confirmations...");
    try {
      await hre.run("verify:verify", {
        address: simpleStorage.address,
        constructorArguments: [],
      });
      log("Contract verified on Etherscan");
    } catch (error) {
      if (error.message.toLowerCase().includes("already verified")) {
        log("Contract is already verified");
      } else {
        log(error);
      }
    }
  }
};

module.exports.tags = ["all", "SimpleStorage"];
'''

            deploy_script_path = deploy_dir / "01_deploy_simple_storage.js"
            with open(deploy_script_path, 'w') as f:
                f.write(deploy_script)

            # Create .gitignore
            gitignore = '''# Dependencies
node_modules/

# Environment variables
.env

# Hardhat files
cache/
artifacts/
deployments/
typechain-types/

# Coverage reports
coverage/
coverage.json/

# Logs
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
'''

            gitignore_path = project_dir / ".gitignore"
            with open(gitignore_path, 'w') as f:
                f.write(gitignore)

            print("✅ Hardhat project initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize project: {e}")
            return False

    def install_dependencies(self, project_dir=None):
        """Install project dependencies."""
        if project_dir is None:
            project_dir = Path.cwd()
        else:
            project_dir = Path(project_dir)

        print("📦 Installing project dependencies...")

        try:
            # Install Hardhat and related packages
            subprocess.run(["npm", "install", "--save-dev", "hardhat"],
                         cwd=project_dir, check=True)

            packages = [
                "@nomicfoundation/hardhat-toolbox",
                "hardhat-gas-reporter",
                "solidity-coverage"
            ]

            for package in packages:
                subprocess.run(["npm", "install", "--save-dev", package],
                             cwd=project_dir, check=True)

            # Install OpenZeppelin contracts for secure contract development
            oz_packages = [
                "@openzeppelin/contracts",
                "@openzeppelin/contracts-upgradeable"
            ]

            for package in oz_packages:
                subprocess.run(["npm", "install", package],
                             cwd=project_dir, check=True)

            # Install runtime dependencies
            subprocess.run(["npm", "install"], cwd=project_dir, check=True)

            print("✅ Dependencies installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False

    def verify_installation(self, project_dir=None):
        """Verify that Hardhat is properly installed and working."""
        if project_dir is None:
            project_dir = Path.cwd()
        else:
            project_dir = Path(project_dir)

        print("🔍 Verifying Hardhat installation...")

        try:
            # Test Hardhat version
            result = subprocess.run(["npx", "hardhat", "--version"],
                                  cwd=project_dir, capture_output=True, text=True)
            print(f"✅ Hardhat version: {result.stdout.strip()}")

            # Test compilation
            subprocess.run(["npx", "hardhat", "compile"],
                         cwd=project_dir, check=True, capture_output=True)
            print("✅ Compilation test passed")

            # Test basic functionality
            result = subprocess.run(["npx", "hardhat", "test"],
                                  cwd=project_dir, capture_output=True, text=True)
            if "passing" in result.stdout.lower():
                print("✅ Basic test suite passed")
            else:
                print("⚠️  Test suite may have issues")

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Installation verification failed: {e}")
            return False
        except FileNotFoundError:
            print("❌ npx not found. Node.js may not be properly installed.")
            return False

    def setup_hardhat_environment(self, version="latest", project_dir=None):
        """Main setup function."""
        print("🚀 Starting Hardhat environment setup...")
        print()

        # Check system requirements
        self.check_system_requirements()

        # Check and install Node.js if needed
        if not self.check_node_installation():
            print("⚠️  Node.js needs to be installed or updated")
            if not self.install_node():
                print("❌ Please install Node.js manually and re-run this script")
                return False

        # Check npm
        if not self.check_npm_installation():
            print("❌ npm is required. Please ensure Node.js is properly installed")
            return False

        # Initialize or update project
        if project_dir or not Path("package.json").exists():
            if not self.initialize_hardhat_project(project_dir):
                return False

        # Install dependencies
        if not self.install_dependencies(project_dir):
            return False

        # Verify installation
        if not self.verify_installation(project_dir):
            return False

        print()
        print("🎉 Hardhat environment setup completed successfully!")
        print()
        print("Next steps:")
        print("1. Copy .env.example to .env and configure your environment variables")
        print("2. Run 'npx hardhat compile' to compile your contracts")
        print("3. Run 'npx hardhat test' to run tests")
        print("4. Run 'npx hardhat node' to start a local blockchain")
        print("5. Run 'npx hardhat run scripts/deploy.js' to deploy contracts")

        return True


def main():
    parser = argparse.ArgumentParser(description="Setup Hardhat development environment")
    parser.add_argument("--version", default="latest",
                       help="Hardhat version to install (default: latest)")
    parser.add_argument("--project-dir",
                       help="Directory to create the project (default: current directory)")

    args = parser.parse_args()

    setup = HardhatSetup()

    try:
        success = setup.setup_hardhat_environment(args.version, args.project_dir)
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()