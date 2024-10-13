#  Copyright (c) 2024. L.J.Afres, All rights reserved.

from .cal_basic import Basic

basic = Basic()


class Compound:
    def __init__(self):
        self.variables = {}

    def set_variable(self, name, value):
        self.variables[name] = value

    def get_variable(self, name):
        return self.variables.get(name, None)

    def evaluate(self, expression):
        try:
            local_vars = {
                'add': Basic.add,
                'sub': Basic.sub,
                'mul': Basic.mul,
                'div': Basic.div,
                **self.variables  # 添加用户定义的变量到local_vars
            }
            result = eval(expression, {}, local_vars)
            print(f"Result: {result}")
            return result
        except ... as e:
            ...

    def parse_variable(self, command):
        try:
            _, rest = command.split(' ', 1)
            name, value_expr = rest.split('=')
            name = name.strip()
            value = self.evaluate(value_expr.strip())
            if value is not None:
                self.set_variable(name, value)
        except Exception as e:
            print(f"Invalid variable assignment. Error: {str(e)}")
