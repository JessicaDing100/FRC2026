import time
import threading
#import random
from .led import LedManager
from .motor_controller import TalonPWM
from .ball_counter import BallCounter

class HubHardware:
    def __init__(self, cfg, node):
        self.cfg = cfg
        self.node = node
        self.is_active = False
        self.is_blink = False
        #self.balls_detected = random.randint(50,300)

        # LED
        self.strip = LedManager(150)
        self.color = (255,0,0) if cfg['alliance']=="RED" else (0,0,255)
        self.my_alliance = "R" if cfg['alliance']=="RED" else "B"
        # Motor
        self.motor_pin = cfg.get("motor_pin", 18)
        self.talon = TalonPWM(self.motor_pin)
        # Ball Counter Integration
        sensor_pins = cfg.get("sensor_pins", [22, 23, 24, 25])
        self.ball_counter = BallCounter(self, pins=sensor_pins, grace_period=3.0)
        # Signal/Event Setup
        self.auto_winner = None
        self.ack_received = False
        self.teleop_ready_signal = threading.Event()
        self.ack_received_signal = threading.Event()

        # Start the score background reporter
        self.stop_reporter = threading.Event()
        self.reporter_thread = threading.Thread(target=self._score_reporter_loop, daemon=True)
        self.reporter_thread.start()

        #if HAS_GPIO and self.sensor_pins:
        #    GPIO.setmode(GPIO.BCM)
        #    for pin in self.sensor_pins:
        #        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        #        GPIO.add_event_detect(pin, GPIO.FALLING,
        #                              callback=self.on_ball_detected, bouncetime=150)

    def _score_reporter_loop(self):
        """Runs in the background, sending the score every 1 second."""
        while not self.stop_reporter.is_set():
            # Only send if the node is active and not aborted
            if not self.node.is_aborted:
                try:
                    # Format: HUB_SCORE:R:15
                    score_msg = f"HUB_SCORE:{self.my_alliance}:{self.balls_detected}"
                    self.node.networking.send_to_server(score_msg)
                except Exception as e:
                    print(f"[REPORTER] Network error: {e}")
            
            # Wait for 1 second (interruptible by the stop event)
            self.stop_reporter.wait(1.0)

    @property
    def balls_detected(self):
        """Used by existing networking code to get current valid total."""
        return self.ball_counter.get_total_valid()

    def led_animator(self):
        if self.is_active:
            self.strip.fill(*self.color)
        else:
            self.strip.fill(0,0,0)

    def led_blink(self, start_time, seconds):
        if self.is_active:
            self.led_animator()
            if self.is_blink:
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
                if not self.count_down(start_time, seconds):
                    return self.emergency_shutdown()
        else:
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
        self.talon.stop()
        self.ball_counter.reset()
        self.ack_received = False
        # If you have a buzzer or specific 'stop' animation, trigger it here
        return False

    def hub_loop(self):
        # --- 1. AUTO (20s) & ASSESSMENT (3s) ---
        print("[HUB] AUTO (20s)")
        self.talon.start(0.6) #ToDo: not tested yet
        self.ball_counter.reset()
        self.ball_counter.switch_phase("AUTO")
        self.is_active = True
        self.is_blink = False
        start_time = time.time()
        self.led_blink(start_time, 20)
        #---- sleep 3 seconds
        if not self.interruptible_sleep(3): return self.emergency_shutdown()
        auto_balls_detected = self.balls_detected

        # --- 2. TRANSITION & HANDSHAKE (10s) ---
        print("[HUB] TELEOP (10s)")
        self.ball_counter.switch_phase("TRANSITION")
        self.is_active = True
        self.led_animator()
        transition_start = time.time()
        last_retry = 0

        # This loop handles both the 5s timeout AND the retry logic
        while (time.time() - transition_start) < 5.0:
            if self.node.is_aborted: return self.emergency_shutdown()

            # If FMS hasn't ACKed yet, retry every 2 seconds
            if not self.ack_received and (time.time() - last_retry > 2.0):
                score_msg = f"HUB_AUTO_SCORE:{self.my_alliance}:{auto_balls_detected}"
                print(score_msg)
                self.node.networking.send_to_server(score_msg)
                last_retry = time.time()

            # Check if the FMS received the ball count
            if self.ack_received_signal.is_set():
               self.ack_received = True
            time.sleep(0.05)
        # Check if the FMS broadcasted the final AUTO_RESULT
        if not self.teleop_ready_signal.is_set():
            print("[HUB] Failed to receive match sync from FMS!")
            return self.emergency_shutdown()

        won_auto = (self.auto_winner == self.my_alliance)
        if won_auto:
            self.is_blink = True
        else:
            self.is_blink = False
        self.led_blink(time.time(), 5)

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
            self.ball_counter.switch_phase(shift['name'])
            is_odd = (i % 2 != 0)
            self.is_active = not is_odd if won_auto else is_odd
            print(f"[HUB] {shift['name']} - Active: {self.is_active}")
            if i == 4:
                self.is_blink = False
            else:
                self.is_blink = True
            # Run the shift timer
            start_shift = time.time()
            self.led_blink(start_shift, shift['duration'] )

        # --- 4. ENDGAME --- (Final 30s)
        # Table 6-3: Both Hubs are ALWAYS active during End Game
        print("[HUB] ENDGAME (30s)")
        self.ball_counter.switch_phase("ENDGAME")
        self.is_active = True
        self.is_blink = False
        self.led_blink(time.time(), 30)

        print("[HUB] Match Complete")
        self.ack_received = False
        
        self.is_active = False
        print("[HUB] Match Over. Final 3s Grace Period...")
        self.interruptible_sleep(3) # Wait for final endgame balls
        self.talon.stop()
        self.ball_counter.reset()

    def cleanup(self):
        self.is_active = False
        self.led_animator()
        self.talon.stop()
        # Stop the reporting thread when the node shuts down
        self.stop_reporter.set()
        self.reporter_thread.join(timeout=1.0)
    #    if HAS_GPIO and self.sensor_pins:
    #        GPIO.cleanup()