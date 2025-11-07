# Smart Contract Deployment Patterns

This guide covers common deployment patterns and best practices for smart contracts using Hardhat. Each pattern includes implementation examples, use cases, and security considerations.

## Table of Contents

1. [Simple Deployment Pattern](#simple-deployment-pattern)
2. [Factory Pattern](#factory-pattern)
3. [Proxy Pattern](#proxy-pattern)
4. [Deterministic Deployment](#deterministic-deployment)
5. [Multi-Contract Deployment](#multi-contract-deployment)
6. [Upgradeable Deployment](#upgradeable-deployment)
7. [Batch Deployment](#batch-deployment)
8. [Timelock Deployment](#timelock-deployment)

## Simple Deployment Pattern

### Use Case
- Single contract deployment
- No upgradeability requirements
- Simple token or utility contracts
- Prototypes and testing

### Implementation

#### Deployment Script (deploy.js)
```javascript
const { ethers } = require("hardhat");

async function main() {
  console.log("Starting deployment...");

  // Get contract factory
  const ContractFactory = await ethers.getContractFactory("MyContract");

  // Deploy contract
  console.log("Deploying MyContract...");
  const contract = await ContractFactory.deploy();

  // Wait for deployment confirmation
  await contract.deployed();

  console.log("MyContract deployed to:", contract.address);
  console.log("Transaction hash:", contract.deployTransaction.hash);
  console.log("Gas used:", contract.deployTransaction.gasLimit.toString());

  // Save deployment info
  saveDeploymentInfo(contract);
}

function saveDeploymentInfo(contract) {
  const fs = require("fs");
  const deploymentsDir = "./deployments";

  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir);
  }

  const deploymentInfo = {
    contractName: "MyContract",
    address: contract.address,
    transactionHash: contract.deployTransaction.hash,
    gasUsed: contract.deployTransaction.gasLimit.toString(),
    deployer: contract.deployTransaction.from,
    network: network.name,
    timestamp: new Date().toISOString()
  };

  fs.writeFileSync(
    `${deploymentsDir}/${network.name}-MyContract.json`,
    JSON.stringify(deploymentInfo, null, 2)
  );
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
```

#### With Constructor Arguments
```javascript
async function main() {
  const ContractFactory = await ethers.getContractFactory("MyToken");

  // Deploy with constructor arguments
  const token = await ContractFactory.deploy(
    "My Token",           // name
    "MTK",                // symbol
    18,                   // decimals
    ethers.utils.parseEther("1000000") // initial supply
  );

  await token.deployed();
  console.log("MyToken deployed to:", token.address);
}
```

## Factory Pattern

### Use Case
- Creating multiple instances of a contract
- NFT collections
- Token factories
- Gaming applications

### Implementation

#### Factory Contract
```solidity
// contracts/ContractFactory.sol
pragma solidity ^0.8.19;

import "./MyContract.sol";

contract ContractFactory {
    address[] public deployedContracts;
    mapping(address => bool) public isDeployedContract;
    mapping(address => address[]) public userContracts;

    event ContractCreated(
        address indexed creator,
        address indexed contractAddress,
        uint256 timestamp
    );

    function createContract(
        string memory name,
        uint256 initialValue
    ) public returns (address) {
        MyContract newContract = new MyContract(
            name,
            initialValue,
            msg.sender
        );

        deployedContracts.push(address(newContract));
        isDeployedContract[address(newContract)] = true;
        userContracts[msg.sender].push(address(newContract));

        emit ContractCreated(msg.sender, address(newContract), block.timestamp);

        return address(newContract);
    }

    function getDeployedContractsCount() public view returns (uint256) {
        return deployedContracts.length;
    }

    function getUserContracts(address user) public view returns (address[] memory) {
        return userContracts[user];
    }
}
```

#### Factory Deployment Script
```javascript
async function main() {
  console.log("Deploying ContractFactory...");

  const FactoryFactory = await ethers.getContractFactory("ContractFactory");
  const factory = await FactoryFactory.deploy();

  await factory.deployed();
  console.log("ContractFactory deployed to:", factory.address);

  // Create a few example contracts
  console.log("Creating example contracts...");

  const tx1 = await factory.createContract("Contract 1", 100);
  await tx1.wait();

  const tx2 = await factory.createContract("Contract 2", 200);
  await tx2.wait();

  console.log("Example contracts created");
}
```

## Proxy Pattern

### Use Case
- Upgradeable contracts
- Large contracts that exceed size limits
- Contracts that need frequent updates
- DeFi protocols

### Implementation

#### UUPS Proxy Pattern
```solidity
// contracts/MyUpgradeableContract.sol
pragma solidity ^0.8.19;

import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";

contract MyUpgradeableContract is Initializable, UUPSUpgradeable, OwnableUpgradeable {
    uint256 public value;
    string public name;

    function initialize(string memory _name, uint256 _initialValue) public initializer {
        __Ownable_init();
        name = _name;
        value = _initialValue;
    }

    function setValue(uint256 _newValue) public {
        value = _newValue;
    }

    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}
}
```

#### Deployment Script
```javascript
const { ethers, upgrades } = require("hardhat");

async function main() {
  console.log("Deploying upgradeable contract...");

  const ContractFactory = await ethers.getContractFactory("MyUpgradeableContract");

  // Deploy upgradeable contract
  const contract = await upgrades.deployProxy(
    ContractFactory,
    ["My Contract", 100], // constructor arguments for initialize
    { initializer: "initialize" }
  );

  await contract.deployed();
  console.log("Upgradeable contract deployed to:", contract.address);

  // Get implementation address
  const implementationAddress = await upgrades.erc1967.getImplementationAddress(
    contract.address
  );
  console.log("Implementation address:", implementationAddress);

  // Save deployment info
  saveProxyDeploymentInfo(contract, implementationAddress);
}

function saveProxyDeploymentInfo(contract, implementationAddress) {
  const fs = require("fs");
  const deploymentsDir = "./deployments";

  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir);
  }

  const deploymentInfo = {
    contractName: "MyUpgradeableContract",
    proxyAddress: contract.address,
    implementationAddress: implementationAddress,
    network: network.name,
    timestamp: new Date().toISOString()
  };

  fs.writeFileSync(
    `${deploymentsDir}/${network.name}-MyUpgradeableContract-proxy.json`,
    JSON.stringify(deploymentInfo, null, 2)
  );
}
```

## Deterministic Deployment

### Use Case
- Known contract addresses before deployment
- Cross-chain contract deployments
- Protocol integrations
- Factory contracts with predictable addresses

### Implementation

#### Create2 Deployment Script
```javascript
const { ethers } = require("hardhat");

async function main() {
  console.log("Starting deterministic deployment...");

  // Get contract factory
  const ContractFactory = await ethers.getContractFactory("MyContract");

  // Calculate deployment parameters
  const salt = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("MySalt"));
  const creationCode = ContractFactory.bytecode;

  // Calculate future address
  const [signer] = await ethers.getSigners();
  const futureAddress = ethers.utils.getCreate2Address(
    signer.address, // deployer address
    salt,
    ethers.utils.keccak256(creationCode)
  );

  console.log("Future contract address:", futureAddress);

  // Deploy using CREATE2
  const factory = await ethers.getContractFactory("DeterministicDeployFactory");
  const deployTx = await factory.deploy(0, salt, creationCode);
  const receipt = await deployTx.wait();

  console.log("Contract deployed to:", futureAddress);
  console.log("Transaction hash:", receipt.transactionHash);
}
```

#### Using Hardhat Create2 Plugin
```javascript
// hardhat.config.js
require("hardhat-deploy");

module.exports = {
  // ... config
};

// scripts/deploy-deterministic.js
async function main() {
  const { deploy } = deployments;

  const { deployer } = await getNamedAccounts();

  await deploy("MyContract", {
    from: deployer,
    args: ["arg1", "arg2"],
    deterministicDeployment: "my-salt",
  });
}
```

## Multi-Contract Deployment

### Use Case
- Complex DeFi protocols
- Projects with multiple interacting contracts
- Systems with shared dependencies

### Implementation

#### Sequential Deployment
```javascript
async function main() {
  console.log("Starting multi-contract deployment...");

  const [deployer] = await ethers.getSigners();
  console.log("Deploying with account:", deployer.address);

  // Deploy contracts in dependency order
  const deployments = {};

  // 1. Deploy governance token
  console.log("Deploying GovernanceToken...");
  const GovernanceToken = await ethers.getContractFactory("GovernanceToken");
  deployments.token = await GovernanceToken.deploy();
  await deployments.token.deployed();
  console.log("GovernanceToken deployed to:", deployments.token.address);

  // 2. Deploy treasury
  console.log("Deploying Treasury...");
  const Treasury = await ethers.getContractFactory("Treasury");
  deployments.treasury = await Treasury.deploy(deployments.token.address);
  await deployments.treasury.deployed();
  console.log("Treasury deployed to:", deployments.treasury.address);

  // 3. Deploy governor
  console.log("Deploying Governor...");
  const Governor = await ethers.getContractFactory("MyGovernor");
  deployments.governor = await Governor.deploy(
    deployments.token.address,
    deployments.treasury.address
  );
  await deployments.governor.deployed();
  console.log("Governor deployed to:", deployments.governor.address);

  // 4. Setup contracts
  console.log("Setting up contracts...");
  await deployments.token.transferOwnership(deployments.governor.address);
  await deployments.treasury.transferOwnership(deployments.governor.address);

  console.log("Multi-contract deployment completed!");

  // Save deployment info
  saveMultiDeploymentInfo(deployments);
}

function saveMultiDeploymentInfo(deployments) {
  const fs = require("fs");
  const deploymentsDir = "./deployments";

  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir);
  }

  const deploymentInfo = {
    network: network.name,
    timestamp: new Date().toISOString(),
    contracts: {}
  };

  for (const [name, contract] of Object.entries(deployments)) {
    deploymentInfo.contracts[name] = {
      address: contract.address,
      transactionHash: contract.deployTransaction.hash,
      gasUsed: contract.deployTransaction.gasLimit.toString()
    };
  }

  fs.writeFileSync(
    `${deploymentsDir}/${network.name}-system-deployment.json`,
    JSON.stringify(deploymentInfo, null, 2)
  );
}
```

## Upgradeable Deployment

### Use Case
- DeFi protocols requiring upgrades
- Long-term projects with evolving requirements
- Contracts needing bug fixes or improvements

### Implementation

#### Upgrade Script
```javascript
const { ethers, upgrades } = require("hardhat");

async function main() {
  const PROXY_ADDRESS = "0x..."; // Existing proxy address

  console.log("Upgrading contract at:", PROXY_ADDRESS);

  // Get the new implementation contract factory
  const ContractFactory = await ethers.getContractFactory("MyUpgradeableContractV2");

  // Upgrade the proxy
  const upgraded = await upgrades.upgradeProxy(PROXY_ADDRESS, ContractFactory);

  console.log("Contract upgraded successfully");
  console.log("New implementation address:", await upgrades.erc1967.getImplementationAddress(PROXY_ADDRESS));

  // Test new functionality
  if (upgraded.newFunction) {
    await upgraded.newFunction();
    console.log("New function tested successfully");
  }
}
```

## Batch Deployment

### Use Case
- Deploying multiple similar contracts
- NFT collections with multiple tokens
- Large-scale token deployments

### Implementation

#### Batch Deployment Script
```javascript
async function main() {
  console.log("Starting batch deployment...");

  const ContractFactory = await ethers.getContractFactory("MyToken");
  const deployments = [];
  const batchSize = 10; // Deploy in batches to avoid gas issues

  const tokens = [
    { name: "Token A", symbol: "TKA", supply: ethers.utils.parseEther("1000000") },
    { name: "Token B", symbol: "TKB", supply: ethers.utils.parseEther("2000000") },
    { name: "Token C", symbol: "TKC", supply: ethers.utils.parseEther("500000") },
    // ... more tokens
  ];

  for (let i = 0; i < tokens.length; i += batchSize) {
    console.log(`Deploying batch ${Math.floor(i / batchSize) + 1}...`);

    const batch = tokens.slice(i, i + batchSize);
    const batchDeployments = await Promise.all(
      batch.map(async (tokenData, index) => {
        const token = await ContractFactory.deploy(
          tokenData.name,
          tokenData.symbol,
          18,
          tokenData.supply
        );
        await token.deployed();

        return {
          name: tokenData.name,
          symbol: tokenData.symbol,
          address: token.address,
          transactionHash: token.deployTransaction.hash
        };
      })
    );

    deployments.push(...batchDeployments);
    console.log(`Batch ${Math.floor(i / batchSize) + 1} completed`);
  }

  console.log("Batch deployment completed!");
  console.log(`Total contracts deployed: ${deployments.length}`);

  // Save batch deployment info
  saveBatchDeploymentInfo(deployments);
}
```

## Timelock Deployment

### Use Case
- Governance systems
- Security-critical deployments
- Contracts requiring execution delays

### Implementation

#### Timelock Contract
```solidity
// contracts/Timelock.sol
pragma solidity ^0.8.19;

contract Timelock {
    uint256 public constant MIN_DELAY = 2 days;
    uint256 public constant MAX_DELAY = 30 days;

    uint256 public delay;
    address public admin;
    mapping(bytes32 => bool) public queuedTransactions;

    event QueuedTransaction(bytes32 indexed txHash, address indexed target, uint256 value, string signature, bytes data, uint256 eta);
    event ExecutedTransaction(bytes32 indexed txHash, address indexed target, uint256 value, string signature, bytes data);
    event CancelledTransaction(bytes32 indexed txHash);
    event NewDelay(uint256 newDelay);
    event NewAdmin(address indexed newAdmin);

    constructor(address _admin, uint256 _delay) {
        admin = _admin;
        delay = _delay;
    }

    function queueTransaction(
        address target,
        uint256 value,
        string memory signature,
        bytes memory data,
        uint256 eta
    ) public returns (bytes32) {
        require(msg.sender == admin, "Timelock: Caller not admin");
        require(eta >= block.timestamp + delay, "Timelock: ETA too early");

        bytes32 txHash = keccak256(abi.encode(target, value, signature, data, eta));
        queuedTransactions[txHash] = true;

        emit QueuedTransaction(txHash, target, value, signature, data, eta);
        return txHash;
    }

    function executeTransaction(
        address target,
        uint256 value,
        string memory signature,
        bytes memory data,
        uint256 eta
    ) public payable returns (bytes memory) {
        bytes32 txHash = keccak256(abi.encode(target, value, signature, data, eta));

        require(queuedTransactions[txHash], "Timelock: Transaction not queued");
        require(block.timestamp >= eta, "Timelock: ETA not reached");
        require(block.timestamp <= eta + delay, "Timelock: Transaction expired");

        queuedTransactions[txHash] = false;

        bytes memory callData;
        if (bytes(signature).length == 0) {
            callData = data;
        } else {
            callData = abi.encodePacked(bytes4(keccak256(bytes(signature))), data);
        }

        (bool success, bytes memory returnData) = target.call{value: value}(callData);
        require(success, "Timelock: Transaction execution failed");

        emit ExecutedTransaction(txHash, target, value, signature, data);
        return returnData;
    }
}
```

#### Timelock Deployment Script
```javascript
async function main() {
  console.log("Deploying timelock system...");

  const [deployer] = await ethers.getSigners();
  const delay = 2 * 24 * 60 * 60; // 2 days in seconds

  // Deploy timelock
  const Timelock = await ethers.getContractFactory("Timelock");
  const timelock = await Timelock.deploy(deployer.address, delay);
  await timelock.deployed();
  console.log("Timelock deployed to:", timelock.address);

  // Deploy target contract
  const TargetContract = await ethers.getContractFactory("MyGovernanceContract");
  const targetContract = await TargetContract.deploy();
  await targetContract.deployed();
  console.log("Target contract deployed to:", targetContract.address);

  // Transfer ownership to timelock
  await targetContract.transferOwnership(timelock.address);
  console.log("Ownership transferred to timelock");

  // Queue a transaction example
  const eta = Math.floor(Date.now() / 1000) + delay + 3600; // ETA = now + delay + 1 hour
  const txHash = await timelock.queueTransaction(
    targetContract.address,
    0,
    "setDelay(uint256)",
    ethers.utils.defaultAbiCoder.encode(["uint256"], [3 * 24 * 60 * 60]), // 3 days
    eta
  );

  console.log("Transaction queued with hash:", txHash.hash);
  console.log("Can be executed after:", new Date(eta * 1000));
}
```

## Deployment Best Practices

### ✅ Pre-Deployment Checks
1. **Contract Testing**: Comprehensive testing on testnets
2. **Gas Optimization**: Optimize deployment and execution gas
3. **Security Audit**: Professional security audit completed
4. **Code Review**: Multiple developers review the code
5. **Configuration Check**: Verify network configurations

### ✅ Deployment Process
1. **Dry Run**: Deploy on testnet first
2. **Verification**: Prepare verification data
3. **Monitoring**: Set up monitoring and alerts
4. **Documentation**: Document deployment parameters
5. **Rollback Plan**: Have emergency rollback procedures

### ✅ Post-Deployment
1. **Contract Verification**: Verify on block explorers
2. **Initial Testing**: Test basic functionality
3. **Monitoring Setup**: Deploy monitoring systems
4. **User Communication**: Inform users about new contracts
5. **Security Monitoring**: Monitor for suspicious activity

### ✅ Security Considerations
1. **Access Control**: Implement proper access controls
2. **Pause Mechanisms**: Include emergency pause functionality
3. **Upgrade Safety**: Ensure upgrade mechanisms are secure
4. **Event Logging**: Comprehensive event logging
5. **Error Handling**: Proper error handling and user feedback

## Common Deployment Issues and Solutions

### ❌ "Out of Gas"
**Solution**: Increase gas limit or optimize contract
```javascript
const contract = await ContractFactory.deploy({
  gasLimit: 8000000
});
```

### ❌ "Transaction Reverted"
**Solution**: Check constructor arguments and validation
```javascript
try {
  const contract = await ContractFactory.deploy(args);
} catch (error) {
  console.error("Deployment failed:", error.message);
  // Handle error
}
```

### ❌ "Contract Size Too Large"
**Solution**: Use proxy pattern or split contract
```javascript
// Use libraries to reduce contract size
const library = await Library.deploy();
await library.deployed();

const ContractFactory = await ethers.getContractFactory("MyContract", {
  libraries: {
    MyLibrary: library.address
  }
});
```

### ❌ "Network Connection Issues"
**Solution**: Add retry mechanism and alternative RPCs
```javascript
async function deployWithRetry(factory, args, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const contract = await factory.deploy(...args);
      return contract;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      console.log(`Retry ${i + 1}/${maxRetries}...`);
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
}
```

This comprehensive guide provides deployment patterns for various use cases. Choose the appropriate pattern based on your project requirements, and always follow security best practices when deploying to production networks.