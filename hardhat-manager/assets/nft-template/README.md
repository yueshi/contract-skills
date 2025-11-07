# NFT Collection Hardhat Template

这是一个完整的 NFT 集合 Hardhat 模板，包含 ERC721 NFT 合约和市场合约的实现。

## 📋 项目结构

```
nft-template/
├── contracts/
│   ├── ERC721Collection.sol          # NFT 集合合约
│   ├── NFTMarketplace.sol            # NFT 市场
│   ├── MetadataGenerator.sol         # 元数据生成器
│   └── test/                         # 测试合约
│       └── MockNFT.sol
├── scripts/                          # 部署脚本
├── test/                            # 测试文件
│   ├── ERC721Collection.test.js
│   └── NFTMarketplace.test.js
├── hardhat.config.js                 # Hardhat 配置
├── package.json                     # 依赖配置
└── README.md                        # 本文档
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
npm run test:nft      # 测试 ERC721Collection
npm run test:marketplace  # 测试 NFTMarketplace

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

## 🎨 核心合约

### 1. ERC721Collection (`contracts/ERC721Collection.sol`)

功能完整的 ERC721 NFT 集合，包含：
- 允许名单和白名单销售
- 公开销售
- 版税支持（ERC2981）
- 可暂停
- 可销毁
- 最大供应量限制

**主要功能**:
```solidity
// 构造函数参数
constructor(
    string memory name_,              // 集合名称
    string memory symbol_,            // 集合符号
    uint256 maxSupply_,               // 最大供应量
    uint256 maxMintPerTx_,            // 每次最大铸造数量
    uint256 mintPrice_,               // 铸造价格（wei）
    uint256 publicSaleStartTime_,     // 公开销售开始时间
    uint256 allowlistSaleStartTime_,  // 允许名单销售开始时间
    string memory baseURI_,           // 基础 URI
    string memory contractURI_        // 合约 URI
)

// 白名单铸造
function mintAllowlist(uint256 amount) external payable

// 公开铸造
function mintPublic(uint256 amount) external payable

// 管理员铸造
function adminMint(address to, uint256 amount) external onlyOwner

// 更新允许名单
function updateAllowlist(address[] calldata users, bool[] calldata allowed) external onlyOwner

// 设置版税
function setRoyalty(address receiver, uint96 feeInBps) external onlyOwner
```

**铸造阶段**:
- **NOT_STARTED**: 销售尚未开始
- **ALLOWLIST**: 允许名单销售阶段
- **PUBLIC**: 公开销售阶段
- **ENDED**: 销售结束

### 2. NFTMarketplace (`contracts/NFTMarketplace.sol`)

功能完整的 NFT 市场，支持：
- 固定价格销售
- 拍卖
- 批量操作
- 费用收取
- 紧急撤回

**主要功能**:
```solidity
// 列出 NFT 出售
function listNFT(
    address nftContract,      // NFT 合约地址
    uint256 tokenId,          // Token ID
    uint256 price            // 销售价格（wei）
) external

// 列出 NFT 拍卖
function listNFTForAuction(
    address nftContract,      // NFT 合约地址
    uint256 tokenId,          // Token ID
    uint256 startingPrice,    // 起拍价格
    uint256 auctionDuration   // 拍卖持续时间（秒）
) external

// 购买 NFT
function buyNFT(uint256 listingId) external payable

// 出价
function placeBid(uint256 listingId) external payable

// 结算拍卖
function settleAuction(uint256 listingId) external
```

**市场特色**:
- 0.3% 交易手续费
- 支持所有 ERC721 NFT
- 可接受的 NFT 合约管理
- 完整的出价和结算系统

### 3. MetadataGenerator (`contracts/MetadataGenerator.sol`)

动态元数据生成器，支持：
- 基于稀有度的属性生成
- 随机种子生成
- OpenSea 标准兼容

## 🧪 测试

项目包含全面的测试套件：

### ERC721Collection 测试
- ✅ 部署和初始化
- ✅ 铸造功能（白名单、公开、管理员）
- ✅ 版税设置
- ✅ 暂停功能
- ✅ 边界条件

### NFTMarketplace 测试
- ✅ 列表功能
- ✅ 购买功能
- ✅ 拍卖功能
- ✅ 出价和结算
- ✅ 取消列表
- ✅ 权限管理

### 运行测试

```bash
# 所有测试
npm run test

# 单个测试
npm run test:nft
npm run test:marketplace

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
npm run verify --network polygon 0x... CONTRACT_ADDRESS
```

## 🌐 网络配置

支持的网络：

### 测试网
- **Goerli**: ETH 测试网
- **Sepolia**: ETH 测试网
- **Mumbai**: Polygon 测试网

### 主网
- **Ethereum**: 以太坊主网
- **Polygon**: Polygon 主网

### 配置环境变量

创建 `.env` 文件：

```env
# RPC URLs
MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_API_KEY
POLYGON_RPC_URL=https://polygon-rpc.com
GOERLI_RPC_URL=https://goerli.infura.io/v3/YOUR_INFURA_API_KEY

