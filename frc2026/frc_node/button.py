import os
import time
import threading
import usb.core
import usb.util
import usb.backend.libusb1

class USBPanicButton:
    def __init__(self, vendor_id=0x8088, product_id=0x0015):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.signature = [102, 204, 3, 0, 1, 9]
        self.dev = None
        self.dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libusb-1.0.dll')
        self._initialize_device()

    def _initialize_device(self):
        try:
            backend = usb.backend.libusb1.get_backend(find_library=lambda x: self.dll_path)
            self.dev = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id, backend=backend)
            if self.dev:
                self.dev.reset()
                self.dev.set_configuration()
                usb.util.claim_interface(self.dev, 0)
                print("✅ Physical Button: Hardware Linked.")
            else:
                print("⚠️ Physical Button: NOT FOUND.")
        except Exception as e:
            print(f"❌ Button Init Error: {e}")

    def start_listening(self, callback):
        if self.dev:
            # We run the listener in a daemon thread so it dies when the FMS closes
            threading.Thread(target=self._listener_loop, args=(callback,), daemon=True).start()

    def _listener_loop(self, callback):
        while True:
            try:
                # Read from endpoint 0x81 as discovered
                data = self.dev.read(0x81, 128, timeout=500)
                
                if list(data[:6]) == self.signature:
                    # Execute the FMS command
                    callback()
                    
                    # --- THE PLUNGER ---
                    # Drain the 0x81 buffer so we don't get 'Errno 132 Overflow'
                    try:
                        while True: self.dev.read(0x81, 128, timeout=10)
                    except: pass 
                    
                    time.sleep(0.3) # Debounce to prevent double-triggers
            except usb.core.USBError as e:
                if e.errno == 10060: continue # Normal timeout
                if e.errno == 132: continue   # Overflow handled
                print(f"❌ USB Thread Stopped: {e}")
                break