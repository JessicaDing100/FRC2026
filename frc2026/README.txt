frc2026/
│
├─ main.py                  # Entry point
├─ config.json              # Configuration file (different node should have different config file)
│
├─ frc_node/
│   ├─ __init__.py
│   ├─ node.py              # Main FRC2026Node class
│   ├─ networking.py        # Server/Client networking
│   ├─ hardware.py          # HUB hardware (LEDs, GPIO, sensors)
│   ├─ sound.py             # SoundManager for cues
│   ├─ gui.py               # ScoreboardGUI
│   └─ panic.py             # PanicButton (USB / keyboard)
│
└─ wav_files/               # All sound files