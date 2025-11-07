# Hardhat Network Configuration Guide

This guide provides comprehensive network configuration instructions for various Ethereum-compatible networks when using Hardhat.

## Supported Networks

### Mainnet Networks

#### Ethereum Mainnet
```javascript
// hardhat.config.js
module.exports = {
  networks: {
    ethereum: {
      url: `https://mainnet.infura.io/v3/${process.env.INFURA_API_KEY}`,
      accounts: [process.env.PRIVATE_KEY],
      chainId: 1,
      gasPrice: 20000000000, // 20 gwei
      gas: 6000000
    }
  }
}
```

**Environment Variables:**
```
INFURA_API_KEY=your_infura_api_key_here
PRIVATE_KEY=your_private_key_here
ETHERSCAN_API_KEY=your_etherscan_api_key_here
```

#### Polygon Mainnet
```javascript
polygon: {
  url: "https://polygon-rpc.com",
  accounts: [process.env.PRIVATE_KEY],
  chainId: 137,
  gasPrice: 30000000000, // 30 gwei
  gas: 6000000
}
```

**Environment Variables:**
```
PRIVATE_KEY=your_private_key_here
POLYGONSCAN_API_KEY=your_polygonscan_api_key_here
```

#### Arbitrum One
```javascript
arbitrum: {
  url: `https://arbitrum-mainnet.infura.io/v3/${process.env.INFURA_API_KEY}`,
  accounts: [process.env.PRIVATE_KEY],
  chainId: 42161,
  gasPrice: 15000000000, // 15 gwei
  gas: 6000000
}
```

#### Optimism
```javascript
optimism: {
  url: `https://optimism-mainnet.infura.io/v3/${process.env.INFURA_API_KEY}`,
  accounts: [process.env.PRIVATE_KEY],
  chainId: 10,
  gasPrice: 15000000000, // 15 gwei
  gas: 6000000
}
```

#### Binance Smart Chain (BSC)
```javascript
bsc: {
  url: "https://bsc-dataseed1.binance.org",
  accounts: [process.env.PRIVATE_KEY],
  chainId: 56,
  gasPrice: 20000000000, // 20 gwei
  gas: 6000000
}
```

### Testnet Networks

#### Goerli Testnet
```javascript
goerli: {
  url: `https://goerli.infura.io/v3/${process.env.INFURA_API_KEY}`,
  accounts: [process.env.PRIVATE_KEY],
  chainId: 5,
  gasPrice: 20000000000, // 20 gwei
  gas: 6000000
}
```

#### Sepolia Testnet
```javascript
sepolia: {
  url: `https://sepolia.infura.io/v3/${process.env.INFURA_API_KEY}`,
  accounts: [process.env.PRIVATE_KEY],
  chainId: 11155111,
  gasPrice: 20000000000, // 20 gwei
  gas: 6000000
}
```

#### Polygon Mumbai
```javascript
mumbai: {
  url: "https://rpc-mumbai.maticvigil.com",
  accounts: [process.env.PRIVATE_KEY],
  chainId: 80001,
  gasPrice: 20000000000, // 20 gwei
  gas: 6000000
}
```

#### Arbitrum Goerli
```javascript
arbitrum-goerli: {
  url: `https://arbitrum-goerli.infura.io/v3/${process.env.INFURA_API_KEY}`,
  accounts: [process.env.PRIVATE_KEY],
  chainId: 421613,
  gasPrice: 10000000000, // 10 gwei
  gas: 6000000
}
```

#### Optimism Goerli
```javascript
optimism-goerli: {
  url: `https://optimism-goerli.infura.io/v3/${process.env.INFURA_API_KEY}`,
  accounts: [process.env.PRIVATE_KEY],
  chainId: 420,
  gasPrice: 10000000000, // 10 gwei
  gas: 6000000
}
```

#### BSC Testnet
```javascript
bsc-testnet: {
  url: "https://data-seed-prebsc-1-s1.binance.org:8545",
  accounts: [process.env.PRIVATE_KEY],
  chainId: 97,
  gasPrice: 20000000000, // 20 gwei
  gas: 6000000
}
```

### Local Development

#### Hardhat Network
```javascript
hardhat: {
  chainId: 31337,
  gas: 12000000,
  blockGasLimit: 12000000,
  allowUnlimitedContractSize: true
}
```

#### Localhost
```javascript
localhost: {
  url: "http://127.0.0.1:8545",
  chainId: 31337,
  gas: 12000000,
  blockGasLimit: 12000000
}
```

## Complete hardhat.config.js Example

```javascript
require("@nomicfoundation/hardhat-toolbox");
require("@nomiclabs/hardhat-etherscan");
require("@openzeppelin/hardhat-upgrades");

