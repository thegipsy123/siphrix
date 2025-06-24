import os
import json

PINNED_FILE = "pinned.json"


def load_pins():
    if os.path.exists(PINNED_FILE):
        with open(PINNED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_pins(pins):
    with open(PINNED_FILE, "w", encoding="utf-8") as f:
        json.dump(pins, f, indent=2)





def get_pinned(contact):
    pins = load_pins()
    return pins.get(contact, [])


def get_pinned_for(username):
    import json, os
    if not os.path.exists("pinned.json"):
        return []
    with open("pinned.json", "r", encoding="utf-8") as f:
        all_pins = json.load(f)
    return all_pins.get(username, [])

def set_pinned_for(username, message):
    import json, os
    pinned_file = "pinned.json"
    if os.path.exists(pinned_file):
        with open(pinned_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    data.setdefault(username, [])
    if message not in data[username]:
        data[username].insert(0, message)  # add to top

    with open(pinned_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def unpin_message(username, index):
    if not os.path.exists(PINNED_FILE):
        return None
    with open(PINNED_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if username not in data or index >= len(data[username]):
        return None
    removed = data[username].pop(index)
    with open(PINNED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return removed
