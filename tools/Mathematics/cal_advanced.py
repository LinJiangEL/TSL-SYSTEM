import re
from sympy import Eq, solve
from sympy.parsing.sympy_parser import parse_expr
from config import SYSTEM_DIGMAX
from tools.Mathematics.cal_basic import Basic


class Advanced:
    def __init__(self):
        basic = Basic()
        self.digmax = SYSTEM_DIGMAX
        self._ok = True

    def resultformat(self, cal_result, cal_fraction=None, cal_sqrt=None):
        resulttext = f"Result (2): {round(cal_result, 2)}\n" + \
                     f"Digits ({self.digmax}): {round(cal_result, self.digmax)}\n" + \
                     f"Fraction: {cal_fraction}\n" + \
                     f"Sqrt: {cal_sqrt}"
        return resulttext

    def ReturnError(self, errors):
        self.error = errors
        return self.error

    def Solve_equation(self, expressions: list):
        ecount = ','.join(expressions).count(',')
        if ecount != 1:
            self._ok = False
            print("ValueError:Solve_equation() takes 2 positional expression but "
                  f"{ecount + 1 if '' not in expressions else len(expressions) - expressions.count('')} "
                  " were given."
                  )
            return 256

        # (\d)([a-zA-Z]) 包含两个捕获组：
        #     (\d)：匹配一个数字字符，即0-9之间的任意一个数字。
        #     ([a - zA - Z])：匹配一个英文字母，即大小写字母a到z之间的任意一个字符。
        # r'\1*\2'：
        #     \1：表示第一个捕获组匹配到的内容，即数字字符。
        #     * ：表示乘法操作符。我们希望在数字和字母之间插入这个乘法操作符。
        #     \2：表示第二个捕获组匹配到的内容，即英文字母。

        expression1 = parse_expr(re.sub(r'(\d)\s*([a-zA-Z])', r'\1*\2', expressions[0].replace("^", "**")))
        expression2 = parse_expr(re.sub(r'(\d)\s*([a-zA-Z])', r'\1*\2', expressions[1].replace("^", "**")))

        eq_symbol1 = expression1.free_symbols
        eq_symbol2 = expression2.free_symbols

        # sympy：3x^2+4x-7,0 sqrt(7)
        symbol = eq_symbol1.union(eq_symbol2)
        # print(expression1, expression2)
        if len(symbol) == 1:
            equation = Eq(expression1, expression2)
            solution = solve(equation, symbol)
        elif len(symbol) > 1:
            print("ValueError:invalid equation symbol, one more symbols was found, "
                  "the smallest letter in ASCII code is used as the character variable symbol.")
            equation = Eq(expression1, expression2)
            solution = solve(equation)
        else:
            solution = 'None'

        return solution
