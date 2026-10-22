#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.
from tools.__built_in__ import style

import os
from config import Tools_DIR

ctfdir = os.path.join(Tools_DIR, "CTF")


def run():
    style.banner('TSL-SYSTEM CTF Module', width=37)


