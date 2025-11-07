// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title SimpleDEX
 * @dev Automated Market Maker (AMM) implementation
 * @notice Supports token swaps with constant product formula (x * y = k)
 */
contract SimpleDEX is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // State variables
    IERC20 public immutable tokenA;
    IERC20 public immutable tokenB;

    uint256 public reserveA;
    uint256 public reserveB;
    uint256 public totalLiquidity;
    uint256 public constant MINIMUM_LIQUIDITY = 1000;

    // LP token
    string public lpTokenName = "SimpleDEX LP Token";
    string public lpTokenSymbol = "SDLP";

    // Mappings
    mapping(address => uint256) public liquidity;
    mapping(address => mapping(address => uint256)) public allowances;

    // Events
    event AddLiquidity(
        address indexed provider,
        uint256 amountA,
        uint256 amountB,
        uint256 liquidityMinted
    );
    event RemoveLiquidity(
        address indexed provider,
        uint256 amountA,
        uint256 amountB,
        uint256 liquidityBurned
    );
    event Swap(
        address indexed trader,
        address tokenIn,
        uint256 amountIn,
        address tokenOut,
        uint256 amountOut
    );
    event Sync(uint256 reserveA, uint256 reserveB);

    // Modifiers
    modifier validAddress(address addr) {
        require(addr != address(0), "Invalid address");
        _;
    }

    modifier validAmount(uint256 amount) {
        require(amount > 0, "Amount must be > 0");
        _;
    }

    /**
     * @dev Constructor
     * @param tokenA_ Address of token A
     * @param tokenB_ Address of token B
     */
    constructor(address tokenA_, address tokenB_) validAddress(tokenA_) validAddress(tokenB_) {
        require(tokenA_ != tokenB_, "Tokens must be different");
        tokenA = IERC20(tokenA_);
        tokenB = IERC20(tokenB_);
        transferOwnership(msg.sender);
    }

    /**
     * @dev Add liquidity to the pool
     * @param amountA Amount of token A to add
     * @param amountB Amount of token B to add
     */
    function addLiquidity(uint256 amountA, uint256 amountB)
        external
        nonReentrant
        validAmount(amountA)
        validAmount(amountB)
    {
        require(amountA > 0 && amountB > 0, "Invalid amounts");

        (uint256 _reserveA, uint256 _reserveB) = getReserves();

        if (totalLiquidity == 0) {
            // First liquidity provider
            uint256 liquidityMinted = _sqrt(amountA * amountB);

            require(liquidityMinted > MINIMUM_LIQUIDITY, "Insufficient liquidity");

            totalLiquidity = liquidityMinted - MINIMUM_LIQUIDITY;
            liquidity[msg.sender] = totalLiquidity;

            // Mint LP tokens (simplified - no actual LP token contract)
            _mintLP(msg.sender, totalLiquidity);
        } else {
            // Calculate amounts based on ratio
            require(
                amountA * _reserveB >= amountB * _reserveA,
                "Incorrect token ratio"
            );

            uint256 liquidityMinted = (amountA * totalLiquidity) / _reserveA;
            uint256 liquidityMintedB = (amountB * totalLiquidity) / _reserveB;
            uint256 actualLiquidityMinted = liquidityMinted < liquidityMintedB
                ? liquidityMinted
                : liquidityMintedB;

            require(actualLiquidityMinted > 0, "Insufficient liquidity minted");

            totalLiquidity += actualLiquidityMinted;
            liquidity[msg.sender] += actualLiquidityMinted;

            _mintLP(msg.sender, actualLiquidityMinted);
        }

        // Transfer tokens
        tokenA.safeTransferFrom(msg.sender, address(this), amountA);
        tokenB.safeTransferFrom(msg.sender, address(this), amountB);

        _update(amountA, amountB);

        emit AddLiquidity(msg.sender, amountA, amountB, liquidity[msg.sender]);
    }

    /**
     * @dev Remove liquidity from the pool
     * @param liquidityAmount Amount of LP tokens to burn
     */
    function removeLiquidity(uint256 liquidityAmount)
        external
        nonReentrant
        validAmount(liquidityAmount)
    {
        require(liquidity[msg.sender] >= liquidityAmount, "Insufficient liquidity");

        (uint256 _reserveA, uint256 _reserveB) = getReserves();

        uint256 amountA = (liquidityAmount * _reserveA) / totalLiquidity;
        uint256 amountB = (liquidityAmount * _reserveB) / totalLiquidity;

        liquidity[msg.sender] -= liquidityAmount;
        totalLiquidity -= liquidityAmount;

        _burnLP(msg.sender, liquidityAmount);

        // Transfer tokens
        tokenA.safeTransfer(msg.sender, amountA);
        tokenB.safeTransfer(msg.sender, amountB);

        _update(_reserveA - amountA, _reserveB - amountB);

        emit RemoveLiquidity(msg.sender, amountA, amountB, liquidityAmount);
    }

    /**
     * @dev Swap tokens
     * @param tokenIn Address of input token
     * @param amountIn Amount of input tokens
     */
    function swap(address tokenIn, uint256 amountIn)
        external
        nonReentrant
        validAmount(amountIn)
        returns (uint256 amountOut)
    {
        require(tokenIn == address(tokenA) || tokenIn == address(tokenB), "Invalid token");

        (address tokenOut, uint256 _reserveIn, uint256 _reserveOut) = getInputOutput(tokenIn);

        require(_reserveIn > 0 && _reserveOut > 0, "Insufficient reserves");

        // Calculate output amount with 0.3% fee
        uint256 amountInWithFee = (amountIn * 997) / 1000;
        amountOut = (_reserveOut * amountInWithFee) / (_reserveIn + amountInWithFee);

        require(amountOut > 0, "Insufficient output amount");
        require(amountOut < _reserveOut, "Insufficient pool liquidity");

        // Transfer input tokens
        IERC20(tokenIn).safeTransferFrom(msg.sender, address(this), amountIn);

        // Transfer output tokens
        IERC20(tokenOut).safeTransfer(msg.sender, amountOut);

        _update(getReserves().reserveA, getReserves().reserveB);

        emit Swap(msg.sender, tokenIn, amountIn, tokenOut, amountOut);
    }

    /**
     * @dev Get price of token A in terms of token B
     */
    function getPriceA() external view returns (uint256) {
        (uint256 _reserveA, uint256 _reserveB) = getReserves();
        require(_reserveB > 0, "Insufficient reserves");
        return (_reserveB * 1e18) / _reserveA;
    }

    /**
     * @dev Get price of token B in terms of token A
     */
    function getPriceB() external view returns (uint256) {
        (uint256 _reserveA, uint256 _reserveB) = getReserves();
        require(_reserveA > 0, "Insufficient reserves");
        return (_reserveA * 1e18) / _reserveB;
    }

    /**
     * @dev Get amount out for a given input
     * @param amountIn Input amount
     * @param reserveIn Input reserve
     * @param reserveOut Output reserve
     */
    function getAmountOut(uint256 amountIn, uint256 reserveIn, uint256 reserveOut)
        external
        pure
        returns (uint256 amountOut)
    {
        require(amountIn > 0, "Amount must be > 0");
        require(reserveIn > 0 && reserveOut > 0, "Insufficient reserves");

        uint256 amountInWithFee = (amountIn * 997) / 1000;
        uint256 numerator = amountInWithFee * reserveOut;
        uint256 denominator = reserveIn * 1000 + amountInWithFee;
        amountOut = numerator / denominator;

        return amountOut;
    }

    /**
     * @dev Get reserves
     */
    function getReserves() public view returns (uint256, uint256) {
        return (reserveA, reserveB);
    }

    /**
     * @dev Get liquidity info
     */
    function getLiquidityInfo(address provider) external view returns (
        uint256 liquidityAmount,
        uint256 sharePercentage
    ) {
        liquidityAmount = liquidity[provider];
        sharePercentage = totalLiquidity > 0
            ? (liquidityAmount * 10000) / totalLiquidity
            : 0;
    }

    /**
     * @dev Emergency function to recover tokens (owner only)
     * @param token Address of token to recover
     * @param amount Amount to recover
     */
    function emergencyTokenRecovery(address token, uint256 amount) external onlyOwner {
        require(token != address(tokenA) && token != address(tokenB), "Cannot recover pool tokens");
        IERC20(token).safeTransfer(owner(), amount);
    }

    // Internal functions

    function _update(uint256 balanceA, uint256 balanceB) internal {
        require(balanceA <= type(uint112).max && balanceB <= type(uint112).max, "Overflow");

        reserveA = uint112(balanceA);
        reserveB = uint112(balanceB);

        emit Sync(reserveA, reserveB);
    }

    function getInputOutput(address tokenIn) internal view returns (
        address tokenOut,
        uint256 reserveIn,
        uint256 reserveOut
    ) {
        if (tokenIn == address(tokenA)) {
            tokenOut = address(tokenB);
            reserveIn = reserveA;
            reserveOut = reserveB;
        } else {
            tokenOut = address(tokenA);
            reserveIn = reserveB;
            reserveOut = reserveA;
        }
    }

    function _sqrt(uint256 y) internal pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }

    // Simplified LP token management
    function _mintLP(address to, uint256 amount) internal {
        // In a real implementation, this would mint actual LP tokens
        // For simplicity, we're just tracking liquidity in the mapping
    }

    function _burnLP(address from, uint256 amount) internal {
        // In a real implementation, this would burn actual LP tokens
        // For simplicity, we're just tracking liquidity in the mapping
    }

    // Get reserves as tuple
    function getReservesTuple() external view returns (uint112, uint112) {
        return (reserveA, reserveB);
    }
}
