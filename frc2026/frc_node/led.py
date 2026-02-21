class LedManager:
    def __init__(self, led_count=150):
        self.led_count = led_count
        self.model = self._get_pi_model()
        # Both are using GPIO 10 (Physical Pin 19)
        if self.model == 5:
            from pi5neo import Pi5Neo
            # Pass the specific SPI path and frequency for Pi 5
            self.pixels = Pi5Neo('/dev/spidev0.0', self.led_count, 800)
        else:
            import board
            import neopixel
            # Pi 4 handles the 800kHz and SPI path via the board.MOSI object
            self.pixels = neopixel.NeoPixel(board.MOSI, self.led_count, auto_write=False)

    def _get_pi_model(self):
        try:
            with open('/proc/device-tree/model', 'r') as f:
                return 5 if 'Raspberry Pi 5' in f.read() else 4
        except:
            return 4

    def fill(self, r, g=None, b=None):
        # If the first argument is a tuple/list, unpack it
        if isinstance(r, (tuple, list)):
            r, g, b = r
    
        if self.model == 5:
            self.pixels.fill_strip(r, g, b)
            self.pixels.update_strip()
        else:
            self.pixels.fill((r, g, b))
            self.pixels.show()

#Note: Pi 4 does not work consistently
# We need to try the suggestion in the following thread and see
#https://chatgpt.com/share/69918208-3bec-8005-9b38-0cdb894acf47