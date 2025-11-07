# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the **Contract Skills Repository** - a collection of specialized skills for Ethereum smart contract development and security auditing. It contains two main skill modules focused on Hardhat project management and Solidity security analysis.

## Skill Architecture

### hardhat-manager Skill
Comprehensive Hardhat development environment management tool for Ethereum smart contracts. Provides complete project lifecycle management from setup through deployment and maintenance.

### wake-auditor Skill
Automated Solidity smart contract security auditing tool using Wake Printer scripts and Python-based static analysis for vulnerability detection.

## Common Development Commands

### Hardhat Manager Commands
```bash
# Complete environment setup
python3 hardhat-manager/scripts/setup_hardhat.py [--version <version>] [--project-dir <directory>]

# Project initialization with templates
python3 hardhat-manager/scripts/setup_project.py --template <template-type> --name <project-name>

# AI-powered contract generation
python3 hardhat-manager/scripts/contract_generator.py --interactive
python3 hardhat-manager/scripts/contract_generator.py --type erc20 --name MyToken --supply 1000000

# Multi-chain deployment
python3 hardhat-manager/scripts/multi_chain_deployer.py --interactive
python3 hardhat-manager/scripts/multi_chain_deployer.py --chains ethereum,polygon,arbitrum --contract MyToken

# Contract deployment with verification
python3 hardhat-manager/scripts/deploy_contracts.py --network <network-name> --verify

# Security auditing and vulnerability scanning
python3 hardhat-manager/scripts/security_scanner.py --scan contracts/MyContract.sol --full-scan
python3 hardhat-manager/scripts/security_scanner.py --project . --tools slither,upgrade_security_analysis

# Gas usage analysis
python3 hardhat-manager/scripts/gas_analyzer.py --contract MyToken --optimize

# Real-time contract monitoring
python3 hardhat-manager/scripts/monitor.py --interactive
python3 hardhat-manager/scripts/monitor.py --contract 0x1234...abcd --network ethereum

# Contract verification
python3 hardhat-manager/scripts/verify_contracts.py --network <network-name> --address <contract-address>

# Upgrade management
python3 hardhat-manager/scripts/upgrade_manager.py --contract <contract-name> --new-implementation <new-address>
```

### Wake Auditor Commands
```bash
# Wake environment setup
python3 wake-auditor/scripts/wake_setup.py

# Contract scanning
python3 wake-auditor/scripts/contract_scanner.py --contract <contract-path>

# Vulnerability detection
python3 wake-auditor/scripts/vulnerability_detector.py --project <project-path>
```

### Standard Hardhat Commands (from templates)
```bash
npx hardhat compile           # Compile contracts
npx hardhat test              # Run tests
npx hardhat test:coverage     # Run test coverage
npx hardhat node              # Start local node
npx hardhat clean             # Clean artifacts
npx hardhat run <script>      # Execute script
npx hardhat console           # Open console

# Linting and code quality
npm run lint                  # Run solhint
npm run lint:fix              # Fix solhint issues
npm run size                  # Check contract sizes
npm run gas-report            # Generate gas usage report

# Deployment commands
npm run deploy:local          # Deploy to localhost
npm run deploy:testnet        # Deploy to testnet
npm run deploy:mainnet        # Deploy to mainnet
npm run deploy:polygon        # Deploy to Polygon
npm run deploy:arbitrum       # Deploy to Arbitrum

# Batch deployment with hardhat-deploy
npm run deploy:all:local      # Deploy all contracts to localhost
npm run deploy:all:testnet    # Deploy all contracts to testnet

# Contract verification
npm run verify                # Verify contract on block explorer
npm run verify:etherscan      # Verify on Etherscan
npm run verify:polygonscan    # Verify on Polygonscan
npm run verify:arbiscan       # Verify on Arbiscan

# Deployment management
npm run deploy:info           # List deployment information
npm run deploy:report         # Generate deployment report
npm run deploy:export         # Export deployment data
```

