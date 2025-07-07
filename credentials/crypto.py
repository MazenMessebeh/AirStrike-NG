# credentials/crypto.py

from cryptography.fernet import Fernet
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
KEY_FILE = os.path.join(DATA_DIR, 'master.key')

def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as f:
        f.write(key)

def load_key():
    with open(KEY_FILE, 'rb') as f:
        return f.read()

def encrypt_data(data: str) -> str:
    fernet = Fernet(load_key())
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(token: str) -> str:
    fernet = Fernet(load_key())
    return fernet.decrypt(token.encode()).decode()
