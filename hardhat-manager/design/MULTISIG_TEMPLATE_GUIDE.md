# Multisig Wallet Template - Complete Guide

## 📋 Overview

This is a **production-ready multisig wallet template** with **Gnosis Safe compatibility** for Ethereum and EVM-compatible blockchains. It provides two tiers of functionality:

- **Tier 1: Basic Multisig** - Simple, secure multisig wallet
- **Tier 2: Timelock Multisig** - Advanced multisig with timelock and multi-tier approvals

## ✨ Key Features

### Core Features (Both Tiers)
- ✅ **Gnosis Safe Compatible** - Can import into Gnosis Safe UI
- ✅ **Multi-owner Support** - Configurable number of owners
- ✅ **ETH & ERC20 Support** - Handles native ETH and ERC20 tokens
- ✅ **Transaction Queuing** - Submit, confirm, and execute transactions
- ✅ **Confirmation Tracking** - Track who confirmed each transaction
- ✅ **Owner Management** - Add/remove owners dynamically
- ✅ **Safe Mode** - Emergency single-owner execution mode
- ✅ **Pausable** - Emergency pause mechanism
- ✅ **Reentrancy Protection** - Secure against reentrancy attacks

### Timelock Features (Tier 2 Only)
- ⏱️ **Transaction Timelock** - Delayed execution (24h - 30 days)
- 🛡️ **Multi-tier Confirmations** - More confirmations for larger amounts
- 🚨 **Emergency Transactions** - Fast execution for urgent matters
- ⏲️ **Grace Periods** - Missed execution window handling
- 🔄 **Batch Execution** - Execute multiple transactions at once
- 👥 **Timelock Admins** - Separate admin role for queueing

## 🏗️ Architecture

### Contract Hierarchy

```
MultisigWallet (Tier 1)
│
└── TimelockMultisigWallet (Tier 2)
    │
    ├── Inherits all Basic functionality
    ├── Adds TimelockController
    ├── Adds Tier Management
    └── Adds Emergency Mechanism
```

### Security Layers

1. **Ownership Validation** - All functions check owner status
2. **Threshold Enforcement** - Minimum confirmations required
3. **Reentrancy Guards** - Prevent reentrancy attacks
4. **Pausable Mechanism** - Emergency stop functionality
5. **Nonce Protection** - Prevent replay attacks
6. **Timelock Security** - Prevent front-running

## 🎯 Use Cases & Recommendations

### Basic Multisig - Choose When:
- ✅ Small team (3-5 people)
- ✅ Simple fund management
- ✅ Low transaction frequency
- ✅ High trust environment
- ✅ Quick deployment needed

**Example Configurations:**
- 2/3 multisig for 3-person team
- 3/4 multisig for 4-person team
- 3/5 multisig for 5-person team

### Timelock Multisig - Choose When:
- ✅ DAO treasury management
- ✅ Project fund governance
- ✅ DeFi protocol control
- ✅ Need transaction delays
- ✅ Require emergency mechanisms
- ✅ Large fund amounts

**Example Configurations:**
- Tier 1: <10 ETH → 2/3 confirmation + 24h delay
- Tier 2: 10-100 ETH → 3/5 confirmation + 48h delay
- Tier 3: >100 ETH → 4/7 confirmation + 72h delay
- Emergency: Any → 2/5 confirmation + 2h delay

## 🚀 Quick Start

### 1. Create Project

```bash
# Basic multisig
python3 scripts/setup_multisig.py \
    --type basic \
    --config basic \
    --name my-multisig

# Timelock multisig
python3 scripts/setup_multisig.py \
    --type timelock \
    --config dao \
    --name my-timelock-multisig
```

### 2. Configure Owners

Edit `config/multisig.config.js`:

```javascript
basic: {
  owners: [
    "0x1234...", // Owner 1
    "0x5678...", // Owner 2
    "0x9abc..."  // Owner 3
  ],
  requiredConfirmations: 2,
  // ... other settings
}
```

### 3. Install Dependencies

```bash
cd my-multisig
npm install
```

### 4. Set Up Environment

```bash
cp .env.example .env
# Edit .env with your private keys and API keys
```

### 5. Deploy

```bash
# Local network
npm run deploy:local

# Testnet
npm run deploy:goerli

# Mainnet
npm run deploy:mainnet
```

### 6. Verify on Etherscan

```bash
npm run verify:contract --network goerli CONTRACT_ADDRESS
```

## 📖 Detailed Usage

### Basic Multisig Operations

