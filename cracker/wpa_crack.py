# attacks/wpa_crack.py

import os
import glob
import subprocess

HANDSHAKE_DIR = "data/handshakes"

def list_handshake_files():
    """Return a list of .cap files from the handshakes directory."""
    return glob.glob(f"{HANDSHAKE_DIR}/*.cap")

def choose_file(files):
    """Display files and let user pick one."""
    print("\nAvailable handshake files:")
    for i, file in enumerate(files, 1):
        print(f"{i}. {os.path.basename(file)}")

    while True:
        try:
            choice = int(input("Select file number: "))
            if 1 <= choice <= len(files):
                return files[choice - 1]
            else:
                print("Invalid selection.")
        except ValueError:
            print("Enter a valid number.")

def crack_handshake():
    files = list_handshake_files()

    if not files:
        print("[-] No handshake files found in data/handshakes/")
        return

    selected_file = choose_file(files)

    default_wordlist = "/usr/share/wordlists/rockyou.txt"
    use_default = input(f"Use default wordlist? ({default_wordlist}) [Y/n]: ").strip().lower()

    if use_default in ["n", "no"]:
        wordlist = input("Enter full path to your wordlist: ").strip()
    else:
        wordlist = default_wordlist

    print(f"\n[+] Cracking WPA handshake: {os.path.basename(selected_file)}")
    print(f"[+] Using wordlist: {wordlist}\n")

    subprocess.run(f"sudo aircrack-ng -w {wordlist} {selected_file}", shell=True)
