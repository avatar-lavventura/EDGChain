import subprocess
from Crypto.Cipher import AES

def decrypt_dek_gpg(encrypted_dek_path, output_dek_path):
    """Use GPG to decrypt the DEK file."""
    gpg_command = [
        "gpg", "--output", output_dek_path, "--decrypt", encrypted_dek_path
    ]
    subprocess.run(gpg_command, check=True)
    print(f"DEK decrypted and saved to {output_dek_path}")

def decrypt_data_file(encrypted_data_path, output_path, dek):
    """Decrypt AES-encrypted data using the decrypted DEK."""
    with open(encrypted_data_path, 'rb') as f:
        nonce = f.read(16)
        tag = f.read(16)
        ciphertext = f.read()

    cipher = AES.new(dek, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)

    with open(output_path, 'wb') as f:
        f.write(plaintext)
    print(f"Data decrypted and saved to {output_path}")

def main():
    # Configuration
    encrypted_data_path = "data.enc"
    encrypted_dek_file = "dek.gpg"
    decrypted_dek_file = "dek.key"
    output_data_file = "data_decrypted.txt"

    # Step 1: Decrypt DEK with recipient's private GPG key
    decrypt_dek_gpg(encrypted_dek_file, decrypted_dek_file)

    # Step 2: Read DEK and use it to decrypt the data
    with open(decrypted_dek_file, 'rb') as f:
        dek = f.read()

    decrypt_data_file(encrypted_data_path, output_data_file, dek)

    # Optional: remove plain DEK for security
    subprocess.run(["rm", "-f", decrypted_dek_file])

if __name__ == "__main__":
    main()
