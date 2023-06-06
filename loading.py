import time
from config import SYSTEM_DIR


def load(module):
    path = f'{SYSTEM_DIR}/modules/{module}'
    print('done')
    time.sleep(0.5)
    return open(path, 'r')


def start(tool):
    try:
        print('')
        exec(f"from tools.{tool}.main import run;run();")
    except ModuleNotFoundError:
        print(f"ModuleNotFoundError:cannot found '{tool}' from the tools folder!\n")
    except SystemExit:
        print(f"Stopping {tool} service.\n")
        time.sleep(1)

