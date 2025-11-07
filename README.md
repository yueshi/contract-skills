# Contract Skills 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Solidity](https://img.shields.io/badge/Solidity-0.8%2B-blue.svg)](https://soliditylang.org/)
[![Hardhat](https://img.shields.io/badge/Hardhat-2.17%2B-ff9e1b.svg)](https://hardhat.org/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://www.python.org/)
[![Ethereum](https://img.shields.io/badge/Ethereum-Smart%20Contracts-627EEA.svg)](https://ethereum.org/)

> 一套专业的以太坊智能合约开发和安全审计工具集，包含 Hardhat 项目管理和 Wake 安全审计两大核心技能模块。

## 🌟 项目特色

- **🏗️ 完整开发环境**: 一键式 Hardhat 环境配置和项目管理
- **🤖 AI 驱动开发**: 智能合约自动生成和代码优化
- **🔐 企业级安全**: 多工具集成的安全审计和漏洞扫描
- **🌐 多链部署**: 支持主流以太坊兼容网络的协调部署
- **📊 实时监控**: 部署后合约监控和告警系统
- **🎯 项目模板**: 预配置的 DeFi、NFT、DAO 项目模板

## 📋 目录

- [技能模块](#-技能模块)
- [快速开始](#-快速开始)
- [安装指南](#-安装指南)
- [使用示例](#-使用示例)
- [项目模板](#-项目模板)
- [安全功能](#-安全功能)
- [支持的网络](#-支持的网络)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

## 🧩 技能模块

### Hardhat Manager 🏗️

专业的 Hardhat 开发环境管理工具，提供完整的智能合约开发生命周期管理。

**核心功能:**
- ✅ 自动化环境设置和配置
- ✅ AI 驱动的智能合约生成
- ✅ 多链部署协调
- ✅ 实时合约监控
- ✅ Gas 优化分析
- ✅ 合约升级管理
- ✅ 自动化验证

### Wake Auditor 🔍

基于 Wake Printer 脚本的 Solidity 智能合约安全审计工具。

**核心功能:**
- ✅ 静态分析和漏洞检测
- ✅ 自定义审计规则
- ✅ 批量合约分析
- ✅ 详细审计报告
- ✅ CI/CD 集成

## 🚀 快速开始

### 系统要求

- Python 3.8+
- Node.js 16+
- Git

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/your-username/contract-skills.git
cd contract-skills
```

2. **安装 Python 依赖**
```bash
pip install -r requirements.txt  # 如果存在
```

3. **设置 Hardhat 环境**
```bash
# 自动化完整环境设置
python3 hardhat-manager/scripts/setup_hardhat.py

# 或者手动设置特定项目
python3 hardhat-manager/scripts/setup_project.py --template basic --name my-project
```

4. **验证安装**
```bash
cd hardhat-manager/assets/basic-template
npm install
npx hardhat test
```

## 📖 使用示例

### 1. 创建新项目

```bash
# 创建 NFT 项目
python3 hardhat-manager/scripts/setup_project.py \
  --template nft \
  --name my-nft-collection \
  --network polygon

# 创建 DeFi 项目
python3 hardhat-manager/scripts/setup_project.py \
  --template defi \
  --name my-defi-protocol \
  --network ethereum
```

### 2. AI 生成智能合约

```bash
# 交互式合约创建
python3 hardhat-manager/scripts/contract_generator.py --interactive

# 生成 ERC20 代币
python3 hardhat-manager/scripts/contract_generator.py \
  --type erc20 \
  --name MyToken \
  --symbol MTK \
  --supply 1000000

# 生成 NFT 合约
python3 hardhat-manager/scripts/contract_generator.py \
  --type nft \
  --name MyCollection \
  --symbol NFT \
  --max-supply 10000
```

### 3. 多链部署

```bash
# 交互式多链部署
python3 hardhat-manager/scripts/multi_chain_deployer.py --interactive

# 同时部署到多个网络
python3 hardhat-manager/scripts/multi_chain_deployer.py \
  --chains ethereum,polygon,arbitrum \
  --contract MyToken \
  --strategy simultaneous
```

### 4. 安全审计

```bash
# 完整安全扫描
python3 hardhat-manager/scripts/security_scanner.py \
  --scan contracts/MyContract.sol \
  --full-scan

# 使用特定工具扫描
python3 hardhat-manager/scripts/security_scanner.py \
  --project . \
  --tools slither,upgrade_security_analysis

# 使用 Wake 进行深度审计
python3 wake-auditor/scripts/vulnerability_detector.py \
  --project ./contracts/
```

### 5. 实时监控

```bash
# 监控特定合约
python3 hardhat-manager/scripts/monitor.py \
  --contract 0x1234...abcd \
  --network ethereum

# 交互式监控设置
python3 hardhat-manager/scripts/monitor.py --interactive
```

## 🎨 项目模板

### 基础模板 (Basic Template)
标准智能合约项目结构，适用于简单的代币和工具合约。

```bash
python3 hardhat-manager/scripts/setup_project.py --template basic --name my-basic-project
```

**包含内容:**
- 预配置的 Hardhat 设置
- 示例智能合约和测试
- 基础部署脚本
- 标准安全配置

### DeFi 模板 (DeFi Template)
去中心化金融协议开发模板，包含代币、质押和治理合约。

```bash
python3 hardhat-manager/scripts/setup_project.py --template defi --name my-defi-protocol
```

**包含内容:**
- ERC20 代币合约
- 质押和奖励合约
- 流动性挖矿合约
- 治理投票合约
- DeFi 安全最佳实践

### NFT 模板 (NFT Template)
非同质化代币项目模板，支持 ERC721 和 ERC1155 标准。

```bash
python3 hardhat-manager/scripts/setup_project.py --template nft --name my-nft-collection
```

**包含内容:**
- ERC721/ERC1155 合约
- 版税和版税分配
- 元数据管理
- 市场集成接口
- IPFS 集成示例

### DAO 模板 (DAO Template)
去中心化自治组织开发模板，包含完整的治理框架。

```bash
python3 hardhat-manager/scripts/setup_project.py --template dao --name my-dao
```

**包含内容:**
- 治理代币合约
- 投票和提案系统
- 金库管理
- 多重签名钱包
- 时间锁合约

### 多重签名模板 (Multisig Template)
企业级多重签名钱包模板。

```bash
python3 hardhat-manager/scripts/setup_project.py --template multisig --name my-multisig
```

**包含内容:**
- Gnosis 兼容的多重签名钱包
- 灵活的确认阈值设置
- 交易历史和状态管理
- 安全的密钥管理

## 🔒 安全功能

### 自动化安全扫描

支持多种行业标准安全工具:

- **Slither** - Solidity 静态分析框架
- **Mythril** - 符号执行和漏洞检测
- **Echidna** - 基于属性的模糊测试
- **自定义模式匹配** - 针对新兴威胁的检测

### 漏洞检测类型

- 🔴 **关键漏洞**: 重入攻击、权限绕过、整数溢出
- 🟠 **高风险**: 访问控制问题、未初始化存储
- 🟡 **中等风险**: Gas 优化问题、事件缺失
- 🔵 **信息级**: 代码质量和最佳实践

### 升级安全分析

专门针对可升级合约的安全分析:
- 存储布局冲突检测
- 代理模式兼容性验证
- 构造函数安全性检查
- 自毁函数风险评估

### 报告生成

- **JSON 报告**: 机器可读的详细漏洞数据
- **Markdown 报告**: 人类可读的安全审计文档
- **执行摘要**: 高层次安全概览
- **修复指导**: 针对每个问题的具体建议

## 🌐 支持的网络

### 主网支持
- **Ethereum** - 以太坊主网
- **Polygon** - PoS 链
- **Arbitrum** - Layer 2 解决方案
- **Optimism** - Layer 2 解决方案
- **BSC** - 币安智能链

### 测试网支持
- **Goerli** - 以太坊测试网
- **Sepolia** - 以太坊测试网
- **Mumbai** - Polygon 测试网
- **Arbitrum Goerli** - Arbitrum 测试网

### 网络特性
- ⚡ **Gas 优化** - 智能Gas价格调整
- 🔄 **自动重试** - 部署失败自动重试
- 📊 **实时状态** - 部署进度实时反馈
- ✅ **自动验证** - 区块浏览器合约验证

## 🛠️ 开发工作流

### 1. 项目初始化
```bash
# 选择合适的模板
python3 hardhat-manager/scripts/setup_project.py --template <type> --name <project>

# 配置开发环境
cd <project-directory>
npm install
npx hardhat compile
```

### 2. 开发和测试
```bash
# 本地开发
npx hardhat node
npx hardhat run scripts/deploy.js --network localhost

# 运行测试
npx hardhat test
npx hardhat coverage

# Gas 分析
python3 hardhat-manager/scripts/gas_analyzer.py --contract MyContract
```

### 3. 安全审计
```bash
# 完整安全扫描
python3 hardhat-manager/scripts/security_scanner.py --project . --full-scan

# 特定工具扫描
python3 hardhat-manager/scripts/security_scanner.py --project . --tools slither

# Wake 深度分析
python3 wake-auditor/scripts/vulnerability_detector.py --project ./contracts/
```

### 4. 部署和验证
```bash
# 多链部署
python3 hardhat-manager/scripts/multi_chain_deployer.py --chains ethereum,polygon --contract MyContract

# 合约验证
python3 hardhat-manager/scripts/verify_contracts.py --network ethereum --address <contract-address>
```

### 5. 监控和维护
```bash
# 设置监控
python3 hardhat-manager/scripts/monitor.py --contract <address> --network <network>

# 合约升级
python3 hardhat-manager/scripts/upgrade_manager.py --contract MyContract --new-implementation <address>
```

## 🤝 贡献指南

我们欢迎所有形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 贡献方式

1. **Fork 项目**
2. **创建功能分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **创建 Pull Request**

### 开发指南

- 遵循现有的代码风格和最佳实践
- 为新功能添加适当的测试
- 更新相关文档
- 确保所有测试通过

## 📚 文档和资源

- [📖 完整文档](docs/)
- [🔧 API 参考](docs/api.md)
- [🎯 教程](docs/tutorials/)
- [❓ 常见问题](docs/faq.md)
- [📊 项目状态](docs/status.md)

### 社区支持

- 💬 [Discord 社区](https://discord.gg/)
- 🐦 [Twitter 关注](https://twitter.com/)
- 📧 [邮件联系](mailto:support@example.com)

## 🔧 技术栈

### 核心技术
- **Solidity** ^0.8.0 - 智能合约开发语言
- **Hardhat** ^2.17.0 - 以太坊开发环境
- **Python** 3.8+ - 自动化脚本语言
- **Node.js** 16+ - JavaScript 运行时

### 主要依赖
- **OpenZeppelin** - 安全的合约库
- **Ethers.js** - 以太坊交互库
- **Chai** - 测试断言库
- **Slither** - 安全分析工具
- **Wake** - Solidity 中间表示分析

## 📈 路线图

### v1.1 (计划中)
- [ ] 更多网络支持 (Avalanche, Fantom)
- [ ] Web3 UI 界面
- [ ] 高级监控仪表板
- [ ] 更多 DeFi 原语模板

### v1.2 (未来)
- [ ] ZK-Rollup 部署支持
- [ ] 跨链桥集成
- [ ] AI 代码优化建议
- [ ] 社区贡献模板市场

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下开源项目和社区的支持:

- [Hardhat](https://hardhat.org/) - 专业的以太坊开发环境
- [OpenZeppelin](https://openzeppelin.com/) - 安全的智能合约标准
- [Slither](https://github.com/crytic/slither) - Solidity 静态分析框架
- [Wake](https://github.com/Ackee-Blockchain/wake) - Solidity 中间表示分析工具

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个 Star！**

Made with ❤️ by the Contract Skills Team

</div>