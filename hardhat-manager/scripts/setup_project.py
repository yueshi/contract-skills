#!/usr/bin/env python3
"""
Hardhat Project Setup Script

This script automates the creation of new Hardhat projects using predefined templates.
It supports basic, DeFi, NFT, and DAO project types with appropriate configurations.

Usage:
    python3 setup_project.py --template <template-type> --name <project-name> --network <target-network>

Examples:
    python3 setup_project.py --template nft --name my-nft-project --network polygon
    python3 setup_project.py --template defi --name defi-protocol --network ethereum
"""

import os
import sys
import argparse
import shutil
import subprocess
from pathlib import Path


class HardhatProjectSetup:
    def __init__(self):
        self.templates_dir = Path(__file__).parent.parent / "assets"
        self.current_dir = Path.cwd()

    def validate_template(self, template_type):
        """Validate that the template exists."""
        template_path = self.templates_dir / f"{template_type}-template"
        if not template_path.exists():
            raise ValueError(f"Template '{template_type}' not found. Available templates: {self.get_available_templates()}")
        return template_path

    def get_available_templates(self):
        """Get list of available templates."""
        templates = []
        if self.templates_dir.exists():
            for item in self.templates_dir.iterdir():
                if item.is_dir() and item.name.endswith("-template"):
                    templates.append(item.name.replace("-template", ""))
        return templates

    def validate_project_name(self, project_name):
        """Validate project name format."""
        if not project_name:
            raise ValueError("Project name cannot be empty")

        # Check for invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in project_name:
                raise ValueError(f"Project name cannot contain '{char}'")

        return True

    def validate_network(self, network):
        """Validate network configuration."""
        supported_networks = [
            'ethereum', 'polygon', 'arbitrum', 'optimism', 'bsc',
            'goerli', 'sepolia', 'mumbai', 'localhost', 'hardhat'
        ]

        if network.lower() not in supported_networks:
            raise ValueError(f"Network '{network}' not supported. Supported networks: {supported_networks}")

        return network.lower()

    def copy_template(self, template_path, project_name):
        """Copy template files to new project directory."""
        project_path = self.current_dir / project_name

        if project_path.exists():
            raise ValueError(f"Directory '{project_name}' already exists")

        # Copy template directory
        shutil.copytree(template_path, project_path)
        print(f"✅ Created project directory: {project_path}")

        return project_path

    def update_package_json(self, project_path, project_name):
        """Update package.json with project-specific information."""
        package_json_path = project_path / "package.json"

        if package_json_path.exists():
            import json
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)

            package_data['name'] = project_name.lower().replace(' ', '-')
            package_data['description'] = f"{project_name} - Hardhat Project"

            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)

            print(f"✅ Updated package.json")

    def create_env_file(self, project_path, network):
        """Create .env file with network-specific configuration."""
        env_path = project_path / ".env"

        env_content = f"""# Environment variables for {network}
PRIVATE_KEY=your_private_key_here
INFURA_API_KEY=your_infura_api_key_here
ETHERSCAN_API_KEY=your_etherscan_api_key_here

# Network specific configurations
NETWORK={network}
"""

        with open(env_path, 'w') as f:
            f.write(env_content)

        print(f"✅ Created .env file for {network}")

    def install_dependencies(self, project_path):
        """Install npm dependencies."""
        print("📦 Installing dependencies...")

        try:
            result = subprocess.run(
                ['npm', 'install'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
            else:
                print(f"⚠️  npm install completed with warnings: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("⚠️  npm install timed out, please run manually: npm install")
        except FileNotFoundError:
            print("⚠️  npm not found, please install Node.js and npm")

    def create_readme(self, project_path, project_name, template_type, network):
        """Create README.md with project-specific information."""
        readme_content = f"""# {project_name}

{template_type.title()} project built with Hardhat.

## Description

This project was generated using the Hardhat Manager skill with the {template_type} template.

## Development

### Prerequisites

- Node.js >= 16.0.0
- npm >= 8.0.0

### Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Copy .env.example to .env and fill in your environment variables:
   ```bash
   cp .env.example .env
   ```

3. Compile contracts:
   ```bash
   npx hardhat compile
   ```

4. Run tests:
   ```bash
   npx hardhat test
   ```

### Deployment

Deploy to {network}:
```bash
npx hardhat run scripts/deploy.js --network {network}
```

## Scripts

- `npx hardhat compile` - Compile contracts
- `npx hardhat test` - Run tests
- `npx hardhat node` - Start local node
- `npx hardhat run scripts/deploy.js --network <network>` - Deploy contracts

## Support

This project was created using the Hardhat Manager skill. For more information, refer to the skill documentation.
"""

        readme_path = project_path / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)

        print(f"✅ Created README.md")

    def setup_project(self, template_type, project_name, network):
        """Main project setup function."""
        try:
            print(f"🚀 Setting up {template_type} project: {project_name}")
            print(f"   Target network: {network}")
            print()

            # Validate inputs
            self.validate_template(template_type)
            self.validate_project_name(project_name)
            network = self.validate_network(network)

            # Get template path
            template_path = self.templates_dir / f"{template_type}-template"

            # Copy template
            project_path = self.copy_template(template_path, project_name)

            # Update project files
            self.update_package_json(project_path, project_name)
            self.create_env_file(project_path, network)
            self.create_readme(project_path, project_name, template_type, network)

            # Install dependencies
            self.install_dependencies(project_path)

            print()
            print(f"✅ Project '{project_name}' setup completed successfully!")
            print(f"📁 Location: {project_path}")
            print()
            print("Next steps:")
            print("1. Navigate to project directory:")
            print(f"   cd {project_name}")
            print("2. Update .env file with your private keys and API keys")
            print("3. Compile contracts:")
            print("   npx hardhat compile")
            print("4. Run tests:")
            print("   npx hardhat test")

        except Exception as e:
            print(f"❌ Error setting up project: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Set up a new Hardhat project")
    parser.add_argument("--template", required=True,
                       help="Project template (basic, defi, nft, dao)")
    parser.add_argument("--name", required=True,
                       help="Project name")
    parser.add_argument("--network", required=True,
                       help="Target network (ethereum, polygon, arbitrum, etc.)")

    args = parser.parse_args()

    setup = HardhatProjectSetup()
    setup.setup_project(args.template, args.name, args.network)


if __name__ == "__main__":
    main()