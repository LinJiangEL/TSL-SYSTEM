#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

from config import *
from selfcheck import selfcheck_system, selfcheck_module
# 检查是否有系统文件缺失
selfcheck_system(SYSTEM_FILES)

import time
import hashlib
import platform
from termcolor import colored
from loguru import logger
from setuptools.errors import PlatformError
from loading import load_user_database
from services import startService_linux, startService_win32
from terminal import terminal
from guard import get_guard
from tools.Passwd.process import encrypt
from tools.__built_in__.TSLlogger import Logger
from tools.__built_in__ import style
from tools.__built_in__.IOProcessor import read_input
from tools.__built_in__.external import display_file, clear_screen
from tools.__built_in__.GetInfo import GetResourcePath
Logger()

"""
 系统默认不会实时输出日志内容，如果有需要:
  ·Windows下请运行:
     set LOGSTDOUT=1
     python3 system.py
  ·Linux下请运行:
     LOGSTDOUT=1 python3 system.py
"""
if not SYSTEM_LOGSTDOUT:
    logger.remove(handler_id=None)

# 设置系统日志格式
system_logger = logger.add(os.path.join(SYSTEM_LOGPATH, "log_{time:YYYY-MM}.log"),
                           format=SYSTEM_LOGFORMAT,
                           level="DEBUG",
                           rotation="32 MB",
                           enqueue=True
                           )

logger.info("System start running.")
logger.info("GetSystemPlatform() returned: {SysVersion}.", SysVersion=platform.platform())

# 安装断点保护，保证系统在异常中断时留下详细日志
breakpoint_guard = get_guard()
breakpoint_guard.install()
logger.info(f"System process started. [PROCESSINFO:({os.getpid()}, "
            f"'{platform.python_version()}', '{platform.platform()}')]"
            )

# 执行系统依赖项自检
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
logger.info("System selfcheck has done.")
style.success('System Self Checking has done!')
print('')
time.sleep(0.3)

# 启动服务项
runrequire_win32services = []
runrequire_linuxservices = []
if sys.platform == 'win32':
    win32_platform = platform.platform()
    if 'Windows' in win32_platform and int(win32_platform.split('-')[1]) >= 10:
        startService_win32(runrequire_win32services)
    elif 'Windows' in win32_platform and win32_platform.split('-')[1] == 7:
        logger.warning("PlatformWarning:your system version is too old, it may broken on your computer.")
        style.warning('PlatformWarning:your system version is too old, it may broken on your computer.')
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

# 加载用户数据库
print(style.highlight('Loading Login Database ... ', 'cyan'), end='', flush=True)
login_datas = load_user_database(os.path.join(SYSTEM_DIR, 'Database/login.db'))
login_infos = login_datas[0]
mode_info = login_datas[1]
admin_users = login_datas[2]
simple_users = login_datas[3]
style.success('done.')
logger.info("Successfully load Login Database.")

print("")
display_file(GetResourcePath("motd"))  # 打印Logo标识
print("")

while True:
    while True:
        passwd_processor = hashlib.md5()

        username = read_input(style.label('Username'), 'username')
        if username in mode_info['user'] or username in mode_info['root']:
            passwd = read_input(style.label('Password'), 'password', secret=True).strip()
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
                    passwd = read_input(style.label('Password'), 'password',
                                        secret=True).strip()
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

    user_mode = '$' if username in mode_info['user'] else '#'
    logger.info(f"System Terminal start running. [USERINFO:('{username}', '{user_mode}')]")
    syscode = terminal(USERNAME=username, MODE=user_mode, Bin_DIR=Bin_DIR)
    if syscode == -1:
        # 用户注销
        logger.info(f"Terminal returned syscode but nothing will happen. [syscode: {syscode}]")
        logger.info(f'The user "{username}" has logged out.')
        style.info(f'The user "{username}" has logged out.')
        time.sleep(1)
        clear_screen()
        print('')
        login_datas = load_user_database(os.path.join(SYSTEM_DIR, 'Database/login.db'))
        login_infos = login_datas[0]
        mode_info = login_datas[1]
        admin_users = login_datas[2]
        simple_users = login_datas[3]
        display_file(GetResourcePath("motd"))
        print('')
        continue
    elif not syscode:
        # 正常退出
        style.success('System shutdown normally.')
        logger.info(f"System shutdown normally. [syscode: {syscode}]")
        break
    elif not -31 <= syscode <= 32:
        # 异常退出
        style.error('System shutdown with invalid syscode.')
        logger.error(f"invalid syscode. [syscode: {syscode}]")
        logger.warning("System shutdown with invalid syscode.")
        break
    else:
        # 未知情况退出
        style.muted(f'Terminal returned syscode but nothing will happen. [syscode: {syscode}]')
        style.success('System shutdown normally.')
        logger.info(f"Terminal returned syscode but nothing will happen. [syscode: {syscode}]")
        logger.info("System shutdown normally.")
        break

logger.info(f"System process exited. [PROCESSINFO:({os.getpid()}, 'bye')]")
