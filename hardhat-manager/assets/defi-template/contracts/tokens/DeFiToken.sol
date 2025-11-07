// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title DeFiToken
 * @dev ERC20 token designed for DeFi protocols
 * @notice Includes minting, burning, and pausable functionality
 */
contract DeFiToken is ERC20, ERC20Burnable, ERC20Pausable, Ownable, ReentrancyGuard {
    // State variables
    mapping(address => bool) public minters;
    mapping(address => bool) public blacklisted;

    // Events
    event MinterAdded(address indexed minter);
    event MinterRemoved(address indexed minter);
    event Blacklisted(address indexed account);
    event UnBlacklisted(address indexed account);
    event Minted(address indexed to, uint256 amount);
    event Burned(address indexed from, uint256 amount);
    event Paused(address indexed account);
    event Unpaused(address indexed account);

    // Modifiers
    modifier onlyMinter() {
        require(minters[msg.sender] || owner() == msg.sender, "Not authorized minter");
        _;
    }

    modifier notBlacklisted(address account) {
        require(!blacklisted[account], "Account is blacklisted");
        _;
    }

    /**
     * @dev Constructor
     * @param name Token name
     * @param symbol Token symbol
     * @param initialSupply Initial supply in wei (e.g., 1000000 * 10^18)
     * @param recipient Address to receive initial supply
     */
    constructor(
        string memory name,
        string memory symbol,
        uint256 initialSupply,
        address recipient
    ) ERC20(name, symbol) {
        require(recipient != address(0), "Invalid recipient");
        require(initialSupply > 0, "Initial supply must be > 0");

        _mint(recipient, initialSupply);
        minters[msg.sender] = true;

        transferOwnership(msg.sender);
    }

    /**
     * @dev Mint tokens (only by authorized minters)
     * @param to Recipient address
     * @param amount Amount to mint
     */
    function mint(address to, uint256 amount)
        external
        onlyMinter
        notBlacklisted(to)
        nonReentrant
    {
        require(to != address(0), "Invalid address");
        require(amount > 0, "Amount must be > 0");

        _mint(to, amount);
        emit Minted(to, amount);
    }

    /**
     * @dev Batch mint tokens
     * @param recipients Array of recipient addresses
     * @param amounts Array of amounts to mint
     */
    function batchMint(address[] calldata recipients, uint256[] calldata amounts)
        external
        onlyMinter
        nonReentrant
    {
        require(recipients.length == amounts.length, "Array length mismatch");
        require(recipients.length <= 100, "Batch size too large");

        for (uint256 i = 0; i < recipients.length; i++) {
            require(recipients[i] != address(0), "Invalid address");
            require(amounts[i] > 0, "Amount must be > 0");
            require(!blacklisted[recipients[i]], "Recipient is blacklisted");

            _mint(recipients[i], amounts[i]);
            emit Minted(recipients[i], amounts[i]);
        }
    }

    /**
     * @dev Override burn to emit event
     * @param amount Amount to burn
     */
    function burn(uint256 amount) public override {
        super.burn(amount);
        emit Burned(msg.sender, amount);
    }

    /**
     * @dev Burn from address (requires allowance)
     * @param from Address to burn from
     * @param amount Amount to burn
     */
    function burnFrom(address from, uint256 amount) public override {
        super.burnFrom(from, amount);
        emit Burned(from, amount);
    }

    /**
     * @dev Add minter
     * @param minter Address to add as minter
     */
    function addMinter(address minter) external onlyOwner {
        require(minter != address(0), "Invalid minter");
        minters[minter] = true;
        emit MinterAdded(minter);
    }

    /**
     * @dev Remove minter
     * @param minter Address to remove from minters
     */
    function removeMinter(address minter) external onlyOwner {
        require(minter != address(0), "Invalid minter");
        minters[minter] = false;
        emit MinterRemoved(minter);
    }

    /**
     * @dev Blacklist account
     * @param account Address to blacklist
     */
    function blacklist(address account) external onlyOwner {
        require(account != address(0), "Invalid address");
        require(!blacklisted[account], "Already blacklisted");
        blacklisted[account] = true;
        emit Blacklisted(account);
    }

    /**
     * @dev Remove from blacklist
     * @param account Address to remove from blacklist
     */
    function unBlacklist(address account) external onlyOwner {
        require(account != address(0), "Invalid address");
        require(blacklisted[account], "Not blacklisted");
        blacklisted[account] = false;
        emit UnBlacklisted(account);
    }

    /**
     * @dev Check if account is blacklisted
     * @param account Address to check
     */
    function isBlacklisted(address account) external view returns (bool) {
        return blacklisted[account];
    }

    /**
     * @dev Check if address is minter
     * @param account Address to check
     */
    function isMinter(address account) external view returns (bool) {
        return minters[account] || account == owner();
    }

    /**
     * @dev Override transfer to check blacklist
     * @param to Recipient address
     * @param amount Amount to transfer
     */
    function transfer(address to, uint256 amount)
        public
        override
        notBlacklisted(msg.sender)
        notBlacklisted(to)
        returns (bool)
    {
        return super.transfer(to, amount);
    }

    /**
     * @dev Override transferFrom to check blacklist
     * @param from Sender address
     * @param to Recipient address
     * @param amount Amount to transfer
     */
    function transferFrom(
        address from,
        address to,
        uint256 amount
    ) public override notBlacklisted(from) notBlacklisted(to) returns (bool) {
        return super.transferFrom(from, to, amount);
    }

    /**
     * @dev Pause contract
     */
    function pause() external onlyOwner {
        _pause();
        emit Paused(msg.sender);
    }

    /**
     * @dev Unpause contract
     */
    function unpause() external onlyOwner {
        _unpause();
        emit Unpaused(msg.sender);
    }

    /**
     * @dev Get contract info
     */
    function getInfo() external view returns (
        string memory name_,
        string memory symbol_,
        uint256 totalSupply_,
        uint8 decimals_
    ) {
        return (name(), symbol(), totalSupply(), decimals());
    }

    // Required overrides
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override(ERC20, ERC20Pausable) {
        super._beforeTokenTransfer(from, to, amount);
    }
}
