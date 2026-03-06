import socket
import threading

class Server:
    def __init__(self, cfg, node):
        self.cfg = cfg
        self.node = node
        #self.HEADER = 64
        self.FORMAT = 'utf-8'
        self.DISCONNECT_MESSAGE = "!DISCONNECT"

        self.PORT = cfg.get("port", 5000)
        self.SERVER = '0.0.0.0'
        self.ADDR = (self.SERVER, self.PORT)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(self.ADDR)
        self.server.listen()

    def start_server(self):
        print("[FMS] Server active. Waiting for hubs...")
        while len(self.node.connected_clients) < self.node.client_number:
            conn, addr = self.server.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

    def handle_client(self, conn, addr):
        print(f"[FMS] Client connected: {addr}")
        self.node.connected_clients.append(conn)
        self.node.client_count += 1
        if self.node.client_count == self.node.client_number:
            self.node.client_all_connected_event.set()

        buffer = "" # NEW: Buffer to store partial data
        connected = True
        while connected:
            try:
                data = conn.recv(1024).decode(self.FORMAT)
                if not data: break
                
                buffer += data
                # NEW: Process every complete message in the buffer
                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)
                    msg = msg.strip()
                    if not msg: continue

                    #print(f"[CLIENT {addr}] {msg}")

                    if ":" in msg:
                        parts = msg.split(":")
                        if len(parts) == 3:
                            header, alliance, val = parts
                            if header == "HUB_AUTO_SCORE":
                                self.node.process_hub_data(addr, alliance, val)
                                conn.send("DATA_ACK\n".encode(self.FORMAT))
                            elif header == "HUB_SCORE":
                                self.node.report_hub_data(addr, alliance, val)

                    elif msg == self.DISCONNECT_MESSAGE:
                        connected = False            
            except Exception as e:
                print(f"[ERROR] Client {addr}: {e}")
                break
        conn.close()
        print(f"[FMS] Client {addr} disconnected")

    def broadcast(self, msg):
        for conn in self.node.connected_clients:
            try:
                conn.send(msg.encode(self.FORMAT))
            except: pass

class Client:
    def __init__(self, cfg, node):
        self.cfg = cfg
        self.node = node
        self.FORMAT = 'utf-8'
        self.net_lock = threading.Lock()

        # Initialize socket
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = cfg.get('server_ip', '10.17.0.162')
        self.port = cfg.get("port", 5000)

    def connect(self):
        """Attempts to connect to the FMS server."""
        try:
            print(f"[HUB] Connecting to FMS at {self.server_ip}:{self.port}...")
            self.client.connect((self.server_ip, self.port))
            print("[HUB] Connected successfully.")
            return True
        except Exception as e:
            print(f"[HUB] Connection failed: {e}")
            return False

    def send_to_server(self, msg):
        """Sends a message with a newline delimiter for framing."""
        try:
            with self.net_lock:
                # strip() ensures we don't send "MSG\n\n" if game logic added a \n
                full_msg = f"{msg.strip()}\n"
                self.client.send(full_msg.encode(self.FORMAT))
        except Exception as e:
            print(f"[CLIENT] Send error: {e}")

    def listen_for_server(self):
        """Listens for FMS commands and processes them using a buffer."""
        print("[HUB] Listening to server...")
        buffer = ""

        while True:
            try:
                # Receive raw data from the stream
                data = self.client.recv(1024).decode(self.FORMAT)
                if not data:
                    print("[HUB] Server closed connection.")
                    break

                buffer += data

                # Process all complete messages in the buffer
                while "\n" in buffer:
                    msg_raw, buffer = buffer.split("\n", 1)
                    msg = msg_raw.strip()

                    if not msg:
                        continue

                    # --- Command Dispatch ---
                    if msg == "GAME_START":
                        print("[HUB] Match signal received!")
                        self.node.is_aborted = False
                        # Run hub hardware logic in a separate thread
                        threading.Thread(target=self.node.hub_loop, daemon=True).start()

                    elif msg == "DATA_ACK":
                        print("[HUB] FMS confirmed receipt of data.")
                        self.node.hub_hardware.ack_received_signal.set()

                    elif msg.startswith("AUTO_RESULT:"):
                        winner = msg.split(":")[1]
                        print(f"[HUB] Auto result received: {winner}")
                        self.node.hub_hardware.auto_winner = winner
                        self.node.hub_hardware.teleop_ready_signal.set()

                    elif msg == "GAME_STOP":
                        print("[HUB] !!! EMERGENCY STOP RECEIVED !!!")
                        self.node.is_aborted = True
                        # Reset hardware signals immediately
                        self.node.hub_hardware.teleop_ready_signal.clear()
                        self.node.hub_hardware.ack_received_signal.clear()
                        self.node.panic_event.set()

                    else:
                        print(f"[HUB] Unknown command: {repr(msg)}")

            except Exception as e:
                print(f"[HUB] Receiver loop error: {e}")
                break