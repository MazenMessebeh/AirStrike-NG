# credentials/vault_manager.py

import json
import os
from datetime import datetime
from .crypto import encrypt_data, decrypt_data

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
VAULT_FILE = os.path.join(DATA_DIR, 'vault.json')

def load_vault():
    if not os.path.exists(VAULT_FILE):
        return []
    with open(VAULT_FILE, 'r') as f:
        return json.load(f)

def save_vault(vault):
    with open(VAULT_FILE, 'w') as f:
        json.dump(vault, f, indent=2)

def add_credential(ssid, username, password, notes=""):
    encrypted_password = encrypt_data(password)
    vault = load_vault()
    vault.append({
        "ssid": ssid,
        "username": username,
        "password": encrypted_password,
        "notes": notes,
        "timestamp": datetime.now().isoformat()
    })
    save_vault(vault)

def list_credentials():
    vault = load_vault()
    for idx, entry in enumerate(vault):
        print(f"[{idx}] SSID: {entry['ssid']} | User: {entry['username']} | Notes: {entry.get('notes', '')} | Time: {entry['timestamp']}")

def view_credential(index):
    vault = load_vault()
    entry = vault[index]
    password = decrypt_data(entry['password'])
    print(f"\nSSID: {entry['ssid']}\nUser: {entry['username']}\nPassword: {password}\nNotes: {entry.get('notes', '')}\nTime: {entry['timestamp']}")

def delete_credential(index):
    vault = load_vault()
    if index < 0 or index >= len(vault):
        print("Invalid index.")
        return
    removed = vault.pop(index)
    save_vault(vault)
    print(f"Deleted entry: SSID = {removed['ssid']}")
