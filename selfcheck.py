#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import os
import io
import sys
import time
import wget
import contextlib
import platform
import subprocess
from config import SYSTEM_DIR

if sys.platform == 'win32':
    import win32api
    import win32con
from setuptools.errors import PlatformError


def selfcheck_system(systemfilelist):
    missing_systemfilelist = []
    print('Checking System files ... ', end='', flush=True)
    for rs in systemfilelist:
        if rs in os.listdir('.'):
            continue
        else:
            missing_systemfilelist.append(rs)
        time.sleep(3)
    if not missing_systemfilelist:
        print('done.\n')
    else:
        print('done.\nMissing System Files:')
        for r in missing_systemfilelist:
            print(r)
        print('')
        sys.exit(256)

    print('check python3 ... ', end='', flush=True)
    python_version = sys.version_info
    workdir = os.path.join(SYSTEM_DIR, "Temp/__prebuild__/")
    if python_version[0] >= 3 and python_version[1] >= 7:
        print('yes')
    else:
        print('no')
        print('PythonVersionNotSupport:TSL-SYSTEM required Python >= 3.9.2, '
              'if you want to use it, please update your Python!'
              )
        ask_updatePython = win32api.MessageBox(0,
                                               "Do you want to update your Python Environment?",
                                               "Update Python",
                                               win32con.MB_YESNO
                                               ) if sys.platform == "win32" else \
            subprocess.run(['zenity', '--question', '--text="Do you want to update your Python Environment?"'],
                           capture_output=True, text=True).returncode
        if ask_updatePython == 6 if sys.platform == 'win32' else 0:  # 6 -> yes, 0 -> yes
            os.chdir(workdir)
            print('Prefer to installing Python-3.9.7')
            if sys.platform == 'linux':
                wget.download('https://www.python.org/ftp/python/3.9.7/Python-3.9.7.tgz', out={workdir})
                os.system(f'tar -xzvf {workdir}/Python-3.9.7.tgz')
                install_to_path = input('Please input the path to install Python-3.9.7 [default: /usr/local]: ')
                os.system('cd Python-3.9.7 && ./configure --prefix='
                          f'{install_to_path if install_to_path != "" else "/usr/local"} && make && make install'
                          )
                os.chdir(SYSTEM_DIR) if python_version[0] >= 3 and python_version[1] >= 7 else \
                    exec("raise RuntimeError('failed to install python or cannot set it into the path.')")
            elif sys.platform == 'win32':
                bit = int(platform.architecture()[0][:2])
                if bit == 64:
                    wget.download('https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe', out=workdir)
                    os.system(f'start {workdir}/python-3.9.7-amd64.exe')
                    os.chdir(SYSTEM_DIR) if python_version[0] >= 3 and python_version[1] >= 7 else \
                        exec("raise RuntimeError('failed to install python or system cannot set it into the path.')")
                elif bit == 32:
                    wget.download('https://www.python.org/ftp/python/3.9.7/python-3.9.7.exe', out=workdir)
                    os.system(f'start {workdir}/python-3.9.7.exe')
                    os.chdir(SYSTEM_DIR) if python_version[0] >= 3 and python_version[1] >= 7 else \
                        exec("raise RuntimeError('failed to install python or cannot set it into the path.')")
                else:
                    os.chdir(SYSTEM_DIR)
                    raise SystemError('bits calculator has broken down!')
            else:
                os.chdir(SYSTEM_DIR)
                raise PlatformError('TSL-SYSTEM must run on the win32 or linux platform!')
        else:  # 7 -> no
            python_error_version = f'{python_version[0]}.{python_version[1]}.{python_version[2]}'
            raise RuntimeError(f'cannot load TSL-SYSTEM with Python-{python_error_version}!')


def check_command(command):
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def selfcheck_module(name: str):
    print('check %s ... ' % name.strip(), end='', flush=True)
    name = name.replace('-', '_')
    time.sleep(0.1)
    try:
        fake_stdout = io.StringIO()
        with contextlib.redirect_stdout(fake_stdout):
            exec(f"import {name}; del {name};")
        # Debug returned message
        # hidden_output = fake_stdout.getvalue()
        # print(hidden_output)
    except ImportError:
        print('no')
        return False
    else:
        print('yes')
        return True
