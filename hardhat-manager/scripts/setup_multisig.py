#!/usr/bin/env python3
"""
Multisig Wallet Setup Script for Hardhat Manager

This script helps create and deploy multisig wallets using predefined templates.
It supports basic multisig wallets and timelock multisig wallets with Gnosis Safe compatibility.

Usage:
    python3 setup_multisig.py --type <basic|timelock> --config <config-name>
    python3 setup_multisig.py --type basic --config basic
    python3 setup_multisig.py --type timelock --config dao
"""

import os
import sys
import argparse
import shutil
import json
from pathlib import Path
from datetime import datetime


class MultisigSetup:
    def __init__(self):
        self.hardhat_manager_dir = Path(__file__).parent.parent
        self.template_dir = self.hardhat_manager_dir / "assets" / "multisig-template"
        self.project_dir = Path.cwd()

    def validate_type(self, multisig_type):
        """Validate multisig type."""
        valid_types = ["basic", "timelock"]
        if multisig_type not in valid_types:
            raise ValueError(f"Invalid type '{multisig_type}'. Must be one of: {valid_types}")
        return multisig_type

    def validate_config(self, config_name):
        """Validate configuration name."""
        config_file = self.template_dir / "config" / "multisig.config.js"

        if not config_file.exists():
            raise ValueError(f"Config file not found: {config_file}")

        # Check if config name exists in the config file
        # For now, we'll validate basic names
        valid_configs = ["basic", "dao", "project", "defi", "personal"]
        if config_name not in valid_configs:
            print(f"⚠️  Warning: Config '{config_name}' may not exist in multisig.config.js")
            print(f"   Valid configs: {valid_configs}")

        return config_name

    def copy_template(self, project_name, multisig_type, config_name):
        """Copy multisig template to new project directory."""
        project_path = self.project_dir / project_name

        if project_path.exists():
            raise ValueError(f"Directory '{project_name}' already exists")

        # Copy template directory
        shutil.copytree(self.template_dir, project_path)
        print(f"✅ Created project directory: {project_path}")

        # Remove unnecessary templates if not needed
        self.customize_template(project_path, multisig_type)

        return project_path

    def customize_template(self, project_path, multisig_type):
        """Customize template based on type."""
        print(f"🔧 Customizing template for {multisig_type} multisig...")

        # Update package.json name
        package_json_path = project_path / "package.json"
        if package_json_path.exists():
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)

            package_data['name'] = f"multisig-{multisig_type}-project"

            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)

            print("   ✅ Updated package.json")

    def update_config(self, project_path, config_name):
        """Update configuration for deployment."""
        config_file = project_path / "config" / "multisig.config.js"

        print(f"\n📋 Configuration: {config_name}")
        print(f"   Config file: {config_file}")
        print(f"\n   ⚠️  IMPORTANT: Please update the following before deploying:")
        print(f"      - Owner addresses in config/multisig.config.js")
        print(f"      - Timelock administrators (if using timelock)")
        print(f"      - Private keys in .env file")
        print(f"      - RPC URLs for networks you'll deploy to")

    def create_env_example(self, project_path):
        """Create .env file with necessary variables."""
        env_content = """# Network RPC URLs
MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_API_KEY
GOERLI_RPC_URL=https://goerli.infura.io/v3/YOUR_INFURA_API_KEY
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_API_KEY
POLYGON_RPC_URL=https://polygon-rpc.com
ARBITRUM_RPC_URL=https://arbitrum-mainnet.infura.io/v3/YOUR_INFURA_API_KEY
OPTIMISM_RPC_URL=https://optimism-mainnet.infura.io/v3/YOUR_INFURA_API_KEY
BSC_RPC_URL=https://bsc-dataseed1.binance.org

# Private keys (NEVER commit real private keys!)
PRIVATE_KEY=your_private_key_here

# Block explorer API keys
ETHERSCAN_API_KEY=your_etherscan_api_key_here
POLYGONSCAN_API_KEY=your_polygonscan_api_key_here
ARBISCAN_API_KEY=your_arbiscan_api_key_here
OPTIMISTIC_ETHERSCAN_API_KEY=your_optimistic_api_key_here
BSCSCAN_API_KEY=your_bscscan_api_key_here

# Deployment settings
REPORT_GAS=true
FORK_ENABLED=false
FORK_BLOCK_NUMBER=
"""

        env_path = project_path / ".env.example"
        with open(env_path, 'w') as f:
            f.write(env_content)

        print(f"   ✅ Created .env.example")

    def create_readme(self, project_path, multisig_type, config_name):
        """Create README with deployment instructions."""
        readme_content = f"""# {multisig_type.title()} Multisig Wallet

This project contains a {multisig_type} multisig wallet with Gnosis Safe compatibility.

## Configuration

Configuration is stored in `config/multisig.config.js`.
- Config name: `{config_name}`
- Multisig type: `{multisig_type}`

**Before deploying, you MUST:**
1. Update owner addresses in `config/multisig.config.js`
2. Set up environment variables in `.env` file
3. Ensure you have sufficient funds for deployment

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env with your private keys and API keys
```

### 3. Update Configuration

Edit `config/multisig.config.js`:
```javascript
{config_name}: {{
  owners: [
    "0x...", // Owner 1 address
    "0x...", // Owner 2 address
    "0x..."  // Owner 3 address
  ],
  requiredConfirmations: 2,
  // ... other settings
}}
```

### 4. Deploy

**Basic Multisig:**
```bash
npm run deploy:local
```

**Timelock Multisig:**
```bash
npm run deploy:timelock:local
```

### 5. Verify on Etherscan

```bash
npm run verify:contract --network goerli CONTRACT_ADDRESS
```

## Deployment Commands

| Command | Description |
|---------|-------------|
| `npm run deploy:local` | Deploy to local Hardhat network |
| `npm run deploy:goerli` | Deploy to Goerli testnet |
| `npm run deploy:sepolia` | Deploy to Sepolia testnet |
| `npm run deploy:mainnet` | Deploy to Ethereum mainnet |
| `npm run deploy:timelock:local` | Deploy timelock multisig to local |
| `npm run deploy:timelock:goerli` | Deploy timelock multisig to Goerli |

## Usage Examples

### Basic Multisig Wallet

```javascript
// Submit transaction
const tx = await multisig.submitTransaction(
    recipient,
    ethers.utils.parseEther("10"),
    "0x",
    {{ from: owner1 }}
);

// Confirm transaction (from another owner)
await multisig.confirmTransaction(tx, {{ from: owner2 }});

// Execute transaction
await multisig.executeTransaction(tx, {{ from: owner3 }});
```

### Timelock Multisig Wallet

```javascript
// Queue timelock transaction
const delay = 24 * 60 * 60; // 24 hours
const txId = await timelockMultisig.queueTimelockTransaction(
    recipient,
    ethers.utils.parseEther("10"),
    "0x",
    delay,
    {{ from: timelockAdmin }}
);

// Confirm transaction (from owners)
await timelockMultisig.confirmTimelockTransaction(txId, {{ from: owner1 }});
await timelockMultisig.confirmTimelockTransaction(txId, {{ from: owner2 }});

// Wait for delay period, then execute
await timelockMultisig.executeTimelockTransaction(txId, {{ from: timelockAdmin }});
```

## Security Best Practices

### Before Deployment
- ✅ Verify all owner addresses are correct
- ✅ Test on testnet before mainnet
- ✅ Have multiple owners confirm the deployment transaction
- ✅ Keep private keys secure
- ✅ Use hardware wallets for production

### After Deployment
- ✅ Fund the multisig wallet
- ✅ Test small transactions first
- ✅ Enable safe mode if needed
- ✅ Enable Gnosis compatibility if using with Gnosis Safe UI
- ✅ Document all procedures

## Multisig Types

### Basic Multisig
- Simple multisig wallet
- Supports ETH and ERC20 transfers
- Basic owner management
- Gnosis Safe compatible
- **Use case:** Small teams, simple fund management

### Timelock Multisig
- All features of basic multisig
- Transaction timelock mechanism
- Multi-tier confirmation requirements
- Emergency transactions
- **Use case:** DAOs, project funds, DeFi governance

## Testing

```bash
# Run all tests
npm test

# Run specific tests
npm run test:multisig
npm run test:timelock

# Run with coverage
npm run coverage
```

## Troubleshooting

### Deployment Fails
1. Check if you have sufficient ETH for gas fees
2. Verify owner addresses are valid
3. Ensure private key has sufficient balance
4. Check network connectivity

### Transaction Won't Execute
1. Verify you have enough confirmations
2. Check if transaction is already executed
3. Ensure you're connected to the right network

### Can't Verify Contract
1. Check Etherscan API key is correct
2. Wait for enough block confirmations (usually 5-6)
3. Ensure contract code matches on Etherscan

## Support

For issues and questions:
- Check the documentation: `MULTISIG_TEMPLATE_GUIDE.md`
- Review the test files for usage examples
- Test thoroughly on testnet before mainnet deployment

---

**⚠️  SECURITY WARNING:** This is a financial contract. Always test thoroughly before deploying to mainnet. Consider getting a professional audit for production use.
"""

        readme_path = project_path / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)

        print(f"   ✅ Created README.md")

    def setup_project(self, multisig_type, config_name, project_name):
        """Main setup function."""
        try:
            print("🚀 Multisig Wallet Setup")
            print("=" * 50)
            print(f"Type: {multisig_type}")
            print(f"Config: {config_name}")
            print(f"Project Name: {project_name}\n")

            # Validate inputs
            multisig_type = self.validate_type(multisig_type)
            config_name = self.validate_config(config_name)

            # Copy template
            project_path = self.copy_template(project_name, multisig_type, config_name)

            # Create .env.example
            self.create_env_example(project_path)

            # Create README
            self.create_readme(project_path, multisig_type, config_name)

            # Update configuration instructions
            self.update_config(project_path, config_name)

            print("\n" + "=" * 50)
            print("✅ Setup completed successfully!")
            print("\nNext steps:")
            print(f"1. cd {project_name}")
            print("2. npm install")
            print("3. Edit config/multisig.config.js with your owner addresses")
            print("4. cp .env.example .env")
            print("5. Edit .env with your private keys and API keys")
            print("6. npm run deploy:local")
            print(f"\nFor more information, see {project_name}/README.md")

        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Setup multisig wallet project")
    parser.add_argument(
        "--type",
        required=True,
        choices=["basic", "timelock"],
        help="Type of multisig wallet (basic or timelock)"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Configuration name (basic, dao, project, defi, or personal)"
    )
    parser.add_argument(
        "--name",
        default="multisig-wallet",
        help="Project name (default: multisig-wallet)"
    )

    args = parser.parse_args()

    setup = MultisigSetup()
    setup.setup_project(args.type, args.config, args.name)


if __name__ == "__main__":
    main()
