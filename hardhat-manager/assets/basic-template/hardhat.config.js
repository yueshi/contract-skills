// Enhanced Hardhat config with hardhat-deploy support
require("@nomicfoundation/hardhat-toolbox");
require("hardhat-deploy");
require("hardhat-contract-sizer");
require("hardhat-gas-reporter");
require("solidity-coverage");
require("dotenv").config();

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  // 默认网络配置
  defaultNetwork: "hardhat",

  // 网络配置
  networks: {
    hardhat: {
      chainId: 31337,
      accounts: {
        count: 100,
        accountsBalance: "10000000000000000000000" // 10000 ETH per account
      },
      // 支持主网分叉测试
      forking: {
        url: process.env.MAINNET_RPC_URL || "",
        enabled: process.env.FORK_ENABLED === "true",
        blockNumber: process.env.FORK_BLOCK_NUMBER || undefined
      }
    },

    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337,
      tags: ["local", "development"]
    },

    // 以太坊测试网
    goerli: {
      url: process.env.GOERLI_RPC_URL || `https://goerli.infura.io/v3/${process.env.INFURA_API_KEY}`,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 5,
      gasPrice: 20000000000, // 20 gwei
      confirmations: 2,
      timeout: 30000,
      tags: ["testnet", "ethereum"]
    },

    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || `https://sepolia.infura.io/v3/${process.env.INFURA_API_KEY}`,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 11155111,
      gasPrice: 20000000000,
      confirmations: 2,
      timeout: 30000,
      tags: ["testnet", "ethereum"]
    },

    // 以太坊主网
    mainnet: {
      url: process.env.MAINNET_RPC_URL || `https://mainnet.infura.io/v3/${process.env.INFURA_API_KEY}`,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 1,
      gasPrice: "auto",
      gas: "auto",
      confirmations: 2,
      timeout: 300000, // 5分钟超时
      tags: ["mainnet", "production"]
    },

    // Polygon
    polygon: {
      url: process.env.POLYGON_RPC_URL || "https://polygon-rpc.com",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 137,
      gasPrice: 30000000000, // 30 gwei
      confirmations: 5,
      timeout: 60000,
      tags: ["mainnet", "polygon"]
    },

    mumbai: {
      url: process.env.MUMBAI_RPC_URL || "https://rpc-mumbai.maticvigil.com",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 80001,
      gasPrice: 20000000000,
      confirmations: 3,
      timeout: 30000,
      tags: ["testnet", "polygon"]
    },

    // Arbitrum
    arbitrum: {
      url: process.env.ARBITRUM_RPC_URL || `https://arbitrum-mainnet.infura.io/v3/${process.env.INFURA_API_KEY}`,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 42161,
      gasPrice: "auto",
      confirmations: 3,
      timeout: 60000,
      tags: ["mainnet", "arbitrum"]
    },

    arbitrumGoerli: {
      url: process.env.ARBITRUM_GOERLI_RPC_URL || `https://arbitrum-goerli.infura.io/v3/${process.env.INFURA_API_KEY}`,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 421613,
      gasPrice: "auto",
      confirmations: 2,
      timeout: 30000,
      tags: ["testnet", "arbitrum"]
    },

    // Optimism
    optimism: {
      url: process.env.OPTIMISM_RPC_URL || `https://optimism-mainnet.infura.io/v3/${process.env.INFURA_API_KEY}`,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 10,
      gasPrice: "auto",
      confirmations: 3,
      timeout: 60000,
      tags: ["mainnet", "optimism"]
    },

    optimismGoerli: {
      url: process.env.OPTIMISM_GOERLI_RPC_URL || `https://optimism-goerli.infura.io/v3/${process.env.INFURA_API_KEY}`,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 420,
      gasPrice: "auto",
      confirmations: 2,
      timeout: 30000,
      tags: ["testnet", "optimism"]
    },

    // BSC
    bsc: {
      url: process.env.BSC_RPC_URL || "https://bsc-dataseed1.binance.org",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 56,
      gasPrice: 5000000000, // 5 gwei
      confirmations: 3,
      timeout: 30000,
      tags: ["mainnet", "bsc"]
    },

    bscTestnet: {
      url: process.env.BSC_TESTNET_RPC_URL || "https://data-seed-prebsc-1-s1.binance.org:8545",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 97,
      gasPrice: 10000000000, // 10 gwei
      confirmations: 2,
      timeout: 30000,
      tags: ["testnet", "bsc"]
    }
  },

  // Solidity 编译器配置
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200  // 编译优化次数，平衡 gas 成本和部署成本
      }
    }
  },

  // 合约大小分析器
  contractSizer: {
    alphaSort: true,
    disambiguatePaths: false,
    runOnCompile: true,
    strict: true,
    only: []
  },

  // Gas 报告配置
  gasReporter: {
    enabled: process.env.REPORT_GAS !== undefined,
    currency: "USD",
    gasPrice: 20,
    showTimeSpent: true,
    showMethodSig: true,
    showNodeName: true,
    outputFile: "gas-report.txt",
    noColors: true
  },

  // Mocha 测试配置
  mocha: {
    timeout: 60000 // 60 秒超时
  },

  // 路径配置
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
    // 部署相关路径
    deployments: "./deployments",  // 部署信息保存目录
    deployScripts: "./scripts/deploy" // 部署脚本目录
  },

  // 部署配置
  namedAccounts: {
    deployer: {
      default: 0, // 默认使用第一个账户
      1: "0xa29d4ccAdF5A14C0C7C5b50A04a35C9c6C2d9b7e", // 主网部署者地址
      5: {
        default: 0  // Goerli 使用第一个账户
      },
      137: {
        default: 0  // Polygon 使用第一个账户
      },
      42161: {
        default: 0  // Arbitrum 使用第一个账户
      },
      10: {
        default: 0  // Optimism 使用第一个账户
      },
      56: {
        default: 0  // BSC 使用第一个账户
      }
    },
    feeCollector: {
      default: 1, // 默认使用第二个账户作为手续费收集者
      1: "0x8ba1f109551bD432803012645Hac136c22B17E6D"
    }
  },

  // Etherscan 验证配置
  etherscan: {
    apiKey: {
      mainnet: process.env.ETHERSCAN_API_KEY,
      goerli: process.env.ETHERSCAN_API_KEY,
      sepolia: process.env.ETHERSCAN_API_KEY,
      polygon: process.env.POLYGONSCAN_API_KEY,
      polygonMumbai: process.env.POLYGONSCAN_API_KEY,
      arbitrumOne: process.env.ARBISCAN_API_KEY,
      arbitrumGoerli: process.env.ARBISCAN_API_KEY,
      optimisticEthereum: process.env.OPTIMISTIC_ETHERSCAN_API_KEY,
      optimisticGoerli: process.env.OPTIMISTIC_ETHERSCAN_API_KEY,
      bsc: process.env.BSCSCAN_API_KEY,
      bscTestnet: process.env.BSCSCAN_API_KEY
    },
    customChains: [
      {
        network: "arbitrum",
        chainId: 42161,
        urls: {
          apiURL: "https://api.arbiscan.io/api",
          browserURL: "https://arbiscan.io"
        }
      },
      {
        network: "polygon",
        chainId: 137,
        urls: {
          apiURL: "https://api.polygonscan.com/api",
          browserURL: "https://polygonscan.com"
        }
      }
    ]
  }
};
