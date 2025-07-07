# airstrike/blue/detector.py

from scapy.all import sniff, Dot11, Dot11Deauth, Dot11Beacon
from datetime import datetime
import threading
import time
import sqlite3
import os

DB_PATH = "logs/airstrike.db"
TRUSTED_SSIDS = {"HomeNet", "Dsoky", "OfficeAP"}  # ← customize this list

# --- internal alert logger ---
def log_alert(alert_type, bssid, description, severity="Medium"):
    print(f"[!] Alert: {alert_type} | {bssid} | {severity} | {description}")
    if not os.path.exists("logs"):
        os.makedirs("logs")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS alerts (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     timestamp TEXT, type TEXT,
                     bssid TEXT, severity TEXT, details TEXT)''')
    cur.execute('''INSERT INTO alerts (timestamp, type, bssid, severity, details)
                   VALUES (?, ?, ?, ?, ?)''',
                (datetime.now().isoformat(), alert_type, bssid, severity, description))
    conn.commit()
    conn.close()

# --- detection logic ---
class WirelessDetector:
    def __init__(self):
        self.deauth_counts = {}   # BSSID → [timestamps]
        self.beacon_seen = {}     # ESSID → BSSIDs

    def sniff_packet(self, pkt):
        if pkt.haslayer(Dot11Deauth):
            self.handle_deauth(pkt)
        elif pkt.haslayer(Dot11Beacon):
            self.handle_beacon(pkt)

    def handle_deauth(self, pkt):
        bssid = pkt.addr2 or "Unknown"
        now = time.time()
        self.deauth_counts.setdefault(bssid, []).append(now)

        # Clean old entries (older than 10s)
        self.deauth_counts[bssid] = [t for t in self.deauth_counts[bssid] if now - t <= 10]

        if len(self.deauth_counts[bssid]) > 50:  # >50 deauths in 10s
            log_alert("Deauth Flood", bssid, f"High rate of deauth frames detected from {bssid}", "High")
            self.deauth_counts[bssid] = []  # reset so we don't spam logs

    def handle_beacon(self, pkt):
        essid = pkt.info.decode(errors='ignore') if pkt.info else "<Hidden>"
        bssid = pkt.addr2

        if essid in TRUSTED_SSIDS:
            if essid not in self.beacon_seen:
                self.beacon_seen[essid] = {bssid}
            elif bssid not in self.beacon_seen[essid]:
                log_alert("Rogue AP", bssid,
                          f"ESSID '{essid}' already exists with another BSSID: {bssid}", "High")
                self.beacon_seen[essid].add(bssid)

    def run(self, interface):
        print(f"[*] Starting Blue-Team detector on {interface}…")
        sniff(iface=interface, prn=self.sniff_packet, store=0)

# --- threaded launcher (for CLI/main tool) ---
def start_detector_in_background(interface):
    detector = WirelessDetector()
    thread = threading.Thread(target=detector.run, args=(interface,), daemon=True)
    thread.start()
    return thread
