// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract LandChain {
    struct Property {
        uint256 propertyId;
        string propertyReference;
        address owner;
        string documentHash;
        bool verified;
        bool exists;
    }

    mapping(uint256 => Property) private properties;

    event PropertyRegistered(uint256 indexed propertyId, string propertyReference, address indexed owner, string documentHash);
    event PropertyVerified(uint256 indexed propertyId, address indexed verifier);
    event OwnershipTransferred(uint256 indexed propertyId, address indexed previousOwner, address indexed newOwner);

    function registerProperty(uint256 propertyId, string memory propertyReference, string memory documentHash) external {
        require(!properties[propertyId].exists, "Property already exists");
        require(bytes(propertyReference).length > 0, "Property reference required");
        properties[propertyId] = Property(propertyId, propertyReference, msg.sender, documentHash, false, true);
        emit PropertyRegistered(propertyId, propertyReference, msg.sender, documentHash);
    }

    function verifyProperty(uint256 propertyId) external {
        require(properties[propertyId].exists, "Property does not exist");
        require(!properties[propertyId].verified, "Property already verified");
        properties[propertyId].verified = true;
        emit PropertyVerified(propertyId, msg.sender);
    }

    function transferOwnership(uint256 propertyId, address newOwner) external {
        require(properties[propertyId].exists, "Property does not exist");
        require(properties[propertyId].owner == msg.sender, "Only owner can transfer");
        require(newOwner != address(0), "Invalid new owner");
        address previousOwner = properties[propertyId].owner;
        properties[propertyId].owner = newOwner;
        emit OwnershipTransferred(propertyId, previousOwner, newOwner);
    }

    function getProperty(uint256 propertyId) external view returns (Property memory) {
        require(properties[propertyId].exists, "Property does not exist");
        return properties[propertyId];
    }
    function getOwner(uint256 propertyId) external view returns (address) {
        require(properties[propertyId].exists, "Property does not exist");
        return properties[propertyId].owner;
    }
    function isVerified(uint256 propertyId) external view returns (bool) {
        require(properties[propertyId].exists, "Property does not exist");
        return properties[propertyId].verified;
    }
    function propertyExists(uint256 propertyId) external view returns (bool) { return properties[propertyId].exists; }
}
