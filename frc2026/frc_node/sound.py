import os
import pygame

class SoundManager:
    def __init__(self, cfg):
        pygame.mixer.init()
        self.sounds = {}
        base_path=os.path.join(os.path.dirname(__file__),"../wav_files")
        sound_files={
            "START": "start_CalvaryCharge.wav",
            "END_AUTO": "end_Buzzer.wav",
            "TELEOP": "resume_Bells.wav",
            "SHIFT": "PowerUpReplacement.wav",
            "WHISTLE": "warning_SteamWhistle.wav",
            "ENDGAME": "Buzzer.wav",
            "STOP": "Foghorn.wav"
        }
        for key,fname in sound_files.items():
            path=os.path.join(base_path,fname)
            if os.path.isfile(path):
                self.sounds[key]=pygame.mixer.Sound(path)
            else:
                print(f"[WARNING] Sound file missing: {fname}")

    def play_cue(self,name):
        if name in self.sounds:
            self.sounds[name].play()
