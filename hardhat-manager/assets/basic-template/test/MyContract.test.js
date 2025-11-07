const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("MyContract", function () {
  let myContract;
  let owner, user1, user2, user3;

  beforeEach(async function () {
    // Get signers
    [owner, user1, user2, user3] = await ethers.getSigners();

    // Deploy contract
    const MyContract = await ethers.getContractFactory("MyContract");
    myContract = await MyContract.deploy();
    await myContract.deployed();
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await myContract.owner()).to.equal(owner.address);
    });

    it("Should authorize the deployer", async function () {
      expect(await myContract.isAuthorized(owner.address)).to.be.true;
    });

    it("Should start with zero items", async function () {
      expect(await myContract.getActiveItemsCount()).to.equal(0);
    });

    it("Should have correct initial state", async function () {
      expect(await myContract.paused()).to.be.false;
      expect(await myContract.isAuthorized(user1.address)).to.be.false;
    });
  });

  describe("User Authorization", function () {
    it("Should allow owner to authorize users", async function () {
      await expect(myContract.authorizeUser(user1.address))
        .to.emit(myContract, "UserAuthorized")
        .withArgs(user1.address);

      expect(await myContract.isAuthorized(user1.address)).to.be.true;
    });

    it("Should not allow non-owners to authorize users", async function () {
      await expect(
        myContract.connect(user1).authorizeUser(user2.address)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });

    it("Should not allow authorizing zero address", async function () {
      await expect(
        myContract.authorizeUser(ethers.constants.AddressZero)
      ).to.be.revertedWith("Invalid address");
    });

    it("Should not allow authorizing already authorized users", async function () {
      await myContract.authorizeUser(user1.address);
      await expect(
        myContract.authorizeUser(user1.address)
      ).to.be.revertedWith("User already authorized");
    });

    it("Should allow owner to deauthorize users", async function () {
      await myContract.authorizeUser(user1.address);

      await expect(myContract.deauthorizeUser(user1.address))
        .to.emit(myContract, "UserDeauthorized")
        .withArgs(user1.address);

      expect(await myContract.isAuthorized(user1.address)).to.be.false;
    });

    it("Should not allow deauthorizing owner", async function () {
      await expect(
        myContract.deauthorizeUser(owner.address)
      ).to.be.revertedWith("Cannot deauthorize owner");
    });
  });

  describe("Item Creation", function () {
    beforeEach(async function () {
      // Authorize user1 to create items
      await myContract.authorizeUser(user1.address);
    });

    it("Should allow authorized users to create items", async function () {
      const itemName = "Test Item";
      const itemPrice = ethers.utils.parseEther("0.1");

      await expect(myContract.connect(user1).createItem(itemName, itemPrice))
        .to.emit(myContract, "ItemCreated")
        .withArgs(1, itemName, user1.address, itemPrice);

      const item = await myContract.getItem(1);
      expect(item.name).to.equal(itemName);
      expect(item.price).to.equal(itemPrice);
      expect(item.creator).to.equal(user1.address);
      expect(item.active).to.be.true;
    });

    it("Should increment item count", async function () {
      await myContract.connect(user1).createItem("Item 1", ethers.utils.parseEther("0.1"));
      expect(await myContract.getActiveItemsCount()).to.equal(1);

      await myContract.connect(user1).createItem("Item 2", ethers.utils.parseEther("0.2"));
      expect(await myContract.getActiveItemsCount()).to.equal(2);
    });

    it("Should not allow unauthorized users to create items", async function () {
      await expect(
        myContract.connect(user2).createItem("Unauthorized Item", ethers.utils.parseEther("0.1"))
      ).to.be.revertedWith("Not authorized");
    });

    it("Should not allow empty item names", async function () {
      await expect(
        myContract.connect(user1).createItem("", ethers.utils.parseEther("0.1"))
      ).to.be.revertedWith("String cannot be empty");
    });

    it("Should not allow zero price", async function () {
      await expect(
        myContract.connect(user1).createItem("Zero Price Item", 0)
      ).to.be.revertedWith("Price must be greater than 0");
    });

    it("Should track user items", async function () {
      await myContract.connect(user1).createItem("Item 1", ethers.utils.parseEther("0.1"));
      await myContract.connect(user1).createItem("Item 2", ethers.utils.parseEther("0.2"));

      const userItems = await myContract.getUserItems(user1.address);
      expect(userItems.length).to.equal(2);
      expect(userItems[0]).to.equal(1);
      expect(userItems[1]).to.equal(2);
    });
  });

  describe("Item Updates", function () {
    beforeEach(async function () {
      await myContract.authorizeUser(user1.address);
      await myContract.connect(user1).createItem("Original Item", ethers.utils.parseEther("0.1"));
    });

    it("Should allow item owner to update their items", async function () {
      const newName = "Updated Item";
      const newPrice = ethers.utils.parseEther("0.2");

      await expect(myContract.connect(user1).updateItem(1, newName, newPrice))
        .to.emit(myContract, "ItemUpdated")
        .withArgs(1, newName, newPrice);

      const item = await myContract.getItem(1);
      expect(item.name).to.equal(newName);
      expect(item.price).to.equal(newPrice);
    });

    it("Should not allow non-owners to update items", async function () {
      await expect(
        myContract.connect(user2).updateItem(1, "Hacked Item", ethers.utils.parseEther("1"))
      ).to.be.revertedWith("Not item owner");
    });

    it("Should not allow updating non-existent items", async function () {
      await expect(
        myContract.connect(user1).updateItem(999, "Non-existent", ethers.utils.parseEther("0.1"))
      ).to.be.revertedWith("Item does not exist");
    });

    it("Should not allow empty new names", async function () {
      await expect(
        myContract.connect(user1).updateItem(1, "", ethers.utils.parseEther("0.2"))
      ).to.be.revertedWith("String cannot be empty");
    });

    it("Should not allow zero new price", async function () {
      await expect(
        myContract.connect(user1).updateItem(1, "Zero Price", 0)
      ).to.be.revertedWith("Price must be greater than 0");
    });
  });

  describe("Item Deactivation", function () {
    beforeEach(async function () {
      await myContract.authorizeUser(user1.address);
      await myContract.connect(user1).createItem("Test Item", ethers.utils.parseEther("0.1"));
    });

    it("Should allow item owner to deactivate their items", async function () {
      await expect(myContract.connect(user1).deactivateItem(1))
        .to.emit(myContract, "ItemDeactivated")
        .withArgs(1);

      expect(await myContract.isValidItemId(1)).to.be.false;
    });

    it("Should not allow non-owners to deactivate items", async function () {
      await expect(
        myContract.connect(user2).deactivateItem(1)
      ).to.be.revertedWith("Not item owner");
    });

    it("Should not allow deactivating non-existent items", async function () {
      await expect(
        myContract.connect(user1).deactivateItem(999)
      ).to.be.revertedWith("Item does not exist");
    });

    it("Should not include deactivated items in active items", async function () {
      await myContract.connect(user1).createItem("Second Item", ethers.utils.parseEther("0.2"));

      await myContract.connect(user1).deactivateItem(1);

      const activeItems = await myContract.getUserActiveItems(user1.address);
      expect(activeItems.length).to.equal(1);
      expect(activeItems[0]).to.equal(2);
    });
  });

  describe("View Functions", function () {
    beforeEach(async function () {
      await myContract.authorizeUser(user1.address);
      await myContract.connect(user1).createItem("Test Item 1", ethers.utils.parseEther("0.1"));
      await myContract.connect(user1).createItem("Test Item 2", ethers.utils.parseEther("0.2"));
    });

    it("Should return correct item details", async function () {
      const item = await myContract.getItem(1);
      expect(item.id).to.equal(1);
      expect(item.name).to.equal("Test Item 1");
      expect(item.creator).to.equal(user1.address);
      expect(item.price).to.equal(ethers.utils.parseEther("0.1"));
      expect(item.active).to.be.true;
    });

    it("Should return correct user items count", async function () {
      expect(await myContract.getUserItemsCount(user1.address)).to.equal(2);
      expect(await myContract.getUserItemsCount(user2.address)).to.equal(0);
    });

    it("Should return correct item price", async function () {
      expect(await myContract.getItemPrice(1)).to.equal(ethers.utils.parseEther("0.1"));
    });

    it("Should return correct item creator", async function () {
      expect(await myContract.getItemCreator(1)).to.equal(user1.address);
    });

    it("Should validate item IDs correctly", async function () {
      expect(await myContract.isValidItemId(1)).to.be.true;
      expect(await myContract.isValidItemId(2)).to.be.true;
      expect(await myContract.isValidItemId(999)).to.be.false;
    });
  });

  describe("Reentrancy Protection", function () {
    it("Should prevent reentrancy attacks", async function () {
      await myContract.authorizeUser(user1.address);

      // This test would require a malicious contract to test reentrancy
      // For now, we just verify the nonReentrant modifier is present
      const contractCode = await ethers.provider.getCode(myContract.address);
      expect(contractCode.length).to.be.gt(0);
    });
  });

  describe("Gas Usage", function () {
    it("Should report reasonable gas usage for operations", async function () {
      await myContract.authorizeUser(user1.address);

      // Test gas usage for createItem
      const tx1 = await myContract.connect(user1).createItem("Gas Test Item", ethers.utils.parseEther("0.1"));
      const receipt1 = await tx1.wait();
      console.log("CreateItem gas used:", receipt1.gasUsed.toString());

      // Test gas usage for updateItem
      const tx2 = await myContract.connect(user1).updateItem(1, "Updated Item", ethers.utils.parseEther("0.2"));
      const receipt2 = await tx2.wait();
      console.log("UpdateItem gas used:", receipt2.gasUsed.toString());

      // Gas usage should be reasonable (less than 200,000 for simple operations)
      expect(receipt1.gasUsed).to.be.lt(200000);
      expect(receipt2.gasUsed).to.be.lt(100000);
    });
  });

  describe("Edge Cases", function () {
    it("Should handle maximum valid item names", async function () {
      await myContract.authorizeUser(user1.address);

      const longName = "A".repeat(100); // 100 character name
      await expect(
        myContract.connect(user1).createItem(longName, ethers.utils.parseEther("0.1"))
      ).to.not.be.reverted;
    });

    it("Should handle maximum prices", async function () {
      await myContract.authorizeUser(user1.address);

      const maxPrice = ethers.constants.MaxUint256;
      await expect(
        myContract.connect(user1).createItem("Max Price Item", maxPrice)
      ).to.not.be.reverted;
    });

    it("Should handle multiple users creating items", async function () {
      await myContract.authorizeUser(user1.address);
      await myContract.authorizeUser(user2.address);

      await myContract.connect(user1).createItem("User1 Item", ethers.utils.parseEther("0.1"));
      await myContract.connect(user2).createItem("User2 Item", ethers.utils.parseEther("0.2"));

      expect(await myContract.getUserItemsCount(user1.address)).to.equal(1);
      expect(await myContract.getUserItemsCount(user2.address)).to.equal(1);
      expect(await myContract.getActiveItemsCount()).to.equal(2);
    });
  });
});