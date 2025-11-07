const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("ERC721Collection", function () {
  let erc721Collection;
  let owner, user1, user2, user3;
  const COLLECTION_NAME = "TestNFT";
  const COLLECTION_SYMBOL = "TNFT";
  const MAX_SUPPLY = 1000;
  const MAX_MINT_PER_TX = 5;
  const MINT_PRICE = ethers.utils.parseEther("0.1");
  const BASE_URI = "ipfs://base/";

  beforeEach(async function () {
    [owner, user1, user2, user3] = await ethers.getSigners();

    // Deploy collection
    const currentTime = await time.latest();
    const publicSaleStart = currentTime + 86400; // +1 day
    const allowlistSaleStart = currentTime + 3600; // +1 hour

    const ERC721Collection = await ethers.getContractFactory("ERC721Collection");
    erc721Collection = await ERC721Collection.deploy(
      COLLECTION_NAME,
      COLLECTION_SYMBOL,
      MAX_SUPPLY,
      MAX_MINT_PER_TX,
      MINT_PRICE,
      publicSaleStart,
      allowlistSaleStart,
      BASE_URI,
      "ipfs://contract/"
    );

    await erc721Collection.deployed();
  });

  describe("Deployment", function () {
    it("Should set correct name and symbol", async function () {
      expect(await erc721Collection.name()).to.equal(COLLECTION_NAME);
      expect(await erc721Collection.symbol()).to.equal(COLLECTION_SYMBOL);
    });

    it("Should set correct max supply", async function () {
      expect(await erc721Collection.maxSupply()).to.equal(MAX_SUPPLY);
    });

    it("Should set correct mint price", async function () {
      expect(await erc721Collection.mintPrice()).to.equal(MINT_PRICE);
    });

    it("Should set owner correctly", async function () {
      expect(await erc721Collection.owner()).to.equal(owner.address);
    });

    it("Should have correct royalty settings", async function () {
      const [receiver, feeNumerator] = await erc721Collection.royaltyInfo(1, 1000);
      expect(receiver).to.equal(owner.address);
      expect(feeNumerator).to.equal(500); // 5%
    });
  });

  describe("Sale Phase", function () {
    it("Should return NOT_STARTED before allowlist sale", async function () {
      expect(await erc721Collection.salePhase()).to.equal(0); // NOT_STARTED
    });

    it("Should return ALLOWLIST during allowlist sale", async function () {
      await time.increase(3600); // +1 hour to reach allowlist sale
      expect(await erc721Collection.salePhase()).to.equal(1); // ALLOWLIST
    });

    it("Should return PUBLIC during public sale", async function () {
      await time.increase(86400); // +1 day to reach public sale
      expect(await erc721Collection.salePhase()).to.equal(2); // PUBLIC
    });
  });

  describe("Allowlist", function () {
    beforeEach(async function () {
      // Fast forward to allowlist sale
      await time.increase(3600);
    });

    it("Owner should add users to allowlist", async function () {
      await erc721Collection.updateAllowlist([user1.address], [true]);
      expect(await erc721Collection.allowlist(user1.address)).to.be.true;
    });

    it("Non-owner cannot add to allowlist", async function () {
      await expect(
        erc721Collection.connect(user1).updateAllowlist([user2.address], [true])
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });

    it("Should allow allowlist minting", async function () {
      await erc721Collection.updateAllowlist([user1.address], [true]);

      // User1 mints
      const value = MINT_PRICE.mul(2);
      await erc721Collection.connect(user1).mintAllowlist(2, { value });

      // Check ownership
      expect(await erc721Collection.ownerOf(1)).to.equal(user1.address);
      expect(await erc721Collection.ownerOf(2)).to.equal(user1.address);
    });

    it("Should limit allowlist minting", async function () {
      await erc721Collection.updateAllowlist([user1.address], [true]);

      // User1 mints max allowed
      await erc721Collection.connect(user1).mintAllowlist(2, { value: MINT_PRICE.mul(2) });

      // Try to mint more (should exceed limit)
      await expect(
        erc721Collection.connect(user1).mintAllowlist(1, { value: MINT_PRICE })
      ).to.be.revertedWith("Exceeds allowlist limit");
    });

    it("Should not allow minting without allowlist", async function () {
      await expect(
        erc721Collection.connect(user1).mintAllowlist(1, { value: MINT_PRICE })
      ).to.be.revertedWith("Not on allowlist");
    });
  });

  describe("Public Sale", function () {
    beforeEach(async function () {
      // Fast forward to public sale
      await time.increase(86400);
    });

    it("Should allow public minting", async function () {
      await erc721Collection.connect(user1).mintPublic(3, { value: MINT_PRICE.mul(3) });

      expect(await erc721Collection.ownerOf(1)).to.equal(user1.address);
      expect(await erc721Collection.ownerOf(2)).to.equal(user1.address);
      expect(await erc721Collection.ownerOf(3)).to.equal(user1.address);
    });

    it("Should enforce mint limit per transaction", async function () {
      await expect(
        erc721Collection.connect(user1).mintPublic(6, { value: MINT_PRICE.mul(6) })
      ).to.be.revertedWith("Exceeds max per transaction");
    });

    it("Should enforce max supply", async function () {
      // Mint maximum supply
      for (let i = 0; i < 200; i++) {
        await erc721Collection.connect(user1).mintPublic(5, { value: MINT_PRICE.mul(5) });
      }

      // Try to mint more
      await expect(
        erc721Collection.connect(user1).mintPublic(1, { value: MINT_PRICE })
      ).to.be.revertedWith("Exceeds max supply");
    });

    it("Should refund excess payment", async function () {
      const tx = await erc721Collection.connect(user1).mintPublic(1, {
        value: MINT_PRICE.mul(2) // Send extra
      });

      const receipt = await tx.wait();
      expect(receipt.effectiveGasPrice.mul(receipt.gasUsed).lte(MINT_PRICE.mul(2)));
    });

    it("Should require sufficient payment", async function () {
      await expect(
        erc721Collection.connect(user1).mintPublic(1, { value: MINT_PRICE.sub(1) })
      ).to.be.revertedWith("Insufficient payment");
    });
  });

  describe("Admin Functions", function () {
    it("Owner should be able to admin mint", async function () {
      await erc721Collection.adminMint(user1.address, 10);

      for (let i = 1; i <= 10; i++) {
        expect(await erc721Collection.ownerOf(i)).to.equal(user1.address);
      }
    });

    it("Should update base URI", async function () {
      const newBaseURI = "ipfs://new-base/";
      await erc721Collection.setBaseURI(newBaseURI);

      // Mint first NFT
      await time.increase(86400);
      await erc721Collection.mintPublic(1, { value: MINT_PRICE });

      expect(await erc721Collection.tokenURI(1)).to.equal("ipfs://new-base/1.json");
    });

    it("Should update contract URI", async function () {
      const newContractURI = "ipfs://new-contract/";
      await erc721Collection.setContractURI(newContractURI);

      expect(await erc721Collection.contractURI()).to.equal("ipfs://new-contract/");
    });

    it("Should update royalty", async function () {
      const newReceiver = user2.address;
      const newFee = 300; // 3%

      await erc721Collection.setRoyalty(newReceiver, newFee);

      const [receiver, feeNumerator] = await erc721Collection.royaltyInfo(1, 1000);
      expect(receiver).to.equal(newReceiver);
      expect(feeNumerator).to.equal(newFee);
    });

    it("Cannot set royalty above 10%", async function () {
      await expect(
        erc721Collection.setRoyalty(user1.address, 1001)
      ).to.be.revertedWith("Fee cannot exceed 10%");
    });

    it("Non-owner cannot update royalty", async function () {
      await expect(
        erc721Collection.connect(user1).setRoyalty(user1.address, 300)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Pausable", function () {
    it("Owner can pause", async function () {
      await erc721Collection.pause();
      expect(await erc721Collection.paused()).to.be.true;
    });

    it("Owner can unpause", async function () {
      await erc721Collection.pause();
      await erc721Collection.unpause();
      expect(await erc721Collection.paused()).to.be.false;
    });

    it("Cannot mint when paused", async function () {
      await time.increase(86400);
      await erc721Collection.pause();

      await expect(
        erc721Collection.mintPublic(1, { value: MINT_PRICE })
      ).to.be.revertedWith("Pausable: paused");
    });

    it("Non-owner cannot pause", async function () {
      await expect(
        erc721Collection.connect(user1).pause()
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("View Functions", function () {
    beforeEach(async function () {
      await time.increase(86400);
      await erc721Collection.mintPublic(5, { value: MINT_PRICE.mul(5) });
    });

    it("Should return total minted", async function () {
      expect(await erc721Collection.totalMinted()).to.equal(5);
    });

    it("Should return tokens of owner", async function () {
      await erc721Collection.connect(user2).mintPublic(3, { value: MINT_PRICE.mul(3) });

      const user1Tokens = await erc721Collection.tokensOfOwner(user1.address);
      expect(user1Tokens.length).to.equal(5);
      expect(user1Tokens[0]).to.equal(1);

      const user2Tokens = await erc721Collection.tokensOfOwner(user2.address);
      expect(user2Tokens.length).to.equal(3);
    });

    it("Should return correct sale phase string", async function () {
      expect(await erc721Collection.getSalePhaseString()).to.equal("PUBLIC");
    });
  });

  describe("Burnable", function () {
    beforeEach(async function () {
      await time.increase(86400);
      await erc721Collection.mintPublic(3, { value: MINT_PRICE.mul(3) });
    });

    it("Owner can burn their NFT", async function () {
      await erc721Collection.connect(user1).burn(1);
      await expect(erc721Collection.ownerOf(1)).to.be.revertedWith("ERC721: invalid token ID");
    });

    it("Cannot burn non-owned NFT", async function () {
      await expect(
        erc721Collection.connect(user2).burn(1)
      ).to.be.revertedWith("ERC721: caller is not token owner or approved");
    });
  });

  describe("Withdraw", function () {
    beforeEach(async function () {
      await time.increase(86400);
      await erc721Collection.mintPublic(10, { value: MINT_PRICE.mul(10) });
    });

    it("Owner can withdraw funds", async function () {
      const balance = await ethers.provider.getBalance(erc721Collection.address);
      expect(balance).to.equal(MINT_PRICE.mul(10));

      const ownerBalanceBefore = await ethers.provider.getBalance(owner.address);
      const tx = await erc721Collection.withdraw();
      const receipt = await tx.wait();
      const gasCost = receipt.gasUsed.mul(receipt.effectiveGasPrice);

      const ownerBalanceAfter = await ethers.provider.getBalance(owner.address);
      expect(ownerBalanceAfter.sub(ownerBalanceBefore).add(gasCost)).to.equal(MINT_PRICE.mul(10));
    });

    it("Non-owner cannot withdraw", async function () {
      await expect(
        erc721Collection.connect(user1).withdraw()
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Edge Cases", function () {
    beforeEach(async function () {
      await time.increase(86400);
    });

    it("Cannot mint 0 NFTs", async function () {
      await expect(
        erc721Collection.mintPublic(0, { value: 0 })
      ).to.be.revertedWith("Amount must be > 0");
    });

    it("Cannot mint with invalid address", async function () {
      await expect(
        erc721Collection.adminMint(ethers.constants.AddressZero, 1)
      ).to.be.revertedWith("Invalid recipient");
    });

    it("Cannot update royalty to zero address", async function () {
      await expect(
        erc721Collection.setRoyalty(ethers.constants.AddressZero, 500)
      ).to.be.revertedWith("Invalid receiver");
    });
  });
});
