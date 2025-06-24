from argon2 import PasswordHasher
import os
import json
from dotenv import load_dotenv
load_dotenv()


ph = PasswordHasher()
import hmac
import hashlib

PEPPER = os.getenv("PEPPER", "supersecret")


def hash_username(username):
    return hmac.new(PEPPER.encode(), username.encode(), hashlib.sha256).hexdigest()


AUTH_FILE = "user_auth.json"


def register_local():
    if os.path.exists(AUTH_FILE):
        print("❌ Already registered.")
        return

    username = input("Choose a username: ").strip().lower()
    password = input("Choose a password: ").strip()

    hash_ = ph.hash(password)
    identifier = hash_username(username)

    with open(AUTH_FILE, "w") as f:
        json.dump({"identifier": identifier, "password_hash": hash_}, f)

    print(f"✅ Registered locally (username hidden)")

    print(f"✅ Registered locally as {username}")


def login_local():
    if not os.path.exists(AUTH_FILE):
        print("❌ Not registered. Run register_local() first.")
        return None, None

    with open(AUTH_FILE, "r") as f:
        data = json.load(f)

    username = input("Enter your username: ").strip().lower()
    password = input("Enter your password: ").strip()

    identifier = hash_username(username)
    if identifier != data["identifier"]:
        print("❌ Username does not match.")
        return None, None

    try:
        ph.verify(data["password_hash"], password)
        print("✅ Login successful.")
        return username, password
    except:
        print("❌ Invalid password.")
        return None, None
