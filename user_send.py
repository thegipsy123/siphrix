import os
if not os.path.exists(".vault"):
    os.makedirs(".vault")
channel = None  # we will assign it later
import sys
import peer_connection
public_keys = peer_connection.public_keys
from sticker_store import add_sticker, get_sticker, load_stickers
import random
import threading
import time

ROUTE_CACHE = {}  # 🔁 Stores auto-generated routes for each user

from dotenv import load_dotenv
from app_lock import check_pin

import hashlib
# Step 1A: Announce user to DHT


def announce_to_dht(username, public_key, profile):
    dht_entry = {
        "username_hash": hashlib.sha256(username.encode()).hexdigest(),
        "public_key": public_key,
        "status": profile.get("status"),
        "avatar": profile.get("profile_picture"),
        "bio": profile.get("preferences", {}).get("bio", "")
    }

    if not os.path.exists("dht.json"):
        dht_data = []
    else:
        with open("dht.json", "r", encoding="utf-8") as f:
            dht_data = json.load(f)

    # Add self to DHT (or replace if exists)
    dht_data = [entry for entry in dht_data if entry["username_hash"] != dht_entry["username_hash"]]
    dht_data.append(dht_entry)

    with open("dht.json", "w", encoding="utf-8") as f:
        json.dump(dht_data, f, indent=2)

    print(f"📡 Announced self to DHT as {username}")


try:
    from playsound import playsound
except ImportError:
    playsound = None

try:
    from win10toast import ToastNotifier
except ImportError:
    ToastNotifier = None

notifier = ToastNotifier() if ToastNotifier else None

load_dotenv()
if not check_pin():
    exit()  # 🔒 Stop app if PIN is wrong
from auth import login_local
from peer_connection import start_webrtc_chat
import asyncio
import json

from datetime import datetime
from constants import USAGE_FILE, GROUP_FILE, HISTORY_FILE, PINNED_FILE
from profile_manager import load_profile
username, password = login_local()
from key_storage import rotate_keys, rotate_keys_if_expired

rotate = input('🔁 Rotate encryption keys before starting? (yes/no): ').strip().lower() == 'yes'
if rotate:
    print('🔐 Rotating keys...')
    private_key, public_key = rotate_keys(f"{username}_keys.json")
else:
    from key_storage import load_or_create_keys
    private_key, public_key = load_or_create_keys(f"{username}_keys.json")

rotate_keys_if_expired()


if not username:
    sys.exit(1)
print("🔍 CWD:", os.getcwd())
print("🔍 .env exists:", os.path.exists(".env"))
profile = load_profile()
announce_to_dht(username, public_key, profile)


status = profile["status"]

# 9️⃣ Now load your keys and continue


def pick_random_route(final_user, all_peers, count=2):
    relays = [p for p in all_peers if p != final_user]
    if not relays:
        return [final_user]
    hops = random.sample(relays, min(count, len(relays)))
    return hops + [final_user]


def auto_rotate_routes(peers):
    while True:
        for friend in peers:
            route = pick_random_route(friend, list(peers.keys()), count=3)
            ROUTE_CACHE[friend] = route
            print(f"🔄 New onion route to {friend}: {' → '.join(route)}")

        time.sleep(180)  # Rotate every 3 minutes


def update_stats(category, amount=1):
    stats = {"messages_sent": 0, "files_sent": 0, "data_sent_kb": 0}
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, "r") as f:
            stats.update(json.load(f))
    if category == "msg":
        stats["messages_sent"] += amount
    elif category == "file":
        stats["files_sent"] += amount
    elif category == "data":
        stats["data_sent_kb"] += amount
    with open(USAGE_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def extract_hashtags(text):
    return re.findall(r"#(\w+)", text)


def log_message_to_history(recipient, text):
    from ecdh_encryption import encrypt_message

    encrypted = encrypt_message(private_key, public_key, text)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] To {recipient}: {encrypted}\n")


