const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("NFTMarketplace", function () {
  let nftMarketplace, mockNFT, mockERC20;
  let owner, seller, buyer, feeReceiver;

  beforeEach(async function () {
    [owner, seller, buyer, feeReceiver] = await ethers.getSigners();

    // Deploy mock NFT
    const MockNFT = await ethers.getContractFactory("MockNFT");
    mockNFT = await MockNFT.deploy();

    // Deploy mock ERC20
    const MockERC20 = await ethers.getContractFactory("MockERC20");
    mockERC20 = await MockERC20.deploy("Mock Token", "MTK", ethers.utils.parseEther("10000"));

    // Deploy marketplace
    const NFTMarketplace = await ethers.getContractFactory("NFTMarketplace");
    nftMarketplace = await NFTMarketplace.deploy(feeReceiver.address, 250); // 2.5% fee
  });

  describe("Deployment", function () {
    it("Should set correct fee receiver", async function () {
      expect(await nftMarketplace.feeReceiver()).to.equal(feeReceiver.address);
    });

    it("Should set correct fee", async function () {
      expect(await nftMarketplace.feeInBps()).to.equal(250);
    });

    it("Owner should be set correctly", async function () {
      expect(await nftMarketplace.owner()).to.equal(owner.address);
    });
  });

  describe("Listing NFTs", function () {
    beforeEach(async function () {
      // Mint NFT to seller
      await mockNFT.mint(seller.address, 1);
    });

    it("Should list NFT for sale", async function () {
      const price = ethers.utils.parseEther("1");

      await mockNFT.connect(seller).approve(nftMarketplace.address, 1);

      await expect(
        nftMarketplace.connect(seller).listNFT(mockNFT.address, 1, price)
      )
        .to.emit(nftMarketplace, "ListingCreated")
        .withArgs(1, mockNFT.address, 1, seller.address, price, false, 0);

      expect(await mockNFT.ownerOf(1)).to.equal(nftMarketplace.address);
    });

    it("Should list NFT for auction", async function () {
      const startingPrice = ethers.utils.parseEther("1");
      const duration = 3600; // 1 hour

      await mockNFT.connect(seller).approve(nftMarketplace.address, 1);

      await expect(
        nftMarketplace.connect(seller).listNFTForAuction(mockNFT.address, 1, startingPrice, duration)
      )
        .to.emit(nftMarketplace, "ListingCreated")
        .withArgs(
          1,
          mockNFT.address,
          1,
          seller.address,
          startingPrice,
          true,
          (await ethers.provider.getBlock("latest")).timestamp + duration
        );

      expect(await mockNFT.ownerOf(1)).to.equal(nftMarketplace.address);
    });

    it("Cannot list with zero price", async function () {
      await mockNFT.connect(seller).approve(nftMarketplace.address, 1);

      await expect(
        nftMarketplace.connect(seller).listNFT(mockNFT.address, 1, 0)
      ).to.be.revertedWith("Price must be > 0");
    });

    it("Cannot list NFT without approval", async function () {
      const price = ethers.utils.parseEther("1");
      await expect(
        nftMarketplace.connect(seller).listNFT(mockNFT.address, 1, price)
      ).to.be.revertedWith("ERC721: transfer caller is not owner nor approved");
    });

    it("Cannot list NFT not owned", async function () {
      const price = ethers.utils.parseEther("1");
      await mockNFT.connect(seller).approve(nftMarketplace.address, 1);

      await expect(
        nftMarketplace.connect(buyer).listNFT(mockNFT.address, 1, price)
      ).to.be.revertedWith("ERC721: transfer caller is not owner nor approved");
    });
  });

  describe("Buying NFTs", function () {
    const price = ethers.utils.parseEther("1");
    let listingId;

    beforeEach(async function () {
      // List NFT
      await mockNFT.mint(seller.address, 1);
      await mockNFT.connect(seller).approve(nftMarketplace.address, 1);
      const tx = await nftMarketplace.connect(seller).listNFT(mockNFT.address, 1, price);
      const receipt = await tx.wait();
      listingId = receipt.events.find(e => e.event === "ListingCreated").args.listingId;
    });

    it("Should buy NFT", async function () {
      const fee = price.mul(250).div(10000);
      const sellerAmount = price.sub(fee);
      const sellerBalanceBefore = await ethers.provider.getBalance(seller.address);
      const feeReceiverBalanceBefore = await ethers.provider.getBalance(feeReceiver.address);

      await expect(
        nftMarketplace.connect(buyer).buyNFT(listingId, { value: price })
      )
        .to.emit(nftMarketplace, "NFTSold")
        .withArgs(listingId, mockNFT.address, 1, seller.address, buyer.address, price);

      expect(await mockNFT.ownerOf(1)).to.equal(buyer.address);
      expect((await ethers.provider.getBalance(seller.address)).sub(sellerBalanceBefore)).to.equal(sellerAmount);
      expect((await ethers.provider.getBalance(feeReceiver.address)).sub(feeReceiverBalanceBefore)).to.equal(fee);
    });

    it("Should refund excess payment", async function () {
      const excess = ethers.utils.parseEther("0.5");
      const buyerBalanceBefore = await ethers.provider.getBalance(buyer.address);
      const totalValue = price.add(excess);

      await nftMarketplace.connect(buyer).buyNFT(listingId, { value: totalValue });

      const buyerBalanceAfter = await ethers.provider.getBalance(buyer.address);
      const gasUsed = buyerBalanceBefore.sub(buyerBalanceAfter);
      // Buyer should have spent approximately price + gas
      expect(buyerBalanceBefore.sub(buyerBalanceAfter)).to.be.gt(price.sub(ethers.utils.parseEther("0.01"))); // Account for gas
      expect(buyerBalanceBefore.sub(buyerBalanceAfter)).to.be.lt(price.add(ethers.utils.parseEther("0.1")));
    });

    it("Cannot buy with insufficient payment", async function () {
      await expect(
        nftMarketplace.connect(buyer).buyNFT(listingId, { value: price.sub(1) })
      ).to.be.revertedWith("Insufficient payment");
    });

    it("Cannot buy already sold NFT", async function () {
      await nftMarketplace.connect(buyer).buyNFT(listingId, { value: price });

      await expect(
        nftMarketplace.connect(seller).buyNFT(listingId, { value: price })
      ).to.be.revertedWith("Listing not active");
    });

    it("Cannot buy from auction listing", async function () {
      // List for auction
      await mockNFT.mint(seller.address, 2);
      await mockNFT.connect(seller).approve(nftMarketplace.address, 2);
      const tx = await nftMarketplace.connect(seller).listNFTForAuction(mockNFT.address, 2, price, 3600);
      const receipt = await tx.wait();
      const auctionListingId = receipt.events.find(e => e.event === "ListingCreated").args.listingId;

      await expect(
        nftMarketplace.connect(buyer).buyNFT(auctionListingId, { value: price })
      ).to.be.revertedWith("Not a fixed price listing");
    });
  });

  describe("Auctions", function () {
    const startingPrice = ethers.utils.parseEther("1");
    let auctionDuration;
    let listingId;

    beforeEach(async function () {
      // List for auction
      await mockNFT.mint(seller.address, 1);
      await mockNFT.connect(seller).approve(nftMarketplace.address, 1);
      auctionDuration = 3600; // 1 hour
      const tx = await nftMarketplace.connect(seller).listNFTForAuction(
        mockNFT.address,
        1,
        startingPrice,
        auctionDuration
      );
      const receipt = await tx.wait();
      listingId = receipt.events.find(e => e.event === "ListingCreated").args.listingId;
    });

    it("Should place bid", async function () {
      const bidAmount = ethers.utils.parseEther("1.5");

      await expect(
        nftMarketplace.connect(buyer).placeBid(listingId, { value: bidAmount })
      )
        .to.emit(nftMarketplace, "BidPlaced")
        .withArgs(listingId, buyer.address, bidAmount);

      const listing = await nftMarketplace.getListing(listingId);
      expect(listing.highestBidder).to.equal(buyer.address);
      expect(listing.highestBid).to.equal(bidAmount);
    });

    it("Should reject bid lower than highest", async function () {
      const bidAmount1 = ethers.utils.parseEther("1.5");
      const bidAmount2 = ethers.utils.parseEther("1.2");

      await nftMarketplace.connect(buyer).placeBid(listingId, { value: bidAmount1 });

      await expect(
        nftMarketplace.connect(seller).placeBid(listingId, { value: bidAmount2 })
      ).to.be.revertedWith("Bid must be higher than current highest");
    });

    it("Should reject bid after auction ended", async function () {
      const bidAmount = ethers.utils.parseEther("1.5");

      // Fast forward time
      await ethers.provider.send("evm_increaseTime", [auctionDuration + 1]);
      await ethers.provider.send("evm_mine", []);

      await expect(
        nftMarketplace.connect(buyer).placeBid(listingId, { value: bidAmount })
      ).to.be.revertedWith("Auction ended");
    });

    it("Should settle auction with winner", async function () {
      const bidAmount = ethers.utils.parseEther("1.5");
      await nftMarketplace.connect(buyer).placeBid(listingId, { value: bidAmount });

      // Fast forward time
      await ethers.provider.send("evm_increaseTime", [auctionDuration + 1]);
      await ethers.provider.send("evm_mine", []);

      await expect(nftMarketplace.settleAuction(listingId))
        .to.emit(nftMarketplace, "AuctionSettled")
        .withArgs(listingId, buyer.address, bidAmount);

      expect(await mockNFT.ownerOf(1)).to.equal(buyer.address);
    });

    it("Should settle auction with no bids", async function () {
      // Fast forward time
      await ethers.provider.send("evm_increaseTime", [auctionDuration + 1]);
      await ethers.provider.send("evm_mine", []);

      await nftMarketplace.settleAuction(listingId);

      expect(await mockNFT.ownerOf(1)).to.equal(seller.address);
    });

    it("Should allow withdraw of previous highest bid", async function () {
      const bidAmount1 = ethers.utils.parseEther("1.5");
      const bidAmount2 = ethers.utils.parseEther("2");

      await nftMarketplace.connect(buyer).placeBid(listingId, { value: bidAmount1 });
      await nftMarketplace.connect(seller).placeBid(listingId, { value: bidAmount2 });

      const sellerBalanceBefore = await ethers.provider.getBalance(seller.address);

      await nftMarketplace.connect(seller).withdraw(listingId);

      const sellerBalanceAfter = await ethers.provider.getBalance(seller.address);
      expect(sellerBalanceAfter.sub(sellerBalanceBefore)).to.be.gt(bidAmount1.sub(ethers.utils.parseEther("0.01"))); // Account for gas
    });
  });

  describe("Cancelling Listings", function () {
    const price = ethers.utils.parseEther("1");

    it("Seller can cancel listing", async function () {
      // List NFT
      await mockNFT.mint(seller.address, 1);
      await mockNFT.connect(seller).approve(nftMarketplace.address, 1);
      const tx = await nftMarketplace.connect(seller).listNFT(mockNFT.address, 1, price);
      const receipt = await tx.wait();
      const listingId = receipt.events.find(e => e.event === "ListingCreated").args.listingId;

      await expect(nftMarketplace.connect(seller).cancelListing(listingId))
        .to.emit(nftMarketplace, "ListingCancelled")
        .withArgs(listingId);

      expect(await mockNFT.ownerOf(1)).to.equal(seller.address);
    });

    it("Owner can cancel any listing", async function () {
      // List NFT
      await mockNFT.mint(seller.address, 1);
      await mockNFT.connect(seller).approve(nftMarketplace.address, 1);
      const tx = await nftMarketplace.connect(seller).listNFT(mockNFT.address, 1, price);
      const receipt = await tx.wait();
      const listingId = receipt.events.find(e => e.event === "ListingCreated").args.listingId;

      // Owner cancels
      await nftMarketplace.connect(owner).cancelListing(listingId);

      expect(await mockNFT.ownerOf(1)).to.equal(seller.address);
    });

    it("Non-seller cannot cancel listing", async function () {
      // List NFT
      await mockNFT.mint(seller.address, 1);
      await mockNFT.connect(seller).approve(nftMarketplace.address, 1);
      const tx = await nftMarketplace.connect(seller).listNFT(mockNFT.address, 1, price);
      const receipt = await tx.wait();
      const listingId = receipt.events.find(e => e.event === "ListingCreated").args.listingId;

      // Buyer tries to cancel
      await expect(
        nftMarketplace.connect(buyer).cancelListing(listingId)
      ).to.be.revertedWith("Not listing owner");
    });
  });

  describe("Admin Functions", function () {
    it("Owner can update fee", async function () {
      const newFee = 300; // 3%
      await nftMarketplace.updateFee(newFee);
      expect(await nftMarketplace.feeInBps()).to.equal(newFee);
    });

    it("Cannot set fee above 10%", async function () {
      await expect(
        nftMarketplace.updateFee(1001)
      ).to.be.revertedWith("Fee cannot exceed 10%");
    });

    it("Owner can update fee receiver", async function () {
      await nftMarketplace.updateFeeReceiver(user1.address);
      expect(await nftMarketplace.feeReceiver()).to.equal(user1.address);
    });

    it("Owner can set accepted NFT", async function () {
      await nftMarketplace.setAcceptedNFT(mockNFT.address, true);
      // This would allow listing even if not accepted initially
    });

    it("Non-owner cannot update settings", async function () {
      await expect(
        nftMarketplace.connect(user1).updateFee(300)
      ).to.be.revertedWith("Ownable: caller is not the owner");

      await expect(
        nftMarketplace.connect(user1).updateFeeReceiver(user1.address)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("View Functions", function () {
    it("Should get listing info", async function () {
      await mockNFT.mint(seller.address, 1);
      await mockNFT.connect(seller).approve(nftMarketplace.address, 1);
      const tx = await nftMarketplace.connect(seller).listNFT(mockNFT.address, 1, ethers.utils.parseEther("1"));
      const receipt = await tx.wait();
      const listingId = receipt.events.find(e => e.event === "ListingCreated").args.listingId;

      const listing = await nftMarketplace.getListing(listingId);
      expect(listing.nftContract).to.equal(mockNFT.address);
      expect(listing.tokenId).to.equal(1);
      expect(listing.seller).to.equal(seller.address);
      expect(listing.price).to.equal(ethers.utils.parseEther("1"));
    });

    it("Should get listings by seller", async function () {
      await mockNFT.mint(seller.address, 1);
      await mockNFT.connect(seller).approve(nftMarketplace.address, 1);
      await nftMarketplace.connect(seller).listNFT(mockNFT.address, 1, ethers.utils.parseEther("1"));

      const listings = await nftMarketplace.getListingsBySeller(seller.address);
      expect(listings.length).to.equal(1);
      expect(listings[0]).to.equal(1);
    });
  });

  describe("Pausable", function () {
    it("Owner can pause", async function () {
      await nftMarketplace.pause();
      expect(await nftMarketplace.paused()).to.be.true;
    });

    it("Owner can unpause", async function () {
      await nftMarketplace.pause();
      await nftMarketplace.unpause();
      expect(await nftMarketplace.paused()).to.be.false;
    });

    it("Cannot list when paused", async function () {
      await mockNFT.mint(seller.address, 1);
      await mockNFT.connect(seller).approve(nftMarketplace.address, 1);
      await nftMarketplace.pause();

      await expect(
        nftMarketplace.connect(seller).listNFT(mockNFT.address, 1, ethers.utils.parseEther("1"))
      ).to.be.revertedWith("Pausable: paused");
    });

    it("Non-owner cannot pause", async function () {
      await expect(
        nftMarketplace.connect(user1).pause()
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Emergency Withdraw", function () {
    it("Owner can emergency withdraw", async function () {
      // List and buy NFT to generate funds
      await mockNFT.mint(seller.address, 1);
      await mockNFT.connect(seller).approve(nftMarketplace.address, 1);
      await nftMarketplace.connect(seller).listNFT(mockNFT.address, 1, ethers.utils.parseEther("1"));
      await nftMarketplace.connect(buyer).buyNFT(1, { value: ethers.utils.parseEther("1") });

      const ownerBalanceBefore = await ethers.provider.getBalance(owner.address);
      const tx = await nftMarketplace.emergencyWithdraw();
      const receipt = await tx.wait();
      const gasCost = receipt.gasUsed.mul(receipt.effectiveGasPrice);

      const ownerBalanceAfter = await ethers.provider.getBalance(owner.address);
      expect(ownerBalanceAfter.sub(ownerBalanceBefore).add(gasCost)).to.be.gt(0); // Fee earned
    });

    it("Non-owner cannot emergency withdraw", async function () {
      await expect(
        nftMarketplace.connect(user1).emergencyWithdraw()
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });
});
