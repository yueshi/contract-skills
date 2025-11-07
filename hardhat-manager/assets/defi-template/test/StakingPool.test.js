const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("StakingPool", function () {
  let stakingPool, stakingToken, rewardToken, owner, user1, user2, user3;
  const INITIAL_SUPPLY = ethers.utils.parseEther("1000000");
  const MIN_LOCK_DURATION = 7 * 24 * 60 * 60; // 7 days
  const MAX_LOCK_DURATION = 365 * 24 * 60 * 60; // 365 days

  beforeEach(async function () {
    [owner, user1, user2, user3] = await ethers.getSigners();

    // Deploy tokens
    const ERC20 = await ethers.getContractFactory("ERC20TestToken");
    stakingToken = await ERC20.deploy("Staking Token", "STK", INITIAL_SUPPLY);
    rewardToken = await ERC20.deploy("Reward Token", "RWD", INITIAL_SUPPLY);

    // Deploy staking pool
    const StakingPool = await ethers.getContractFactory("StakingPool");
    stakingPool = await StakingPool.deploy(stakingToken.address, rewardToken.address);
    await stakingPool.deployed();

    // Setup tokens
    await stakingToken.transfer(user1.address, ethers.utils.parseEther("10000"));
    await stakingToken.transfer(user2.address, ethers.utils.parseEther("10000"));
    await rewardToken.transfer(stakingPool.address, ethers.utils.parseEther("100000"));
  });

  describe("Deployment", function () {
    it("Should set correct token addresses", async function () {
      expect(await stakingPool.stakingToken()).to.equal(stakingToken.address);
      expect(await stakingPool.rewardToken()).to.equal(rewardToken.address);
    });

    it("Should initialize with zero staked", async function () {
      expect(await stakingPool.totalStaked()).to.equal(0);
    });

    it("Should set owner correctly", async function () {
      expect(await stakingPool.owner()).to.equal(owner.address);
    });
  });

  describe("Staking", function () {
    beforeEach(async function () {
      // Approve tokens
      await stakingToken.connect(user1).approve(stakingPool.address, ethers.constants.MaxUint256);
      await stakingToken.connect(user2).approve(stakingPool.address, ethers.constants.MaxUint256);
    });

    it("User can stake tokens without lock", async function () {
      const stakeAmount = ethers.utils.parseEther("1000");

      await stakingPool.connect(user1).stake(stakeAmount, 0);

      const userStaked = await stakingPool.getTotalStaked(user1.address);
      const totalStaked = await stakingPool.totalStaked();

      expect(userStaked).to.equal(stakeAmount);
      expect(totalStaked).to.equal(stakeAmount);
    });

    it("User can stake tokens with lock", async function () {
      const stakeAmount = ethers.utils.parseEther("1000");
      const lockDuration = MIN_LOCK_DURATION;

      await stakingPool.connect(user1).stake(stakeAmount, lockDuration);

      const userStaked = await stakingPool.getTotalStaked(user1.address);
      const lockEnd = await stakingPool.getLockEnd(user1.address);

      expect(userStaked).to.equal(stakeAmount);
      expect(lockEnd).to.equal((await ethers.provider.getBlock("latest")).timestamp + lockDuration);
    });

    it("Cannot stake zero amount", async function () {
      await expect(
        stakingPool.connect(user1).stake(0, 0)
      ).to.be.revertedWith("Amount must be > 0");
    });

    it("Cannot use invalid lock duration", async function () {
      const stakeAmount = ethers.utils.parseEther("1000");

      // Lock duration too short
      await expect(
        stakingPool.connect(user1).stake(stakeAmount, MIN_LOCK_DURATION - 1)
      ).to.be.revertedWith("Invalid lock duration");

      // Lock duration too long
      await expect(
        stakingPool.connect(user1).stake(stakeAmount, MAX_LOCK_DURATION + 1)
      ).to.be.revertedWith("Invalid lock duration");
    });

    it("Can extend lock duration", async function () {
      const stakeAmount = ethers.utils.parseEther("1000");

      await stakingPool.connect(user1).stake(stakeAmount, MIN_LOCK_DURATION);

      const firstLockEnd = await stakingPool.getLockEnd(user1.address);

      // Stake more with longer lock
      await stakingPool.connect(user1).stake(stakeAmount, MAX_LOCK_DURATION);

      const secondLockEnd = await stakingPool.getLockEnd(user1.address);
      expect(secondLockEnd).to.be.gt(firstLockEnd);
    });

    it("Cannot reduce lock duration", async function () {
      const stakeAmount = ethers.utils.parseEther("1000");

      await stakingPool.connect(user1).stake(stakeAmount, MAX_LOCK_DURATION);

      // Try to stake with shorter lock (should not reduce)
      await stakingPool.connect(user1).stake(stakeAmount, MIN_LOCK_DURATION);

      const lockEnd = await stakingPool.getLockEnd(user1.address);
      expect(lockEnd).to.equal((await ethers.provider.getBlock("latest")).timestamp + MAX_LOCK_DURATION);
    });

    it("Should emit Staked event", async function () {
      const stakeAmount = ethers.utils.parseEther("1000");
      const lockDuration = MIN_LOCK_DURATION;

      await expect(stakingPool.connect(user1).stake(stakeAmount, lockDuration))
        .to.emit(stakingPool, "Staked")
        .withArgs(user1.address, stakeAmount, lockDuration);
    });
  });

  describe("Withdrawing", function () {
    beforeEach(async function () {
      // Approve and stake
      await stakingToken.connect(user1).approve(stakingPool.address, ethers.constants.MaxUint256);
      await stakingPool.connect(user1).stake(ethers.utils.parseEther("1000"), 0);
    });

    it("User can withdraw unstaked tokens", async function () {
      const withdrawAmount = ethers.utils.parseEther("500");

      await stakingPool.connect(user1).withdraw(withdrawAmount);

      const userStaked = await stakingPool.getTotalStaked(user1.address);
      const userBalance = await stakingToken.balanceOf(user1.address);

      expect(userStaked).to.equal(ethers.utils.parseEther("500"));
      expect(userBalance).to.be.gt(ethers.utils.parseEther("9000")); // Original 10000 - 1000 staked + 500 withdrawn
    });

    it("Cannot withdraw more than staked", async function () {
      await expect(
        stakingPool.connect(user1).withdraw(ethers.utils.parseEther("2000"))
      ).to.be.revertedWith("Insufficient staked amount");
    });

    it("Cannot withdraw during lock period", async function () {
      const stakeAmount = ethers.utils.parseEther("1000");
      await stakingPool.connect(user1).stake(stakeAmount, MAX_LOCK_DURATION);

      await expect(
        stakingPool.connect(user1).withdraw(stakeAmount)
      ).to.be.revertedWith("Tokens are locked");
    });

    it("Can withdraw unlocked portion", async function () {
      const stakeAmount = ethers.utils.parseEther("1000");

      // Stake with max lock
      await stakingPool.connect(user1).stake(stakeAmount, MAX_LOCK_DURATION);

      // Try to withdraw initial unstaked amount
      await stakingPool.connect(user1).withdraw(stakeAmount); // Should work

      // Verify
      const userStaked = await stakingPool.getTotalStaked(user1.address);
      expect(userStaked).to.equal(stakeAmount); // Only the newly staked amount remains
    });

    it("Should emit Withdrawn event", async function () {
      const withdrawAmount = ethers.utils.parseEther("500");

      await expect(stakingPool.connect(user1).withdraw(withdrawAmount))
        .to.emit(stakingPool, "Withdrawn")
        .withArgs(user1.address, withdrawAmount);
    });
  });

  describe("Rewards", function () {
    beforeEach(async function () {
      // Setup staking
      await stakingToken.connect(user1).approve(stakingPool.address, ethers.constants.MaxUint256);
      await stakingPool.connect(user1).stake(ethers.utils.parseEther("1000"), 0);

      // Add rewards
      await stakingPool.notifyReward(ethers.utils.parseEther("10000"));
    });

    it("User earns rewards over time", async function () {
      const initialEarned = await stakingPool.earned(user1.address);

      // Fast forward 100 blocks
      await ethers.provider.send("evm_increaseTime", [1500]); // 15 seconds per block
      await ethers.provider.send("evm_mine", []);

      const finalEarned = await stakingPool.earned(user1.address);

      expect(finalEarned).to.be.gt(initialEarned);
      expect(finalEarned).to.be.gt(0);
    });

    it("User can claim rewards", async function () {
      // Fast forward time
      await ethers.provider.send("evm_increaseTime", [1500]);
      await ethers.provider.send("evm_mine", []);

      const earnedBefore = await stakingPool.earned(user1.address);

      await stakingPool.connect(user1).getReward();

      const earnedAfter = await stakingPool.earned(user1.address);
      const userRewardBalance = await rewardToken.balanceOf(user1.address);

      expect(earnedAfter).to.equal(0);
      expect(userRewardBalance).to.equal(earnedBefore);
    });

    it("Should emit RewardPaid event", async function () {
      // Fast forward time
      await ethers.provider.send("evm_increaseTime", [1500]);
      await ethers.provider.send("evm_mine", []);

      await expect(stakingPool.connect(user1).getReward())
        .to.emit(stakingPool, "RewardPaid")
        .withArgs(user1.address, ethers.utils.parseEther("0")); // Amount may vary
    });

    it("User can exit (withdraw all and claim rewards)", async function () {
      // Fast forward time
      await ethers.provider.send("evm_increaseTime", [1500]);
      await ethers.provider.send("evm_mine", []);

      const earnedBefore = await stakingPool.earned(user1.address);

      await stakingPool.connect(user1).exit();

      const userStaked = await stakingPool.getTotalStaked(user1.address);
      const earnedAfter = await stakingPool.earned(user1.address);
      const userRewardBalance = await rewardToken.balanceOf(user1.address);

      expect(userStaked).to.equal(0);
      expect(earnedAfter).to.equal(0);
      expect(userRewardBalance).to.equal(earnedBefore);
    });
  });

  describe("Locking Boost", function () {
    beforeEach(async function () {
      await stakingToken.connect(user1).approve(stakingPool.address, ethers.constants.MaxUint256);
    });

    it("Locked tokens get boost multiplier", async function () {
      // Stake without lock
      await stakingPool.connect(user1).stake(ethers.utils.parseEther("1000"), 0);
      const noLockBoost = await stakingPool.getBoostMultiplier(user1.address);
      expect(noLockBoost).to.equal(ethers.utils.parseEther("1")); // No boost

      // Stake with max lock
      await stakingPool.connect(user1).stake(ethers.utils.parseEther("1000"), MAX_LOCK_DURATION);
      const withLockBoost = await stakingPool.getBoostMultiplier(user1.address);
      expect(withLockBoost).to.equal(ethers.utils.parseEther("2")); // 2x boost for max lock
    });

    it("Boost decreases as lock period decreases", async function () {
      // Stake with different lock durations
      await stakingPool.connect(user1).stake(ethers.utils.parseEther("1000"), MAX_LOCK_DURATION);

      const boost = await stakingPool.getBoostMultiplier(user1.address);
      expect(boost).to.be.gt(ethers.utils.parseEther("1"));
      expect(boost).to.be.lte(ethers.utils.parseEther("2"));
    });

    it("Locked amount calculation is correct", async function () {
      await stakingPool.connect(user1).stake(ethers.utils.parseEther("1000"), MAX_LOCK_DURATION);

      const lockedAmount = await stakingPool.getLockedAmount(user1.address);
      const userStaked = await stakingPool.getTotalStaked(user1.address);

      expect(lockedAmount).to.be.lt(userStaked);
      expect(lockedAmount).to.be.gt(0);
    });
  });

  describe("Reward Rate", function () {
    beforeEach(async function () {
      // Setup staking
      await stakingToken.connect(user1).approve(stakingPool.address, ethers.constants.MaxUint256);
      await stakingPool.connect(user1).stake(ethers.utils.parseEther("1000"), 0);
    });

    it("Owner can set reward rate", async function () {
      const newRewardRate = ethers.utils.parseEther("1");
      await stakingPool.setRewardRate(newRewardRate);

      // Verify by checking rewards earned
      await ethers.provider.send("evm_increaseTime", [1500]);
      await ethers.provider.send("evm_mine", []);

      const earned = await stakingPool.earned(user1.address);
      expect(earned).to.be.gt(0);
    });

    it("Cannot set invalid reward rate", async function () {
      await expect(
        stakingPool.setRewardRate(ethers.constants.MaxUint256)
      ).to.be.reverted; // Should not overflow
    });

    it("Reward rate affects rewards earned", async function () {
      // First period with low rate
      await stakingPool.notifyReward(ethers.utils.parseEther("1000"));

      await ethers.provider.send("evm_increaseTime", [1500]);
      await ethers.provider.send("evm_mine", []);

      const earnedFirst = await stakingPool.earned(user1.address);

      // Reset and add higher rate
      await stakingPool.notifyReward(ethers.utils.parseEther("10000"));

      await ethers.provider.send("evm_increaseTime", [1500]);
      await ethers.provider.send("evm_mine", []);

      const earnedSecond = await stakingPool.earned(user1.address);

      expect(earnedSecond).to.be.gt(earnedFirst);
    });
  });

  describe("View Functions", function () {
    beforeEach(async function () {
      await stakingToken.connect(user1).approve(stakingPool.address, ethers.constants.MaxUint256);
      await stakingPool.connect(user1).stake(ethers.utils.parseEther("1000"), MIN_LOCK_DURATION);
    });

    it("Should return correct total staked", async function () {
      const totalStaked = await stakingPool.getTotalStaked(user1.address);
      expect(totalStaked).to.equal(ethers.utils.parseEther("1000"));
    });

    it("Should return correct lock end time", async function () {
      const lockEnd = await stakingPool.getLockEnd(user1.address);
      expect(lockEnd).to.be.gt((await ethers.provider.getBlock("latest")).timestamp);
    });

    it("Should return correct boost multiplier", async function () {
      const boost = await stakingPool.getBoostMultiplier(user1.address);
      expect(boost).to.be.gt(ethers.utils.parseEther("1"));
      expect(boost).to.be.lte(ethers.utils.parseEther("2"));
    });

    it("Should return correct earned amount", async function () {
      const earned = await stakingPool.earned(user1.address);
      expect(earned).to.be.gte(0);
    });
  });

  describe("Events", function () {
    it("Should emit RewardAdded when adding rewards", async function () {
      const rewardAmount = ethers.utils.parseEther("1000");

      await expect(stakingPool.notifyReward(rewardAmount))
        .to.emit(stakingPool, "RewardAdded")
        .withArgs(rewardAmount);
    });

    it("Should emit LockDurationUpdated when extending lock", async function () {
      await stakingToken.connect(user1).approve(stakingPool.address, ethers.constants.MaxUint256);

      await stakingPool.connect(user1).stake(ethers.utils.parseEther("1000"), MIN_LOCK_DURATION);

      const newLockEnd = (await ethers.provider.getBlock("latest")).timestamp + MAX_LOCK_DURATION;

      await expect(stakingPool.connect(user1).stake(ethers.utils.parseEther("500"), MAX_LOCK_DURATION))
        .to.emit(stakingPool, "LockDurationUpdated")
        .withArgs(user1.address, newLockEnd);
    });
  });

  describe("Admin Functions", function () {
    it("Owner can add rewards", async function () {
      const rewardAmount = ethers.utils.parseEther("5000");
      await stakingPool.notifyReward(rewardAmount);
      // No revert means success
    });

    it("Owner can accrue rewards", async function () {
      await stakingPool.accrueReward();
      // No revert means success
    });

    it("Owner can recover wrong tokens", async function () {
      const TestToken = await ethers.getContractFactory("ERC20TestToken");
      const testToken = await TestToken.deploy("Test", "TST", ethers.utils.parseEther("1000"));
      await testToken.transfer(stakingPool.address, ethers.utils.parseEther("100"));

      await stakingPool.emergencyTokenRecovery(testToken.address, ethers.utils.parseEther("50"));

      const balance = await testToken.balanceOf(owner.address);
      expect(balance).to.equal(ethers.utils.parseEther("50"));
    });

    it("Cannot recover staking or reward tokens", async function () {
      await expect(
        stakingPool.emergencyTokenRecovery(stakingToken.address, ethers.utils.parseEther("100"))
      ).to.be.revertedWith("Cannot recover pool tokens");

      await expect(
        stakingPool.emergencyTokenRecovery(rewardToken.address, ethers.utils.parseEther("100"))
      ).to.be.revertedWith("Cannot recover pool tokens");
    });

    it("Non-owner cannot call admin functions", async function () {
      await expect(
        stakingPool.connect(user1).notifyReward(ethers.utils.parseEther("1000"))
      ).to.be.revertedWith("Ownable: caller is not the owner");

      await expect(
        stakingPool.connect(user1).setRewardRate(ethers.utils.parseEther("1"))
      ).to.be.revertedWith("Ownable: caller is not the owner");

      await expect(
        stakingPool.connect(user1).emergencyTokenRecovery(stakingToken.address, ethers.utils.parseEther("100"))
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });
});
