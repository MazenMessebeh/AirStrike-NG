# credentials/auth.py

import os
import bcrypt
import getpass

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
PASSWORD_FILE = os.path.join(DATA_DIR, 'vault.pass')

def setup_master_password():
    print("🔐 First-time setup: Create a master password.")
    while True:
        password = getpass.getpass("Enter new master password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password == confirm:
            break
        print("Passwords do not match. Try again.")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    with open(PASSWORD_FILE, 'wb') as f:
        f.write(hashed)
    print("✅ Master password set successfully.")

def verify_master_password():
    if not os.path.exists(PASSWORD_FILE):
        setup_master_password()
        return True

    with open(PASSWORD_FILE, 'rb') as f:
        stored_hash = f.read()

    for attempt in range(3):
        password = getpass.getpass("Enter master password: ")
        if bcrypt.checkpw(password.encode(), stored_hash):
            print("✅ Access granted.")
            return True
        else:
            print("❌ Incorrect password.")
    print("🚫 Too many failed attempts. Exiting.")
    return False
