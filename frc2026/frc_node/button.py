import threading
from evdev import InputDevice, categorize, ecodes

class USBPanicButton:
    def __init__(self):
        #ToDo: move this path to config file?
        self.device_path = '/dev/input/by-id/usb-LinTx_LinTx_Keyboard_BE2F48FE-if01-event-kbd'
        self.dev = None
        self._initialize_device()

    def _initialize_device(self):
        try:
            self.dev = InputDevice(self.device_path)
            # 'grab' hides the keypress from the rest of the OS (terminal/desktop)
            self.dev.grab() 
            print(f"✅ Button Linked: {self.dev.name}")
        except Exception as e:
            print(f"❌ Connection Error: {e}")

    def start_listening(self, callback):
        if self.dev:
            threading.Thread(target=self._listener_loop, args=(callback,), daemon=True).start()

    def _listener_loop(self, callback):
        for event in self.dev.read_loop():
            # EV_KEY is a keyboard event
            if event.type == ecodes.EV_KEY:
                key_event = categorize(event)
                # keystate 1 means 'pressed down'
                if key_event.keystate == 1:
                    callback()
