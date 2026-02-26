frc2026/
│
├─ main.py                  # Entry point
├─ config.json              # Configuration file (different node should have different config file)
│
├─ frc_node/
│   ├─ __init__.py
│   ├─ node.py              # Main FRC2026Node class
│   ├─ networking.py        # Server/Client networking
│   ├─ hub.py               # HUB loop control (LEDs, GPIO, sensors)
│   ├─ led.py               # HUB LEDs
│   ├─ sound.py             # SoundManager for cues
│   ├─ button.py            # PanicButton
│   ├─ gui_config.py        # ConfigGUI
│   └─ gui.py               # ScoreboardGUI
│

└─ wav_files/               # All sound files
Note: match_powerup.wav found from https://github.com/Team254/cheesy-arena/commit/19f168147710f02d770495f09c15399ac2e88268


The Full "Double Handshake" Flow
This creates a very robust chain of events during those first 10 seconds:
Hub → FMS: "Here is my ball count (e.g., 12)."
FMS → Hub: "Got it! (DATA_ACK)" — The Hub drive team breathes a sigh of relief.
FMS (after getting both): "Comparison complete. Blue won! (AUTO_RESULT:B)"
Hub → Hardware: Switches to Table 6-3 behavior based on being the winner or loser.

In hub_loop, if FMS doesn't receive the DATA_ACK within 2 seconds of sennding ball count, 
the Hub re-send the message. 
This ensures the FMS eventually gets the data even if there was a momentary signal drop.


