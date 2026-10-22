#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

"""外部命令执行工具。

`os.system` 已被 Python 标记为软弃用（soft deprecated），因此项目里所有
需要调用外部程序的地方统一改用 `subprocess.run`。本模块把三种常见用法
集中封装起来：

1. `run()`：按参数列表执行外部命令，参数不会被 shell 解释，从根源上避免
   命令注入；需要 shell 语义（管道、重定向）时代码应在 Python 里完成。
2. `display_file()`：直接输出文本文件内容，替代 `type` / `cat` 这类内建命令。
3. `clear_screen()`：用 ANSI 转义序列清屏，替代 `cls` / `clear` 内建命令。
"""

import subprocess


def run(arguments, cwd=None, silent=False):
    """执行外部命令并返回退出码。

    arguments 必须是参数列表（例如 ['git', 'pull']），不会被 shell 重新
    解析，因此调用方无需为参数手工加引号；silent 为 True 时丢弃命令输出。
    """
    options = {'cwd': cwd}
    if silent:
        options['stdout'] = subprocess.DEVNULL
        options['stderr'] = subprocess.DEVNULL
    try:
        return subprocess.run([str(argument) for argument in arguments], **options).returncode
    except FileNotFoundError:
        print(f"RuntimeError:cannot find the command '{arguments[0]}', "
              "please check the system environment."
              )
        return 127
    except OSError as error:
        print(f"OSError:{error}")
        return 126


def display_file(filepath):
    """把文本文件的内容打印到标准输出，替代 'type' / 'cat' 命令。"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as file:
            print(file.read(), end='')
    except OSError as error:
        print(f"FileNotFoundError:cannot read the file '{filepath}', {error}.")


def clear_screen():
    """清空终端屏幕，替代 'cls' / 'clear' 命令。"""
    print('\033[2J\033[H', end='', flush=True)
