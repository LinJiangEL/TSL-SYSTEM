#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

import os
import sys
import glob
import shutil
import platform
import subprocess
from config import SYSTEM_DIR
from setuptools.errors import PlatformError

python_version = sys.version_info
workdir = os.path.join(SYSTEM_DIR, "Temp/__prebuild__/")
os.chdir(workdir)
subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', 'pip', 'setuptools', 'wheel', 'termcolor'])

from termcolor import colored


def unpack_sources(directory):
    """解压目录里的源码包，替代原来的 'tar -xzvf *.gz && unzip *.zip'。"""
    for pattern in ('*.gz', '*.zip'):
        for archive in glob.glob(os.path.join(directory, pattern)):
            shutil.unpack_archive(archive, directory)


def compile_sources(directory):
    """编译并安装目录里的源码包，替代原来的 'cd ... && python3 setup.py'。"""
    for name in [entry for entry in os.listdir(directory)
                 if os.path.isdir(os.path.join(directory, entry))]:
        print(colored(f"Compiling {name.split('-')[0]}", color='magenta'))
        package_dir = os.path.join(directory, name)
        subprocess.run([sys.executable, 'setup.py', 'build'], cwd=package_dir)
        subprocess.run([sys.executable, 'setup.py', 'install'], cwd=package_dir)


if sys.platform == 'win32':
    requirementsfile = open(os.path.join(SYSTEM_DIR, "win32requirements.txt"), 'r')
    win32_requirements = [name.strip('\n ') for name in requirementsfile.readlines()
                          if name.strip('\n ') not in ['', 'win32', 'win32api', 'win32con']] + ["pywin32", "pypiwin32"]

    for module in win32_requirements:
        print(colored(f"Installing {module}", color='magenta'))
        print()
        subprocess.run([sys.executable, '-m', 'pip', 'install', module,
                        '-f', os.path.join(workdir, sys.platform)])

    sources_dir = os.path.join(workdir, "sources")
    unpack_sources(sources_dir)
    compile_sources(sources_dir)
elif sys.platform == 'linux':
    from config import packagemgr
    if packagemgr is not None:
        subprocess.run([packagemgr, 'update'])
        subprocess.run([packagemgr, 'upgrade'])
        subprocess.run([packagemgr, 'install', '-y', 'zenity'])
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
        subprocess.run([sys.executable, '-m', 'pip', 'install', module,
                        '-f', os.path.join(workdir, sys.platform)])

    sources_dir = os.path.join(workdir, "sources")
    unpack_sources(sources_dir)
    compile_sources(sources_dir)
else:
    raise PlatformError('TSL-SYSTEM can only run on win32 or linux platform, but yours is %s.' % sys.platform)

import wget
if sys.platform == "win32":
    import win32api
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
            subprocess.run(['tar', '-xzvf', f'{workdir}/Python-3.9.7.tgz'])
            install_to_path = input('Please input the path to install Python-3.9.7 [default: /usr/local]: ')
            install_prefix = install_to_path if install_to_path != "" else "/usr/local"
            subprocess.run(['./configure', f'--prefix={install_prefix}'], cwd='Python-3.9.7')
            subprocess.run(['make'], cwd='Python-3.9.7')
            subprocess.run(['make', 'install'], cwd='Python-3.9.7')
        elif sys.platform == 'win32':
            bit = int(platform.architecture()[0][:2])
            if bit == 64:
                wget.download('https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe', out=workdir)
                os.startfile(os.path.join(workdir, 'python-3.9.7-amd64.exe'))
            elif bit == 32:
                wget.download('https://www.python.org/ftp/python/3.9.7/python-3.9.7.exe', out=workdir)
                os.startfile(os.path.join(workdir, 'python-3.9.7.exe'))
            else:
                raise SystemError('bits calculator has broken down!')
        else:
            raise PlatformError('TSL-SYSTEM must run on the win32 or linux platform!')
    else:  # 7 -> no
        python_error_version = f'{python_version[0]}.{python_version[1]}.{python_version[2]}'
        raise RuntimeError(f'cannot load TSL-SYSTEM with Python-{python_error_version}!')
