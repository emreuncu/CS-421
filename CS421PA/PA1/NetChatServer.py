from http.server import BaseHTTPRequestHandler, HTTPServer
import re
from typing import List
from urllib.parse import urlparse, parse_qs

class NetChatServer(BaseHTTPRequestHandler):
    # Class-level dictionary to store all users
    users: dict = {}
    
    def __init__(self, *args, **kwargs):
        # Initialize the server's user tracking
        if not hasattr(self.__class__, 'initialized'):
            self.__class__.users = {}
            self.__class__.initialized = True
        super().__init__(*args, **kwargs)

    def do_GET(self):
        
        print(f"Path: {self.path}")
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        if parsed_url.path == "/userlist.txt":
            
            if not query_params:
            
                response = self.form_user_list()
                print(f"User list sent: {response}")
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response.encode())

            else:

                username = query_params.get("username", [None])[0]
                if username and username in self.users:
                    ip = self.users[username]
                    ip_address = ip['ip'] + ":" + ip['port']
                    self.send_response(200)
                    self.send_header("Content-type", "text/plain")
                    self.send_header("Content-Length", str(len(ip_address)))
                    self.end_headers()
                    self.wfile.write(ip_address.encode())
                    print(f"Sent IP for {username}: {ip_address}")
                else:
                    error_msg = "User not found"
                    self.send_response(404)
                    self.send_header("Content-type", "text/plain")
                    self.send_header("Content-Length", str(len(error_msg)))
                    self.end_headers()
                    self.wfile.write(error_msg.encode())
                    print(f"User {username} not found")

        
            
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode()

        command = post_data.split(" ")[0]

        if command == "UPDATE" and self.check_register(post_data):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
        else:
            self.send_response(400)
            self.end_headers()

    def form_user_list(self) -> str:
        return ''.join(f"{username}@{data['ip']}:{data['port']}\n" 
                      for username, data in self.users.items())

    def check_register(self, command: str) -> bool:
        parts = command.split(" ")
        if len(parts) != 2:
            print(f"Invalid command: {command}")
            return False

        user_info = parts[1].split("@")
        if len(user_info) != 2:
            print("Format error")
            return False

        username = user_info[0]
        if username in self.users:
            print("Username already exists")
            return False

        if ":" in username:
            print("Format error")
            return False

        address_info = user_info[1].split(":")
        if len(address_info) != 2:
            print("Address format error")
            return False

        ip, port = address_info
        if not self.valid_ip(ip):
            print(f"Invalid or empty IP: {ip}")
            return False

        if not port:
            print("Empty port")
            return False

        # Check if IP:port combination already exists
        for existing_user in self.users.values():
            if existing_user['ip'] == ip and existing_user['port'] == port:
                print("IP-port pair already exists")
                return False

        # Store user data in dictionary
        self.users[username] = {'ip': ip, 'port': port}
        
        print(f"Username: {username}")
        print(f"User IP:  {ip}")
        print(f"User Port: {port}")
        
        return True

    @staticmethod
    def valid_ip(ip: str) -> bool:
        pattern = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
        return bool(pattern.match(ip)) and all(0 <= int(part) <= 255 for part in ip.split("."))


def run(handler_class=NetChatServer, port=80):
    server_address = ("", port)
    httpd = HTTPServer(server_address, handler_class)
    print(f"Server started on port {port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run()