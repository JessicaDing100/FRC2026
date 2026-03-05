from gpiozero import Servo
from time import sleep

class TalonPWM:
    def __init__(self, gpio_pin=18):
        """
        Initializes a Talon SRX via PWM on the Raspberry Pi 5.
        Default pin is GPIO 18 (Physical Pin 12).
        """
        # Standard Talon SRX PWM: 1.0ms (Full Rev), 1.5ms (Neutral), 2.0ms (Full Fwd)
        self.motor = Servo(
            gpio_pin, 
            min_pulse_width=1/1000, 
            max_pulse_width=2/1000,
            initial_value=0
        )
        self.is_running = False
        print(f"Talon SRX initialized on GPIO {gpio_pin}")

    def start(self, speed=0.5):
        """Sets the motor to a specific speed (-1.0 to 1.0)."""
        self.motor.value = speed
        self.is_running = True
        print(f"Motor ON: Speed {speed}")

    def stop(self):
        """Triggers Neutral/Brake state."""
        self.motor.value = 0
        self.is_running = False
        print("Motor OFF: Neutral")

    def emergency_shutdown(self):
        """Complete release of the PWM signal."""
        self.motor.value = 0
        self.is_running = False
        self.motor.close()
        print("GPIO Released: Emergency Stop")
