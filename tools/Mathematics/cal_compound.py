#  Copyright (c) 2024-2025. L.J.Afres, All rights reserved.

import re
from .cal_basic import Basic

basic = Basic()


class Compound:
    def __init__(self):
        self.varibles = {}
        self._patterns = {
            "symbol": re.compile(r"^\d+(?:\.\d+)?(?:[+\-*/]\d+(?:\.\d+)?)+$"),
            "expression": re.compile(r""),
        }

    def base(self, expression):
        """Base calculation."""
        if self._check_if_vaild(expression) is None:
            print("SyntaxError:invalid syntax.")
        else:
            try:
                result = eval(expression, {"__builtins__": None}, {})
                return result
            except ZeroDivisionError:
                return "ZeroDivisionError: division by zero."

    def _check_if_vaild(self, oridata):
        return re.fullmatch(self._patterns["symbol"], oridata)

