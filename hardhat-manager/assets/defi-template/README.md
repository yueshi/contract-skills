# DeFi Protocol Hardhat Template

这是一个完整的 DeFi 协议 Hardhat 模板，包含去中心化交易所（DEX）、借贷池和质押池的核心合约实现。

## 📋 项目结构

```
defi-template/
├── contracts/
│   ├── dex/
│   │   └── SimpleDEX.sol              # 自动做市商 DEX
│   ├── lending/
│   │   └── LendingPool.sol            # 借贷池
│   ├── staking/
│   │   └── StakingPool.sol            # 质押池
│   ├── tokens/
│   │   └── DeFiToken.sol              # DeFi 代币
│   ├── libraries/                      # 工具库
│   ├── interfaces/                     # 接口
│   └── test/                          # 测试合约
│       ├── ERC20TestToken.sol
│       └── MockERC20.sol
├── scripts/                           # 部署脚本
├── test/                             # 测试文件
│   ├── DeFiToken.test.js
│   ├── SimpleDEX.test.js
│   └── StakingPool.test.js
├── hardhat.config.js                  # Hardhat 配置
├── package.json                      # 依赖配置
└── README.md                         # 本文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 编译合约

```bash
npm run compile
```

### 3. 运行测试

```bash
# 运行所有测试
npm run test

# 运行特定测试
npm run test:token      # 测试 DeFiToken
npm run test:dex        # 测试 SimpleDEX
npm run test:staking    # 测试 StakingPool

# 运行覆盖率测试
npm run test:coverage
```

### 4. 部署合约

```bash
# 部署到本地网络
npm run deploy:local

# 部署到测试网
npm run deploy:testnet

# 部署到主网
npm run deploy:mainnet
```

## 💰 核心合约

### 1. DeFiToken (`contracts/tokens/DeFiToken.sol`)

功能完整的 ERC20 代币，支持：
- 铸造和销毁
- 权限管理（铸币员）
- 黑名单功能
- 暂停功能

**主要功能**:
```solidity
// 添加铸币员
function addMinter(address minter) external onlyOwner

// 铸造代币
function mint(address to, uint256 amount) external onlyMinter

// 批量铸造
function batchMint(address[] calldata recipients, uint256[] calldata amounts) external onlyMinter

// 销毁代币
function burn(uint256 amount) public

// 黑名单管理
function blacklist(address account) external onlyOwner
```

### 2. SimpleDEX (`contracts/dex/SimpleDEX.sol`)

自动做市商（AMM）实现的去中心化交易所：
- 恒定乘积公式 (x * y = k)
- 流动性挖矿
- 0.3% 交易手续费

**主要功能**:
```solidity
// 添加流动性
function addLiquidity(uint256 amountA, uint256 amountB) external

// 移除流动性
function removeLiquidity(uint256 liquidityAmount) external

// 交换代币
function swap(address tokenIn, uint256 amountIn) external returns (uint256 amountOut)

// 获取价格
function getPriceA() external view returns (uint256)
function getPriceB() external view returns (uint256)
```

### 3. StakingPool (`contracts/staking/StakingPool.sol`)

质押池合约，支持：
- 锁仓奖励机制
- 灵活锁仓期限
- 奖励发放

**主要功能**:
```solidity
// 质押代币
function stake(uint256 amount, uint256 lockDuration) external

// 提取代币
function withdraw(uint256 amount) external

// 领取奖励
function getReward() external

// 退出（提取所有并领取奖励）
function exit() external
```

### 4. LendingPool (`contracts/lending/LendingPool.sol`)

借贷池合约（简化版）：
- 存入代币赚取利息
- 借贷功能
- 利率模型

**主要功能**:
```solidity
// 存入代币
function deposit(uint256 amount) external

// 提取代币
function withdraw(uint256 shares) external

// 借贷代币
function borrow(uint256 amount) external

// 偿还贷款
function repay(uint256 amount) external

// 获取利率
function getBorrowRate() external view returns (uint256)
```

## 🧪 测试

项目包含全面的测试套件，测试覆盖：

- ✅ 部署和初始化
- ✅ 核心功能
- ✅ 权限管理
- ✅ 异常处理
- ✅ 事件验证
- ✅ Gas 优化

### 运行测试

```bash
# 所有测试
npm run test

