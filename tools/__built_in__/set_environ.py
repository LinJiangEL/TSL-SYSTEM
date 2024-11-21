#  Copyright (c) 2024. L.J.Afres, All rights reserved.
import os
import sys
import warnings
warnings.filterwarnings('ignore')
if sys.platform == 'win32':
    import winreg
from setuptools.errors import PlatformError

def set_env_variable(name, value):
    """设置系统环境变量。"""
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