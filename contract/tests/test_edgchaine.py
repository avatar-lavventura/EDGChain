import pytest

# from ape import accounts, project
import base58
from multihash import decode, encode

# === Helpers ===


def cid_to_bytes32(cid_str):
    """
    Decode base58 CIDv0 and extract SHA-256 digest as bytes32
    """
    mh_bytes = base58.b58decode(cid_str)
    decoded = decode(mh_bytes)
    assert decoded.name == "sha2-256", "CID must be SHA-256"
    assert len(decoded.digest) == 32, "Digest must be 32 bytes"
    return decoded.digest


def bytes32_to_cid(digest_bytes):
    """
    Reconstruct CIDv0 string from SHA-256 digest
    """
    mh_bytes = encode(digest_bytes, "sha2-256")
    return base58.b58encode(mh_bytes).decode()


# === Fixtures ===


@pytest.fixture
def owner(accounts):
    return accounts[0]


@pytest.fixture
def contributor(accounts):
    return accounts[1]


@pytest.fixture
def outsider(accounts):
    return accounts[2]


# === Tests ===


def test_commit_with_ipfs_digest(project, owner, contributor, accounts):
    acct = accounts[0]
    edg = acct.deploy(project.EDGChainE)

    # Example IPFS CIDs (replace with actual CIDs from your IPFS storage)
    genesis_cid_str = "QmT78zSuBmuS4z925W2u7F6zXZx3jUunZ2x7Y6W92Ar81m"
    data1_cid_str = "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco"
    data2_cid_str = "QmYwAPJzv5CZsnAzt8auVTLXgfF6iMJxmswXAXqc7x2xR9"

    # Convert to bytes32 digest
    genesis_digest = cid_to_bytes32(genesis_cid_str)
    data1_digest = cid_to_bytes32(data1_cid_str)
    data2_digest = cid_to_bytes32(data2_cid_str)

    # Project ID (can also be based on a hash of project name)
    project_id = genesis_digest

    # Create project
    edg.createProject(project_id, genesis_digest, sender=owner)

    assert edg.getGenesisCid(project_id) == genesis_digest
    assert edg.getLatestCid(project_id) == genesis_digest

    # Add contributor
    edg.addContributor(project_id, contributor, sender=owner)

    # Commit 1
    edg.commitData(project_id, data1_digest, genesis_digest, sender=contributor)
    latest = edg.getLatestCid(project_id)
    assert latest == data1_digest

    # Reconstruct CID and compare
    reconstructed = bytes32_to_cid(latest)
    assert reconstructed == data1_cid_str

    # Commit 2
    edg.commitData(project_id, data2_digest, data1_digest, sender=contributor)
    latest = edg.getLatestCid(project_id)
    assert latest == data2_digest
    assert edg.getParentCid(project_id, data2_digest) == data1_digest

    reconstructed2 = bytes32_to_cid(latest)
    assert reconstructed2 == data2_cid_str


def test_fail_duplicate_commit(project, accounts, owner):
    acct = accounts[0]
    edg = acct.deploy(project.EDGChainE)

    project_id = cid_to_bytes32("QmT78zSuBmuS4z925W2u7F6zXZx3jUunZ2x7Y6W92Ar81m")
    genesis_digest = project_id
    edg.createProject(project_id, genesis_digest, sender=owner)
    edg.addContributor(project_id, owner, sender=owner)

    edg.commitData(project_id, genesis_digest, genesis_digest, sender=owner)

    with pytest.raises(Exception):
        edg.commitData(project_id, genesis_digest, genesis_digest, sender=owner)


def test_fail_duplicate_project(project, accounts, owner):
    acct = accounts[0]
    edg = acct.deploy(project.EDGChainE)

    project_id = cid_to_bytes32("QmT78zSuBmuS4z925W2u7F6zXZx3jUunZ2x7Y6W92Ar81m")
    genesis_digest = project_id
    edg.createProject(project_id, genesis_digest, sender=owner)

    with pytest.raises(Exception):
        edg.createProject(project_id, genesis_digest, sender=owner)


def test_create_project(project, accounts, owner):
    acct = accounts[0]
    edg = acct.deploy(project.EDGChainE)

    project_id = cid_to_bytes32("QmT78zSuBmuS4z925W2u7F6zXZx3jUunZ2x7Y6W92Ar81m")
    genesis_cid = cid_to_bytes32("QmT78zSuBmuS4z925W2u7F6zXZx3jUunZ2x7Y6W92Ar811")

    tx = edg.createProject(project_id, genesis_cid, sender=owner)

    # Event control
    assert tx.events[0]["projectID"] == project_id
    assert tx.events[0]["creator"] == owner.address
    assert tx.events[0]["genesisCid"] == genesis_cid

    assert edg.getGenesisCid(project_id) == genesis_cid
    assert edg.getLatestCid(project_id) == genesis_cid


