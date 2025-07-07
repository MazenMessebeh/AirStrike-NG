import sys
import os
import random
import threading
import pyfiglet

try:
    import readline  # Enables arrow keys + history
except ImportError:
    print("[!] readline module not available. Install with: pip install readline")

from colorama import init as colorama_init, Fore, Style
colorama_init(autoreset=True)

from attacks import deauth, evil_twin, handshake_capture
from scanner import wifi_scanner as wifi
from scanner import host_scanner as host
from cracker import wpa_crack as cracker
from utils.helpers import get_wireless_adapters, refresh_adapter, clear_cache
from utils import log_viewer, mac_spoofer
from blue.detector import start_detector_in_background
from blue import log_analyzer_tool
from credentials import cli as credentials

# Banner
fonts = pyfiglet.FigletFont.getFonts()
random_font = random.choice(fonts)
ascii_art = pyfiglet.figlet_format("AirStrike", font=random_font)
ascii_art_colored = Fore.RED + ascii_art + Style.RESET_ALL

if os.geteuid() != 0:
    print(Fore.RED + "[!] This script must be run as root. Use sudo.")
    sys.exit(1)

# === Adapter Selection ===
def select_wireless_adapter():
    adapters = get_wireless_adapters()
    if not adapters:
        print(Fore.RED + "[!] No wireless adapters found.")
        return None
    print(Fore.CYAN + "\nAvailable Wireless Adapters:")
    for idx, ad in enumerate(adapters):
        print(Fore.YELLOW + f"{idx + 1}. {ad}")
    while True:
        try:
            idx = int(input(Fore.CYAN + "Select adapter number: ")) - 1
            if 0 <= idx < len(adapters):
                return refresh_adapter(adapters[idx])
            else:
                print(Fore.RED + "[!] Invalid selection.")
        except ValueError:
            print(Fore.RED + "[!] Enter a valid number.")

# === Menus ===
def main_menu():
    os.system("clear")
    print(ascii_art_colored)
    print(Fore.CYAN + Style.BRIGHT + """
	=== AirStrike: Wi-Fi Penetration Testing Toolkit ===
	""" + Fore.YELLOW + """    1. Wi-Fi Scan
	    2. Host Scan
	    3. Deauthentication Attack
	    4. Evil Twin Attacks ➤
	    5. WPA Handshake ➤
	    6. Blue-Team Defense ➤
	    7. MAC Spoofing ➤
	    8. Credentials Manager 🔐
	    9. Log Analyzer ➤
	    0. Exit
	""" + Style.RESET_ALL)
    while True:
        choice = input(Fore.CYAN + "Select an option: " + Style.RESET_ALL).strip()
        if choice in [str(i) for i in range(0, 11)]:
            return choice
        print(Fore.RED + "[!] Invalid option. Choose 0–10.")


def evil_twin_menu():
    adapter = select_wireless_adapter()
    if not adapter:
        input(Fore.CYAN + "[↩] Press Enter to return...")
        return

    while True:
        print(Fore.CYAN + Style.BRIGHT + """
=== Evil Twin Attacks ===
1. Start Evil Twin Attack
2. Stop Evil Twin Attack
3. Back to Main Menu
""" + Style.RESET_ALL)
        choice = input(Fore.CYAN + "Select an option: " + Style.RESET_ALL).strip()
        if choice == '1':
            evil_twin.evil_twin_attack(adapter)
            input(Fore.CYAN + "\n[↩] Press Enter to return...")
        elif choice == '2':
            evil_twin.stop_evil_twin()
            input(Fore.CYAN + "\n[↩] Press Enter to return...")
        elif choice == '3':
            break
        else:
            print(Fore.RED + "[!] Invalid choice.")

def wpa_handshake_menu():
    adapter = select_wireless_adapter()
    if not adapter:
        input(Fore.CYAN + "[↩] Press Enter to return...")
        return

    while True:
        print(Fore.CYAN + Style.BRIGHT + """
=== WPA Handshake Operations ===
1. Capture WPA Handshake
2. Crack Captured Handshake
3. Back to Main Menu
""" + Style.RESET_ALL)
        choice = input(Fore.CYAN + "Select an option: " + Style.RESET_ALL).strip()
        if choice == '1':
            handshake_capture.wpa_handshake_capture(adapter)
            input(Fore.CYAN + "\n[↩] Press Enter to return...")
        elif choice == '2':
            cracker.crack_handshake()
            input(Fore.CYAN + "\n[↩] Press Enter to return...")
        elif choice == '3':
            break
        else:
            print(Fore.RED + "[!] Invalid choice.")

