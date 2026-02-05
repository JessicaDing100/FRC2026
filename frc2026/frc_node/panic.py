import platform

class PanicButton:
    def __init__(self,node):
        self.node=node

    def start_listener(self):
        system=platform.system()
        if system=="Windows":
            try:
                import pywinusb.hid as hid
            except ImportError:
                print("[FMS] pywinusb not installed. USB panic disabled.")
                return
            devices=hid.find_all_hid_devices()
            if not devices:
                print("[FMS] No HID devices found. USB panic disabled.")
                return
            device=devices[0]
            device.open()
            print(f"[FMS] Listening for USB panic on {device.vendor_name}-{device.product_name}")
            def handler(data):
                if data[0]!=0:
                    print("[FMS] USB Panic pressed!")
                    self.node.panic_event.set()
                    self.node.sound_manager.play_cue("STOP")
                    self.node.networking.broadcast("GAME_STOP")
            device.set_raw_data_handler(handler)
        else:
            try:
                import keyboard
                print("[FMS] Keyboard 'p' key used as panic button")
                keyboard.wait('p')
                self.node.panic_event.set()
                self.node.sound_manager.play_cue("STOP")
                self.node.networking.broadcast("GAME_STOP")
            except ImportError:
                print("[FMS] No panic button available")