#### Submit Transaction
```javascript
const tx = await multisig.submitTransaction(
  recipientAddress,
  ethers.utils.parseEther("10"), // 10 ETH
  "0x", // Transaction data (empty for simple transfer)
  { from: owner1 }
);

console.log("Transaction ID:", tx.toString());
```

#### Confirm Transaction
```javascript
// Other owners must confirm
await multisig.confirmTransaction(tx, { from: owner2 });
await multisig.confirmTransaction(tx, { from: owner3 });
```

#### Execute Transaction
```javascript
// Once enough confirmations are received
await multisig.executeTransaction(tx, { from: anyOwner });
```

#### Transfer ERC20 Tokens
```javascript
// Prepare token transfer data
const transferData = token.interface.encodeFunctionData("transfer", [
  recipientAddress,
  ethers.utils.parseEther("1000") // 1000 tokens
]);

// Submit transaction
const tx = await multisig.submitTransaction(
  token.address, // Token contract address
  0, // No ETH value
  transferData,
  { from: owner1 }
);
```

### Timelock Multisig Operations

#### Queue Timelock Transaction
```javascript
const delay = 24 * 60 * 60; // 24 hours in seconds
const txId = await timelockMultisig.queueTimelockTransaction(
  recipientAddress,
  ethers.utils.parseEther("50"),
  "0x",
  delay,
  { from: timelockAdmin }
);

console.log("Queued transaction ID:", txId.toString());
```

#### Confirm Timelock Transaction
```javascript
// Owners confirm the transaction
await timelockMultisig.confirmTimelockTransaction(txId, { from: owner1 });
await timelockMultisig.confirmTimelockTransaction(txId, { from: owner2 });

// Check if enough confirmations
const required = await timelockMultisig.getRequiredConfirmations(
  ethers.utils.parseEther("50")
);
console.log("Required confirmations:", required.toString());
```

#### Execute After Delay
```javascript
// Wait for the delay period
// Then execute
await timelockMultisig.executeTimelockTransaction(txId, { from: timelockAdmin });
```

#### Emergency Transactions
```javascript
// Queue emergency transaction (2 hour delay)
const emgTxId = await timelockMultisig.queueEmergencyTransaction(
  recipientAddress,
  ethers.utils.parseEther("100"),
  "0x",
  { from: timelockAdmin }
);

// Wait 2+ hours, then execute
await timelockMultisig.executeEmergencyTransaction(emgTxId, { from: owner1 });
```

### Tier Management

Transactions are automatically categorized by value:

```javascript
// Check tier for specific value
const required = await timelockMultisig.getRequiredConfirmations(
  ethers.utils.parseEther("5")   // Tier 1: 2 confirmations
);
// returns: 2

const required2 = await timelockMultisig.getRequiredConfirmations(
  ethers.utils.parseEther("50")  // Tier 2: 3 confirmations
);
// returns: 3

const required3 = await timelockMultisig.getRequiredConfirmations(
  ethers.utils.parseEther("200") // Tier 3: 4 confirmations
);
// returns: 4
```

### Batch Operations

```javascript
// Queue multiple transactions
const txIds = [];
for (let i = 0; i < 5; i++) {
  const txId = await timelockMultisig.queueTimelockTransaction(
    recipient,
    ethers.utils.parseEther("1"),
    "0x",
    24 * 60 * 60,
    { from: admin }
  );
  txIds.push(txId);
}

// Confirm all
for (const txId of txIds) {
  await timelockMultisig.confirmTimelockTransaction(txId, { from: owner1 });
  await timelockMultisig.confirmTimelockTransaction(txId, { from: owner2 });
}

// Wait for delay, then batch execute
await increaseTime(24 * 60 * 60 + 1);
await timelockMultisig.batchExecuteTimelock(txIds, { from: admin });
```

## 🔒 Security Best Practices

### Pre-Deployment Checklist

- [ ] Owner addresses verified (not contracts, not zero address)
- [ ] Test on testnet first
- [ ] Multiple owners confirm deployment
- [ ] Verify configuration is correct
- [ ] Private keys secured (use hardware wallet if possible)
- [ ] Sufficient ETH for deployment gas
- [ ] Etherscan API keys configured

### Configuration Security

```javascript
// ✅ Good: Diverse owners from different locations
owners: [
  "0x...", // Founder - secured
  "0x...", // CTO - secured
  "0x...", // Community representative
  "0x...", // Advisor
  "0x..."  // Legal representative
]

// ❌ Bad: Same person controls all
owners: [
  "0x1234...", // Same person
  "0x1234...", // Same person
  "0x1234..."  // Same person
]
```

### Owner Selection

