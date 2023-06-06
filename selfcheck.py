import os
import sys
import time
import platform
import wget
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
    if python_version[0] >= 3 and python_version[1] >= 7:
        print('yes')
    else:
        print('no')
        print('PythonVersionNotSupport:TSL-SYSTEM required Python >= 3.9.2, if you want to use it, please update your Python!')
        if __name__ == '__main__':
            ask_updatePython = win32api.MessageBox(0, "Do you want to update your Python Environment?", "Update Python", win32con.MB_YESNO)
            if ask_updatePython == 6:  # 6 -> yes
                print('Prefer to installing Python-3.9.7')
                if sys.platform == 'linux':
                    wget.download('https://www.python.org/ftp/python/3.9.7/Python-3.9.7.tgz')
                    os.system('tar -xzvf Python-3.9.7.tgz')
                    install_to_path = input('Please input the path to install Python-3.9.7 [default: /usr/local]: ')
                    os.system(f'cd Python-3.9.7 && ./configure --prefix={install_to_path if install_to_path != "" else "/usr/local"} && make && make install')
                elif sys.platform == 'win32':
                    bit = int(platform.architecture()[0][:2])
                    if bit == 64:
                        wget.download('https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe')
                        os.system('start python-3.9.7-amd64.exe')
                    elif bit == 32:
                        wget.download('https://www.python.org/ftp/python/3.9.7/python-3.9.7.exe')
                        os.system('start python-3.9.7.exe')
                    else:
                        raise SystemError('bits calculator broken down!')
                else:
                    raise PlatformError('TSL-SYSTEM must run on the win32 or linux platform!')
            else:  # 7 -> no
                python_error_version = f'{python_version[0]}.{python_version[1]}.{python_version[2]}'
                raise RuntimeError(f'cannot load TSL-SYSTEM with Python-{python_error_version}!')

def selfcheck_module(name):
    print('check %s ... ' % name.strip(), end='', flush=True)
    time.sleep(0.1)
    try:
        exec(f"import {name}; del {name};")
    except ImportError:
        print('no')
        return False
    else:
        print('yes')
        return True
