# Hardhat Project Templates Guide

This guide provides detailed specifications and customization instructions for the various Hardhat project templates available in this skill. Each template is designed for specific use cases with appropriate contract structures, testing frameworks, and deployment patterns.

## Available Templates

1. [Basic Template](#basic-template) - Standard smart contract projects
2. [DeFi Template](#defi-template) - DeFi protocols and financial applications
3. [NFT Template](#nft-template) - NFT collections and marketplaces
4. [DAO Template](#dao-template) - DAO governance and voting systems

## Basic Template

### Overview
The Basic Template is designed for standard smart contract projects including tokens, simple utilities, and foundational contracts. It provides a clean, well-structured starting point for most Ethereum development projects.

### Structure
```
basic-template/
├── contracts/
│   ├── interfaces/
│   ├── libraries/
│   └── MyContract.sol
├── scripts/
│   └── deploy.js
├── test/
│   ├── MyContract.test.js
│   └── helpers.js
├── hardhat.config.js
├── package.json
├── .env.example
└── README.md
```

### Contract Structure

#### Main Contract Template
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title MyContract
 * @dev Basic contract template with common patterns
 */
contract MyContract is Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;

    // State variables
    Counters.Counter private _itemIds;
    mapping(uint256 => Item) public items;
    mapping(address => uint256[]) public userItems;

    // Structs
    struct Item {
        uint256 id;
        string name;
        address creator;
        uint256 createdAt;
        bool active;
    }

    // Events
    event ItemCreated(uint256 indexed itemId, string name, address indexed creator);
    event ItemUpdated(uint256 indexed itemId, string newName);
    event ItemDeactivated(uint256 indexed itemId);

    // Modifiers
    modifier onlyItemOwner(uint256 itemId) {
        require(items[itemId].creator == msg.sender, "Not item owner");
        _;
    }

    modifier itemExists(uint256 itemId) {
        require(items[itemId].active, "Item does not exist");
        _;
    }

    // Constructor
    constructor() {
        // Initialize contract
    }

    // Functions
    function createItem(string memory _name) external nonReentrant {
        require(bytes(_name).length > 0, "Name cannot be empty");

        _itemIds.increment();
        uint256 newItemId = _itemIds.current();

        items[newItemId] = Item({
            id: newItemId,
            name: _name,
            creator: msg.sender,
            createdAt: block.timestamp,
            active: true
        });

        userItems[msg.sender].push(newItemId);

        emit ItemCreated(newItemId, _name, msg.sender);
    }

    function updateItem(uint256 _itemId, string memory _newName)
        external
        onlyItemOwner(_itemId)
        itemExists(_itemId)
    {
        require(bytes(_newName).length > 0, "Name cannot be empty");

        items[_itemId].name = _newName;
        emit ItemUpdated(_itemId, _newName);
    }

    function deactivateItem(uint256 _itemId)
        external
        onlyItemOwner(_itemId)
        itemExists(_itemId)
    {
        items[_itemId].active = false;
        emit ItemDeactivated(_itemId);
    }

    // View functions
    function getItem(uint256 _itemId) external view returns (Item memory) {
        require(items[_itemId].active, "Item does not exist");
        return items[_itemId];
    }

    function getUserItems(address _user) external view returns (uint256[] memory) {
        return userItems[_user];
    }

    function getTotalItems() external view returns (uint256) {
        return _itemIds.current();
    }
}
```

### Configuration

#### hardhat.config.js
```javascript
require("@nomicfoundation/hardhat-toolbox");
require("hardhat-gas-reporter");
require("solidity-coverage");

const INFURA_API_KEY = process.env.INFURA_API_KEY || "";
const PRIVATE_KEY = process.env.PRIVATE_KEY || "";
const ETHERSCAN_API_KEY = process.env.ETHERSCAN_API_KEY || "";

module.exports = {
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    hardhat: {
      chainId: 31337
    },
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337
    },
    goerli: {
      url: `https://goerli.infura.io/v3/${INFURA_API_KEY}`,
      accounts: [PRIVATE_KEY],
      chainId: 5
    },
    mainnet: {
      url: `https://mainnet.infura.io/v3/${INFURA_API_KEY}`,
      accounts: [PRIVATE_KEY],
      chainId: 1,
      gasPrice: 20000000000
    }
  },
  etherscan: {
    apiKey: ETHERSCAN_API_KEY
  },
  gasReporter: {
    enabled: process.env.REPORT_GAS !== undefined,
    currency: "USD"
  }
};
```

### Testing

#### Test Template
```javascript
// test/MyContract.test.js
const { expect } = require("chai");
const { ethers } = require("hardhat");
const { deployContract } = require("./helpers");

describe("MyContract", function () {
  let contract;
  let owner, user1, user2;

  beforeEach(async function () {
    const signers = await ethers.getSigners();
    owner = signers[0];
    user1 = signers[1];
    user2 = signers[2];

    contract = await deployContract("MyContract");
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await contract.owner()).to.equal(owner.address);
    });

    it("Should start with zero items", async function () {
      expect(await contract.getTotalItems()).to.equal(0);
    });
  });

  describe("Item Management", function () {
    it("Should create items", async function () {
      await expect(contract.connect(user1).createItem("Test Item"))
        .to.emit(contract, "ItemCreated")
        .withArgs(1, "Test Item", user1.address);

      const item = await contract.getItem(1);
      expect(item.name).to.equal("Test Item");
      expect(item.creator).to.equal(user1.address);
    });

    it("Should update items", async function () {
      await contract.connect(user1).createItem("Original Name");

      await expect(contract.connect(user1).updateItem(1, "New Name"))
        .to.emit(contract, "ItemUpdated")
        .withArgs(1, "New Name");

      const item = await contract.getItem(1);
      expect(item.name).to.equal("New Name");
    });
  });
});
```

## DeFi Template

### Overview
The DeFi Template is designed for decentralized finance protocols including AMMs, lending platforms, yield farming, and staking contracts. It includes standard DeFi patterns, security measures, and integration hooks.

### Structure
```
defi-template/
├── contracts/
│   ├── core/
│   │   ├── Token.sol
│   │   ├── StakingPool.sol
│   │   └── RewardsDistributor.sol
│   ├── governance/
│   │   ├── Governor.sol
│   │   └── Timelock.sol
│   ├── interfaces/
│   │   ├── IStakingPool.sol
│   │   └── IRewardsDistributor.sol
│   ├── libraries/
│   │   ├── Math.sol
│   │   └── SafeERC20.sol
│   └── mock/
│       └── MockOracle.sol
├── scripts/
│   ├── deploy-core.js
│   ├── deploy-governance.js
│   └── setup-protocol.js
├── test/
│   ├── unit/
│   ├── integration/
│   └── security/
└── hardhat.config.js
```

### Core Contracts

#### Governance Token
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";

contract GovernanceToken is ERC20, Ownable {
    uint256 public constant MAX_SUPPLY = 1000000000 * 10**18; // 1B tokens

    constructor() ERC20("Governance Token", "GOV") {
        // Mint initial supply to owner
        _mint(msg.sender, 100000000 * 10**18); // 100M tokens
    }

    function mint(address to, uint256 amount) external onlyOwner {
        require(totalSupply() + amount <= MAX_SUPPLY, "Max supply reached");
        _mint(to, amount);
    }

    // Voting power delegation
    function delegate(address delegatee) external {
        _delegate(msg.sender, delegatee);
    }
}
```

