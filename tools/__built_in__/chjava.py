#  Copyright (c) 2025. L.J.Afres, All rights reserved.

import os
import re
import platform
from pathlib import Path
from tools.__built_in__.set_environ import set_env_variable


def get_windows_java_paths():
    paths = set()

    # 检查注册表
    import winreg
    reg_paths = [
        r"SOFTWARE\JavaSoft\Java Development Kit",
        r"SOFTWARE\JavaSoft\Java Runtime Environment",
        r"SOFTWARE\Wow6432Node\JavaSoft\Java Development Kit",
        r"SOFTWARE\Wow6432Node\JavaSoft\Java Runtime Environment"
    ]

    for reg_path in reg_paths:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    java_home, _ = winreg.QueryValueEx(subkey, "JavaHome")
                    exe_path = os.path.join(java_home, 'bin', 'java.exe')
                    if os.path.isfile(exe_path):
                        paths.add(exe_path)
                    i += 1
                except OSError:
                    break
        except FileNotFoundError:
            continue

    # 检查PATH环境变量
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    for path_dir in path_dirs:
        exe_path = os.path.join(path_dir, 'java.exe')
        if os.path.isfile(exe_path):
            paths.add(os.path.realpath(exe_path))

    # 检查常见安装目录
    prog_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
    java_dir = os.path.join(prog_files, 'Java')
    if os.path.isdir(java_dir):
        for entry in os.listdir(java_dir):
            exe_path = os.path.join(java_dir, entry, 'bin', 'java.exe')
            if os.path.isfile(exe_path):
                paths.add(os.path.realpath(exe_path))

    return list(paths)


def get_java_paths():
    system = platform.system()
    if system == 'Windows':
        javalist = get_windows_java_paths()
        return {int(re.findall(r'(?:jdk-|1\.)(\d+)', p)[0]): p for p in javalist}
    else:
        raise OSError("it only supported on Windows.")


JAVA_HOME = os.getenv('JAVA_HOME')
if os.getenv("PATH").lower().count("java") > 1:
    raise OSError("the environ PATH can not set any java path, instead of JAVA_HOME.")


def setjava(version):
    javas = get_java_paths()
    new_java = javas.get(version)
    if new_java is None:
        print(f"ValueError:cannot find java {version} in your computer, please install them in the directory C:\\Program Files\\Java.\n")
        return None
    else:
        new_java = str(Path(new_java).parent)
    if JAVA_HOME == new_java:
        print("OSError:a same JAVA_HOME already set.\n")
    else:
        set_env_variable("JAVA_HOME", new_java)
        print(f"Successfully change java version to {version}.")
        print("Reboot TSL-SYSTEM later to apply the change.\n")
