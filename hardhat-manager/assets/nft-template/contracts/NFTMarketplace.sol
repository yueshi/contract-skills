// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/interfaces/IERC2981.sol";

/**
 * @title NFTMarketplace
 * @dev NFT Marketplace with listing, buying, and auction functionality
 * @notice Supports both fixed-price sales and auctions
 */
contract NFTMarketplace is IERC721Receiver, Ownable, ReentrancyGuard, Pausable {
    using Counters for Counters.Counter;

    // Structs
    struct Listing {
        address nftContract;
        uint256 tokenId;
        address seller;
        uint256 price;
        bool isAuction;
        uint256 auctionEndTime;
        address highestBidder;
        uint256 highestBid;
        bool isActive;
    }

    struct Bid {
        address bidder;
        uint256 amount;
        uint256 timestamp;
    }

    // State variables
    Counters.Counter private _listingIds;
    mapping(uint256 => Listing) public listings;
    mapping(uint256 => mapping(address => uint256)) public pendingReturns; // For auction refunds
    mapping(address => bool) public acceptedTokens;

    // Fees
    uint96 public feeInBps = 250; // 2.5%
    address public feeReceiver;

    // Events
    event ListingCreated(
        uint256 indexed listingId,
        address indexed nftContract,
        uint256 indexed tokenId,
        address seller,
        uint256 price,
        bool isAuction,
        uint256 auctionEndTime
    );
    event ListingCancelled(uint256 indexed listingId);
    event NFTSold(
        uint256 indexed listingId,
        address indexed nftContract,
        uint256 indexed tokenId,
        address seller,
        address buyer,
        uint256 price
    );
    event BidPlaced(
        uint256 indexed listingId,
        address indexed bidder,
        uint256 amount
    );
    event AuctionSettled(
        uint256 indexed listingId,
        address indexed winner,
        uint256 amount
    );
    event FeeUpdated(uint96 newFee);
    event TokenAccepted(address indexed token, bool accepted);

    // Modifiers
    modifier validListing(uint256 listingId) {
        require(listings[listingId].isActive, "Listing not active");
        _;
    }

    modifier notContract(address account) {
        require(account == msg.sender, "Caller must be externally owned");
        _;
    }

    /**
     * @dev Constructor
     * @param feeReceiver_ Fee receiver address
     * @param initialFeeInBps Initial fee in basis points
     */
    constructor(address feeReceiver_, uint96 initialFeeInBps) {
        require(feeReceiver_ != address(0), "Invalid fee receiver");
        require(initialFeeInBps <= 1000, "Fee cannot exceed 10%"); // Max 10%

        feeReceiver = feeReceiver_;
        feeInBps = initialFeeInBps;

        transferOwnership(msg.sender);
    }

    /**
     * @dev List NFT for sale (fixed price)
     * @param nftContract NFT contract address
     * @param tokenId Token ID
     * @param price Sale price
     */
    function listNFT(
        address nftContract,
        uint256 tokenId,
        uint256 price
    ) external nonReentrant notContract whenNotPaused {
        require(price > 0, "Price must be > 0");
        require(acceptedTokens[nftContract] || owner() == msg.sender, "NFT not accepted");

        IERC721(nftContract).safeTransferFrom(msg.sender, address(this), tokenId);

        _listingIds.increment();
        uint256 listingId = _listingIds.current();

        listings[listingId] = Listing({
            nftContract: nftContract,
            tokenId: tokenId,
            seller: msg.sender,
            price: price,
            isAuction: false,
            auctionEndTime: 0,
            highestBidder: address(0),
            highestBid: 0,
            isActive: true
        });

        emit ListingCreated(listingId, nftContract, tokenId, msg.sender, price, false, 0);
    }

    /**
     * @dev List NFT for auction
     * @param nftContract NFT contract address
     * @param tokenId Token ID
     * @param startingPrice Starting bid price
     * @param auctionDuration Auction duration in seconds
     */
    function listNFTForAuction(
        address nftContract,
        uint256 tokenId,
        uint256 startingPrice,
        uint256 auctionDuration
    ) external nonReentrant notContract whenNotPaused {
        require(startingPrice > 0, "Starting price must be > 0");
        require(auctionDuration >= 300, "Auction duration must be at least 5 minutes"); // Min 5 min
        require(auctionDuration <= 604800, "Auction duration cannot exceed 7 days"); // Max 7 days
        require(acceptedTokens[nftContract] || owner() == msg.sender, "NFT not accepted");

        IERC721(nftContract).safeTransferFrom(msg.sender, address(this), tokenId);

        _listingIds.increment();
        uint256 listingId = _listingIds.current();

        listings[listingId] = Listing({
            nftContract: nftContract,
            tokenId: tokenId,
            seller: msg.sender,
            price: startingPrice,
            isAuction: true,
            auctionEndTime: block.timestamp + auctionDuration,
            highestBidder: address(0),
            highestBid: startingPrice,
            isActive: true
        });

        emit ListingCreated(
            listingId,
            nftContract,
            tokenId,
            msg.sender,
            startingPrice,
            true,
            block.timestamp + auctionDuration
        );
    }

    /**
     * @dev Buy NFT (fixed price)
     * @param listingId Listing ID
     */
    function buyNFT(uint256 listingId) external payable nonReentrant notContract whenNotPaused {
        Listing storage listing = listings[listingId];
        require(!listing.isAuction, "Not a fixed price listing");
        require(msg.value >= listing.price, "Insufficient payment");

        address seller = listing.seller;
        listing.isActive = false;

        IERC721(listing.nftContract).safeTransferFrom(address(this), msg.sender, listing.tokenId);

        uint256 fee = (listing.price * feeInBps) / 10000;
        uint256 sellerAmount = listing.price - fee;

        if (fee > 0) {
            payable(feeReceiver).transfer(fee);
        }
        payable(seller).transfer(sellerAmount);

        // Refund excess
        if (msg.value > listing.price) {
            payable(msg.sender).transfer(msg.value - listing.price);
        }

        emit NFTSold(listingId, listing.nftContract, listing.tokenId, seller, msg.sender, listing.price);
    }

    /**
     * @dev Place bid on auction
     * @param listingId Listing ID
     */
    function placeBid(uint256 listingId) external payable nonReentrant notContract whenNotPaused {
        Listing storage listing = listings[listingId];
        require(listing.isAuction, "Not an auction listing");
        require(listing.isActive, "Listing not active");
        require(block.timestamp < listing.auctionEndTime, "Auction ended");
        require(msg.value > listing.highestBid, "Bid must be higher than current highest");

        address previousHighestBidder = listing.highestBidder;
        uint256 previousHighestBid = listing.highestBid;

        listing.highestBidder = msg.sender;
        listing.highestBid = msg.value;

        pendingReturns[listingId][previousHighestBidder] += previousHighestBid;

        emit BidPlaced(listingId, msg.sender, msg.value);
    }

    /**
     * @dev Settle auction (can be called by anyone after auction ends)
     * @param listingId Listing ID
     */
    function settleAuction(uint256 listingId) external nonReentrant {
        Listing storage listing = listings[listingId];
        require(listing.isAuction, "Not an auction listing");
        require(listing.isActive, "Listing not active");
        require(block.timestamp >= listing.auctionEndTime, "Auction not ended");

        listing.isActive = false;

        if (listing.highestBidder != address(0)) {
            IERC721(listing.nftContract).safeTransferFrom(
                address(this),
                listing.highestBidder,
                listing.tokenId
            );

            uint256 fee = (listing.highestBid * feeInBps) / 10000;
            uint256 sellerAmount = listing.highestBid - fee;

            if (fee > 0) {
                payable(feeReceiver).transfer(fee);
            }
            payable(listing.seller).transfer(sellerAmount);

            emit AuctionSettled(listingId, listing.highestBidder, listing.highestBid);
        } else {
            IERC721(listing.nftContract).safeTransferFrom(
                address(this),
                listing.seller,
                listing.tokenId
            );
        }
    }

    /**
     * @dev Cancel listing (seller only)
     * @param listingId Listing ID
     */
    function cancelListing(uint256 listingId) external nonReentrant {
        Listing storage listing = listings[listingId];
        require(listing.seller == msg.sender || owner() == msg.sender, "Not listing owner");
        require(listing.isActive, "Listing not active");

        listing.isActive = false;

        IERC721(listing.nftContract).safeTransferFrom(address(this), listing.seller, listing.tokenId);

        emit ListingCancelled(listingId);
    }

    /**
     * @dev Withdraw pending returns (for bidders who were outbid)
     * @param listingId Listing ID
     */
    function withdraw(uint256 listingId) external nonReentrant {
        uint256 amount = pendingReturns[listingId][msg.sender];
        require(amount > 0, "No pending returns");

        pendingReturns[listingId][msg.sender] = 0;
        payable(msg.sender).transfer(amount);
    }

    /**
     * @dev Get listing info
     * @param listingId Listing ID
     */
    function getListing(uint256 listingId) external view returns (Listing memory) {
        return listings[listingId];
    }

    /**
     * @dev Get active listings count
     */
    function getActiveListingsCount() external view returns (uint256) {
        uint256 count = 0;
        for (uint256 i = 1; i <= _listingIds.current(); i++) {
            if (listings[i].isActive) {
                count++;
            }
        }
        return count;
    }

    /**
     * @dev Get listings by seller
     * @param seller Seller address
     */
    function getListingsBySeller(address seller) external view returns (uint256[] memory) {
        uint256[] memory sellerListings = new uint256[](_listingIds.current());
        uint256 count = 0;
        for (uint256 i = 1; i <= _listingIds.current(); i++) {
            if (listings[i].seller == seller) {
                sellerListings[count] = i;
                count++;
            }
        }
        return _sliceArray(sellerListings, count);
    }

    /**
     * @dev Set accepted NFT token
     * @param nftContract NFT contract address
     * @param accepted Whether to accept this NFT
     */
    function setAcceptedNFT(address nftContract, bool accepted) external onlyOwner {
        acceptedTokens[nftContract] = accepted;
        emit TokenAccepted(nftContract, accepted);
    }

    /**
     * @dev Update fee
     * @param newFeeInBps New fee in basis points
     */
    function updateFee(uint96 newFeeInBps) external onlyOwner {
        require(newFeeInBps <= 1000, "Fee cannot exceed 10%");
        feeInBps = newFeeInBps;
        emit FeeUpdated(newFeeInBps);
    }

    /**
     * @dev Update fee receiver
     * @param newReceiver New fee receiver
     */
    function updateFeeReceiver(address newReceiver) external onlyOwner {
        require(newReceiver != address(0), "Invalid receiver");
        feeReceiver = newReceiver;
    }

    /**
     * @dev Emergency withdrawal (owner only)
     */
    function emergencyWithdraw() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
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

    // Required override
    function onERC721Received(
        address operator,
        address from,
        uint256 tokenId,
        bytes calldata data
    ) external pure override returns (bytes4) {
        return IERC721Receiver.onERC721Received.selector;
    }

    // Internal helper
    function _sliceArray(uint256[] memory array, uint256 length) internal pure returns (uint256[] memory) {
        uint256[] memory result = new uint256[](length);
        for (uint256 i = 0; i < length; i++) {
            result[i] = array[i];
        }
        return result;
    }
}
