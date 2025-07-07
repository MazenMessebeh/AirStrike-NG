import os
import re
import subprocess

def _run(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()

def scan_alive_hosts(_adapter=None):
    try:
        print("[*] Scanning for active hosts using nmap...")

        # Get all IPv4 addresses and their interfaces
        output = _run("ip -4 addr show")
        matches = re.findall(r'\d+: (\w+):.*?\n\s+inet (\d+\.\d+\.\d+\.\d+)/(\d+)', output)

        for iface, ip, mask in matches:
            if iface == "lo" or iface.endswith("mon"):
                continue  # Skip loopback and monitor interfaces

            base_ip = ".".join(ip.split(".")[:3]) + ".0/24"

            print(f"[i] Detected real interface: {iface} with IP {ip}")
            print(f"[i] Scanning subnet: {base_ip}\n")

            os.system(f"sudo nmap -sn {base_ip}")
            return  # Stop after first usable interface

        print("[-] No suitable network interface found with a real IP.")

    except Exception as e:
        print(f"[!] Error during scan: {e}")
