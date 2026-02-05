import time
import math
#try:
#    import RPi.GPIO as GPIO
#    HAS_GPIO = True
#except ImportError:
#    HAS_GPIO = False
#from pi5neo import Pi5Neo

class HubHardware:
    def __init__(self, cfg, node):
        self.cfg = cfg
        self.node = node
        self.is_active = False
        self.balls_detected = 0
        self.strip = Pi5Neo('/dev/spidev0.0', 150, 800)
        self.color = (255,0,0) if cfg['alliance']=="RED" else (0,0,255)
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

    def led_animator(self, pulse=False):
        if self.is_active:
            if pulse: #ToDo: don't really need this part
                t = time.time()
                intensity = int((math.sin(t*3)+1)/2 * 255)
                self.strip.fill_strip(int(self.color[0]*intensity/255),
                                      int(self.color[1]*intensity/255),
                                      int(self.color[2]*intensity/255))
            else:
                self.strip.fill_strip(*self.color)
        else:
            self.strip.fill_strip(0,0,0)
        self.strip.update_strip()

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
        # If you have a buzzer or specific 'stop' animation, trigger it here
        return False

    def hub_loop(self):
        self.is_active = True
        start_time = time.time()
        self.led_animator()
        if not self.count_down(start_time, 17): 
            return self.emergency_shutdown()
        
        mid_time = time.time()

        # Pulse to indicate end (when pulse is needed)
        for _ in range(4):
            self.is_active = False
            self.led_animator()
            if not self.interruptible_sleep(0.25): return self.emergency_shutdown()
            self.is_active = True
            if not self.interruptible_sleep(0.25): return self.emergency_shutdown()
            self.led_animator()
     
        self.is_active = False
        self.led_animator()
        end_time = time.time()
        print("[HUB] total period duration", 20)
        print("[HUB] count down start @", round(mid_time-start_time))
        print("[HUB] end @", round(end_time-start_time))
        print("[HUB] Hub loop complete")

        # 1. ASSESSMENT BUFFER (3s)
        if not self.interruptible_sleep(3): return self.emergency_shutdown()

        # 2. Transition Shift
        self.is_active = True
        start_time = time.time()
        self.led_animator()
        if not self.count_down(start_time, 10): 
            return self.emergency_shutdown() 
              
        # 3. MATCH TIMEFRAMES (Table 6-3)
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
            won_auto = True #(game_data == my_alliance)
            is_odd_shift = (i % 2 != 0)
        
            if won_auto:
                self.is_active = not is_odd_shift
            else:
                self.is_active = is_odd_shift
            print(self.is_active)
            print(f"[HUB] {shift['name']} - Active: {self.is_active}")
            self.led_animator() # Update LEDs to show state

            # Run the shift timer
            start_shift = time.time()
            if not self.node.count_down(start_shift, shift['duration']):
                return self.emergency_shutdown()

        # 3. END GAME (Final 30s)
        # Table 6-3: Both Hubs are ALWAYS active during End Game
        self.is_active = True
        self.led_animator()
        if not self.node.count_down(time.time(), 30):
            return self.emergency_shutdown()

        print("[HUB] Match Complete")
        self.is_active = False
        self.led_animator()

    #def cleanup(self):
    #    if HAS_GPIO and self.sensor_pins:
    #        GPIO.cleanup()
