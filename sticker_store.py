import os
import json

STICKERS_FILE = "stickers.json"


def load_stickers():
    if os.path.exists(STICKERS_FILE):
        with open(STICKERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_stickers(data):
    with open(STICKERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def add_sticker(name, path):
    data = load_stickers()
    data[name] = path
    save_stickers(data)


def remove_sticker(name):
    data = load_stickers()
    if name in data:
        del data[name]

        save_stickers(data)


def get_sticker(name):
    return load_stickers().get(name)