# 单个测试文件
npm run test:token
npm run test:dex
npm run test:staking

# 覆盖率
npm run test:coverage
```

## 📊 Gas 报告

```bash
# 生成 gas 使用报告
npm run gas-report
```

## 🔍 合约验证

```bash
# 验证合约
npm run verify

# 验证特定网络
npm run verify:etherscan
npm run verify:polygonscan
npm run verify:arbiscan
```

## 🌐 网络配置

支持的网络：

### 测试网
- **Goerli**: ETH 测试网
- **Sepolia**: ETH 测试网
- **Mumbai**: Polygon 测试网
- **Arbitrum Goerli**: Arbitrum 测试网
- **Optimism Goerli**: Optimism 测试网

### 主网
- **Ethereum**: 以太坊主网
- **Polygon**: Polygon 主网
- **Arbitrum**: Arbitrum One
- **Optimism**: Optimism

### 配置环境变量

创建 `.env` 文件：

```env
# RPC URLs
MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_API_KEY
POLYGON_RPC_URL=https://polygon-rpc.com
ARBITRUM_RPC_URL=https://arbitrum-mainnet.infura.io/v3/YOUR_INFURA_API_KEY

# 私钥（永远不要提交真实私钥！）
PRIVATE_KEY=your_private_key_here

# 区块浏览器 API 密钥
ETHERSCAN_API_KEY=your_etherscan_api_key_here
POLYGONSCAN_API_KEY=your_polygonscan_api_key_here
ARBISCAN_API_KEY=your_arbiscan_api_key_here
```

## 📖 使用示例

### 1. 部署 SimpleDEX

```javascript
const SimpleDEX = await ethers.getContractFactory("SimpleDEX");
const dex = await SimpleDEX.deploy(tokenA.address, tokenB.address);
await dex.deployed();
```

### 2. 添加流动性

```javascript
// 批准代币
await tokenA.approve(dex.address, ethers.utils.parseEther("100"));
await tokenB.approve(dex.address, ethers.utils.parseEther("200"));

// 添加流动性
await dex.addLiquidity(
  ethers.utils.parseEther("100"),  // Token A 数量
  ethers.utils.parseEther("200")   // Token B 数量
);
```

### 3. 交换代币

```javascript
// 批准代币
await tokenA.approve(dex.address, ethers.utils.parseEther("10"));

// 交换
await dex.swap(tokenA.address, ethers.utils.parseEther("10"));
```

### 4. 质押代币

```javascript
// 批准代币
await stakingToken.approve(stakingPool.address, ethers.utils.parseEther("1000"));

// 质押（30天锁仓）
await stakingPool.stake(
  ethers.utils.parseEther("1000"),
  30 * 24 * 60 * 60  // 30天（秒）
);

// 领取奖励
await stakingPool.getReward();
```

## 🔒 安全考虑

项目采用以下安全措施：

1. **ReentrancyGuard**: 防止重入攻击
2. **访问控制**: 严格的所有者和权限管理
3. **输入验证**: 所有外部输入都有验证
4. **暂停机制**: 紧急情况下可以暂停合约
5. **全面测试**: 覆盖所有主要功能

## 📚 参考资源

- [Solidity 文档](https://docs.soliditylang.org/)
- [OpenZeppelin 文档](https://docs.openzeppelin.com/)
- [Hardhat 文档](https://hardhat.org/docs)
- [Ethers.js 文档](https://docs.ethers.org/)

## 🐛 故障排除

### 常见问题

1. **编译错误**
   ```bash
   npm run clean && npm run compile
   ```

2. **测试失败**
   ```bash
   npm run test -- --reporter spec
   ```

3. **部署失败**
   - 检查网络配置
   - 确认私钥和 RPC URL 正确
   - 检查账户余额

4. **Gas 不足**
   ```bash
   # 查看 gas 报告
   npm run gas-report
   ```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⚠️ 免责声明

本项目仅用于教育目的。在生产环境使用前，请务必进行专业的安全审计。
