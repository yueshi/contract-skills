---
name: hardhat-manager
description: Comprehensive Hardhat development environment management tool. This skill should be used when working with Ethereum smart contracts using Hardhat - including project setup, contract compilation, testing, deployment, verification, and maintenance workflows.
---

# Hardhat Manager

## Overview

This skill provides complete Hardhat project lifecycle management, from initial project setup through deployment and maintenance. It automates common development tasks, provides project templates for different use cases, and ensures best practices for smart contract development.

## Workflow Decision Tree

Determine the appropriate workflow based on your current needs:

**Starting a new project?**
→ Use "Project Setup" workflow

**Working with existing project?**
→ Check project type (Basic, DeFi, NFT, DAO)
→ Follow "Development & Testing" workflow

**Ready to deploy?**
→ Review "Deployment" workflow based on target network

**Post-deployment tasks?**
→ Use "Maintenance & Verification" workflow

## Hardhat Environment Setup

### Complete Environment Installation

For users new to Hardhat or needing a fresh development environment, use the automated setup script:

```bash
python3 scripts/setup_hardhat.py [--version <version>] [--project-dir <directory>]
```

**Features:**
- **System Requirements Check** - Verifies Node.js, npm, and system compatibility
- **Node.js Installation** - Automatically installs Node.js on macOS/Linux
- **Hardhat Installation** - Installs Hardhat with recommended dependencies
- **Project Initialization** - Creates a complete project structure
- **Configuration Setup** - Generates hardhat.config.js and environment files
- **Sample Contracts** - Includes working example contracts and tests

**Examples:**
```bash
# Quick setup in current directory
python3 scripts/setup_hardhat.py

# Setup in specific directory with latest version
python3 scripts/setup_hardhat.py --project-dir ./my-hardhat-project

# Setup with specific version
python3 scripts/setup_hardhat.py --version 2.17.0
```

**Supported Systems:**
- **macOS** - Automatic installation via Homebrew
- **Linux** - Ubuntu/Debian/CentOS via NodeSource repositories
- **Windows** - Manual installation instructions provided

**What Gets Installed:**
- Node.js 16+ and npm 8+ (if not present)
- Hardhat with core development tools
- Ethers.js and Chai for testing
- Gas reporter and coverage tools
- Sample contracts, tests, and deployment scripts

### Manual Environment Setup

If you prefer manual setup or already have Node.js installed:

1. **Install Node.js** (version 16+ required)
   ```bash
   # Check if installed
   node --version
   npm --version
   ```

2. **Install Hardhat globally**
   ```bash
   npm install -g hardhat
   ```

3. **Create new project**
   ```bash
   mkdir my-hardhat-project
   cd my-hardhat-project
   npm init -y
   npm install --save-dev hardhat
   npx hardhat init
   ```

## AI-Powered Contract Generation

### Smart Contract Code Generator

Generate production-ready smart contracts with best practices automatically:

```bash
python3 scripts/contract_generator.py [--type <contract-type>] --name <contract-name>
```

**Supported Contract Types:**
- **ERC20 Tokens** - Standard fungible tokens with advanced features
- **ERC721 NFTs** - Non-fungible tokens with royalty support
- **DeFi Vaults** - Yield farming and staking contracts
- **Generic Contracts** - Custom contract templates

**Features:**
- **Best Practices Built-in** - Security patterns, gas optimization, proper event emission
- **Auto-Generated Tests** - Comprehensive test suites with edge cases
- **Deployment Scripts** - Ready-to-use deployment scripts with verification
- **Interactive Mode** - Guided contract creation with customization options
- **Template System** - Extensible templates for different use cases

**Examples:**
```bash
# Interactive contract creation
python3 scripts/contract_generator.py --interactive

# Generate ERC20 token
python3 scripts/contract_generator.py --type erc20 --name MyToken --symbol MTK --supply 1000000

# Generate NFT collection
python3 scripts/contract_generator.py --type nft --name MyCollection --symbol NFT --max-supply 10000
```