# 私钥（永远不要提交真实私钥！）
PRIVATE_KEY=your_private_key_here

# 区块浏览器 API 密钥
ETHERSCAN_API_KEY=your_etherscan_api_key_here
POLYGONSCAN_API_KEY=your_polygonscan_api_key_here
```

## 📖 使用示例

### 1. 部署 NFT 集合

```javascript
const currentTime = await time.latest();
const publicSaleStart = currentTime + 86400; // +1 day
const allowlistSaleStart = currentTime + 3600; // +1 hour

const ERC721Collection = await ethers.getContractFactory("ERC721Collection");
const nftCollection = await ERC721Collection.deploy(
  "My NFT Collection",      // 集合名称
  "MNC",                    // 集合符号
  1000,                     // 最大供应量
  5,                        // 每次最大铸造数量
  ethers.utils.parseEther("0.1"), // 铸造价格
  publicSaleStart,          // 公开销售开始时间
  allowlistSaleStart,       // 允许名单销售开始时间
  "ipfs://base/",           // 基础 URI
  "ipfs://contract/"        // 合约 URI
);
```

### 2. 设置允许名单

```javascript
const allowlistAddresses = [user1.address, user2.address];
const allowlistStatus = [true, true];

await nftCollection.updateAllowlist(allowlistAddresses, allowlistStatus);
```

### 3. 铸造 NFT

```javascript
// 白名单铸造（50% 折扣）
await nftCollection.connect(user1).mintAllowlist(2, { 
  value: ethers.utils.parseEther("0.1") * 2 // 50% 折扣价格
});

// 公开铸造
await nftCollection.mintPublic(3, { 
  value: ethers.utils.parseEther("0.1") * 3
});
```

### 4. 部署市场

```javascript
const NFTMarketplace = await ethers.getContractFactory("NFTMarketplace");
const marketplace = await NFTMarketplace.deploy(
  feeReceiver.address,  // 费用接收地址
  250                   // 2.5% 手续费
);
```

### 5. 列出 NFT 出售

```javascript
// 批准 NFT
await nftCollection.approve(marketplace.address, 1);

// 列出出售
const price = ethers.utils.parseEther("1");
await marketplace.listNFT(nftCollection.address, 1, price);

// 购买
await marketplace.buyNFT(1, { value: price });
```

## 🔒 安全考虑

项目采用以下安全措施：

1. **ReentrancyGuard**: 防止重入攻击
2. **Access Control**: 严格的所有者和权限管理
3. **Input Validation**: 所有外部输入都有验证
4. **Pausable**: 紧急情况下可以暂停合约
5. **SafeERC20**: 安全地处理代币转移
6. **Comprehensive Testing**: 覆盖所有主要功能

## 🎯 最佳实践

### 1. 元数据管理

```json
{
  "name": "NFT #1",
  "description": "My NFT Collection",
  "image": "ipfs://image/1.png",
  "attributes": [
    {
      "trait_type": "Color",
      "value": "Red",
      "rarity": "10%"
    }
  ]
}
```

### 2. IPFS 存储

推荐使用 IPFS 存储 NFT 元数据和图片：
- Pinata
- NFT.Storage
- Infura IPFS

### 3. 合约验证

部署后务必验证合约：

```bash
npx hardhat verify --network polygon CONTRACT_ADDRESS "constructor_arg1" "constructor_arg2"
```

## 📚 参考资源

- [ERC721 标准](https://eips.ethereum.org/EIPS/eip-721)
- [ERC2981 版税标准](https://eips.ethereum.org/EIPS/eip-2981)
- [OpenZeppelin 文档](https://docs.openzeppelin.com/)
- [ERC721 Metadata 规范](https://docs.opensea.io/docs/metadata-standards)

## 🐛 故障排除

### 常见问题

1. **铸造失败**
   - 检查销售阶段
   - 确认价格正确
   - 检查是否在允许名单中

2. **市场交易失败**
   - 检查 NFT 是否已批准
   - 确认价格/出价正确
   - 检查拍卖是否结束

3. **元数据不显示**
   - 检查 tokenURI 配置
   - 确认 IPFS 链接有效
   - 验证 JSON 格式正确

### 调试命令

```bash
# 检查销售阶段
const phase = await nftCollection.salePhase();
console.log("Sale phase:", phase.toString());

# 检查用户允许名单状态
const allowed = await nftCollection.allowlist(user.address);
console.log("Allowlist status:", allowed);
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⚠️ 免责声明

本项目仅用于教育目的。在生产环境使用前，请务必进行专业的安全审计。
