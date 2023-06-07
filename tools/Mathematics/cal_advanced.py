import math
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
    def ReturnError(errors):
        print('error')
        return errors