#### Staking Pool
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract StakingPool is ReentrancyGuard, Ownable {
    using SafeERC20 for IERC20;

    IERC20 public stakingToken;
    IERC20 public rewardsToken;

    struct Stake {
        uint256 amount;
        uint256 timestamp;
        uint256 rewardDebt;
    }

    mapping(address => Stake) public stakes;
    uint256 public totalStaked;

    uint256 public rewardRate;
    uint256 public lastUpdateTime;
    uint256 public rewardPerTokenStored;

    mapping(address => uint256) public userRewardPerTokenPaid;
    mapping(address => uint256) public rewards;

    uint256 public constant REWARD_DURATION = 7 days;
    uint256 public lockPeriod = 30 days;

    event Staked(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event RewardPaid(address indexed user, uint256 reward);
    event RewardRateUpdated(uint256 newRate);

    constructor(address _stakingToken, address _rewardsToken) {
        stakingToken = IERC20(_stakingToken);
        rewardsToken = IERC20(_rewardsToken);
        rewardRate = 100; // 100 rewards per second
        lastUpdateTime = block.timestamp;
    }

    function rewardPerToken() public view returns (uint256) {
        if (totalStaked == 0) {
            return rewardPerTokenStored;
        }
        return rewardPerTokenStored + (((block.timestamp - lastUpdateTime) * rewardRate * 1e18) / totalStaked);
    }

    function earned(address account) public view returns (uint256) {
        return ((stakes[account].amount * (rewardPerToken() - userRewardPerTokenPaid[account])) / 1e18) + rewards[account];
    }

    function stake(uint256 amount) external nonReentrant {
        require(amount > 0, "Cannot stake 0");

        _updateReward(msg.sender);

        stakes[msg.sender].amount += amount;
        stakes[msg.sender].timestamp = block.timestamp;
        totalStaked += amount;

        stakingToken.safeTransferFrom(msg.sender, address(this), amount);

        emit Staked(msg.sender, amount);
    }

    function withdraw(uint256 amount) external nonReentrant {
        require(amount > 0, "Cannot withdraw 0");
        require(stakes[msg.sender].amount >= amount, "Insufficient stake");
        require(block.timestamp >= stakes[msg.sender].timestamp + lockPeriod, "Stake still locked");

        _updateReward(msg.sender);

        stakes[msg.sender].amount -= amount;
        totalStaked -= amount;

        stakingToken.safeTransfer(msg.sender, amount);

        emit Withdrawn(msg.sender, amount);
    }

    function getReward() external nonReentrant {
        _updateReward(msg.sender);
        uint256 reward = rewards[msg.sender];
        if (reward > 0) {
            rewards[msg.sender] = 0;
            rewardsToken.safeTransfer(msg.sender, reward);
            emit RewardPaid(msg.sender, reward);
        }
    }

    function _updateReward(address account) internal {
        rewardPerTokenStored = rewardPerToken();
        lastUpdateTime = block.timestamp;
        rewards[account] = earned(account);
        userRewardPerTokenPaid[account] = rewardPerTokenStored;
    }

    function setRewardRate(uint256 _rewardRate) external onlyOwner {
        _updateReward(address(0));
        rewardRate = _rewardRate;
        emit RewardRateUpdated(_rewardRate);
    }
}
```

### DeFi Deployment Script
```javascript
// scripts/deploy-core.js
const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying DeFi Protocol...");

  const [deployer] = await ethers.getSigners();
  console.log("Deploying with account:", deployer.address);

  // Deploy Governance Token
  console.log("Deploying Governance Token...");
  const GovernanceToken = await ethers.getContractFactory("GovernanceToken");
  const governanceToken = await GovernanceToken.deploy();
  await governanceToken.deployed();
  console.log("GovernanceToken deployed to:", governanceToken.address);

  // Deploy Staking Pool
  console.log("Deploying Staking Pool...");
  const StakingPool = await ethers.getContractFactory("StakingPool");
  const stakingPool = await StakingPool.deploy(
    governanceToken.address,
    governanceToken.address
  );
  await stakingPool.deployed();
  console.log("StakingPool deployed to:", stakingPool.address);

  // Setup initial liquidity
  const initialLiquidity = ethers.utils.parseEther("1000000");
  await governanceToken.transfer(stakingPool.address, initialLiquidity);
  console.log("Transferred initial liquidity to staking pool");

  // Save deployment info
  const deploymentInfo = {
    governanceToken: governanceToken.address,
    stakingPool: stakingPool.address,
    deployer: deployer.address,
    network: network.name,
    timestamp: new Date().toISOString()
  };

  console.log("Deployment completed:", deploymentInfo);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
```

## NFT Template

### Overview
The NFT Template is designed for NFT collections, marketplaces, and metadata management contracts. It includes ERC721, ERC1155 implementations, marketplace functionality, and metadata standards.

### Structure
```
nft-template/
├── contracts/
│   ├── NFTCollection.sol
│   ├── NFTMarketplace.sol
│   ├── ERC1155Collection.sol
│   ├── interfaces/
│   │   ├── INFTCollection.sol
│   │   └── INFTMarketplace.sol
│   └── libraries/
│       └── Metadata.sol
├── scripts/
│   ├── deploy-collection.js
│   ├── deploy-marketplace.js
│   └── mint-collection.js
├── test/
│   ├── NFTCollection.test.js
│   └── NFTMarketplace.test.js
└── metadata/
    ├── collection.json
    └── tokens/
```

### NFT Collection Contract
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract NFTCollection is ERC721URIStorage, Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;

    Counters.Counter private _tokenIds;

    uint256 public maxSupply;
    uint256 public mintPrice;
    uint256 public maxMintPerTx;
    bool public saleActive;
    string public baseTokenURI;

    mapping(address => uint256) public mintedByAddress;
    mapping(uint256 => string) public customTokenURIs;

    event Minted(address indexed to, uint256 indexed tokenId);
    event SaleStatusChanged(bool active);
    event BaseURIUpdated(string newBaseURI);
    event MintPriceUpdated(uint256 newPrice);

    constructor(
        string memory name,
        string memory symbol,
        uint256 _maxSupply,
        uint256 _mintPrice,
        uint256 _maxMintPerTx,
        string memory _baseTokenURI
    ) ERC721(name, symbol) {
        maxSupply = _maxSupply;
        mintPrice = _mintPrice;
        maxMintPerTx = _maxMintPerTx;
        baseTokenURI = _baseTokenURI;
    }

    function mint(uint256 quantity) external payable nonReentrant {
        require(saleActive, "Sale not active");
        require(quantity > 0, "Quantity must be > 0");
        require(quantity <= maxMintPerTx, "Exceeds max mint per tx");
        require(_tokenIds.current() + quantity <= maxSupply, "Exceeds max supply");
        require(msg.value >= mintPrice * quantity, "Insufficient payment");

        for (uint256 i = 0; i < quantity; i++) {
            _tokenIds.increment();
            uint256 newTokenId = _tokenIds.current();
            _safeMint(msg.sender, newTokenId);
            emit Minted(msg.sender, newTokenId);
        }

        mintedByAddress[msg.sender] += quantity;
    }

    function mintTo(address to, uint256 quantity) external onlyOwner {
        require(_tokenIds.current() + quantity <= maxSupply, "Exceeds max supply");

        for (uint256 i = 0; i < quantity; i++) {
            _tokenIds.increment();
            uint256 newTokenId = _tokenIds.current();
            _safeMint(to, newTokenId);
            emit Minted(to, newTokenId);
        }
    }

    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721URIStorage)
        returns (string memory)
    {
        require(_exists(tokenId), "Token does not exist");

        string memory customURI = customTokenURIs[tokenId];
        if (bytes(customURI).length > 0) {
            return customURI;
        }

        return bytes(baseTokenURI).length > 0
            ? string(abi.encodePacked(baseTokenURI, Strings.toString(tokenId)))
            : "";
    }

    function setTokenURI(uint256 tokenId, string memory _tokenURI) external onlyOwner {
        require(_exists(tokenId), "Token does not exist");
        customTokenURIs[tokenId] = _tokenURI;
    }

    function setBaseURI(string memory _baseTokenURI) external onlyOwner {
        baseTokenURI = _baseTokenURI;
        emit BaseURIUpdated(_baseTokenURI);
    }

    function setSaleActive(bool _active) external onlyOwner {
        saleActive = _active;
        emit SaleStatusChanged(_active);
    }

    function setMintPrice(uint256 _newPrice) external onlyOwner {
        mintPrice = _newPrice;
        emit MintPriceUpdated(_newPrice);
    }

    function withdraw() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No funds to withdraw");

        payable(owner()).transfer(balance);
    }

    function totalSupply() external view returns (uint256) {
        return _tokenIds.current();
    }

    function exists(uint256 tokenId) external view returns (bool) {
        return _exists(tokenId);
    }
}
```

### NFT Marketplace Contract
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/token/ERC1155/IERC1155.sol";

contract NFTMarketplace is ReentrancyGuard, Ownable {
    struct Listing {
        uint256 itemId;
        address nftContract;
        uint256 tokenId;
        address payable seller;
        uint256 price;
        bool active;
        bool isERC1155;
        uint256 amount; // For ERC1155 only
    }

    uint256 private _itemIds;
    mapping(uint256 => Listing) public listings;

    uint256 public marketplaceFee = 250; // 2.5%
    uint256 public constant MAX_FEE = 1000; // 10%

    event ItemListed(
        uint256 indexed itemId,
        address indexed nftContract,
        uint256 indexed tokenId,
        address seller,
        uint256 price
    );

    event ItemSold(
        uint256 indexed itemId,
        address indexed nftContract,
        uint256 indexed tokenId,
        address seller,
        address buyer,
        uint256 price
    );

    event ItemCanceled(uint256 indexed itemId);

    modifier listingExists(uint256 itemId) {
        require(listings[itemId].active, "Listing does not exist");
        _;
    }

    modifier onlyItemOwner(uint256 itemId) {
        require(listings[itemId].seller == msg.sender, "Not item owner");
        _;
    }

    function listItem(
        address nftContract,
        uint256 tokenId,
        uint256 price,
        bool isERC1155,
        uint256 amount
    ) external nonReentrant {
        require(price > 0, "Price must be > 0");

        if (isERC1155) {
            require(amount > 0, "Amount must be > 0");
            require(
                IERC1155(nftContract).balanceOf(msg.sender, tokenId) >= amount,
                "Insufficient balance"
            );
        } else {
            require(
                IERC721(nftContract).ownerOf(tokenId) == msg.sender,
                "Not token owner"
            );
        }

        _itemIds++;
        uint256 itemId = _itemIds;

        listings[itemId] = Listing({
            itemId: itemId,
            nftContract: nftContract,
            tokenId: tokenId,
            seller: payable(msg.sender),
            price: price,
            active: true,
            isERC1155: isERC1155,
            amount: amount
        });

        if (isERC1155) {
            IERC1155(nftContract).safeTransferFrom(msg.sender, address(this), tokenId, amount, "");
        } else {
            IERC721(nftContract).transferFrom(msg.sender, address(this), tokenId);
        }

        emit ItemListed(itemId, nftContract, tokenId, msg.sender, price);
    }

    function buyItem(uint256 itemId) external payable nonReentrant listingExists(itemId) {
        Listing memory listing = listings[itemId];
        require(msg.value >= listing.price, "Insufficient payment");

        uint256 totalPrice = listing.price;
        uint256 marketplaceFeeAmount = (totalPrice * marketplaceFee) / 10000;
        uint256 sellerAmount = totalPrice - marketplaceFeeAmount;

        // Transfer NFT to buyer
        if (listing.isERC1155) {
            IERC1155(listing.nftContract).safeTransferFrom(
                address(this),
                msg.sender,
                listing.tokenId,
                listing.amount,
                ""
            );
        } else {
            IERC721(listing.nftContract).transferFrom(address(this), msg.sender, listing.tokenId);
        }

        // Transfer funds to seller
        listing.seller.transfer(sellerAmount);

        // Deactivate listing
        listings[itemId].active = false;

        emit ItemSold(
            itemId,
            listing.nftContract,
            listing.tokenId,
            listing.seller,
            msg.sender,
            totalPrice
        );

        // Return excess payment
        if (msg.value > totalPrice) {
            payable(msg.sender).transfer(msg.value - totalPrice);
        }
    }

    function cancelListing(uint256 itemId)
        external
        nonReentrant
        listingExists(itemId)
        onlyItemOwner(itemId)
    {
        Listing memory listing = listings[itemId];

        // Transfer NFT back to seller
        if (listing.isERC1155) {
            IERC1155(listing.nftContract).safeTransferFrom(
                address(this),
                listing.seller,
                listing.tokenId,
                listing.amount,
                ""
            );
        } else {
            IERC721(listing.nftContract).transferFrom(address(this), listing.seller, listing.tokenId);
        }

        // Deactivate listing
        listings[itemId].active = false;

        emit ItemCanceled(itemId);
    }

    function updateListingPrice(uint256 itemId, uint256 newPrice)
        external
        listingExists(itemId)
        onlyItemOwner(itemId)
    {
        require(newPrice > 0, "Price must be > 0");
        listings[itemId].price = newPrice;
    }

    function setMarketplaceFee(uint256 newFee) external onlyOwner {
        require(newFee <= MAX_FEE, "Fee too high");
        marketplaceFee = newFee;
    }

    function getActiveListings() external view returns (Listing[] memory) {
        uint256 activeCount = 0;

        for (uint256 i = 1; i <= _itemIds; i++) {
            if (listings[i].active) {
                activeCount++;
            }
        }

        Listing[] memory activeListings = new Listing[](activeCount);
        uint256 index = 0;

        for (uint256 i = 1; i <= _itemIds; i++) {
            if (listings[i].active) {
                activeListings[index] = listings[i];
                index++;
            }
        }

        return activeListings;
    }
}
```

## DAO Template

### Overview
The DAO Template is designed for decentralized autonomous organizations with governance, voting, treasury management, and proposal systems. It implements OpenZeppelin Governor standards and includes security measures.

### Structure
```
dao-template/
├── contracts/
│   ├── governance/
│   │   ├── Governor.sol
│   │   ├── Timelock.sol
│   │   └── Treasury.sol
│   ├── tokens/
│   │   └── GovernanceToken.sol
│   ├── interfaces/
│   │   ├── IGovernor.sol
│   │   └── ITreasury.sol
│   └── proposals/
│       └── ProposalFactory.sol
├── scripts/
│   ├── deploy-dao.js
│   ├── setup-governance.js
│   └── create-proposal.js
└── test/
    ├── governance/
    └── proposals/
```

### Governor Contract
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorCountingSimple.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorTimelockControl.sol";

contract MyDAO is Governor, GovernorSettings, GovernorCountingSimple, GovernorVotes, GovernorVotesQuorumFraction, GovernorTimelockControl {
    constructor(
        IVotes _token,
        TimelockController _timelock
    )
        Governor("MyDAO")
        GovernorSettings(1, 50400, 0) // 1 block voting delay, 1 week voting period
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(4) // 4% quorum
        GovernorTimelockControl(_timelock)
    {}

    // The following functions are overrides required by Solidity

    function votingDelay()
        public
        view
        override(IGovernor, GovernorSettings)
        returns (uint256)
    {
        return super.votingDelay();
    }

    function votingPeriod()
        public
        view
        override(IGovernor, GovernorSettings)
        returns (uint256)
    {
        return super.votingPeriod();
    }

    function quorum(uint256 blockNumber)
        public
        view
        override(IGovernor, GovernorVotesQuorumFraction)
        returns (uint256)
    {
        return super.quorum(blockNumber);
    }

    function getVotes(address account)
        public
        view
        override(IGovernor, GovernorVotes)
        returns (uint256)
    {
        return super.getVotes(account);
    }

    function proposalThreshold()
        public
        view
        override(Governor, GovernorSettings)
        returns (uint256)
    {
        return super.proposalThreshold();
    }

    function _execute(
        uint256 proposalId,
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) internal override(Governor, GovernorTimelockControl) {
        return super._execute(proposalId, targets, values, calldatas, descriptionHash);
    }

    function _cancel(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) internal override(Governor, GovernorTimelockControl) returns (uint256) {
        return super._cancel(targets, values, calldatas, descriptionHash);
    }

    function _executor()
        internal
        view
        override(Governor, GovernorTimelockControl)
        returns (address)
    {
        return super._executor();
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(Governor, GovernorTimelockControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
```

### Treasury Contract
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract Treasury is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    struct Transaction {
        address recipient;
        IERC20 token;
        uint256 amount;
        string reason;
        uint256 timestamp;
        bool executed;
    }

    mapping(address => uint256) public tokenBalances;
    mapping(uint256 => Transaction) public transactions;
    uint256 public transactionCount;

    uint256 public constant MAX_SINGLE_WITHDRAWAL = 100 ether; // For ETH
    mapping(IERC20 => uint256) public maxTokenWithdrawal;

    event Withdrawal(
        address indexed recipient,
        IERC20 indexed token,
        uint256 amount,
        string reason
    );

    event TokensDeposited(
        address indexed depositor,
        IERC20 indexed token,
        uint256 amount
    );

    modifier onlyOwnerOrDAO() {
        require(
            msg.sender == owner() || msg.sender == _getDAOAddress(),
            "Not authorized"
        );
        _;
    }

    function _getDAOAddress() internal view returns (address) {
        // This would be set during DAO deployment
        return owner(); // Placeholder
    }

    receive() external payable {
        tokenBalances[address(0)] += msg.value;
    }

    function depositTokens(IERC20 token, uint256 amount) external {
        require(amount > 0, "Amount must be > 0");

        token.safeTransferFrom(msg.sender, address(this), amount);
        tokenBalances[address(token)] += amount;

        emit TokensDeposited(msg.sender, token, amount);
    }

    function withdraw(
        address recipient,
        IERC20 token,
        uint256 amount,
        string memory reason
    ) external onlyOwnerOrDAO nonReentrant {
        require(amount > 0, "Amount must be > 0");
        require(recipient != address(0), "Invalid recipient");

        if (address(token) == address(0)) {
            // ETH withdrawal
            require(
                amount <= MAX_SINGLE_WITHDRAWAL,
                "Exceeds max withdrawal"
            );
            require(address(this).balance >= amount, "Insufficient ETH balance");

            payable(recipient).transfer(amount);
            tokenBalances[address(0)] -= amount;
        } else {
            // Token withdrawal
            uint256 maxWithdrawal = maxTokenWithdrawal[token];
            if (maxWithdrawal > 0) {
                require(amount <= maxWithdrawal, "Exceeds max token withdrawal");
            }

            require(tokenBalances[address(token)] >= amount, "Insufficient token balance");

            token.safeTransfer(recipient, amount);
            tokenBalances[address(token)] -= amount;
        }

        transactionCount++;
        transactions[transactionCount] = Transaction({
            recipient: recipient,
            token: token,
            amount: amount,
            reason: reason,
            timestamp: block.timestamp,
            executed: true
        });

        emit Withdrawal(recipient, token, amount, reason);
    }

    function batchWithdraw(
        address[] calldata recipients,
        IERC20[] calldata tokens,
        uint256[] calldata amounts,
        string memory reason
    ) external onlyOwnerOrDAO nonReentrant {
        require(
            recipients.length == tokens.length && tokens.length == amounts.length,
            "Array length mismatch"
        );

        for (uint256 i = 0; i < recipients.length; i++) {
            withdraw(recipients[i], tokens[i], amounts[i], reason);
        }
    }

    function setMaxTokenWithdrawal(IERC20 token, uint256 maxAmount) external onlyOwner {
        maxTokenWithdrawal[token] = maxAmount;
    }

    function getTokenBalance(IERC20 token) external view returns (uint256) {
        if (address(token) == address(0)) {
            return address(this).balance;
        }
        return tokenBalances[address(token)];
    }

    function getTransaction(uint256 transactionId)
        external
        view
        returns (Transaction memory)
    {
        return transactions[transactionId];
    }
}
```

## Template Customization

### Customizing Template Selection
```javascript
// scripts/setup_project.py (modified section)
def create_readme(self, project_path, project_name, template_type, network):
    """Create README.md with template-specific information."""

    template_descriptions = {
        'basic': "Basic smart contract project with standard patterns",
        'defi': "DeFi protocol with staking, governance, and token contracts",
        'nft': "NFT collection with marketplace functionality",
        'dao': "DAO with governance, voting, and treasury management"
    }

    template_features = {
        'basic': [
            "Basic contract structure with events and modifiers",
            "Standard testing patterns",
            "Deployment scripts",
            "Security best practices"
        ],
        'defi': [
            "Governance token with voting",
            "Staking pool with rewards",
            "Timelock governance",
            "DeFi security patterns"
        ],
        'nft': [
            "ERC721 and ERC1155 implementations",
            "NFT marketplace",
            "Metadata management",
            "Royalty support"
        ],
        'dao': [
            "On-chain governance",
            "Treasury management",
            "Proposal system",
            "Voting mechanisms"
        ]
    }

    readme_content = f"""# {project_name}

{template_descriptions.get(template_type, 'Custom project')} built with Hardhat.

## Features

{chr(10).join(f"- {feature}" for feature in template_features.get(template_type, []))}

## Development

### Prerequisites

- Node.js >= 16.0.0
- npm >= 8.0.0

### Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Copy .env.example to .env and fill in your environment variables:
   ```bash
   cp .env.example .env
   ```

3. Compile contracts:
   ```bash
   npx hardhat compile
   ```

4. Run tests:
   ```bash
   npx hardhat test
   ```

### Deployment

Deploy to {network}:
```bash
npx hardhat run scripts/deploy.js --network {network}
```

## Template Specific Instructions

### {template_type.title()} Template

{self.get_template_specific_instructions(template_type)}

## Scripts

- `npx hardhat compile` - Compile contracts
- `npx hardhat test` - Run tests
- `npx hardhat node` - Start local node
- `npx hardhat run scripts/deploy.js --network <network>` - Deploy contracts

## Support

This project was created using the Hardhat Manager skill. For more information, refer to the skill documentation.
"""

    # ... rest of function
