import json
import os
import threading
import time
#import keyboard
#import platform
from .networking import Server, Client
from .hub import HubHardware
from .sound import SoundManager
#from .gui import ScoreboardGUI
#from .panic import PanicButton

class FRC2026Node:
    def __init__(self, config_path="config.json"):
        # -------------------- Load Config --------------------
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"Config file '{config_path}' not found.")
        with open(config_path) as f:
            self.cfg = json.load(f)
        
        # -------------------- Shared State --------------------
        self.connected_clients = []
        self.client_number = 1 #total number of clients
        self.client_count = 0
        self.client_all_connected_event = threading.Event()

        self.current_period = "PREMATCH"
        self.panic_event = threading.Event()
        self.is_aborted = False
        self.match_thread = None
        #self.score_lock = threading.Lock()
        #self.scores = {}
        self.balls = 0
        self.points = 0
        self.is_active = False

        # -------------------- Role-specific Setup --------------------
        if self.cfg['role'] == "FMS":
            self.networking = Server(self.cfg, self)
            self.sound_manager = SoundManager(self.cfg)        
        elif self.cfg['role'] == "HUB":
            self.networking = Client(self.cfg, self)
            self.hardware = HubHardware(self.cfg, self)
        else:
            raise ValueError("Invalid role in config (must be 'FMS' or 'HUB')")
        #self.gui = ScoreboardGUI(self)
        #self.panic_button = PanicButton(self)
        

    # -------------------- Countdown --------------------
    def count_down(self, start_time, target_duration):
        # An interruptible countdown timer
        while (time.time() - start_time) < target_duration:
            if self.is_aborted:
                return False  # Tell the caller we need to stop
            time.sleep(0.05)   # Check for abort flag every 100ms
        return True

    # -------------------- Game Loops --------------------
    def master_loop(self):

        # --- AUTONOMOUS ---
        self.current_period = "AUTONOMOUS"
        start_time = time.time()
        self.sound_manager.play_cue("START")
        if not self.count_down(start_time, 20): 
            return self.emergency_shutdown()
        self.sound_manager.play_cue("END_AUTO")

        # --- TRANSITION ---
        # Scoring assessment buffer
        if not self.interruptible_sleep(3): 
            return self.emergency_shutdown()

        # --- TELEOP ---
        self.current_period = "TELEOP"
        start_time = time.time()
        self.sound_manager.play_cue("TELEOP")
        for t in [10, 35, 60, 85, 110, 140]:
            if not self.count_down(start_time, t):
                return self.emergency_shutdown()
            print(t)
            if t < 110: self.sound_manager.play_cue("SHIFT")
            elif t == 110: self.sound_manager.play_cue("WHISTLE")
            elif t == 140: self.sound_manager.play_cue("ENDGAME")

        self.current_period = "POSTMATCH"
        time.sleep(5)
    
    def interruptible_sleep(self, seconds):
        """A replacement for time.sleep() that honors the panic button."""
        start = time.time()
        while time.time() - start < seconds:
            if self.is_aborted: return False
            time.sleep(0.1)
        return True
     
    def emergency_shutdown(self):
        # Logic to execute when the match is killed
        #self.sound_manager.stop_all()
        self.sound_manager.play_cue("STOP")
        self.current_period = "ABORTED"
        print("Match safely terminated.")
        return False


    def hub_loop(self):
        #self.hardware.hub_loop(panic_event=self.panic_event)
        self.hardware.hub_loop()

    def keyboard_button(self):
        import keyboard
        while True:
            keyboard.wait('p') # This blocks THIS thread, which is fine
            print("[FMS] PANIC PRESSED!")
            self.is_aborted = True
            self.panic_event.set()
            # Broadcast immediately when the key is pressed
            self.networking.broadcast("GAME_STOP")

    # -------------------- Game Start --------------------
    def start_game(self):
        import keyboard
        print("[FMS] Waiting for all clients...")
        self.client_all_connected_event.wait()
        print("[FMS] All clients connected!")
        try: 
            while True:
                # Wait for 'S' to start instead of Enter to keep it consistent
                print("[FMS] Press 'S' to start the match...")
                keyboard.wait('s') 
            
                self.is_aborted = False
                self.panic_event.clear()
            
                print("[FMS] Starting game now!")
                self.networking.broadcast("GAME_START")
            
                # Start the match timeline
                self.match_thread = threading.Thread(target=self.master_loop, daemon=True)
                self.match_thread.start()
            
                # Wait for the match to finish or be aborted before allowing a restart
                self.match_thread.join() 
                print("[FMS] Match sequence finished. Ready for next.")          
        except KeyboardInterrupt:
            print("[FMS] Shutting down.")       

    # -------------------- Main Loops --------------------
    def fms_loop(self):
        threading.Thread(target=self.keyboard_button, daemon=True).start()
        #threading.Thread(target=self.gui.run, daemon=True).start()
        threading.Thread(target=self.networking.start_server, daemon=True).start()
        self.start_game()
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            print("[FMS] Shutting down.")

    def hub_loop_main(self):
        self.networking.listen_for_server()

    # -------------------- Run --------------------
    def run(self):
        try:
            if self.cfg['role'] == "FMS":
                self.fms_loop()
            elif self.cfg['role'] == "HUB":
                self.hub_loop_main()
        finally:
            pass
            #self.hardware.cleanup()
