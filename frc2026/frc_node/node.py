import json
import os
import threading
import time
import random
from datetime import datetime

from .gui_config import ConfigGui
from .networking import Server, Client
from .hub import HubHardware
from .sound import SoundManager
#from .gui import MatchLogger
from .button import USBPanicButton
from .gui_scoreboard import ScoreboardGUI

class FRC2026Node:
    def __init__(self, config_path="config.json"):
        # -------------------- Load Config --------------------
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"Config file '{config_path}' not found.")
        with open(config_path) as f:
            self.cfg = json.load(f)

        # -------------------- Shared State --------------------
        self.connected_clients = []
        self.client_number = 0
        self.client_count = 0
        self.client_all_connected_event = threading.Event()
        self.hub_number = 0
        self.hub_counts = {}
        self.auto_winner_mode = 'S';
        self.alliance_scores = {'R': 0, 'B': 0}
        self.handshake_lock = threading.Lock()

        self.current_period = "PREMATCH"
        self.panic_event = threading.Event()
        self.is_aborted = False
        self.match_thread = None
        self.match_in_progress = False
        self.start_triggered = threading.Event()
        #self.score_lock = threading.Lock()
        #self.scores = {}
        #self.balls = 0
        #self.points = 0
        #self.is_active = False

        # -------------------- Role-specific Setup --------------------
        if self.cfg['role'] == "FMS":
            self.networking = Server(self.cfg, self)
            self.sound_manager = SoundManager(self.cfg)
            self.physical_button = USBPanicButton()
            self.physical_button.start_listening(callback=self.handle_physical_button)

            #self.scoreboard = Scoreboard()
            # 1. Start the NetworkTables Server
            #self.inst = ntcore.NetworkTablesInstance.getDefault()
            #self.inst.startServer() # The Pi is now the "Boss"

        elif self.cfg['role'] == "HUB":
            self.networking = Client(self.cfg, self)
            self.hub_hardware = HubHardware(self.cfg, self)
        else:
            raise ValueError("Invalid role in config (must be 'FMS' or 'HUB')")
        #self.gui = ScoreboardGUI(self)
        #self.panic_button = PanicButton(self)

    def report_hub_data(self, addr, alliance, ball_count):
        #with self.handshake_lock:
        self.alliance_scores[alliance] = int(ball_count)
            
    def process_hub_data(self, addr, alliance, ball_count):
        with self.handshake_lock:
            # Update the count for this specific hub address
            self.hub_counts[addr] = int(ball_count)
            self.alliance_scores[alliance] = int(ball_count)

            if len(self.hub_counts) == self.hub_number:
                if self.hub_number == 1:
                    winner = self.auto_winner_mode
                    print(f"[FMS] Auto Winner set to: {winner}")
                else:
                    if self.auto_winner_mode == 'S':
                        # Decide winner (Red vs Blue)
                        # Q: what if tie? Randomly choose the winner
                        # Direct lookup by alliance key avoids the list index issues
                        red_total = self.alliance_scores.get('R', 0)
                        blue_total = self.alliance_scores.get('B', 0)

                        if red_total > blue_total:
                            winner = "R"
                        elif blue_total > red_total:
                            winner = "B"
                        else:
                            winner = random.choice(["R", "B"])
                    else:
                        winner = self.auto_winner_mode
                    print(f"[FMS] Both Hubs reported. Auto Winner: {winner}")
                self.networking.broadcast(f"AUTO_RESULT:{winner}\n")
            else:
                print(f"[FMS] Waiting for second hub data... (Currently have {len(self.hub_counts)})")

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
        self.hub_counts = {}
        self.alliance_scores = {'R': 0, 'B': 0}
        # --- AUTONOMOUS ---
        self.current_period = "AUTONOMOUS"
        auto_duration = 20
        self.current_period_end_time = time.time() + auto_duration
        #start_time = time.time()
        self.sound_manager.play_cue("START")
        if not self.count_down(time.time(), auto_duration):
            return self.emergency_shutdown()
        self.sound_manager.play_cue("END_AUTO")
        #self.alliance_scores['R'] = random.randint(0, 50)
        #self.alliance_scores['B'] = random.randint(0, 50)

        # --- TRANSITION ---
        # Scoring assessment buffer
        self.current_period = "TRANSITION"
        if not self.interruptible_sleep(3):
            return self.emergency_shutdown()

        # --- TELEOP ---
        self.current_period = "TELEOP"
        teleop_duration = 140
        self.current_period_end_time = time.time() + teleop_duration
        start_time = time.time()
        self.sound_manager.play_cue("TELEOP")
        for t in [10, 35, 60, 85, 110, 140]:
            if not self.count_down(start_time, t):
                return self.emergency_shutdown()
            #print(t)
            if t < 110: self.sound_manager.play_cue("SHIFT")
            elif t == 110: self.sound_manager.play_cue("WHISTLE")
            elif t == 140: self.sound_manager.play_cue("ENDGAME")
            #self.alliance_scores['R'] = self.alliance_scores['R'] + random.randint(0, 50)
            #self.alliance_scores['B'] = self.alliance_scores['B'] + random.randint(0, 50)

        self.current_period = "POSTMATCH"
        #self.current_period_end_time = time.time()
        self.match_in_progress = False
        print("[FMS] Match complete. Waiting for post-match processing...")
        #self.hub_counts = {}
        #self.alliance_scores = {'R': 0, 'B': 0}
        time.sleep(5)

    def interruptible_sleep(self, seconds):
        """A replacement for time.sleep() that honors the panic button."""
        start = time.time()
        while time.time() - start < seconds:
            if self.is_aborted: return False
            time.sleep(0.05)
        return True

    def emergency_shutdown(self):
        # Logic to execute when the match is killed
        #self.sound_manager.stop_all()
        self.is_aborted = True
        self.match_in_progress = False
        self.current_period = "ABORTED"
        self.networking.broadcast("GAME_STOP\n")
        self.sound_manager.play_cue("STOP")
        self.hub_counts = {}
        #self.alliance_scores = {'R': 0, 'B': 0}
        print("Match safely terminated.")
        return False

    def reset_match(self):
        self.is_aborted = False
        self.match_in_progress = False
        self.current_period = "PREMATCH"
        self.alliance_scores = {'R': 0, 'B': 0}
        self.hub_counts = {}
        # This ensures the GUI renders "0:20" again
        self.current_period_end_time = time.time()
        print("[FMS] Scoreboard and Timer reset to 0:20.")
        
    def hub_loop(self):
        #self.hub_hardware.hub_loop(panic_event=self.panic_event)
        self.hub_hardware.hub_loop()

    def handle_physical_button(self):
        """This function runs whenever the USB button is pressed."""
        # State 1: Match is over or hasn't started -> Start the match
        if self.current_period == "PREMATCH":
            print("[FMS] Physical Button -> START MATCH")
            self.start_triggered.set()

        # State 2: Match is currently running -> Emergency Stop
        elif self.match_in_progress:
            print("[FMS] Physical Button -> EMERGENCY STOP")
            self.emergency_shutdown()

        # State 3: Match is finished (POSTMATCH/ABORTED) -> Reset to PREMATCH
        else:
            print("[FMS] Physical Button -> RESET TO PREMATCH")
            self.reset_match()
            
