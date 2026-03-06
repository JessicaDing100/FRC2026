import time
from gpiozero import Button

# ==========================================
# BALL COUNTER CLASS
# ==========================================
class BallCounter:
    def __init__(self, hub_instance, pins=[22, 23, 24, 25], grace_period=3.0):
        self.hub = hub_instance
        self.pins = pins
        self.grace_period = grace_period
        
        # Track counts for every phase of the FRC match
        self.session_totals = {
            "AUTO": 0,
            "TRANSITION": 0,
            "SHIFT_1": 0,
            "SHIFT_2": 0,
            "SHIFT_3": 0,
            "SHIFT_4": 0,
            "ENDGAME": 0
        }
        self.current_phase = "AUTO"
        self.invalid_count = 0
        self.last_active_time = 0
        
        self.buttons = []
        for pin in self.pins:
            # Matches your standalone script: pull_up=False, bounce_time=0.005
            btn = Button(pin, pull_up=False, bounce_time=0.005)
            btn.when_released = self._on_trigger
            self.buttons.append(btn)

    def _on_trigger(self, device):
        current_time = time.time()
        
        # If the Hub is active, refresh the timestamp
        if self.hub.is_active:
            self.last_active_time = current_time

        # Logic: Valid if Hub is active OR we are within the 3s grace period
        is_within_grace = (current_time - self.last_active_time) <= self.grace_period
        
        if self.hub.is_active or is_within_grace:
            self.session_totals[self.current_phase] += 1
            print(f"[SENSOR] Valid Ball in {self.current_phase}! Pin: {device.pin.number}")
        else:
            self.invalid_count += 1
            print(f"[SENSOR] Invalid Ball (Inactive & Grace Expired) on Pin: {device.pin.number}")

    def switch_phase(self, new_phase):
        if new_phase in self.session_totals:
            self.current_phase = new_phase

    def get_total_valid(self):
        return sum(self.session_totals.values())

    def reset(self):
        for key in self.session_totals:
            self.session_totals[key] = 0
        self.invalid_count = 0
        self.last_active_time = 0
