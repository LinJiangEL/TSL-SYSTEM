#  Copyright (c) 2024-2025. L.J.Afres, All rights reserved.

import os
import sys
import uuid
import warnings
warnings.filterwarnings('ignore')  # 忽视警告信息
import getpass
from cachetools import LRUCache
from termcolor import colored
from setuptools.errors import PlatformError
from loguru import logger
from tools.__built_in__.TSLlogger import Logger
from tools.__built_in__.GetInfo import GetResourcePath, get_packagemgr
from tools.__built_in__.set_environ import set_env_variable

Logger()

# 初始化系统设置
APIKEY_IDENTIFY = "TSL-SYSTEM-APIKEY" if sys.platform == 'win32' else "TSL_SYSTEM_APIKEY"
APIKEY = getpass.getpass("Please input the permission password: ") if os.getenv(APIKEY_IDENTIFY) is None else \
         os.getenv(APIKEY_IDENTIFY)
SYSTEM_ID = str(uuid.uuid3(uuid.NAMESPACE_X500, APIKEY))
SYSTEM_DIR = os.path.dirname(os.path.abspath(GetResourcePath(__file__)))
SYSTEM_FILES = ['bin', 'backup', 'Database', 'tools', 'Temp', 'loading.py',
                'config.py', 'services.py', 'upgrade.py', 'sysmgr.py', 'motd',
                'terminal.py', 'runrequirements.txt', 'README.md', 'README_CN.md', 'VERSION',
                'loading.py', 'motd', 'LICENSE', 'motd.jpg', 'selfcheck.py', 'system.py',
                'linuxrequirements.txt', 'win32requirements.txt'
                ]
SYSTEM_LOGPATH = os.path.join(SYSTEM_DIR, "Temp/logs")
SYSTEM_LOGFORMAT = "{time:YYYY-MM-DD HH:mm:ss} [{level}] {message}"
SYSTEM_STDOUT_LOGFORMAT = "<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> <level>[{level}]</level> <level>{message}</level>"
SYSTEM_LOGSTDOUT = not (os.getenv("LOGSTDOUT") is None or os.getenv("LOGSTDOUT") != '1')
if not os.path.exists(SYSTEM_LOGPATH):
    os.mkdir(SYSTEM_LOGPATH)
logger.remove()
stdIO = logger.add(sys.stderr,
                   colorize=True,
                   format=SYSTEM_STDOUT_LOGFORMAT,
                   level="INFO"
                   )
null = "NUL 2>&1" if sys.platform == "win32" else "/dev/null 2>&1"  # 使屏幕输出nul，即屏幕无输出
Tools_DIR = os.path.join(SYSTEM_DIR, 'tools')
SYSTEM_DIGMAX = 8
SuperUser = ['root']  # 设置'root'用户为系统最高管理者
SYSTEM_PRINTER = 'cat' if sys.platform == 'linux' else 'type' if sys.platform == 'win32' else 0
SYSTEM_CLEARSTDOUT = 'clear' if sys.platform == 'linux' else 'cls' if sys.platform == 'win32' else 0
CACHE = LRUCache(maxsize=64)  # 设置最大缓存数为 64
REFRESH_SWITCH = True
requirements_file = os.path.join(SYSTEM_DIR, f'{sys.platform}requirements.txt')
if not os.path.exists(os.path.join(SYSTEM_DIR, "Temp/PwdUser")):
    # 初始化用户登录缓存文件
    with open(os.path.join(SYSTEM_DIR, "Temp/PwdUser"), 'w') as pwd:
        pwd.write("0")

# 设置内置可执行文件的存放目录
if sys.platform in ['win32', 'linux']:
    Bin_DIR = os.path.join(SYSTEM_DIR, f"bin/{sys.platform}")
    sys.path.append(Bin_DIR)
else:
    raise PlatformError('TSL-SYSTEM can only run on the win32 or linux platform!')

if sys.platform == 'linux':
    packagemgr = get_packagemgr(["pkg", "apt", "yum", "dnf"])

ffmpeg_path = r"D:\ffmpeg\bin\ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"

# 如果系统类型是Linux, 则判断系统载体是否为Termux
if sys.platform == 'linux':
    istermux = True if "termux" in os.getcwd() or "com.termux" in os.environ["SHELL"] else False
else:
    istermux = False

# 加载帮助信息
help_keys = []
help_values = []
with open(os.path.join(SYSTEM_DIR, f'bin/{sys.platform}bin.help'), 'r') as binhelpdictfile:
    for line in binhelpdictfile.readlines():
        if line.strip().startswith('#') or line.strip() == '':
            continue
        else:
            help_keys.append(line.split(':')[0])
            help_values.append(line.split(':')[1])

HelpPages_DIR = os.path.join(SYSTEM_DIR, 'doc')
PageReader = os.path.join(Bin_DIR, 'more.exe') if sys.platform == 'win32' else 'more' if sys.platform == 'linux' else 0

# 初始化帮助信息
if sys.platform == 'win32':
    binhelp_win32dict = dict(zip(help_keys, help_values))
elif sys.platform == 'linux':
    binhelp_linuxdict = dict(zip(help_keys, help_values))
else:
    raise PlatformError('TSL-SYSTEM can only run on the win32 or linux platform!')

# 创建空目录，防止执行过程中抛出找不到文件的异常
emptyfiles = ['Temp/logs', 'backup/TSL-SYSTEM-BACKUP-FILES']
for emptyfile in emptyfiles:
    path = os.path.join(SYSTEM_DIR, emptyfile)
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        continue

# 正版验证 =m=
id_processor = __import__("hashlib").md5()
id_processor.update(str(SYSTEM_ID).encode(encoding="utf-8"))
id_md5 = id_processor.hexdigest()
print("Checking ... ", end='', flush=True)
if id_md5 != "22f6fbf8b9bcf38e12ba4cd9e2e3a7f8":
    print(colored('failed', color="red"))
    raise PermissionError("operation had been blocked because the password was incorrect.")
else:
    print(colored('ok', color="green"))
    if os.getenv(APIKEY_IDENTIFY) is None:
        set_env_variable(APIKEY_IDENTIFY, APIKEY)

del id_processor
