import os
import shutil
import hashlib
import subprocess
import tempfile
from typing import List, Dict, Tuple

# === Simulated cryptographic operations ===
import base64
def generate_dek() -> bytes:
    return os.urandom(32)

def encrypt(data: bytes, key: bytes) -> bytes:
    return base64.b64encode(data[::-1])  # Placeholder for AES-256

def decrypt(data: bytes, key: bytes) -> bytes:
    return base64.b64decode(data)[::-1]

# === Simulated IPFS storage ===
ipfs_storage: Dict[str, bytes] = {}

def ipfs_add(data: bytes) -> str:
    cid = hashlib.sha256(data).hexdigest()
    ipfs_storage[cid] = data
    return cid

def ipfs_get(cid: str) -> bytes:
    return ipfs_storage[cid]

# === Git-based patch utilities ===
def git_diff_files(base_files: Dict[str, str], new_files: Dict[str, str]) -> Dict[str, bytes]:
    diffs = {}
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        subprocess.run(["git", "init"], check=True, stdout=subprocess.DEVNULL)

        # Write base files
        for path, content in base_files.items():
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "base"], check=True, stdout=subprocess.DEVNULL)

        # Overwrite with new files
        for path, content in new_files.items():
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)

        # Get unified diff
        diff = subprocess.check_output(["git", "diff", "--binary"])
        diffs["__multi_patch__"] = diff
    return diffs

def git_apply_patch(base_files: Dict[str, str], diff_bytes: bytes) -> Dict[str, str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        subprocess.run(["git", "init"], check=True, stdout=subprocess.DEVNULL)

        # Write base files
        for path, content in base_files.items():
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "base"], check=True, stdout=subprocess.DEVNULL)

        # Apply patch
        patch_path = os.path.join(tmpdir, "patch.diff")
        with open(patch_path, "wb") as f:
            f.write(diff_bytes)
        subprocess.run(["git", "apply", "--allow-binary-replacement", patch_path], check=True)

        # Read resulting files
        result = {}
        for root, _, files in os.walk(tmpdir):
            for file in files:
                full = os.path.join(root, file)
                rel = os.path.relpath(full, tmpdir)
                with open(full, "r") as f:
                    result[rel] = f.read()
        return result

# === EDGChain multi-file versioning ===
class EDGChainRepo:
    def __init__(self):
        self.versions: List[List[Tuple[str, str]]] = []  # list of (patch_cid, dek_cid) per version

    def commit_new_version(self, new_files: Dict[str, str]):
        base_files = self.reconstruct_latest() if self.versions else {}
        patch_map = git_diff_files(base_files, new_files)
        patch_bytes = patch_map["__multi_patch__"]

        dek = generate_dek()
        enc_patch = encrypt(patch_bytes, dek)
        enc_dek = encrypt(dek, b"user-pub-key")

        patch_cid = ipfs_add(enc_patch)
        dek_cid = ipfs_add(enc_dek)

        self.versions.append([(patch_cid, dek_cid)])

    def reconstruct_latest(self) -> Dict[str, str]:
        files: Dict[str, str] = {}
        for version in self.versions:
            for patch_cid, dek_cid in version:
                enc_patch = ipfs_get(patch_cid)
                enc_dek = ipfs_get(dek_cid)
                dek = decrypt(enc_dek, b"user-priv-key")
                patch = decrypt(enc_patch, dek)
                files = git_apply_patch(files, patch)
        return files

# === Demo usage ===
if __name__ == "__main__":
    repo = EDGChainRepo()

    v1 = {
        "main.py": "print('Version 1')\n",
        "README.md": "# EDGChain\nInitial version"
    }
    v2 = {
        "main.py": "print('Version 2')\n",
        "README.md": "# EDGChain\nUpdated version\nWith more info"
    }
    v3 = {
        "main.py": "print('Final Version')\nprint('EDGChain running')",
        "README.md": "# EDGChain\nUpdated again\n"
    }

    repo.commit_new_version(v1)
    repo.commit_new_version(v2)
    repo.commit_new_version(v3)

    result = repo.reconstruct_latest()
    print("=== Reconstructed Files ===")
    for path, content in result.items():
        print(f"\n-- {path} --\n{content}")
