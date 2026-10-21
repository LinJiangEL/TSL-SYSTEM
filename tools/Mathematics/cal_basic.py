#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

import math
import re
from cachetools import cached
from config import SYSTEM_DIGMAX, CACHE
from fractions import Fraction
from ast import literal_eval
from decimal import Decimal

ERROR_PATTERN = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception)):\s*(.*)$')
NUMBER_PATTERN = re.compile(r'^[+\-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?$')
MAX_EXPONENT = 1024


def get_float_length(n):
    text = str(n)
    return len(text.split('.')[1]) if '.' in text else 0


def dot2fraction(n: float):
    _num = Fraction(str(n))
    return Fraction(_num.numerator, _num.denominator)


def is_number(text):
    """判断文本是否为一个合法的十进制数。"""
    return NUMBER_PATTERN.fullmatch(str(text).strip()) is not None


def format_error(message):
    """把错误信息统一为 'ErrorName: message.' 的格式。"""
    text = str(message).strip()
    match = ERROR_PATTERN.fullmatch(text)
    if match:
        name, detail = match.group(1), match.group(2).strip()
    else:
        name, detail = 'ValueError', text
    if not detail:
        detail = 'invalid value.'
    if not detail.endswith('.'):
        detail = detail + '.'
    return '%s: %s' % (name, detail)


def to_fraction(number, digmax=SYSTEM_DIGMAX):
    """尽可能把数值转换成精确的分数，无法精确表示时返回 None。"""
    if isinstance(number, Fraction):
        return number
    if isinstance(number, bool):
        return Fraction(int(number))
    if isinstance(number, int):
        return Fraction(number)
    if isinstance(number, float):
        if not math.isfinite(number):
            return None
        exact = Fraction(str(number))
        if exact.denominator <= 10 ** digmax:
            return exact
    return None


def _scientific_text(value, precision):
    """把超大数值转换成科学计数法文本。"""
    try:
        if isinstance(value, Fraction):
            decimal_value = Decimal(value.numerator) / Decimal(value.denominator)
        else:
            decimal_value = Decimal(value)
        return format(decimal_value, '.%de' % precision)
    except (TypeError, ValueError, ArithmeticError):
        return str(value)


def _fraction_text(cal_fraction, digmax=SYSTEM_DIGMAX):
    """把分数转换成文本，过长的精确值用科学计数法缩写。"""
    if cal_fraction is None:
        return 'None'
    text = str(cal_fraction)
    if len(text) > 24:
        return '%s (exact, %d digits)' % (_scientific_text(cal_fraction, digmax), len(text))
    return text


def result_text(cal_result, cal_fraction=None, cal_sqrt=None, digmax=SYSTEM_DIGMAX):
    """生成三个模块统一的计算结果文本。"""
    if cal_fraction is None:
        cal_fraction = to_fraction(cal_result, digmax)
    try:
        two = '%.2f' % round(cal_result, 2)
        if len(two) > 24:
            two = _scientific_text(cal_result, 2)
    except (OverflowError, TypeError, ValueError):
        two = _scientific_text(cal_result, 2)
    try:
        digits = '%s' % round(cal_result, digmax)
        if len(digits) > 24:
            digits = _scientific_text(cal_result, digmax)
    except (OverflowError, TypeError):
        digits = _scientific_text(cal_result, digmax)
    return ('Result (2): %s\n'
            'Digits (%d): %s\n'
            'Fraction: %s\n'
            'Sqrt: %s' % (two, digmax, digits,
                          _fraction_text(cal_fraction, digmax),
                          cal_sqrt if cal_sqrt is not None else 'None'))


def expression_text(expression):
    """生成统一的结果前缀行。"""
    return 'Expression: %s' % expression


