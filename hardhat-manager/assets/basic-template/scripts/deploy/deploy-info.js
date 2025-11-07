// Deployment Information Management Script
// Provides easy access to deployed contract addresses and details

const { ethers } = require("hardhat");
const { deployments, getNamedAccounts, network } = require("hardhat");
const fs = require("fs");
const path = require("path");

/**
 * Get deployment information for a specific contract
 */
async function getContractInfo(contractName) {
  try {
    // Try to get from deployments
    const deployment = await deployments.get(contractName);
    console.log(`\n📍 ${contractName} Deployment Info:`);
    console.log(`   Address: ${deployment.address}`);
    console.log(`   Network: ${network.name}`);
    console.log(`   Block: ${deployment.receipt?.blockNumber || "N/A"}`);
    console.log(`   Tx Hash: ${deployment.receipt?.transactionHash || "N/A"}`);
    console.log(`   Gas Used: ${deployment.receipt?.gasUsed?.toString() || "N/A"}`);
    console.log(`   Deployer: ${deployment.args ? "With constructor args" : "No args"}`);

    return deployment;
  } catch (error) {
    console.log(`❌ Contract ${contractName} not found in deployments`);
    return null;
  }
}

/**
 * List all deployed contracts
 */
async function listAllDeployments() {
  console.log(`\n📋 All deployments on ${network.name}:`);

  const deploymentFiles = [];
  const deploymentsDir = path.join(process.cwd(), "deployments", network.name);

  if (fs.existsSync(deploymentsDir)) {
    const files = fs.readdirSync(deploymentsDir);
    for (const file of files) {
      if (file.endsWith(".json") && !file.includes(".db")) {
        const filePath = path.join(deploymentsDir, file);
        const data = JSON.parse(fs.readFileSync(filePath, "utf8"));
        deploymentFiles.push({
          name: file.replace(".json", ""),
          address: data.address,
          txHash: data.transactionHash || "N/A",
          blockNumber: data.receipt?.blockNumber || data.blockNumber || "N/A"
        });
      }
    }
  }

  if (deploymentFiles.length === 0) {
    console.log("   No deployments found");
  } else {
    console.log("");
    for (const contract of deploymentFiles) {
      console.log(`   • ${contract.name}:`);
      console.log(`     Address: ${contract.address}`);
      console.log(`     Tx: ${contract.txHash}`);
      console.log(`     Block: ${contract.blockNumber}`);
    }
  }

  return deploymentFiles;
}

/**
 * Generate deployment report
 */
async function generateDeploymentReport() {
  console.log(`\n📊 Generating deployment report for ${network.name}...`);

  const deploymentFiles = await listAllDeployments();

  const report = {
    network: network.name,
    timestamp: new Date().toISOString(),
    contracts: []
  };

  for (const contract of deploymentFiles) {
    try {
      const deployment = await deployments.get(contract.name);
      report.contracts.push({
        name: contract.name,
        address: deployment.address,
        deployedAt: new Date().toISOString(),
        blockNumber: deployment.receipt?.blockNumber,
        transactionHash: deployment.receipt?.transactionHash,
        gasUsed: deployment.receipt?.gasUsed?.toString(),
        deployer: deployment.from,
        network: network.name,
        chainId: network.config.chainId
      });
    } catch (error) {
      console.log(`⚠️ Could not get details for ${contract.name}: ${error.message}`);
    }
  }

  // Save report
  const reportPath = path.join(process.cwd(), "deployment-report.json");
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`💾 Report saved to: ${reportPath}`);

  return report;
}

/**
 * Verify deployment status
 */
async function verifyDeployment(contractName) {
  try {
    const deployment = await deployments.get(contractName);

    // Check if contract exists on network
    const code = await ethers.provider.getCode(deployment.address);
    if (code === "0x") {
      console.log(`❌ ${contractName}: Contract does not exist at ${deployment.address}`);
      return false;
    }

    console.log(`✅ ${contractName}: Contract exists at ${deployment.address}`);

    // Try to get contract instance
    try {
      const contract = await ethers.getContract(contractName);
      console.log(`✅ ${contractName}: Contract instance created successfully`);
      return true;
    } catch (error) {
      console.log(`⚠️ ${contractName}: Could not create instance: ${error.message}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ ${contractName}: Deployment not found`);
    return false;
  }
}

/**
 * Main CLI
 */
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  switch (command) {
    case "info":
      if (args[1]) {
        await getContractInfo(args[1]);
      } else {
        console.log("Usage: npx hardhat run scripts/deploy/deploy-info.js --network <network> -- info <contract-name>");
      }
      break;

    case "list":
      await listAllDeployments();
      break;

    case "report":
      await generateDeploymentReport();
      break;

    case "verify":
      if (args[1]) {
        await verifyDeployment(args[1]);
      } else {
        console.log("Usage: npx hardhat run scripts/deploy/deploy-info.js --network <network> -- verify <contract-name>");
      }
      break;

    case "export":
      await exportDeployments();
      break;

    default:
      console.log(`
📖 Deployment Information Tool

Usage:
  npx hardhat run scripts/deploy/deploy-info.js --network <network> -- <command>

Commands:
  info <contract-name>     Get detailed info about a specific contract
  list                    List all deployed contracts
  report                  Generate deployment report
  verify <contract-name>  Verify deployment status
  export                  Export deployments to JSON

Examples:
  npx hardhat run scripts/deploy/deploy-info.js --network goerli -- info MyContract
  npx hardhat run scripts/deploy/deploy-info.js --network polygon -- list
  npx hardhat run scripts/deploy/deploy-info.js --network mainnet -- report
      `);
  }
}

/**
 * Export deployments to JSON for frontend
 */
async function exportDeployments() {
  console.log("\n📤 Exporting deployments to JSON...");

  const deploymentFiles = await listAllDeployments();
  const exportData = {
    network: network.name,
    chainId: network.config.chainId,
    contracts: {}
  };

  for (const contract of deploymentFiles) {
    try {
      const deployment = await deployments.get(contract.name);
      exportData.contracts[contract.name] = {
        address: deployment.address,
        blockNumber: deployment.receipt?.blockNumber,
        transactionHash: deployment.receipt?.transactionHash
      };
    } catch (error) {
      console.log(`⚠️ Could not export ${contract.name}: ${error.message}`);
    }
  }

  // Save to exports directory
  const exportsDir = path.join(process.cwd(), "exports");
  if (!fs.existsSync(exportsDir)) {
    fs.mkdirSync(exportsDir);
  }

  const exportPath = path.join(exportsDir, `${network.name}-contracts.json`);
  fs.writeFileSync(exportPath, JSON.stringify(exportData, null, 2));

  console.log(`✅ Exported to: ${exportPath}`);
  console.log("\n📋 Exported contracts:");
  for (const [name, data] of Object.entries(exportData.contracts)) {
    console.log(`   ${name}: ${data.address}`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