def test_add_and_remove_owner(project, accounts, owner, contributor):
    acct = accounts[0]
    edg = acct.deploy(project.EDGChainE)

    project_id = b"\x03" * 32
    genesis_cid = b"\x04" * 32
    edg.createProject(project_id, genesis_cid, sender=owner)

    # owner contributor'ı owner yap
    tx = edg.addOwner(project_id, contributor.address, sender=owner)
    assert tx.events[0]["user"] == contributor.address

    # owner'u çıkar
    tx2 = edg.removeOwner(project_id, contributor.address, sender=owner)
    assert tx.events[0]["user"] == contributor.address


def test_add_and_remove_contributor(project, accounts, owner, contributor):
    acct = accounts[0]
    edg = acct.deploy(project.EDGChainE)

    project_id = b"\x05" * 32
    genesis_cid = b"\x06" * 32
    edg.createProject(project_id, genesis_cid, sender=owner)

    tx = edg.addContributor(project_id, contributor.address, sender=owner)
    assert tx.events[0]["user"] == contributor.address

    # contributor olmayan biri eklemeye çalışırsa hata
    with pytest.raises(Exception):
        edg.addContributor(project_id, owner.address, sender=contributor)

    # contributor çıkarma
    tx2 = edg.removeContributor(project_id, contributor.address, sender=owner)
    assert tx.events[0]["user"] == contributor.address


def test_commit_flow(project, accounts, owner, contributor):
    acct = accounts[0]
    edg = acct.deploy(project.EDGChainE)

    project_id = b"\x07" * 32
    genesis_cid = b"\x08" * 32
    edg.createProject(project_id, genesis_cid, sender=owner)
    edg.addContributor(project_id, contributor.address, sender=owner)

    new_cid_1 = b"\x09" * 32
    new_cid_2 = b"\x0a" * 32

    # İlk commit - contributor tarafından
    tx = edg.commitData(project_id, new_cid_1, genesis_cid, sender=contributor)
    assert tx.events[0]["cid"] == new_cid_1
    assert tx.events[0]["parentCid"] == genesis_cid

    assert edg.getLatestCid(project_id) == new_cid_1

    # İkinci commit, parent ilk commit
    tx2 = edg.commitData(project_id, new_cid_2, new_cid_1, sender=contributor)
    assert tx2.events[0]["cid"] == new_cid_2
    assert edg.getLatestCid(project_id) == new_cid_2
    assert edg.getParentCid(project_id, new_cid_2) == new_cid_1


def test_commit_reverts_for_non_contributor(project, accounts, owner, outsider):
    acct = accounts[0]
    edg = acct.deploy(project.EDGChainE)

    project_id = cid_to_bytes32("QmT78zSuBmuS4z925W2u7F6zXZx3jUunZ2x7Y6W92Ar81m")
    genesis_cid = b"\x0c" * 32
    edg.createProject(project_id, genesis_cid, sender=owner)

    new_cid = b"\x0d" * 32
    # outsider contributor değil, hata vermeli
    with pytest.raises(Exception):
        edg.commitData(project_id, new_cid, genesis_cid, sender=outsider)


def test_create_project_duplicate_revert(project, accounts, owner):
    acct = accounts[0]
    edg = acct.deploy(project.EDGChainE)

    project_id = cid_to_bytes32("QmT78zSuBmuS4z925W2u7F6zXZx3jUunZ2x7Y6W92Ar81m")
    genesis_cid = b"\x0f" * 32

    edg.createProject(project_id, genesis_cid, sender=owner)

    # Aynı proje ile tekrar oluşturma revert olmalı
    with pytest.raises(Exception):
        edg.createProject(project_id, genesis_cid, sender=owner)


def test_commit_duplicate_cid_revert(project, accounts, owner, contributor):
    acct = accounts[0]
    edg = acct.deploy(project.EDGChainE)

    project_id = cid_to_bytes32("QmT78zSuBmuS4z925W2u7F6zXZx3jUunZ2x7Y6W92Ar81m")
    genesis_cid = b"\x11" * 32
    edg.createProject(project_id, genesis_cid, sender=owner)
    edg.addContributor(project_id, contributor.address, sender=owner)

    new_cid = b"\x12" * 32

    edg.commitData(project_id, new_cid, genesis_cid, sender=contributor)

    # Aynı cid ile commit tekrar yapılamaz
    with pytest.raises(Exception):
        edg.commitData(project_id, new_cid, genesis_cid, sender=contributor)
