# peer_connection.py

import asyncio
import json
import os
import cv2
channel = None
from aiortc import RTCPeerConnection, RTCSessionDescription
try:
    from playsound import playsound
except ImportError:
    playsound = None
public_keys = {}
presence_status = {}
from auto_backup import should_backup, create_auto_backup
from pinned import set_pinned_for
from pinned import get_pinned_for, unpin_message


# 💡 Temporary signal file (simulate QR exchange or basic server)
SIGNAL_FILE = "signal_offer.json"

GROUP_FILE = "groups.json"


def load_groups():
    if os.path.exists(GROUP_FILE):
        with open(GROUP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_groups(groups):
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(groups, f, indent=2)


def auto_share_dht(channel, username):
    if not os.path.exists("dht.json"):
        print("📭 No DHT to share.")
        return

    with open("dht.json", "r", encoding="utf-8") as f:
        dht_data = json.load(f)

    payload = json.dumps({
        "type": "dht_share",
        "from": username,
        "data": dht_data
    })

    channel.send(payload)
    print("📡 Auto-shared DHT with all peers.")


def ping_contacts(channel, contacts, username):
    for contact in contacts:
        channel.send(f"@ping::{username}")


from datetime import datetime
from constants import HISTORY_FILE
from ecdh_encryption import encrypt_message
from ecdh_encryption import decrypt_message


def log_received(my_username, sender, text, private_key, public_key):
    encrypted = encrypt_message(private_key, public_key, text)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] From {sender}: {encrypted}\n")


def merge_dht(received, username):
    filename = "dht.json"
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            local = json.load(f)
    else:
        local = []

    hashes = {entry["username_hash"] for entry in local}
    for entry in received:
        if entry["username_hash"] not in hashes:
            local.append(entry)

    # ✅ Sort by XOR distance to your own username
    import hashlib
    my_hash = hashlib.sha256(username.encode()).hexdigest()

    def xor_dist(h1, h2):
        return int(h1, 16) ^ int(h2, 16)
    local.sort(key=lambda e: xor_dist(my_hash, e["username_hash"]))

    local = local[:200]  # Keep only closest 200
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(local, f, indent=2)
    print(f"🤝 Merged {len(received)} entries into DHT.")


def blur_faces(image_path):
    try:
        image = cv2.imread(image_path)
        if image is None:
            print("❌ Could not read image.")
            return None

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        for (x, y, w, h) in faces:
            face = image[y:y + h, x:x + w]
            blurred = cv2.GaussianBlur(face, (99, 99), 30)
            image[y:y + h, x:x + w] = blurred

        out_path = "blurred_output.jpg"
        cv2.imwrite(out_path, image)
        return out_path
    except Exception as e:
        print("❌ Blur failed:", e)
        return None


