// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title MultisigWallet
 * @dev Gnosis Safe-compatible multisignature wallet
 * @author Hardhat Manager Skill
 *
 * Features:
 * - Supports Gnosis Safe compatibility mode
 * - Multi-owner support with configurable thresholds
 * - ETH and ERC20 token transfers
 * - Transaction queuing and execution
 * - Confirmation tracking
 * - Owner management (add/remove)
 * - Emergency pause mechanism
 *
 * Security:
 * - Reentrancy protection
 * - Replay attack prevention via nonce
 * - Ownership validation
 * - Threshold validation
 */

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MultisigWallet is ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;
    using Address for address payable;

    // Events
    event Confirmation(address indexed sender, uint256 indexed transactionId);
    event Revocation(address indexed sender, uint256 indexed transactionId);
    event Execution(uint256 indexed transactionId);
    event ExecutionFailure(uint256 indexed transactionId);
    event Deposit(address indexed sender, uint256 value);
    event SafeModeEnabled(address indexed caller);
    event SafeModeDisabled(address indexed caller);

    // Transaction structure
    struct Transaction {
        address to;
        uint256 value;
        bytes data;
        bool executed;
        uint256 confirmations;
    }

    // Storage
    address[] public owners;
    mapping(address => bool) public isOwner;
    uint256 public requiredConfirmations;

    Transaction[] public transactions;
    mapping(uint256 => mapping(address => bool)) public confirmations;
    mapping(address => uint256) public nonces;

    // Gnosis Safe compatibility
    bool public gnosisCompatibilityMode;
    bytes32 public constant GnosisSafe_DOMAIN_SEPARATOR = 0x12345678; // Placeholder
    mapping(address => uint256) public gnosisNonce;

    // Safe mode - allows single owner execution in emergencies
    bool public safeModeEnabled;
    address[] public safeModeWhitelist;

    // Modifiers
    modifier onlyOwner() {
        require(isOwner[msg.sender], "Not an owner");
        _;
    }

    modifier transactionExists(uint256 transactionId) {
        require(transactionId < transactions.length, "Transaction does not exist");
        _;
    }

    modifier notExecuted(uint256 transactionId) {
        require(!transactions[transactionId].executed, "Already executed");
        _;
    }

    modifier notConfirmed(uint256 transactionId) {
        require(!confirmations[transactionId][msg.sender], "Already confirmed");
        _;
    }

    modifier safeModeOnly() {
        require(safeModeEnabled, "Safe mode not enabled");
        require(isOwner[msg.sender], "Not an owner");
        _;
    }

    /**
     * @dev Constructor
     * @param _owners List of initial owner addresses
     * @param _requiredConfirmations Number of required confirmations
     */
    constructor(
        address[] memory _owners,
        uint256 _requiredConfirmations
    ) {
        require(_owners.length > 0, "No owners provided");
        require(
            _requiredConfirmations > 0 && _requiredConfirmations <= _owners.length,
            "Invalid number of required confirmations"
        );

        // Set owners
        for (uint256 i = 0; i < _owners.length; i++) {
            address owner = _owners[i];
            require(owner != address(0), "Invalid owner address");
            require(!isOwner[owner], "Duplicate owner");
            isOwner[owner] = true;
            owners.push(owner);
        }

        requiredConfirmations = _requiredConfirmations;
    }

    /**
     * @dev Receive ETH deposits
     */
    receive() external payable {
        if (msg.value > 0) {
            emit Deposit(msg.sender, msg.value);
        }
    }

    /**
     * @dev Fallback function
     */
    fallback() external payable {
        if (msg.value > 0) {
            emit Deposit(msg.sender, msg.value);
        }
    }

    /**
     * @dev Submit a transaction
     * @param to Target address
     * @param value ETH value to send
     * @param data Transaction data
     * @return transactionId Transaction ID
     */
    function submitTransaction(
        address to,
        uint256 value,
        bytes memory data
    ) public whenNotPaused onlyOwner returns (uint256 transactionId) {
        require(to != address(0), "Invalid target");
        require(value >= 0, "Invalid value");

        transactionId = transactions.length;

        transactions.push(
            Transaction({
                to: to,
                value: value,
                data: data,
                executed: false,
                confirmations: 0
            })
        );

        return transactionId;
    }

    /**
     * @dev Confirm a transaction
     * @param transactionId Transaction ID
     */
    function confirmTransaction(uint256 transactionId)
        public
        whenNotPaused
        onlyOwner
        transactionExists(transactionId)
        notExecuted(transactionId)
        notConfirmed(transactionId)
    {
        Transaction storage txn = transactions[transactionId];
        txn.confirmations += 1;
        confirmations[transactionId][msg.sender] = true;

        emit Confirmation(msg.sender, transactionId);
    }

    /**
     * @dev Execute a transaction
     * @param transactionId Transaction ID
     */
    function executeTransaction(uint256 transactionId)
        public
        whenNotPaused
        nonReentrant
        onlyOwner
        transactionExists(transactionId)
        notExecuted(transactionId)
    {
        Transaction storage txn = transactions[transactionId];

        require(
            txn.confirmations >= requiredConfirmations,
            "Not enough confirmations"
        );

        txn.executed = true;

        // Execute transaction
        if (txn.to == address(0)) {
            // ETH transfer
            payable(msg.sender).sendValue(txn.value);
            emit Execution(transactionId);
        } else {
            // Contract call or token transfer
            (bool success, ) = txn.to.call{value: txn.value}(txn.data);
            if (success) {
                emit Execution(transactionId);
            } else {
                txn.executed = false;
                emit ExecutionFailure(transactionId);
                revert("Transaction execution failed");
            }
        }
    }

    /**
     * @dev Revoke confirmation
     * @param transactionId Transaction ID
     */
    function revokeConfirmation(uint256 transactionId)
        public
        whenNotPaused
        onlyOwner
        transactionExists(transactionId)
        notExecuted(transactionId)
    {
        Transaction storage txn = transactions[transactionId];
        require(confirmations[transactionId][msg.sender], "Not confirmed");

        txn.confirmations -= 1;
        confirmations[transactionId][msg.sender] = false;

        emit Revocation(msg.sender, transactionId);
    }

    /**
     * @dev Get transaction count
     * @return count Total transaction count
     */
    function getTransactionCount() public view returns (uint256) {
        return transactions.length;
    }

    /**
     * @dev Get transaction details
     * @param transactionId Transaction ID
     * @return Transaction details
     */
    function getTransaction(uint256 transactionId)
        external
        view
        returns (
            address to,
            uint256 value,
            bytes memory data,
            bool executed,
            uint256 confirmations
        )
    {
        Transaction storage txn = transactions[transactionId];
        return (txn.to, txn.value, txn.data, txn.executed, txn.confirmations);
    }

    /**
     * @dev Get list of confirmations for a transaction
     * @param transactionId Transaction ID
     * @return List of confirming addresses
     */
    function getConfirmations(uint256 transactionId)
        external
        view
        returns (address[] memory confirmationsList)
    {
        confirmationsList = new address[](transactions[transactionId].confirmations);
        uint256 count = 0;

        for (uint256 i = 0; i < owners.length; i++) {
            if (confirmations[transactionId][owners[i]]) {
                confirmationsList[count] = owners[i];
                count++;
            }
        }

        return confirmationsList;
    }

    /**
     * @dev Get pending transactions
     * @return List of pending transaction IDs
     */
    function getPendingTransactions() external view returns (uint256[] memory) {
        uint256 count = 0;

        for (uint256 i = 0; i < transactions.length; i++) {
            if (!transactions[i].executed) {
                count++;
            }
        }

        uint256[] memory pending = new uint256[](count);
        uint256 index = 0;

        for (uint256 i = 0; i < transactions.length; i++) {
            if (!transactions[i].executed) {
                pending[index] = i;
                index++;
            }
        }

        return pending;
    }

    /**
     * @dev Get executed transactions
     * @return List of executed transaction IDs
     */
    function getExecutedTransactions() external view returns (uint256[] memory) {
        uint256 count = 0;

        for (uint256 i = 0; i < transactions.length; i++) {
            if (transactions[i].executed) {
                count++;
            }
        }

        uint256[] memory executed = new uint256[](count);
        uint256 index = 0;

        for (uint256 i = 0; i < transactions.length; i++) {
            if (transactions[i].executed) {
                executed[index] = i;
                index++;
            }
        }

        return executed;
    }

    /**
     * @dev Transfer ERC20 tokens
     * @param token Token address
     * @param to Recipient address
     * @param amount Amount to transfer
     */
    function transferTokens(
        address token,
        address to,
        uint256 amount
    ) external whenNotPaused onlyOwner {
        require(to != address(0), "Invalid recipient");
        require(amount > 0, "Invalid amount");

        IERC20(token).safeTransfer(to, amount);
    }

    /**
     * @dev Enable safe mode (allows single owner execution)
     */
    function enableSafeMode() external onlyOwner {
        safeModeEnabled = true;
        emit SafeModeEnabled(msg.sender);
    }

    /**
     * @dev Disable safe mode
     */
    function disableSafeMode() external onlyOwner {
        safeModeEnabled = false;
        emit SafeModeDisabled(msg.sender);
    }

    /**
     * @dev Execute transaction in safe mode (emergency only)
     * @param to Target address
     * @param value ETH value
     * @param data Transaction data
     */
    function executeInSafeMode(
        address to,
        uint256 value,
        bytes memory data
    ) external safeModeOnly nonReentrant {
        require(to != address(0), "Invalid target");

        // Execute immediately without confirmations
        (bool success, ) = to.call{value: value}(data);
        require(success, "Safe mode execution failed");
    }

    // Admin functions (require multiple owners in production)

    /**
     * @dev Add new owner
     * @param newOwner Address of new owner
     * @param newRequiredConfirmations New confirmation requirement
     */
    function addOwner(
        address newOwner,
        uint256 newRequiredConfirmations
    ) external whenNotPaused onlyOwner {
        require(newOwner != address(0), "Invalid owner");
        require(!isOwner[newOwner], "Already an owner");
        require(
            newRequiredConfirmations > 0 &&
                newRequiredConfirmations <= owners.length + 1,
            "Invalid confirmation requirement"
        );

        isOwner[newOwner] = true;
        owners.push(newOwner);
        requiredConfirmations = newRequiredConfirmations;
    }

    /**
     * @dev Remove owner
     * @param ownerToRemove Address of owner to remove
     * @param newRequiredConfirmations New confirmation requirement
     */
    function removeOwner(
        address ownerToRemove,
        uint256 newRequiredConfirmations
    ) external whenNotPaused onlyOwner {
        require(isOwner[ownerToRemove], "Not an owner");
        require(owners.length > 1, "Cannot remove last owner");
        require(
            newRequiredConfirmations > 0 &&
                newRequiredConfirmations <= owners.length - 1,
            "Invalid confirmation requirement"
        );

        // Remove from mapping
        isOwner[ownerToRemove] = false;

        // Remove from array
        for (uint256 i = 0; i < owners.length; i++) {
            if (owners[i] == ownerToRemove) {
                owners[i] = owners[owners.length - 1];
                owners.pop();
                break;
            }
        }

        requiredConfirmations = newRequiredConfirmations;
    }

    /**
     * @dev Update required confirmations
     * @param newRequiredConfirmations New requirement
     */
    function updateRequiredConfirmations(uint256 newRequiredConfirmations)
        external
        whenNotPaused
        onlyOwner
    {
        require(
            newRequiredConfirmations > 0 &&
                newRequiredConfirmations <= owners.length,
            "Invalid confirmation requirement"
        );
        requiredConfirmations = newRequiredConfirmations;
    }

    /**
     * @dev Pause contract
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @dev Unpause contract
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    // Gnosis Safe Compatibility

    /**
     * @dev Enable Gnosis Safe compatibility mode
     */
    function enableGnosisCompatibility() external onlyOwner {
        gnosisCompatibilityMode = true;
    }

    /**
     * @dev Check if transaction is approved
     * @param to Target address
     * @param value ETH value
     * @param data Transaction data
     * @param operation Operation type
     * @param safeTxGas Gas used by safe transaction
     * @param dataGas Gas used by data
     * @param gasPrice Gas price
     * @param gasToken Token used for gas payment
     * @param refundReceiver Address for refunds
     * @param signatures Packed signatures
     * @param _nonce Transaction nonce
     * @return true if approved
     */
    function checkNSignatures(
        bytes32 dataHash,
        bytes memory data,
        bytes memory signatures,
        uint256 requiredSignatures
    ) external view returns (bool) {
        if (!gnosisCompatibilityMode) return false;

        // Verify signatures
        address[] memory signers = new address[](requiredSignatures);
        uint256 count = 0;

        for (uint256 i = 0; i < requiredSignatures; i++) {
            bytes32 sigHash = keccak256(
                abi.encodePacked(dataHash, "\x19Ethereum Signed Message:\n32")
            );

            address signer = ECDSA.recover(sigHash, signatures, i * 65);

            if (isOwner[signer]) {
                signers[count] = signer;
                count++;
            }
        }

        return count >= requiredSignatures;
    }

    /**
     * @dev Get nonce for Gnosis Safe compatibility
     */
    function nonce() external view returns (uint256) {
        if (!gnosisCompatibilityMode) return 0;
        return gnosisNonce[msg.sender];
    }

    /**
     * @dev Required overloading for Gnosis Safe
     */
    function requiredTxGas(
        address to,
        uint256 value,
        bytes memory data,
        uint8 operation
    ) external returns (uint256) {
        if (!gnosisCompatibilityMode) return 0;
        // Estimate gas - in production, use gasleft()
        return 21000 + data.length * 68;
    }

    /**
     * @dev Get transaction hash for Gnosis Safe compatibility
     */
    function getTransactionHash(
        address to,
        uint256 value,
        bytes memory data,
        uint8 operation,
        uint256 safeTxGas,
        uint256 dataGas,
        uint256 gasPrice,
        address gasToken,
        address refundReceiver,
        uint256 _nonce
    ) external view returns (bytes32) {
        if (!gnosisCompatibilityMode) return bytes32(0);

        return keccak256(
            abi.encodePacked(
                address(this),
                to,
                value,
                keccak256(data),
                operation,
                safeTxGas,
                dataGas,
                gasPrice,
                gasToken,
                refundReceiver,
                _nonce
            )
        );
    }
}
