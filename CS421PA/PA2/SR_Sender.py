import socket
import threading
import time
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

class SegmentSender(threading.Thread):
    def __init__(self, sock, segment, dest_addr, timeout):
        super().__init__()
        self.sock       = sock
        self.segment    = segment
        self.dest_addr  = dest_addr
        self.timeout    = timeout
        self.daemon     = True
        self._stop_event = threading.Event()

    def run(self):
        try:
            while not self._stop_event.is_set():
                self.sock.sendto(self.segment, self.dest_addr)
                if self._stop_event.wait(self.timeout):
                    break
        except Exception:
            return
        
    def stop(self):
        self._stop_event.set()

listen_ack = True  # receive_acks döngüsünü durdurmak için

def receive_acks(acked):
    sock.settimeout(1.0)
    while listen_ack:
        try:
            ack, _ = sock.recvfrom(2)
            packet_no = int.from_bytes(ack, byteorder="big")
            acked.add(packet_no)
        except socket.timeout:
            continue
        except:
            break

def main():
    file_path = sys.argv[1]
    recv_port = int(sys.argv[2])
    win_size  = int(sys.argv[3])
    timeout   = int(sys.argv[4]) / 1000.0
    recv_addr = ("127.0.0.1", recv_port)
    global listen_ack

    with open(file_path, "rb") as file:
        data = file.read()
    packets = [data[i:i + 1022] for i in range(0, len(data), 1022)]
    total_packets = len(packets)

    acked   = set()
    senders = {}

    ack_thread = threading.Thread(target=receive_acks, args=(acked,))
    ack_thread.start()

    base     = 1
    next_seq = 1

    while base <= total_packets:
        while next_seq < base + win_size and next_seq <= total_packets:
            segment = next_seq.to_bytes(2, byteorder="big") + packets[next_seq - 1]
            sender = SegmentSender(sock, segment, recv_addr, timeout)
            senders[next_seq] = sender
            sender.start()
            next_seq += 1

        while base in acked:
            senders[base].stop()
            del senders[base]
            base += 1

        time.sleep(0.0001)

    sock.sendto((0).to_bytes(2, byteorder="big"), recv_addr)

    listen_ack = False
    for s in senders.values():
        s.stop()
    time.sleep(0.1)
    sock.close()

    print(f"{total_packets} packets sent")

if __name__ == "__main__":
    main()
