import os
import sys
import time
from config import SYSTEM_PRINTER

available_tools = ["SendMessage"]


def load(name):
    try:
        if name not in available_tools:
            raise ModuleNotFoundError
        exec(f'import tools.Network.{name}')
    except ModuleNotFoundError:
        print(f"ModuleNotFoundError:cannot found '{name}' from folders! Maybe it is not available.\n")
    except SystemExit:
        print(f"Stopping {name} module.\n")
        time.sleep(1)


def title():
    print('-' * 37)
    print('|     TSL-SYSTEM Network Module     |')
    print('-' * 37)
    print('')


def run():
    print(f'The available modules as follows:')
    for a_tool in available_tools:
        print(a_tool)
    print('')

    title()
    while True:
        print('Please input the fullname of module which you want to use: ')
        module_choice = input('> ')
        if module_choice == 'exit':
            print('Stopping Network Tool ...')
            time.sleep(3)
            if sys.platform == 'win32':
                os.system(f'cls && echo. && {SYSTEM_PRINTER} motd && echo.')
            elif sys.platform == 'linux':
                os.system(f'clear && echo && {SYSTEM_PRINTER} motd && echo')
            break
        load(module_choice)
