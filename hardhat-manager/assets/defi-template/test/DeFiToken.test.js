const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("DeFiToken", function () {
  let defiToken, owner, minter, user1, user2;
  const INITIAL_SUPPLY = ethers.utils.parseEther("1000000"); // 1M tokens

  beforeEach(async function () {
    [owner, minter, user1, user2] = await ethers.getSigners();

    const DeFiToken = await ethers.getContractFactory("DeFiToken");
    defiToken = await DeFiToken.deploy("DeFi Token", "DFI", INITIAL_SUPPLY, owner.address);
    await defiToken.deployed();
  });

  describe("Deployment", function () {
    it("Should set correct name and symbol", async function () {
      expect(await defiToken.name()).to.equal("DeFi Token");
      expect(await defiToken.symbol()).to.equal("DFI");
    });

    it("Should mint initial supply to owner", async function () {
      expect(await defiToken.balanceOf(owner.address)).to.equal(INITIAL_SUPPLY);
      expect(await defiToken.totalSupply()).to.equal(INITIAL_SUPPLY);
    });

    it("Should set owner as minter", async function () {
      expect(await defiToken.isMinter(owner.address)).to.be.true;
    });
  });

  describe("Minting", function () {
    beforeEach(async function () {
      await defiToken.addMinter(minter.address);
    });

    it("Minter can mint tokens", async function () {
      const mintAmount = ethers.utils.parseEther("1000");
      await defiToken.connect(minter).mint(user1.address, mintAmount);

      expect(await defiToken.balanceOf(user1.address)).to.equal(mintAmount);
      expect(await defiToken.totalSupply()).to.equal(INITIAL_SUPPLY.add(mintAmount));
    });

    it("Owner can mint tokens", async function () {
      const mintAmount = ethers.utils.parseEther("500");
      await defiToken.mint(user1.address, mintAmount);

      expect(await defiToken.balanceOf(user1.address)).to.equal(mintAmount);
    });

    it("Non-minter cannot mint", async function () {
      const mintAmount = ethers.utils.parseEther("100");
      await expect(
        defiToken.connect(user1).mint(user2.address, mintAmount)
      ).to.be.revertedWith("Not authorized minter");
    });

    it("Cannot mint to zero address", async function () {
      await expect(
        defiToken.connect(minter).mint(ethers.constants.AddressZero, ethers.utils.parseEther("100"))
      ).to.be.revertedWith("Invalid address");
    });

    it("Cannot mint zero amount", async function () {
      await expect(
        defiToken.connect(minter).mint(user1.address, 0)
      ).to.be.revertedWith("Amount must be > 0");
    });

    it("Can batch mint", async function () {
      const recipients = [user1.address, user2.address];
      const amounts = [ethers.utils.parseEther("100"), ethers.utils.parseEther("200")];

      await defiToken.connect(minter).batchMint(recipients, amounts);

      expect(await defiToken.balanceOf(user1.address)).to.equal(amounts[0]);
      expect(await defiToken.balanceOf(user2.address)).to.equal(amounts[1]);
    });
  });

  describe("Burning", function () {
    beforeEach(async function () {
      await defiToken.transfer(user1.address, ethers.utils.parseEther("1000"));
    });

    it("User can burn own tokens", async function () {
      const burnAmount = ethers.utils.parseEther("500");
      await defiToken.connect(user1).burn(burnAmount);

      expect(await defiToken.balanceOf(user1.address)).to.equal(ethers.utils.parseEther("500"));
      expect(await defiToken.totalSupply()).to.equal(INITIAL_SUPPLY.sub(burnAmount));
    });

    it("User can burn from allowance", async function () {
      const approveAmount = ethers.utils.parseEther("1000");
      const burnAmount = ethers.utils.parseEther("300");

      await defiToken.connect(user1).approve(owner.address, approveAmount);
      await defiToken.burnFrom(user1.address, burnAmount);

      expect(await defiToken.balanceOf(user1.address)).to.equal(ethers.utils.parseEther("700"));
    });
  });

  describe("Access Control", function () {
    it("Owner can add minter", async function () {
      await defiToken.addMinter(minter.address);
      expect(await defiToken.isMinter(minter.address)).to.be.true;
    });

    it("Owner can remove minter", async function () {
      await defiToken.addMinter(minter.address);
      await defiToken.removeMinter(minter.address);
      expect(await defiToken.isMinter(minter.address)).to.be.false;
    });

    it("Non-owner cannot add minter", async function () {
      await expect(
        defiToken.connect(user1).addMinter(user2.address)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });

    it("Non-owner cannot remove minter", async function () {
      await defiToken.addMinter(minter.address);
      await expect(
        defiToken.connect(user1).removeMinter(minter.address)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Blacklist", function () {
    beforeEach(async function () {
      await defiToken.transfer(user1.address, ethers.utils.parseEther("1000"));
    });

    it("Owner can blacklist account", async function () {
      await defiToken.blacklist(user1.address);
      expect(await defiToken.isBlacklisted(user1.address)).to.be.true;
    });

    it("Owner can remove from blacklist", async function () {
      await defiToken.blacklist(user1.address);
      await defiToken.unBlacklist(user1.address);
      expect(await defiToken.isBlacklisted(user1.address)).to.be.false;
    });

    it("Blacklisted user cannot transfer", async function () {
      await defiToken.blacklist(user1.address);
      await expect(
        defiToken.connect(user1).transfer(user2.address, ethers.utils.parseEther("100"))
      ).to.be.revertedWith("Account is blacklisted");
    });

    it("Cannot transfer to blacklisted account", async function () {
      await defiToken.blacklist(user2.address);
      await expect(
        defiToken.connect(user1).transfer(user2.address, ethers.utils.parseEther("100"))
      ).to.be.revertedWith("Recipient is blacklisted");
    });

    it("Blacklisted user cannot receive mint", async function () {
      await defiToken.addMinter(minter.address);
      await defiToken.blacklist(user1.address);
      await expect(
        defiToken.connect(minter).mint(user1.address, ethers.utils.parseEther("100"))
      ).to.be.revertedWith("Recipient is blacklisted");
    });

    it("Non-owner cannot blacklist", async function () {
      await expect(
        defiToken.connect(user1).blacklist(user2.address)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Pausable", function () {
    it("Owner can pause", async function () {
      await defiToken.pause();
      expect(await defiToken.paused()).to.be.true;
    });

    it("Owner can unpause", async function () {
      await defiToken.pause();
      await defiToken.unpause();
      expect(await defiToken.paused()).to.be.false;
    });

    it("Non-owner cannot pause", async function () {
      await expect(
        defiToken.connect(user1).pause()
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });

    it("Cannot transfer when paused", async function () {
      await defiToken.pause();
      await expect(
        defiToken.transfer(user1.address, ethers.utils.parseEther("100"))
      ).to.be.revertedWith("Pausable: paused");
    });

    it("Cannot mint when paused", async function () {
      await defiToken.pause();
      await expect(
        defiToken.mint(user1.address, ethers.utils.parseEther("100"))
      ).to.be.revertedWith("Pausable: paused");
    });

    it("Cannot burn when paused", async function () {
      await defiToken.transfer(user1.address, ethers.utils.parseEther("100"));
      await defiToken.pause();
      await expect(
        defiToken.connect(user1).burn(ethers.utils.parseEther("50"))
      ).to.be.revertedWith("Pausable: paused");
    });
  });

  describe("View Functions", function () {
    it("Should return correct token info", async function () {
      const info = await defiToken.getInfo();
      expect(info.name_).to.equal("DeFi Token");
      expect(info.symbol_).to.equal("DFI");
      expect(info.totalSupply_).to.equal(INITIAL_SUPPLY);
      expect(info.decimals_).to.equal(18);
    });
  });

  describe("Events", function () {
    it("Should emit MinterAdded event", async function () {
      await expect(defiToken.addMinter(minter.address))
        .to.emit(defiToken, "MinterAdded")
        .withArgs(minter.address);
    });

    it("Should emit MinterRemoved event", async function () {
      await defiToken.addMinter(minter.address);
      await expect(defiToken.removeMinter(minter.address))
        .to.emit(defiToken, "MinterRemoved")
        .withArgs(minter.address);
    });

    it("Should emit Minted event", async function () {
      await defiToken.addMinter(minter.address);
      const mintAmount = ethers.utils.parseEther("100");
      await expect(defiToken.connect(minter).mint(user1.address, mintAmount))
        .to.emit(defiToken, "Minted")
        .withArgs(user1.address, mintAmount);
    });

    it("Should emit Burned event", async function () {
      await defiToken.transfer(user1.address, ethers.utils.parseEther("100"));
      const burnAmount = ethers.utils.parseEther("50");
      await expect(defiToken.connect(user1).burn(burnAmount))
        .to.emit(defiToken, "Burned")
        .withArgs(user1.address, burnAmount);
    });
  });
});
