import os
import sys
import platform
import subprocess
from config import SYSTEM_DIR
from setuptools.errors import PlatformError

python_version = sys.version_info
workdir = os.path.join(SYSTEM_DIR, "Temp/__prebuild__/")
os.chdir(workdir)
os.system("python3 -m pip install -U pip setuptools wheel termcolor")

from termcolor import colored

if sys.platform == 'win32':
    requirementsfile = open(os.path.join(SYSTEM_DIR, "win32requirements.txt"), 'r')
    win32_requirements = [name.strip('\n ') for name in requirementsfile.readlines()
                          if name.strip('\n ') not in ['', 'win32', 'win32api', 'win32con']] + ["pywin32", "pypiwin32"]

    for module in win32_requirements:
        print(colored(f"Installing {module}", color='magenta'))
        print()
        os.system(f'pip install {module} -f {os.path.join(workdir, sys.platform)}')

    os.chdir(os.path.join(workdir, "sources"))
    os.system("tar -xzvf *.gz && unzip *.zip")
    for file in [d for d in os.listdir('.') if os.path.isdir(d)]:
        print(colored(f"Compiling {file.split('-')[0]}", color='magenta'))
        os.system(f"cd {file} && python3 setup.py build && python3 setup.py install")
elif sys.platform == 'linux':
    from config import packagemgr
    if packagemgr is not None:
        os.system(f"{packagemgr} update && {packagemgr} upgrade && {packagemgr} install -y zenity")
    else:
        sys.exit("System Package Manager cannot be found in the path, "
                 "please install 'apt' or 'yum' or feedback this problem to us. "
                 f"Your system version is {platform.platform()}."
                 )

    linux_requirements = [name.strip('\n ') for name in open(os.path.join(SYSTEM_DIR, "linuxrequirements.txt"), 'r'
                                                             ).readlines() if name.strip('\n ') != '']
    for module in linux_requirements:
        print(colored(f"Installing {module}", color='magenta'))
        print()
        os.system(f'pip install {module} -f {os.path.join(workdir, sys.platform)}')

    os.chdir(os.path.join(workdir, "sources"))
    os.system("tar -xzvf *.gz && unzip *.zip")
    for file in [d for d in os.listdir('.') if os.path.isdir(d)]:
        print(colored(f"Compiling {file.split('-')[0]}", color='magenta'))
        os.system(f"cd {file} && python3 setup.py build && python3 setup.py install")
else:
    raise PlatformError('TSL-SYSTEM can only run on win32 or linux platform, but yours is %s.' % sys.platform)

import wget
if sys.platform == "win32":
    import win32con

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
        print('Prefer to installing Python-3.9.7')
        if sys.platform == 'linux':
            wget.download('https://www.python.org/ftp/python/3.9.7/Python-3.9.7.tgz', out={workdir})
            os.system(f'tar -xzvf {workdir}/Python-3.9.7.tgz')
            install_to_path = input('Please input the path to install Python-3.9.7 [default: /usr/local]: ')
            os.system('cd Python-3.9.7 && ./configure --prefix='
                      f'{install_to_path if install_to_path != "" else "/usr/local"} && make && make install'
                      )
        elif sys.platform == 'win32':
            bit = int(platform.architecture()[0][:2])
            if bit == 64:
                wget.download('https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe', out=workdir)
                os.system(f'start {workdir}/python-3.9.7-amd64.exe')
            elif bit == 32:
                wget.download('https://www.python.org/ftp/python/3.9.7/python-3.9.7.exe', out=workdir)
                os.system(f'start {workdir}/python-3.9.7.exe')
            else:
                raise SystemError('bits calculator has broken down!')
        else:
            raise PlatformError('TSL-SYSTEM must run on the win32 or linux platform!')
    else:  # 7 -> no
        python_error_version = f'{python_version[0]}.{python_version[1]}.{python_version[2]}'
        raise RuntimeError(f'cannot load TSL-SYSTEM with Python-{python_error_version}!')
