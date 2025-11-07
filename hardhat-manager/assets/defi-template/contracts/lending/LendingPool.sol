// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title LendingPool
 * @dev Simple lending pool for depositing and borrowing tokens
 * @notice Interest model: Compound-like with variable rate
 */
contract LendingPool is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // State variables
    IERC20 public immutable underlying;
    uint256 public totalDeposits;
    uint256 public totalBorrows;

    // Interest parameters
    uint256 public constant BLOCKS_PER_YEAR = 2102400; // ~15 seconds per block
    uint256 public baseRate = 50000000000000000; // 5% base rate
    uint256 public multiplier = 100000000000000000; // 10% multiplier
    uint256 public utilizationOptimal = 800000000000000000; // 80% optimal utilization
    uint256 public constant RATE_MULTIPLIER = 1e18;

    // Accrual
    uint256 public borrowIndex = 1e18;
    uint256 public lastUpdateBlock;

    // User data
    mapping(address => uint256) public accountBorrows;
    mapping(address => uint256) public borrowIndices;
    mapping(address => uint256) public deposits;

    // Events
    event Deposit(address indexed user, uint256 amount, uint256 shares);
    event Withdraw(address indexed user, uint256 amount);
    event Borrow(address indexed user, uint256 amount, uint256 newTotalBorrows);
    event Repay(address indexed user, uint256 amount, uint256 remainingBorrows);
    event InterestAccrued(uint256 newBorrowIndex, uint256 newTotalBorrows);

    // Modifiers
    modifier validAmount(uint256 amount) {
        require(amount > 0, "Amount must be > 0");
        _;
    }

    /**
     * @dev Constructor
     * @param underlying_ Address of underlying token
     */
    constructor(address underlying_) validAmount(uint256(uint160(underlying_))) {
        require(underlying_ != address(0), "Invalid underlying token");
        underlying = IERC20(underlying_);
        lastUpdateBlock = block.number;
        transferOwnership(msg.sender);
    }

    /**
     * @dev Deposit tokens to earn interest
     * @param amount Amount to deposit
     */
    function deposit(uint256 amount)
        external
        nonReentrant
        validAmount(amount)
    {
        _accrueInterest();

        // Calculate shares based on current exchange rate
        uint256 shares = _calculateShares(amount);

        // Update state
        deposits[msg.sender] += shares;
        totalDeposits += amount;

        // Transfer tokens
        underlying.safeTransferFrom(msg.sender, address(this), amount);

        emit Deposit(msg.sender, amount, shares);
    }

    /**
     * @dev Withdraw deposited tokens
     * @param shares Amount of shares to withdraw
     */
    function withdraw(uint256 shares)
        external
        nonReentrant
        validAmount(shares)
    {
        _accrueInterest();

        require(deposits[msg.sender] >= shares, "Insufficient deposits");

        // Calculate amount to withdraw
        uint256 amount = _calculateAmountFromShares(shares);

        require(totalDeposits >= amount, "Insufficient pool liquidity");

        // Update state
        deposits[msg.sender] -= shares;
        totalDeposits -= amount;

        // Transfer tokens
        underlying.safeTransfer(msg.sender, amount);

        emit Withdraw(msg.sender, amount);
    }

    /**
     * @dev Borrow tokens
     * @param amount Amount to borrow
     */
    function borrow(uint256 amount)
        external
        nonReentrant
        validAmount(amount)
    {
        _accrueInterest();

        require(amount <= getMaxBorrow(), "Insufficient pool liquidity");
        require(accountBorrows[msg.sender] == 0, "Already has borrow position"); // Simplified: one borrow per user

        // Update borrow data
        accountBorrows[msg.sender] = amount;
        borrowIndices[msg.sender] = borrowIndex;
        totalBorrows += amount;

        // Transfer tokens
        underlying.safeTransfer(msg.sender, amount);

        emit Borrow(msg.sender, amount, totalBorrows);
    }

    /**
     * @dev Repay borrowed tokens
     * @param amount Amount to repay
     */
    function repay(uint256 amount)
        external
        nonReentrant
        validAmount(amount)
    {
        _accrueInterest();

        uint256 borrowedAmount = _calculateBorrowedAmount(msg.sender);
        require(borrowedAmount > 0, "No borrow to repay");

        uint256 repayAmount = amount > borrowedAmount ? borrowedAmount : amount;

        // Transfer tokens
        underlying.safeTransferFrom(msg.sender, address(this), repayAmount);

        // Update borrow data
        accountBorrows[msg.sender] = borrowedAmount - repayAmount;
        totalBorrows -= repayAmount;

        // If fully repaid, reset borrow index
        if (accountBorrows[msg.sender] == 0) {
            borrowIndices[msg.sender] = 0;
        }

        emit Repay(msg.sender, repayAmount, accountBorrows[msg.sender]);
    }

    /**
     * @dev Calculate current borrow rate
     */
    function getBorrowRate() public view returns (uint256) {
        uint256 utilization = getUtilization();

        if (utilization <= utilizationOptimal) {
            // Base rate + utilization * multiplier
            return baseRate + (utilization * multiplier) / RATE_MULTIPLIER;
        } else {
            // Beyond optimal: exponential increase
            uint256 excess = utilization - utilizationOptimal;
            uint256 excessRate = baseRate + multiplier + (excess * multiplier) / RATE_MULTIPLIER;
            return excessRate;
        }
    }

    /**
     * @dev Calculate current supply rate
     */
    function getSupplyRate() external view returns (uint256) {
        uint256 borrowRate = getBorrowRate();
        uint256 utilization = getUtilization();
        return (borrowRate * utilization) / RATE_MULTIPLIER;
    }

    /**
     * @dev Calculate utilization ratio
     */
    function getUtilization() public view returns (uint256) {
        if (totalDeposits == 0) return 0;
        return (totalBorrows * RATE_MULTIPLIER) / totalDeposits;
    }

    /**
     * @dev Get maximum borrowable amount for user
     */
    function getMaxBorrow() public view returns (uint256) {
        // Simplified: 50% collateral ratio
        uint256 maxBorrow = (totalDeposits * 5000) / 10000;
        return maxBorrow > totalBorrows ? maxBorrow - totalBorrows : 0;
    }

    /**
     * @dev Get user's current borrow position
     */
    function getUserBorrow(address user) external view returns (uint256) {
        return _calculateBorrowedAmount(user);
    }

    /**
     * @dev Get user's deposit shares
     */
    function getUserDeposits(address user) external view returns (uint256) {
        return deposits[user];
    }

    /**
     * @dev Accrue interest to update borrow index
     */
    function accrueInterest() external {
        _accrueInterest();
    }

    // Internal functions

    function _accrueInterest() internal {
        uint256 currentBlock = block.number;
        uint256 blocksElapsed = currentBlock - lastUpdateBlock;

        if (blocksElapsed == 0) {
            return;
        }

        uint256 borrowRate = getBorrowRate();
        uint256 simpleInterestFactor = borrowRate * blocksElapsed;
        uint256 compoundInterestFactor = (borrowIndex * simpleInterestFactor) / (RATE_MULTIPLIER * BLOCKS_PER_YEAR);
        uint256 newBorrowIndex = borrowIndex + compoundInterestFactor;

        // Update total borrows with interest
        uint256 interestAccrued = (totalBorrows * compoundInterestFactor) / RATE_MULTIPLIER;
        totalBorrows += interestAccrued;

        // Update borrow index
        borrowIndex = newBorrowIndex;
        lastUpdateBlock = currentBlock;

        emit InterestAccrued(newBorrowIndex, totalBorrows);
    }

    function _calculateShares(uint256 amount) internal view returns (uint256) {
        if (totalDeposits == 0) {
            return amount; // First depositor gets 1:1 shares
        }
        return (amount * 1e18) / getExchangeRate();
    }

    function _calculateAmountFromShares(uint256 shares) internal view returns (uint256) {
        return (shares * getExchangeRate()) / 1e18;
    }

    function _calculateBorrowedAmount(address user) internal view returns (uint256) {
        uint256 borrowBalance = accountBorrows[user];
        uint256 userBorrowIndex = borrowIndices[user];

        if (borrowBalance == 0 || userBorrowIndex == 0) {
            return borrowBalance;
        }

        uint256 compoundFactor = (borrowIndex * RATE_MULTIPLIER) / userBorrowIndex;
        return (borrowBalance * compoundFactor) / RATE_MULTIPLIER;
    }

    function getExchangeRate() internal view returns (uint256) {
        if (totalDeposits == 0) {
            return 1e18;
        }
        return (totalDeposits * 1e18) / totalDeposits; // Simplified: 1:1 for deposit
    }

    // Admin functions

    /**
     * @dev Set interest rate parameters
     * @param baseRate_ New base rate
     * @param multiplier_ New multiplier
     * @param utilizationOptimal_ New optimal utilization
     */
    function setInterestRateParams(
        uint256 baseRate_,
        uint256 multiplier_,
        uint256 utilizationOptimal_
    ) external onlyOwner {
        require(baseRate_ <= 1e18, "Invalid base rate");
        require(multiplier_ <= 1e18, "Invalid multiplier");
        require(utilizationOptimal_ <= 1e18, "Invalid utilization");

        baseRate = baseRate_;
        multiplier = multiplier_;
        utilizationOptimal = utilizationOptimal_;
    }

    /**
     * @dev Emergency function to recover tokens (owner only)
     * @param token Address of token to recover
     * @param amount Amount to recover
     */
    function emergencyTokenRecovery(address token, uint256 amount) external onlyOwner {
        require(token != address(underlying), "Cannot recover underlying tokens");
        IERC20(token).safeTransfer(owner(), amount);
    }
}
