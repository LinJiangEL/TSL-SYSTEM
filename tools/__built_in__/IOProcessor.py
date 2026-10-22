#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

"""系统输入处理模块。

项目里所有交互式输入都应通过本模块读取。InputProcessor.read() 会按照
指定规则逐字符检查输入内容，把非法字符替换为 '*'，并以 CRITICAL 级别
记录该事件（密码等敏感输入在日志中会被整体遮蔽），这样非法内容既不会
进入后续流程，也不会被完整写入日志。
"""

import getpass
import re

from ast import literal_eval
from loguru import logger


class InputProcessor:
    """处理系统所有输入内容，并过滤掉非法的部分。"""

    MASK_CHARACTER = '*'
    DEFAULT_PATTERN = 'text'
    PRINTABLE_CHARACTER = r'[^\x00-\x1F\x7F]'

    def __init__(self):
        self.string_simplify = lambda string: list(dict.fromkeys(string))
        self.PatternList = lambda a, b: list(range(a, b))
        self.patterns = ['username', 'password', 'secret', 'terminal',
                         'identkey', 'text', 'path', 'number', 'expression', 'url']
        self.pattern_characters = {
            'username': re.compile(r'[0-9A-Za-z]'),
            'password': re.compile(r'[0-9A-Za-z#$&*]'),
            'secret': re.compile(self.PRINTABLE_CHARACTER),
            'terminal': re.compile(self.PRINTABLE_CHARACTER),
            'identkey': re.compile(r'[0-9A-Za-z_\-]'),
            'text': re.compile(self.PRINTABLE_CHARACTER),
            'path': re.compile(self.PRINTABLE_CHARACTER),
            'number': re.compile(r'[0-9]'),
            'expression': re.compile(self.PRINTABLE_CHARACTER),
            'url': re.compile(self.PRINTABLE_CHARACTER)
        }
        self.last_illegal = 0
        self.last_masked = ''

    def get_characters(self, pattern):
        """返回指定规则所用的单字符正则表达式。"""
        if pattern not in self.pattern_characters:
            raise NameError(f"pattern '{pattern}' is not defined in patterns.")
        return self.pattern_characters[pattern]

    def input_illegal_check(self, text, pattern):
        """判断输入是否完全合法：True 表示合法，False 表示含有非法字符。"""
        characters = self.get_characters(pattern)
        return all(characters.fullmatch(char) is not None for char in text)

    def sanitize(self, text, pattern=DEFAULT_PATTERN):
        """把非法字符替换为 '*'，返回 (处理后的文本, 非法字符数量)。"""
        characters = self.get_characters(pattern)
        result, illegal = [], 0
        for char in text:
            if characters.fullmatch(char) is None:
                result.append(self.MASK_CHARACTER)
                illegal += 1
            else:
                result.append(char)
        return ''.join(result), illegal

    def record_illegal(self, pattern, masked, illegal, secret=False):
        """以 CRITICAL 级别记录非法输入，敏感内容整体遮蔽。"""
        preview = self.MASK_CHARACTER * len(masked) if secret else masked
        logger.critical(
            "InputSecurityWarning:illegal input was detected and "
            "the illegal characters were replaced by '*'. "
            f"[INPUTINFO:('{pattern}', {illegal}, '{preview}')]"
        )

    def read(self, prompt='', pattern=DEFAULT_PATTERN, secret=False, strip=False):
        """读取一行输入并按指定规则过滤。

        secret 为 True 时使用 getpass 读取，日志中只保留等长的 '*'。
        返回值里的非法字符已经被替换为 '*'，调用方可以再决定是否接受。
        """
        source = getpass.getpass(prompt) if secret else input(prompt)
        masked, illegal = self.sanitize(source, pattern)
        self.last_illegal = illegal
        self.last_masked = masked
        if illegal:
            self.record_illegal(pattern, masked, illegal, secret)
        return masked.strip() if strip else masked


input_processor = InputProcessor()


def read_input(prompt='', pattern=InputProcessor.DEFAULT_PATTERN, secret=False, strip=False):
    """项目统一的输入入口，所有模块都应使用它读取用户输入。"""
    return input_processor.read(prompt, pattern, secret, strip)


class Null(object):
    def write(self, string):
        self.string = literal_eval(string)
        return
