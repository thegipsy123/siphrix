import os
from ecdh_encryption import encrypt_message, decrypt_message

VAULT_DIR = ".vault"


def save_encrypted_to_vault(filename, data, private_key, public_key):
    encrypted = encrypt_message(private_key, public_key, data)
    path = os.path.join(VAULT_DIR, filename + ".vault")
    with open(path, "w", encoding="utf-8") as f:
        f.write(encrypted)
    print(f"🔒 Saved encrypted file to {path}")


def load_encrypted_from_vault(filename, private_key, public_key):
    path = os.path.join(VAULT_DIR, filename + ".vault")
    if not os.path.exists(path):
        print("❌ File not found in vault.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        encrypted = f.read()
    try:
        decrypted = decrypt_message(private_key, public_key, encrypted)
        print(f"🔓 Decrypted {filename}")
        return decrypted
    except Exception as e:
        print("❌ Failed to decrypt vault file:", e)
        return None
