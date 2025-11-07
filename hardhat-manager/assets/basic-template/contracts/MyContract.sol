// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title MyContract
 * @dev Basic contract template demonstrating common patterns
 * @notice This contract shows best practices for contract development
 */
contract MyContract is Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;

    // State variables
    Counters.Counter private _itemIds;
    mapping(uint256 => Item) public items;
    mapping(address => uint256[]) public userItems;
    mapping(address => bool) public authorizedUsers;

    // Structs
    struct Item {
        uint256 id;
        string name;
        address creator;
        uint256 createdAt;
        uint256 price;
        bool active;
    }

    // Events
    event ItemCreated(
        uint256 indexed itemId,
        string name,
        address indexed creator,
        uint256 price
    );
    event ItemUpdated(uint256 indexed itemId, string newName, uint256 newPrice);
    event ItemDeactivated(uint256 indexed itemId);
    event UserAuthorized(address indexed user);
    event UserDeauthorized(address indexed user);

    // Modifiers
    modifier onlyAuthorized() {
        require(
            msg.sender == owner() || authorizedUsers[msg.sender],
            "Not authorized"
        );
        _;
    }

    modifier onlyItemOwner(uint256 itemId) {
        require(items[itemId].creator == msg.sender, "Not item owner");
        _;
    }

    modifier itemExists(uint256 itemId) {
        require(items[itemId].active, "Item does not exist");
        _;
    }

    modifier validString(string memory str) {
        require(bytes(str).length > 0, "String cannot be empty");
        _;
    }

    // Constructor
    constructor() {
        // Initialize contract state
        authorizedUsers[msg.sender] = true;
        emit UserAuthorized(msg.sender);
    }

    // External functions
    function createItem(string memory _name, uint256 _price)
        external
        onlyAuthorized
        nonReentrant
        validString(_name)
        returns (uint256)
    {
        require(_price > 0, "Price must be greater than 0");

        _itemIds.increment();
        uint256 newItemId = _itemIds.current();

        items[newItemId] = Item({
            id: newItemId,
            name: _name,
            creator: msg.sender,
            createdAt: block.timestamp,
            price: _price,
            active: true
        });

        userItems[msg.sender].push(newItemId);

        emit ItemCreated(newItemId, _name, msg.sender, _price);
        return newItemId;
    }

    function updateItem(uint256 _itemId, string memory _newName, uint256 _newPrice)
        external
        onlyItemOwner(_itemId)
        itemExists(_itemId)
        validString(_newName)
    {
        require(_newPrice > 0, "Price must be greater than 0");

        items[_itemId].name = _newName;
        items[_itemId].price = _newPrice;

        emit ItemUpdated(_itemId, _newName, _newPrice);
    }

    function deactivateItem(uint256 _itemId)
        external
        onlyItemOwner(_itemId)
        itemExists(_itemId)
    {
        items[_itemId].active = false;
        emit ItemDeactivated(_itemId);
    }

    function authorizeUser(address _user) external onlyOwner {
        require(_user != address(0), "Invalid address");
        require(!authorizedUsers[_user], "User already authorized");

        authorizedUsers[_user] = true;
        emit UserAuthorized(_user);
    }

    function deauthorizeUser(address _user) external onlyOwner {
        require(_user != address(0), "Invalid address");
        require(_user != owner(), "Cannot deauthorize owner");
        require(authorizedUsers[_user], "User not authorized");

        authorizedUsers[_user] = false;
        emit UserDeauthorized(_user);
    }

    // View functions
    function getItem(uint256 _itemId) external view returns (Item memory) {
        require(_itemId > 0 && _itemId <= _itemIds.current(), "Invalid item ID");
        require(items[_itemId].active, "Item does not exist");
        return items[_itemId];
    }

    function getUserItems(address _user) external view returns (uint256[] memory) {
        return userItems[_user];
    }

    function getActiveItemsCount() external view returns (uint256) {
        return _itemIds.current();
    }

    function getUserItemsCount(address _user) external view returns (uint256) {
        return userItems[_user].length;
    }

    function isAuthorized(address _user) external view returns (bool) {
        return authorizedUsers[_user];
    }

    function getUserActiveItems(address _user) external view returns (uint256[] memory) {
        uint256[] memory userItemIds = userItems[_user];
        uint256 activeCount = 0;

        // Count active items
        for (uint256 i = 0; i < userItemIds.length; i++) {
            if (items[userItemIds[i]].active) {
                activeCount++;
            }
        }

        // Create array of active items
        uint256[] memory activeItems = new uint256[](activeCount);
        uint256 index = 0;

        for (uint256 i = 0; i < userItemIds.length; i++) {
            if (items[userItemIds[i]].active) {
                activeItems[index] = userItemIds[i];
                index++;
            }
        }

        return activeItems;
    }

    // Utility functions
    function isValidItemId(uint256 _itemId) external view returns (bool) {
        return _itemId > 0 && _itemId <= _itemIds.current() && items[_itemId].active;
    }

    function getItemPrice(uint256 _itemId) external view itemExists(_itemId) returns (uint256) {
        return items[_itemId].price;
    }

    function getItemCreator(uint256 _itemId) external view itemExists(_itemId) returns (address) {
        return items[_itemId].creator;
    }

    function getItemCreationTime(uint256 _itemId) external view itemExists(_itemId) returns (uint256) {
        return items[_itemId].createdAt;
    }

    // Emergency functions
    function emergencyDeactivate() external onlyOwner {
        // This would typically have more specific logic
        // For demonstration, we'll just show the pattern
        _pause();
    }

    function emergencyReactivate() external onlyOwner {
        _unpause();
    }

    // Pausing functionality (using OpenZeppelin Pausable would be better)
    bool private _paused;

    modifier whenNotPaused() {
        require(!_paused, "Contract is paused");
        _;
    }

    function _pause() internal {
        _paused = true;
    }

    function _unpause() internal {
        _paused = false;
    }

    function paused() external view returns (bool) {
        return _paused;
    }
}