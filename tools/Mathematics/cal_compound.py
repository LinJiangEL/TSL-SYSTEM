#  Copyright (c) 2024-2025. L.J.Afres, All rights reserved.

import re
from fractions import Fraction
from .cal_basic import Basic

basic = Basic()


class Symbol:
    opsymbols = {
        "+": basic.add,
        "-": basic.sub,
        "*": basic.mul,
        "/": basic.div
    }


class Compound:
    def __init__(self):
        self.varibles = {}
        self._patterns = {
            "symbol": re.compile(r"^\d+(?:\.\d+)?(?:[+\-*/]\d+(?:\.\d+)?)+$"),
            "expression": re.compile(r""),
        }

    def base(self, expression):
        symbol = Symbol()
        """Base calculation."""
        if self._check_if_vaild(expression):
            return ["SyntaxError:invalid syntax."]
        else:
            # try:
            #     result = eval(expression, {"__builtins__": None}, {})
            #     return result
            # except ZeroDivisionError:
            #     return "ZeroDivisionError: division by zero."
            # except SyntaxError as e:
            #     return f"SyntaxError:{e}"
            nums = re.findall(r'\d+(?:\.\d+)?', expression)
            operators = re.findall(r'[+\-*/]', expression)
            print(nums, operators)
            nums = [float(n) for n in nums]

            i = 0
            while i < len(operators):
                if operators[i] in ['*', '/']:
                    result = symbol.opsymbols[operators[i]](nums[i], nums[i + 1])
                    if isinstance(result, str) and "Error" in result:
                        return [result]
                    if isinstance(result, list):
                        nums[i] = result[1]
                    else:
                        nums[i] = result
                    nums.pop(i + 1)
                    operators.pop(i)
                else:
                    i += 1

            result = nums[0]
            for i in range(len(operators)):
                result = symbol.opsymbols[operators[i]](result, nums[i + 1])
                if isinstance(result, str) and "Error" in result:
                    return [result]
                if isinstance(result, list):
                    result = result[1]

            resulttext = f"Result (2): {round(result, 2):.2f}\n" + \
                        f"Digits (8): {round(result, 8)}\n" + \
                        f"Fraction: {Fraction(str(result))}"
            return [resulttext, result, Fraction(str(result))]

    def _check_if_vaild(self, oridata: str) -> bool:
        oridata = ''.join([exp.strip() for exp in oridata.split(' ') if exp])
        return re.fullmatch(self._patterns["symbol"], oridata) is None

    def parse(self, expression):
        pass
