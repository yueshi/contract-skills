const { ethers } = require("hardhat");

/**
 * Increase time in the blockchain
 * @param {number} seconds - Number of seconds to increase
 */
async function increaseTime(seconds) {
  await ethers.provider.send("evm_increaseTime", [seconds]);
  await ethers.provider.send("evm_mine", []);
}

/**
 * Set the next block timestamp
 * @param {number} timestamp - Unix timestamp
 */
async function setNextBlockTimestamp(timestamp) {
  await ethers.provider.send("evm_setNextBlockTimestamp", [timestamp]);
  await ethers.provider.send("evm_mine", []);
}

/**
 * Mine a block
 */
async function mineBlock() {
  await ethers.provider.send("evm_mine", []);
}

/**
 * Get current block timestamp
 * @returns {Promise<number>} Current block timestamp
 */
async function getCurrentTimestamp() {
  const blockNumber = await ethers.provider.getBlockNumber();
  const block = await ethers.provider.getBlock(blockNumber);
  return block.timestamp;
}

module.exports = {
  increaseTime,
  setNextBlockTimestamp,
  mineBlock,
  getCurrentTimestamp
};
