// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/**
 * @title MetadataGenerator
 * @dev Generates dynamic metadata for NFTs with traits and attributes
 * @notice Supports rarity-based trait distribution and custom metadata
 */
contract MetadataGenerator is Ownable {
    using Strings for uint256;

    // Trait structure
    struct Trait {
        string name;
        string value;
        uint256 rarity; // Probability in basis points (e.g., 1000 = 10%)
    }

    // Trait type (category)
    struct TraitType {
        string name;
        Trait[] traits;
    }

    // State variables
    mapping(uint256 => string) public traitTypes; // typeId => typeName
    mapping(uint256 => mapping(uint256 => Trait)) public traitData; // typeId => traitId => Trait
    mapping(uint256 => uint256) public traitTypeCounts; // typeId => traitCount

    uint256 public traitTypeCount;
    string public baseURI;

    // Events
    event TraitTypeAdded(uint256 indexed typeId, string name);
    event TraitAdded(uint256 indexed typeId, uint256 indexed traitId, string name, string value, uint256 rarity);
    event BaseURIUpdated(string newBaseURI);

    /**
     * @dev Constructor
     * @param baseURI_ Base URI for metadata
     */
    constructor(string memory baseURI_) {
        baseURI = baseURI_;
        transferOwnership(msg.sender);
    }

    /**
     * @dev Add a new trait type
     * @param name Trait type name (e.g., "Background", "Body")
     */
    function addTraitType(string calldata name) external onlyOwner returns (uint256 typeId) {
        typeId = traitTypeCount;
        traitTypes[typeId] = name;
        traitTypeCount++;
        emit TraitTypeAdded(typeId, name);
    }

    /**
     * @dev Add a trait to a type
     * @param typeId Trait type ID
     * @param name Trait name
     * @param value Trait value
     * @param rarity Rarity in basis points
     */
    function addTrait(
        uint256 typeId,
        string calldata name,
        string calldata value,
        uint256 rarity
    ) external onlyOwner {
        require(typeId < traitTypeCount, "Invalid type ID");
        require(rarity > 0 && rarity <= 10000, "Rarity must be between 0 and 10000");

        uint256 traitId = traitTypeCounts[typeId];
        traitData[typeId][traitId] = Trait(name, value, rarity);
        traitTypeCounts[typeId]++;

        emit TraitAdded(typeId, traitId, name, value, rarity);
    }

    /**
     * @dev Generate token metadata
     * @param tokenId Token ID
     * @param seed Random seed for trait generation
     */
    function generateMetadata(uint256 tokenId, uint256 seed) external view returns (string memory) {
        string memory json = string(abi.encodePacked('{"name":"NFT #', tokenId.toString(), '","description":"Dynamic NFT with randomized traits","image":"', baseURI, tokenId.toString(), '.png","attributes":['));

        uint256 totalRarity = 0;
        uint256[] memory selectedTraits = new uint256[](traitTypeCount);

        // First pass: calculate total rarity
        for (uint256 i = 0; i < traitTypeCount; i++) {
            totalRarity += getTotalRarityForType(i);
        }

        // Second pass: select traits based on rarity
        for (uint256 i = 0; i < traitTypeCount; i++) {
            uint256 typeRarity = getTotalRarityForType(i);
            uint256 randomValue = (seed + i * 1000) % typeRarity;
            uint256 cumulativeRarity = 0;

            for (uint256 j = 0; j < traitTypeCounts[i]; j++) {
                cumulativeRarity += traitData[i][j].rarity;
                if (randomValue < cumulativeRarity) {
                    selectedTraits[i] = j;
                    break;
                }
            }

            // Add comma if not first attribute
            if (i > 0) {
                json = string(abi.encodePacked(json, ","));
            }

            // Build attribute JSON
            json = string(abi.encodePacked(
                json,
                '{"trait_type":"',
                traitTypes[i],
                '","value":"',
                traitData[i][selectedTraits[i]].value,
                '","rarity":"',
                (traitData[i][selectedTraits[i]].rarity / 100).toString(),
                '%"}'
            ));
        }

        json = string(abi.encodePacked(json, ']}'));
        return json;
    }

    /**
     * @dev Generate deterministic metadata from seed
     * @param seed Seed for trait generation
     */
    function generateMetadataFromSeed(uint256 seed) external view returns (string memory) {
        return generateMetadata(0, seed);
    }

    /**
     * @dev Get total rarity for a trait type
     * @param typeId Trait type ID
     */
    function getTotalRarityForType(uint256 typeId) public view returns (uint256) {
        uint256 total = 0;
        for (uint256 i = 0; i < traitTypeCounts[typeId]; i++) {
            total += traitData[typeId][i].rarity;
        }
        return total;
    }

    /**
     * @dev Get trait type info
     * @param typeId Trait type ID
     */
    function getTraitTypeInfo(uint256 typeId) external view returns (string memory name, uint256 traitCount) {
        require(typeId < traitTypeCount, "Invalid type ID");
        return (traitTypes[typeId], traitTypeCounts[typeId]);
    }

    /**
     * @dev Get trait info
     * @param typeId Trait type ID
     * @param traitId Trait ID
     */
    function getTraitInfo(uint256 typeId, uint256 traitId) external view returns (
        string memory name,
        string memory value,
        uint256 rarity
    ) {
        require(typeId < traitTypeCount, "Invalid type ID");
        require(traitId < traitTypeCounts[typeId], "Invalid trait ID");
        Trait memory trait = traitData[typeId][traitId];
        return (trait.name, trait.value, trait.rarity);
    }

    /**
     * @dev Set base URI
     * @param newBaseURI New base URI
     */
    function setBaseURI(string calldata newBaseURI) external onlyOwner {
        baseURI = newBaseURI;
        emit BaseURIUpdated(newBaseURI);
    }

    /**
     * @dev Batch add trait types
     * @param names Array of trait type names
     */
    function batchAddTraitTypes(string[] calldata names) external onlyOwner {
        for (uint256 i = 0; i < names.length; i++) {
            addTraitType(names[i]);
        }
    }

    /**
     * @dev Batch add traits for a type
     * @param typeId Trait type ID
     * @param names Array of trait names
     * @param values Array of trait values
     * @param rarities Array of rarities
     */
    function batchAddTraits(
        uint256 typeId,
        string[] calldata names,
        string[] calldata values,
        uint256[] calldata rarities
    ) external onlyOwner {
        require(names.length == values.length, "Array length mismatch");
        require(names.length == rarities.length, "Array length mismatch");

        for (uint256 i = 0; i < names.length; i++) {
            addTrait(typeId, names[i], values[i], rarities[i]);
        }
    }

    /**
     * @dev Generate OpenSea-style metadata
     * @param tokenId Token ID
     * @param traits Selected traits
     */
    function generateOpenSeaMetadata(uint256 tokenId, uint256[] calldata traits) external view returns (string memory) {
        string memory json = string(abi.encodePacked('{"name":"NFT #', tokenId.toString(), '","description":"Unique NFT with rare traits","image":"', baseURI, tokenId.toString(), '.png","attributes":['));

        for (uint256 i = 0; i < traits.length; i++) {
            if (i > 0) {
                json = string(abi.encodePacked(json, ","));
            }

            // This would need to be customized based on your trait structure
            json = string(abi.encodePacked(json, '{"trait_type":"Trait #', i.toString(), '","value":"', traits[i].toString(), '"}'));
        }

        json = string(abi.encodePacked(json, ']}'));
        return json;
    }
}
