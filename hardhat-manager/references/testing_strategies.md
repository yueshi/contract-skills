# Hardhat Testing Strategies Guide

This comprehensive guide covers testing strategies and best practices for smart contracts using Hardhat. Includes unit testing, integration testing, security testing, and performance testing approaches.

## Table of Contents

1. [Testing Framework Setup](#testing-framework-setup)
2. [Unit Testing Strategies](#unit-testing-strategies)
3. [Integration Testing](#integration-testing)
4. [Security Testing](#security-testing)
5. [Gas Optimization Testing](#gas-optimization-testing)
6. [Property-Based Testing](#property-based-testing)
7. [Test Coverage](#test-coverage)
8. [Testing Patterns](#testing-patterns)
9. [Continuous Integration](#continuous-integration)
10. [Test Data Management](#test-data-management)

## Testing Framework Setup

### Hardhat Testing Environment

#### Basic Setup
```javascript
// hardhat.config.js
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
      accounts: {
        count: 100,
        accountsBalance: "10000000000000000000000" // 10000 ETH per account
      }
    }
  },
  mocha: {
    timeout: 60000 // Increase timeout for complex tests
  }
};
```

#### Test Dependencies
```json
{
  "devDependencies": {
    "@nomicfoundation/hardhat-chai-matchers": "^2.0.0",
    "@nomicfoundation/hardhat-ethers": "^3.0.0",
    "@nomicfoundation/hardhat-network-helpers": "^1.0.0",
    "@nomicfoundation/hardhat-toolbox": "^3.0.0",
    "@nomicfoundation/hardhat-verify": "^1.0.0",
    "chai": "^4.2.0",
    "ethers": "^6.0.0",
    "hardhat-gas-reporter": "^1.0.8",
    "solidity-coverage": "^0.8.0"
  }
}
```

#### Test Helper Setup
```javascript
// test/helpers.js
const { ethers } = require("hardhat");
const { expect } = require("chai");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

async function getSigners() {
  const [owner, user1, user2, user3, ...others] = await ethers.getSigners();
  return { owner, user1, user2, user3, others };
}

async function deployContract(contractName, ...args) {
  const ContractFactory = await ethers.getContractFactory(contractName);
  const contract = await ContractFactory.deploy(...args);
  await contract.deployed();
  return contract;
}

async function mineBlocks(count) {
  for (let i = 0; i < count; i++) {
    await ethers.provider.send("evm_mine", []);
  }
}

async function increaseTime(seconds) {
  await time.increase(seconds);
}

async function getTimestamp() {
  const block = await ethers.provider.getBlock("latest");
  return block.timestamp;
}

module.exports = {
  getSigners,
  deployContract,
  mineBlocks,
  increaseTime,
  getTimestamp
};
```

## Unit Testing Strategies

### Basic Unit Test Structure

#### Simple Token Test
```javascript
// test/MyToken.test.js
const { expect } = require("chai");
const { ethers } = require("hardhat");
const { deployContract, getSigners } = require("./helpers");

describe("MyToken", function () {
  let token;
  let owner, user1, user2;

  beforeEach(async function () {
    const signers = await getSigners();
    owner = signers.owner;
    user1 = signers.user1;
    user2 = signers.user2;

    token = await deployContract("MyToken", "My Token", "MTK", 18, ethers.utils.parseEther("1000000"));
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await token.owner()).to.equal(owner.address);
    });

    it("Should assign the total supply to the owner", async function () {
      const ownerBalance = await token.balanceOf(owner.address);
      expect(await token.totalSupply()).to.equal(ownerBalance);
    });

    it("Should have correct name, symbol, and decimals", async function () {
      expect(await token.name()).to.equal("My Token");
      expect(await token.symbol()).to.equal("MTK");
      expect(await token.decimals()).to.equal(18);
    });
  });

  describe("Transactions", function () {
    it("Should transfer tokens between accounts", async function () {
      const transferAmount = ethers.utils.parseEther("50");

      // Transfer 50 tokens from owner to user1
      await expect(token.transfer(user1.address, transferAmount))
        .to.changeTokenBalance(token, user1, transferAmount);

      // Check balances
      expect(await token.balanceOf(user1.address)).to.equal(transferAmount);
    });

    it("Should fail if sender doesn't have enough tokens", async function () {
      const initialOwnerBalance = await token.balanceOf(owner.address);
      const transferAmount = initialOwnerBalance.add(1);

      // Try to send 1 token more than owner has
      await expect(
        token.connect(user1).transfer(owner.address, transferAmount)
      ).to.be.revertedWith("ERC20: transfer amount exceeds balance");
    });

    it("Should update balances after transfers", async function () {
      const initialOwnerBalance = await token.balanceOf(owner.address);
      const transferAmount = ethers.utils.parseEther("100");

      // Transfer to user1
      await token.transfer(user1.address, transferAmount);

      // Check balances
      expect(await token.balanceOf(owner.address)).to.equal(
        initialOwnerBalance.sub(transferAmount)
      );
      expect(await token.balanceOf(user1.address)).to.equal(transferAmount);
    });
  });

  describe("Allowances", function () {
    it("Should approve and use allowances", async function () {
      const allowanceAmount = ethers.utils.parseEther("1000");

      // Approve user1 to spend owner's tokens
      await token.approve(user1.address, allowanceAmount);
      expect(await token.allowance(owner.address, user1.address)).to.equal(allowanceAmount);

      // User1 transfers owner's tokens to user2
      const transferAmount = ethers.utils.parseEther("500");
      await expect(
        token.connect(user1).transferFrom(owner.address, user2.address, transferAmount)
      ).to.changeTokenBalance(token, user2, transferAmount);

      // Check updated allowance
      expect(await token.allowance(owner.address, user1.address)).to.equal(
        allowanceAmount.sub(transferAmount)
      );
    });
  });
});
```

#### Edge Case Testing
```javascript
describe("Edge Cases", function () {
  it("Should handle zero address transfers", async function () {
    await expect(
      token.transfer(ethers.constants.AddressZero, ethers.utils.parseEther("100"))
    ).to.be.revertedWith("ERC20: transfer to the zero address");
  });

  it("Should handle zero amount transfers", async function () {
    await expect(token.transfer(user1.address, 0))
      .to.emit(token, "Transfer")
      .withArgs(owner.address, user1.address, 0);
  });

  it("Should handle maximum uint256 values", async function () {
    const maxUint256 = ethers.constants.MaxUint256;

    // Test with maximum values where applicable
    await token.approve(user1.address, maxUint256);
    expect(await token.allowance(owner.address, user1.address)).to.equal(maxUint256);
  });
});
```

## Integration Testing

### Multi-Contract Integration Tests

#### DeFi Protocol Integration Test
```javascript
// test/integration/DefiProtocol.test.js
const { expect } = require("chai");
const { ethers } = require("hardhat");
const { deployContract, getSigners, increaseTime } = require("../helpers");

describe("DeFi Protocol Integration", function () {
  let token, staking, rewards, governance;
  let owner, user1, user2, user3;

  beforeEach(async function () {
    const signers = await getSigners();
    owner = signers.owner;
    user1 = signers.user1;
    user2 = signers.user2;
    user3 = signers.user3;

    // Deploy protocol contracts
    token = await deployContract("GovernanceToken", "Governance Token", "GOV", 18);
    staking = await deployContract("StakingPool", token.address);
    rewards = await deployContract("RewardsDistributor", token.address, staking.address);
    governance = await deployContract("Governance", token.address);

    // Setup protocol
    await token.transfer(staking.address, ethers.utils.parseEther("100000"));
    await staking.setRewardsDistributor(rewards.address);
    await token.transfer(user1.address, ethers.utils.parseEther("1000"));
    await token.transfer(user2.address, ethers.utils.parseEther("1000"));
  });

  describe("Complete Staking Flow", function () {
    it("Should handle complete staking and rewards flow", async function () {
      const stakeAmount = ethers.utils.parseEther("100");

      // User1 stakes tokens
      await token.connect(user1).approve(staking.address, stakeAmount);
      await expect(staking.connect(user1).stake(stakeAmount))
        .to.emit(staking, "Staked")
        .withArgs(user1.address, stakeAmount);

      // Advance time to earn rewards
      await increaseTime(86400); // 1 day

      // User1 claims rewards
      const initialBalance = await token.balanceOf(user1.address);
      await staking.connect(user1).claimRewards();
      const finalBalance = await token.balanceOf(user1.address);

      expect(finalBalance).to.be.gt(initialBalance);

      // User1 unstakes
      await staking.connect(user1).unstake(stakeAmount);
      expect(await token.balanceOf(user1.address)).to.be.gt(
        initialBalance.add(stakeAmount)
      );
    });
  });

  describe("Governance Integration", function () {
    it("Should handle governance proposal flow", async function () {
      const proposalThreshold = ethers.utils.parseEther("100");

      // User1 and user2 delegate voting power
      await token.connect(user1).delegate(user1.address);
      await token.connect(user2).delegate(user2.address);

      // Create proposal
      const proposalCalldata = rewards.interface.encodeFunctionData("setRewardRate", [100]);
      await expect(governance.connect(user1).propose(
        [rewards.address],
        [0],
        [proposalCalldata],
        "Update reward rate to 100"
      )).to.emit(governance, "ProposalCreated");

      // Vote on proposal
      const proposalId = 1; // Assuming first proposal
      await governance.connect(user1).vote(proposalId, 1); // Vote for

      // Wait for voting period
      await increaseTime(604800); // 1 week

      // Execute proposal
      await governance.execute(
        [rewards.address],
        [0],
        [proposalCalldata]
      );

      // Verify proposal executed
      expect(await rewards.rewardRate()).to.equal(100);
    });
  });
});
```

### Cross-Chain Integration Testing
```javascript
// test/integration/CrossChain.test.js
describe("Cross-Chain Integration", function () {
  let bridge, token, wrapper;
  let owner, user1;

  beforeEach(async function () {
    // Deploy bridge system
    bridge = await deployContract("Bridge");
    token = await deployContract("MyToken", "Token", "TKN", 18);
    wrapper = await deployContract("WrappedToken", "Wrapped Token", "WTKN", 18, bridge.address);

    // Initialize bridge
    await bridge.addSupportedToken(token.address, wrapper.address);
    await token.mint(owner.address, ethers.utils.parseEther("1000"));
  });

  it("Should handle cross-chain transfer", async function () {
    const transferAmount = ethers.utils.parseEther("100");

    // Lock tokens on source chain
    await token.approve(bridge.address, transferAmount);
    await expect(bridge.lockTokens(token.address, transferAmount, "chainB"))
      .to.emit(bridge, "TokensLocked")
      .withArgs(token.address, transferAmount, "chainB");

    // Simulate mint on destination chain (in real scenario, this would be done by validators)
    await wrapper.mint(user1.address, transferAmount);
    expect(await wrapper.balanceOf(user1.address)).to.equal(transferAmount);
  });
});
```

## Security Testing

### Reentrancy Testing
```javascript
// test/security/Reentrancy.test.js
describe("Reentrancy Protection", function () {
  let vault, attacker;
  let owner, user1;

  beforeEach(async function () {
    const signers = await getSigners();
    owner = signers.owner;
    user1 = signers.user1;

    vault = await deployContract("SecureVault");
    attacker = await deployContract("ReentrancyAttacker", vault.address);

    // Fund vault and attacker
    await owner.sendTransaction({
      to: vault.address,
      value: ethers.utils.parseEther("10")
    });

    await attacker.fund({
      value: ethers.utils.parseEther("1")
    });
  });

  it("Should prevent reentrancy attacks", async function () {
    const attackAmount = ethers.utils.parseEther("1");

    // Attempt reentrancy attack
    await expect(attacker.attack(attackAmount))
      .to.be.revertedWith("ReentrancyGuard: reentrant call");

    // Vault balance should remain unchanged
    expect(await ethers.provider.getBalance(vault.address)).to.equal(
      ethers.utils.parseEther("10")
    );
  });
});

// Mock Attacker Contract
// contracts/ReentrancyAttacker.sol
contract ReentrancyAttacker {
    IVault public vault;
    bool public attacking;

    constructor(address _vault) {
        vault = IVault(_vault);
    }

    function fund() external payable {
        require(msg.value > 0, "Must send ETH");
    }

    function attack(uint256 amount) external {
        attacking = true;
        vault.withdraw(amount);
        attacking = false;
    }

    receive() external payable {
        if (attacking && address(vault).balance > 0) {
            vault.withdraw(1 ether);
        }
    }
}
```

### Access Control Testing
```javascript
// test/security/AccessControl.test.js
describe("Access Control", function () {
  let contract;
  let owner, admin, user1, user2;

  beforeEach(async function () {
    const signers = await getSigners();
    owner = signers.owner;
    admin = signers.user1;
    user1 = signers.user2;
    user2 = signers.user3;

    contract = await deployContract("AccessControlContract");
    await contract.grantAdminRole(admin.address);
  });

  it("Should only allow admin to call admin functions", async function () {
    await expect(contract.connect(admin).setAdminParameter(100))
      .to.not.be.reverted;

    await expect(contract.connect(user1).setAdminParameter(100))
      .to.be.revertedWith("AccessControl: caller is not admin");
  });

  it("Should handle role transfers correctly", async function () {
    await contract.connect(admin).transferAdminRole(user1.address);

    await expect(contract.connect(user1).setAdminParameter(100))
      .to.not.be.reverted;

    await expect(contract.connect(admin).setAdminParameter(100))
      .to.be.revertedWith("AccessControl: caller is not admin");
  });
});
```

### Integer Overflow Testing
```javascript
// test/security/IntegerOverflow.test.js
describe("Integer Overflow Protection", function () {
  let contract;

  beforeEach(async function () {
    contract = await deployContract("MathContract");
  });

  it("Should prevent uint256 overflow", async function () {
    const maxUint256 = ethers.constants.MaxUint256;

    await expect(contract.add(maxUint256, 1))
      .to.be.revertedWith("SafeMath: addition overflow");

    await expect(contract.multiply(maxUint256.div(2), 3))
      .to.be.revertedWith("SafeMath: multiplication overflow");
  });

  it("Should prevent uint256 underflow", async function () {
    await expect(contract.subtract(1, 2))
      .to.be.revertedWith("SafeMath: subtraction underflow");
  });
});
```

## Gas Optimization Testing

### Gas Profiling
```javascript
// test/gas/GasProfiling.test.js
describe("Gas Optimization", function () {
  let contract;

  beforeEach(async function () {
    contract = await deployContract("GasOptimizedContract");
  });

  it("Should report gas usage for functions", async function () {
    // Test different functions and report gas usage
    const tx1 = await contract.simpleFunction();
    console.log("simpleFunction gas used:", tx1.gasLimit.toString());

    const tx2 = await contract.complexFunction(100);
    console.log("complexFunction gas used:", tx2.gasLimit.toString());

    const tx3 = await contract.loopFunction(50);
    console.log("loopFunction(50) gas used:", tx3.gasLimit.toString());

    // Assertions for gas limits
    expect(tx1.gasLimit).to.be.lt(50000);
    expect(tx2.gasLimit).to.be.lt(100000);
    expect(tx3.gasLimit).to.be.lt(200000);
  });

  it("Should optimize storage operations", async function () {
    const testValue = ethers.utils.formatBytes32String("test");

    // Test SSTORE operations
    const tx1 = await contract.writeToStorage(testValue);
    console.log("Write to storage gas used:", tx1.gasLimit.toString());

    // Test SLOAD operations
    const tx2 = await contract.readFromStorage();
    console.log("Read from storage gas used:", tx2.gasLimit.toString());

    // Test batch operations vs individual operations
    const tx3 = await contract.batchWrite([testValue, testValue, testValue]);
    console.log("Batch write gas used:", tx3.gasLimit.toString());
  });
});
```

### Gas Comparison Testing
```javascript
describe("Gas Comparison", function () {
  let optimizedContract, unoptimizedContract;

  beforeEach(async function () {
    optimizedContract = await deployContract("OptimizedContract");
    unoptimizedContract = await deployContract("UnoptimizedContract");
  });

  it("Should show gas savings from optimizations", async function () {
    const testData = ethers.utils.formatBytes32String("test");

    const unoptimizedTx = await unoptimizedContract.processData(testData);
    const optimizedTx = await optimizedContract.processData(testData);

    const gasSavings = unoptimizedTx.gasLimit.sub(optimizedTx.gasLimit);
    const savingsPercentage = gasSavings.mul(100).div(unoptimizedTx.gasLimit);

    console.log("Unoptimized gas:", unoptimizedTx.gasLimit.toString());
    console.log("Optimized gas:", optimizedTx.gasLimit.toString());
    console.log("Gas savings:", gasSavings.toString());
    console.log("Savings percentage:", savingsPercentage.toString() + "%");

    expect(gasSavings).to.be.gt(0);
    expect(savingsPercentage).to.be.gt(10); // At least 10% savings
  });
});
```

## Property-Based Testing

### Using Echidna for Property-Based Testing
```javascript
// test/properties/TokenProperties.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "hardhat/console.sol";
import "../contracts/MyToken.sol";

contract TokenProperties {
    MyToken token;
    address owner;
    address user1;
    address user2;

    constructor() {
        owner = address(this);
        token = new MyToken("Test Token", "TEST", 18, 1000000 * 10**18);
        user1 = address(0x1);
        user2 = address(0x2);
    }

    // Property: Total supply should never increase
    function echidna_total_supply_never_increases() public view returns (bool) {
        return token.totalSupply() <= 1000000 * 10**18;
    }

    // Property: Balances should never be negative
    function echidna_balances_never_negative() public view returns (bool) {
        return token.balanceOf(owner) >= 0 &&
               token.balanceOf(user1) >= 0 &&
               token.balanceOf(user2) >= 0;
    }

    // Property: Allowances should never exceed approved amount
    function echidna_allowance_exceeds_approved() public view returns (bool) {
        return token.allowance(owner, user1) <= 1000000 * 10**18;
    }

    // Fuzzing function
    function fuzz_transfer(uint256 amount) public {
        amount = amount % 1000000 * 10**18; // Limit to reasonable range
        token.transfer(user1, amount);
    }

    function fuzz_approve_and_transferFrom(uint256 amount) public {
        amount = amount % 1000000 * 10**18;
        token.approve(user1, amount);
        token.transferFrom(owner, user2, amount);
    }
}
```

### Property-Based Testing with Hardhat
```javascript
// test/properties/TokenProperties.test.js
describe("Token Properties", function () {
  let token;
  let owner, user1, user2;

  beforeEach(async function () {
    const signers = await getSigners();
    owner = signers.owner;
    user1 = signers.user1;
    user2 = signers.user2;

    token = await deployContract("MyToken", "Test Token", "TEST", 18, ethers.utils.parseEther("1000000"));
  });

  describe("Property: Total Supply Invariant", function () {
    it("Should maintain total supply invariance", async function () {
      const initialSupply = await token.totalSupply();

      // Perform random transfers
      for (let i = 0; i < 100; i++) {
        const amount = Math.floor(Math.random() * 1000);
        const from = Math.random() > 0.5 ? owner : user1;
        const to = Math.random() > 0.5 ? user1 : user2;

        try {
          await token.connect(from).transfer(to.address, amount);
        } catch (error) {
          // Expected for invalid transfers
        }
      }

      const finalSupply = await token.totalSupply();
      expect(finalSupply).to.equal(initialSupply);
    });
  });

  describe("Property: Balance Non-Negative", function () {
    it("Should never have negative balances", async function () {
      // Test various operations
      for (let i = 0; i < 50; i++) {
        const amount = Math.floor(Math.random() * 100);

        try {
          await token.transfer(user1.address, amount);
          await token.transfer(user2.address, amount);
          await token.connect(user1).transfer(user2.address, amount);
        } catch (error) {
          // Expected for invalid transfers
        }
      }

      const balances = [
        await token.balanceOf(owner.address),
        await token.balanceOf(user1.address),
        await token.balanceOf(user2.address)
      ];

      balances.forEach(balance => {
        expect(balance).to.be.gte(0);
      });
    });
  });
});
```

## Test Coverage

### Setting Up Coverage
```javascript
// hardhat.config.js
module.exports = {
  solidity: "0.8.19",
  coverage: {
    providerOptions: {
      istanbulFolder: "coverage"
    }
  }
};
```

### Running Coverage Tests
```bash
# Generate coverage report
npx hardhat coverage

# Generate coverage with specific test files
npx hardhat coverage --testfiles "test/**/*.test.js"

# Exclude contracts from coverage
npx hardhat coverage --solcoverjs ./.solcover.js
```

### Solcover Configuration
```javascript
// .solcover.js
module.exports = {
  skipFiles: [
    "mock/",
    "test/",
    "interfaces/"
  ],
  providerOptions: {
    network_id: 999,
    gas: 0xfffffffffff,
    gasPrice: 0x01
  },
  mocha: {
    grep: "^(?!.*\\[skip coverage\\]).*",
    timeout: 60000
  }
};
```

### Coverage Thresholds
```javascript
// package.json scripts
{
  "scripts": {
    "coverage": "npx hardhat coverage",
    "coverage:threshold": "npx hardhat coverage && npx istanbul check-coverage --statements 95 --branches 90 --functions 100 --lines 95"
  }
}
```

## Testing Patterns

### Arrange-Act-Assert Pattern
```javascript
describe("Arrange-Act-Assert Pattern", function () {
  it("Should follow AAA pattern", async function () {
    // Arrange
    const transferAmount = ethers.utils.parseEther("100");
    await token.transfer(user1.address, transferAmount);
    const initialBalance = await token.balanceOf(user1.address);

    // Act
    await token.connect(user1).transfer(user2.address, transferAmount.div(2));

    // Assert
    const finalBalance = await token.balanceOf(user1.address);
    expect(finalBalance).to.equal(initialBalance.sub(transferAmount.div(2)));
  });
});
```

### Test Data Builder Pattern
```javascript
// test/builders/TransactionBuilder.js
class TransactionBuilder {
  constructor() {
    this.from = null;
    this.to = null;
    this.value = ethers.utils.parseEther("1");
    this.data = "0x";
  }

  withFrom(address) {
    this.from = address;
    return this;
  }

  withTo(address) {
    this.to = address;
    return this;
  }

  withValue(ethAmount) {
    this.value = ethers.utils.parseEther(ethAmount.toString());
    return this;
  }

  withData(callData) {
    this.data = callData;
    return this;
  }

  build() {
    return {
      from: this.from,
      to: this.to,
      value: this.value,
      data: this.data
    };
  }
}

module.exports = TransactionBuilder;

// Usage in tests
const TransactionBuilder = require("../builders/TransactionBuilder");

const transaction = new TransactionBuilder()
  .withFrom(user1.address)
  .withTo(contract.address)
  .withValue(10)
  .withData(contract.interface.encodeFunctionData("setValue", [100]))
  .build();
```

### Custom Chai Matchers
```javascript
// test/matchers/index.js
const { expect } = require("chai");
const { ethers } = require("hardhat");

expect.extend({
  async toChangeTokenBalance(token, account, change) {
    const balanceBefore = await token.balanceOf(account);
    await this.promise;
    const balanceAfter = await token.balanceOf(account);
    const actualChange = balanceAfter.sub(balanceBefore);

    if (!actualChange.eq(change)) {
      throw new Error(
        `Expected token balance to change by ${ethers.utils.formatEther(change)}, ` +
        `but it changed by ${ethers.utils.formatEther(actualChange)}`
      );
    }

    return this;
  },

  async toEmitEvent(contract, eventName, expectedArgs = null) {
    const receipt = await this.promise.wait();
    const events = receipt.events?.filter(e => e.event === eventName) || [];

    if (events.length === 0) {
      throw new Error(`Expected event ${eventName} but none was emitted`);
    }

    if (expectedArgs) {
      const event = events[0];
      for (const [key, expectedValue] of Object.entries(expectedArgs)) {
        const actualValue = event.args[key];
        if (!actualValue.eq(expectedValue)) {
          throw new Error(
            `Expected ${key} to be ${expectedValue}, but got ${actualValue}`
          );
        }
      }
    }

    return this;
  }
});

// Usage in tests
await expect(token.transfer(user1.address, ethers.utils.parseEther("100")))
  .to.changeTokenBalance(token, user1, ethers.utils.parseEther("100"));

await expect(contract.setValue(100))
  .to.emitEvent(contract, "ValueChanged", { oldValue: 0, newValue: 100 });
```

## Continuous Integration

### GitHub Actions Configuration
```yaml
# .github/workflows/test.yml
name: Smart Contract Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        node-version: [16.x, 18.x]

    steps:
    - uses: actions/checkout@v3

    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Run tests
      run: npm test

    - name: Run coverage
      run: npm run coverage

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage/lcov.info

    - name: Run Slither analysis
      run: |
        pip3 install slither-analyzer
        slither . --filter-paths "node_modules/" --json slither-results.json

    - name: Upload Slither results
      uses: actions/upload-artifact@v3
      with:
        name: slither-results
        path: slither-results.json
```

### Docker Testing Environment
```dockerfile
# Dockerfile.test
FROM node:18-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    gcc \
    musl-dev \
    linux-headers

# Install Python dependencies for security tools
RUN pip3 install slither-analyzer

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm ci

# Copy source code
COPY . .

# Run tests
CMD ["npm", "test"]
```

### Test Scripts
```json
{
  "scripts": {
    "test": "npx hardhat test",
    "test:unit": "npx hardhat test test/unit/",
    "test:integration": "npx hardhat test test/integration/",
    "test:security": "npx hardhat test test/security/",
    "test:gas": "REPORT_GAS=true npx hardhat test test/gas/",
    "test:coverage": "npx hardhat coverage",
    "test:ci": "npm run test:unit && npm run test:integration && npm run test:security",
    "lint": "solhint 'contracts/**/*.sol'",
    "lint:fix": "solhint 'contracts/**/*.sol' --fix",
    "security:slither": "slither . --filter-paths 'node_modules/'",
    "security:mythril": "myth analyze contracts/",
    "precommit": "npm run lint && npm run test:unit"
  }
}
```

## Test Data Management

### Test Fixtures
```javascript
// test/fixtures/index.js
const { ethers } = require("hardhat");

const testFixtures = {
  users: {
    owner: "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    user1: "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    user2: "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
    user3: "0x90F79bf6EB2c4f870365E785982E1f101E93b906"
  },

  tokens: {
    largeAmount: ethers.utils.parseEther("1000000"),
    mediumAmount: ethers.utils.parseEther("10000"),
    smallAmount: ethers.utils.parseEther("100"),
    tinyAmount: ethers.utils.parseEther("1")
  },

  time: {
    oneDay: 86400,
    oneWeek: 604800,
    oneMonth: 2592000,
    oneYear: 31536000
  },

  contracts: {
    uniswapV2Router: "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    weth: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
  }
};

module.exports = testFixtures;
```

### Mock Contracts
```javascript
// test/mocks/MockERC20.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockERC20 is ERC20 {
    uint8 private _decimals;

    constructor(
        string memory name,
        string memory symbol,
        uint8 decimalsValue,
        uint256 initialSupply
    ) ERC20(name, symbol) {
        _decimals = decimalsValue;
        _mint(msg.sender, initialSupply);
    }

    function decimals() public view virtual override returns (uint8) {
        return _decimals;
    }

    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }

    function burn(address from, uint256 amount) external {
        _burn(from, amount);
    }
}
```

### Test Utilities
```javascript
// test/utils/Deployments.js
class DeploymentManager {
  constructor() {
    this.deployments = new Map();
  }

  async deployContract(contractName, ...args) {
    const ContractFactory = await ethers.getContractFactory(contractName);
    const contract = await ContractFactory.deploy(...args);
    await contract.deployed();

    this.deployments.set(contractName, contract);
    return contract;
  }

  getContract(contractName) {
    return this.deployments.get(contractName);
  }

  async redeployContract(contractName, ...args) {
    if (this.deployments.has(contractName)) {
      this.deployments.delete(contractName);
    }
    return this.deployContract(contractName, ...args);
  }

  getAllDeployments() {
    return Object.fromEntries(this.deployments);
  }
}

module.exports = DeploymentManager;
```

This comprehensive testing guide provides strategies for all aspects of smart contract testing. Implement these patterns and techniques to ensure your contracts are thoroughly tested and secure before deployment.