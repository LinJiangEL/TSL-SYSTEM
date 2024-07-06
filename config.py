import os
import sys
import uuid
import warnings
warnings.filterwarnings('ignore')
if sys.platform == 'win32':
    import winreg
import getpass
import math
from cachetools import LRUCache
from termcolor import colored
from setuptools.errors import PlatformError
from loguru import logger
from tools.__built_in__.TSLlogger import Logger
from tools.__built_in__.GetInfo import GetResourcePath

Logger()
SYSTEM_FILES = ['bin', 'backup', 'Database', 'tools', 'modules', 'Temp', 'loading.py', 'selfcheck.py', 'system.py',
                'config.py', 'services.py',
                'upgrade.py', 'sysmgr.py', 'motd', 'terminal.py', 'linuxrequirements.txt', 'win32requirements.txt',
                'loading.py', 'motd', 'LICENSE',
                'motd.jpg', 'README.md', 'VERSION']

APIKEY_IDENTIFY = "TSL-SYSTEM-APIKEY" if sys.platform == 'win32' else "TSL_SYSTEM_APIKEY"
APIKEY = getpass.getpass("Please input the permission password: ") if os.getenv(APIKEY_IDENTIFY) is None else \
         os.getenv(APIKEY_IDENTIFY)
SYSTEM_ID = str(uuid.uuid3(uuid.NAMESPACE_X500, APIKEY))
SYSTEM_DIR = os.path.dirname(os.path.abspath(GetResourcePath(__file__)))
SYSTEM_LOGPATH = os.path.join(SYSTEM_DIR, "Temp/logs")
SYSTEM_LOGFORMAT = "{time:YYYY-MM-DD HH:mm:ss} [{level}] {message}"
SYSTEM_STDOUT_LOGFORMAT = "<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> <level>[{level}]</level> <level>{message}</level>"
SYSTEM_LOGSTDOUT = os.getenv("SYSTEM_LOGSTDOUT") is None
if not os.path.exists(SYSTEM_LOGPATH):
    os.mkdir(SYSTEM_LOGPATH)
logger.remove()
stdIO = logger.add(sys.stderr,
                   colorize=True,
                   format=SYSTEM_STDOUT_LOGFORMAT,
                   level="INFO"
                   )
null = "NUL 2>&1" if sys.platform == "win32" else "/dev/null 2>&1"
Tools_DIR = os.path.join(SYSTEM_DIR, 'tools')
SYSTEM_DIGMAX = 8
SuperUser = ['root']
SYSTEM_PRINTER = 'cat' if sys.platform == 'linux' else 'type' if sys.platform == 'win32' else 0
SYSTEM_CLEARSTDOUT = 'clear' if sys.platform == 'linux' else 'cls' if sys.platform == 'win32' else 0
CACHE = LRUCache(maxsize=64)
requirements_file = os.path.join(SYSTEM_DIR, f'{sys.platform}requirements.txt')
if not os.path.exists(os.path.join(SYSTEM_DIR, "Temp/PwdUser")):
    with open(os.path.join(SYSTEM_DIR, "Temp/PwdUser"), 'w') as pwd:
        pwd.write("0")


def get_packagemgr(mgrlist):
    from selfcheck import check_command

    for manager in mgrlist:
        if check_command(manager):
            return manager
    return None


if sys.platform in ['win32', 'linux']:
    Bin_DIR = os.path.join(SYSTEM_DIR, f"bin/{sys.platform}")
    sys.path.append(Bin_DIR)
else:
    raise PlatformError('TSL-SYSTEM can only run on the win32 or linux platform!')

ffmpeg_path = r"D:\ffmpeg\bin\ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"

if sys.platform == 'linux':
    packagemgr = get_packagemgr(["pkg", "apt", "yum", "dnf"])

if sys.platform == 'linux':
    istermux = True if "termux" in os.getcwd() or "com.termux" in os.environ["SHELL"] else False
else:
    istermux = False

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

if sys.platform == 'win32':
    binhelp_win32dict = dict(zip(help_keys, help_values))
elif sys.platform == 'linux':
    binhelp_linuxdict = dict(zip(help_keys, help_values))
else:
    raise PlatformError('TSL-SYSTEM can only run on the win32 or linux platform!')

efiles = ['Temp/logs', 'backup/TSL-SYSTEM-BACKUP-FILES']
for efile in efiles:
    path = os.path.join(SYSTEM_DIR, efile)
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        continue


def set_env_variable(name, value):
    if sys.platform == 'win32':
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
        winreg.CloseKey(key)
    elif sys.platform == 'linux':
        home = os.getenv("HOME")
        if os.path.exists(os.path.join(home, '.zshrc')):
            with open(os.path.join(home, '.zshrc'), 'a') as envir:
                envir.write(f'\nexport "{name}"={value}')
                envir.close()
        else:
            with open(os.path.join(home, '.zshrc'), 'w') as envir:
                envir.write(f'\nexport "{name}"={value}')
                envir.close()
        os.system(f'export "{name}"={value}')
    else:
        raise PlatformError('TSL-SYSTEM can only run on the win32 or linux platform!')


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