## Code Architecture and Structure

### Hardhat Manager Structure
- **scripts/**: Python automation scripts for Hardhat workflows
  - Core management: `setup_hardhat.py`, `setup_project.py`, `contract_generator.py`
  - Deployment: `deploy_contracts.py`, `multi_chain_deployer.py`, `verify_contracts.py`
  - Security: `security_scanner.py`, `monitor.py`, `upgrade_manager.py`
  - Analysis: `gas_analyzer.py`, `check_openzeppelin.py`
- **assets/**: Project templates and boilerplate code
  - `basic-template/`: Standard Hardhat project structure
  - `defi-template/`: DeFi protocols with token and staking contracts
  - `nft-template/`: NFT projects with ERC721/ERC1155 implementation
  - `dao-template/`: DAO governance and voting contracts
  - `multisig-template/`: Multi-signature wallet implementation
- **references/**: Comprehensive documentation for different development scenarios
  - Network configurations, deployment patterns, security checklists, testing strategies
- **design/**: Implementation plans and technical specifications

### Wake Auditor Structure
- **scripts/**: Python-based security analysis tools
  - `wake_setup.py`: Wake environment configuration
  - `contract_scanner.py`: Contract analysis and scanning
  - `vulnerability_detector.py`: Security vulnerability detection
- **references/**: Solidity security patterns and Wake documentation

### Project Templates (hardhat-manager/assets/)
Each template includes:
- Complete Hardhat configuration (`hardhat.config.js`)
- Sample contracts with best practices
- Comprehensive test suites
- Deployment scripts for multiple networks
- Package.json with full dependency set

## Supported Networks

### Mainnet Networks
- Ethereum Mainnet
- Polygon
- Arbitrum
- Optimism
- BSC (Binance Smart Chain)

### Testnet Networks
- Goerli
- Sepolia
- Mumbai (Polygon testnet)
- And other standard testnets

## Security Tools Integration

### Supported Security Scanners
- **Slither**: Static analysis framework for Solidity
- **Mythril**: Symbolic execution tool
- **Echidna**: Property-based fuzz testing
- **Custom Pattern Matching**: Vulnerability pattern detection
- **Upgrade Security Analysis**: Specialized analysis for upgradeable contracts

### Security Features
- Automated vulnerability detection with CWE mapping
- Contract verification on multiple block explorers
- Real-time monitoring and alerting
- Gas optimization analysis
- Upgrade security validation
- Pattern-based security checks

## Development Workflow Integration

### Project Setup Flow
1. Use `setup_hardhat.py` for complete environment installation
2. Choose appropriate template from `assets/` directory
3. Initialize project with `setup_project.py`
4. Configure network settings from `references/network_configs.md`

### Development Cycle
1. Contract generation with `contract_generator.py`
2. Local testing with `npx hardhat test`
3. Security scanning with `security_scanner.py`
4. Gas optimization with `gas_analyzer.py`
5. Multi-chain deployment with `multi_chain_deployer.py`

### Monitoring and Maintenance
1. Real-time monitoring with `monitor.py`
2. Contract upgrades with `upgrade_manager.py`
3. Ongoing security audits with security scanning tools
4. Performance optimization and gas analysis

## Dependencies and Requirements

### Python Dependencies
- Standard web3 libraries (ethers, web3.py)
- Security scanning tools (slither, mythril when available)
- Monitoring and alerting frameworks

### Node.js Dependencies (from templates)
- Hardhat development framework
- OpenZeppelin contracts library
- Ethers.js for contract interaction
- Testing frameworks (Chai, Mocha)
- Deployment tools (hardhat-deploy, hardhat-upgrades)
- Code quality tools (solhint, solidity-coverage)

## Best Practices

- Use provided templates for consistent project structure
- Run security scans before deployment
- Test on multiple networks before mainnet deployment
- Use automated verification for all deployed contracts
- Monitor deployed contracts with the monitoring system
- Follow security checklists from `references/security_checklist.md`