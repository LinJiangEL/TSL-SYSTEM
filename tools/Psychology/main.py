#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.
from tools.__built_in__ import style
from tools.__built_in__.IOProcessor import read_input
from termcolor import colored
# textblob：情感分析

"""
    load [modules]
    
"""


def run():
    print('-'*36)
    style.banner('TSL-SYSTEM Psychology Module', width=37)
    print('-'*36)

    while True:
        cmd = read_input(style.prompt('[Psychology]', color='light_cyan'),
                         'terminal', strip=True)
        if cmd == 'exit':
            break