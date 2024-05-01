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
        resultlist = [resulttext, cal_result, cal_fraction, cal_sqrt]
        return resultlist

    def ReturnError(self, errors):
        self.error = errors
        return self.error

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
        if b == 0:
            return self.ReturnError("ZeroDivisionError: division by zero.")
        else:
            if '.' in str(a):
                if str(a).count('.') > 1:
                    self.ReturnError("Invaild digtal num, many '.' was found.")
                else:
                    a = int(a * pow(10, len(str(a).split('.')[1])))
            if '.' in str(b):
                if str(b).count('.') > 1:
                    self.ReturnError("Invaild digtal num, many '.' was found.")
                else:
                    b = int(b * pow(10, len(str(b).split('.')[1])))
            return self.resultformat(cal_result=a / b, cal_fraction=Fraction(a, b))

    # x ** a
    def pow(self, x, a):
        return self.resultformat(cal_result=math.pow(x, a))

    # a // b
    def fdiv(self, a, b):
        if b == 0:
            return self.ReturnError("ZeroDivisionError: integer division or modulo by zero.")
        else:
            return self.resultformat(cal_result=a // b)

    # a % b
    def mod(self, a, b):
        if b == 0:
            return self.ReturnError("ZeroDivisionError: integer division or modulo by zero.")
        else:
            return self.resultformat(cal_result=math.fmod(a, b))

    # |a|
    def abs(self, x):
        return self.resultformat(cal_result=math.fabs(x))

    # x ** 2
    def sqr(self, x):
        return self.resultformat(cal_result=math.pow(x, 2))

    # [y]√x
    def sqrt(self, x, y=2, list_1=None, list_2=None) -> list:
        if len(str(x)) > 10:
            x = int(str(x)[:10])
            print(x)
            print("SpillOverError:invaild sqrt parameter 'x' whose length must be inside '10', "
                  "overflow bits will be rounded."
                  )
        if y >= 161:
            y = 2
            print("ValueError:invaild sqrt parameter 'y', default set its value to '2'.")
        elif y == 0:
            y = 2
            print("ZeroDivisionError: division by zero, default set parameter 'y' value to '2'.")
        else:
            pass

        if list_1 is None:
            list_1 = []
        if list_2 is None:
            list_2 = ()

        digit_result = math.pow(x, 1 / y)

        while True:
            n = 100
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
                            cal_sqrt=str(y) + '_' + str(n) + chr(8730) + list_2 if n > 1 and y > 2
                            else str(y) + '_' + chr(8730) + list_2 if n <= 1 and y > 2
                            else str(n) + chr(8730) + list_2 if n > 1 and y == 2
                            else x if y == 1 else chr(8730) + list_2
                        )
                else:
                    n = n - 1
                    del list_1[0]

            return self.resultformat(cal_result=digit_result, cal_sqrt=0)
