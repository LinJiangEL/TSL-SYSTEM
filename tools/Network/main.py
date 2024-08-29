#  Copyright (c) 2024. L.J.Afres, All rights reserved.

# socket, psutil, netifaces
import os
from config import Tools_DIR

available_modules = ["SendMessage"]
networkdir = os.path.join(Tools_DIR, "Network")


def run():
    print('-' * 37)
    print('|     TSL-SYSTEM Network Module     |')
    print('-' * 37)
    print('')
    choice = input('Please input the module name which you want to run. [@available] > ')
    if choice.strip() == '@available':
        print(f'The available modules as follows:')
        for module in available_modules:
            print(module)
    print('')
