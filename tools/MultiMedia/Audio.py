#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import os
import playsound
from config import null, istermux


class AudioPlayer:
    def __init__(self):
        self.null = null

    def play(self, filename):
        if istermux:
            os.system(f"termux-media-player play {filename} > {self.null}")
        else:
            playsound.playsound(filename)

