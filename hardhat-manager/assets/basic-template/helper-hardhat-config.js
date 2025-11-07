// Helper configuration for Hardhat deployments

// 网络配置
const developmentChains = ["hardhat", "localhost", "arbitrumGoerli", "polygonMumbai", "sepolia", "goerli", "bscTestnet"];
const nonLocalChains = ["mainnet", "polygon", "arbitrum", "optimism", "bsc"];

// 确认次数配置
const VERIFICATION_BLOCK_CONFIRMATIONS = 6;
const WAIT_FOR_CONFIRMATIONS = developmentChains.includes(network.name) ? 1 : VERIFICATION_BLOCK_CONFIRMATIONS;

// API keys 检查
const API_KEYS = {
  ETHERSCAN: process.env.ETHERSCAN_API_KEY,
  POLYGONSCAN: process.env.POLYGONSCAN_API_KEY,
  ARBISCAN: process.env.ARBISCAN_API_KEY,
  OPTIMISTIC_ETHERSCAN: process.env.OPTIMISTIC_ETHERSCAN_API_KEY,
  BSCSCAN: process.env.BSCSCAN_API_KEY,
  ETHEREUM_RPC: process.env.MAINNET_RPC_URL || process.env.INFURA_API_KEY,
  POLYGON_RPC: process.env.POLYGON_RPC_URL,
  ARBITRUM_RPC: process.env.ARBITRUM_RPC_URL,
  OPTIMISM_RPC: process.env.OPTIMISM_RPC_URL,
  BSC_RPC: process.env.BSC_RPC_URL
};

// 验证函数
function verify(contractAddress, args, contractName) {
  console.log(`🔍 Verifying ${contractName}...`);

  // 检查是否在测试网络
  if (developmentChains.includes(network.name)) {
    console.log(`ℹ️ Skipping verification on ${network.name}`);
    return;
  }

  console.log("Waiting for block confirmations...");

  // 等待区块确认
  hre.run("verify:verify", {
    address: contractAddress,
    constructorArguments: args,
  }).then(() => {
    console.log(`✅ ${contractName} verified on ${network.name}`);
  }).catch((error) => {
    if (error.message.toLowerCase().includes("already verified")) {
      console.log(`ℹ️ ${contractName} is already verified on ${network.name}`);
    } else {
      console.error(error);
    }
  });
}

// 检查网络配置
function checkNetworkConfig() {
  const missingKeys = [];

  if (nonLocalChains.includes(network.name)) {
    // 检查 API key
    const networkKeyMap = {
      mainnet: "ETHEREUM_RPC",
      polygon: "POLYGON_RPC",
      arbitrum: "ARBITRUM_RPC",
      optimism: "OPTIMISM_RPC",
      bsc: "BSC_RPC"
    };

    const rpcKey = networkKeyMap[network.name];
    if (!API_KEYS[rpcKey]) {
      missingKeys.push(rpcKey);
    }

    // 检查验证 API key
    const verifyKeyMap = {
      mainnet: "ETHERSCAN",
      polygon: "POLYGONSCAN",
      arbitrum: "ARBISCAN",
      optimism: "OPTIMISTIC_ETHERSCAN",
      bsc: "BSCSCAN"
    };

    const apiKey = verifyKeyMap[network.name];
    if (!API_KEYS[apiKey]) {
      console.log(`⚠️ Warning: No ${apiKey} found. Contract verification will be skipped.`);
    }
  }

  if (missingKeys.length > 0) {
    throw new Error(`Missing required environment variables: ${missingKeys.join(", ")}`);
  }
}

// 格式化部署信息
function printDeploymentInfo(contractName, deployedContract, deploymentReceipt = null) {
  console.log(`\n🎉 ${contractName} deployed successfully!`);
  console.log(`   📍 Contract address: ${deployedContract.address}`);
  console.log(`   🔗 Network: ${network.name}`);

  if (deploymentReceipt) {
    console.log(`   📦 Gas used: ${deploymentReceipt.gasUsed.toString()}`);
    console.log(`   💰 Transaction hash: ${deploymentReceipt.transactionHash}`);
  }

  // 检查是否需要验证
  if (nonLocalChains.includes(network.name)) {
    console.log(`\n🔍 To verify the contract, run:`);
    console.log(`   npx hardhat verify --network ${network.name} ${deployedContract.address}`);
  }
}

// 等待部署确认
async function waitForDeployment(contractDeployment) {
  const deployment = await contractDeployment.waitForDeployment();

  // 等待确认
  if (!developmentChains.includes(network.name)) {
    await deployment.deploymentTransaction().wait(WAIT_FOR_CONFIRMATIONS);
  }

  const address = await deployment.getAddress();
  const deploymentReceipt = deployment.deploymentTransaction()
    ? await deployment.deploymentTransaction().wait()
    : null;

  return { deployment, address, deploymentReceipt };
}

// 获取账户余额
async function logDeploymentBalance(deployerAddress) {
  const balance = await ethers.provider.getBalance(deployerAddress);
  console.log(`💰 Deployer balance: ${ethers.utils.formatEther(balance)} ETH`);
}

// 批量部署函数
async function deployAllContracts(contracts, deploymentFunc) {
  console.log(`\n🚀 Starting batch deployment of ${contracts.length} contracts...`);
  const deployedContracts = [];

  for (const contractName of contracts) {
    try {
      const deployedContract = await deploymentFunc(contractName);
      deployedContracts.push({ name: contractName, ...deployedContract });
      console.log(`✅ ${contractName} deployed successfully`);
    } catch (error) {
      console.error(`❌ Failed to deploy ${contractName}:`, error);
      throw error;
    }
  }

  console.log(`\n🎉 Batch deployment completed! ${deployedContracts.length}/${contracts.length} contracts deployed.`);
  return deployedContracts;
}

module.exports = {
  developmentChains,
  nonLocalChains,
  VERIFICATION_BLOCK_CONFIRMATIONS,
  WAIT_FOR_CONFIRMATIONS,
  API_KEYS,
  verify,
  checkNetworkConfig,
  printDeploymentInfo,
  waitForDeployment,
  logDeploymentBalance,
  deployAllContracts
};