**Good Practices:**
- Choose owners from different teams/roles
- Use hardware wallets for production
- Distribute owners geographically
- Include legal entity representatives
- Consider multi-sig for owners themselves

**Bad Practices:**
- All owners from same company
- No geographic distribution
- Owners can't communicate
- All owners have same private key

### Fund Management

```javascript
// ✅ Good: Daily/weekly limits
spendingLimits: {
  dailyLimit: "10",     // 10 ETH per day
  weeklyLimit: "50",    // 50 ETH per week
  monthlyLimit: "200"   // 200 ETH per month
}

// ✅ Good: Multi-tier confirmations
// <10 ETH: 2/3
// 10-100 ETH: 3/5
// >100 ETH: 4/7
// Emergency: 2/5 with 2h delay
```

### Operational Security

1. **Regular Audits**
   - Review transaction history
   - Verify all owners are active
   - Check for suspicious patterns

2. **Communication**
   - Use secure communication channels
   - Verify owner identities
   - Document all procedures

3. **Key Management**
   - Use hardware wallets
   - Backup seeds securely
   - Never share private keys
   - Rotate keys if compromised

4. **Change Management**
   - Document all owner changes
   - Require multiple confirmations
   - Test changes on testnet first
   - Update documentation

## 🔧 Configuration Guide

### Config Structure

```javascript
module.exports = {
  // Config name
  basic: {
    // Basic settings
    name: "Basic Multisig Wallet",
    owners: [...],           // Array of owner addresses
    requiredConfirmations: 2,
    safeModeEnabled: true,    // Enable emergency mode
    gnosisCompatibility: true, // Compatible with Gnosis Safe UI

    // Optional settings
    timelockEnabled: false,   // For basic config
    useCase: "team_funds"
  },

  dao: {
    // ... configuration
  },

  project: {
    // ... configuration
  },

  defi: {
    // ... configuration
  },

  personal: {
    // ... configuration
  }
};
```

### Network Configuration

All supported networks in `hardhat.config.js`:
- Ethereum Mainnet
- Goerli Testnet
- Sepolia Testnet
- Polygon
- Mumbai Testnet
- Arbitrum
- Optimism
- BSC
- BSC Testnet

## 🧪 Testing

### Run Tests

```bash
# All tests
npm test

# Specific tests
npm run test:multisig    # Basic multisig tests
npm run test:timelock    # Timelock tests

# With coverage
npm run coverage
```

### Test Categories

**Basic Multisig Tests:**
- Deployment validation
- Transaction lifecycle (submit/confirm/execute)
- ETH transfers
- ERC20 transfers
- Owner management
- Safe mode operations
- Pausable functionality
- Gnosis compatibility
- View functions
- Access control

**Timelock Tests:**
- Timelock transaction lifecycle
- Emergency transactions
- Tier management
- Batch operations
- Delay enforcement
- Grace periods
- Admin management
- Access control

## 🔍 Verification & Monitoring

### Etherscan Verification

After deployment, verify on Etherscan:

```bash
# Verify single contract
npm run verify:contract --network goerli CONTRACT_ADDRESS

# Verify with constructor arguments
npx hardhat verify --network goerli CONTRACT_ADDRESS "arg1" "arg2"
```

### Monitoring Tools

1. **Etherscan** - View transactions, verify code
2. **Tenderly** - Advanced transaction tracing
3. **Dune Analytics** - Transaction analytics
4. **Custom Scripts** - Monitor events

### Event Monitoring

Subscribe to contract events:

```javascript
// Listen to confirmations
multisig.on("Confirmation", (sender, txId) => {
  console.log(`Transaction ${txId} confirmed by ${sender}`);
});

// Listen to executions
multisig.on("Execution", (txId) => {
  console.log(`Transaction ${txId} executed`);
});
```

## 🚨 Troubleshooting

### Common Issues

**Issue: Deployment fails**
```
Error: insufficient funds for gas * price + value
```
**Solution:** Ensure deployer has sufficient ETH for gas fees

**Issue: Can't confirm transaction**
```
Error: Not an owner
```
**Solution:** Check that the address is actually an owner

**Issue: Transaction won't execute**
```
Error: Not enough confirmations
```
**Solution:** More owners need to confirm the transaction

**Issue: Timelock transaction not ready**
```
Error: Transaction not yet ready
```
**Solution:** Wait for the timelock delay period

**Issue: Can't verify on Etherscan**
```
Error: Contract verification failed
```
**Solution:**
- Wait for more block confirmations
- Check constructor arguments
- Verify compiler version matches

### Debug Commands

