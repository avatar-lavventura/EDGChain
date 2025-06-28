// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EDGChainE {
    struct Commit {
        bytes32 cid;              // IPFS CID of encrypted data/patch (content hash)
        bytes32 parentCid;        // Parent commit CID
        mapping(address => bytes) encryptedDEK; // Encrypted DEK per authorized user
        address[] authorizedUsers; // List of authorized users
    }

    mapping(bytes32 => Commit) public commits;   // Mapping from CID to commit info
    mapping(address => bool) public owners;      // Owner addresses for access control
    mapping(address => bool) public contributors; // Contributor addresses
    bytes32 public latestCid;                    // Latest commit CID

    event CommitAdded(bytes32 indexed cid, bytes32 indexed parentCid);
    event AccessGranted(bytes32 indexed cid, address indexed user);
    event AccessRevoked(bytes32 indexed cid, address indexed user);

    modifier onlyOwner() {
        require(owners[msg.sender], "Not authorized (owner only)");
        _;
    }

    modifier onlyContributor() {
        require(contributors[msg.sender], "Not authorized (contributor only)");
        _;
    }

    constructor() {
        owners[msg.sender] = true;
    }

    function addOwner(address newOwner) external onlyOwner {
        owners[newOwner] = true;
    }

    function addContributor(address newContributor) external onlyOwner {
        contributors[newContributor] = true;
    }

    function commitData(
        bytes32 newCid,
        bytes32 parentCid,
        address[] calldata users,
        bytes[] calldata encryptedDEKs
    ) external onlyContributor {
        require(users.length == encryptedDEKs.length, "Mismatched inputs");
        require(commits[newCid].cid == 0, "CID already exists");

        Commit storage c = commits[newCid];
        c.cid = newCid;
        c.parentCid = parentCid;

        for (uint i = 0; i < users.length; i++) {
            c.encryptedDEK[users[i]] = encryptedDEKs[i];
            c.authorizedUsers.push(users[i]);
            emit AccessGranted(newCid, users[i]);
        }

        latestCid = newCid;
        emit CommitAdded(newCid, parentCid);
    }

    function getEncryptedDEK(bytes32 cid, address user) external view returns (bytes memory) {
        require(commits[cid].cid != 0, "Commit not found");
        bytes memory dek = commits[cid].encryptedDEK[user];
        require(dek.length > 0, "No DEK for this user");
        return dek;
    }

    function revokeAccess(bytes32 cid, address user) external onlyOwner {
        require(commits[cid].cid != 0, "Commit not found");
        delete commits[cid].encryptedDEK[user];

        // Remove from authorizedUsers array
        address[] storage authUsers = commits[cid].authorizedUsers;
        for (uint i = 0; i < authUsers.length; i++) {
            if (authUsers[i] == user) {
                authUsers[i] = authUsers[authUsers.length - 1];
                authUsers.pop();
                break;
            }
        }
        emit AccessRevoked(cid, user);
    }

    function getAuthorizedUsers(bytes32 cid) external view returns (address[] memory) {
        require(commits[cid].cid != 0, "Commit not found");
        return commits[cid].authorizedUsers;
    }

    function getParentCid(bytes32 cid) external view returns (bytes32) {
        require(commits[cid].cid != 0, "Commit not found");
        return commits[cid].parentCid;
    }
}
