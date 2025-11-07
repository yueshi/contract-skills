// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title StakingPool
 * @dev Staking pool for earning rewards
 * @notice Supports time-based reward distribution
 */
contract StakingPool is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // State variables
    IERC20 public immutable stakingToken;
    IERC20 public immutable rewardToken;

    uint256 public totalStaked;
    uint256 public rewardRate; // Rewards per block
    uint256 public lastUpdateBlock;
    uint256 public rewardPerTokenStored;
    uint256 public constant REWARD_MULTIPLIER = 1e18;

    // User data
    mapping(address => uint256) public userStaked;
    mapping(address => uint256) public userRewardPerTokenPaid;
    mapping(address => uint256) public rewards;

    // Locking
    mapping(address => uint256) public lockEndTime;
    uint256 public constant MIN_LOCK_DURATION = 7 days;
    uint256 public constant MAX_LOCK_DURATION = 365 days;
    uint256 public constant LOCK_BOOST_PERIOD = 30 days; // 30 days for maximum boost

    // Events
    event Staked(address indexed user, uint256 amount, uint256 lockDuration);
    event Withdrawn(address indexed user, uint256 amount);
    event RewardPaid(address indexed user, uint256 reward);
    event RewardAdded(uint256 reward);
    event LockDurationUpdated(uint256 indexed user, uint256 lockEnd);

    // Modifiers
    modifier validAmount(uint256 amount) {
        require(amount > 0, "Amount must be > 0");
        _;
    }

    modifier updateReward(address account) {
        rewardPerTokenStored = rewardPerToken();
        lastUpdateBlock = block.number;

        if (account != address(0)) {
            rewards[account] = earned(account);
            userRewardPerTokenPaid[account] = rewardPerTokenStored;
        }
        _;
    }

    /**
     * @dev Constructor
     * @param stakingToken_ Address of staking token
     * @param rewardToken_ Address of reward token
     */
    constructor(address stakingToken_, address rewardToken_) validAmount(uint256(uint160(stakingToken_))) {
        require(stakingToken_ != address(0) && rewardToken_ != address(0), "Invalid token addresses");
        require(stakingToken_ != rewardToken_, "Tokens must be different");

        stakingToken = IERC20(stakingToken_);
        rewardToken = IERC20(rewardToken_);
        lastUpdateBlock = block.number;

        transferOwnership(msg.sender);
    }

    /**
     * @dev Stake tokens
     * @param amount Amount to stake
     * @param lockDuration Lock duration in seconds (0 for no lock)
     */
    function stake(uint256 amount, uint256 lockDuration)
        external
        nonReentrant
        updateReward(msg.sender)
        validAmount(amount)
    {
        require(lockDuration == 0 || (lockDuration >= MIN_LOCK_DURATION && lockDuration <= MAX_LOCK_DURATION), "Invalid lock duration");

        // Calculate lock end time
        uint256 newLockEnd = lockDuration > 0 ? block.timestamp + lockDuration : lockEndTime[msg.sender];
        if (lockDuration > 0 && newLockEnd > lockEndTime[msg.sender]) {
            lockEndTime[msg.sender] = newLockEnd;
            emit LockDurationUpdated(msg.sender, newLockEnd);
        }

        // Update staking data
        totalStaked += amount;
        userStaked[msg.sender] += amount;

        // Transfer tokens
        stakingToken.safeTransferFrom(msg.sender, address(this), amount);

        emit Staked(msg.sender, amount, lockDuration);
    }

    /**
     * @dev Withdraw staked tokens
     * @param amount Amount to withdraw
     */
    function withdraw(uint256 amount)
        external
        nonReentrant
        updateReward(msg.sender)
        validAmount(amount)
    {
        require(userStaked[msg.sender] >= amount, "Insufficient staked amount");

        // Check lock period
        if (lockEndTime[msg.sender] > block.timestamp) {
            require(amount <= userStaked[msg.sender] - _getLockedAmount(msg.sender), "Tokens are locked");
        }

        // Update staking data
        totalStaked -= amount;
        userStaked[msg.sender] -= amount;

        // Transfer tokens
        stakingToken.safeTransfer(msg.sender, amount);

        emit Withdrawn(msg.sender, amount);
    }

    /**
     * @dev Claim earned rewards
     */
    function getReward() external nonReentrant updateReward(msg.sender) {
        uint256 reward = rewards[msg.sender];
        if (reward > 0) {
            rewards[msg.sender] = 0;
            rewardToken.safeTransfer(msg.sender, reward);
            emit RewardPaid(msg.sender, reward);
        }
    }

    /**
     * @dev Exit (withdraw all and claim rewards)
     */
    function exit() external {
        uint256 amount = userStaked[msg.sender];
        withdraw(amount);
        getReward();
    }

    /**
     * @dev Calculate current rewards earned by user
     */
    function earned(address account) public view returns (uint256) {
        uint256 accountRewardPerToken = rewardPerTokenStored - userRewardPerTokenPaid[account];
        uint256 stakingAmount = userStaked[account];

        uint256 additionalReward = (stakingAmount * accountRewardPerToken) / REWARD_MULTIPLIER;
        uint256 boost = _getBoostMultiplier(account);

        return rewards[account] + (additionalReward * boost) / REWARD_MULTIPLIER;
    }

    /**
     * @dev Calculate current reward per token
     */
    function rewardPerToken() public view returns (uint256) {
        if (totalStaked == 0) {
            return rewardPerTokenStored;
        }

        uint256 blocksElapsed = block.number - lastUpdateBlock;
        uint256 rewardPerBlock = rewardRate;

        uint256 rewardAccrued = (blocksElapsed * rewardPerBlock * REWARD_MULTIPLIER) / totalStaked;
        return rewardPerTokenStored + rewardAccrued;
    }

    /**
     * @dev Get total staked for user
     */
    function getTotalStaked(address account) external view returns (uint256) {
        return userStaked[account];
    }

    /**
     * @dev Get locked amount for user
     */
    function getLockedAmount(address account) external view returns (uint256) {
        return _getLockedAmount(account);
    }

    /**
     * @dev Get lock end time for user
     */
    function getLockEnd(address account) external view returns (uint256) {
        return lockEndTime[account];
    }

    /**
     * @dev Get boost multiplier for user (0.5x to 2x based on lock time)
     */
    function getBoostMultiplier(address account) external view returns (uint256) {
        return _getBoostMultiplier(account);
    }

    // Admin functions

    /**
     * @dev Add reward to the pool
     * @param reward Amount of reward to add
     */
    function notifyReward(uint256 reward) external onlyOwner updateReward(address(0)) validAmount(reward) {
        require(reward > 0, "No reward");

        // Transfer reward tokens
        rewardToken.safeTransferFrom(msg.sender, address(this), reward);

        if (totalStaked > 0) {
            // Distribute over approximately 30 days (assuming 15s blocks)
            uint256 blocksIn30Days = (30 days) / 15;
            rewardRate = reward / blocksIn30Days;
        } else {
            rewardRate = 0;
        }

        emit RewardAdded(reward);
    }

    /**
     * @dev Set reward rate
     * @param newRewardRate New reward rate per block
     */
    function setRewardRate(uint256 newRewardRate) external onlyOwner {
        _accrueReward();
        rewardRate = newRewardRate;
    }

    /**
     * @dev Accrue reward (can be called by anyone)
     */
    function accrueReward() external {
        _accrueReward();
    }

    /**
     * @dev Emergency function to recover tokens (owner only)
     * @param token Address of token to recover
     * @param amount Amount to recover
     */
    function emergencyTokenRecovery(address token, uint256 amount) external onlyOwner {
        require(token != address(stakingToken) && token != address(rewardToken), "Cannot recover pool tokens");
        IERC20(token).safeTransfer(owner(), amount);
    }

    // Internal functions

    function _accrueReward() internal updateReward(address(0)) {}

    function _getLockedAmount(address account) internal view returns (uint256) {
        if (lockEndTime[account] <= block.timestamp) {
            return 0;
        }

        // Calculate locked portion based on lock duration
        uint256 lockTimeRemaining = lockEndTime[account] - block.timestamp;
        uint256 totalLockDuration = lockEndTime[account] - (lockEndTime[account] - MIN_LOCK_DURATION);

        if (totalLockDuration == 0) {
            return 0;
        }

        uint256 lockPercentage = (lockTimeRemaining * REWARD_MULTIPLIER) / totalLockDuration;
        return (userStaked[account] * lockPercentage) / REWARD_MULTIPLIER;
    }

    function _getBoostMultiplier(address account) internal view returns (uint256) {
        if (lockEndTime[account] <= block.timestamp) {
            return REWARD_MULTIPLIER; // No boost for unlocked tokens
        }

        uint256 lockTimeRemaining = lockEndTime[account] - block.timestamp;
        uint256 totalLockDuration = MAX_LOCK_DURATION;

        uint256 lockPercentage = (lockTimeRemaining * REWARD_MULTIPLIER) / totalLockDuration;

        // Boost ranges from 0.5x to 2x
        uint256 boostMultiplier = REWARD_MULTIPLIER + (lockPercentage * REWARD_MULTIPLIER);

        // Cap at 2x
        if (boostMultiplier > 2 * REWARD_MULTIPLIER) {
            boostMultiplier = 2 * REWARD_MULTIPLIER;
        }

        return boostMultiplier;
    }

    /**
     * @dev Get current block number (for testing)
     */
    function getCurrentBlock() external view returns (uint256) {
        return block.number;
    }
}