**Generated Files:**
- Smart contract source code with full documentation
- Comprehensive test suite with multiple test scenarios
- Deployment script with verification support
- Configuration templates for different networks

## Multi-Chain Deployment Coordination

### Cross-Chain Deployment Manager

Deploy and manage contracts across multiple Ethereum-compatible chains simultaneously:

```bash
python3 scripts/multi_chain_deployer.py [--config <config-file>] [--chains <chains>]
```

**Deployment Strategies:**
- **Simultaneous** - Deploy to all networks at once for fastest deployment
- **Sequential** - Deploy one by one with priority ordering and dependency management
- **Coordinated** - Two-phase deployment with synchronization for complex applications

**Supported Networks:**
- **Layer 1**: Ethereum, BSC, Avalanche
- **Layer 2**: Polygon, Arbitrum, Optimism
- **Testnets**: Goerli, Sepolia, Mumbai

**Features:**
- **Intelligent Retry Logic** - Automatic retry with exponential backoff
- **Real-time Verification** - Automatic contract verification on block explorers
- **Deployment Reports** - Comprehensive JSON and markdown reports
- **Gas Optimization** - Cross-chain gas price optimization
- **Dependency Management** - Handle contract dependencies across chains

**Examples:**
```bash
# Interactive multi-chain deployment
python3 scripts/multi_chain_deployer.py --interactive

# Deploy to multiple networks simultaneously
python3 scripts/multi_chain_deployer.py --chains ethereum,polygon,arbitrum --contract MyToken --strategy simultaneous

# Coordinated deployment with configuration
python3 scripts/multi_chain_deployer.py --config deployment_config.json
```

**Configuration Management:**
- JSON-based deployment configurations
- Network-specific settings and priorities
- Constructor arguments and verification settings
- Custom gas prices and timeouts

## Real-Time Contract Monitoring

### Contract Monitoring and Alerting System

Monitor deployed contracts in real-time with configurable alerts and notifications:

```bash
python3 scripts/monitor.py [--config <config-file>] [--contract <address> --network <network>]
```

**Monitoring Capabilities:**
- **Balance Monitoring** - Track ETH and token balances with threshold alerts
- **Transaction Analysis** - Monitor transaction frequency and gas usage patterns
- **Event Tracking** - Real-time event monitoring for important contract events
- **Health Checks** - Automated contract health and availability monitoring

**Alert Channels:**
- **Email Alerts** - SMTP-based email notifications with detailed reports
- **Webhook Integration** - Custom webhook endpoints for alert forwarding
- **Discord Notifications** - Rich embed notifications for Discord servers
- **Slack Integration** - Channel notifications with formatted messages

**Alert Types:**
- **Info** - General contract events and updates
- **Warning** - Unusual activity or potential issues
- **Critical** - Serious problems requiring immediate attention

**Examples:**
```bash
# Interactive monitoring setup
python3 scripts/monitor.py --interactive

# Monitor specific contract
python3 scripts/monitor.py --contract 0x1234...abcd --network ethereum

# Load monitoring configuration
python3 scripts/monitor.py --config monitor_config.json
```

**Monitoring Features:**
- **Configurable Intervals** - Custom monitoring frequency (30s to hours)
- **Historical Data** - Store and analyze historical alert patterns
- **Performance Metrics** - Track gas usage, transaction frequency, and user activity
- **Automated Reports** - Generate comprehensive monitoring reports

## Smart Contract Security Audit & Vulnerability Scanning

### Comprehensive Security Scanner

Perform automated security audits using multiple industry-standard tools and pattern-based vulnerability detection:

```bash
python3 scripts/security_scanner.py [--scan <contract-path>] [--project <project-path>] [--tools <tools>]
```

