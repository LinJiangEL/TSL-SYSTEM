#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

import os
import playsound
from config import null, istermux
from tools.__built_in__.external import run


class AudioPlayer:
    def __init__(self):
        self.null = null

    def play(self, filename):
        if istermux:
            run(['termux-media-player', 'play', filename], silent=True)
        else:
            playsound.playsound(filename)


class MIDI:
    def __init__(self):
        pass

    
