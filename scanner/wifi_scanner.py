import os
import subprocess
import re

def scan_networks(adapter):
    """Scans for nearby Wi-Fi networks and displays them in a structured format like WiFite."""
    print("\nScanning for networks...\n")

    # Run airodump-ng for a limited time and capture output
    command = f"sudo timeout 10 airodump-ng {adapter} --write /tmp/scan --output-format csv"
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    csv_file = "/tmp/scan-01.csv"
    networks = []

    try:
        with open(csv_file, "r") as file:
            lines = file.readlines()

        for line in lines[2:]:  # Skip headers
            fields = line.split(',')
            if len(fields) > 13:
                bssid = fields[0].strip()
                power = fields[8].strip()
                channel = fields[3].strip()
                encryption = fields[5].strip()
                wps = "yes" if "WPA" in encryption else "no"
                essid = fields[13].strip() or "<Hidden>"
                clients = fields[10].strip() if fields[10].strip().isdigit() else "0"

                index = len(networks) + 1
                networks.append((index, bssid, channel, essid, encryption, power, wps, clients))

        # Display network list like WiFite
        print("\n{:<4} {:<20} {:<4} {:<20} {:<8} {:<6} {:<4} {:<6}".format(
            "NUM", "BSSID", "CH", "ESSID", "ENCR", "PWR", "WPS", "CLIENT"))
        print("=" * 100)
        for net in networks:
            print("{:<4} {:<20} {:<4} {:<20} {:<8} {:<6} {:<4} {:<6}".format(*net))

    except FileNotFoundError:
        print("Error: No scan data found. Ensure your adapter is in monitor mode.")

    return networks


def choose_target(networks):
    """Allows the user to select a network by entering its number."""
    while True:
        try:
            choice = int(input("\nSelect target (1-{}): ".format(len(networks))))
            if 1 <= choice <= len(networks):
                return networks[choice - 1]
            else:
                print("Invalid selection. Choose a valid number.")
        except ValueError:
            print("Please enter a valid number.")
