from config import *
from selfcheck import selfcheck_system, selfcheck_module

selfcheck_system(SYSTEM_FILES)

import time
import hashlib
import getpass
import platform
from termcolor import colored
# colored('This is some strings.', color='red') # color:['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
# magenta: 淡紫, cyan: 淡蓝
from loguru import logger
from setuptools.errors import PlatformError
from loading import load, load_login_database
from services import startService_linux, startService_win32
from terminal import terminal
from tools.Passwd.process import encrypt
from tools.__built_in__.TSLlogger import Logger
from tools.__built_in__.GetInfo import GetResourcePath
Logger()

if not SYSTEM_LOGSTDOUT:
    logger.remove(handler_id=None)

system_logger = logger.add(os.path.join(SYSTEM_LOGPATH, "log_{time:YYYY-MM}.log"),
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
login_datas = load_login_database(os.path.join(SYSTEM_DIR, 'Database/login.db'))
login_infos = login_datas[0]
mode_info = login_datas[1]
admin_users = login_datas[2]
simple_users = login_datas[3]
print('done.')
logger.info("Successfully load Login Database.")

print("")
os.system(f'{SYSTEM_PRINTER} {GetResourcePath("motd")}')
print("")

while True:
    while True:
        passwd_processor = hashlib.md5()

        username = input("Username: ")
        if username in mode_info['user'] or username in mode_info['root']:
            passwd = getpass.getpass("Password: ").strip()
            passwd = passwd.encode(encoding='utf-8')
            passwd_processor.update(passwd)
            passwd = passwd_processor.hexdigest()

            if encrypt(passwd, 3, SYSTEM_ID[:6]) == login_infos.get(f"{username}@{'root' if username in admin_users else 'user'}").strip():
                logger.info("Successfully log in the system. [USERINFO:('{user}')]", user=username)
                print(colored('Successfully log in the system!\n', color="green"))
                break
            else:
                logger.error("Wrong password to user. [USERINFO:('{user}')]", user=username)
                print(colored(f"The password to '{username}' is wrong!\n", color="red"))
                while True:
                    del passwd, passwd_processor
                    passwd_processor = hashlib.md5()
                    passwd = getpass.getpass("Password: ").strip()
                    passwd = passwd.encode(encoding='utf-8')
                    passwd_processor.update(passwd)
                    passwd = passwd_processor.hexdigest()

                    if encrypt(passwd, 3, SYSTEM_ID[:6]) == login_infos.get(f"{username}@{'root' if username in admin_users else 'user'}").strip():
                        logger.info("Successfully log in the system. [USERINFO:('{user}')]", user=username)
                        print(colored('Successfully login the system!\n', color="green"))
                        break
                    else:
                        logger.error("Wrong password to user. [USERINFO:('{user}')]", user=username)
                        print(colored(f"The password to '{username}' is wrong!\n", color="red"))
                break
        else:
            logger.error("UserNotExistedError:no such user named '{user}' was found in login database.", user=username)
            print(colored(f"UserNotExistedError:no such user named '{username}' was found in login database.\n",
                          color="red"
                          ))

    logger.info("System Terminal start running.")
    syscode = terminal(USERNAME=username, MODE='$' if username in mode_info['user'] else '#', Bin_DIR=Bin_DIR)
    if syscode == -1:
        logger.info(f"Terminal returned syscode but nothing will happen. [syscode: {syscode}]")
        logger.info(f'The user "{username}" has logged out.')
        time.sleep(2)
        os.system(SYSTEM_CLEARSTDOUT)
        print('')
        login_datas = load_login_database(os.path.join(SYSTEM_DIR, 'Database/login.db'))
        login_infos = login_datas[0]
        mode_info = login_datas[1]
        admin_users = login_datas[2]
        simple_users = login_datas[3]
        os.system(f'{SYSTEM_PRINTER} {GetResourcePath("motd")}')
        print('')
        continue
    elif not syscode:
        logger.info("System shutdown normally.")
        break
    elif not -31 <= syscode <= 32:
        logger.error(f"invaild syscode. [syscode: {syscode}]")
        logger.warning("System shutdown with invaild syscode.")
        break
    else:
        logger.info(f"Terminal returned syscode but nothing will happen. [syscode: {syscode}]")
        logger.info("System shutdown normally.")
        break