const INFURA_API_KEY = process.env.INFURA_API_KEY || "";
const PRIVATE_KEY = process.env.PRIVATE_KEY || "";
const ETHERSCAN_API_KEY = process.env.ETHERSCAN_API_KEY || "";

module.exports = {
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    hardhat: {
      chainId: 31337,
      gas: 12000000,
      blockGasLimit: 12000000,
      allowUnlimitedContractSize: true
    },
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337,
      gas: 12000000,
      blockGasLimit: 12000000
    },
    goerli: {
      url: `https://goerli.infura.io/v3/${INFURA_API_KEY}`,
      accounts: [PRIVATE_KEY],
      chainId: 5,
      gasPrice: 20000000000,
      gas: 6000000
    },
    sepolia: {
      url: `https://sepolia.infura.io/v3/${INFURA_API_KEY}`,
      accounts: [PRIVATE_KEY],
      chainId: 11155111,
      gasPrice: 20000000000,
      gas: 6000000
    },
    mumbai: {
      url: "https://rpc-mumbai.maticvigil.com",
      accounts: [PRIVATE_KEY],
      chainId: 80001,
      gasPrice: 20000000000,
      gas: 6000000
    },
    ethereum: {
      url: `https://mainnet.infura.io/v3/${INFURA_API_KEY}`,
      accounts: [PRIVATE_KEY],
      chainId: 1,
      gasPrice: 20000000000,
      gas: 6000000
    },
    polygon: {
      url: "https://polygon-rpc.com",
      accounts: [PRIVATE_KEY],
      chainId: 137,
      gasPrice: 30000000000,
      gas: 6000000
    },
    arbitrum: {
      url: `https://arbitrum-mainnet.infura.io/v3/${INFURA_API_KEY}`,
      accounts: [PRIVATE_KEY],
      chainId: 42161,
      gasPrice: 15000000000,
      gas: 6000000
    },
    optimism: {
      url: `https://optimism-mainnet.infura.io/v3/${INFURA_API_KEY}`,
      accounts: [PRIVATE_KEY],
      chainId: 10,
      gasPrice: 15000000000,
      gas: 6000000
    },
    bsc: {
      url: "https://bsc-dataseed1.binance.org",
      accounts: [PRIVATE_KEY],
      chainId: 56,
      gasPrice: 20000000000,
      gas: 6000000
    }
  },
  etherscan: {
    apiKey: {
      mainnet: ETHERSCAN_API_KEY,
      goerli: ETHERSCAN_API_KEY,
      sepolia: ETHERSCAN_API_KEY,
      polygon: process.env.POLYGONSCAN_API_KEY,
      polygonMumbai: process.env.POLYGONSCAN_API_KEY,
      arbitrumOne: process.env.ARBISCAN_API_KEY,
      arbitrumGoerli: process.env.ARBISCAN_API_KEY,
      optimisticEthereum: process.env.OPTIMISM_API_KEY,
      optimisticGoerli: process.env.OPTIMISM_API_KEY,
      bsc: process.env.BSCSCAN_API_KEY,
      bscTestnet: process.env.BSCSCAN_API_KEY
    }
  },
  gasReporter: {
    enabled: process.env.REPORT_GAS !== undefined,
    currency: "USD"
  }
};
```

## Environment Setup

### 1. Create .env file
```bash
# Copy template
cp .env.example .env

# Edit .env file
nano .env
```

### 2. Required Environment Variables
```bash
# Infura API Key (for Ethereum, Arbitrum, Optimism)
INFURA_API_KEY=your_infura_api_key_here

# Private Key (never commit to version control)
PRIVATE_KEY=your_private_key_here

