from tools.Mathematics.cal_basic import Basic
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

    def ReturnError(self, errors):
        self.error = errors
        return self.error

    def Solve_equation(self, expressions: list):
        ecount = ','.join(expressions).count(',')
        if ecount != 1:
            print("ValueError:Solve_equation() takes 2 positional expression but "
                  f"{ecount+1 if '' not in expressions else len(expressions)-expressions.count('')} "
                  " were given."
                  )
            return 256
        expression1 = expressions[0]
        expression2 = expressions[1]

        # 正则表达式：3x^2+4x-7,0
        print(expression1, expression2)

        if '^' in expression1 or '^' in expression2:
            # 多次解
            pass
        else:
            pass
