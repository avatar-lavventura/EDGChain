// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EDGChainE {
    struct Commit {
        bytes32 cid; // IPFS CID
        bytes32 parentCid; // optional for off-chain event validation
    }

    mapping(bytes32 => Commit) public commits; // cid => Commit
    mapping(address => bool) public owners; // admins/owners
    mapping(address => bool) public contributors; // users who can commit
    mapping(address => bool) public authorizedUsers; // users who can access any commit
    bytes32 public latestCid;

    event CommitAdded(bytes32 indexed cid, bytes32 indexed parentCid);
    event AccessGranted(address indexed user);
    event AccessRevoked(address indexed user);

    modifier onlyOwner() {
        require(owners[msg.sender], "Only owner");
        _;
    }

    modifier onlyContributor() {
        require(contributors[msg.sender], "Only contributor");
        _;
    }

    constructor() {
        owners[msg.sender] = true;
    }

    // Owner role management
    function addOwner(address user) external onlyOwner {
        owners[user] = true;
    }

    function removeOwner(address user) external onlyOwner {
        owners[user] = false;
    }

    // Contributor role management
    function addContributor(address user) external onlyOwner {
        contributors[user] = true;
    }

    function removeContributor(address user) external onlyOwner {
        contributors[user] = false;
    }

    // Global access management
    function grantAccess(address user) external onlyOwner {
        authorizedUsers[user] = true;
        emit AccessGranted(user);
    }

    function revokeAccess(address user) external onlyOwner {
        authorizedUsers[user] = false;
        emit AccessRevoked(user);
    }

    // Commit data (no per-user DEK mapping, users manage DEK off-chain)
    function commitData(bytes32 newCid, bytes32 parentCid) external onlyContributor {
        require(commits[newCid].cid == 0, "CID already exists");

        commits[newCid] = Commit({
            cid: newCid,
            parentCid: parentCid
        });

        latestCid = newCid;
        emit CommitAdded(newCid, parentCid);
    }

    // Simple check: does user have repo access?
    function hasAccess(address user) external view returns (bool) {
        return authorizedUsers[user];
    }

    // Retrieve parent for off-chain use
    function getParentCid(bytes32 cid) external view returns (bytes32) {
        require(commits[cid].cid != 0, "Commit not found");
        return commits[cid].parentCid;
    }
}
