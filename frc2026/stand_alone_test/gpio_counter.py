import sys
import termios
import tty
import time
import pyfiglet  # <-- NEW IMPORT
from gpiozero import Button

# --- Configuration ---
GPIO_PINS = [22, 23, 24, 25]
DEBOUNCE_TIME = 0.005  

# --- Global State ---
counters = {pin: 0 for pin in GPIO_PINS}
counting = False

def on_toggle(device):
    if counting:
        pin = device.pin.number
        counters[pin] += 1
        print(f"\rGPIO {pin} triggered! Count={counters[pin]}\r\n")

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def main():
    global counting
    
    buttons = []
    for pin in GPIO_PINS:
        btn = Button(pin, pull_up=False, bounce_time=DEBOUNCE_TIME)
        btn.when_released = on_toggle
        buttons.append(btn)

    print("=== Ball Counter Ready ===")
    print(f"Monitoring Pins: {GPIO_PINS}")
    print("--------------------------")
    print("Press the SPACE BAR to START counting.")
    print("Press 'q' or 'Q' to QUIT.\n")

    try:
        while True:
            ch = getch()
            
            if ch.lower() == 'q' or ch == '\x03':
                print("\nExiting program...")
                break
                
            elif ch == ' ':
                if not counting:
                    for pin in counters:
                        counters[pin] = 0
                    counting = True
                    print("\r--> Counting STARTED. (Press SPACE BAR again to stop)     ")
                else:
                    counting = False
                    print("\r--> Counting STOPPED.")
                    
                    print("\n=== Counting Period Results ===")
                    total_balls = 0
                    for pin in GPIO_PINS:
                        count = counters[pin]
                        print(f"GPIO {pin}: {count} balls")
                        total_balls += count
                    
                    print("-" * 31)
                    
                    # --- NEW ASCII ART OUTPUT ---
                    # The 'block' font is thick and highly readable from a distance
                    ascii_art = pyfiglet.figlet_format(str(total_balls), font="bigmono9")
                    print("\nFINAL COUNT:")
                    print(ascii_art)
                    print("===============================\n")
                    
                    print("Press the SPACE BAR to START a new counting period, or 'q' to quit.")

    except KeyboardInterrupt:
        print("\nExiting program...")

if __name__ == "__main__":
    main()