**Security Analysis Tools:**
- **Slither** - Static analysis framework for Solidity with comprehensive vulnerability detection
- **Mythril** - Symbolic execution tool for deep contract analysis
- **Echidna** - Property-based fuzz testing framework
- **Pattern Matching** - Custom vulnerability pattern detection for common issues
- **Security Rules** - Custom security rules and best practices validation
- **Upgrade Security Analysis** - Specialized analysis for upgradeable contract security

**Vulnerability Detection:**
- **Critical Issues** - Reentrancy, delegatecall vulnerabilities, integer overflow/underflow
- **High Severity** - Access control issues, uninitialized storage, logical errors
- **Medium Severity** - Gas optimization issues, event emission problems
- **Warning/Info** - Code quality issues, potential improvements
- **Upgrade-specific** - Storage collision risks, proxy pattern compatibility, initialization issues

**Severity Classification:**
- **Critical** (CWE-843, CWE-787) - Immediate security risks requiring immediate attention
- **High** (CWE-20, CWE-119) - Serious vulnerabilities that should be fixed before deployment
- **Medium** (CWE-200, CWE-285) - Important security issues that should be addressed
- **Warning** - Potential security concerns that merit review
- **Info/Low** - Minor issues and code quality improvements

**Upgrade Security Analysis Features:**
- **Storage Layout Analysis** - Detect potential storage collisions in upgradeable contracts
- **Proxy Pattern Compatibility** - Validate OpenZeppelin upgradeable patterns
- **Constructor Security** - Check for constructor vs. initializer pattern issues
- **Delegatecall Safety** - Identify unsafe delegatecall usage in upgradeable context
- **Self-destruct Detection** - Flag self-destruct patterns that break proxy functionality
- **External Call Complexity** - Assess external call risks in upgradeable contracts

**Report Generation:**
- **JSON Reports** - Machine-readable detailed vulnerability reports with CWE mapping
- **Markdown Reports** - Human-readable security audit reports with code snippets
- **Executive Summary** - High-level security overview with severity distribution
- **Remediation Guidance** - Specific recommendations for each identified issue
- **CWE Mapping** - Industry-standard vulnerability classification

**Examples:**
```bash
# Interactive security scanning
python3 scripts/security_scanner.py --interactive

# Comprehensive scan with all tools
python3 scripts/security_scanner.py --scan contracts/MyContract.sol --full-scan

# Scan specific tools only
python3 scripts/security_scanner.py --project . --tools slither,upgrade_security_analysis

# Create scan configuration
python3 scripts/security_scanner.py --create-config --project .

# List available security tools
python3 scripts/security_scanner.py --list-tools
```

**CI/CD Integration:**
```bash
# Setup automated security scanning
python3 scripts/security_scanner.py --setup-ci

# This creates:
# - GitHub Actions workflow for automated scanning
# - Pre-commit hooks for development-time security checks
# - Configuration files for continuous security monitoring
```

**Advanced Features:**
- **Automated Tool Installation** - Installs missing security tools automatically
- **Pattern-based Detection** - Custom vulnerability patterns for emerging threats
- **Deduplication** - Intelligent vulnerability deduplication across tools
- **Historical Tracking** - Track security improvements over time
- **Threshold-based Alerting** - Configurable alert thresholds for different severity levels

**Security Best Practices Integration:**
- **Event Emission Validation** - Ensure critical state changes emit appropriate events
- **Access Control Verification** - Validate proper access control mechanisms
- **Gas Optimization Analysis** - Identify potential gas optimization opportunities
- **Function Visibility Checks** - Ensure proper function visibility modifiers
- **Constructor Security Review** - Validate secure initialization patterns

## Project Setup

### Step 1: Choose Project Template

Select appropriate template from `assets/` directory:
- `basic-template/` - Standard smart contract project
- `defi-template/` - DeFi protocols with token and staking contracts
- `nft-template/` - NFT projects with ERC721/ERC1155 contracts
- `dao-template/` - DAO governance and voting contracts

