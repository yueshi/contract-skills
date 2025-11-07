// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Pausable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";

/**
 * @title ERC721Collection
 * @dev Advanced ERC721 NFT Collection with comprehensive features
 * @notice This contract demonstrates enterprise-level NFT collection implementation
 */
contract ERC721Collection is
    ERC721,
    ERC721Enumerable,
    ERC721URIStorage,
    ERC721Pausable,
    ERC721Burnable,
    ERC2981,
    Ownable,
    ReentrancyGuard
{
    using Counters for Counters.Counter;

    // State variables
    Counters.Counter private _tokenIds;

    // Collection configuration
    uint256 public immutable maxSupply;
    uint256 public immutable maxMintPerTx;
    uint256 public immutable mintPrice;
    uint256 public immutable publicSaleStartTime;
    uint256 public immutable allowlistSaleStartTime;

    // Sale phases
    enum SalePhase {
        NOT_STARTED,
        ALLOWLIST,
        PUBLIC,
        ENDED
    }

    // Access control
    mapping(address => bool) public allowlist;
    mapping(address => uint256) public allowlistMinted;
    uint256 public allowlistMintLimit = 2;

    // Royalty configuration
    address public royaltyReceiver;
    uint96 public royaltyFeeInBps = 500; // 5%

    // Metadata
    string private baseTokenURI;
    string private contractURI;

    // Events
    event Minted(address indexed to, uint256 indexed tokenId, string tokenURI);
    event BatchMinted(address indexed to, uint256[] tokenIds);
    event AllowlistUpdated(address indexed user, bool allowed);
    event SalePhaseUpdated(SalePhase phase);
    event BaseURIUpdated(string newBaseURI);
    event ContractURIUpdated(string newContractURI);
    event RoyaltyUpdated(address indexed receiver, uint96 feeInBps);
    event Paused(address indexed account);
    event Unpaused(address indexed account);

    // Modifiers
    modifier onlyDuringSale() {
        require(salePhase() != SalePhase.NOT_STARTED, "Sale not started");
        require(salePhase() != SalePhase.ENDED, "Sale ended");
        _;
    }

    modifier validateMintAmount(uint256 amount) {
        require(amount > 0, "Amount must be > 0");
        require(amount <= maxMintPerTx, "Exceeds max per transaction");
        require(_tokenIds.current() + amount <= maxSupply, "Exceeds max supply");
        _;
    }

    modifier validatePayment(uint256 amount) {
        require(msg.value >= mintPrice * amount, "Insufficient payment");
        _;
    }

    /**
     * @dev Constructor
     * @param name_ Collection name
     * @param symbol_ Collection symbol
     * @param maxSupply_ Maximum supply
     * @param maxMintPerTx_ Maximum mint per transaction
     * @param mintPrice_ Price per NFT in wei
     * @param publicSaleStartTime_ Public sale start timestamp
     * @param allowlistSaleStartTime_ Allowlist sale start timestamp
     * @param baseURI_ Base URI for token metadata
     * @param contractURI_ Contract metadata URI
     */
    constructor(
        string memory name_,
        string memory symbol_,
        uint256 maxSupply_,
        uint256 maxMintPerTx_,
        uint256 mintPrice_,
        uint256 publicSaleStartTime_,
        uint256 allowlistSaleStartTime_,
        string memory baseURI_,
        string memory contractURI_
    ) ERC721(name_, symbol_) {
        require(maxSupply_ > 0, "Max supply must be > 0");
        require(maxMintPerTx_ > 0, "Max mint per tx must be > 0");
        require(publicSaleStartTime_ > block.timestamp, "Public sale start time must be in future");
        require(allowlistSaleStartTime_ <= publicSaleStartTime_, "Allowlist start must be before public");

        maxSupply = maxSupply_;
        maxMintPerTx = maxMintPerTx_;
        mintPrice = mintPrice_;
        publicSaleStartTime = publicSaleStartTime_;
        allowlistSaleStartTime = allowlistSaleStartTime_;
        baseTokenURI = baseURI_;
        contractURI = contractURI_;
        royaltyReceiver = msg.sender;

        transferOwnership(msg.sender);
    }

    /**
     * @dev Mint function for allowlist
     * @param amount Number of NFTs to mint
     */
    function mintAllowlist(uint256 amount)
        external
        payable
        nonReentrant
        validateMintAmount(amount)
        validatePayment(amount)
        onlyDuringSale
    {
        require(salePhase() == SalePhase.ALLOWLIST, "Allowlist sale not active");
        require(allowlist[msg.sender], "Not on allowlist");
        require(
            allowlistMinted[msg.sender] + amount <= allowlistMintLimit,
            "Exceeds allowlist limit"
        );

        allowlistMinted[msg.sender] += amount;
        _mintTokens(msg.sender, amount);
        _refundExcess(msg.value - (mintPrice * amount));
    }

    /**
     * @dev Mint function for public sale
     * @param amount Number of NFTs to mint
     */
    function mintPublic(uint256 amount)
        external
        payable
        nonReentrant
        validateMintAmount(amount)
        validatePayment(amount)
        onlyDuringSale
    {
        require(salePhase() == SalePhase.PUBLIC, "Public sale not active");

        _mintTokens(msg.sender, amount);
        _refundExcess(msg.value - (mintPrice * amount));
    }

    /**
     * @dev Admin mint function (for team, giveaways, etc.)
     * @param to Recipient address
     * @param amount Number of NFTs to mint
     */
    function adminMint(address to, uint256 amount) external onlyOwner validateMintAmount(amount) {
        _mintTokens(to, amount);
    }

    /**
     * @dev Batch mint function
     * @param to Recipient address
     * @param amounts Array of mint amounts (for different URIs)
     */
    function batchMint(address to, uint256[] calldata amounts)
        external
        onlyOwner
        validateMintAmount(amounts.length)
    {
        require(to != address(0), "Invalid recipient");
        uint256 totalAmount = 0;
        for (uint256 i = 0; i < amounts.length; i++) {
            totalAmount += amounts[i];
        }
        require(totalAmount <= maxSupply - _tokenIds.current(), "Exceeds max supply");

        for (uint256 i = 0; i < amounts.length; i++) {
            _mintTokens(to, amounts[i]);
        }

        emit BatchMinted(to, new uint256[](0)); // Event with token IDs would need tracking
    }

    /**
     * @dev Internal mint function
     * @param to Recipient address
     * @param amount Number of NFTs to mint
     */
    function _mintTokens(address to, uint256 amount) internal {
        for (uint256 i = 0; i < amount; i++) {
            _tokenIds.increment();
            uint256 newId = _tokenIds.current();

            _safeMint(to, newId);
            _setTokenURI(newId, string(abi.encodePacked(baseTokenURI, _toString(newId), ".json")));

            emit Minted(to, newId, tokenURI(newId));
        }
    }

    /**
     * @dev Refund excess payment
     * @param excess Amount to refund
     */
    function _refundExcess(uint256 excess) internal {
        if (excess > 0) {
            payable(msg.sender).transfer(excess);
        }
    }

    /**
     * @dev Get current sale phase
     */
    function salePhase() public view returns (SalePhase) {
        if (block.timestamp < allowlistSaleStartTime) {
            return SalePhase.NOT_STARTED;
        } else if (block.timestamp < publicSaleStartTime) {
            return SalePhase.ALLOWLIST;
        } else if (block.timestamp < publicSaleStartTime + (365 days)) {
            return SalePhase.PUBLIC;
        } else {
            return SalePhase.ENDED;
        }
    }

    /**
     * @dev Get current sale phase as string
     */
    function getSalePhaseString() external view returns (string memory) {
        SalePhase phase = salePhase();
        if (phase == SalePhase.NOT_STARTED) return "NOT_STARTED";
        if (phase == SalePhase.ALLOWLIST) return "ALLOWLIST";
        if (phase == SalePhase.PUBLIC) return "PUBLIC";
        return "ENDED";
    }

    /**
     * @dev Update allowlist
     * @param users Array of user addresses
     * @param allowed Array of allowlist status
     */
    function updateAllowlist(address[] calldata users, bool[] calldata allowed)
        external
        onlyOwner
    {
        require(users.length == allowed.length, "Array length mismatch");
        for (uint256 i = 0; i < users.length; i++) {
            allowlist[users[i]] = allowed[i];
            emit AllowlistUpdated(users[i], allowed[i]);
        }
    }

    /**
     * @dev Set base URI
     * @param newBaseURI New base URI
     */
    function setBaseURI(string memory newBaseURI) external onlyOwner {
        baseTokenURI = newBaseURI;
        emit BaseURIUpdated(newBaseURI);
    }

    /**
     * @dev Set contract URI
     * @param newContractURI New contract URI
     */
    function setContractURI(string memory newContractURI) external onlyOwner {
        contractURI = newContractURI;
        emit ContractURIUpdated(newContractURI);
    }

    /**
     * @dev Set royalty
     * @param receiver Royalty receiver address
     * @param feeInBps Royalty fee in basis points (e.g., 500 = 5%)
     */
    function setRoyalty(address receiver, uint96 feeInBps) external onlyOwner {
        require(receiver != address(0), "Invalid receiver");
        require(feeInBps <= 1000, "Fee cannot exceed 10%"); // Max 10%
        royaltyReceiver = receiver;
        royaltyFeeInBps = feeInBps;
        _setDefaultRoyalty(receiver, feeInBps);
        emit RoyaltyUpdated(receiver, feeInBps);
    }

    /**
     * @dev Withdraw funds
     */
    function withdraw() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No funds to withdraw");
        payable(owner()).transfer(balance);
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
     * @dev Get total minted
     */
    function totalMinted() external view returns (uint256) {
        return _tokenIds.current();
    }

    /**
     * @dev Get tokens of owner
     */
    function tokensOfOwner(address owner_) external view returns (uint256[] memory) {
        return _tokenOfOwner(owner_);
    }

    // Required overrides
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId,
        uint256 batchSize
    ) internal override(ERC721, ERC721Enumerable, ERC721Pausable) {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
    }

    function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage) {
        super._burn(tokenId);
    }

    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (string memory)
    {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721Enumerable, ERC2981)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    // The following functions are overrides required by Solidity.
    function _increaseBalance(address account, uint128 value)
        internal
        override(ERC721, ERC721Enumerable)
    {
        super._increaseBalance(account, value);
    }
}
