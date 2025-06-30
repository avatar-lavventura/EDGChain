import os
import subprocess
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

def encrypt_data_file(data_path, output_path, dek):
    """Encrypt the data file with AES using the provided DEK."""
    cipher = AES.new(dek, AES.MODE_GCM)
    with open(data_path, 'rb') as f:
        plaintext = f.read()
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    with open(output_path, 'wb') as f:
        f.write(cipher.nonce + tag + ciphertext)
    print(f"Data encrypted: {output_path}")

def save_dek_to_temp(dek_path, dek):
    """Save DEK to a temporary file before GPG encryption."""
    with open(dek_path, 'wb') as f:
        f.write(dek)

def encrypt_dek_gpg(dek_path, recipients, output_path):
    """Encrypt the DEK file for multiple recipients using GPG."""
    gpg_command = ["gpg", "--output", output_path, "--encrypt"]
    for r in recipients:
        gpg_command.extend(["--recipient", r])
    gpg_command.append(dek_path)
    subprocess.run(gpg_command, check=True)
    print(f"DEK encrypted for recipients {recipients} and saved to {output_path}")

def main():
    # Configuration
    data_path = "data.txt"                  # Your original data file
    encrypted_data_path = "data.enc"        # Encrypted data file
    dek_file = "dek.key"
    encrypted_dek_file = "dek.gpg"
    recipients = ["alper@example.com", "alice@example.com"]  # Replace with actual GPG key IDs or emails

    # Generate a random 256-bit DEK (32 bytes for AES-256)
    dek = get_random_bytes(32)

    # Encrypt the data file
    encrypt_data_file(data_path, encrypted_data_path, dek)

    # Save DEK and encrypt it for multiple recipients using GPG
    save_dek_to_temp(dek_file, dek)
    encrypt_dek_gpg(dek_file, recipients, encrypted_dek_file)

    # Optional: remove plain DEK file for security
    os.remove(dek_file)

    print("All done. Upload `data.enc` and `dek.gpg` to IPFS.")

if __name__ == "__main__":
    main()
