#  Copyright (c) 2024. L.J.Afres, All rights reserved.
from termcolor import colored
# textblob：情感分析

"""
    load [modules]
    
"""


def run():
    print('-'*36)
    print('|    TSL-SYSTEM Psychology Module    |')
    print('-'*36)

    while True:
        cmd = input(colored('[Psychology]', color='light_cyan') + ' >> ').strip()
        if cmd == 'exit':
            break