# Block Explorer API Keys
ETHERSCAN_API_KEY=your_etherscan_api_key_here
POLYGONSCAN_API_KEY=your_polygonscan_api_key_here
ARBISCAN_API_KEY=your_arbiscan_api_key_here
OPTIMISM_API_KEY=your_optimism_api_key_here
BSCSCAN_API_KEY=your_bscscan_api_key_here

# Gas Reporting (optional)
REPORT_GAS=true
```

### 3. Getting Test Ether

#### Goerli Testnet
- **Faucet**: https://goerlifaucet.com/
- **Alternative**: https://faucet.paradigm.xyz/
- **Requirements**: GitHub account with activity

#### Sepolia Testnet
- **Faucet**: https://sepoliafaucet.com/
- **Alternative**: https://faucet.sepolia.dev/
- **Requirements**: GitHub account with activity

#### Polygon Mumbai
- **Faucet**: https://faucet.polygon.technology/
- **Requirements**: No requirements, just wallet address

#### Arbitrum Goerli
- **Faucet**: https://faucet.arbitrum.io/
- **Requirements**: Twitter account

#### Optimism Goerli
- **Faucet**: https://faucet.optimism.io/
- **Requirements: Discord account

#### BSC Testnet
- **Faucet**: https://testnet.binance.org/faucet-smart
- **Requirements**: BNB Smart Chain wallet

## Gas Price Strategies

### Dynamic Gas Pricing
```javascript
networks: {
  ethereum: {
    url: `https://mainnet.infura.io/v3/${INFURA_API_KEY}`,
    accounts: [PRIVATE_KEY],
    chainId: 1,
    gasPrice: async () => {
      const gasPrice = await ethers.provider.getGasPrice();
      return gasPrice.mul(110).div(100); // +10%
    }
  }
}
```

### Fixed Gas Prices
```javascript
networks: {
  ethereum: {
    url: `https://mainnet.infura.io/v3/${INFURA_API_KEY}`,
    accounts: [PRIVATE_KEY],
    chainId: 1,
    gasPrice: 20000000000, // 20 gwei
    gas: 6000000
  }
}
```

## Troubleshooting

### Common Issues

#### 1. "Insufficient funds for gas"
- Check account balance on the target network
- Ensure you have native tokens for gas fees
- Adjust gas price if network is congested

#### 2. "Network timeout"
- Check RPC endpoint availability
- Try alternative RPC URLs
- Increase timeout in deployment script

#### 3. "Invalid chainId"
- Verify network chainId matches the blockchain
- Check network configuration in hardhat.config.js

#### 4. "Contract verification failed"
- Ensure exact Solidity version matches deployment
- Check constructor arguments
- Verify compiler settings (optimizer runs)

### Alternative RPC Providers

#### Alchemy
```javascript
ethereum: {
  url: `https://eth-mainnet.g.alchemy.com/v2/${process.env.ALCHEMY_API_KEY}`,
  accounts: [process.env.PRIVATE_KEY],
  chainId: 1
}
```

#### QuickNode
```javascript
ethereum: {
  url: `https://${process.env.QUICKNODE_ENDPOINT}`,
  accounts: [process.env.PRIVATE_KEY],
  chainId: 1
}
```

#### Ankr
```javascript
ethereum: {
  url: "https://rpc.ankr.com/eth",
  accounts: [process.env.PRIVATE_KEY],
  chainId: 1
}
```

## Best Practices

1. **Security**
   - Never commit private keys to version control
   - Use hardware wallets for mainnet deployments
   - Limit private key permissions

2. **Gas Optimization**
   - Monitor gas prices before deployment
   - Use dynamic gas pricing for mainnet
   - Consider Layer 2 solutions for cost savings

3. **Network Selection**
   - Use testnets for development and testing
   - Verify contracts on testnets before mainnet deployment
   - Consider network-specific requirements (block time, finality)

4. **Configuration Management**
   - Use environment variables for sensitive data
   - Separate configurations for different environments
   - Version control configuration templates (.env.example)

5. **Monitoring**
   - Track deployment costs
   - Monitor transaction confirmations
   - Set up alerts for failed transactions