def read_encrypted_history():
    from ecdh_encryption import decrypt_message

    if not os.path.exists(HISTORY_FILE):
        print("📭 No history found.")
        return

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                prefix, encrypted = line.split(": ", 1)
                decrypted = decrypt_message(private_key, public_key, encrypted.strip())
                print(f"{prefix}: {decrypted}")
            except:
                print("⚠️ Could not decrypt line:", line.strip())


def search_messages(query):
    from ecdh_encryption import decrypt_message
    if not os.path.exists(HISTORY_FILE):
        print("📭 No chat history found.")
        return

    found = 0
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                if ": " not in line:
                    continue
                prefix, encrypted = line.strip().split(": ", 1)
                decrypted = decrypt_message(private_key, public_key, encrypted)
                if query.lower() in decrypted.lower():
                    print(f"🔍 {prefix}: {decrypted}")
                    found += 1
            except:
                continue

    if found == 0:
        print("🔎 No matching messages found.")


def save_tag(tag, message):
    data = {}
    if os.path.exists("tags.json"):
        with open("tags.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    data.setdefault(tag, []).append(message)
    with open("tags.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_mention(username, message):
    data = {}
    if os.path.exists("mentions.json"):
        with open("mentions.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    data.setdefault(username, []).append(message)
    with open("mentions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_sent_id(recipient, msg_id, content):
    file = "sent_ids.json"
    data = {}

    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

    if recipient not in data:
        data[recipient] = {}

    if msg_id not in data[recipient]:  # Only save if it's new
        data[recipient][msg_id] = content
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def list_sent_ids():
    if not os.path.exists("sent_ids.json"):
        print("📭 No sent messages stored.")
        return
    with open("sent_ids.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    print("🆔 Sent Message IDs:")
    for user, messages in data.items():
        for mid, content in messages.items():
            print(f"   {user} → {mid}: {content}")


def load_pinned():
    if os.path.exists(PINNED_FILE):
        with open(PINNED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def search_dht(username):
    if not os.path.exists("dht.json"):
        print("📭 No DHT file found.")
        return None
    with open("dht.json", "r", encoding="utf-8") as f:
        dht = json.load(f)
    for entry in dht:
        if entry.get("username_hash") == hashlib.sha256(username.encode()).hexdigest():
            return entry
    return None


def save_pinned(pins):
    with open(PINNED_FILE, "w", encoding="utf-8") as f:
        json.dump(pins, f, indent=2)


def get_pinned_for(user):
    pins = load_pinned()
    return pins.get(user, [])


def set_pinned_for(user, message):
    pins = load_pinned()
    if user not in pins:
        pins[user] = []
    pins[user].append(message)
    save_pinned(pins)


def unpin_message(user, index):
    pins = load_pinned()
    if user in pins and 0 <= index < len(pins[user]):
        removed = pins[user].pop(index)
        if not pins[user]:
            del pins[user]
        save_pinned(pins)
        return removed
    return None


def export_chat():
    if not os.path.exists(HISTORY_FILE):
        print("📭 No chat history to export.")
        return

    export_path = input("Enter export file name (e.g. my_chat.txt): ").strip()
    if not export_path:
        print("❌ Invalid filename.")
        return

    with open(HISTORY_FILE, "r", encoding="utf-8") as src:
        with open(export_path, "w", encoding="utf-8") as dst:
            dst.writelines(src.readlines())

    print(f"✅ Chat history exported to {export_path}")


def get_expiry_seconds():
    print("\nChoose message expiration:")
    print("1. 1 minute\n2. 5 minutes\n3. Custom\n4. Never delete")
    choice = input("Enter choice [1-4]: ").strip()
    if choice == "1": return 60
    elif choice == "2": return 300
    elif choice == "3":
        unit = input("Unit (seconds/minutes/hours): ").strip().lower()
        value = int(input("Enter value: "))
        return value * {"seconds": 1, "minutes": 60, "hours": 3600}.get(unit, 1)
    return None  # Never delete


def handle_command(text):
    text = text.strip()

    if text == "/showtags":
        if os.path.exists("tags.json"):
            with open("tags.json", "r", encoding="utf-8") as f:
                tags = json.load(f)
                print("📌 Tags so far:")
                for tag, items in tags.items():
                    print(f" - {tag} ({len(items)} messages)")
        else:
            print("📭 No tags found.")
        return True

    elif text == "/emojilist":
        from emoji_store import load_emojis
        emojis = load_emojis()
        if not emojis:
            print("📭 No emojis saved.")
        else:
            print("😊 Saved Emojis:")
            for name, symbol in emojis.items():
                print(f"{symbol} {name}")
        return True

    elif text == "/stats":
        if os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, "r", encoding="utf-8") as f:
                stats = json.load(f)
            print("\n📊 Usage Stats:")
            print(f"   - Messages sent: {stats.get('messages_sent', 0)}")
            print(f"   - Files sent:    {stats.get('files_sent', 0)}")
            print(f"   - Data sent:     {stats.get('data_sent_kb', 0)} KB")
        else:
            print("📭 No usage stats found.")
        return True

    elif text == "/dashboard":
        from usage_dashboard import show_usage_dashboard
        show_usage_dashboard()
        return True




    elif text == "/edithistory":
        if not os.path.exists("edit_history.json"):
            print("📭 No edit history.")
            return True
        with open("edit_history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
        print("📝 Message Edit History:")
        for user, edits in history.items():
            for msg_id, changes in edits.items():
                print(f"  🔄 {user} / ID {msg_id}:")
                for item in changes:
                    print(f"     - {item['time']}: {item['new_text']}")
        return True


    elif text == "/cleartags":
        if os.path.exists("tags.json"):
            os.remove("tags.json")
            print("🧹 All tags cleared.")
        else:
            print("📭 No tags to clear.")
        return True

    elif text == "/clearmentions":
        if os.path.exists("mentions.json"):
            os.remove("mentions.json")
            print("🧹 All mentions cleared.")
        else:
            print("📭 No mentions to clear.")
        return True

    elif text.startswith("/findtag "):
        tag = text.replace("/findtag ", "").strip("# ")
        if os.path.exists("tags.json"):
            with open("tags.json", "r", encoding="utf-8") as f:
                tags = json.load(f)
            if tag in tags:
                print(f"\n🔍 Messages with #{tag}:")
                for msg in tags[tag]:
                    print(f" - {msg}")
            else:
                print(f"❌ No messages found with tag #{tag}")
        else:
            print("📭 No tags saved.")
        return True

    elif text.startswith("/findmention "):
        name = text.replace("/findmention ", "").strip("@ ")
        if os.path.exists("mentions.json"):
            with open("mentions.json", "r", encoding="utf-8") as f:
                mentions = json.load(f)
            if name in mentions:
                print(f"\n📣 Messages mentioning @{name}:")
                for msg in mentions[name]:
                    print(f" - {msg}")
            else:
                print(f"❌ No mentions for @{name}")
        else:
            print("📭 No mentions saved.")
        return True


    elif text.startswith("/react "):

        try:

            parts = text.split(" ")

            msg_id = parts[1]

            emoji_or_name = parts[2]

            from emoji_store import get_custom_emoji

            from reactions import add_reaction

            # Try loading custom emoji by name

            actual_emoji = get_custom_emoji(emoji_or_name)

            if actual_emoji:

                emoji = actual_emoji

            else:

                emoji = emoji_or_name  # Use raw emoji if no match

            add_reaction(msg_id, emoji, username)

        except:

            print("❌ Usage: /react msg_id emoji_or_name")

        return True


    elif text.startswith("/reactions "):
        from reactions import show_reactions
        msg_id = text.split(" ", 1)[1].strip()
        show_reactions(msg_id)
        return True

    elif text == "/stats":
        if os.path.exists("usage_stats.json"):
            with open("usage_stats.json", "r", encoding="utf-8") as f:
                stats = json.load(f)
            print("📊 Usage Stats:")
            print(f" - Messages sent: {stats.get('messages_sent', 0)}")
            print(f" - Files sent: {stats.get('files_sent', 0)}")
            print(f" - Data sent (KB): {stats.get('data_sent_kb', 0)}")
        else:
            print("📭 No usage stats yet.")
        return True
    elif text == "/showtags":
        if os.path.exists("tags.json"):
            with open("tags.json", "r", encoding="utf-8") as f:
                tags = json.load(f)
                print("📌 Tags so far:")
                for tag, items in tags.items():
                    print(f" - {tag} ({len(items)} messages)")
        else:
            print("📭 No tags found.")
        return True



    elif text == "/cleartags":
        if os.path.exists("tags.json"):
            os.remove("tags.json")
            print("🧹 All tags cleared.")
        else:
            print("📭 No tags to clear.")
        return True

    elif text == "/clearmentions":
        if os.path.exists("mentions.json"):
            os.remove("mentions.json")
            print("🧹 All mentions cleared.")
        else:
            print("📭 No mentions to clear.")
        return True

    elif text == "/exportchat":
        export_chat()
        return True

    elif text.startswith("/search "):
        term = text.split(" ", 1)[1].strip()
        search_messages(term)
        return True

    elif text == "/exportkeys":
        from qr_transfer import export_keys_to_qr
        export_keys_to_qr(username)
        return True

    elif text.startswith("/importkeys "):
        from qr_transfer import import_keys_from_qr
        image_path = text.split(" ", 1)[1].strip()
        import_keys_from_qr(image_path)
        return True

    elif text.startswith("/loadvault "):
        from vault_manager import load_encrypted_from_vault
        parts = text.split(" ", 1)
        if len(parts) < 2:
            print("❌ Usage: /loadvault filename")
            return True
        filename = parts[1].strip()
        result = load_encrypted_from_vault(filename, private_key, public_key)
        if result:
            print(f"🔓 Vault contents of '{filename}':\n{result}")
        return True

    elif text == "/showpins":
        user = input("👤 Whose pinned messages? ").strip()
        pins = get_pinned_for(user)
        if pins:
            print(f"📌 Pinned messages for {user}:")
            for i, msg in enumerate(pins):
                print(f" {i+1}. {msg}")
        else:
            print(f"📭 No pinned messages for {user}")
        return True



    elif text == "/mentions":
        if os.path.exists("mentions.json"):
            with open("mentions.json", "r", encoding="utf-8") as f:
                mentions = json.load(f)
                print("📣 Mentions so far:")
                for mention, items in mentions.items():
                    print(f" - @{mention} ({len(items)} messages)")
        else:
            print("📭 No mentions found.")
        return True

    elif text.startswith("/addemoji "):
        try:
            parts = text.split(" ", 2)
            name = parts[1].strip()
            emoji = parts[2].strip()
            from emoji_store import add_custom_emoji
            add_custom_emoji(name, emoji)
        except:
            print("❌ Usage: /addemoji name emoji")
        return True

    elif text.startswith("/emoji "):
        try:
            name = text.split(" ", 1)[1].strip()
            from emoji_store import get_custom_emoji
            emoji = get_custom_emoji(name)
            if emoji:
                print(f"🔎 Emoji '{name}': {emoji}")
            else:
                print(f"❌ No emoji found for '{name}'")
        except:
            print("❌ Usage: /emoji name")
        return True

    elif text == "/emojis":
        from emoji_store import load_emojis
        emojis = load_emojis()
        if emojis:
            print("🎨 Custom Emojis:")
            for name, emoji in emojis.items():
                print(f" - {name}: {emoji}")
        else:
            print("📭 No custom emojis saved.")
        return True

    elif text.startswith("/removeemoji "):
        from emoji_store import remove_emoji
        name = text.replace("/removeemoji ", "").strip()
        remove_emoji(name)
        return True

    elif text.startswith("/updateemoji "):
        try:
            parts = text.split(" ", 2)
            name = parts[1].strip().lower()
            new_emoji = parts[2].strip()
            from emoji_store import update_custom_emoji
            if update_custom_emoji(name, new_emoji):
                print(f"🔁 Updated emoji '{name}' to {new_emoji}")
            else:
                print(f"❌ Emoji '{name}' not found.")
        except:
            print("❌ Usage: /updateemoji emoji_name new_emoji")
        return True

    elif text.startswith("/deleteemoji "):
        from emoji_store import delete_emoji
        name = text.split(" ", 1)[1].strip().lower()
        if delete_emoji(name):
            print(f"🗑️ Deleted emoji '{name}'.")
        else:
            print(f"❌ Emoji '{name}' not found.")
        return True


    elif text.startswith("/sendemoji "):
        global channel
        from emoji_store import load_emojis
        parts = text.split(" ", 2)
        if len(parts) < 3:
            print("❌ Usage: /sendemoji [username] [emoji_name]")
            return True
        recipient = parts[1]
        emoji_name = parts[2]

        emojis = load_emojis()
        if emoji_name not in emojis:
            print(f"❌ Emoji '{emoji_name}' not found.")
            return True

        emoji_value = emojis[emoji_name]

        from hashlib import sha256
        msg_hash = sha256(emoji_value.encode()).hexdigest()
        from ecdh_encryption import encrypt_message, sign_message

        if recipient not in peer_connection.public_keys:
            print(f"🔍 Requesting public key from {recipient}...")
            from peer_connection import public_keys  # just to be sure
            # Ideally your relay/request system handles this

        encrypted = encrypt_message(private_key, public_keys.get(recipient, ""), emoji_value)
        signature = sign_message(private_key, emoji_value)
        payload = f"@msg::{username}::{msg_hash}::None::{encrypted}::{signature}"
        print(f"📤 Sending emoji '{emoji_name}' to {recipient}...")

        # Send it
        if recipient in public_keys:
            if channel:
                channel.send(payload)
                print("✅ Emoji sent!")
            else:
                print("❌ Channel not ready yet.")
        else:
            print("📭 Person offline. Queuing message.")
            queue_offline_message(recipient, payload)


    elif text == "/listemojis":
        from emoji_store import load_emojis
        emojis = load_emojis()
        if not emojis:
            print("📭 No emojis saved yet.")
        else:
            print("🎨 Saved Emojis:")
            for name, val in emojis.items():
                print(f" - {name}: {val}")
        return True

    elif text.startswith("/delemoji "):
        from emoji_store import delete_emoji
        name = text.split(" ", 1)[1].strip()
        if delete_emoji(name):
            print(f"🗑️ Emoji '{name}' deleted.")
        else:
            print(f"❌ Emoji '{name}' not found.")
        return True

    elif text == "/wipeemojis":
        from emoji_store import wipe_all_emojis
        wipe_all_emojis()
        return True

    elif text == "/emojiinfo":
        from emoji_store import load_emojis
        emojis = load_emojis()
        if not emojis:
            print("📭 No emojis saved.")
        else:
            sorted_emojis = sorted(emojis.items())
            print(f"📦 You have {len(sorted_emojis)} custom emojis:")
            for name, emoji in sorted_emojis:
                print(f" - {name}: {emoji}")
        return True

    elif text.startswith("/importemojis "):
        file_path = text.split(" ", 1)[1].strip()
        from emoji_store import import_emoji_pack
        import_emoji_pack(file_path)
        return True

    elif text.startswith("/addsticker "):
        try:
            parts = text.split(" ", 2)
            name = parts[1].strip()
            path = parts[2].strip()
            if os.path.exists(path):
                add_sticker(name, path)
                print(f"✅ Sticker '{name}' added.")
            else:
                print("❌ File not found.")
        except:
            print("❌ Usage: /addsticker name path_to_image")
        return True

    elif text == "/stickers":
        stickers = load_stickers()
        if not stickers:
            print("📭 No stickers saved.")
        else:
            print("🎟️ Saved Stickers:")
            for name, path in stickers.items():
                print(f" - {name}: {path}")
        return True

    elif text.startswith("/sendsticker "):
        parts = text.split(" ", 2)
        if len(parts) < 3:
            print("❌ Usage: /sendsticker username sticker_name")
            return True
        recipient = parts[1].strip()
        sticker_name = parts[2].strip()
        path = get_sticker(sticker_name)
        if not path or not os.path.exists(path):
            print("❌ Sticker not found.")
            return True

        # Send it like a file
        with open(path, "rb") as f:
            data = f.read()
        from hashlib import sha256
        from ecdh_encryption import encrypt_message, sign_message

        file_hash = sha256(data).hexdigest()
        encrypted = encrypt_message(private_key, peer_connection.public_keys.get(recipient, ""), data.decode(errors="ignore"))
        filename = os.path.basename(path)
        signature = sign_message(private_key, filename)
        payload = f"@file::{username}::{filename}::{file_hash}::None::{encrypted}"

        if recipient in peer_connection.public_keys:
            if channel:
                channel.send(payload)
                print(f"📤 Sticker '{sticker_name}' sent to {recipient}")
            else:
                print("❌ Channel not ready yet.")
        else:
            queue_offline_message(recipient, payload)
            print(f"📥 Person offline. Queued sticker '{sticker_name}'")

        return True


    elif text == "/share_dht":
        if os.path.exists("dht.json"):
            with open("dht.json", "r", encoding="utf-8") as f:
                dht_data = json.load(f)
            payload = json.dumps({
                "type": "dht_share",
                "from": username,
                "data": dht_data
            })
            if channel:
                channel.send(payload)
                print("📡 Shared DHT with peer.")
            else:
                print("❌ Channel not ready yet.")
        else:
            print("📭 No DHT to share.")
        return True


    elif text == "/sendonion":
        global channel
        try:
            route = input("🔗 Enter onion route (comma-separated usernames): ").strip().lower().split(",")
            route = [r.strip() for r in route if r.strip()]
            final_message = input("💬 What is the secret message? ").strip()

            if not route or not final_message:
                print("❌ Route or message missing.")
                return True

            from ecdh_encryption import encrypt_message
            payload = final_message
            for hop in reversed(route):
                if hop not in peer_connection.public_keys:
                    print(f"❌ No public key for {hop}.")
                    return True
                payload = encrypt_message(private_key, peer_connection.public_keys[hop], payload)

            first_hop = route[0]
            full = {
                "type": "onion",
                "route": route[1:],  # the rest after first hop
                "payload": payload
            }

            # Encrypt outermost layer for first hop
            outer = encrypt_message(private_key, peer_connection.public_keys[first_hop], json.dumps(full))
            final_payload = json.dumps({
                "type": "onion",
                "route": [first_hop],
                "payload": outer
            })

            if channel:
                channel.send(final_payload)
                print(f"🧅 Sent onion message through route: {' → '.join(route)}")
            else:
                print("❌ Channel not ready yet.")

            print(f"🧅 Sent onion message through route: {' → '.join(route)}")

        except Exception as e:
            print("❌ Error sending onion:", e)
        return True

    elif text == "/anonmsg":
        global channel
        target = input("👤 Who do you want to message anonymously? ").strip().lower()
        entry = search_dht(target)
        if not entry:
            print("❌ User not found in DHT.")
            return True

        msg = input("💬 What’s the message? ").strip()
        from ecdh_encryption import encrypt_message
        from peer_connection import public_keys, channel

        # Dummy example route (in real case, you'd choose 3 trusted friends)
        route = ROUTE_CACHE.get(target)
        if not route:
            print("❌ No cached route found for that user.")
            return True
        print(f"🔁 Using route from cache: {' → '.join(route)}")

        # Make sure you have keys
        for peer in route:
            if peer not in public_keys:
                print(f"🔍 Requesting key from {peer}...")
                channel.send(f"@request_key::{peer}")
                import time
                for _ in range(10):
                    time.sleep(0.5)
                    if peer in public_keys:
                        break
            if peer not in public_keys:
                print(f"❌ Missing public key for {peer}.")
                return True

        payload = msg
        for peer in reversed(route):
            payload = encrypt_message(private_key, public_keys[peer], payload)

        outer = json.dumps({
            "type": "onion",
            "route": route[1:],  # skip first hop
            "payload": payload
        })

        wrapped = encrypt_message(private_key, public_keys[route[0]], outer)

        final = json.dumps({
            "type": "onion",
            "route": [route[0]],
            "payload": wrapped
        })

        if channel:
            channel.send(final)
            print(f"📤 Sent anonymous message to {target} via: {' → '.join(route)}")
        else:
            print("❌ Channel not ready yet.")

        return True

    return False  # Not a command, keep going with normal message logic


def save_group(name, members):
    groups = {}
    if os.path.exists(GROUP_FILE):
        with open(GROUP_FILE, "r", encoding="utf-8") as f:
            groups = json.load(f)
    groups[name] = members
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(groups, f, indent=2)


def load_group(name):
    if os.path.exists(GROUP_FILE):
        with open(GROUP_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get(name)
    return None

read_encrypted_history()




def update_message_status(recipient, msg_id, status):
    file = "message_status.json"
    data = {}

    # Load old data
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

    if recipient not in data:
        data[recipient] = {}

    # Prevent overwriting "read" with "delivered"
    current = data[recipient].get(msg_id)
    if current == "read":
        return

    data[recipient][msg_id] = status

    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def queue_offline_message(recipient, payload):
    data = {}
    if os.path.exists("offline_queue.json"):
        with open("offline_queue.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    data.setdefault(recipient, []).append(payload)
    with open("offline_queue.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)




def try_send_with_retry(websocket, recipient, payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            asyncio.run(websocket.send(json.dumps(payload)))
            print(f"✅ Sent to {recipient} on try {attempt + 1}")
            return True
        except Exception as e:
            print(f"⚠️ Try {attempt + 1} failed for {recipient}. Error: {e}")
            time.sleep(1)  # wait 1 second before retry
    print(f"📭 Failed to send to {recipient}. Queuing offline.")
    queue_offline_message(recipient, payload)


    return False


def panic_wipe(username):
    files_to_delete = [
        "inbox_history.txt",
        "usage_stats.json",
        "contacts.json",
        "contacts_info.json",
        "profile.json",
        f"{username}_keys.json",
        "tags.json",
        "mentions.json",
        "sent_ids.json",
        "groups.json",
        "pinned_messages.json",
        "offline_queue.json"
    ]
    print("\n⚠️ WARNING: This will delete ALL your local data. This cannot be undone.")
    confirm = input("Type 'WIPE' to confirm: ").strip()
    if confirm != "WIPE":
        print("❌ Panic wipe canceled.")
        return

    for file in files_to_delete:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️ Deleted {file}")

    if os.path.exists("vault"):
        import shutil
        shutil.rmtree("vault", ignore_errors=True)
        print("🗑️ Deleted vault folder")

    print("💥 All local data wiped. App reset complete.")


from ecdh_encryption import sign_message, verify_signature

# Start the program
print("🖋️ Signing test: Verifying message signing works...")

test = "Hello"
sig = sign_message(private_key, test)
if verify_signature(public_key, test, sig):
    print("✅ Signature valid.")
else:
    print("❌ Signature failed.")

def cleanup_message_state():
    import json
    removed_entries = {"sent_ids": 0, "message_status": 0, "unread_count": 0}

    # Clean sent_ids.json
    if os.path.exists("sent_ids.json"):
        with open("sent_ids.json", "r", encoding="utf-8") as f:
            sent_ids = json.load(f)
        for user in list(sent_ids.keys()):
            for msg_id in list(sent_ids[user].keys()):
                if os.path.exists("message_status.json"):
                    with open("message_status.json", "r", encoding="utf-8") as mf:
                        status_data = json.load(mf)
                    if user in status_data and msg_id in status_data[user]:
                        if status_data[user][msg_id] == "read":
                            del sent_ids[user][msg_id]
                            removed_entries["sent_ids"] += 1
            if not sent_ids[user]:
                del sent_ids[user]
        with open("sent_ids.json", "w", encoding="utf-8") as f:
            json.dump(sent_ids, f, indent=2)

    # Clean message_status.json
    if os.path.exists("message_status.json"):
        with open("message_status.json", "r", encoding="utf-8") as f:
            status_data = json.load(f)
        for user in list(status_data.keys()):
            for msg_id in list(status_data[user].keys()):
                if status_data[user][msg_id] == "read":
                    del status_data[user][msg_id]
                    removed_entries["message_status"] += 1
            if not status_data[user]:
                del status_data[user]
        with open("message_status.json", "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2)

    # Clean unread_count.json
    if os.path.exists("unread_count.json"):
        with open("unread_count.json", "r", encoding="utf-8") as f:
            unread_data = json.load(f)
        unread_data = {k: v for k, v in unread_data.items() if v > 0}
        removed_entries["unread_count"] += 1
        with open("unread_count.json", "w", encoding="utf-8") as f:
            json.dump(unread_data, f, indent=2)

    print("🧹 Cleanup complete:", removed_entries)


def handle_incoming_receipt(msg: str):
    if msg.startswith("@read::"):
        reader = msg.split("::")[1]
        print(f"👀 Message read by {reader} (✅✅✨)")

        # ✅ Reset unread count to 0 when they read it
        unread_file = "unread_count.json"
        try:
            if os.path.exists(unread_file):
                with open(unread_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if reader in data:
                    data[reader] = 0
                    with open(unread_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    print(f"🔄 Unread count reset for {reader}")
        except Exception as e:
            print("⚠️ Could not reset unread count:", e)

    elif msg.startswith("@delivered::"):
        reader = msg.split("::")[1]
        print(f"📬 Message delivered to {reader} (✅)")

cleanup_message_state()

import re
from emoji_store import load_emojis


def check_for_reminder(text, sender):
    match = re.search(r"remind me in (\d+)\s*(sec|second|seconds|min|minute|minutes)", text.lower())
    if match:
        number = int(match.group(1))
        unit = match.group(2)

        seconds = number
        if "min" in unit:
            seconds *= 60

        def remind_later():
            time.sleep(seconds)
            print(f"⏰ Reminder: {sender} asked to be reminded '{text}'")

        threading.Thread(target=remind_later, daemon=True).start()
        print(f"🧠 Reminder set for {number} {unit}.")

def load_scheduled_messages():
    if os.path.exists("scheduled_messages.json"):
        with open("scheduled_messages.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_scheduled_messages(messages):
    with open("scheduled_messages.json", "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2)

def schedule_message(recipient, text, send_time_str):
    try:
        send_time = datetime.strptime(send_time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        print("❌ Invalid format. Use YYYY-MM-DD HH:MM")
        return
    messages = load_scheduled_messages()
    messages.append({
        "to": recipient,
        "text": text,
        "time": send_time_str
    })
    save_scheduled_messages(messages)
    print(f"⏳ Scheduled message to {recipient} at {send_time_str}")

def start_scheduled_sender(channel, username, private_key, public_key, encrypt_message, sign_message):
    def check_loop():
        while True:
            now = datetime.now()
            messages = load_scheduled_messages()
            remaining = []
            for msg in messages:
                send_time = datetime.strptime(msg["time"], "%Y-%m-%d %H:%M")
                if now >= send_time:
                    text = msg["text"]
                    recipient = msg["to"]
                    from hashlib import sha256
                    emojis = load_emojis()
                    for name, symbol in emojis.items():
                        text = text.replace(f":{name}:", symbol)
                    msg_hash = sha256(text.encode()).hexdigest()
                    encrypted = encrypt_message(private_key, peer_connection.public_keys.get(recipient, ""), text)
                    signature = sign_message(private_key, text)
                    payload = f"@msg::{username}::{msg_hash}::None::{encrypted}::{signature}"
                    channel.send(payload)
                    print(f"📤 Sent scheduled message to {recipient}")
                else:
                    remaining.append(msg)
            save_scheduled_messages(remaining)
            time.sleep(60)
    t = threading.Thread(target=check_loop, daemon=True)
    t.start()



asyncio.run(start_webrtc_chat(username, private_key, public_key))
import __main__
channel = getattr(__main__, "channel", None)
# ✅ Start auto route rotation (every 3 minutes)
t = threading.Thread(target=auto_rotate_routes, args=(peer_connection.public_keys,), daemon=True)
t.start()
