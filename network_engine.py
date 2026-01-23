import platform
import subprocess
import socket
import threading
import time
import re
import os
import requests
import psutil
from datetime import datetime

try:
    from scapy.all import ARP, Ether, srp
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

class NetworkEngine:
    def __init__(self):
        self.lock = threading.Lock()
        self.mac_vendor_cache = {}
        # STATISTICS
        self.start_time = datetime.now()
        self.total_pings = 0
        self.failed_pings = 0
        self.incidents = []

    def log_incident(self, target_name):
        self.incidents.append({
            "target": target_name,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    def get_statistics(self):
        duration = datetime.now() - self.start_time
        hours = duration.total_seconds() / 3600
        uptime = 100.0
        if self.total_pings > 0:
            uptime = ((self.total_pings - self.failed_pings) / self.total_pings) * 100
        
        return {
            "uptime": f"{uptime:.2f}%",
            "incidents": len(self.incidents),
            "incident_log": self.incidents[-5:], # Last 5
            "duration": f"{hours:.1f} hours"
        }

    def get_server_health(self):
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        return {
            "cpu": f"{cpu}%",
            "ram_used": f"{memory.used / (1024**3):.2f} GB",
            "ram_total": f"{memory.total / (1024**3):.2f} GB",
            "ram_percent": f"{memory.percent}%"
        }

    def scan_vulnerabilities(self, ip):
        dangerous_ports = {
            21: "FTP (Unencrypted)", 23: "Telnet (Unsecure)", 
            3389: "RDP (Remote Desktop)", 445: "SMB (File Share)", 80: "HTTP (No SSL)"
        }
        open_vulns = []
        score = 100 
        
        for port, desc in dangerous_ports.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                if sock.connect_ex((ip, port)) == 0:
                    open_vulns.append({"port": port, "issue": desc})
                    score -= 20
                sock.close()
            except: pass
            
        if score < 0: score = 0
        grade = "A"
        if score < 90: grade = "B"
        if score < 70: grade = "C"
        if score < 50: grade = "D"
        if score < 30: grade = "F"
        
        return {"ip": ip, "score": score, "grade": grade, "vulnerabilities": open_vulns}

    def ping_host(self, host):
        self.total_pings += 1
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', host]
        try:
            if platform.system().lower() == 'windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                output = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
            else:
                output = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            success = (output.returncode == 0)
            if not success: self.failed_pings += 1
            return success
        except Exception:
            self.failed_pings += 1
            return False

    def get_mac_vendor(self, mac):
        if not mac: return "Unknown"
        mac_clean = mac.replace(':', '').replace('-', '').upper()
        if len(mac_clean) < 6: return "Invalid MAC"
        if mac_clean[:6] in self.mac_vendor_cache: return self.mac_vendor_cache[mac_clean[:6]]
        
        # Fake vendor for demo if offline (Optimization: Removed online check to prevent timeout)
        if mac_clean.startswith("005056"): return "VMware"
        if mac_clean.startswith("B827EB"): return "Raspberry Pi"
        
        return "Unknown Vendor"
        # try:
        #     url = f"https://macvendors.co/api/{mac}"
        #     response = requests.get(url, timeout=0.5)
        #     if response.status_code == 200:
        #         data = response.json()
        #         vendor = data.get('result', {}).get('company', 'Unknown Vendor')
        #         self.mac_vendor_cache[mac_clean[:6]] = vendor
        #         return vendor
        # except Exception: pass
        # return "Unknown Vendor"

    def scan_ports(self, ip):
        common_ports = {21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP", 443: "HTTPS", 3389: "RDP"}
        open_ports = []
        for port, service in common_ports.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                if sock.connect_ex((ip, port)) == 0:
                    open_ports.append({"port": port, "service": service, "status": "Open"})
            except: pass
            finally: sock.close()
        return open_ports

    def get_connected_devices(self, ip_range="192.168.1.1/24"):
        devices = []
        # Try system ARP first as it is faster and safer
        try:
            output = subprocess.check_output("arp -a", shell=True).decode()
            entries = re.findall(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:-]{17})', output)
            for ip, mac in entries:
                if "255" not in ip: # Filter broadcast
                    vendor = self.get_mac_vendor(mac)
                    devices.append({'ip': ip, 'mac': mac, 'vendor': vendor})
        except Exception: pass
        return devices

    def wake_on_lan(self, mac_address):
        if len(mac_address) == 12: pass
        elif len(mac_address) == 17:
             sep = mac_address[2]
             mac_address = mac_address.replace(sep, '')
        else: return "Invalid MAC Address"
        data = b'FFFFFFFFFFFF' + (bytes.fromhex(mac_address) * 16)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(data, ('<broadcast>', 9))
        sock.close()
        return "Magic Packet Sent!"

    def run_traceroute(self, host):
        cmd = "tracert" if platform.system().lower() == "windows" else "traceroute"
        try:
            output = subprocess.check_output([cmd, "-h", "15", host], timeout=20).decode()
            return output
        except subprocess.TimeoutExpired: return "Traceroute timeout."
        except Exception as e: return str(e)
            
    def measure_speed(self):
        try:
            import speedtest
            st = speedtest.Speedtest()
            st.get_best_server()
            download = st.download() / 1_000_000
            upload = st.upload() / 1_000_000
            return {"download": f"{download:.2f} Mbps", "upload": f"{upload:.2f} Mbps", "ping": f"{st.results.ping} ms"}
        except ImportError: return {"error": "speedtest-cli not installed"}
        except Exception as e: return {"error": str(e)}
