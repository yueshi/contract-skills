// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

/**
 * @title MockNFT
 * @dev Mock ERC721 token for testing
 */
contract MockNFT is ERC20 {
    uint256 public nextTokenId = 1;
    mapping(address => uint256[]) public userTokens;

    constructor() ERC20("Mock NFT", "MNFT") {}

    function mint(address to, uint256 tokenId) external {
        _mint(to, tokenId);
        userTokens[to].push(tokenId);
    }

    function mintNew(address to) external returns (uint256) {
        uint256 tokenId = nextTokenId++;
        _mint(to, tokenId);
        userTokens[to].push(tokenId);
        return tokenId;
    }

    function getUserTokens(address user) external view returns (uint256[] memory) {
        return userTokens[user];
    }
}
