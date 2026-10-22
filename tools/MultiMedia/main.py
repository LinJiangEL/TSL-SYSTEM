#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.
from tools.__built_in__ import style
from tools.__built_in__.IOProcessor import read_input

import os
from config import Tools_DIR
from termcolor import colored

mediadir = os.path.join(Tools_DIR, 'media')


def run():
    print('-'*38)
    style.banner('TSL-SYSTEM MultiMedia Module', width=37)
    print('-'*38)

    while True:
        cmd = read_input(colored("> "), 'terminal', strip=True)
        if cmd == '':
            continue
        if cmd == 'exit':
            break

        if cmd == 'convert':
            """convert --type ..."""
            pass