### Step 2: Initialize Project

Use the setup script to create a new Hardhat project:

```bash
python3 scripts/setup_project.py --template <template-type> --name <project-name> --network <target-network>
```

**Example:**
```bash
python3 scripts/setup_project.py --template nft --name my-nft-project --network ethereum
```

### Step 3: Configure Environment

1. Copy appropriate network configuration from `references/network_configs.md`
2. Set up environment variables in `.env` file
3. Install dependencies: `npm install`
4. Verify configuration: `npx hardhat test`

## Development & Testing

### Compilation Workflow

1. **Compile contracts**: `npx hardhat compile`
2. **Check for compilation errors**: Review build artifacts
3. **Run type checking**: Use TypeScript if configured
4. **Generate contract ABIs**: Extract for frontend integration

### Testing Strategy

Follow testing guidelines from `references/testing_strategies.md`:

1. **Unit tests**: Test individual contract functions
2. **Integration tests**: Test contract interactions
3. **Gas optimization tests**: Use `scripts/gas_analyzer.py`
4. **Security tests**: Follow `references/security_checklist.md`

**Run all tests**: `npx hardhat test`
**Run specific test**: `npx hardhat test <test-file>`
**Run gas analysis**: `python3 scripts/gas_analyzer.py`

### Local Development

1. **Start local node**: `npx hardhat node`
2. **Deploy locally**: `npx hardhat run scripts/deploy.js --network localhost`
3. **Interact with contracts**: Use Hardhat console

## Deployment

### Pre-Deployment Checklist

Before deploying, verify:
- [ ] All tests pass
- [ ] Gas optimization completed
- [ ] Security checklist reviewed
- [ ] Network configuration correct
- [ ] Private keys and environment variables secure
- [ ] Contract verification requirements understood

### Deployment Workflow

1. **Configure target network** using guidance from `references/network_configs.md`
2. **Run deployment script**:
   ```bash
   python3 scripts/deploy_contracts.py --network <network-name> --verify
   ```
3. **Verify deployment**: Check contract addresses on block explorer
4. **Update frontend contracts**: Replace contract addresses in dApp

**Supported networks:**
- Ethereum Mainnet
- Polygon
- Arbitrum
- Optimism
- BSC
- Testnets (Goerli, Sepolia, Mumbai, etc.)

### Contract Verification

Use automated verification script:

```bash
python3 scripts/verify_contracts.py --network <network-name> --address <contract-address>
```

Verification requires:
- Contract source code
- Constructor arguments (if any)
- Compiler version and settings

## Maintenance & Verification

### Contract Upgrades

For upgradeable contracts, use `scripts/upgrade_manager.py`:

```bash
python3 scripts/upgrade_manager.py --contract <contract-name> --new-implementation <new-address>
```

### Monitoring Tasks

1. **Gas usage monitoring**: Track ongoing gas costs
2. **Contract event monitoring**: Set up event listeners
3. **Security audits**: Regular security reviews
4. **Performance optimization**: Identify bottlenecks

### Troubleshooting

Common issues and solutions:
- **Compilation errors**: Check Solidity version compatibility
- **Deployment failures**: Verify gas settings and network connectivity
- **Verification errors**: Ensure exact compiler settings match deployment
- **Test failures**: Check mock data and contract initialization

## Quick Reference Commands

**Essential Hardhat commands:**
```bash
npx hardhat compile           # Compile contracts
npx hardhat test              # Run tests
npx hardhat run <script>      # Execute script
npx hardhat node              # Start local node
npx hardhat console           # Open console
npx hardhat clean             # Clean artifacts
```

**Custom script commands:**
```bash
python3 scripts/setup_hardhat.py      # Complete Hardhat environment setup
python3 scripts/setup_project.py      # New project setup
python3 scripts/deploy_contracts.py   # Deploy contracts
python3 scripts/verify_contracts.py   # Verify contracts
python3 scripts/gas_analyzer.py       # Analyze gas usage
python3 scripts/upgrade_manager.py    # Manage upgrades
python3 scripts/security_scanner.py   # Security audit and vulnerability scanning
```

