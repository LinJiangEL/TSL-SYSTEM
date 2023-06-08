from config import *
from selfcheck import selfcheck_system, selfcheck_module

selfcheck_system(SYSTEM_FILES)

import time
import hashlib
import getpass
import platform
# from termcolor import colored
# colored('This is some strings.', color='red') # color:['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
from loguru import logger
from setuptools.errors import PlatformError
from loading import load
from services import startService_linux, startService_win32
from terminal import terminal
from tools.Passwd.process import encrypt

if not SYSTEM_LOGSTDOUT:
    logger.remove(handler_id=None)

system_logger = logger.add(os.path.join(SYSTEM_LOGPATH, "log-{time:YYYY-MM}.log"),
                           format=SYSTEM_LOGFORMAT,
                           level="DEBUG",
                           rotation="32 MB",
                           enqueue=True
                           )

logger.info("System start running.")
logger.info("GetSystemPlatform() returned: {SysVersion}.", SysVersion=platform.platform())

logger.info("System selfcheck start running.")
runrequire_modules = open(requirements_file, 'r')
for item in runrequire_modules.readlines():
    item = item.strip()
    if not selfcheck_module(item):
        runrequire_modules.close()
        logger.critical("ModuleNotFoundError:module {item} is missing!", item=item)
        logger.info("System selfcheck has done, but system cannot normally start.")
        logger.info("System shutdown.")
        raise ModuleNotFoundError(f"module {item} is missing!")
    time.sleep(0.1)
runrequire_modules.close()

runrequire_win32services = []
runrequire_linuxservices = []
if sys.platform == 'win32':
    win32_platform = platform.platform()
    if 'Windows' in win32_platform and int(win32_platform.split('-')[1]) >= 10:
        startService_win32(runrequire_win32services)
    elif 'Windows' in win32_platform and win32_platform.split('-')[1] == 7:
        logger.warning("PlatformWarning:your system version is too old, it may broken on your computer.")
        print('\033[33mPlatformWarning:your system version is too old, it may broken on your computer.\033[0m')
        startService_win32(runrequire_win32services)
    else:
        logger.critical("PlatformError:cannot start TSL-SYSTEM on your computer! [VersionNotSupport]")
        logger.info("System shutdown.")
        raise PlatformError('cannot start TSL-SYSTEM on your computer! [VersionNotSupport]')
elif sys.platform == 'linux':
    startService_linux(runrequire_linuxservices)
else:
    logger.critical("PlatformError:TSL-SYSTEM can only run on win32 or linux platform, but yours is %s!" % sys.platform)
    logger.info("System shutdown with Exceptions.")
    raise PlatformError('TSL-SYSTEM can only run on win32 or linux platform, but yours is %s.' % sys.platform)

logger.info("System selfcheck has done.")
print('System Self Checking has done!\n')
time.sleep(0.3)

print('Loading Finite Element Module (FEM) ... ', end='', flush=True)
load('FEM.h')
logger.info("Successfully load Finite Element Module (FEM).")

print('Loading Finite Difference Module (FDM) ... ', end='', flush=True)
load('FDM.h')
logger.info("Successfully load Difference Module (FDM).")

print('Loading Login Database ... ', end='', flush=True)
login_infos = {}
mode_info = {}
admin_users = []
simple_users = []
with open(os.path.join(SYSTEM_DIR, 'Database/login.db'), 'r') as login_file:
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
                raise OSError('login.db cannot be normally read!')

            mode_info['root'] = admin_users
            mode_info['user'] = simple_users
    login_file.close()

print('done.')
logger.info("Successfully load Login Database.")

print("")
os.system(f'{SYSTEM_PRINTER} motd')
print("")

while True:
    passwd_processor = hashlib.md5()

    username = input("Username: ")
    if username in mode_info['user'] or username in mode_info['root']:
        passwd = getpass.getpass("Password: ")
        passwd = passwd.encode(encoding='utf-8')
        passwd_processor.update(passwd)
        passwd = passwd_processor.hexdigest()

        if encrypt(passwd, 3, SYSTEM_ID[:6]) == login_infos.get(
                f"{username}@{'root' if username in admin_users else 'user'}").strip():
            logger.info("Successfully log in the system. [USERINFO:{user}]", user=username)
            print('Successfully log in the system!\n')
            break
        else:
            logger.error("Wrong password to user. [USERINFO:{user}]", user=username)
            print(f"The password to '{username}' is wrong!\n")
            while True:
                del passwd, passwd_processor
                passwd_processor = hashlib.md5()
                passwd = getpass.getpass("Password: ")
                passwd = passwd.encode(encoding='utf-8')
                passwd_processor.update(passwd)
                passwd = passwd_processor.hexdigest()

                if encrypt(passwd, 3, SYSTEM_ID[:6]) == login_infos.get(
                        f"{username}@{'root' if username in admin_users else 'user'}").strip():
                    logger.info("Successfully log in the system. [USERINFO:{user}]", user=username)
                    print('Successfully login the system!\n')
                    break
                else:
                    print(f"The password to '{username}' is wrong!\n")
            break
    else:
        logger.error("UserNotExistedError:no such user named '{user}' was found in login database.", user=username)
        print(f"UserNotExistedError:no such user named '{username}' was found in login database.\n")

logger.info("System Terminal start running.")
terminal(USERNAME=username, MODE='$' if username in mode_info['user'] else '#', Bin_DIR=Bin_DIR)
logger.info("System Terminal hostdown.")
logger.info("System shutdown normally.")
