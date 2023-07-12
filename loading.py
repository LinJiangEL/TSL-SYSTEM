import gc
import sys
import time
import importlib
from config import SYSTEM_DIR


def load(module):
    path = f'{SYSTEM_DIR}/modules/{module}'
    print('done')
    time.sleep(0.5)
    return open(path, 'r')


def start(tool):
    try:
        print('')
        # exec(f"from tools.{tool}.main import run;run();")
        module = importlib.import_module(f"tools.{tool}.main")
        getattr(module, "run")()
        if module.__name__ in sys.modules:
            del sys.modules[module.__name__]
            del module
            gc.collect()
    except ModuleNotFoundError:
        print(f"ModuleNotFoundError:cannot found '{tool}' from the tools folder!\n")
    except SystemExit:
        print(f"Stopping {tool} service.\n")
        time.sleep(1)
