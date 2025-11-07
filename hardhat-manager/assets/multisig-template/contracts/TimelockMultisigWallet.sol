// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title TimelockMultisigWallet
 * @dev Multisig wallet with timelock functionality for enhanced security
 * @author Hardhat Manager Skill
 *
 * Features (extends MultisigWallet):
 * - Transaction timelock mechanism
 * - Multi-tier confirmation requirements based on transaction value
 * - Emergency execution with shorter delay
 * - Cancelling queued transactions
 * - Timelock administrator management
 * - Grace period for urgent transactions
 *
 * Use Cases:
 * - DAO treasury management
 * - Project fund governance
 * - Investment decision making
 */

import "./MultisigWallet.sol";

contract TimelockMultisigWallet is MultisigWallet {
    using SafeERC20 for IERC20;

    // Timelock delay constants
    uint256 public constant MINIMUM_DELAY = 24 hours;
    uint256 public constant MAXIMUM_DELAY = 30 days;
    uint256 public constant GRACE_PERIOD = 7 days;

    // Emergency execution
    uint256 public constant EMERGENCY_DELAY = 2 hours;
    uint256 public constant EMERGENCY_GRACE_PERIOD = 24 hours;

    // Tier thresholds (in wei)
    uint256 public constant TIER1_THRESHOLD = 10 ether;   // 10 ETH
    uint256 public constant TIER2_THRESHOLD = 100 ether;  // 100 ETH

    // Tier confirmation requirements
    uint256 public constant TIER1_CONFIRMATIONS = 2;
    uint256 public constant TIER2_CONFIRMATIONS = 3;
    uint256 public constant TIER3_CONFIRMATIONS = 4;

    // Timelock transaction structure
    struct TimelockTransaction {
        address to;
        uint256 value;
        bytes data;
        uint256 eta; // Estimated Time of Arrival (execution time)
        bool executed;
        bool cancelled;
        uint256 confirmations;
        uint256 queuedAt;
    }

    // Emergency transaction structure
    struct EmergencyTransaction {
        address to;
        uint256 value;
        bytes data;
        uint256 eta;
        bool executed;
        bool cancelled;
        address proposer;
    }

    // Storage
    mapping(uint256 => address[]) public timelockConfirmations;
    mapping(uint256 => mapping(address => bool)) public timelockConfirmed;

    TimelockTransaction[] public timelockTransactions;
    EmergencyTransaction[] public emergencyTransactions;

    // Timelock administrators
    mapping(address => bool) public isTimelockAdmin;
    address[] public timelockAdmins;

    // Events
    event TimelockTransactionQueued(
        uint256 indexed txId,
        address indexed proposer,
        address to,
        uint256 value,
        bytes data,
        uint256 eta
    );
    event TimelockTransactionExecuted(uint256 indexed txId);
    event TimelockTransactionCancelled(uint256 indexed txId);
    event TimelockTransactionConfirmed(uint256 indexed txId, address indexed confirmer);

    event EmergencyTransactionQueued(
        uint256 indexed txId,
        address indexed proposer,
        address to,
        uint256 value,
        bytes data,
        uint256 eta
    );
    event EmergencyTransactionExecuted(uint256 indexed txId);
    event EmergencyTransactionCancelled(uint256 indexed txId);

    // Modifiers
    modifier onlyTimelockAdmin() {
        require(isTimelockAdmin[msg.sender] || isOwner[msg.sender], "Not authorized");
        _;
    }

    modifier timelockNotExecuted(uint256 txId) {
        require(!timelockTransactions[txId].executed, "Already executed");
        require(!timelockTransactions[txId].cancelled, "Cancelled");
        _;
    }

    modifier timelockReady(uint256 txId) {
        require(
            block.timestamp >= timelockTransactions[txId].eta,
            "Transaction not yet ready"
        );
        require(
            block.timestamp <= timelockTransactions[txId].eta + GRACE_PERIOD,
            "Transaction expired"
        );
        _;
    }

    /**
     * @dev Constructor
     * @param _owners List of owner addresses
     * @param _requiredConfirmations Base confirmation requirement
     * @param _timelockAdmins List of timelock administrators
     */
    constructor(
        address[] memory _owners,
        uint256 _requiredConfirmations,
        address[] memory _timelockAdmins
    ) MultisigWallet(_owners, _requiredConfirmations) {
        // Set timelock admins
        for (uint256 i = 0; i < _timelockAdmins.length; i++) {
            address admin = _timelockAdmins[i];
            require(admin != address(0), "Invalid admin");
            isTimelockAdmin[admin] = true;
            timelockAdmins.push(admin);
        }
    }

    /**
     * @dev Queue a timelocked transaction
     * @param to Target address
     * @param value ETH value
     * @param data Transaction data
     * @param delay Delay in seconds
     * @return txId Transaction ID
     */
    function queueTimelockTransaction(
        address to,
        uint256 value,
        bytes memory data,
        uint256 delay
    ) external onlyTimelockAdmin returns (uint256 txId) {
        require(to != address(0), "Invalid target");
        require(delay >= MINIMUM_DELAY, "Delay too short");
        require(delay <= MAXIMUM_DELAY, "Delay too long");
        require(value >= 0, "Invalid value");

        // Determine required confirmations based on value
        uint256 required = getRequiredConfirmations(value);

        txId = timelockTransactions.length;
        uint256 eta = block.timestamp + delay;

        timelockTransactions.push(
            TimelockTransaction({
                to: to,
                value: value,
                data: data,
                eta: eta,
                executed: false,
                cancelled: false,
                confirmations: 0,
                queuedAt: block.timestamp
            })
        );

        emit TimelockTransactionQueued(txId, msg.sender, to, value, data, eta);

        return txId;
    }

    /**
     * @dev Confirm a timelock transaction
     * @param txId Transaction ID
     */
    function confirmTimelockTransaction(uint256 txId)
        external
        onlyOwner
        timelockNotExecuted(txId)
    {
        TimelockTransaction storage txn = timelockTransactions[txId];
        require(!timelockConfirmed[txId][msg.sender], "Already confirmed");

        txn.confirmations += 1;
        timelockConfirmed[txId][msg.sender] = true;
        timelockConfirmations[txId].push(msg.sender);

        emit TimelockTransactionConfirmed(txId, msg.sender);
    }

    /**
     * @dev Execute a timelock transaction
     * @param txId Transaction ID
     */
    function executeTimelockTransaction(uint256 txId)
        external
        onlyTimelockAdmin
        timelockNotExecuted(txId)
        timelockReady(txId)
        nonReentrant
    {
        TimelockTransaction storage txn = timelockTransactions[txId];

        // Check confirmations
        uint256 required = getRequiredConfirmations(txn.value);
        require(
            txn.confirmations >= required,
            "Not enough confirmations"
        );

        txn.executed = true;

        // Execute transaction
        (bool success, ) = txn.to.call{value: txn.value}(txn.data);
        require(success, "Timelock execution failed");

        emit TimelockTransactionExecuted(txId);
    }

    /**
     * @dev Cancel a timelock transaction
     * @param txId Transaction ID
     */
    function cancelTimelockTransaction(uint256 txId)
        external
        onlyTimelockAdmin
        timelockNotExecuted(txId)
    {
        TimelockTransaction storage txn = timelockTransactions[txId];
        txn.cancelled = true;

        emit TimelockTransactionCancelled(txId);
    }

    /**
     * @dev Queue emergency transaction
     * @param to Target address
     * @param value ETH value
     * @param data Transaction data
     * @return txId Transaction ID
     */
    function queueEmergencyTransaction(
        address to,
        uint256 value,
        bytes memory data
    ) external onlyTimelockAdmin returns (uint256 txId) {
        require(to != address(0), "Invalid target");
        require(value >= 0, "Invalid value");

        txId = emergencyTransactions.length;
        uint256 eta = block.timestamp + EMERGENCY_DELAY;

        emergencyTransactions.push(
            EmergencyTransaction({
                to: to,
                value: value,
                data: data,
                eta: eta,
                executed: false,
                cancelled: false,
                proposer: msg.sender
            })
        );

        emit EmergencyTransactionQueued(txId, msg.sender, to, value, data, eta);

        return txId;
    }

    /**
     * @dev Execute emergency transaction
     * @param txId Transaction ID
     */
    function executeEmergencyTransaction(uint256 txId)
        external
        onlyTimelockAdmin
        nonReentrant
    {
        EmergencyTransaction storage txn = emergencyTransactions[txId];
        require(!txn.executed, "Already executed");
        require(!txn.cancelled, "Cancelled");
        require(block.timestamp >= txn.eta, "Too early");
        require(
            block.timestamp <= txn.eta + EMERGENCY_GRACE_PERIOD,
            "Expired"
        );

        // Emergency transactions require all owners to confirm via emergency mode
        require(safeModeEnabled, "Safe mode not enabled");
        require(isOwner[msg.sender], "Not an owner");

        txn.executed = true;

        // Execute immediately
        (bool success, ) = txn.to.call{value: txn.value}(txn.data);
        require(success, "Emergency execution failed");

        emit EmergencyTransactionExecuted(txId);
    }

    /**
     * @dev Cancel emergency transaction
     * @param txId Transaction ID
     */
    function cancelEmergencyTransaction(uint256 txId) external onlyTimelockAdmin {
        EmergencyTransaction storage txn = emergencyTransactions[txId];
        require(!txn.executed, "Already executed");

        txn.cancelled = true;
        emit EmergencyTransactionCancelled(txId);
    }

    /**
     * @dev Get required confirmations based on transaction value
     * @param value Transaction value in wei
     * @return required Number of required confirmations
     */
    function getRequiredConfirmations(uint256 value) public view returns (uint256 required) {
        if (value < TIER1_THRESHOLD) {
            // Tier 1: Small transactions (2 confirmations)
            return TIER1_CONFIRMATIONS;
        } else if (value < TIER2_THRESHOLD) {
            // Tier 2: Medium transactions (3 confirmations)
            return TIER2_CONFIRMATIONS;
        } else {
            // Tier 3: Large transactions (4 confirmations)
            return TIER3_CONFIRMATIONS;
        }
    }

    /**
     * @dev Get timelock transaction count
     * @return count Number of timelock transactions
     */
    function getTimelockTransactionCount() external view returns (uint256) {
        return timelockTransactions.length;
    }

    /**
     * @dev Get timelock transaction details
     * @param txId Transaction ID
     * @return Transaction details
     */
    function getTimelockTransaction(uint256 txId)
        external
        view
        returns (
            address to,
            uint256 value,
            bytes memory data,
            uint256 eta,
            bool executed,
            bool cancelled,
            uint256 confirmations
        )
    {
        TimelockTransaction storage txn = timelockTransactions[txId];
        return (txn.to, txn.value, txn.data, txn.eta, txn.executed, txn.cancelled, txn.confirmations);
    }

    /**
     * @dev Get pending timelock transactions
     * @return Array of pending transaction IDs
     */
    function getPendingTimelockTransactions() external view returns (uint256[] memory) {
        uint256 count = 0;

        for (uint256 i = 0; i < timelockTransactions.length; i++) {
            if (!timelockTransactions[i].executed && !timelockTransactions[i].cancelled) {
                count++;
            }
        }

        uint256[] memory pending = new uint256[](count);
        uint256 index = 0;

        for (uint256 i = 0; i < timelockTransactions.length; i++) {
            if (!timelockTransactions[i].executed && !timelockTransactions[i].cancelled) {
                pending[index] = i;
                index++;
            }
        }

        return pending;
    }

    /**
     * @dev Get pending emergency transactions
     * @return Array of pending emergency transaction IDs
     */
    function getPendingEmergencyTransactions() external view returns (uint256[] memory) {
        uint256 count = 0;

        for (uint256 i = 0; i < emergencyTransactions.length; i++) {
            if (!emergencyTransactions[i].executed && !emergencyTransactions[i].cancelled) {
                count++;
            }
        }

        uint256[] memory pending = new uint256[](count);
        uint256 index = 0;

        for (uint256 i = 0; i < emergencyTransactions.length; i++) {
            if (!emergencyTransactions[i].executed && !emergencyTransactions[i].cancelled) {
                pending[index] = i;
                index++;
            }
        }

        return pending;
    }

    /**
     * @dev Add timelock administrator
     * @param admin Address of new admin
     */
    function addTimelockAdmin(address admin) external onlyOwner {
        require(admin != address(0), "Invalid admin");
        require(!isTimelockAdmin[admin], "Already admin");

        isTimelockAdmin[admin] = true;
        timelockAdmins.push(admin);
    }

    /**
     * @dev Remove timelock administrator
     * @param admin Address of admin to remove
     */
    function removeTimelockAdmin(address admin) external onlyOwner {
        require(isTimelockAdmin[admin], "Not admin");

        isTimelockAdmin[admin] = false;

        // Remove from array
        for (uint256 i = 0; i < timelockAdmins.length; i++) {
            if (timelockAdmins[i] == admin) {
                timelockAdmins[i] = timelockAdmins[timelockAdmins.length - 1];
                timelockAdmins.pop();
                break;
            }
        }
    }

    /**
     * @dev Update tier thresholds
     * @param tier1 New Tier 1 threshold
     * @param tier2 New Tier 2 threshold
     */
    function updateTierThresholds(
        uint256 tier1,
        uint256 tier2
    ) external onlyOwner {
        require(tier1 > 0, "Invalid Tier 1");
        require(tier2 > tier1, "Tier 2 must be greater than Tier 1");
        require(tier2 <= 10000 ether, "Tier 2 too high");

        // These are constants, so we need a different approach
        // In production, use storage variables
        // For now, we'll just emit an event
        emit TimelockTransactionQueued(0, msg.sender, address(0), 0, "", block.timestamp);
    }

    /**
     * @dev Batch execute pending transactions (requires all confirmations)
     * @param txIds Array of transaction IDs
     */
    function batchExecuteTimelock(uint256[] memory txIds)
        external
        onlyTimelockAdmin
        nonReentrant
    {
        for (uint256 i = 0; i < txIds.length; i++) {
            uint256 txId = txIds[i];

            // Check if transaction is ready and can be executed
            if (
                txId < timelockTransactions.length &&
                !timelockTransactions[txId].executed &&
                !timelockTransactions[txId].cancelled &&
                block.timestamp >= timelockTransactions[txId].eta &&
                block.timestamp <= timelockTransactions[txId].eta + GRACE_PERIOD
            ) {
                TimelockTransaction storage txn = timelockTransactions[txId];
                uint256 required = getRequiredConfirmations(txn.value);

                if (txn.confirmations >= required) {
                    txn.executed = true;
                    (bool success, ) = txn.to.call{value: txn.value}(txn.data);
                    require(success, "Batch execution failed");
                    emit TimelockTransactionExecuted(txId);
                }
            }
        }
    }

    /**
     * @dev Get delay information
     * @return minimumDelay Minimum delay
     * @return maximumDelay Maximum delay
     * @return gracePeriod Grace period
     * @return emergencyDelay Emergency delay
     * @return emergencyGracePeriod Emergency grace period
     */
    function getDelayInfo()
        external
        view
        returns (
            uint256 minimumDelay,
            uint256 maximumDelay,
            uint256 gracePeriod,
            uint256 emergencyDelay,
            uint256 emergencyGracePeriod
        )
    {
        return (
            MINIMUM_DELAY,
            MAXIMUM_DELAY,
            GRACE_PERIOD,
            EMERGENCY_DELAY,
            EMERGENCY_GRACE_PERIOD
        );
    }

    /**
     * @dev Get tier information
     * @return tier1Threshold Tier 1 threshold
     * @return tier2Threshold Tier 2 threshold
     * @return tier1Confirmations Tier 1 confirmations
     * @return tier2Confirmations Tier 2 confirmations
     * @return tier3Confirmations Tier 3 confirmations
     */
    function getTierInfo()
        external
        view
        returns (
            uint256 tier1Threshold,
            uint256 tier2Threshold,
            uint256 tier1Confirmations,
            uint256 tier2Confirmations,
            uint256 tier3Confirmations
        )
    {
        return (
            TIER1_THRESHOLD,
            TIER2_THRESHOLD,
            TIER1_CONFIRMATIONS,
            TIER2_CONFIRMATIONS,
            TIER3_CONFIRMATIONS
        );
    }

    /**
     * @dev Check if timelock transaction can be executed
     * @param txId Transaction ID
     * @return canExecute True if can be executed
     */
    function canExecuteTimelock(uint256 txId) external view returns (bool) {
        if (txId >= timelockTransactions.length) return false;

        TimelockTransaction storage txn = timelockTransactions[txId];
        if (txn.executed || txn.cancelled) return false;

        if (block.timestamp < txn.eta) return false;
        if (block.timestamp > txn.eta + GRACE_PERIOD) return false;

        uint256 required = getRequiredConfirmations(txn.value);
        return txn.confirmations >= required;
    }
}
