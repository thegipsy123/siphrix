import os
import json

EMOJI_FILE = "custom_emojis.json"


def load_emojis():
    if os.path.exists(EMOJI_FILE):
        with open(EMOJI_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_emojis(emojis):
    with open(EMOJI_FILE, "w", encoding="utf-8") as f:
        json.dump(emojis, f, indent=2)


def add_custom_emoji(name, emoji):
    emojis = load_emojis()
    emojis[name] = emoji
    save_emojis(emojis)
    print(f"✨ Added emoji '{emoji}' as '{name}'")


def get_custom_emoji(name):
    return load_emojis().get(name)


def remove_emoji(name):
    emojis = load_emojis()
    if name in emojis:
        del emojis[name]
        save_emojis(emojis)
        print(f"🗑️ Removed emoji '{name}'")
    else:
        print(f"❌ Emoji '{name}' not found.")


def update_custom_emoji(name, new_value):
    emojis = load_emojis()
    name = name.lower()
    if name in emojis:
        emojis[name] = new_value
        save_emojis(emojis)
        return True
    return False


def import_emoji_pack(file_path):
    if not os.path.exists(file_path):
        print("❌ File not found.")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            imported = json.load(f)

        if not isinstance(imported, dict):
            print("❌ Invalid format. Must be a JSON object.")
            return

        emojis = load_emojis()
        emojis.update(imported)

        with open("emojis.json", "w", encoding="utf-8") as f:
            json.dump(emojis, f, indent=2)

        print(f"✅ Imported {len(imported)} emojis.")
    except Exception as e:
        print("❌ Failed to import emoji pack:", e)


def wipe_all_emojis():
    import os
    if os.path.exists("emojis.json"):
        os.remove("emojis.json")
        print("🧹 All emojis wiped.")
    else:
        print("📭 No emoji file to wipe.")


def delete_emoji(name):
    if not os.path.exists("emojis.json"):
        return False
    with open("emojis.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    if name in data:
        del data[name]
        with open("emojis.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    return False
