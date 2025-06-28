// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EDGChainE {

    struct Commit {
        bytes32 cid; 
        bytes32 parentCid;
    }

    struct Project {
        bytes32 genesisCid; // IPFS CID of the initial encrypted dataset
        bytes32 latestCid;
        mapping(bytes32 => Commit) commits;
        mapping(address => bool) owners;
        mapping(address => bool) contributors;
        mapping(address => bool) authorizedUsers;
    }

    mapping(bytes32 => Project) private projects; // projectID => Project

    event ProjectCreated(bytes32 indexed projectID, address indexed creator, bytes32 genesisCid);
    event CommitAdded(bytes32 indexed projectID, bytes32 indexed cid, bytes32 indexed parentCid);
    event AccessGranted(bytes32 indexed projectID, address indexed user);
    event AccessRevoked(bytes32 indexed projectID, address indexed user);
    event ContributorAdded(bytes32 indexed projectID, address indexed user);
    event ContributorRemoved(bytes32 indexed projectID, address indexed user);
    event OwnerAdded(bytes32 indexed projectID, address indexed user);
    event OwnerRemoved(bytes32 indexed projectID, address indexed user);

    modifier onlyOwner(bytes32 projectID) {
        require(projects[projectID].owners[msg.sender], "Only project owner");
        _;
    }

    modifier onlyContributor(bytes32 projectID) {
        require(projects[projectID].contributors[msg.sender], "Only project contributor");
        _;
    }

    function createProject(bytes32 projectID, bytes32 genesisCid) external {
        require(projects[projectID].owners[msg.sender] == false, "Project exists");
        Project storage p = projects[projectID];
        p.owners[msg.sender] = true;
        p.genesisCid = genesisCid;
        p.latestCid = genesisCid;

        emit ProjectCreated(projectID, msg.sender, genesisCid);
        emit OwnerAdded(projectID, msg.sender);
    }

    function addOwner(bytes32 projectID, address user) external onlyOwner(projectID) {
        projects[projectID].owners[user] = true;
        emit OwnerAdded(projectID, user);
    }

    function removeOwner(bytes32 projectID, address user) external onlyOwner(projectID) {
        projects[projectID].owners[user] = false;
        emit OwnerRemoved(projectID, user);
    }

    function addContributor(bytes32 projectID, address user) external onlyOwner(projectID) {
        projects[projectID].contributors[user] = true;
        emit ContributorAdded(projectID, user);
    }

    function removeContributor(bytes32 projectID, address user) external onlyOwner(projectID) {
        projects[projectID].contributors[user] = false;
        emit ContributorRemoved(projectID, user);
    }

    function grantAccess(bytes32 projectID, address user) external onlyOwner(projectID) {
        projects[projectID].authorizedUsers[user] = true;
        emit AccessGranted(projectID, user);
    }

    function revokeAccess(bytes32 projectID, address user) external onlyOwner(projectID) {
        projects[projectID].authorizedUsers[user] = false;
        emit AccessRevoked(projectID, user);
    }

    function commitData(bytes32 projectID, bytes32 newCid, bytes32 parentCid) external onlyContributor(projectID) {
        Project storage p = projects[projectID];
        require(p.commits[newCid].cid == 0, "CID exists");

        p.commits[newCid] = Commit({
            cid: newCid,
            parentCid: parentCid
        });

        p.latestCid = newCid;

        emit CommitAdded(projectID, newCid, parentCid);
    }

    // -----------------
    // READ FUNCTIONS
    // -----------------

    function hasAccess(bytes32 projectID, address user) external view returns (bool) {
        return projects[projectID].authorizedUsers[user];
    }

    function getLatestCid(bytes32 projectID) external view returns (bytes32) {
        return projects[projectID].latestCid;
    }

    function getGenesisCid(bytes32 projectID) external view returns (bytes32) {
        return projects[projectID].genesisCid;
    }

    function getParentCid(bytes32 projectID, bytes32 cid) external view returns (bytes32) {
        require(projects[projectID].commits[cid].cid != 0, "Commit not found");
        return projects[projectID].commits[cid].parentCid;
    }
}
