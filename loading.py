#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import gc
import sys
import time
import importlib
from loguru import logger


def load_user_database(databasefile):
    """加载用户数据库。"""
    login_infos = {}
    mode_info = {}
    admin_users = []
    simple_users = []
    with open(databasefile, 'r') as login_file:
        for login_info in login_file.readlines():
            if login_info.startswith('#') or login_info.strip() == '':
                continue
            else:
                username_mode, hash_passwd = tuple(login_info.split(':'))
                login_infos[username_mode] = hash_passwd
                if username_mode.split('@')[1] == 'root':
                    admin_users.append(username_mode.split('@')[0])
                elif username_mode.split('@')[1] == 'user':
                    simple_users.append(username_mode.split('@')[0])
                else:
                    logger.critical("OSError:Login Database cannot be normally read.")
                    logger.error("System shutdown with Exceptions.")
                    raise OSError('login.db cannot be normally read!')

                mode_info['root'] = admin_users
                mode_info['user'] = simple_users
        login_file.close()

    return [login_infos, mode_info, admin_users, simple_users]


def start(tool):
    """启动系统工具。"""
    try:
        print('')
        # exec(f"from tools.{tool}.main import run;run();")
        module = importlib.import_module(f"tools.{tool}.main")
        getattr(module, "run")()
        if module.__name__ in sys.modules:
            del sys.modules[module.__name__]
            del module
            gc.collect()
        else:
            gc.collect()
    except ModuleNotFoundError as e:
        print(f"ModuleNotFoundError:{e}.")
        print(f"ImportError:cannot import '{tool}' from the tools folder!\n")
    except SystemExit:
        print(f"Stopping {tool} service.\n")
        time.sleep(1)
