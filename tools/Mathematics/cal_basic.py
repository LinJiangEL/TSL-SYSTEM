#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import math
from cachetools import cached
from config import SYSTEM_DIGMAX, CACHE
from fractions import Fraction
from decimal import Decimal

def get_float_length(n):
    return len(str(n).split('.')[1])

def dot2fraction(n: float):
    _num = Fraction(str(n))
    return Fraction(_num.numerator, _num.denominator)


class Basic:
    def __init__(self):
        self.one = ['abs', 'sqr', 'sqrt']
        self.two = ['add', 'sub', 'mul', 'div', 'pow', 'fdiv', 'mod', 'sqrt']
        self.needlist = []
        self.digmax = SYSTEM_DIGMAX

    def resultformat(self, cal_result, cal_fraction=None, cal_sqrt=None):
        resulttext = f"Result (2): {round(cal_result, 2)}\n" + \
                     f"Digits ({self.digmax}): {round(cal_result, self.digmax)}\n" + \
                     f"Fraction: {cal_fraction}\n" + \
                     f"Sqrt: {cal_sqrt}"
        resultlist = [resulttext, cal_result, cal_fraction, cal_sqrt]
        return resultlist

    def ReturnError(self, errors):
        self.error = errors
        return self.error

    # a + b
    # @cached(cache=CACHE)
    def add(self, a, b):
        return self.resultformat(cal_result=math.fsum([a, b]))

    # a - b
    # @cached(cache=CACHE)
    def sub(self, a, b):
        return self.resultformat(cal_result=math.fsum([a, -b]))

    # a * b
    # @cached(cache=CACHE)
    def mul(self, a, b):
        return self.resultformat(cal_result=a * b)

    # a / b
    @cached(cache=CACHE)
    def div(self, a, b):
        if b == 0:
            return self.ReturnError("ZeroDivisionError: division by zero.")
        else:
            max_float_length = max(get_float_length(a), get_float_length(b))
            if '.' in str(a):
                if str(a).count('.') > 1:
                    self.ReturnError("Invalid digtal num, many '.' was found.")
                else:
                    a = int(a * pow(10, max_float_length))
            if '.' in str(b):
                if str(b).count('.') > 1:
                    self.ReturnError("Invalid digtal num, many '.' was found.")
                else:
                    b = int(b * pow(10, max_float_length))
            return self.resultformat(cal_result=a / b, cal_fraction=Fraction(a, b))

    # x ** a
    @cached(cache=CACHE)
    def pow(self, x, a):
        try:
            result = math.pow(x, a)
        except OverflowError:
            result = float('inf')

        return self.resultformat(cal_result=result)

    # a // b
    @cached(cache=CACHE)
    def fdiv(self, a, b):
        if b == 0:
            return self.ReturnError("ZeroDivisionError: integer division or modulo by zero.")
        else:
            return self.resultformat(cal_result=a // b)

    # a % b
    @cached(cache=CACHE)
    def mod(self, a, b):
        if b == 0:
            return self.ReturnError("ZeroDivisionError: integer division or modulo by zero.")
        else:
            return self.resultformat(cal_result=math.fmod(a, b))

    # |a|
    # @cached(cache=CACHE)
    def abs(self, x):
        return self.resultformat(cal_result=math.fabs(x))

    # x ** 2
    @cached(cache=CACHE)
    def sqr(self, x):
        return self.resultformat(cal_result=math.pow(x, 2))

    # [y]√x
    @cached(cache=CACHE)
    def sqrt(self, x, y=2, list_1=None, list_2=None) -> list:
        if len(x) > 12:
            return self.ReturnError("Invalid")
        # sqrt 8,0.2 -> 8**5
        # x = int(x) if isnum(x) else x
        if y >= 161:
            y = 2
            print("ValueError:invalid sqrt parameter 'y', default set its value to '2'.\n")
        elif y == 0:
            y = 2
            print("ZeroDivisionError: division by zero, default set parameter 'y' value to '2'.\ns")
        else:
            pass
        y = dot2fraction(y)

        list_1 = [] if list_1 is None else list_1
        list_2 = () if list_2 is None else list_2

        digit_result = math.pow(x, 1 / y)

        while True:
            n = 1000
            while n != 0:
                if x == 0:
                    break
                b = x / pow(n, y)
                list_1.append(b)
                for i in list_1:
                    list_2 = ('{:g}'.format(i))
                if Decimal(list_2) == Decimal(list_2).to_integral():
                    if int(list_2) == 1:
                        return self.resultformat(cal_result=digit_result, cal_sqrt=n)
                    else:
                        return self.resultformat(
                            cal_result=digit_result,
                            cal_sqrt=f"{str(n)}({str(y)}){chr(8730)}{list_2}" if n > 1 and y > 2
                            else f"({str(y)}){chr(8730)}{list_2}" if n <= 1 and y > 2
                            else f"{str(n)}{chr(8730)}{list_2}" if n > 1 and y == 2
                            else x if y == 1
                            else f"({str(y)}){chr(8730)}{list_2}" if y < 2
                            else chr(8730) + list_2
                        )
                else:
                    n = n - 1
                    del list_1[0]

            return self.resultformat(cal_result=digit_result, cal_sqrt=0)
