import json
import os
from datetime import datetime
from cryptography.fernet import Fernet
from encryption import generate_keypair  # Make sure this exists in encryption.py

KEY_BACKUP_DIR = "backups"
RECOVERY_KEY_FILE = "recovery.key"

# Ensure backup directory exists
os.makedirs(KEY_BACKUP_DIR, exist_ok=True)

def load_or_create_recovery_key():
    if not os.path.exists(RECOVERY_KEY_FILE):
        key = Fernet.generate_key()
        with open(RECOVERY_KEY_FILE, "wb") as f:
            f.write(key)
    else:
        key = open(RECOVERY_KEY_FILE, "rb").read()
    return Fernet(key)

def load_or_create_keys(filename: str):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            keys = json.load(f)
            return keys["private_key"], keys["public_key"]
    else:
        private_key, public_key = generate_keypair()
        with open(filename, "w") as f:
            json.dump({
                "private_key": private_key,
                "public_key": public_key
            }, f)
        return private_key, public_key

def backup_keys(filename: str):
    if not os.path.exists(filename):
        return False
    with open(filename, "r") as f:
        data = f.read()
    fernet = load_or_create_recovery_key()
    encrypted = fernet.encrypt(data.encode())
    timestamp = datetime.now().isoformat(timespec="seconds").replace(":", "-")
    backup_file = os.path.join(KEY_BACKUP_DIR, f"keys_backup_{timestamp}.json")
    with open(backup_file, "wb") as f:
        f.write(encrypted)
    return True

def rotate_keys(filename: str):
    if os.path.exists(filename):
        backup_keys(filename)
        os.remove(filename)
    private_key, public_key = generate_keypair()
    with open(filename, "w") as f:
        json.dump({
            "private_key": private_key,
            "public_key": public_key
        }, f)
    return private_key, public_key

def recover_last_backup(filename: str):
    files = sorted([
        f for f in os.listdir(KEY_BACKUP_DIR) if f.startswith("keys_backup_")
    ], reverse=True)
    if not files:
        return False
    latest = os.path.join(KEY_BACKUP_DIR, files[0])
    fernet = load_or_create_recovery_key()
    with open(latest, "rb") as f:
        decrypted = fernet.decrypt(f.read()).decode()
    with open(filename, "w") as f:
        f.write(decrypted)
    return True


def rotate_keys_if_expired():
    return None


def maybe_rotate_keys():
    return None