# contacts.py – Persistent contact management
import json
import os

CONTACTS_FILE = "contacts.json"

def load_contacts():
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_contacts(contacts):
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=2)

def add_contact(username):
    contacts = load_contacts()
    if username not in contacts:
        contacts.append(username)
        save_contacts(contacts)

def remove_contact(username):
    contacts = load_contacts()
    if username in contacts:
        contacts.remove(username)
        save_contacts(contacts)

def request_presence(ws, contacts):
    for contact in contacts:
        ws.send(f"@presence_request::{contact}")


import json
import os

CONTACT_INFO_FILE = "contacts_info.json"

def save_contact_info(name, status, last_seen):
    data = {}
    if os.path.exists(CONTACT_INFO_FILE):
        with open(CONTACT_INFO_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                data = {}
    data[name] = {
        "status": status,
        "last_seen": last_seen
    }
    with open(CONTACT_INFO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_contact_info():
    if os.path.exists(CONTACT_INFO_FILE):
        try:
            with open(CONTACT_INFO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}
