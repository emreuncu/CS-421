import socket
import threading
import sys

class NetChatClient:
    def __init__(self, username):
        self.username = username
        self.ip = self.get_ip()
        self.port = self.get_port()
        self.known_users = {}
        self.message_history = {}
        self.server_host = 'localhost'
        self.server_port = 80
    
    def get_ip(self):
        return socket.gethostbyname(socket.gethostname())

    def get_port(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("localhost", 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def register(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.server_host, self.server_port))

        data = f"UPDATE {self.username}@{self.ip}:{self.port}"
        
        request = "POST / HTTP/1.1\r\n"
        request += f"Host: {self.server_host}\r\n"
        request += "Connection: close\r\n"
        request += f"Content-Length: {len(data)}\r\n"
        request += "\r\n"
        request += data
        
        s.sendall(request.encode())
        
        resps = []
        while True:
            resp = s.recv(4096)
            if not resp:
                break
            resps.append(resp)
        
        s.close()
        response = b''.join(resps).decode()
                
        headers, _ = response.split("\r\n\r\n", 1)
        status_line = headers.split("\r\n")[0]
        status_code = int(status_line.split()[1])

        if status_code == 200:
            print(">>User registered in server!")
        else:
            print(">>Registration failed!")

    def get_user_list(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.server_host, self.server_port))
        
        request = "GET /userlist.txt HTTP/1.1\r\n"
        request += f"Host: {self.server_host}\r\n"
        request += "Connection: close\r\n"
        request += "\r\n"

        s.sendall(request.encode())
        
        resps = []
        while True:
            resp = s.recv(4096)
            if not resp:
                break
            resps.append(resp)
        
        s.close()
        response = b''.join(resps).decode()
        
        headers, content = response.split("\r\n\r\n", 1)
        status_line = headers.split("\r\n")[0]
        status_code = int(status_line.split()[1])
        content = content.strip()

        if status_code == 200:
            user_list = content.split("\n")
            for user in user_list:
                if user:
                    username, address = user.split("@")
                    self.known_users[username] = address
        else:
            print(">>Failed to get user list!")

    def get_user_info(self, username):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.server_host, self.server_port))
        
        request = f"GET /userlist.txt?username={username} HTTP/1.1\r\n"
        request += f"Host: {self.server_host}\r\n"
        request += "Connection: close\r\n"
        request += "\r\n"

        s.sendall(request.encode())
        
        resps = []
        while True:
            resp = s.recv(4096)
            if not resp:
                break
            resps.append(resp)
        
        s.close()
        response = b''.join(resps).decode()
        
        headers, content = response.split("\r\n\r\n", 1)
        status_line = headers.split("\r\n")[0]
        status_code = int(status_line.split()[1])
        content = content.strip()

        if status_code == 200:
            ip_port = content
            self.known_users[username] = ip_port
        else:
            print(f">>User {username} not found!")
        
    def send_message(self, recipient, message):
        if recipient not in self.known_users:
            self.get_user_info(recipient)
        if recipient in self.known_users:
            ip, port = self.known_users[recipient].split(":")
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((ip, int(port)))
                s.sendall(f"{self.username}: {message}".encode())
                s.close()
                
                if recipient not in self.message_history:
                    self.message_history[recipient] = []
                self.message_history[recipient].append(f"{message.split('"')[1]} - user")
            except Exception as e:
                print(f">>Failed to send message: {e}")
        else:
            print(">>User not found!")

    def delete_message(self, recipient):
        if recipient in self.message_history and self.message_history[recipient]:
            messages = self.message_history[recipient]
            for i in range(len(messages)-1, -1, -1):
                if messages[i].endswith("- user") and not messages[i] == "Deleted - user":
                    messages[i] = "Deleted - user"
                    if recipient in self.known_users:
                        try:
                            ip, port = self.known_users[recipient].split(":")
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.connect((ip, int(port)))
                            delete_signal = f"DELETE_MESSAGE:{self.username}"
                            s.sendall(delete_signal.encode())
                            s.close()
                            # print(">>Message deleted!")
                            if recipient in self.message_history:
                                for msg in self.message_history[recipient]:
                                    print(f">>{msg}")
                            else:
                                print(">>No messages found!")
                            break
                        except Exception as e:
                            print(f">>Failed to send delete notification: {e}")
            else:
                print(">>No messages to delete!")
        else:
            print(">>No messages to delete!")

    def listen_for_messages(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.ip, self.port))
        s.listen()
        while True:
            conn, addr = s.accept()
            data = conn.recv(1024)
            if data:
                message = data.decode()
                if message.startswith("DELETE_MESSAGE:"):
                    sender = message.split(":")[1]
                    if sender in self.message_history:
                        messages = self.message_history[sender]
                        for i in range(len(messages)-1, -1, -1):
                            if messages[i].endswith(f"- {sender}") and not messages[i] == f"Deleted - {sender}":
                                messages[i] = f"Deleted - {sender}"
                                break
                else:
                    sender = message.split(":")[0]
                    if sender not in self.message_history:
                        self.message_history[sender] = []
                    self.message_history[sender].append(f"{message.split('"')[1]} - {sender}")
                    print(f"\n\r\033[K>>You have a message from {sender}", end="")
                    print("\nWaiting for a command (to exit write EXIT): ", end="")
            conn.close()
        s.close()

    def start(self):
        self.register()
        self.get_user_list()
        threading.Thread(target=self.listen_for_messages, daemon=True).start()
        while True:
            command = input("Waiting for a command (to exit write EXIT): ")
            if command == "EXIT":
                break
            elif command.startswith("LIST"):  # LIST
                parts = command.split(" ")
                if len(parts) == 1:
                    self.get_user_list()
                    print(f">>[{', '.join(self.known_users.keys())}]")
                else:
                    print(">>Invalid LIST command!")
            elif command.startswith("SEND_MULTI"): # SEND_MULTI [user1,user2,...] "message"
                parts = command.split(" ")
                if len(parts) >= 3:
                    recipients = parts[1].strip("[]").split(",")
                    message = " ".join(parts[2:])
                    successful_sends = []
                    failed_sends = []
                    
                    for recipient in recipients:
                        recipient = recipient.strip()
                        if recipient not in self.known_users:
                            self.get_user_list()
                        
                        if recipient in self.known_users:
                            self.send_message(recipient, message)
                            successful_sends.append(recipient)
                        else:
                            failed_sends.append(recipient)
                    
                    if failed_sends:
                        print(f">> Error: Message cannot be sent to {', '.join(failed_sends)}, user does not exist")
                    elif successful_sends:
                        print(">>Message sent!")
                else:
                    print(">>Invalid SEND_MULTI command!")
            elif command.startswith("SEND"):  # SEND user "message"
                parts = command.split(" ")
                if len(parts) >= 3:
                    recipient = parts[1]
                    message = " ".join(parts[2:])
                    self.send_message(recipient, message)
                    print(">>Message sent!")
                else:
                    print(">>Invalid SEND command!")
            elif command.startswith("READ"):  # READ user
                parts = command.split(" ")
                if len(parts) == 2:
                    user = parts[1]
                    if user in self.message_history:
                        for msg in self.message_history[user]:
                            print(f">>{msg}")
                    else:
                        print(">>No messages found!")
                else:
                    print("Invalid READ command!")
            elif command.startswith("DELETE"):  # DELETE user
                parts = command.split(" ")
                if len(parts) == 2:
                    user = parts[1]
                    self.delete_message(user)
                else:
                    print(">>Invalid DELETE command!")
            else:
                print(">>Unknown command!")

if __name__ == "__main__":
    username = sys.argv[1]
    # ip = input("Enter your IP address: ")
    # port = int(input("Enter your port number: "))
    client = NetChatClient(username)
    client.start()