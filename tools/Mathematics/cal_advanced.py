from cal_basic import Basic
from config import SYSTEM_DIGMAX


class Advanced:
    def __init__(self):
        basic = Basic()
        self.digmax = SYSTEM_DIGMAX

    def resultformat(self, cal_result, cal_fraction=None, cal_sqrt=None):
        resulttext = f"Result (2): {round(cal_result, 2)}\n" + \
                     f"Digits ({self.digmax}): {round(cal_result, self.digmax)}\n" + \
                     f"Fraction: {cal_fraction}\n" + \
                     f"Sqrt: {cal_sqrt}"
        return resulttext

    @staticmethod
    def ReturnError(self, errors):
        print('error')
        return errors

    @staticmethod
    def Solve_equation(expressions: list):
        if expressions.count(',') != 1:
            print("ValueError:Solve_equation() takes 1 positional expression but "
                  f"{expressions.count(',')+1 if '' not in expressions else ...}"
                  " were given."
                  )
            return 256
        expression1 = expressions[0]
        expression2 = expressions[1]