async def start_webrtc_chat(username, private_key, public_key):
    # Setup
    pc = RTCPeerConnection()
    channel = pc.createDataChannel("siphrix")
    import __main__
    __main__.channel = channel
    from user_send import start_scheduled_sender
    from ecdh_encryption import encrypt_message, sign_message
    start_scheduled_sender(channel, username, private_key, public_key, encrypt_message, sign_message)

    print(f"📡 [{username}] Peer connection created.")

    async def monitor_presence():
        while True:
            for person in presence_status:
                if presence_status[person] != "🟢 online":
                    presence_status[person] = "⚫ offline"
            await asyncio.sleep(30)

    # When message is received
    @channel.on("message")
    async def on_message(message):

        # ✅ Handle onion messages
        try:
            parsed = json.loads(message)
            from ecdh_encryption import decrypt_message

            if parsed.get("type") == "onion":
                route = parsed.get("route", [])
                encrypted_payload = parsed.get("payload")

                if not route:
                    print("📩 Final onion message reached me!")
                    from ecdh_encryption import decrypt_message
                    decrypted = decrypt_message(private_key, "", encrypted_payload)
                    print("🔓 Onion payload:", decrypted)
                    return

                next_hop = route[0]
                remaining_route = route[1:]

                # Prepare next layer to send
                from ecdh_encryption import encrypt_message
                if next_hop not in public_keys:
                    print(f"❌ No key for next hop: {next_hop}")
                    return

                inner_payload = json.dumps({
                    "type": "onion",
                    "route": remaining_route,
                    "payload": encrypted_payload
                })

                double_encrypted = encrypt_message(private_key, public_keys[next_hop], inner_payload)

                forward = json.dumps({
                    "type": "onion",
                    "route": [next_hop],
                    "payload": double_encrypted
                })

                channel.send(forward)
                print(f"🧅 Forwarded to {next_hop}")
                return
        except:
            pass

        try:

            if message.startswith("@ping::"):
                sender = message.split("::")[1]
                channel.send(f"@pong::{username}")
                return

            if message.startswith("@pong::"):
                sender = message.split("::")[1]
                presence_status[sender] = "🟢 online"
                print(f"🟢 {sender} is online")
                last_seen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Save it to a local file
                seen_data = {}
                if os.path.exists("last_seen.json"):
                    with open("last_seen.json", "r", encoding="utf-8") as f:
                        seen_data = json.load(f)
                seen_data[sender] = last_seen
                with open("last_seen.json", "w", encoding="utf-8") as f:
                    json.dump(seen_data, f, indent=2)

                # ✅ Send any queued messages
                try:
                    from user_send import queue_offline_message
                    if os.path.exists("offline_queue.json"):
                        with open("offline_queue.json", "r", encoding="utf-8") as f:
                            queue = json.load(f)
                        if sender in queue:
                            for payload in queue[sender]:
                                channel.send(payload)
                                print(f"📤 Sent queued message to {sender}")
                            del queue[sender]
                            with open("offline_queue.json", "w", encoding="utf-8") as f:
                                json.dump(queue, f, indent=2)
                except Exception as e:
                    print("⚠️ Failed to send queued messages:", e)

            if message.startswith("@key::"):
                # Save the peer's public key
                parts = message.split("::", 2)
                sender = parts[1]
                pubkey = parts[2]
                public_keys[sender] = pubkey
                print(f"🔐 Received public key from {sender}")
                return

            if message.startswith("@request_key::"):
                parts = message.split("::", 1)
                requester = parts[1]
                key = public_key  # your own public key
                response = f"@key_for::{username}::{key}"
                channel.send(response)
                print(f"📤 Sent public key to {requester}")
                return

            if message.startswith("@key_for::"):
                parts = message.split("::", 2)
                contact = parts[1]
                pubkey = parts[2]
                public_keys[contact] = pubkey
                print(f"📬 Key for {contact} received and saved.")
                return

            if isinstance(message, bytes):
                message = message.decode("utf-8")



            # ✅ Check for DHT sharing
            try:
                parsed = json.loads(message)
                if parsed.get("type") == "dht_share":
                    print(f"📥 Received DHT share from {parsed['from']}")
                    merge_dht(parsed["data"], username)
                    return
            except:
                pass

            if message.startswith("@typing::"):
                sender = message.split("::")[1]
                print(f"✍️ {sender} is typing...")
                return

            if message.startswith("@stop_typing::"):
                sender = message.split("::")[1]
                print(f"✍️ {sender} stopped typing.")
                return

            if message.startswith("@reaction::"):
                parts = message.split("::", 3)
                if len(parts) == 4:
                    sender, msg_id, emoji = parts[1], parts[2], parts[3]
                    print(f"💞 {sender} reacted to msg {msg_id}: {emoji}")
                    if playsound:
                        try:
                            playsound("sounds/reaction.mp3", block=False)
                        except Exception as e:
                            print("🔇 Could not play sound:", e)

                    pass
                return

            if message.startswith("@edit::"):
                parts = message.split("::", 3)
                if len(parts) == 4:
                    sender, msg_id, new_text = parts[1], parts[2], parts[3]
                    print(f"✏️ Message from {sender} (ID: {msg_id}) was edited:")
                    print(f"➡️  New content: {new_text}")

                    # 📝 Save to edit_history.json
                    history_file = "edit_history.json"
                    history = {}
                    if os.path.exists(history_file):
                        with open(history_file, "r", encoding="utf-8") as f:
                            history = json.load(f)
                    history.setdefault(sender, {}).setdefault(msg_id, []).append({
                        "new_text": new_text,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    with open(history_file, "w", encoding="utf-8") as f:
                        json.dump(history, f, indent=2)
                return

            if message.startswith("@delete::"):
                parts = message.split("::", 2)
                if len(parts) == 3:
                    sender, msg_id = parts[1], parts[2]
                    print(f"🗑️ Message from {sender} (ID: {msg_id}) was deleted.")
                return

            from hashlib import sha256

            if message.startswith("@file::"):
                parts = message.split("::", 5)
                sender = parts[1]
                filename = parts[2]
                file_hash = parts[3]
                expiry = parts[4]
                encrypted = parts[5]

                if sender not in public_keys:
                    print(f"❌ No public key for sender: {sender}")
                    return

                # Decrypt
                decrypted_bytes = decrypt_message(private_key, public_keys[sender], encrypted).encode()
                actual_hash = sha256(decrypted_bytes).hexdigest()

                if actual_hash != file_hash:
                    print(f"🚨 File '{filename}' from {sender} failed integrity check!")
                    return

                try:
                    from tkinter import filedialog, Tk
                    Tk().withdraw()
                    folder = filedialog.askdirectory(title="Select folder to save file")
                except Exception as e:
                    print("❌ Could not open folder dialog:", e)
                    folder = "."

                if folder:
                    save_path = os.path.join(folder, f"received_{filename}")
                    # Save decrypted file to disk
                    with open(save_path, "wb") as f:
                        f.write(decrypted_bytes)
                    print(f"📁 File saved to: {save_path}")

                    # ✅ Also store encrypted copy in vault
                    from vault_manager import save_encrypted_to_vault
                    save_encrypted_to_vault(filename, decrypted_bytes.decode(errors="ignore"), private_key,
                                            public_keys[sender])

                    print(f"📁 File from {sender} saved to: {save_path}")

                    if expiry and expiry != "None":
                        try:
                            seconds = int(expiry)
                            print(f"⏳ This file will self-destruct in {seconds} seconds...")
                            await asyncio.sleep(seconds)
                            os.remove(save_path)
                            print("💥 File deleted after view.")
                        except Exception as e:
                            print("⚠️ Error during file expiration:", e)
                else:
                    print("❌ No folder selected.")
                return

            from hashlib import sha256

            if message.startswith("@msg::"):
                parts = message.split("::", 5)
                sender = parts[1]
                msg_hash = parts[2]
                expiry = parts[3]  # seconds as string
                encrypted = parts[4]
                signature = parts[5]

                if sender not in public_keys:
                    print(f"❌ No key for {sender}")
                    return

                try:
                    decrypted = decrypt_message(private_key, public_keys[sender], encrypted)
                    from ecdh_encryption import verify_signature
                    if not verify_signature(public_keys[sender], decrypted, signature):
                        print(f"🚨 Signature check failed for message from {sender}")
                        return

                except Exception as e:
                    print("❌ Decryption failed:", e)
                    return

                actual_hash = sha256(decrypted.encode()).hexdigest()
                if actual_hash != msg_hash:
                    print(f"🚨 Message from {sender} failed hash check!")
                    return

                # 📌 Show pinned messages at the top
                from pinned import get_pinned_for
                pinned = get_pinned_for(sender)
                if pinned:
                    print("📌 Pinned messages:")
                    for i, msg in enumerate(pinned):
                        print(f"   {i + 1}. {msg}")

                print(f"\n📩 Message from {sender}: {decrypted}")

                from user_send import check_for_reminder
                check_for_reminder(decrypted, sender)

                # 🔵 Increase unread count
                unread_file = "unread_count.json"
                try:
                    unread_data = {}
                    if os.path.exists(unread_file):
                        with open(unread_file, "r", encoding="utf-8") as f:
                            unread_data = json.load(f)
                    unread_data[sender] = unread_data.get(sender, 0) + 1
                    with open(unread_file, "w", encoding="utf-8") as f:
                        json.dump(unread_data, f, indent=2)
                    print(f"🔵 Unread count for {sender}: {unread_data[sender]}")
                except Exception as e:
                    print("⚠️ Failed to update unread count:", e)

                # ✅✅ Send read receipt back to sender
                if sender:
                    read_receipt = f"@read::{username}"
                    channel.send(read_receipt)
                # ✅ Send delivery receipt back to sender
                delivered_receipt = f"@delivered::{username}"
                channel.send(delivered_receipt)

                from profile_manager import get_contact_profile  # 📌 Make sure this is at the top of the file!

                profile = get_contact_profile(sender)
                if profile:
                    print("👤 Sender Profile:")
                    print("   - Name:", profile.get("name", "N/A"))
                    print("   - Status:", profile.get("status", "N/A"))
                    print("   - Last seen:", profile.get("last_seen", "N/A"))
                    print("   - Avatar path:", profile.get("avatar", "Not set"))
                # ✅ Show last seen info
                if os.path.exists("last_seen.json"):
                    with open("last_seen.json", "r", encoding="utf-8") as f:
                        seen_data = json.load(f)
                    last_seen = seen_data.get(sender)
                    if last_seen:
                        print("   - Last seen:", last_seen)

                if expiry and expiry != "None":
                    try:
                        seconds = int(expiry)
                        print(f"⏳ This message will self-destruct in {seconds} seconds...")
                        await asyncio.sleep(seconds)
                        print("💥 Message destroyed.")
                    except:
                        pass
                else:
                    log_received(username, sender, decrypted, private_key, public_key)
                    print("📩 Message saved.")

                    if should_backup():
                        create_auto_backup()

                    if message.startswith("@read::"):
                        reader = message.split("::")[1]
                        print(f"👀 Message read by {reader} (✅✅✨)")
                        return

            # 📨 Handle read/delivered receipts
            from user_send import handle_incoming_receipt
            if message.startswith("@read::") or message.startswith("@delivered::"):
                handle_incoming_receipt(message)
                return

            else:
                print(f"📨 Raw message received: {message}")

        except Exception as e:
            print("❌ Failed to decrypt or process:", e)

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    # 💾 Save offer to file
    with open(SIGNAL_FILE, "w") as f:
        json.dump({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}, f)
    print("📤 Offer saved to", SIGNAL_FILE)

    # 🔁 Wait for answer
    print("⏳ Waiting for answer... Paste into 'signal_answer.json'")
    while not os.path.exists("signal_answer.json"):
        await asyncio.sleep(1)

    with open("signal_answer.json", "r") as f:
        data = json.load(f)
        answer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
        await pc.setRemoteDescription(answer)

    print("✅ Connection established!")
    auto_share_dht(channel, username)

    # 🟢 Send pings to known contacts
    from contacts import load_contacts
    contacts = load_contacts()
    ping_contacts(channel, contacts, username)
    # ✅ Start presence monitor AFTER connection is set
    monitor_task = asyncio.create_task(monitor_presence())

    # 🔁 Send message loop
    while True:
        text = input("💬 Type message: ").strip()

        if text == "/blurcam":
            filepath = input("📷 Path to image (jpg/png): ").strip()
            recipient = input("👤 Send to: ").strip().lower()

            if not os.path.exists(filepath):
                print("❌ File not found.")
                continue

            blurred_path = blur_faces(filepath)
            if not blurred_path:
                print("❌ Failed to blur image.")
                continue

            with open(blurred_path, "rb") as f:
                data = f.read()

            if recipient not in public_keys:
                print(f"🔍 Requesting key from {recipient}...")
                channel.send(f"@request_key::{recipient}")
                for _ in range(10):
                    await asyncio.sleep(0.5)
                    if recipient in public_keys:
                        break
            if recipient not in public_keys:
                print("❌ Still no key.")
                continue

            from hashlib import sha256
            file_hash = sha256(data).hexdigest()
            from ecdh_encryption import encrypt_message

            encrypted = encrypt_message(private_key, public_keys[recipient], data.decode(errors="ignore"))
            filename = os.path.basename(blurred_path)
            payload = f"@file::{username}::{filename}::{file_hash}::None::{encrypted}"

            channel.send(payload)
            print(f"📤 Blurred image sent to {recipient}")
            continue

        if text.startswith("/schedule"):
            parts = text.split(" ", 2)
            if len(parts) < 3:
                print("❌ Usage: /schedule [username] [YYYY-MM-DD HH:MM]")
                continue
            recipient = parts[1]
            send_time = input("🕒 When to send? (YYYY-MM-DD HH:MM): ").strip()
            msg = input("💬 Message: ").strip()
            from user_send import schedule_message
            schedule_message(recipient, msg, send_time)
            continue

        if text.startswith("/pin "):
            msg = text.replace("/pin ", "").strip()
            recipient = input("👤 Pin this for which contact? ").strip().lower()
            set_pinned_for(recipient, msg)
            print("📌 Message pinned!")
            continue

        if text == "/unpin":
            recipient = input("👤 Unpin message for which contact? ").strip().lower()
            pins = get_pinned_for(recipient)

            if not pins:
                print("📭 No pinned messages.")
                continue
            for i, msg in enumerate(pins):
                print(f"{i + 1}. {msg}")
            idx = input("Which one to unpin? (number): ").strip()
            if idx.isdigit():
                removed = unpin_message(recipient, int(idx) - 1)
                if removed:
                    print(f"🗑️ Unpinned: {removed}")
                else:
                    print("❌ Invalid number.")
            continue

        # 🧠 Check if command
        from user_send import handle_command, extract_hashtags, save_tag, save_mention
        if handle_command(text):
            continue

        if text == "/panic":
            from user_send import panic_wipe  # ✅ moved inside
            panic_wipe(username)
            continue

        if text == "/sendfile":
            filepath = input("📁 Path to file: ").strip()
            recipient = input("👤 Send to: ").strip().lower()

            if not os.path.exists(filepath):
                print("❌ File not found.")
                continue

            if recipient not in public_keys:
                print(f"🔍 Requesting key from {recipient}...")
                channel.send(f"@request_key::{recipient}")
                for _ in range(10):
                    await asyncio.sleep(0.5)
                    if recipient in public_keys:
                        break
            if recipient not in public_keys:
                print("❌ Still no key.")
                continue

            with open(filepath, "rb") as f:
                data = f.read()

            from hashlib import sha256

            file_hash = sha256(data).hexdigest()
            encrypted = encrypt_message(private_key, public_keys[recipient], data.decode(errors="ignore"))
            filename = os.path.basename(filepath)
            payload = f"@file::{username}::{filename}::{file_hash}::{encrypted}"

            channel.send(payload)
            print(f"📤 File '{filename}' sent to {recipient}")
            continue

        if text == "/exit":
            print("👋 Closing...")
            break
        if text.startswith("/group"):
            sub = input("Group command (new/show/send): ").strip()

            if sub == "new":
                group_name = input("Group name: ").strip()
                members = input("Usernames (comma-separated): ").strip().split(",")
                members = [m.strip() for m in members if m.strip()]
                groups = load_groups()
                groups[group_name] = members
                save_groups(groups)
                print(f"✅ Group '{group_name}' saved with members: {members}")
                continue

            if sub == "show":
                groups = load_groups()
                for name, members in groups.items():
                    print(f"👥 {name}: {', '.join(members)}")
                continue

            if sub == "send":
                groups = load_groups()
                gname = input("Group name: ").strip()
                if gname not in groups:
                    print("❌ Group not found.")
                    continue
                message = input("💬 Group message: ").strip()

                for member in groups[gname]:
                    if member == username:
                        continue

                    from hashlib import sha256
                    from ecdh_encryption import sign_message

                    msg_hash = sha256(message.encode()).hexdigest()
                    encrypted = encrypt_message(private_key, public_keys.get(member, ""), message)
                    expiry = "None"
                    signature = sign_message(private_key, message)
                    payload = f"@msg::{username}::{msg_hash}::{expiry}::{encrypted}::{signature}"

                    if member not in public_keys:
                        print(f"📥 {member} is offline. Queuing group message.")
                        from user_send import queue_offline_message
                        queue_offline_message(member, payload)
                    else:
                        channel.send(payload)
                        print(f"📤 Sent to {member}")

                continue

        recipient = input("👤 Who do you want to send to? ").strip().lower()
        # 🟢 Optional: ping before send
        channel.send(f"@ping::{username}")

        # 🔑 Check for recipient key
        if recipient not in public_keys:
            print(f"🔍 Requesting public key from {recipient}...")
            channel.send(f"@request_key::{recipient}")

            # 🔁 Wait briefly for key to arrive
            for _ in range(10):
                await asyncio.sleep(0.5)
                if recipient in public_keys:
                    break

        from hashlib import sha256
        msg_hash = sha256(text.encode()).hexdigest()
        from user_send import update_message_status
        update_message_status(recipient, msg_hash, "sent")
        encrypted = encrypt_message(private_key, public_keys.get(recipient, ""), text)
        expiry = input("💣 Self-destruct after how many seconds? (or press Enter to keep forever): ").strip()
        expiry = expiry if expiry else "None"
        from ecdh_encryption import sign_message
        signature = sign_message(private_key, text)
        payload = f"@msg::{username}::{msg_hash}::{expiry}::{encrypted}::{signature}"

        if recipient not in public_keys:
            print("📥 Person still offline. Saving to queue.")
            from user_send import queue_offline_message
            queue_offline_message(recipient, payload)
            continue

        # 🔖 Save hashtags
        for tag in extract_hashtags(text):
            save_tag(tag, text)

        # 📣 Save mentions
        for word in text.split():
            if word.startswith("@") and len(word) > 1:
                mentioned = word[1:]
                save_mention(mentioned, text)

        channel.send(payload)
        print(f"📤 Sent encrypted message to {recipient} (expires in {expiry} seconds)")

    await pc.close()