```

### Template-Specific Testing
```javascript
// test/helpers/template-helpers.js
const templateHelpers = {
  basic: {
    defaultMigrations: ["MyContract"],
    testPatterns: ["test/unit/*.test.js"],
    gasLimits: {
      deploy: 3000000,
      functions: 100000
    }
  },

  defi: {
    defaultMigrations: ["GovernanceToken", "StakingPool", "RewardsDistributor"],
    testPatterns: ["test/unit/*.test.js", "test/integration/*.test.js"],
    gasLimits: {
      deploy: 8000000,
      functions: 500000
    },
    securityTests: true
  },

  nft: {
    defaultMigrations: ["NFTCollection", "NFTMarketplace"],
    testPatterns: ["test/unit/*.test.js", "test/marketplace/*.test.js"],
    gasLimits: {
      deploy: 5000000,
      mint: 200000,
      transfer: 100000
    },
    metadataTests: true
  },

  dao: {
    defaultMigrations: ["GovernanceToken", "Governor", "Timelock", "Treasury"],
    testPatterns: ["test/governance/*.test.js", "test/proposals/*.test.js"],
    gasLimits: {
      deploy: 10000000,
      proposals: 800000
    },
    governanceTests: true
  }
};

function getTemplateConfig(templateType) {
  return templateHelpers[templateType] || templateHelpers.basic;
}

module.exports = { getTemplateConfig, templateHelpers };
```

This comprehensive template guide provides detailed specifications for each project type, allowing developers to quickly start with the appropriate template and customize it according to their specific requirements.