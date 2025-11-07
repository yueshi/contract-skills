#!/usr/bin/env python3
"""
Multi-Chain Deployment Coordinator

Deploys smart contracts across multiple Ethereum-compatible chains simultaneously
with coordinated timing and verification. Supports cross-chain applications
and manages complex deployment scenarios.

Usage:
    python3 multi_chain_deployer.py --config <deployment-config.json>
    python3 multi_chain_deployer.py --interactive
    python3 multi_chain_deployer.py --chains ethereum,polygon,arbitrum --contract <contract-name>
"""

import os
import sys
import json
import time
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class MultiChainDeployer:
    def __init__(self):
        self.configs_dir = Path("configs")
        self.deployments_dir = Path("deployments")
        self.reports_dir = Path("reports")

        # Ensure directories exist
        self.configs_dir.mkdir(exist_ok=True)
        self.deployments_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)

        # Predefined network configurations
        self.network_configs = {
            "ethereum": {
                "name": "Ethereum Mainnet",
                "chainId": 1,
                "rpc": "https://mainnet.infura.io/v3/{INFURA_API_KEY}",
                "gasPrice": "auto",
                "confirmations": 2,
                "blockExplorer": "https://etherscan.io",
                "explorerApi": "https://api.etherscan.io/api"
            },
            "polygon": {
                "name": "Polygon Mainnet",
                "chainId": 137,
                "rpc": "https://polygon-rpc.com",
                "gasPrice": "auto",
                "confirmations": 5,
                "blockExplorer": "https://polygonscan.com",
                "explorerApi": "https://api.polygonscan.com/api"
            },
            "arbitrum": {
                "name": "Arbitrum One",
                "chainId": 42161,
                "rpc": "https://arbitrum-mainnet.infura.io/v3/{INFURA_API_KEY}",
                "gasPrice": "auto",
                "confirmations": 3,
                "blockExplorer": "https://arbiscan.io",
                "explorerApi": "https://api.arbiscan.io/api"
            },
            "optimism": {
                "name": "Optimism",
                "chainId": 10,
                "rpc": "https://optimism-mainnet.infura.io/v3/{INFURA_API_KEY}",
                "gasPrice": "auto",
                "confirmations": 3,
                "blockExplorer": "https://optimistic.etherscan.io",
                "explorerApi": "https://api-optimistic.etherscan.io/api"
            },
            "bsc": {
                "name": "Binance Smart Chain",
                "chainId": 56,
                "rpc": "https://bsc-dataseed1.binance.org",
                "gasPrice": "auto",
                "confirmations": 3,
                "blockExplorer": "https://bscscan.com",
                "explorerApi": "https://api.bscscan.com/api"
            },
            "avalanche": {
                "name": "Avalanche C-Chain",
                "chainId": 43114,
                "rpc": "https://api.avax.network/ext/bc/C/rpc",
                "gasPrice": "auto",
                "confirmations": 2,
                "blockExplorer": "https://snowtrace.io",
                "explorerApi": "https://api.snowtrace.io/api"
            },
            "goerli": {
                "name": "Goerli Testnet",
                "chainId": 5,
                "rpc": "https://goerli.infura.io/v3/{INFURA_API_KEY}",
                "gasPrice": 20000000000,
                "confirmations": 1,
                "blockExplorer": "https://goerli.etherscan.io",
                "explorerApi": "https://api-goerli.etherscan.io/api"
            },
            "sepolia": {
                "name": "Sepolia Testnet",
                "chainId": 11155111,
                "rpc": "https://sepolia.infura.io/v3/{INFURA_API_KEY}",
                "gasPrice": 20000000000,
                "confirmations": 1,
                "blockExplorer": "https://sepolia.etherscan.io",
                "explorerApi": "https://api-sepolia.etherscan.io/api"
            },
            "mumbai": {
                "name": "Polygon Mumbai",
                "chainId": 80001,
                "rpc": "https://rpc-mumbai.maticvigil.com",
                "gasPrice": 20000000000,
                "confirmations": 2,
                "blockExplorer": "https://mumbai.polygonscan.com",
                "explorerApi": "https://api-testnet.polygonscan.com/api"
            }
        }

    def create_deployment_config(self, chains, contract_name, constructor_args=None):
        """Create a deployment configuration template."""
        config = {
            "deployment": {
                "contract": contract_name,
                "constructorArgs": constructor_args or [],
                "timestamp": datetime.now().isoformat(),
                "strategy": "simultaneous",  # simultaneous, sequential, coordinated
                "retryAttempts": 3,
                "retryDelay": 5000,  # milliseconds
                "verificationEnabled": True
            },
            "networks": {}
        }

        for chain in chains:
            if chain in self.network_configs:
                config["networks"][chain] = {
                    "enabled": True,
                    "priority": 1,  # 1-5, lower = higher priority
                    "customGasPrice": None,
                    "customTimeout": 300000,  # 5 minutes
                    "skipVerification": False,
                    "dependencies": []  # networks this deployment depends on
                }
            else:
                print(f"⚠️  Unknown network: {chain}")

        return config

    def save_config(self, config, filename=None):
        """Save deployment configuration to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"deployment_config_{timestamp}.json"

        config_file = self.configs_dir / filename
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✅ Configuration saved to: {config_file}")
        return config_file

    def load_config(self, config_file):
        """Load deployment configuration from file."""
        config_path = Path(config_file)
        if not config_path.exists():
            config_path = self.configs_dir / config_file

        with open(config_path, 'r') as f:
            config = json.load(f)

        print(f"✅ Configuration loaded from: {config_path}")
        return config

    def deploy_to_network(self, network, config):
        """Deploy contract to a specific network."""
        print(f"🚀 Starting deployment to {network}...")

        try:
            network_config = self.network_configs[network]
            network_settings = config["deployment"]["networks"][network]

            # Build deployment command
            cmd = [
                "npx", "hardhat", "run",
                f"scripts/deploy_{config['deployment']['contract'].lower()}.js",
                "--network", network
            ]

            # Add custom settings if specified
            env = os.environ.copy()
            if network_settings.get("customGasPrice"):
                env["GAS_PRICE"] = str(network_settings["customGasPrice"])

            # Execute deployment
            print(f"📋 Executing: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                env=env,
                timeout=network_settings.get("customTimeout", 300000)
            )

            if result.returncode == 0:
                print(f"✅ Deployment to {network} successful!")
                deployment_info = self.parse_deployment_output(result.stdout, network)
                deployment_info["network"] = network
                deployment_info["timestamp"] = datetime.now().isoformat()

                # Verify contract if enabled
                if config["deployment"]["verificationEnabled"] and not network_settings.get("skipVerification"):
                    print(f"🔍 Verifying contract on {network}...")
                    verification_info = self.verify_contract(network, deployment_info)
                    deployment_info["verification"] = verification_info

                return {
                    "success": True,
                    "network": network,
                    "deployment": deployment_info,
                    "output": result.stdout
                }
            else:
                print(f"❌ Deployment to {network} failed: {result.stderr}")
                return {
                    "success": False,
                    "network": network,
                    "error": result.stderr,
                    "output": result.stdout
                }

        except subprocess.TimeoutExpired:
            print(f"❌ Deployment to {network} timed out")
            return {
                "success": False,
                "network": network,
                "error": "Deployment timed out"
            }
        except Exception as e:
            print(f"❌ Deployment to {network} failed: {e}")
            return {
                "success": False,
                "network": network,
                "error": str(e)
            }

    def parse_deployment_output(self, output, network):
        """Parse deployment output to extract contract information."""
        deployment_info = {}

        lines = output.split('\n')
        for line in lines:
            if "Contract address:" in line or "deployed to:" in line:
                import re
                addresses = re.findall(r'0x[a-fA-F0-9]{40}', line)
                if addresses:
                    deployment_info["contractAddress"] = addresses[0]

            elif "Transaction hash:" in line:
                import re
                tx_hashes = re.findall(r'0x[a-fA-F0-9]{64}', line)
                if tx_hashes:
                    deployment_info["transactionHash"] = tx_hashes[0]

            elif "Gas used:" in line:
                import re
                gas_used = re.search(r'Gas used:\s*(\d+)', line)
                if gas_used:
                    deployment_info["gasUsed"] = int(gas_used.group(1))

        if "contractAddress" not in deployment_info:
            # Try to extract from other patterns
            import re
            addresses = re.findall(r'0x[a-fA-F0-9]{40}', output)
            if addresses:
                deployment_info["contractAddress"] = addresses[-1]  # Usually the last address is the deployed contract

        return deployment_info

    def verify_contract(self, network, deployment_info):
        """Verify contract on block explorer."""
        contract_address = deployment_info.get("contractAddress")
        if not contract_address:
            return {"success": False, "error": "No contract address found"}

        try:
            cmd = [
                "npx", "hardhat", "verify",
                "--network", network,
                contract_address
            ]

            constructor_args = deployment_info.get("constructorArgs", [])
            if constructor_args:
                cmd.extend(constructor_args)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120000  # 2 minutes
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "Contract verified successfully",
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "output": result.stdout
                }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Verification timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_deployment(self, config):
        """Execute multi-chain deployment based on configuration."""
        deployment_strategy = config["deployment"]["strategy"]
        networks = [net for net, settings in config["networks"].items() if settings.get("enabled", True)]

        print(f"🎯 Starting multi-chain deployment strategy: {deployment_strategy}")
        print(f"📍 Target networks: {', '.join(networks)}")
        print(f"📦 Contract: {config['deployment']['contract']}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        results = {}

        if deployment_strategy == "simultaneous":
            results = self.deploy_simultaneous(networks, config)
        elif deployment_strategy == "sequential":
            results = self.deploy_sequential(networks, config)
        elif deployment_strategy == "coordinated":
            results = self.deploy_coordinated(networks, config)
        else:
            raise ValueError(f"Unknown deployment strategy: {deployment_strategy}")

        # Generate deployment report
        self.generate_deployment_report(results, config)
        return results

    def deploy_simultaneous(self, networks, config):
        """Deploy to all networks simultaneously."""
        print("🚀 Simultaneous deployment to all networks...")
        print()

        results = {}
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=min(len(networks), 5)) as executor:
            # Submit all deployment tasks
            future_to_network = {
                executor.submit(self.deploy_to_network, network, config): network
                for network in networks
            }

            # Process results as they complete
            for future in as_completed(future_to_network):
                network = future_to_network[future]
                try:
                    result = future.result()
                    results[network] = result

                    if result["success"]:
                        print(f"✅ {network}: SUCCESS - {result['deployment'].get('contractAddress', 'Unknown')}")
                    else:
                        print(f"❌ {network}: FAILED - {result.get('error', 'Unknown error')}")

                except Exception as exc:
                    print(f"❌ {network}: EXCEPTION - {exc}")
                    results[network] = {
                        "success": False,
                        "network": network,
                        "error": str(exc)
                    }

        end_time = time.time()
        print(f"\n⏱️  Simultaneous deployment completed in {end_time - start_time:.2f} seconds")

        return results

    def deploy_sequential(self, networks, config):
        """Deploy to networks sequentially."""
        print("📋 Sequential deployment to networks...")
        print()

        results = {}
        start_time = time.time()

        # Sort networks by priority
        sorted_networks = sorted(
            networks,
            key=lambda n: config["networks"][n].get("priority", 1)
        )

        for i, network in enumerate(sorted_networks, 1):
            print(f"📍 [{i}/{len(sorted_networks)}] Deploying to {network}...")

            result = self.deploy_to_network(network, config)
            results[network] = result

            if result["success"]:
                print(f"✅ {network}: SUCCESS - {result['deployment'].get('contractAddress', 'Unknown')}")
            else:
                print(f"❌ {network}: FAILED - {result.get('error', 'Unknown error')}")

                # Check if we should continue or stop
                if i < len(sorted_networks):
                    response = input(f"Continue with remaining networks? (y/N): ").strip().lower()
                    if response != 'y':
                        print("🛑 Sequential deployment stopped by user")
                        break

            # Small delay between deployments
            if i < len(sorted_networks):
                time.sleep(2)

        end_time = time.time()
        print(f"\n⏱️  Sequential deployment completed in {end_time - start_time:.2f} seconds")

        return results

    def deploy_coordinated(self, networks, config):
        """Deploy to networks with coordination."""
        print("🎭 Coordinated deployment with synchronization...")
        print()

        results = {}
        start_time = time.time()

        # Phase 1: Deploy to priority networks
        priority_networks = [n for n in networks if config["networks"][n].get("priority", 1) == 1]
        if priority_networks:
            print("🎯 Phase 1: Deploying to priority networks...")
            phase1_results = self.deploy_simultaneous(priority_networks, config)
            results.update(phase1_results)

        # Phase 2: Wait for coordination time
        print("⏳ Phase 2: Coordination delay...")
        time.sleep(10)  # Wait for block confirmations

        # Phase 3: Deploy to remaining networks
        remaining_networks = [n for n in networks if n not in priority_networks]
        if remaining_networks:
            print("🎯 Phase 3: Deploying to remaining networks...")
            phase3_results = self.deploy_simultaneous(remaining_networks, config)
            results.update(phase3_results)

        end_time = time.time()
        print(f"\n⏱️  Coordinated deployment completed in {end_time - start_time:.2f} seconds")

        return results

    def generate_deployment_report(self, results, config):
        """Generate comprehensive deployment report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"deployment_report_{timestamp}.json"

        report = {
            "summary": {
                "totalNetworks": len(results),
                "successfulDeployments": len([r for r in results.values() if r["success"]]),
                "failedDeployments": len([r for r in results.values() if not r["success"]]),
                "deploymentStrategy": config["deployment"]["strategy"],
                "contract": config["deployment"]["contract"],
                "timestamp": datetime.now().isoformat()
            },
            "networks": {},
            "config": config
        }

        for network, result in results.items():
            report["networks"][network] = {
                "success": result["success"],
                "contractAddress": result.get("deployment", {}).get("contractAddress") if result["success"] else None,
                "transactionHash": result.get("deployment", {}).get("transactionHash") if result["success"] else None,
                "gasUsed": result.get("deployment", {}).get("gasUsed") if result["success"] else None,
                "verification": result.get("deployment", {}).get("verification") if result["success"] else None,
                "error": result.get("error") if not result["success"] else None,
                "output": result.get("output", "")[:1000]  # Truncate output
            }

        # Save JSON report
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Generate markdown report
        markdown_report = self.generate_markdown_report(report)
        markdown_file = self.reports_dir / f"deployment_report_{timestamp}.md"
        with open(markdown_file, 'w') as f:
            f.write(markdown_report)

        print(f"\n📊 Deployment reports generated:")
        print(f"   JSON: {report_file}")
        print(f"   Markdown: {markdown_file}")

        # Print summary
        self.print_deployment_summary(report)

        return report_file

    def generate_markdown_report(self, report):
        """Generate markdown deployment report."""
        summary = report["summary"]

        markdown = f"""# Multi-Chain Deployment Report

## Summary

- **Contract**: {summary['contract']}
- **Strategy**: {summary['strategy']}
- **Total Networks**: {summary['totalNetworks']}
- **Successful**: {summary['successfulDeployments']}
- **Failed**: {summary['failedDeployments']}
- **Timestamp**: {summary['timestamp']}

## Network Results

| Network | Status | Contract Address | Transaction Hash | Gas Used | Verification |
|---------|--------|------------------|------------------|----------|--------------|
"""

        for network, result in report["networks"].items():
            status = "✅ Success" if result["success"] else "❌ Failed"
            address = result["contractAddress"] or "N/A"
            tx_hash = result["transactionHash"] or "N/A"
            gas_used = str(result["gasUsed"]) if result["gasUsed"] else "N/A"

            if result["success"] and result["verification"]:
                verification = "✅ Verified" if result["verification"]["success"] else "❌ Failed"
            else:
                verification = "N/A"

            markdown += f"| {network} | {status} | {address} | {tx_hash} | {gas_used} | {verification} |\n"

        # Add failed deployments details
        failed_networks = [n for n, r in report["networks"].items() if not r["success"]]
        if failed_networks:
            markdown += "\n## Failed Deployments\n\n"
            for network in failed_networks:
                result = report["networks"][network]
                markdown += f"### {network}\n"
                markdown += f"**Error**: {result['error']}\n\n"

        return markdown

    def print_deployment_summary(self, report):
        """Print deployment summary to console."""
        summary = report["summary"]

        print("\n" + "="*60)
        print("📊 DEPLOYMENT SUMMARY")
        print("="*60)
        print(f"Contract: {summary['contract']}")
        print(f"Strategy: {summary['strategy']}")
        print(f"Success Rate: {summary['successfulDeployments']}/{summary['totalNetworks']} ({summary['successfulDeployments']/summary['totalNetworks']*100:.1f}%)")
        print()

        successful = [n for n, r in report["networks"].items() if r["success"]]
        failed = [n for n, r in report["networks"].items() if not r["success"]]

        if successful:
            print("✅ Successful Deployments:")
            for network in successful:
                result = report["networks"][network]
                print(f"   {network}: {result['contractAddress']}")

        if failed:
            print("\n❌ Failed Deployments:")
            for network in failed:
                result = report["networks"][network]
                print(f"   {network}: {result['error']}")

        print("="*60)

    def interactive_mode(self):
        """Interactive multi-chain deployment setup."""
        print("🎯 Interactive Multi-Chain Deployment")
        print("="*50)

        # Select contract
        contract_files = list(Path("scripts").glob("deploy_*.js"))
        if not contract_files:
            print("❌ No deployment scripts found in scripts/ directory")
            return

        print("\nAvailable contracts:")
        for i, file in enumerate(contract_files, 1):
            contract_name = file.stem.replace("deploy_", "").replace(".js", "")
            print(f"{i}. {contract_name}")

        while True:
            try:
                choice = input(f"\nSelect contract (1-{len(contract_files)}): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(contract_files):
                    break
                print("Invalid choice.")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled")
                return

        selected_file = contract_files[int(choice) - 1]
        contract_name = selected_file.stem.replace("deploy_", "").replace(".js", "")

        # Select networks
        print("\nAvailable networks:")
        network_list = list(self.network_configs.keys())
        for i, network in enumerate(network_list, 1):
            config = self.network_configs[network]
            print(f"{i}. {config['name']} ({network})")

        print("\nEnter network numbers separated by commas (e.g., 1,3,5):")
        while True:
            try:
                input_str = input("Networks: ").strip()
                selected_indices = [int(x.strip()) for x in input_str.split(",")]
                selected_networks = [network_list[i-1] for i in selected_indices if 1 <= i <= len(network_list)]
                if selected_networks:
                    break
                print("Invalid selection.")
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Operation cancelled")
                return

        # Select deployment strategy
        print("\nDeployment strategies:")
        print("1. Simultaneous - Deploy to all networks at once")
        print("2. Sequential - Deploy one by one with priority")
        print("3. Coordinated - Two-phase deployment with synchronization")

        while True:
            try:
                strategy_choice = input("Select strategy (1-3): ").strip()
                if strategy_choice in ["1", "2", "3"]:
                    break
                print("Invalid choice.")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled")
                return

        strategies = {"1": "simultaneous", "2": "sequential", "3": "coordinated"}
        strategy = strategies[strategy_choice]

        # Constructor arguments (optional)
        constructor_args = []
        args_input = input("\nConstructor arguments (comma-separated, leave empty if none): ").strip()
        if args_input:
            constructor_args = [arg.strip() for arg in args_input.split(",")]

        # Create configuration
        config = self.create_deployment_config(selected_networks, contract_name, constructor_args)
        config["deployment"]["strategy"] = strategy

        # Save configuration
        config_file = self.save_config(config)
        print(f"\n✅ Configuration saved to: {config_file}")

        # Confirm deployment
        confirm = input(f"\n🚀 Ready to deploy {contract_name} to {len(selected_networks)} networks using {strategy} strategy. Continue? (y/N): ").strip().lower()
        if confirm == 'y':
            # Execute deployment
            results = self.execute_deployment(config)

            # Ask if user wants to save deployment addresses
            successful_deployments = [n for n, r in results.items() if r["success"]]
            if successful_deployments:
                save_addresses = input("\n💾 Save successful deployment addresses to file? (y/N): ").strip().lower()
                if save_addresses == 'y':
                    self.save_deployment_addresses(contract_name, results)
        else:
            print("❌ Deployment cancelled")


def main():
    parser = argparse.ArgumentParser(description="Multi-chain deployment coordinator")
    parser.add_argument("--config", help="Deployment configuration file")
    parser.add_argument("--chains", help="Comma-separated list of chains")
    parser.add_argument("--contract", help="Contract name to deploy")
    parser.add_argument("--strategy", choices=["simultaneous", "sequential", "coordinated"],
                       help="Deployment strategy")
    parser.add_argument("--interactive", action="store_true",
                       help="Interactive mode")
    parser.add_argument("--list-networks", action="store_true",
                       help="List available networks")

    args = parser.parse_args()

    deployer = MultiChainDeployer()

    if args.list_networks:
        print("Available networks:")
        for network, config in deployer.network_configs.items():
            print(f"  {network}: {config['name']} (Chain ID: {config['chainId']})")
        return

    if args.interactive:
        deployer.interactive_mode()
    elif args.config:
        try:
            config = deployer.load_config(args.config)
            deployer.execute_deployment(config)
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
    elif args.chains and args.contract:
        chains = [chain.strip() for chain in args.chains.split(",")]
        config = deployer.create_deployment_config(chains, args.contract)
        if args.strategy:
            config["deployment"]["strategy"] = args.strategy

        config_file = deployer.save_config(config)
        deployer.execute_deployment(config)
    else:
        print("❌ Please provide --config file, --chains and --contract, or use --interactive mode")
        parser.print_help()


if __name__ == "__main__":
    import subprocess
    main()