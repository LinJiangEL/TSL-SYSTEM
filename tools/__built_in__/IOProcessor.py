#  Copyright (c) 2024. L.J.Afres, All rights reserved.

from ast import literal_eval


class InputProcessor:
    """处理系统所有输入输出内容，并过滤掉非法的部分。"""
    def __init__(self):
        self.string_simplify = lambda string: list(dict.fromkeys(string))
        self.PatternList = lambda a, b: list(range(a, b))
        self.patterns = ['username', 'password', 'terminal']
        self.pattern_username = self.PatternList(48, 58) + self.PatternList(65, 91) + self.PatternList(97, 123)
        self.pattern_password = self.pattern_username + [35, 36, 38, 42]
        self.pattern_terminal = []

    def Input_illegal_check(self, text, pattern):
        if pattern in self.patterns:
            chars = self.string_simplify(text)
            result = []
            for char in chars:
                if ord(char) in getattr(self, f"pattern_{pattern}"):
                    result.append(1)
                else:
                    result.append(0)
            return all(result)
        else:
            print(f"NameError:pattern '{pattern}' is not defined in patterns.")
            return


class Null(object):
    def write(self, string):
        self.string = literal_eval(string)
        return
