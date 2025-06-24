import os
import json
import getpass
import hashlib

PIN_FILE = "pin_lock.json"


def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()


def check_pin():
    # 🔐 First time? Ask to create one
    if not os.path.exists(PIN_FILE):
        print("🔒 No PIN set. Please create a 6-digit PIN:")
        while True:
            pin = getpass.getpass("➡️ Enter new PIN: ")
            confirm = getpass.getpass("🔁 Confirm PIN: ")
            if pin == confirm and pin.isdigit() and len(pin) == 6:
                with open(PIN_FILE, "w") as f:
                    json.dump({"pin_hash": hash_pin(pin)}, f)
                print("✅ PIN saved.")
                return True
            else:
                print("❌ PINs didn’t match or not 6 digits. Try again.")
    else:
        # 🔐 Ask for the PIN
        with open(PIN_FILE, "r") as f:
            saved = json.load(f)
        for _ in range(3):
            pin = getpass.getpass("🔑 Enter your 6-digit PIN: ")
            if hash_pin(pin) == saved["pin_hash"]:
                print("✅ Correct PIN. Welcome!")
                return True
            else:
                print("❌ Wrong PIN.")
        print("⛔ Too many tries. Exiting.")
        return False
