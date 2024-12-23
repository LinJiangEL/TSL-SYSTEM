#  Copyright (c) 2024. L.J.Afres, All rights reserved.

from termcolor import colored
from tools.__built_in__.IOProcessor import InputProcessor
# textblob：情感分析

"""
    load [models]
    reload [models]
    run [module]
"""


def run():
    print('-'*36)
    print('|    TSL-SYSTEM Psychology Module    |')
    print('-'*36)

    while True:
        cmd = input(colored('[Psychology]', color='light_cyan') + ' >> ').strip()
        _cmd_tmp = [__tmp.strip() for __tmp in cmd.split(' ') if __tmp]
        _maincmd = _cmd_tmp[0]
        if cmd == 'exit':
            break
            