def blue_team_menu(detector_started_flag):
    adapter = select_wireless_adapter()
    if not adapter:
        input(Fore.CYAN + "[↩] Press Enter to return...")
        return

    while True:
        print(Fore.CYAN + Style.BRIGHT + """
=== Blue-Team Defense ===
1. Start Blue-Team Detection
2. View Blue-Team Alerts
3. Clear Blue-Team Logs
4. Back to Main Menu
""" + Style.RESET_ALL)
        choice = input(Fore.CYAN + "Select an option: " + Style.RESET_ALL).strip()

        if choice == '1':
            print(Fore.YELLOW + """
1. Run in Background (Silent)
2. Run in Foreground (Visible Alerts)
3. Back
""")
            mode = input(Fore.CYAN + "Choose a mode: " + Style.RESET_ALL).strip()
            if mode == '1':
                if not detector_started_flag[0]:
                    start_detector_in_background(adapter)
                    detector_started_flag[0] = True
                    print(Fore.GREEN + "[✓] Detector started in background.")
                else:
                    print(Fore.YELLOW + "[i] Detector already running.")
                input(Fore.CYAN + "\n[↩] Press Enter to return...")
            elif mode == '2':
                from blue.detector import WirelessDetector
                from scapy.all import sniff

                print(Fore.YELLOW + "[*] Starting live Blue-Team detection (press Enter to stop)…")
                detector = WirelessDetector()
                stop_flag = threading.Event()

                def sniff_with_stop():
                    sniff(iface=adapter, prn=detector.sniff_packet, store=0,
                          stop_filter=lambda pkt: stop_flag.is_set())

                thread = threading.Thread(target=sniff_with_stop, daemon=True)
                thread.start()

                input(Fore.CYAN + "[↩] Press Enter to stop detection...\n")
                stop_flag.set()
                thread.join()
            elif mode == '3':
                continue
            else:
                print(Fore.RED + "[!] Invalid mode.")

        elif choice == '2':
            log_viewer.view_logs()
            input(Fore.CYAN + "\n[↩] Press Enter to return...")
        elif choice == '3':
            log_viewer.clear_logs()
            input(Fore.CYAN + "\n[↩] Press Enter to return...")
        elif choice == '4':
            break
        else:
            print(Fore.RED + "[!] Invalid option.")

def mac_spoofing_menu():
    adapters = get_wireless_adapters()
    if not adapters:
        print(Fore.RED + "[!] No wireless adapters found.")
        input(Fore.CYAN + "[↩] Press Enter to return...")
        return

    print(Fore.CYAN + "\nAvailable Wireless Adapters:")
    for idx, ad in enumerate(adapters):
        print(Fore.YELLOW + f"{idx + 1}. {ad}")
    while True:
        try:
            idx = int(input(Fore.CYAN + "Select adapter: ")) - 1
            if 0 <= idx < len(adapters):
                iface = adapters[idx]
                break
            else:
                print(Fore.RED + "[!] Invalid choice.")
        except ValueError:
            print(Fore.RED + "[!] Enter a valid number.")

    while True:
        print(Fore.CYAN + f"""
=== MAC Spoofing for {iface} ===
1. Randomize MAC
2. Set Custom MAC
3. Restore Original MAC
4. Show Current MAC
5. Back to Main Menu
""")
        choice = input(Fore.CYAN + "Choose an option: " + Style.RESET_ALL).strip()

        if choice == '1':
            mac_spoofer.randomize_mac(iface)
            input(Fore.CYAN + "[↩] Press Enter to continue...")
        elif choice == '2':
            custom = input(Fore.CYAN + "Enter custom MAC address (format: XX:XX:XX:XX:XX:XX): ").strip()
            mac_spoofer.set_custom_mac(iface, custom)
            input(Fore.CYAN + "[↩] Press Enter to continue...")
        elif choice == '3':
            mac_spoofer.restore_mac(iface)
            input(Fore.CYAN + "[↩] Press Enter to continue...")
        elif choice == '4':
            mac = mac_spoofer.get_current_mac(iface)
            print(Fore.GREEN + f"[i] Current MAC: {mac}" if mac else Fore.RED + "[!] Unable to retrieve MAC.")
            input(Fore.CYAN + "[↩] Press Enter to continue...")
        elif choice == '5':
            break
        else:
            print(Fore.RED + "[!] Invalid option.")

# === Main ===
def main():
    detector_started_flag = [False]  # shared state for background detection

    while True:
        choice = main_menu()

        if choice == '1':
            adapter = select_wireless_adapter()
            if adapter:
                networks = wifi.scan_networks(adapter)
                if networks:
                    selected = wifi.choose_target(networks)
                    print(Fore.GREEN + f"\n[✓] Selected: {selected[1]} (CH: {selected[2]}, ESSID: {selected[3]})")
            input("\n[↩] Press Enter to return...")

        elif choice == '2':
            adapters = get_wireless_adapters() + ["eth0"]
            if not adapters:
                print(Fore.RED + "[!] No adapters available.")
                input("[↩] Press Enter to return...")
                continue

            print("\nAvailable Adapters for Host Scanning:")
            for idx, ad in enumerate(adapters):
                print(f"{idx + 1}. {ad}")
            while True:
                try:
                    idx = int(input("Choose adapter: ")) - 1
                    if 0 <= idx < len(adapters):
                        scan_adapter = adapters[idx]
                        break
                    else:
                        print(Fore.RED + "[!] Invalid choice.")
                except ValueError:
                    print(Fore.RED + "[!] Enter a valid number.")

            if "mon" in scan_adapter:
                print(Fore.RED + "[x] Monitor mode adapter cannot perform host scan (no IP).")
            else:
                host.scan_alive_hosts(scan_adapter)
            input("\n[↩] Press Enter to return...")

        elif choice == '3':
            adapter = select_wireless_adapter()
            if adapter:
                deauth.deauth_attack(adapter)
            input("\n[↩] Press Enter to return...")

       

        elif choice == '4':
            evil_twin_menu()

        elif choice == '5':
            wpa_handshake_menu()

        elif choice == '6':
            blue_team_menu(detector_started_flag)

        elif choice == '7':
            mac_spoofing_menu()

        
        elif choice == '8':
            credentials.init()
            credentials.menu()
            input("\n[↩] Press Enter to return...")

        elif choice == '9':
            log_analyzer_tool.run_tool()
            input("\n[↩] Press Enter to return...")

        elif choice == '0':
            print("[!] Exiting and cleaning cache...")
            clear_cache()
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)
