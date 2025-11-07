const fs = require("fs");
const path = require("path");

/**
 * Deploy Basic Multisig Wallet
 *
 * This script deploys a MultisigWallet contract with the configuration
 * specified in config/multisig.config.js
 *
 * Usage:
 *   npx hardhat run scripts/deploy-multisig-basic.js --network <network>
 */

async function main() {
  console.log("🚀 Deploying Basic Multisig Wallet...\n");

  // Load configuration
  const config = require("../config/multisig.config.js");
  const deploymentConfig = config.basic; // Change to 'dao', 'project', 'defi', or 'personal'

  // Validate configuration
  if (!deploymentConfig.owners || deploymentConfig.owners.length === 0) {
    throw new Error("No owners configured. Please update config/multisig.config.js");
  }

  if (deploymentConfig.owners.length < deploymentConfig.requiredConfirmations) {
    throw new Error("Not enough owners for required confirmations");
  }

  console.log("📋 Deployment Configuration:");
  console.log(`   Name: ${deploymentConfig.name}`);
  console.log(`   Description: ${deploymentConfig.description}`);
  console.log(`   Owners: ${deploymentConfig.owners.length}`);
  console.log(`   Required Confirmations: ${deploymentConfig.requiredConfirmations}`);
  console.log(`   Safe Mode: ${deploymentConfig.safeModeEnabled ? "Enabled" : "Disabled"}`);
  console.log(`   Gnosis Compatibility: ${deploymentConfig.gnosisCompatibility ? "Enabled" : "Disabled"}`);
  console.log(`   Use Case: ${deploymentConfig.useCase}`);
  console.log("");

  // Get deployer
  const [deployer] = await ethers.getSigners();
  console.log("👤 Deploying with account:", deployer.address);
  console.log("💰 Account balance:", ethers.utils.formatEther(await deployer.getBalance()), "ETH");
  console.log("");

  // Deploy MultisigWallet
  console.log("⏳ Deploying MultisigWallet contract...");
  const MultisigWallet = await ethers.getContractFactory("MultisigWallet");

  const multisig = await MultisigWallet.deploy(
    deploymentConfig.owners,
    deploymentConfig.requiredConfirmations
  );

  await multisig.deployed();

  console.log("✅ MultisigWallet deployed successfully!");
  console.log(`   Contract Address: ${multisig.address}`);
  console.log(`   Network: ${hre.network.name}`);
  console.log("");

  // Enable safe mode if configured
  if (deploymentConfig.safeModeEnabled) {
    console.log("🔒 Enabling safe mode...");
    await (await multisig.enableSafeMode()).wait();
    console.log("   Safe mode enabled");
  }

  // Enable Gnosis compatibility if configured
  if (deploymentConfig.gnosisCompatibility) {
    console.log("🔌 Enabling Gnosis Safe compatibility...");
    await (await multisig.enableGnosisCompatibility()).wait();
    console.log("   Gnosis compatibility enabled");
  }

  // Save deployment information
  const deploymentInfo = {
    contract: "MultisigWallet",
    network: hre.network.name,
    chainId: hre.network.config.chainId,
    address: multisig.address,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    config: deploymentConfig,
    transactionHash: multisig.deployTransaction.hash
  };

  // Create deployments directory if it doesn't exist
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir, { recursive: true });
  }

  // Save to JSON file
  const filename = `multisig-${hre.network.name}-${Date.now()}.json`;
  const filepath = path.join(deploymentsDir, filename);
  fs.writeFileSync(filepath, JSON.stringify(deploymentInfo, null, 2));

  console.log("💾 Deployment info saved to:", filename);
  console.log("");

  // Print summary
  console.log("📊 Deployment Summary:");
  console.log("=".repeat(50));
  console.log(`Contract: ${deploymentConfig.name}`);
  console.log(`Address: ${multisig.address}`);
  console.log(`Owners: ${deploymentConfig.owners.length}`);
  console.log(`Required: ${deploymentConfig.requiredConfirmations}`);
  console.log(`Safe Mode: ${deploymentConfig.safeModeEnabled ? "✅" : "❌"}`);
  console.log(`Gnosis Compatible: ${deploymentConfig.gnosisCompatibility ? "✅" : "❌"}`);
  console.log("=".repeat(50));
  console.log("");

  // Print next steps
  console.log("📝 Next Steps:");
  console.log("1. Fund the multisig wallet with ETH:");
  console.log(`   eth.send({from: eth.accounts[0], to: "${multisig.address}", value: web3.toWei(10, "ether")})`);
  console.log("");
  console.log("2. Submit a transaction:");
  console.log("   const tx = await multisig.submitTransaction(recipient, amount, '0x')");
  console.log("");
  console.log("3. Confirm transaction (from another owner):");
  console.log("   await multisig.confirmTransaction(tx)");
  console.log("");
  console.log("4. Execute transaction:");
  console.log("   await multisig.executeTransaction(tx)");
  console.log("");

  return multisig.address;
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
