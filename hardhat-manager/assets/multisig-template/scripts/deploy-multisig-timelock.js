const fs = require("fs");
const path = require("path");

/**
 * Deploy Timelock Multisig Wallet
 *
 * This script deploys a TimelockMultisigWallet contract with the configuration
 * specified in config/multisig.config.js
 *
 * Usage:
 *   npx hardhat run scripts/deploy-multisig-timelock.js --network <network>
 */

async function main() {
  console.log("🚀 Deploying Timelock Multisig Wallet...\n");

  // Load configuration
  const config = require("../config/multisig.config.js");

  // You can choose different configurations here
  const deploymentConfig = config.dao; // Change to 'dao', 'project', or 'defi'

  // Validate configuration
  if (!deploymentConfig.owners || deploymentConfig.owners.length === 0) {
    throw new Error("No owners configured. Please update config/multisig.config.js");
  }

  if (!deploymentConfig.timelockEnabled) {
    throw new Error("Timelock is not enabled in the configuration");
  }

  if (deploymentConfig.owners.length < deploymentConfig.requiredConfirmations) {
    throw new Error("Not enough owners for required confirmations");
  }

  // Validate timelock configuration
  const timelock = deploymentConfig.timelock;
  if (!timelock) {
    throw new Error("Timelock configuration not found");
  }

  console.log("📋 Deployment Configuration:");
  console.log(`   Name: ${deploymentConfig.name}`);
  console.log(`   Description: ${deploymentConfig.description}`);
  console.log(`   Owners: ${deploymentConfig.owners.length}`);
  console.log(`   Required Confirmations: ${deploymentConfig.requiredConfirmations}`);
  console.log(`   Timelock Enabled: ${deploymentConfig.timelockEnabled ? "✅" : "❌"}`);
  console.log(`   Safe Mode: ${deploymentConfig.safeModeEnabled ? "Enabled" : "Disabled"}`);
  console.log(`   Gnosis Compatibility: ${deploymentConfig.gnosisCompatibility ? "Enabled" : "Disabled"}`);
  console.log(`   Use Case: ${deploymentConfig.useCase}`);
  console.log("");
  console.log("⏱️  Timelock Configuration:");
  console.log(`   Minimum Delay: ${timelock.minimumDelay / 3600} hours`);
  console.log(`   Maximum Delay: ${timelock.maximumDelay / (24 * 3600)} days`);
  console.log(`   Grace Period: ${timelock.gracePeriod / (24 * 3600)} days`);
  console.log(`   Emergency Delay: ${timelock.emergencyDelay / 3600} hours`);
  console.log(`   Tier 1 Threshold: ${timelock.tier1Threshold} ETH`);
  console.log(`   Tier 2 Threshold: ${timelock.tier2Threshold} ETH`);
  console.log(`   Tier 1 Confirmations: ${timelock.tier1Confirmations}`);
  console.log(`   Tier 2 Confirmations: ${timelock.tier2Confirmations}`);
  console.log(`   Tier 3 Confirmations: ${timelock.tier3Confirmations}`);
  if (deploymentConfig.timelockAdmins) {
    console.log(`   Timelock Admins: ${deploymentConfig.timelockAdmins.length}`);
  }
  console.log("");

  // Get deployer
  const [deployer] = await ethers.getSigners();
  console.log("👤 Deploying with account:", deployer.address);
  console.log("💰 Account balance:", ethers.utils.formatEther(await deployer.getBalance()), "ETH");
  console.log("");

  // Deploy TimelockMultisigWallet
  console.log("⏳ Deploying TimelockMultisigWallet contract...");
  const TimelockMultisigWallet = await ethers.getContractFactory("TimelockMultisigWallet");

  const timelockAdmins = deploymentConfig.timelockAdmins || deploymentConfig.owners;

  const timelockMultisig = await TimelockMultisigWallet.deploy(
    deploymentConfig.owners,
    deploymentConfig.requiredConfirmations,
    timelockAdmins
  );

  await timelockMultisig.deployed();

  console.log("✅ TimelockMultisigWallet deployed successfully!");
  console.log(`   Contract Address: ${timelockMultisig.address}`);
  console.log(`   Network: ${hre.network.name}`);
  console.log("");

  // Enable safe mode if configured
  if (deploymentConfig.safeModeEnabled) {
    console.log("🔒 Enabling safe mode...");
    await (await timelockMultisig.enableSafeMode()).wait();
    console.log("   Safe mode enabled");
  }

  // Enable Gnosis compatibility if configured
  if (deploymentConfig.gnosisCompatibility) {
    console.log("🔌 Enabling Gnosis Safe compatibility...");
    await (await timelockMultisig.enableGnosisCompatibility()).wait();
    console.log("   Gnosis compatibility enabled");
  }

  // Save deployment information
  const deploymentInfo = {
    contract: "TimelockMultisigWallet",
    network: hre.network.name,
    chainId: hre.network.config.chainId,
    address: timelockMultisig.address,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    config: deploymentConfig,
    timelockConfig: timelock,
    transactionHash: timelockMultisig.deployTransaction.hash
  };

  // Create deployments directory if it doesn't exist
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir, { recursive: true });
  }

  // Save to JSON file
  const filename = `timelock-multisig-${hre.network.name}-${Date.now()}.json`;
  const filepath = path.join(deploymentsDir, filename);
  fs.writeFileSync(filepath, JSON.stringify(deploymentInfo, null, 2));

  console.log("💾 Deployment info saved to:", filename);
  console.log("");

  // Print tier information
  const tierInfo = await timelockMultisig.getTierInfo();
  console.log("📊 Tier Configuration:");
  console.log("=".repeat(50));
  console.log(`Tier 1: < ${ethers.utils.formatEther(tierInfo.tier1Threshold)} ETH - ${tierInfo.tier1Confirmations} confirmations`);
  console.log(`Tier 2: < ${ethers.utils.formatEther(tierInfo.tier2Threshold)} ETH - ${tierInfo.tier2Confirmations} confirmations`);
  console.log(`Tier 3: >= ${ethers.utils.formatEther(tierInfo.tier2Threshold)} ETH - ${tierInfo.tier3Confirmations} confirmations`);
  console.log("=".repeat(50));
  console.log("");

  // Print delay information
  const delayInfo = await timelockMultisig.getDelayInfo();
  console.log("⏱️  Delay Configuration:");
  console.log("=".repeat(50));
  console.log(`Minimum Delay: ${delayInfo.minimumDelay / 3600} hours`);
  console.log(`Maximum Delay: ${delayInfo.maximumDelay / (24 * 3600)} days`);
  console.log(`Grace Period: ${delayInfo.gracePeriod / (24 * 3600)} days`);
  console.log(`Emergency Delay: ${delayInfo.emergencyDelay / 3600} hours`);
  console.log(`Emergency Grace: ${delayInfo.emergencyGracePeriod / 3600} hours`);
  console.log("=".repeat(50));
  console.log("");

  // Print next steps
  console.log("📝 Next Steps:");
  console.log("1. Fund the multisig wallet:");
  console.log(`   eth.send({from: eth.accounts[0], to: "${timelockMultisig.address}", value: web3.toWei(10, "ether")})`);
  console.log("");
  console.log("2. Queue a timelocked transaction:");
  console.log("   const delay = 24 * 60 * 60; // 24 hours");
  console.log("   const txId = await timelockMultisig.queueTimelockTransaction(recipient, amount, '0x', delay)");
  console.log("");
  console.log("3. Confirm transaction (from another owner):");
  console.log("   await timelockMultisig.confirmTimelockTransaction(txId)");
  console.log("");
  console.log("4. Wait for delay period, then execute:");
  console.log("   await timelockMultisig.executeTimelockTransaction(txId)");
  console.log("");
  console.log("5. For emergency transactions:");
  console.log("   const emgTxId = await timelockMultisig.queueEmergencyTransaction(recipient, amount, '0x')");
  console.log("   await timelockMultisig.executeEmergencyTransaction(emgTxId)");
  console.log("");

  return timelockMultisig.address;
}

// Export for use in other scripts
module.exports = { main };

// Execute main function if called directly
if (require.main === module) {
  main()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}
