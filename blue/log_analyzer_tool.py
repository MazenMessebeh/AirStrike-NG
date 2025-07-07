# log_analyzer_tool.py
# FULL CODE UPDATED - LOOP, LAZY LOG INPUT, DARK MODE, NON-EXITING

import re
import os
import shutil
import webbrowser
from collections import Counter
import matplotlib.pyplot as plt

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Pattern/Severity/Remediation
EVENT_PATTERNS = {
    "Associations": (r"associated", "Normal behavior, no action needed.", "Low"),
    "DHCP Assignments": (r"DHCPACK", "Ensure IP pool is managed to avoid exhaustion.", "Low"),
    "Deauthentications": (r"deauthenticated", "Investigate if frequent; could indicate spoofing/deauth attack.", "Medium"),
    "Handshakes": (r"group key handshake completed", "Ensure WPA2/WPA3 is in use; normal if not excessive.", "Low"),
    "Admin Logins": (r"User '.*' logged in", "Verify login sources; enforce strong passwords.", "Medium"),
    "Blocked Ports": (r"Blocked connection attempt", "Review firewall rules and block unneeded services.", "Medium"),
    "ICMP Blocks": (r"UFW BLOCK.*ICMP", "Possible scanning attempt; consider rate-limiting ICMP.", "Medium"),
    "Deauth Floods": (r"Possible deauth flood detected", "Alert! Deauthentication attack possible. Investigate source.", "High"),
    "Disconnections": (r"disconnected", "Normal unless frequent. Could indicate instability or attacks.", "Low"),
    "CPU Spikes": (r"CPU load spike detected", "Investigate running processes or hardware issues.", "Medium"),
    "Cron Jobs": (r"Executed scheduled job", "Expected behavior if configured properly.", "Low"),
}

SEVERITY_COLORS = {"High": (255, 100, 100), "Medium": (255, 200, 100), "Low": (200, 255, 200)}
HTML_SEVERITY_COLORS = {"High": "#ff6464", "Medium": "#ffc864", "Low": "#c8ffc8"}

def get_event_impact(event):
    return {
        "Associations": "Tracks device connections. Harmless unless suspicious.",
        "DHCP Assignments": "IP exhaustion can block new connections.",
        "Deauthentications": "May indicate jamming or spoofing attack.",
        "Handshakes": "Could mean password cracking attempts.",
        "Admin Logins": "Compromised admin can reconfigure router.",
        "Blocked Ports": "Port scanning or recon attempts.",
        "ICMP Blocks": "Recon tools like ping/trace.",
        "Deauth Floods": "Critical: disconnects all users.",
        "Disconnections": "Can be instability or forced disconnects.",
        "CPU Spikes": "Could be attack or resource exhaustion.",
        "Cron Jobs": "Used by attackers for persistence.",
    }.get(event, "No specific impact available.")

def parse_logs(path):
    event_counts = Counter()
    source_ips = Counter()
    with open(path, "r") as f:
        for line in f:
            if (ip := re.search(r"SRC=(\d+\.\d+\.\d+\.\d+)", line)):
                source_ips[ip.group(1)] += 1
            for event, (pattern, _, _) in EVENT_PATTERNS.items():
                if re.search(pattern, line):
                    event_counts[event] += 1
    return event_counts, source_ips

def generate_summary_html(event_counts, source_ips, output_html):
    details_dir = os.path.join(os.path.dirname(output_html), "event_details")
    os.makedirs(details_dir, exist_ok=True)

    with open(output_html, "w") as f:
        f.write("""<html><head><title>Router Log Report</title>
<style>
body { font-family: Arial; transition: background 0.3s, color 0.3s; }
.dark-mode { background-color: #111; color: #eee; }
.dark-mode table, .dark-mode th, .dark-mode td { border-color: #555; }
.dark-mode th { background-color: #333; }
table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid #ccc; padding: 10px; text-align: center; }
th { background-color: #eee; }
.toggle { float: right; margin: 10px; }
</style>
<script>
function toggleDarkMode() { document.body.classList.toggle('dark-mode'); }
</script></head><body>
<button class='toggle' onclick='toggleDarkMode()'>🌙 Toggle Dark Mode</button>
<h2>Router Log Summary Report</h2>
<table><tr><th>Event</th><th>Count</th><th>Severity</th><th>Details</th></tr>""")

        for event, count in event_counts.items():
            remediation, severity = EVENT_PATTERNS[event][1:]
            color = HTML_SEVERITY_COLORS.get(severity, "#fff")
            safe_event = event.replace(" ", "_").lower()
            detail_file = os.path.join(details_dir, f"{safe_event}.html")

            with open(detail_file, "w") as df:
                df.write(f"""<html><body><h2>{event}</h2>
<p><b>Severity:</b> {severity}</p>
<p><b>Remediation:</b> {remediation}</p>
<p><b>Wi-Fi Impact:</b> {get_event_impact(event)}</p>
<p><a href='../log_summary.html'>⬅ Back to Report</a></p></body></html>""")

            f.write(f"<tr style='background:{color}'><td>{event}</td><td>{count}</td><td>{severity}</td><td><a href='event_details/{safe_event}.html' target='_blank'>View</a></td></tr>")

        f.write("</table>")

        if source_ips:
            ip, pkts = source_ips.most_common(1)[0]
            f.write(f"<h3>Top Talker</h3><p>IP: {ip}<br>Packets: {pkts}</p>")

        f.write("</body></html>")
    print(f"HTML saved: {output_html}")
    webbrowser.open(f"file://{os.path.abspath(output_html)}")

def generate_chart(event_counts, output_png):
    plt.figure(figsize=(12, 6))
    plt.bar(event_counts.keys(), event_counts.values(), color='skyblue')
    plt.xticks(rotation=45, ha='right')
    plt.title("Router Log Event Summary")
    plt.tight_layout()
    plt.savefig(output_png)
    print(f"Chart saved: {output_png}")
    webbrowser.open(f"file://{os.path.abspath(output_png)}")

def clear_summaries():
    for f in ["log_summary.pdf", "log_summary.html", "log_summary_chart.png"]:
        full_path = os.path.join(DATA_DIR, f)
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"Deleted {f}")
    details_path = os.path.join(DATA_DIR, "event_details")
    if os.path.exists(details_path):
        shutil.rmtree(details_path)
        print("Deleted event_details/")
    print("✔ All reports cleared.\n")

# Exposed function to run from AirStrike main menu
def run_tool():
    print("\n=== Log Analyzer Tool ===")
    while True:
        log_file_path = input("\nEnter path to log file (or 'exit' to quit): ").strip()
        if log_file_path.lower() == "exit":
            print("Exiting log analyzer. Goodbye!")
            break

        if not os.path.isfile(log_file_path):
            print("❌ File not found. Please try again.")
            continue

        print("\nChoose an action:")
        print("1 - Generate HTML Report")
        print("2 - Clear All Summary Reports")
        print("3 - Exit")
        choice = input("Enter your choice (1, 2, or 3): ").strip()

        if choice == "3":
            print("Exiting log analyzer. Goodbye!")
            break
        elif choice == "2":
            clear_summaries()
        elif choice == "1":
            event_counts, source_ips = parse_logs(log_file_path)
            output_html_path = os.path.join(DATA_DIR, "log_summary.html")
            generate_summary_html(event_counts, source_ips, output_html_path)
            output_png = os.path.join(DATA_DIR, "log_summary_chart.png")
            generate_chart(event_counts, output_png)
        else:
            print("Invalid choice. Returning to log file input.")

        input("\nPress Enter to analyze another log or type 'exit' next time to quit...")
