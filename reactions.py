import os
import json

REACTIONS_FILE = "reactions.json"


def load_reactions():
    if os.path.exists(REACTIONS_FILE):
        with open(REACTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_reactions(data):
    with open(REACTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def add_reaction(msg_id, emoji, username):
    data = load_reactions()
    data.setdefault(msg_id, {})
    data[msg_id][username] = emoji
    save_reactions(data)
    print(f"😊 {username} reacted to {msg_id} with {emoji}")


def show_reactions(msg_id):
    data = load_reactions()
    if msg_id in data:
        for user, emoji in data[msg_id].items():
            print(f"   {user} → {emoji}")
    else:
        print("❌ No reactions for that message.")