## Resources

This skill includes comprehensive resources for Hardhat development:

### scripts/
Hardhat automation and management scripts:

**Core Scripts:**
- `setup_hardhat.py` - Complete Hardhat environment installation and configuration
- `setup_project.py` - Initialize new Hardhat projects with templates
- `contract_generator.py` - AI-powered smart contract code generator
- `multi_chain_deployer.py` - Multi-chain deployment coordinator
- `deploy_contracts.py` - Automated contract deployment with verification
- `verify_contracts.py` - Contract source verification on block explorers
- `gas_analyzer.py` - Gas usage analysis and optimization recommendations
- `monitor.py` - Real-time contract monitoring and alerting system
- `upgrade_manager.py` - Manage upgradeable contracts and implementations
- `security_scanner.py` - Comprehensive security audit and vulnerability scanning

**Usage Examples:**
```bash
# Complete environment setup for new users
python3 scripts/setup_hardhat.py --project-dir ./my-hardhat-project

# Generate smart contracts with AI assistance
python3 scripts/contract_generator.py --interactive
python3 scripts/contract_generator.py --type erc20 --name MyToken --supply 1000000

# Multi-chain deployment coordinator
python3 scripts/multi_chain_deployer.py --interactive
python3 scripts/multi_chain_deployer.py --chains ethereum,polygon,arbitrum --contract MyToken --strategy coordinated

# Setup new NFT project
python3 scripts/setup_project.py --template nft --name my-collection --network polygon

# Deploy with verification
python3 scripts/deploy_contracts.py --network ethereum --verify --gas-price auto

# Real-time contract monitoring
python3 scripts/monitor.py --interactive
python3 scripts/monitor.py --contract 0x1234...abcd --network ethereum

# Analyze gas usage
python3 scripts/gas_analyzer.py --contract MyToken --optimize

# Verify deployed contract
python3 scripts/verify_contracts.py --network ethereum --address 0x1234...abcd

# Comprehensive security audit
python3 scripts/security_scanner.py --scan contracts/MyContract.sol --full-scan

# Upgrade security analysis
python3 scripts/security_scanner.py --project . --tools slither,upgrade_security_analysis

# Setup automated CI/CD security scanning
python3 scripts/security_scanner.py --setup-ci
```

### references/
Comprehensive Hardhat development documentation:

- `project_templates.md` - Detailed template specifications and customization guides
- `network_configs.md` - Network configuration parameters and setup instructions
- `deployment_patterns.md` - Common deployment patterns and best practices
- `security_checklist.md` - Security considerations and audit procedures
- `testing_strategies.md` - Testing methodologies and framework usage

**When to reference:**
- Network configuration issues → Check `network_configs.md`
- Security concerns → Review `security_checklist.md`
- Deployment problems → Consult `deployment_patterns.md`
- Testing strategy planning → Use `testing_strategies.md`

### assets/
Project templates and boilerplate code:

**Project Templates:**
- `basic-template/` - Standard Hardhat project structure with sample contracts
- `defi-template/` - DeFi project template with token, staking, and governance contracts
- `nft-template/` - NFT project template with ERC721/ERC1155 implementation
- `dao-template/` - DAO project template with voting and governance mechanisms

**Configuration Examples:**
- `hardhat.config.examples/` - Various network and configuration examples
- Contract templates for common patterns
- Deployment script templates
- Test suite templates

**Template Usage:**
Templates are copied to new project directories and customized based on requirements. Each template includes:
- Sample contracts with best practices
- Pre-configured hardhat.config.js
- Test suites with example tests
- Deployment scripts
- Documentation scaffold

---

All resources are designed to work together seamlessly. Scripts reference templates, while references provide detailed guidance for customization and troubleshooting.
