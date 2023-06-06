import math
from config import SYSTEM_DIGMAX
from fractions import Fraction
from decimal import Decimal


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
        return resulttext

    @staticmethod
    def ReturnError(errors):
        print('error')
        return errors

    # a + b
    def add(self, a, b):
        return self.resultformat(cal_result=math.fsum([a, b]))

    # a - b
    def sub(self, a, b):
        return self.resultformat(cal_result=math.fsum([a, -b]))

    # a * b
    def mul(self, a, b):
        return self.resultformat(cal_result=a * b)

    # a / b
    def div(self, a, b):
        return self.resultformat(cal_result=a / b, cal_fraction=Fraction(a, b))

    # x ** a
    def pow(self, x, a):
        return self.resultformat(cal_result=math.pow(x, a))

    # a // b
    def fdiv(self, a, b):
        return self.resultformat(cal_result=a // b)

    # a % b
    def mod(self, a, b):
        return self.resultformat(cal_result=math.fmod(a, b))

    # |a|
    def abs(self, x):
        return self.resultformat(cal_result=math.fabs(x))

    # x ** 2
    def sqr(self, x):
        return self.resultformat(cal_result=math.pow(x, 2))

    # [y]√x
    def sqrt(self, x, y=2, list_1=None, list_2=None):
        if list_1 is None:
            list_1 = []
        if list_2 is None:
            list_2 = ()

        digit_result = math.pow(x, 1 / y)

        while True:
            n = 1000
            while n != 0:
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
                            cal_sqrt=str(y) + '_' + str(n) + chr(8730) + list_2 if n > 1 and y > 2
                            else str(y) + '_' + chr(8730) + list_2 if n <= 1 and y > 2
                            else str(n) + chr(8730) + list_2 if n > 1 and y == 2
                            else x if y == 1 else chr(8730) + list_2)
                else:
                    n = n - 1
                    del list_1[0]
