#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

import os
from config import Tools_DIR
from termcolor import colored

mediadir = os.path.join(Tools_DIR, 'media')


def run():
    print('-'*38)
    print('|    TSL-SYSTEM MultiMedia Module    |')
    print('-'*38)

    while True:
        cmd = input(colored("> ")).strip()
        if cmd == '':
            continue
        if cmd == 'exit':
            break

        if cmd == 'convert':
            """convert --type ..."""
            pass