```javascript
// Check owner status
await multisig.isOwner(address)

// Check confirmation count
const tx = await multisig.transactions(txId)
console.log(tx.confirmations)

// Check required confirmations
await multisig.requiredConfirmations()

// Check pending transactions
const pending = await multisig.getPendingTransactions()
console.log(pending)

// Check timelock transaction status
const timelockTx = await timelockMultisig.getTimelockTransaction(txId)
console.log(timelockTx.eta, timelockTx.executed)

// Check if can execute
const canExecute = await timelockMultisig.canExecuteTimelock(txId)
console.log(canExecute)
```

## 📚 Integration with Gnosis Safe

### Enable Compatibility

```javascript
// Enable Gnosis compatibility
await multisig.enableGnosisCompatibility()

// Check if enabled
const isEnabled = await multisig.gnosisCompatibilityMode()
console.log(isEnabled) // true
```

### Import to Gnosis Safe UI

1. Deploy multisig using this template
2. Go to [Gnosis Safe](https://gnosis-safe.io/)
3. Click "Create Safe"
4. Select "Import existing Safe"
5. Enter your contract address
6. Add owners (should match your configuration)
7. Set threshold (required confirmations)
8. Import and start using

### Gnosis Safe Features Available

- ✅ View transactions
- ✅ Confirm/reject transactions
- ✅ Execute transactions
- ✅ View transaction history
- ❌ Change owners (must use code)
- ❌ Change threshold (must use code)

## 📊 Gas Usage

### Typical Gas Costs

| Operation | Gas Used (Estimate) |
|-----------|-------------------|
| Deploy Basic Multisig | ~3,500,000 |
| Deploy Timelock Multisig | ~4,500,000 |
| Submit Transaction | ~80,000 |
| Confirm Transaction | ~60,000 |
| Execute Transaction | ~150,000 |
| Queue Timelock | ~120,000 |
| Execute Timelock | ~200,000 |

### Optimization Tips

- Use batch execution for multiple transactions
- Confirmations can be from any owner
- Safe mode executes immediately (no gas for delays)
- Use multicall for viewing multiple states

## 🎓 Advanced Topics

### Custom Modifications

#### Adding Whitelisted Contracts

```solidity
mapping(address => bool) public whitelistedContracts;

modifier onlyWhitelisted() {
    require(whitelistedContracts[msg.sender], "Not whitelisted");
    _;
}

function addToWhitelist(address contract) external onlyOwner {
    whitelistedContracts[contract] = true;
}
```

#### Custom Spending Limits

```solidity
mapping(address => uint256) public dailySpent;
uint256 public dailyLimit = 10 ether;

modifier withinDailyLimit(uint256 amount) {
    require(
        dailySpent[msg.sender] + amount <= dailyLimit,
        "Exceeds daily limit"
    );
    _;
}
```

#### Proxy Upgrade Pattern

```solidity
// Use OpenZeppelin's upgradeable contracts
contract MultisigWalletV2 is MultisigWallet {
    // New features added in V2
    function newFeature() external onlyOwner {
        // ...
    }
}
```

### Formal Verification

For critical applications, consider:
- Formal verification with Certora or SeMeter
- Runtime verification with Runtime Verification
- Independent security audits
- Bug bounty programs

## 📞 Support & Resources

### Documentation
- [Solidity Documentation](https://docs.soliditylang.org/)
- [Hardhat Documentation](https://hardhat.org/docs)
- [Ethers.js Documentation](https://docs.ethers.io/)
- [OpenZeppelin Documentation](https://docs.openzeppelin.com/)

### Tools
- [Remix IDE](https://remix.ethereum.org/)
- [Tenderly](https://tenderly.co/)
- [Dune Analytics](https://dune.com/)
- [Etherscan](https://etherscan.io/)

### Community
- [Ethereum Stack Exchange](https://ethereum.stackexchange.com/)
- [Reddit r/ethdev](https://www.reddit.com/r/ethdev/)
- [Discord](https://discord.gg/hardhat)

---

## ⚠️ Disclaimer

This software is provided as-is without warranty. Multisig wallets handle real funds and require proper testing and security measures. Always:

- Test thoroughly on testnets
- Use hardware wallets for production
- Get professional audits for large funds
- Keep private keys secure
- Follow best practices

**Use at your own risk.**

---

## 🎉 Conclusion

This multisig template provides a **secure, flexible, and production-ready** solution for managing funds on Ethereum. With Gnosis Safe compatibility and comprehensive features, it's suitable for teams, DAOs, and individuals who need secure multi-owner control of digital assets.

Start with the **Basic multisig** for simple needs, or use **Timelock multisig** for advanced governance requirements.
