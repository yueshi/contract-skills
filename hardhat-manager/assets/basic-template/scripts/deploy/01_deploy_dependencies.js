// Deployment script using hardhat-deploy
// This script deploys necessary infrastructure contracts first

const { ethers } = require("hardhat");
const { deploy } = require("@openzeppelin/hardhat-upgrades");
const { developmentChains } = require("../../helper-hardhat-config");

module.exports = async (hre) => {
  const { getNamedAccounts, deployments, network } = hre;
  const { deployer, feeCollector } = await getNamedAccounts();
  const { log } = deployments;

  const isLocal = developmentChains.includes(network.name);

  log("\n🚀 Deploying infrastructure contracts...");

  // Deploy MockToken (for testing)
  if (isLocal) {
    const MockToken = await ethers.getContractFactory("MockToken");
    log(`📝 Deploying MockToken as deployer: ${deployer}`);

    const mockToken = await MockToken.deploy("Mock Token", "MTK");
    await mockToken.deployed();

    log(`✅ MockToken deployed at: ${mockToken.address}`);

    // Save deployment
    await deployments.save("MockToken", {
      address: mockToken.address,
      abi: mockToken.interface.format(ethers.utils.FormatTypes.json)
    });

    // Transfer ownership if needed
    const owner = await mockToken.owner();
    if (owner === deployer) {
      log("ℹ️ MockToken owner is deployer (as expected)");
    }
  }

  // Deploy MockWETH (for testing)
  if (isLocal) {
    const MockWETH = await ethers.getContractFactory("MockWETH");
    log(`📝 Deploying MockWETH as deployer: ${deployer}`);

    const mockWETH = await MockWETH.deploy();
    await mockWETH.deployed();

    log(`✅ MockWETH deployed at: ${mockWETH.address}`);

    // Save deployment
    await deployments.save("MockWETH", {
      address: mockWETH.address,
      abi: mockWETH.interface.format(ethers.utils.FormatTypes.json)
    });
  }

  log("\n✅ Infrastructure contracts deployment completed!");
};

module.exports.tags = ["all", "infrastructure"];
