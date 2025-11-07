// Smart Contract Deployment Script using hardhat-deploy
// Demonstrates best practices for deployment with hardhat-deploy

const { ethers } = require("hardhat");
const { deploy } = require("@openzeppelin/hardhat-upgrades");
const {
  developmentChains,
  VERIFICATION_BLOCK_CONFIRMATIONS,
  waitForDeployment,
  logDeploymentBalance,
  printDeploymentInfo,
  verify,
  checkNetworkConfig
} = require("../../helper-hardhat-config");

module.exports = async (hre) => {
  const { getNamedAccounts, deployments, network } = hre;
  const { deployer } = await getNamedAccounts();
  const { log } = deployments;

  const isLocal = developmentChains.includes(network.name);

  log("\n🚀 Starting MyContract deployment...");

  // 检查网络配置
  if (!isLocal) {
    checkNetworkConfig();
  }

  // 记录部署者余额
  await logDeploymentBalance(deployer);

  // 部署参数
  const args = []; // 构造函数参数

  // 部署合约
  try {
    log("📝 Deploying MyContract...");

    // 使用 hardhat-deploy 部署
    const myContract = await deployments.deploy("MyContract", {
      from: deployer,
      args: args,
      log: true,
      waitConfirmations: isLocal ? 1 : VERIFICATION_BLOCK_CONFIRMATIONS,
      gasPrice: isLocal ? undefined : "auto"
    });

    const { deployment, address, deploymentReceipt } = await waitForDeployment(myContract);

    // 打印部署信息
    printDeploymentInfo("MyContract", address, deploymentReceipt);

    // 验证合约（如果不在本地网络）
    if (!isLocal) {
      log("⏳ Waiting for block confirmations before verification...");
      await verify(address, args, "MyContract");
    }

    // 获取合约实例
    const myContractContract = await ethers.getContract("MyContract", deployer);

    // 初始化设置（如果需要）
    if (isLocal) {
      log("\n🔧 Running post-deployment initialization (local network only)...");

      // 示例：授权当前部署者为用户
      try {
        const initTx = await myContractContract.authorizeUser(deployer);
        await initTx.wait();
        log("✅ Authorized deployer as user");
      } catch (error) {
        log(`ℹ️ Authorization might have failed (this is normal if already authorized): ${error.message}`);
      }

      // 示例：创建测试数据
      try {
        const createItemTx = await myContractContract.createItem("Test Item", ethers.utils.parseEther("0.1"));
        await createItemTx.wait();
        log("✅ Created test item");
      } catch (error) {
        log(`ℹ️ Failed to create test item: ${error.message}`);
      }
    }

    // 保存合约信息
    log("\n💾 Saving contract information...");
    await deployments.save("MyContract", {
      address: address,
      abi: (await ethers.getContract("MyContract")).interface.format(ethers.utils.FormatTypes.json)
    });

    log("\n✅ MyContract deployment completed successfully!");

    return {
      address,
      deploymentReceipt,
      contract: myContractContract
    };

  } catch (error) {
    log(`\n❌ Deployment failed: ${error.message}`);
    log(`Stack trace: ${error.stack}`);
    throw error;
  }
};

module.exports.tags = ["all", "main", "MyContract"];
module.exports.dependencies = ["infrastructure"];
