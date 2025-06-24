import os
import json

PROFILE_FILE = "profile.json"

DEFAULT_PROFILE = {
    "username": "",
    "status": "Available",
    "profile_picture": "",
    "preferences": {
        "notifications": True,
        "language": "en",
        "theme": "light"
    }
}

def load_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        profile = setup_profile()
        save_profile(profile)
        return profile

def save_profile(profile):
    os.makedirs("profiles", exist_ok=True)
    with open("profile.json", "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
    # Also save a public version
    username = profile.get("username")
    if username:
        with open(f"profiles/{username}.json", "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)


def setup_profile():
    profile = DEFAULT_PROFILE.copy()
    profile["username"] = input("Enter your Siphrix username: ").strip().lower()
    profile["status"] = input("Set your status (default: Available): ").strip() or "Available"
    profile["profile_picture"] = input("Path to profile picture (optional): ").strip()
    print("Preferences:")
    profile["preferences"]["notifications"] = input("Enable notifications? (yes/no): ").strip().lower() != "no"
    profile["preferences"]["language"] = input("Preferred language (en/es/de/etc): ").strip().lower() or "en"
    profile["preferences"]["theme"] = input("Theme (light/dark): ").strip().lower() or "light"
    return profile

def get_username():
    return load_profile()["username"]

def get_status():
    return load_profile()["status"]

def get_preferences():
    return load_profile()["preferences"]

def update_status(new_status):
    profile = load_profile()
    profile["status"] = new_status
    save_profile(profile)

def update_preferences(new_prefs: dict):
    profile = load_profile()
    profile["preferences"].update(new_prefs)
    save_profile(profile)
def get_contact_profile(username):
    try:
        with open("contacts_info.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(username, {})
    except:
        return {}