#    def keyboard_button(self):
#        import keyboard
#        while True:
#            keyboard.wait('p') # This blocks THIS thread, which is fine
#            print("[FMS] PANIC PRESSED!")
#            self.is_aborted = True
#            self.panic_event.set()
#            # Broadcast immediately when the key is pressed
#            self.networking.broadcast("GAME_STOP\n")

    # -------------------- Game Start --------------------
    def start_game(self):
        #import keyboard
        print("[FMS] Waiting for all clients...")
        self.client_all_connected_event.wait()
        print("[FMS] All clients connected!")
        try:
            while True:
                # 1. SETUP PREMATCH
                self.current_period = "PREMATCH"
                self.alliance_scores = {'R': 0, 'B': 0} # Clear scores for the new match
                self.is_aborted = False
                self.match_in_progress = False
                
                print("\n[FMS] SYSTEM READY. Press USB Button to START match...")
                # Wait for physical button to start the timeline
                self.start_triggered.wait()
                self.start_triggered.clear() # Reset for next time

                # 2. RUN MATCH
                self.match_in_progress = True              
                #self.scoreboard.update(self.alliance_scores.get('B', 0), self.alliance_scores.get('R', 0), "2 / 6  :16")
                print("[FMS] Starting game now!")
                self.networking.broadcast("GAME_START\n")

                # Wait for 'S' to start instead of Enter to keep it consistent
                #print("[FMS] Press 's' to start the match...")
                #keyboard.wait('s')
                #self.panic_event.clear()

                # Start the match timeline
                self.match_thread = threading.Thread(target=self.master_loop, daemon=True)
                self.match_thread.start()

                # 3. WAIT FOR COMPLETION                
                #print("[FMS] Press 'p' to stop the match...")
                print("[FMS] Press USB Button for EMERGENCY STOP...")
                self.match_thread.join()
                #self.match_thread.join(timeout=1.0) # AI suggested this
                # Once master_loop ends (natually or aborted)
                self.match_in_progress = False
                print("[FMS] Displaying Final Results. Press USB Button to RESET TO PREMATCH...")

                # 4. THE RESET TRIGGER
                # This stops the loop here until you press the button to "Confirm" the reset
                self.start_triggered.wait()
                self.start_triggered.clear()
                print(self.current_period)
                print(self.match_in_progress)
                print("[FMS] Resetting field...")
                time.sleep(1) # Small buffer to prevent double-triggering

        except KeyboardInterrupt:
            self.networking.server.close()
            print("[FMS] Shutting down.")

    # -------------------- Main Loops --------------------
    def fms_loop(self):
        launcher = ConfigGui()
        config = launcher.get_config()
        self.hub_number = config["hubs"]
        self.client_number = config["clients"]
        self.auto_winner_mode = config["winner_mode"]
        print(f"Mode Selected: {self.auto_winner_mode}")
        if self.auto_winner_mode == 'R':
            print("Manual override: Red Alliance wins.")
        elif self.auto_winner_mode == 'B':
            print("Manual override: Blue Alliance wins.")
        else:
            print("Automatic: Calculating winner based on scores.")
                
        #self.physical_button.start_listening(callback=self.handle_physical_button)
        #threading.Thread(target=self.keyboard_button, daemon=True).start()
        #threading.Thread(target=self.gui.run, daemon=True).start()

        # 1. Start Networking in a background thread
        threading.Thread(target=self.networking.start_server, daemon=True).start()
        # 2. Start the Match Logic (start_game) in a background thread
        threading.Thread(target=self.start_game, daemon=True).start()
        # 3. Call the Scoreboard on the MAIN thread
        self.scoreboard = ScoreboardGUI(self)
        print("[FMS] Launching Simplified Scoreboard...")
        self.scoreboard.run()

        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            #ToDo: what else need to be clean up?
            self.networking.server.close()
            print("[FMS] Shutting down.")

    def hub_loop_main(self):
        # 1. Attempt connection
        if self.networking.connect():
            # 2. Start the listener in a BACKGROUND thread
            # This allows the listener to run while this function continues
            listener = threading.Thread(target=self.networking.listen_for_server, daemon=True)
            listener.start()
            print("[HUB] Network listener is running in the background.")
        else:
            print("[HUB] Failed to connect. Check FMS IP and Network.")

        # 3. Now the main thread can do other things, like a heart-beat or status check
        while True:
            # Keep the main process alive or do general status updates here
            time.sleep(1)

    # -------------------- Run --------------------
    def run(self):
        try:
            if self.cfg['role'] == "FMS":
                self.fms_loop()
            elif self.cfg['role'] == "HUB":
                self.hub_loop_main()
        finally:
            if self.cfg['role'] == "FMS":
                self.networking.server.close()
            elif self.cfg['role'] == "HUB":
                print("Clean up Hub")
                self.hub_hardware.cleanup()