const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("SimpleDEX", function () {
  let simpleDEX, tokenA, tokenB, owner, user1, user2, user3;
  const INITIAL_SUPPLY = ethers.utils.parseEther("10000");

  beforeEach(async function () {
    [owner, user1, user2, user3] = await ethers.getSigners();

    // Deploy tokens
    const ERC20 = await ethers.getContractFactory("ERC20TestToken");
    tokenA = await ERC20.deploy("Token A", "TKA", INITIAL_SUPPLY);
    tokenB = await ERC20.deploy("Token B", "TKB", INITIAL_SUPPLY);

    // Deploy DEX
    const SimpleDEX = await ethers.getContractFactory("SimpleDEX");
    simpleDEX = await SimpleDEX.deploy(tokenA.address, tokenB.address);
    await simpleDEX.deployed();
  });

  describe("Deployment", function () {
    it("Should set correct token addresses", async function () {
      expect(await simpleDEX.tokenA()).to.equal(tokenA.address);
      expect(await simpleDEX.tokenB()).to.equal(tokenB.address);
    });

    it("Should start with zero reserves", async function () {
      const reserves = await simpleDEX.getReserves();
      expect(reserves.reserveA).to.equal(0);
      expect(reserves.reserveB).to.equal(0);
    });

    it("Should have zero total liquidity", async function () {
      expect(await simpleDEX.totalLiquidity()).to.equal(0);
    });
  });

  describe("Adding Liquidity", function () {
    beforeEach(async function () {
      // Approve tokens for DEX
      await tokenA.transfer(user1.address, ethers.utils.parseEther("1000"));
      await tokenB.transfer(user1.address, ethers.utils.parseEther("1000"));
      await tokenA.connect(user1).approve(simpleDEX.address, ethers.constants.MaxUint256);
      await tokenB.connect(user1).approve(simpleDEX.address, ethers.constants.MaxUint256);
    });

    it("First liquidity provider should receive LP tokens", async function () {
      const amountA = ethers.utils.parseEther("100");
      const amountB = ethers.utils.parseEther("200");

      await simpleDEX.connect(user1).addLiquidity(amountA, amountB);

      expect(await simpleDEX.totalLiquidity()).to.be.gt(0);
      expect(await simpleDEX.getLiquidityInfo(user1.address)).to.include({
        liquidityAmount: ethers.utils.parseEther("141") // sqrt(100 * 200) - 1000
      });
    });

    it("Should add liquidity in correct ratio", async function () {
      const amountA = ethers.utils.parseEther("100");
      const amountB = ethers.utils.parseEther("200");

      await simpleDEX.connect(user1).addLiquidity(amountA, amountB);

      const reserves = await simpleDEX.getReserves();
      expect(reserves.reserveA).to.equal(amountA);
      expect(reserves.reserveB).to.equal(amountB);
    });

    it("Cannot add liquidity with zero amounts", async function () {
      await expect(
        simpleDEX.connect(user1).addLiquidity(0, ethers.utils.parseEther("100"))
      ).to.be.revertedWith("Amount must be > 0");

      await expect(
        simpleDEX.connect(user1).addLiquidity(ethers.utils.parseEther("100"), 0)
      ).to.be.revertedWith("Amount must be > 0");
    });

    it("Second liquidity provider must maintain ratio", async function () {
      // First provider adds 100 A and 200 B
      await simpleDEX.connect(user1).addLiquidity(
        ethers.utils.parseEther("100"),
        ethers.utils.parseEther("200")
      );

      // Second provider adds tokens in wrong ratio
      await tokenA.transfer(user2.address, ethers.utils.parseEther("100"));
      await tokenB.transfer(user2.address, ethers.utils.parseEther("300"));
      await tokenA.connect(user2).approve(simpleDEX.address, ethers.constants.MaxUint256);
      await tokenB.connect(user2).approve(simpleDEX.address, ethers.constants.MaxUint256);

      await expect(
        simpleDEX.connect(user2).addLiquidity(
          ethers.utils.parseEther("100"),
          ethers.utils.parseEther("300")
        )
      ).to.be.revertedWith("Incorrect token ratio");
    });

    it("Should sync reserves after adding liquidity", async function () {
      const amountA = ethers.utils.parseEther("100");
      const amountB = ethers.utils.parseEther("200");

      await simpleDEX.connect(user1).addLiquidity(amountA, amountB);

      const reserves = await simpleDEX.getReserves();
      expect(reserves.reserveA).to.equal(amountA);
      expect(reserves.reserveB).to.equal(amountB);
    });

    it("Should emit AddLiquidity event", async function () {
      const amountA = ethers.utils.parseEther("100");
      const amountB = ethers.utils.parseEther("200");

      await expect(simpleDEX.connect(user1).addLiquidity(amountA, amountB))
        .to.emit(simpleDEX, "AddLiquidity")
        .withArgs(user1.address, amountA, amountB, ethers.utils.parseEther("141"));
    });
  });

  describe("Swapping", function () {
    beforeEach(async function () {
      // Add initial liquidity
      await tokenA.transfer(user1.address, ethers.utils.parseEther("1000"));
      await tokenB.transfer(user1.address, ethers.utils.parseEther("1000"));
      await tokenA.connect(user1).approve(simpleDEX.address, ethers.constants.MaxUint256);
      await tokenB.connect(user1).approve(simpleDEX.address, ethers.constants.MaxUint256);

      await simpleDEX.connect(user1).addLiquidity(
        ethers.utils.parseEther("100"),
        ethers.utils.parseEther("200")
      );

      // Setup user2 for swapping
      await tokenA.transfer(user2.address, ethers.utils.parseEther("100"));
      await tokenA.connect(user2).approve(simpleDEX.address, ethers.constants.MaxUint256);
    });

    it("Should swap token A for token B", async function () {
      const swapAmount = ethers.utils.parseEther("10");
      const reservesBefore = await simpleDEX.getReserves();

      await simpleDEX.connect(user2).swap(tokenA.address, swapAmount);

      const reservesAfter = await simpleDEX.getReserves();
      expect(reservesAfter.reserveA).to.equal(reservesBefore.reserveA.add(swapAmount));
      expect(reservesAfter.reserveB).to.be.lt(reservesBefore.reserveB);

      const user2BalanceB = await tokenB.balanceOf(user2.address);
      expect(user2BalanceB).to.be.gt(0);
    });

    it("Should swap token B for token A", async function () {
      await tokenB.transfer(user2.address, ethers.utils.parseEther("100"));
      await tokenB.connect(user2).approve(simpleDEX.address, ethers.constants.MaxUint256);

      const swapAmount = ethers.utils.parseEther("20");
      const reservesBefore = await simpleDEX.getReserves();

      await simpleDEX.connect(user2).swap(tokenB.address, swapAmount);

      const reservesAfter = await simpleDEX.getReserves();
      expect(reservesAfter.reserveB).to.equal(reservesBefore.reserveB.add(swapAmount));
      expect(reservesAfter.reserveA).to.be.lt(reservesBefore.reserveA);
    });

    it("Should calculate correct output amount", async function () {
      const swapAmount = ethers.utils.parseEther("10");
      const expectedOutput = await simpleDEX.getAmountOut(
        swapAmount,
        ethers.utils.parseEther("100"),
        ethers.utils.parseEther("200")
      );

      expect(expectedOutput).to.be.gt(0);
      expect(expectedOutput).to.be.lt(ethers.utils.parseEther("20")); // Should be less than input due to fee
    });

    it("Cannot swap with zero amount", async function () {
      await expect(
        simpleDEX.connect(user2).swap(tokenA.address, 0)
      ).to.be.revertedWith("Amount must be > 0");
    });

    it("Cannot swap invalid token", async function () {
      const TestToken = await ethers.getContractFactory("ERC20TestToken");
      const invalidToken = await TestToken.deploy("Invalid", "INV", INITIAL_SUPPLY);
      await invalidToken.transfer(user2.address, ethers.utils.parseEther("100"));
      await invalidToken.connect(user2).approve(simpleDEX.address, ethers.constants.MaxUint256);

      await expect(
        simpleDEX.connect(user2).swap(invalidToken.address, ethers.utils.parseEther("10"))
      ).to.be.revertedWith("Invalid token");
    });

    it("Should emit Swap event", async function () {
      const swapAmount = ethers.utils.parseEther("10");

      await expect(simpleDEX.connect(user2).swap(tokenA.address, swapAmount))
        .to.emit(simpleDEX, "Swap")
        .withArgs(user2.address, tokenA.address, swapAmount, tokenB.address, ethers.utils.parseEther("19")); // Approximate
    });

    it("Should maintain constant product (x * y = k)", async function () {
      const swapAmount = ethers.utils.parseEther("10");

      const reservesBefore = await simpleDEX.getReserves();
      const kBefore = reservesBefore.reserveA.mul(reservesBefore.reserveB);

      await simpleDEX.connect(user2).swap(tokenA.address, swapAmount);

      const reservesAfter = await simpleDEX.getReserves();
      const kAfter = reservesAfter.reserveA.mul(reservesAfter.reserveB);

      // K should be approximately equal (allowing for rounding errors)
      expect(kAfter).to.be.closeTo(kBefore, 1000000000000000000); // Within 1e18 (1 token worth)
    });
  });

  describe("Removing Liquidity", function () {
    beforeEach(async function () {
      // Add liquidity
      await tokenA.transfer(user1.address, ethers.utils.parseEther("1000"));
      await tokenB.transfer(user1.address, ethers.utils.parseEther("1000"));
      await tokenA.connect(user1).approve(simpleDEX.address, ethers.constants.MaxUint256);
      await tokenB.connect(user1).approve(simpleDEX.address, ethers.constants.MaxUint256);

      await simpleDEX.connect(user1).addLiquidity(
        ethers.utils.parseEther("100"),
        ethers.utils.parseEther("200")
      );

      const liquidityInfo = await simpleDEX.getLiquidityInfo(user1.address);
      user1Liquidity = liquidityInfo.liquidityAmount;
    });

    let user1Liquidity;

    it("User can remove liquidity", async function () {
      const amountToRemove = user1Liquidity.div(2);

      const reservesBefore = await simpleDEX.getReserves();

      await simpleDEX.connect(user1).removeLiquidity(amountToRemove);

      const reservesAfter = await simpleDEX.getReserves();
      const user1BalanceA = await tokenA.balanceOf(user1.address);
      const user1BalanceB = await tokenB.balanceOf(user1.address);

      expect(user1BalanceA).to.be.gt(0);
      expect(user1BalanceB).to.be.gt(0);
      expect(reservesAfter.reserveA).to.be.lt(reservesBefore.reserveA);
      expect(reservesAfter.reserveB).to.be.lt(reservesBefore.reserveB);
    });

    it("Cannot remove more liquidity than owned", async function () {
      const excessLiquidity = user1Liquidity.mul(2);

      await expect(
        simpleDEX.connect(user1).removeLiquidity(excessLiquidity)
      ).to.be.revertedWith("Insufficient liquidity");
    });

    it("Should emit RemoveLiquidity event", async function () {
      const amountToRemove = user1Liquidity.div(2);

      await expect(simpleDEX.connect(user1).removeLiquidity(amountToRemove))
        .to.emit(simpleDEX, "RemoveLiquidity")
        .withArgs(user1.address, ethers.utils.parseEther("50"), ethers.utils.parseEther("100"), amountToRemove);
    });
  });

  describe("Price Functions", function () {
    beforeEach(async function () {
      // Add liquidity
      await tokenA.transfer(user1.address, ethers.utils.parseEther("1000"));
      await tokenB.transfer(user1.address, ethers.utils.parseEther("1000"));
      await tokenA.connect(user1).approve(simpleDEX.address, ethers.constants.MaxUint256);
      await tokenB.connect(user1).approve(simpleDEX.address, ethers.constants.MaxUint256);

      await simpleDEX.connect(user1).addLiquidity(
        ethers.utils.parseEther("100"),
        ethers.utils.parseEther("200")
      );
    });

    it("Should return correct price for token A", async function () {
      const priceA = await simpleDEX.getPriceA();
      // Price should be approximately 2 (200 B / 100 A)
      expect(priceA).to.be.closeTo(ethers.utils.parseEther("2"), ethers.utils.parseEther("0.1"));
    });

    it("Should return correct price for token B", async function () {
      const priceB = await simpleDEX.getPriceB();
      // Price should be approximately 0.5 (100 A / 200 B)
      expect(priceB).to.be.closeTo(ethers.utils.parseEther("0.5"), ethers.utils.parseEther("0.1"));
    });

    it("Should calculate amount out correctly", async function () {
      const amountIn = ethers.utils.parseEther("10");
      const amountOut = await simpleDEX.getAmountOut(
        amountIn,
        ethers.utils.parseEther("100"),
        ethers.utils.parseEther("200")
      );

      // Should be less than 20 due to 0.3% fee
      expect(amountOut).to.be.gt(0);
      expect(amountOut).to.be.lt(ethers.utils.parseEther("20"));
    });
  });

  describe("View Functions", function () {
    beforeEach(async function () {
      // Add liquidity
      await tokenA.transfer(user1.address, ethers.utils.parseEther("1000"));
      await tokenB.transfer(user1.address, ethers.utils.parseEther("1000"));
      await tokenA.connect(user1).approve(simpleDEX.address, ethers.constants.MaxUint256);
      await tokenB.connect(user1).approve(simpleDEX.address, ethers.constants.MaxUint256);

      await simpleDEX.connect(user1).addLiquidity(
        ethers.utils.parseEther("100"),
        ethers.utils.parseEther("200")
      );
    });

    it("Should return liquidity info correctly", async function () {
      const liquidityInfo = await simpleDEX.getLiquidityInfo(user1.address);

      expect(liquidityInfo.liquidityAmount).to.be.gt(0);
      expect(liquidityInfo.sharePercentage).to.equal(10000); // 100% (basis points)
    });

    it("Should return reserves as tuple", async function () {
      const [reserveA, reserveB] = await simpleDEX.getReservesTuple();
      expect(reserveA).to.equal(ethers.utils.parseEther("100"));
      expect(reserveB).to.equal(ethers.utils.parseEther("200"));
    });
  });

  describe("Emergency Recovery", function () {
    it("Owner can recover non-pool tokens", async function () {
      const TestToken = await ethers.getContractFactory("ERC20TestToken");
      const testToken = await TestToken.deploy("Test", "TST", INITIAL_SUPPLY);
      await testToken.transfer(simpleDEX.address, ethers.utils.parseEther("1000"));

      const ownerBalanceBefore = await testToken.balanceOf(owner.address);

      await simpleDEX.emergencyTokenRecovery(testToken.address, ethers.utils.parseEther("500"));

      const ownerBalanceAfter = await testToken.balanceOf(owner.address);
      expect(ownerBalanceAfter.sub(ownerBalanceBefore)).to.equal(ethers.utils.parseEther("500"));
    });

    it("Owner cannot recover pool tokens", async function () {
      await expect(
        simpleDEX.emergencyTokenRecovery(tokenA.address, ethers.utils.parseEther("100"))
      ).to.be.revertedWith("Cannot recover pool tokens");
    });

    it("Non-owner cannot recover tokens", async function () {
      await expect(
        simpleDEX.connect(user1).emergencyTokenRecovery(tokenA.address, ethers.utils.parseEther("100"))
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });
});
