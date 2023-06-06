from config import *
from selfcheck import selfcheck_system, selfcheck_module
selfcheck_system(SYSTEM_FILES)

import time
import hashlib
import getpass
import platform
# from termcolor import colored
# colored('This is some strings.', color='red') # color:['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
from setuptools.errors import PlatformError
from loading import load
from services import startService_linux, startService_win32
from terminal import terminal
from tools.Passwd.process import encrypt

runrequire_modules = open(requirements_file, 'r')
for item in runrequire_modules.readlines():
    item = item.strip()
    if not selfcheck_module(item):
        runrequire_modules.close()
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
        print('\033[33mPlatformWarning:your system version is too old, it may broken on your computer.\033[0m')
        startService_win32(runrequire_win32services)
    else:
        raise PlatformError('cannot start TSL-SYSTEM on your computer! Your computer is too old!')
elif sys.platform == 'linux':
    startService_linux(runrequire_linuxservices)
else:
    raise PlatformError('TSL-SYSTEM can only run on the win32 or linux platform!')

print('System Self Checking has done!\n')
time.sleep(0.3)

print('Loading Finite Element Module (FEM) ... ', end='', flush=True)
load('FEM.h')

print('Loading Finite Difference Module (FDM) ... ', end='', flush=True)
load('FDM.h')

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
            print('Successfully login the system!\n')
            break
        else:
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
                    print('Successfully login the system!\n')
                    break
                else:
                    print(f"The password to '{username}' is wrong!\n")
            break
    else:
        print(f"UserNotExistedError:no such user named '{username}' was found in login database.\n")

terminal(USERNAME=username, MODE='$' if username in mode_info['user'] else '#', Bin_DIR=Bin_DIR)