class Basic:
    def __init__(self):
        self.error = ""
        self.one = ['abs', 'sqr', 'sqrt']
        self.two = ['add', 'sub', 'mul', 'div', 'pow', 'fdiv', 'mod', 'sqrt']
        self.needlist = []
        self.digmax = SYSTEM_DIGMAX

    def resultformat(self, cal_result, cal_fraction=None, cal_sqrt=None):
        if cal_fraction is None:
            cal_fraction = to_fraction(cal_result, self.digmax)
        return [result_text(cal_result, cal_fraction, cal_sqrt, self.digmax),
                cal_result, cal_fraction, cal_sqrt]

    def ReturnError(self, errors):
        self.error = format_error(errors)
        return self.error

    @staticmethod
    def iseven(n):
        return n % 2 == 0

    @staticmethod
    def _exact_values(*values):
        """把操作数转换成精确的分数。"""
        exact = []
        for value in values:
            if isinstance(value, Fraction):
                exact.append(value)
            elif isinstance(value, float):
                if not math.isfinite(value):
                    raise ValueError('the value must be finite.')
                exact.append(Fraction(str(value)))
            else:
                exact.append(Fraction(value))
        return exact

    def _finish(self, value):
        """把精确的分数结果格式化为统一的文本。"""
        if not isinstance(value, Fraction):
            return self.resultformat(cal_result=value)
        try:
            cal_result = float(value)
        except OverflowError:
            cal_result = float('inf')
        if not math.isfinite(cal_result):
            return self.resultformat(cal_result=cal_result, cal_fraction=value)
        return self.resultformat(cal_result=cal_result, cal_fraction=value)

    # a + b
    def add(self, a, b):
        try:
            exact_a, exact_b = self._exact_values(a, b)
        except (TypeError, ValueError, OverflowError):
            return self.resultformat(cal_result=math.fsum([a, b]))
        return self._finish(exact_a + exact_b)

    # a - b
    def sub(self, a, b):
        try:
            exact_a, exact_b = self._exact_values(a, b)
        except (TypeError, ValueError, OverflowError):
            return self.resultformat(cal_result=math.fsum([a, -b]))
        return self._finish(exact_a - exact_b)

    # a * b
    def mul(self, a, b):
        try:
            exact_a, exact_b = self._exact_values(a, b)
        except (TypeError, ValueError, OverflowError):
            return self.resultformat(cal_result=a * b)
        return self._finish(exact_a * exact_b)

    # a / b
    def div(self, a, b):
        if b == 0:
            return self.ReturnError("ZeroDivisionError: division by zero.")
        try:
            exact_a, exact_b = self._exact_values(a, b)
        except (TypeError, ValueError, OverflowError):
            return self.resultformat(cal_result=a / b)
        return self._finish(exact_a / exact_b)

    # x ** a
    @cached(cache=CACHE)
    def pow(self, x, a):
        if isinstance(a, float) and a.is_integer():
            a = int(a)
        if isinstance(a, int) and abs(a) <= MAX_EXPONENT:
            try:
                exact_x = self._exact_values(x)[0]
            except (TypeError, ValueError, OverflowError):
                exact_x = None
            if exact_x is not None:
                try:
                    return self._finish(exact_x ** a)
                except ZeroDivisionError:
                    return self.ReturnError("ZeroDivisionError: 0 cannot be raised to a negative power.")
        try:
            result = math.pow(x, a)
        except OverflowError:
            result = float('inf')
        except ValueError:
            return self.ReturnError("ValueError: math domain error.")
        return self.resultformat(cal_result=result)

    # a // b
    @cached(cache=CACHE)
    def fdiv(self, a, b):
        if b == 0:
            return self.ReturnError("ZeroDivisionError: integer division or modulo by zero.")
        try:
            exact_a, exact_b = self._exact_values(a, b)
        except (TypeError, ValueError, OverflowError):
            return self.resultformat(cal_result=a // b)
        return self._finish(Fraction(math.floor(exact_a / exact_b)))

    # a % b
    @cached(cache=CACHE)
    def mod(self, a, b):
        if b == 0:
            return self.ReturnError("ZeroDivisionError: integer division or modulo by zero.")
        try:
            exact_a, exact_b = self._exact_values(a, b)
        except (TypeError, ValueError, OverflowError):
            return self.resultformat(cal_result=math.fmod(a, b))
        return self._finish(exact_a - exact_b * math.floor(exact_a / exact_b))

    # |a|
    def abs(self, x):
        try:
            exact_x = self._exact_values(x)[0]
        except (TypeError, ValueError, OverflowError):
            return self.resultformat(cal_result=math.fabs(x))
        return self._finish(abs(exact_x))

    # x ** 2
    @cached(cache=CACHE)
    def sqr(self, x):
        try:
            exact_x = self._exact_values(x)[0]
        except (TypeError, ValueError, OverflowError):
            return self.resultformat(cal_result=math.pow(x, 2))
        return self._finish(exact_x ** 2)

    # [y]√x
    @cached(cache=CACHE)
    def sqrt(self, x, y=2, list_1=None, list_2=None) -> list:
        try:
            y = float(y)
        except (TypeError, ValueError):
            return self.ReturnError("TypeError: 'y' must be a number.")
        if not math.isfinite(y):
            return self.ReturnError("ValueError: invalid operate y.")
        if self.iseven(y) and x < 0:
            return self.ReturnError("ValueError: math domain error.")
        # sqrt 8,0.2 -> 8**5
        if y > 154.1273577 or not y:
            return self.ReturnError("ValueError: invalid operate y.")
        if y < 0:
            return self.ReturnError("ValueError: please simplify the negative number y before execute calculate command.")
        y = dot2fraction(y)

        list_1 = [] if list_1 is None else list_1
        list_2 = () if list_2 is None else list_2

        try:
            digit_result = math.pow(abs(x), 1 / y) * (1, -1)[x < 0]
        except (OverflowError, ValueError, ZeroDivisionError):
            return self.ReturnError("ValueError: math domain error.")

        while True:
            n = 100
            while n != 0:
                if x == 0:
                    break
                try:
                    b = x / pow(n, y)
                    list_1.append(b)
                except OverflowError:
                    return self.ReturnError("OverflowError: int too large to operate.")
                for i in list_1:
                    list_2 = f'{i:g}'
                if Decimal(list_2) == Decimal(list_2).to_integral():
                    if math.fabs(int(literal_eval(f"{list_2}"))) == 1:
                        return self.resultformat(cal_result=digit_result, cal_sqrt=n * (1, -1)[x < 0])
                    else:
                        return self.resultformat(
                            cal_result=digit_result,
                            cal_sqrt=f"{str(n)}({str(y)}){chr(8730)}{list_2}" if n > 1 and y > 2
                            else f"({str(y)}){chr(8730)}{list_2}" if n <= 1 and y > 2
                            else f"{str(n)}{chr(8730)}{list_2}" if n > 1 and y == 2
                            else x if y == 1
                            else f"({str(y)}){chr(8730)}{list_2}" if y < 2
                            else f"{chr(8730)}{list_2}"
                        )
                else:
                    n = n - 1
                    del list_1[0]

            return self.resultformat(cal_result=digit_result, cal_sqrt=0)
