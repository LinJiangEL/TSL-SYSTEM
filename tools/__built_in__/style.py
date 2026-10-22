#  Copyright (c) 2026. L.J.Afres, All rights reserved.

"""终端美化工具。

把项目里重复出现的标题栏、分隔线、输入提示符和彩色状态信息集中到
一个模块中，让每个工具模块的输出风格保持一致。本模块只负责显示，
不参与任何业务逻辑，也不改变已有输出中的文字内容。
"""

import sys
import colorama

from termcolor import colored
from typing import Literal, Final, Optional

Color = Literal[
    "black", "grey", "red", "green", "yellow", "blue", "magenta",
    "cyan", "light_grey", "dark_grey", "light_red", "light_green",
    "light_yellow", "light_blue", "light_magenta", "light_cyan", "white",
]

if sys.platform == 'win32':
    # 打开 Windows 控制台对 ANSI 转义序列的支持，命令本身不会产生输出。
    colorama.just_fix_windows_console()

BANNER_WIDTH = 37
RULE_WIDTH = 60

_TITLE_COLOR: Final[Color] = 'cyan'
_PROMPT_COLOR: Final[Color] = 'magenta'
_NAME_COLOR: Final[Color] = 'cyan'
_VALUE_COLOR: Final[Color] = 'white'


def banner(title, width=BANNER_WIDTH, color: Optional[Color] = _TITLE_COLOR, attrs=('bold',)):
    """打印一个居中的模块标题栏。"""
    if len(title) + 2 > width:
        width = len(title) + 4
    print(colored('-' * width, color=color, attrs=attrs))
    print(colored((' %s ' % title).center(width), color=color, attrs=attrs))
    print(colored('-' * width, color=color, attrs=attrs))
    print('')


def rule(width=RULE_WIDTH, color: Optional[Color] = 'dark_grey'):
    """打印一条分隔线。"""
    print(colored('-' * width, color=color))


def heading(text, color: Optional[Color] = _TITLE_COLOR):
    """打印一个小节标题。"""
    print(colored('== %s ==' % text, color=color, attrs=['bold']))


def section(text, color: Optional[Color] = _TITLE_COLOR):
    """打印一个带方括号的小标签。"""
    print(colored('[%s]' % text, color=color, attrs=['bold']))


def prompt(label, color: Optional[Color] = _PROMPT_COLOR):
    """返回彩色的输入提示符。

    如果传入的标签本身已经带有 '>>' 提示符，则不再重复追加。
    """
    stripped = label.rstrip()
    if stripped.endswith('>>'):
        return colored(stripped, color=color, attrs=['bold'])
    return colored('%s >> ' % stripped, color=color, attrs=['bold'])


def label(text, color: Optional[Color] = _NAME_COLOR):
    """返回彩色的提示标签，用于 Username、Password 一类的输入。"""
    if text.endswith((':', ': ')):
        return colored(text, color=color, attrs=['bold'])
    return colored('%s: ' % text, color=color, attrs=['bold'])


def success(text):
    """打印成功信息。"""
    print(colored(text, color='green'))


def warning(text):
    """打印警告信息。"""
    print(colored(text, color='yellow'))


def error(text):
    """打印错误信息。"""
    print(colored(text, color='red'))


def info(text):
    """打印提示信息。"""
    print(colored(text, color=_TITLE_COLOR))


def muted(text):
    """打印弱化的辅助信息。"""
    print(colored(text, color='dark_grey'))


def highlight(text, color: Optional[Color] = 'green', attrs=('bold',)):
    """返回高亮后的字符串，不打印。"""
    return colored(text, color=color, attrs=attrs)


def key_value(name, value, name_color: Optional[Color] = _NAME_COLOR, value_color: Optional[Color] = _VALUE_COLOR):
    """打印一行对齐的“名称: 值”。"""
    print(colored('%-12s' % (name + ':'), color=name_color) + colored(str(value), color=value_color))


def error_from(error_type, message):
    """按项目的错误信息风格打印一条错误。"""
    error('%s:%s' % (error_type, message))
