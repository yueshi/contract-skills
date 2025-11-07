const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MultisigWallet", function () {
  let multisig;
  let owners;
  let requiredConfirmations;
  let nonOwners;

  beforeEach(async function () {
    // Get signers
    const signers = await ethers.getSigners();
    owners = signers.slice(0, 3);
    nonOwners = signers.slice(3, 5);
    requiredConfirmations = 2;

    // Deploy multisig wallet
    const ownerAddresses = await Promise.all(owners.map(o => o.getAddress()));
    const MultisigWallet = await ethers.getContractFactory("MultisigWallet");
    multisig = await MultisigWallet.deploy(ownerAddresses, requiredConfirmations);
    await multisig.deployed();
  });

  describe("Deployment", function () {
    it("Should deploy with correct owners and confirmations", async function () {
      expect(await multisig.ownerCount()).to.equal(owners.length);

      for (let i = 0; i < owners.length; i++) {
        expect(await multisig.isOwner(owners[i].address)).to.be.true;
      }
      expect(await multisig.requiredConfirmations()).to.equal(requiredConfirmations);
    });

    it("Should not deploy with zero owners", async function () {
      const MultisigWallet = await ethers.getContractFactory("MultisigWallet");
      await expect(
        MultisigWallet.deploy([], 1)
      ).to.be.revertedWith("No owners provided");
    });

    it("Should not deploy with invalid confirmation requirement", async function () {
      const MultisigWallet = await ethers.getContractFactory("MultisigWallet");
      const ownerAddresses = await Promise.all(owners.map(o => o.getAddress()));

      await expect(
        MultisigWallet.deploy(ownerAddresses, 0)
      ).to.be.revertedWith("Invalid number of required confirmations");

      await expect(
        MultisigWallet.deploy(ownerAddresses, owners.length + 1)
      ).to.be.revertedWith("Invalid number of required confirmations");
    });
  });

  describe("Transactions", function () {
    let transactionId;
    const value = ethers.utils.parseEther("1");
    const recipient = ethers.Wallet.createRandom().address;

    beforeEach(async function () {
      // Submit transaction
      transactionId = await multisig
        .connect(owners[0])
        .submitTransaction(recipient, value, "0x");
    });

    it("Should submit transaction correctly", async function () {
      const tx = await multisig.transactions(transactionId);
      expect(tx.to).to.equal(recipient);
      expect(tx.value).to.equal(value);
      expect(tx.executed).to.be.false;
      expect(tx.confirmations).to.equal(0);
    });

    it("Should not submit transaction to zero address", async function () {
      await expect(
        multisig.connect(owners[0]).submitTransaction(
          ethers.constants.AddressZero,
          value,
          "0x"
        )
      ).to.be.revertedWith("Invalid target");
    });

    it("Should confirm transaction", async function () {
      await multisig.connect(owners[0]).confirmTransaction(transactionId);

      const tx = await multisig.transactions(transactionId);
      expect(tx.confirmations).to.equal(1);

      expect(await multisig.confirmations(transactionId, owners[0].address))
        .to.be.true;
    });

    it("Should not confirm already confirmed transaction", async function () {
      await multisig.connect(owners[0]).confirmTransaction(transactionId);
      await expect(
        multisig.connect(owners[0]).confirmTransaction(transactionId)
      ).to.be.revertedWith("Already confirmed");
    });

    it("Should not confirm non-existent transaction", async function () {
      await expect(
        multisig.connect(owners[0]).confirmTransaction(999)
      ).to.be.revertedWith("Transaction does not exist");
    });

    it("Should revoke confirmation", async function () {
      await multisig.connect(owners[0]).confirmTransaction(transactionId);
      await multisig.connect(owners[0]).revokeConfirmation(transactionId);

      const tx = await multisig.transactions(transactionId);
      expect(tx.confirmations).to.equal(0);

      expect(await multisig.confirmations(transactionId, owners[0].address))
        .to.be.false;
    });

    it("Should execute transaction with enough confirmations", async function () {
      // Get recipient balance before
      const balanceBefore = await ethers.provider.getBalance(recipient);

      // Confirm transaction from required owners
      await multisig.connect(owners[0]).confirmTransaction(transactionId);
      await multisig.connect(owners[1]).confirmTransaction(transactionId);

      // Execute transaction
      await multisig.connect(owners[2]).executeTransaction(transactionId);

      // Check execution
      const tx = await multisig.transactions(transactionId);
      expect(tx.executed).to.be.true;

      // Check recipient balance
      const balanceAfter = await ethers.provider.getBalance(recipient);
      expect(balanceAfter.sub(balanceBefore)).to.equal(value);
    });

    it("Should not execute without enough confirmations", async function () {
      await multisig.connect(owners[0]).confirmTransaction(transactionId);

      await expect(
        multisig.connect(owners[1]).executeTransaction(transactionId)
      ).to.be.revertedWith("Not enough confirmations");
    });

    it("Should not execute already executed transaction", async function () {
      await multisig.connect(owners[0]).confirmTransaction(transactionId);
      await multisig.connect(owners[1]).confirmTransaction(transactionId);
      await multisig.connect(owners[2]).executeTransaction(transactionId);

      await expect(
        multisig.connect(owners[0]).executeTransaction(transactionId)
      ).to.be.revertedWith("Already executed");
    });
  });

  describe("ETH Transfers", function () {
    let transactionId;
    const value = ethers.utils.parseEther("5");
    const recipient = ethers.Wallet.createRandom().address;

    it("Should transfer ETH correctly", async function () {
      // Fund the multisig
      await owners[0].sendTransaction({
        to: multisig.address,
        value: ethers.utils.parseEther("10")
      });

      // Submit transaction
      transactionId = await multisig
        .connect(owners[0])
        .submitTransaction(recipient, value, "0x");

      // Get balances before
      const recipientBalanceBefore = await ethers.provider.getBalance(recipient);
      const multisigBalanceBefore = await ethers.provider.getBalance(multisig.address);

      // Confirm and execute
      await multisig.connect(owners[0]).confirmTransaction(transactionId);
      await multisig.connect(owners[1]).confirmTransaction(transactionId);
      await multisig.connect(owners[2]).executeTransaction(transactionId);

      // Check balances
      const recipientBalanceAfter = await ethers.provider.getBalance(recipient);
      const multisigBalanceAfter = await ethers.provider.getBalance(multisig.address);

      expect(recipientBalanceAfter.sub(recipientBalanceBefore)).to.equal(value);
      expect(multisigBalanceBefore.sub(multisigBalanceAfter)).to.equal(value);
    });

    it("Should handle fallback function", async function () {
      const value = ethers.utils.parseEther("1");
      await owners[0].sendTransaction({
        to: multisig.address,
        value: value
      });

      const balance = await ethers.provider.getBalance(multisig.address);
      expect(balance).to.equal(value);
    });
  });

  describe("ERC20 Transfers", function () {
    let transactionId;
    let testToken;
    const amount = ethers.utils.parseEther("100");
    const recipient = ethers.Wallet.createRandom().address;

    beforeEach(async function () {
      // Deploy test token
      const TestToken = await ethers.getContractFactory("TestToken");
      testToken = await TestToken.deploy(
        "Test Token",
        "TEST",
        ethers.utils.parseEther("1000")
      );
      await testToken.deployed();

      // Transfer tokens to multisig
      await testToken.transfer(multisig.address, ethers.utils.parseEther("200"));
    });

    it("Should transfer tokens via contract call", async function () {
      // Submit transaction to transfer tokens
      const transferData = testToken.interface.encodeFunctionData("transfer", [
        recipient,
        amount
      ]);

      transactionId = await multisig
        .connect(owners[0])
        .submitTransaction(testToken.address, 0, transferData);

      // Confirm and execute
      await multisig.connect(owners[0]).confirmTransaction(transactionId);
      await multisig.connect(owners[1]).confirmTransaction(transactionId);
      await multisig.connect(owners[2]).executeTransaction(transactionId);

      // Check token balance
      const recipientBalance = await testToken.balanceOf(recipient);
      expect(recipientBalance).to.equal(amount);
    });
  });

  describe("Owner Management", function () {
    let newOwner;

    beforeEach(async function () {
      newOwner = ethers.Wallet.createRandom();
    });

    it("Should add new owner", async function () {
      await multisig
        .connect(owners[0])
        .addOwner(newOwner.address, requiredConfirmations);

      expect(await multisig.isOwner(newOwner.address)).to.be.true;
      expect(await multisig.ownerCount()).to.equal(owners.length + 1);
    });

    it("Should not add duplicate owner", async function () {
      await expect(
        multisig.connect(owners[0]).addOwner(owners[0].address, requiredConfirmations)
      ).to.be.revertedWith("Already an owner");
    });

    it("Should not add owner with invalid address", async function () {
      await expect(
        multisig.connect(owners[0]).addOwner(
          ethers.constants.AddressZero,
          requiredConfirmations
        )
      ).to.be.revertedWith("Invalid owner");
    });

    it("Should remove owner", async function () {
      await multisig
        .connect(owners[0])
        .addOwner(newOwner.address, requiredConfirmations);

      await multisig
        .connect(owners[0])
        .removeOwner(newOwner.address, requiredConfirmations);

      expect(await multisig.isOwner(newOwner.address)).to.be.false;
      expect(await multisig.ownerCount()).to.equal(owners.length);
    });

    it("Should update required confirmations", async function () {
      await multisig
        .connect(owners[0])
        .updateRequiredConfirmations(3);

      expect(await multisig.requiredConfirmations()).to.equal(3);
    });

    it("Should not update required confirmations to invalid value", async function () {
      await expect(
        multisig.connect(owners[0]).updateRequiredConfirmations(0)
      ).to.be.revertedWith("Invalid confirmation requirement");

      await expect(
        multisig.connect(owners[0]).updateRequiredConfirmations(owners.length + 1)
      ).to.be.revertedWith("Invalid confirmation requirement");
    });
  });

  describe("Safe Mode", function () {
    it("Should enable safe mode", async function () {
      await multisig.connect(owners[0]).enableSafeMode();
      expect(await multisig.safeModeEnabled()).to.be.true;
    });

    it("Should disable safe mode", async function () {
      await multisig.connect(owners[0]).enableSafeMode();
      await multisig.connect(owners[0]).disableSafeMode();
      expect(await multisig.safeModeEnabled()).to.be.false;
    });

    it("Should execute in safe mode", async function () {
      await multisig.connect(owners[0]).enableSafeMode();

      const recipient = ethers.Wallet.createRandom().address;
      const value = ethers.utils.parseEther("1");

      // Fund multisig
      await owners[0].sendTransaction({
        to: multisig.address,
        value: ethers.utils.parseEther("2")
      });

      // Execute in safe mode
      await multisig
        .connect(owners[1])
        .executeInSafeMode(recipient, value, "0x");

      // Check balance
      const balance = await ethers.provider.getBalance(recipient);
      expect(balance).to.equal(value);
    });

    it("Should not execute in safe mode without enabling", async function () {
      const recipient = ethers.Wallet.createRandom().address;
      const value = ethers.utils.parseEther("1");

      await expect(
        multisig.connect(owners[0]).executeInSafeMode(recipient, value, "0x")
      ).to.be.revertedWith("Safe mode not enabled");
    });
  });

  describe("Pausable", function () {
    it("Should pause contract", async function () {
      await multisig.connect(owners[0]).pause();
      expect(await multisig.paused()).to.be.true;
    });

    it("Should unpause contract", async function () {
      await multisig.connect(owners[0]).pause();
      await multisig.connect(owners[0]).unpause();
      expect(await multisig.paused()).to.be.false;
    });

    it("Should not allow transactions when paused", async function () {
      await multisig.connect(owners[0]).pause();

      const recipient = ethers.Wallet.createRandom().address;
      const value = ethers.utils.parseEther("1");

      await expect(
        multisig.connect(owners[0]).submitTransaction(recipient, value, "0x")
      ).to.be.revertedWithCustomError(multisig, "EnforcedPause");
    });
  });

  describe("Gnosis Safe Compatibility", function () {
    it("Should enable Gnosis compatibility", async function () {
      await multisig.connect(owners[0]).enableGnosisCompatibility();
      expect(await multisig.gnosisCompatibilityMode()).to.be.true;
    });

    it("Should return nonce", async function () {
      await multisig.connect(owners[0]).enableGnosisCompatibility();
      expect(await multisig.nonce()).to.equal(0);
    });

    it("Should check signatures", async function () {
      await multisig.connect(owners[0]).enableGnosisCompatibility();

      const dataHash = ethers.utils.keccak256("0x");
      const data = "0x";
      const signatures = "0x";
      const requiredSignatures = 2;

      // Should return false for empty signatures
      const result = await multisig.checkNSignatures(
        dataHash,
        data,
        signatures,
        requiredSignatures
      );
      expect(result).to.be.false;
    });

    it("Should return transaction hash", async function () {
      await multisig.connect(owners[0]).enableGnosisCompatibility();

      const txHash = await multisig.getTransactionHash(
        ethers.constants.AddressZero,
        0,
        "0x",
        0,
        0,
        0,
        0,
        ethers.constants.AddressZero,
        ethers.constants.AddressZero,
        0
      );

      expect(txHash).to.not.equal(bytes32(0));
    });
  });

  describe("View Functions", function () {
    beforeEach(async function () {
      // Submit some transactions
      for (let i = 0; i < 3; i++) {
        await multisig
          .connect(owners[0])
          .submitTransaction(ethers.Wallet.createRandom().address, 0, "0x");

        // Confirm some transactions
        await multisig.connect(owners[0]).confirmTransaction(i);
        await multisig.connect(owners[1]).confirmTransaction(i);
      }

      // Execute one transaction
      await multisig.connect(owners[2]).executeTransaction(0);
    });

    it("Should return transaction count", async function () {
      expect(await multisig.getTransactionCount()).to.equal(3);
    });

    it("Should return transaction details", async function () {
      const [to, value, data, executed, confirmations] =
        await multisig.getTransaction(0);

      expect(to).to.not.equal(ethers.constants.AddressZero);
      expect(executed).to.be.true;
      expect(confirmations).to.equal(requiredConfirmations);
    });

    it("Should return confirmations", async function () {
      const confirmations = await multisig.getConfirmations(0);
      expect(confirmations.length).to.equal(requiredConfirmations);
    });

    it("Should return pending transactions", async function () {
      const pending = await multisig.getPendingTransactions();
      expect(pending.length).to.equal(2);
    });

    it("Should return executed transactions", async function () {
      const executed = await multisig.getExecutedTransactions();
      expect(executed.length).to.equal(1);
    });
  });

  describe("Non-Owner Restrictions", function () {
    const value = ethers.utils.parseEther("1");
    const recipient = ethers.Wallet.createRandom().address;

    it("Should not allow non-owner to submit transaction", async function () {
      await expect(
        multisig
          .connect(nonOwners[0])
          .submitTransaction(recipient, value, "0x")
      ).to.be.revertedWith("Not an owner");
    });

    it("Should not allow non-owner to confirm transaction", async function () {
      const txId = await multisig
        .connect(owners[0])
        .submitTransaction(recipient, value, "0x");

      await expect(
        multisig.connect(nonOwners[0]).confirmTransaction(txId)
      ).to.be.revertedWith("Not an owner");
    });

    it("Should not allow non-owner to execute transaction", async function () {
      const txId = await multisig
        .connect(owners[0])
        .submitTransaction(recipient, value, "0x");

      await multisig.connect(owners[0]).confirmTransaction(txId);
      await multisig.connect(owners[1]).confirmTransaction(txId);

      await expect(
        multisig.connect(nonOwners[0]).executeTransaction(txId)
      ).to.be.revertedWith("Not an owner");
    });
  });
});
