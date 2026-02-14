import time
import threading
import math
import random
#try:
#    import RPi.GPIO as GPIO
#    HAS_GPIO = True
#except ImportError:
#    HAS_GPIO = False
from pi5neo import Pi5Neo  # enable on HUBs

class HubHardware:
    def __init__(self, cfg, node):
        self.cfg = cfg
        self.node = node
        self.is_active = False
        self.balls_detected = random.randint(50,300)
        self.strip = Pi5Neo('/dev/spidev0.0', 150, 800)
        self.color = (255,0,0) if cfg['alliance']=="RED" else (0,0,255)
        self.my_alliance = "R" if cfg['alliance']=="RED" else "B"
        self.auto_winner = None
        self.ack_received = False
        self.teleop_ready_signal = threading.Event()
        self.ack_received_signal = threading.Event()
        #self.sensor_pins = cfg.get("sensor_pins", [])
        #if HAS_GPIO and self.sensor_pins:
        #    GPIO.setmode(GPIO.BCM)
        #    for pin in self.sensor_pins:
        #        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        #        GPIO.add_event_detect(pin, GPIO.FALLING,
        #                              callback=self.on_ball_detected, bouncetime=150)

    def on_ball_detected(self, channel):
        self.balls_detected +=1
        #self.flash_led()
        print(f"[HUB] Ball detected on pin {channel}")

    def flash_led(self, duration=0.2):
        self.is_active=False
        self.led_animator()
        time.sleep(duration)
        self.is_active=True
        self.led_animator()

    def led_animator(self):
        if self.is_active:
            self.strip.fill_strip(*self.color)
        else:
            self.strip.fill_strip(0,0,0)
        self.strip.update_strip()

    def led_blink(self, is_active, start_time, seconds):
        if is_active:
            self.is_active = True
            self.led_animator()
            if not self.count_down(start_time, seconds-3):
                return self.emergency_shutdown()

            # Pulse to indicate end of the period
            for _ in range(4):
                self.is_active = False
                self.led_animator()
                if not self.interruptible_sleep(0.25): return self.emergency_shutdown()
                self.is_active = True
                if not self.interruptible_sleep(0.25): return self.emergency_shutdown()
                self.led_animator()
            self.is_active = False
            self.led_animator()
        else:
            self.is_active = False
            self.led_animator()
            if not self.count_down(start_time, seconds):
                return self.emergency_shutdown()
        

    def interruptible_sleep(self, seconds):
        """Replacement for time.sleep that checks for panic flag every 0.05s."""
        stop_at = time.time() + seconds
        while time.time() < stop_at:
            if self.node.is_aborted:
                return False
            time.sleep(0.05) # Small granularity check
        return True

    def count_down(self, start_time, target_duration):
        # An interruptible countdown timer
        while (time.time() - start_time) < target_duration:
            if self.node.is_aborted:
                return False  # Tell the caller we need to stop
            time.sleep(0.05)   # Check for abort flag every 100ms
        return True
    
    def emergency_shutdown(self):
        """Forces LEDs off and exits logic."""
        print("[HUB] !!! ABORTING HUB LOOP !!!")
        self.is_active = False
        self.led_animator()
        self.ack_received = False
        # If you have a buzzer or specific 'stop' animation, trigger it here
        return False

    def hub_loop(self):
        # --- 1. AUTO (20s) & ASSESSMENT (3s) ---
        print("[HUB] AUTO (20s)")
        start_time = time.time()
        self.led_blink(True, start_time, 20)
        #---- sleep 3 seconds
        if not self.interruptible_sleep(3): return self.emergency_shutdown()

        # --- 2. TRANSITION & HANDSHAKE (10s) ---
        print("[HUB] TELEOP (10s)")
        self.is_active = True
        self.led_animator()
        transition_start = time.time()
        last_retry = 0

        # This loop handles both the 5s timeout AND the retry logic
        while (time.time() - transition_start) < 5.0:
            if self.node.is_aborted: return self.emergency_shutdown()
            
            # If FMS hasn't ACKed yet, retry every 2 seconds
            if not self.ack_received and (time.time() - last_retry > 2.0):
                print(f"[HUB] Sending ball count ({self.balls_detected})...")
                if self.my_alliance == "R":
                    self.node.networking.send_to_server(f"HUB_SCORE:R:{self.balls_detected}")
                else:
                    self.node.networking.send_to_server(f"HUB_SCORE:B:{self.balls_detected}")

                last_retry = time.time()
            
            # Check if the FMS received the ball count
            if self.ack_received_signal.is_set():
               self.ack_received = True
                
            time.sleep(0.05)
        # Check if the FMS broadcasted the final AUTO_RESULT
        if not self.teleop_ready_signal.is_set():
            print("[HUB] Failed to receive match sync from FMS!")
            return self.emergency_shutdown()

        self.led_blink(True, time.time(), 5)

        # --- 3. TELEOP SHIFTS --- (Table 6-3)
        # Each Shift is 25 seconds (example duration)
        shifts = [
            {"name": "SHIFT 1", "duration": 25},
            {"name": "SHIFT 2", "duration": 25},
            {"name": "SHIFT 3", "duration": 25},
            {"name": "SHIFT 4", "duration": 25}
        ]

        for i, shift in enumerate(shifts, 1):
            # Determine Activity based on Table 6-3 logic
            # If we won Auto, we are inactive on odd shifts (1, 3)
            won_auto = (self.auto_winner == self.my_alliance)
            is_odd = (i % 2 != 0)
            self.is_active = not is_odd if won_auto else is_odd
            print(f"[HUB] {shift['name']} - Active: {self.is_active}")
            # Run the shift timer
            start_shift = time.time()
            self.led_blink(self.is_active, start_shift, shift['duration'] )

        # --- 4. ENDGAME --- (Final 30s)
        # Table 6-3: Both Hubs are ALWAYS active during End Game
        print("[HUB] ENDGAME (30s)")
        self.led_blink(True, time.time(), 30)

        print("[HUB] Match Complete")
        self.ack_received = False

    #def cleanup(self):
    #    if HAS_GPIO and self.sensor_pins:
    #        GPIO.cleanup()
