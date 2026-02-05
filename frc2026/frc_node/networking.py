import socket
import threading

class Server:
    def __init__(self, cfg, node):
        self.cfg = cfg
        self.node = node
        self.HEADER = 64
        self.PORT = cfg.get("port", 5000)
        self.SERVER = '0.0.0.0'
        self.ADDR = (self.SERVER, self.PORT)
        self.FORMAT = 'utf-8'
        self.DISCONNECT_MESSAGE = "!DISCONNECT"
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.ADDR)
        self.server.listen()

    def start_server(self):
        print("[FMS] Server starting...")
        while len(self.node.connected_clients) < self.node.client_number:
            conn, addr = self.server.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
            thread.start()

    def handle_client(self, conn, addr):
        print(f"[FMS] Client connected: {addr}")
        self.node.connected_clients.append(conn)
        self.node.client_count += 1
        if self.node.client_count == self.node.client_number:
            self.node.client_all_connected_event.set()
        
        connected = True
        while connected:
            print(connected)
            try:
                raw_len = conn.recv(self.HEADER)
                print(raw_len)
                if not raw_len: 
                    break
                msg_len = int(raw_len.decode(self.FORMAT).strip())
                msg = conn.recv(msg_len).decode(self.FORMAT)
                print(msg)
                print(f"[CLIENT {addr}] {msg}")
                if msg == self.DISCONNECT_MESSAGE: 
                    connected = False
                #if msg.startswith("SCORE:"):
                #    score = int(msg.split(":")[1])
                #    with self.node.score_lock:
                #        self.node.scores[addr] = score
                conn.send("Msg received".encode(self.FORMAT))
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
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((cfg.get('server_ip','10.17.0.141'), cfg.get("port",5000)))
        self.FORMAT = 'utf-8'

    def listen_for_server(self):
        print("[HUB] Listening to server...")
        while True:
            try:
                msg = self.client.recv(1024).decode(self.FORMAT)
                if not msg:
                    break
                
                if msg == "GAME_START":
                    print("[HUB] Match signal received!")
                    # START THE LOOP IN A THREAD
                    # This allows the 'while True' listener to keep running
                    self.node.is_aborted = False # Reset flag
                    game_thread = threading.Thread(target=self.node.hub_loop, daemon=True)
                    game_thread.start()
                    
                elif msg == "GAME_STOP":
                    print("[HUB] !!! EMERGENCY STOP RECEIVED !!!")
                    # Set the flag that your master_loop is checking
                    self.node.is_aborted = True
                    # Optional: notify your node's event object if using one
                    self.node.panic_event.set()
            except Exception as e:
                print(f"[HUB] Error: {e}")
                break
