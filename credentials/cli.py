from .vault_manager import add_credential, list_credentials, view_credential, delete_credential
from .crypto import generate_key
from .auth import verify_master_password
import os
import string
import secrets
from colorama import init as colorama_init, Fore, Style

colorama_init(autoreset=True)

def init():
    if not os.path.exists(os.path.join(os.path.dirname(_file_), "data", "master.key")):
        print(Fore.YELLOW + "🔑 Generating encryption key...")
        generate_key()

    if not verify_master_password():
        exit()

def generate_secure_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = ''.join(secrets.choice(characters) for _ in range(length))
        if (any(c.isdigit() for c in password) and
            any(c in string.punctuation for c in password)):
            return password

def is_valid_password(password):
    if (len(password) >= 12 and
        any(c.isdigit() for c in password) and
        any(c in string.punctuation for c in password)):
        return True
    return False

def menu():
    while True:
        print(Fore.CYAN + "\n=== Credential Vault Menu ===")
        print(Fore.GREEN + "[1]" + Fore.WHITE + " Add Credential (Manual Password Entry)")
        print(Fore.GREEN + "[2]" + Fore.WHITE + " Add Credential (Random Password Generation)")
        print(Fore.GREEN + "[3]" + Fore.WHITE + " List Credentials")
        print(Fore.GREEN + "[4]" + Fore.WHITE + " View Credential")
        print(Fore.GREEN + "[5]" + Fore.WHITE + " Delete Credential")
        print(Fore.RED   + "[6]" + Fore.WHITE + " Exit")

        choice = input(Fore.YELLOW + "Select an option: ").strip()

        if choice == '1':
            ssid = input("SSID: ")
            username = input("Username: ")

            while True:
                password = input("Password (min 12 chars, include number + special char): ")
                if is_valid_password(password):
                    break
                print(Fore.RED + "⚠️ Password too weak. Try again.")

            add_credential(ssid, username, password)
            print(Fore.GREEN + "✅ Credential added.")

        elif choice == '2':
            ssid = input("SSID: ")
            username = input("Username: ")
            password = generate_secure_password()
            print(Fore.MAGENTA + f"🔐 Generated password: {password}")
            add_credential(ssid, username, password)
            print(Fore.GREEN + "✅ Credential added with random password.")

        elif choice == '3':
            list_credentials()

        elif choice == '4':
            try:
                index = int(input("Index of credential: "))
                view_credential(index)
            except Exception:
                print(Fore.RED + "⚠️ Invalid index.")

        elif choice == '5':
            try:
                index = int(input("Index to delete: "))
                delete_credential(index)
            except Exception:
                print(Fore.RED + "⚠️ Invalid index.")

        elif choice == '6':
            print(Fore.BLUE + "🔒 Vault locked. Returning to AirStrike...")
            break
        else:
            print(Fore.RED + "❌ Invalid choice.")

if __name__ == "__main__":
    init()
    menu()
