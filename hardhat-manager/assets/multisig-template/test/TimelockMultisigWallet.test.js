const { expect } = require("chai");
const { ethers } = require("hardhat");
const { increaseTime } = require("./helpers/time");

describe("TimelockMultisigWallet", function () {
  let timelockMultisig;
  let owners;
  let requiredConfirmations;
  let timelockAdmins;

  beforeEach(async function () {
    // Get signers
    const signers = await ethers.getSigners();
    owners = signers.slice(0, 3);
    timelockAdmins = signers.slice(0, 2);
    requiredConfirmations = 2;

    // Deploy timelock multisig wallet
    const ownerAddresses = await Promise.all(owners.map(o => o.getAddress()));
    const timelockAdminAddresses = await Promise.all(timelockAdmins.map(a => a.getAddress()));

    const TimelockMultisigWallet = await ethers.getContractFactory("TimelockMultisigWallet");
    timelockMultisig = await TimelockMultisigWallet.deploy(
      ownerAddresses,
      requiredConfirmations,
      timelockAdminAddresses
    );
    await timelockMultisig.deployed();
  });

  describe("Deployment", function () {
    it("Should deploy with correct configuration", async function () {
      expect(await timelockMultisig.ownerCount()).to.equal(owners.length);
      expect(await timelockMultisig.requiredConfirmations()).to.equal(requiredConfirmations);

      for (let i = 0; i < owners.length; i++) {
        expect(await timelockMultisig.isOwner(owners[i].address)).to.be.true;
      }
    });

    it("Should set timelock administrators", async function () {
      for (let i = 0; i < timelockAdmins.length; i++) {
        expect(await timelockMultisig.isTimelockAdmin(timelockAdmins[i].address)).to.be.true;
      }
    });
  });

  describe("Tier Configuration", function () {
    it("Should return correct tier info", async function () {
      const tierInfo = await timelockMultisig.getTierInfo();

      expect(tierInfo.tier1Threshold).to.equal(ethers.utils.parseEther("10"));
      expect(tierInfo.tier2Threshold).to.equal(ethers.utils.parseEther("100"));
      expect(tierInfo.tier1Confirmations).to.equal(2);
      expect(tierInfo.tier2Confirmations).to.equal(3);
      expect(tierInfo.tier3Confirmations).to.equal(4);
    });

    it("Should determine correct confirmation requirements by value", async function () {
      // Tier 1: < 10 ETH -> 2 confirmations
      expect(await timelockMultisig.getRequiredConfirmations(ethers.utils.parseEther("5")))
        .to.equal(2);

      // Tier 2: 10-100 ETH -> 3 confirmations
      expect(await timelockMultisig.getRequiredConfirmations(ethers.utils.parseEther("50")))
        .to.equal(3);

      // Tier 3: >= 100 ETH -> 4 confirmations
      expect(await timelockMultisig.getRequiredConfirmations(ethers.utils.parseEther("200")))
        .to.equal(4);
    });
  });

  describe("Delay Configuration", function () {
    it("Should return delay info", async function () {
      const delayInfo = await timelockMultisig.getDelayInfo();

      expect(delayInfo.minimumDelay).to.equal(24 * 60 * 60); // 24 hours
      expect(delayInfo.maximumDelay).to.equal(30 * 24 * 60 * 60); // 30 days
      expect(delayInfo.gracePeriod).to.equal(7 * 24 * 60 * 60); // 7 days
      expect(delayInfo.emergencyDelay).to.equal(2 * 60 * 60); // 2 hours
      expect(delayInfo.emergencyGracePeriod).to.equal(24 * 60 * 60); // 24 hours
    });
  });

  describe("Timelock Transactions", function () {
    let txId;
    const value = ethers.utils.parseEther("5");
    const recipient = ethers.Wallet.createRandom().address;
    const delay = 24 * 60 * 60; // 24 hours

    beforeEach(async function () {
      // Queue timelock transaction
      txId = await timelockMultisig
        .connect(timelockAdmins[0])
        .queueTimelockTransaction(recipient, value, "0x", delay);
    });

    it("Should queue timelock transaction correctly", async function () {
      const tx = await timelockMultisig.getTimelockTransaction(txId);

      expect(tx.to).to.equal(recipient);
      expect(tx.value).to.equal(value);
      expect(tx.executed).to.be.false;
      expect(tx.cancelled).to.be.false;
      expect(tx.confirmations).to.equal(0);
      expect(tx.eta).to.equal((await ethers.provider.getBlock("latest")).timestamp + delay);
    });

    it("Should not queue with invalid delay", async function () {
      const minDelay = 24 * 60 * 60;
      await expect(
        timelockMultisig
          .connect(timelockAdmins[0])
          .queueTimelockTransaction(recipient, value, "0x", minDelay - 1)
      ).to.be.revertedWith("Delay too short");

      const maxDelay = 30 * 24 * 60 * 60;
      await expect(
        timelockMultisig
          .connect(timelockAdmins[0])
          .queueTimelockTransaction(recipient, value, "0x", maxDelay + 1)
      ).to.be.revertedWith("Delay too long");
    });

    it("Should confirm timelock transaction", async function () {
      await timelockMultisig.connect(owners[0]).confirmTimelockTransaction(txId);

      const tx = await timelockMultisig.getTimelockTransaction(txId);
      expect(tx.confirmations).to.equal(1);

      const confirmations = await timelockMultisig.timelockConfirmations(txId);
      expect(confirmations).to.contain(owners[0].address);
    });

    it("Should execute timelock transaction after delay", async function () {
      // Confirm transaction
      await timelockMultisig.connect(owners[0]).confirmTimelockTransaction(txId);
      await timelockMultisig.connect(owners[1]).confirmTimelockTransaction(txId);

      // Increase time past delay
      await increaseTime(delay + 1);

      // Fund the contract
      await owners[0].sendTransaction({
        to: timelockMultisig.address,
        value: ethers.utils.parseEther("10")
      });

      // Execute transaction
      await timelockMultisig
        .connect(timelockAdmins[0])
        .executeTimelockTransaction(txId);

      // Check execution
      const tx = await timelockMultisig.getTimelockTransaction(txId);
      expect(tx.executed).to.be.true;
    });

    it("Should not execute before delay", async function () {
      await timelockMultisig.connect(owners[0]).confirmTimelockTransaction(txId);
      await timelockMultisig.connect(owners[1]).confirmTimelockTransaction(txId);

      await expect(
        timelockMultisig
          .connect(timelockAdmins[0])
          .executeTimelockTransaction(txId)
      ).to.be.revertedWith("Transaction not yet ready");
    });

    it("Should not execute after grace period", async function () {
      await timelockMultisig.connect(owners[0]).confirmTimelockTransaction(txId);
      await timelockMultisig.connect(owners[1]).confirmTimelockTransaction(txId);

      // Increase time past delay and grace period
      const gracePeriod = 7 * 24 * 60 * 60;
      await increaseTime(delay + gracePeriod + 1);

      await expect(
        timelockMultisig
          .connect(timelockAdmins[0])
          .executeTimelockTransaction(txId)
      ).to.be.revertedWith("Transaction expired");
    });

    it("Should not execute without enough confirmations", async function () {
      await timelockMultisig.connect(owners[0]).confirmTimelockTransaction(txId);

      await increaseTime(delay + 1);

      await expect(
        timelockMultisig
          .connect(timelockAdmins[0])
          .executeTimelockTransaction(txId)
      ).to.be.revertedWith("Not enough confirmations");
    });

    it("Should cancel timelock transaction", async function () {
      await timelockMultisig
        .connect(timelockAdmins[0])
        .cancelTimelockTransaction(txId);

      const tx = await timelockMultisig.getTimelockTransaction(txId);
      expect(tx.cancelled).to.be.true;
    });

    it("Should not execute cancelled transaction", async function () {
      await timelockMultisig.connect(owners[0]).confirmTimelockTransaction(txId);
      await timelockMultisig.connect(owners[1]).confirmTimelockTransaction(txId);

      await timelockMultisig
        .connect(timelockAdmins[0])
        .cancelTimelockTransaction(txId);

      await increaseTime(delay + 1);

      await expect(
        timelockMultisig
          .connect(timelockAdmins[0])
          .executeTimelockTransaction(txId)
      ).to.be.revertedWith("Cancelled");
    });

    it("Should check if transaction can be executed", async function () {
      // Not ready yet
      expect(await timelockMultisig.canExecuteTimelock(txId)).to.be.false;

      // Confirm but not enough
      await timelockMultisig.connect(owners[0]).confirmTimelockTransaction(txId);
      expect(await timelockMultisig.canExecuteTimelock(txId)).to.be.false;

      // Enough confirmations but not ready
      await timelockMultisig.connect(owners[1]).confirmTimelockTransaction(txId);
      expect(await timelockMultisig.canExecuteTimelock(txId)).to.be.false;

      // Ready to execute
      await increaseTime(delay + 1);
      expect(await timelockMultisig.canExecuteTimelock(txId)).to.be.true;
    });
  });

  describe("Emergency Transactions", function () {
    let emgTxId;
    const value = ethers.utils.parseEther("5");
    const recipient = ethers.Wallet.createRandom().address;

    beforeEach(async function () {
      // Queue emergency transaction
      await timelockMultisig
        .connect(timelockAdmins[0])
        .enableSafeMode();

      emgTxId = await timelockMultisig
        .connect(timelockAdmins[0])
        .queueEmergencyTransaction(recipient, value, "0x");
    });

    it("Should queue emergency transaction", async function () {
      // Emergency transactions execute after EMERGENCY_DELAY (2 hours)
      const tx = await timelockMultisig.getEmergencyTransaction(emgTxId);

      expect(tx.to).to.equal(recipient);
      expect(tx.value).to.equal(value);
      expect(tx.executed).to.be.false;
      expect(tx.cancelled).to.be.false;
      expect(tx.proposer).to.equal(timelockAdmins[0].address);
    });

    it("Should execute emergency transaction after delay", async function () {
      // Increase time past emergency delay
      const emergencyDelay = 2 * 60 * 60;
      await increaseTime(emergencyDelay + 1);

      // Fund the contract
      await owners[0].sendTransaction({
        to: timelockMultisig.address,
        value: ethers.utils.parseEther("10")
      });

      // Execute emergency transaction
      await timelockMultisig
        .connect(owners[0])
        .executeEmergencyTransaction(emgTxId);

      // Check execution
      const tx = await timelockMultisig.getEmergencyTransaction(emgTxId);
      expect(tx.executed).to.be.true;
    });

    it("Should not execute emergency transaction too early", async function () {
      await expect(
        timelockMultisig
          .connect(owners[0])
          .executeEmergencyTransaction(emgTxId)
      ).to.be.revertedWith("Too early");
    });

    it("Should not execute emergency transaction after grace period", async function () {
      const emergencyDelay = 2 * 60 * 60;
      const emergencyGracePeriod = 24 * 60 * 60;
      await increaseTime(emergencyDelay + emergencyGracePeriod + 1);

      await expect(
        timelockMultisig
          .connect(owners[0])
          .executeEmergencyTransaction(emgTxId)
      ).to.be.revertedWith("Expired");
    });

    it("Should cancel emergency transaction", async function () {
      await timelockMultisig
        .connect(timelockAdmins[0])
        .cancelEmergencyTransaction(emgTxId);

      const tx = await timelockMultisig.getEmergencyTransaction(emgTxId);
      expect(tx.cancelled).to.be.true;
    });
  });

  describe("Batch Execution", function () {
    it("Should execute multiple timelock transactions", async function () {
      const recipient = ethers.Wallet.createRandom().address;
      const value = ethers.utils.parseEther("1");
      const delay = 24 * 60 * 60;

      // Queue multiple transactions
      const txIds = [];
      for (let i = 0; i < 3; i++) {
        const txId = await timelockMultisig
          .connect(timelockAdmins[0])
          .queueTimelockTransaction(recipient, value, "0x", delay);
        txIds.push(txId);
      }

      // Confirm all transactions
      for (let i = 0; i < 3; i++) {
        await timelockMultisig.connect(owners[0]).confirmTimelockTransaction(txIds[i]);
        await timelockMultisig.connect(owners[1]).confirmTimelockTransaction(txIds[i]);
      }

      // Increase time
      await increaseTime(delay + 1);

      // Fund contract
      await owners[0].sendTransaction({
        to: timelockMultisig.address,
        value: ethers.utils.parseEther("10")
      });

      // Batch execute
      await timelockMultisig
        .connect(timelockAdmins[0])
        .batchExecuteTimelock(txIds);

      // Check all executed
      for (let i = 0; i < 3; i++) {
        const tx = await timelockMultisig.getTimelockTransaction(txIds[i]);
        expect(tx.executed).to.be.true;
      }
    });
  });

  describe("Timelock Admin Management", function () {
    it("Should add timelock admin", async function () {
      const newAdmin = ethers.Wallet.createRandom();
      await timelockMultisig.connect(owners[0]).addTimelockAdmin(newAdmin.address);

      expect(await timelockMultisig.isTimelockAdmin(newAdmin.address)).to.be.true;
    });

    it("Should remove timelock admin", async function () {
      await timelockMultisig
        .connect(owners[0])
        .removeTimelockAdmin(timelockAdmins[0].address);

      expect(await timelockMultisig.isTimelockAdmin(timelockAdmins[0].address)).to.be.false;
    });

    it("Should not add duplicate admin", async function () {
      await expect(
        timelockMultisig.connect(owners[0]).addTimelockAdmin(timelockAdmins[0].address)
      ).to.be.revertedWith("Already admin");
    });

    it("Should not add invalid admin", async function () {
      await expect(
        timelockMultisig.connect(owners[0]).addTimelockAdmin(ethers.constants.AddressZero)
      ).to.be.revertedWith("Invalid admin");
    });
  });

  describe("View Functions", function () {
    beforeEach(async function () {
      // Queue some timelock transactions
      for (let i = 0; i < 3; i++) {
        await timelockMultisig
          .connect(timelockAdmins[0])
          .queueTimelockTransaction(
            ethers.Wallet.createRandom().address,
            ethers.utils.parseEther("1"),
            "0x",
            24 * 60 * 60
          );
      }
    });

    it("Should return timelock transaction count", async function () {
      expect(await timelockMultisig.getTimelockTransactionCount()).to.equal(3);
    });

    it("Should return pending timelock transactions", async function () {
      const pending = await timelockMultisig.getPendingTimelockTransactions();
      expect(pending.length).to.equal(3);
    });

    it("Should return pending emergency transactions", async function () {
      // Queue emergency transactions
      for (let i = 0; i < 2; i++) {
        await timelockMultisig
          .connect(timelockAdmins[0])
          .queueEmergencyTransaction(
            ethers.Wallet.createRandom().address,
            ethers.utils.parseEther("1"),
            "0x"
          );
      }

      const pending = await timelockMultisig.getPendingEmergencyTransactions();
      expect(pending.length).to.equal(2);
    });
  });

  describe("Non-Admin Restrictions", function () {
    const value = ethers.utils.parseEther("5");
    const recipient = ethers.Wallet.createRandom().address;
    const delay = 24 * 60 * 60;

    it("Should not allow non-admin to queue timelock transaction", async function () {
      await expect(
        timelockMultisig
          .connect(owners[0])
          .queueTimelockTransaction(recipient, value, "0x", delay)
      ).to.be.revertedWith("Not authorized");
    });

    it("Should not allow non-admin to queue emergency transaction", async function () {
      await expect(
        timelockMultisig
          .connect(owners[0])
          .queueEmergencyTransaction(recipient, value, "0x")
      ).to.be.revertedWith("Not authorized");
    });

    it("Should not allow non-admin to execute timelock transaction", async function () {
      const txId = await timelockMultisig
        .connect(timelockAdmins[0])
        .queueTimelockTransaction(recipient, value, "0x", delay);

      await timelockMultisig.connect(owners[0]).confirmTimelockTransaction(txId);
      await timelockMultisig.connect(owners[1]).confirmTimelockTransaction(txId);

      await increaseTime(delay + 1);

      await expect(
        timelockMultisig
          .connect(owners[0])
          .executeTimelockTransaction(txId)
      ).to.be.revertedWith("Not authorized");
    });
  });

  describe("Different Tier Confirmations", function () {
    const recipient = ethers.Wallet.createRandom().address;
    const delay = 24 * 60 * 60;

    it("Should require more confirmations for higher tiers", async function () {
      // Tier 1 transaction (< 10 ETH)
      const tier1Tx = await timelockMultisig
        .connect(timelockAdmins[0])
        .queueTimelockTransaction(recipient, ethers.utils.parseEther("5"), "0x", delay);

      // Tier 2 transaction (10-100 ETH)
      const tier2Tx = await timelockMultisig
        .connect(timelockAdmins[0])
        .queueTimelockTransaction(recipient, ethers.utils.parseEther("50"), "0x", delay);

      // Tier 3 transaction (>= 100 ETH)
      const tier3Tx = await timelockMultisig
        .connect(timelockAdmins[0])
        .queueTimelockTransaction(recipient, ethers.utils.parseEther("200"), "0x", delay);

      // Confirm all
      await timelockMultisig.connect(owners[0]).confirmTimelockTransaction(tier1Tx);
      await timelockMultisig.connect(owners[1]).confirmTimelockTransaction(tier1Tx);
      // Tier 1 ready

      await timelockMultisig.connect(owners[0]).confirmTimelockTransaction(tier2Tx);
      await timelockMultisig.connect(owners[1]).confirmTimelockTransaction(tier2Tx);
      // Tier 2 needs one more

      await timelockMultisig.connect(owners[2]).confirmTimelockTransaction(tier2Tx);
      // Tier 2 ready

      await timelockMultisig.connect(owners[0]).confirmTimelockTransaction(tier3Tx);
      await timelockMultisig.connect(owners[1]).confirmTimelockTransaction(tier3Tx);
      await timelockMultisig.connect(owners[2]).confirmTimelockTransaction(tier3Tx);
      // Tier 3 needs one more

      await increaseTime(delay + 1);

      // Only tier 1 should be executable
      expect(await timelockMultisig.canExecuteTimelock(tier1Tx)).to.be.true;
      expect(await timelockMultisig.canExecuteTimelock(tier2Tx)).to.be.true;
      expect(await timelockMultisig.canExecuteTimelock(tier3Tx)).to.be.false;

      // Add one more confirmation to tier 3
      const newOwner = ethers.Wallet.createRandom();
      await timelockMultisig.connect(owners[0]).addOwner(newOwner.address, 4);
      await timelockMultisig.connect(newOwner).confirmTimelockTransaction(tier3Tx);

      expect(await timelockMultisig.canExecuteTimelock(tier3Tx)).to.be.true;
    });
  });
});
