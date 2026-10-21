#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

import math
import re
from fractions import Fraction
from operator import add, sub, mul, truediv, floordiv, mod
from tools.Mathematics.cal_basic import Basic, format_error, expression_text, to_fraction

basic = Basic()


class CalculateError(Exception):
    """底层计算模块抛出的错误，异常信息本身即为错误提示。"""
    pass


class Symbol:
    """复合运算的运算符表。"""

    precedence = {
        "+": 1,
        "-": 1,
        "*": 2,
        "/": 2,
        "//": 2,
        "%": 2,
        "^": 3
    }

    opsymbols = {
        "+": add,
        "-": sub,
        "*": mul,
        "/": truediv,
        "//": floordiv,
        "%": mod
    }


class Compound:
    """复合运算，支持运算符优先级、括号、变量与函数调用。"""

    def __init__(self):
        self.varibles = {}
        self.symbol = Symbol()
        self.max_exponent = 1024
        self._tokens = []
        self._index = 0
        self._sqrt = None
        self._patterns = {
            "expression": re.compile(r"^[0-9A-Za-z_.+\-*/%^(),=]+$"),
            "assignment": re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.+)$"),
            "number": re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?"),
            "name": re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
        }

    def base(self, expression):
        """Base calculation."""
        original = expression.strip()
        expression = ''.join(expression.split())
        if self._check_if_vaild(expression):
            return [format_error("SyntaxError: invalid syntax.")]
        name = None
        try:
            if '=' in expression:
                assignment = self._patterns["assignment"].fullmatch(expression)
                if assignment is None:
                    raise SyntaxError("invalid syntax.")
                name, expression = assignment.group(1), assignment.group(2)
                value = self._evaluate(expression)
                self.varibles[name] = value
            else:
                value = self._evaluate(expression)
        except CalculateError as error:
            return [format_error(str(error))]
        except (ZeroDivisionError, SyntaxError, NameError, TypeError, ValueError, OverflowError) as error:
            return [format_error(f"{type(error).__name__}: {error}")]
        result = self._result(value, name)
        result[0] = expression_text(original) + '\n' + result[0]
        return result

    def reset(self):
        """清空变量表与临时状态。"""
        self.varibles.clear()
        self._sqrt = None

    def _result(self, value, name=None):
        """按照 Basic 的格式输出计算结果。"""
        try:
            cal_result = float(value)
        except OverflowError:
            cal_result = float("inf")
        if math.isinf(cal_result) or math.isnan(cal_result):
            cal_fraction = to_fraction(value, basic.digmax) if isinstance(value, (int, Fraction)) else None
        else:
            cal_fraction = to_fraction(value, basic.digmax)
        resulttext = basic.resultformat(cal_result=cal_result, cal_fraction=cal_fraction,
                                        cal_sqrt=self._sqrt)[0]
        if name is not None:
            resulttext = f"{name} = {self._num2str(value)}\n" + resulttext
        return [resulttext, cal_result, cal_fraction]

    @staticmethod
    def _num2str(number):
        """把数值转换成便于阅读的字符串。"""
        if isinstance(number, float):
            return f"{number:g}"
        return str(number)

    def _check_if_vaild(self, oridata: str) -> bool:
        """检查表达式的基础格式，格式非法时返回 True。"""
        oridata = ''.join(oridata.split())
        if oridata == '':
            return True
        if oridata.count('(') != oridata.count(')'):
            return True
        return re.fullmatch(self._patterns["expression"], oridata) is None

    def _evaluate(self, expression):
        """解析并计算一个不含赋值号的表达式。"""
        self._tokens = self._tokenize(expression)
        self._index = 0
        self._sqrt = None
        value = self._parse_binary(1)
        if self._index < len(self._tokens):
            raise SyntaxError(f"unexpected token '{self._tokens[self._index]}'.")
        return value

    def _tokenize(self, expression):
        """把表达式切分成记号。"""
        tokens = []
        index = 0
        while index < len(expression):
            char = expression[index]
            if expression[index:index + 2] == '//':
                tokens.append('//')
                index += 2
            elif char in '+-*/%^(),=':
                tokens.append(char)
                index += 1
            elif char.isdigit() or char == '.':
                number = self._patterns["number"].match(expression, index)
                if number is None:
                    raise SyntaxError("invalid decimal literal.")
                tokens.append(number.group())
                index = number.end()
            else:
                name = self._patterns["name"].match(expression, index)
                if name is None:
                    raise SyntaxError(f"invalid character '{char}'.")
                tokens.append(name.group())
                index = name.end()
        return tokens

    def _parse_binary(self, min_precedence):
        """解析二元运算（优先级爬升）。"""
        left = self._parse_unary()
        while self._index < len(self._tokens):
            operator = self._tokens[self._index]
            if operator not in self.symbol.opsymbols:
                break
            precedence = self.symbol.precedence[operator]
            if precedence < min_precedence:
                break
            self._index += 1
            right = self._parse_binary(precedence + 1)
            left = self._operate(operator, left, right)
        return left

    def _parse_unary(self):
        """解析正负号。"""
        if self._index < len(self._tokens) and self._tokens[self._index] in ['+', '-']:
            operator = self._tokens[self._index]
            self._index += 1
            operand = self._parse_unary()
            return operand if operator == '+' else -operand
        return self._parse_power()

    def _parse_power(self):
        """解析幂运算（右结合）。"""
        left = self._parse_primary()
        if self._index < len(self._tokens) and self._tokens[self._index] == '^':
            self._index += 1
            right = self._parse_unary()
            return self._operate('^', left, right)
        return left

    def _parse_primary(self):
        """解析数字、变量、函数调用与括号。"""
        if self._index >= len(self._tokens):
            raise SyntaxError("unexpected EOF while parsing.")
        token = self._tokens[self._index]
        self._index += 1
        if token == '(':
            value = self._parse_binary(1)
            if self._index >= len(self._tokens):
                raise SyntaxError("unexpected EOF while parsing.")
            if self._tokens[self._index] != ')':
                raise SyntaxError(f"unexpected token '{self._tokens[self._index]}'.")
            self._index += 1
            return value
        if token == ')':
            raise SyntaxError("unmatched ')'.")
        if token[0].isdigit() or token[0] == '.':
            return self._parse_number(token)
        if token[0].isalpha() or token[0] == '_':
            return self._parse_symbol(token)
        raise SyntaxError(f"unexpected token '{token}'.")

    def _parse_number(self, token):
        """把数字记号转换成精确的数值。"""
        if '.' in token or 'e' in token.lower():
            return Fraction(token)
        return int(token)

    def _parse_symbol(self, token):
        """解析变量与函数调用。"""
        if self._index < len(self._tokens) and self._tokens[self._index] == '(':
            self._index += 1
            arguments = []
            if self._index < len(self._tokens) and self._tokens[self._index] == ')':
                self._index += 1
                return self._call_function(token, arguments)
            while True:
                arguments.append(self._parse_binary(1))
                if self._index >= len(self._tokens):
                    raise SyntaxError("unexpected EOF while parsing.")
                if self._tokens[self._index] == ',':
                    self._index += 1
                    continue
                if self._tokens[self._index] != ')':
                    raise SyntaxError(f"unexpected token '{self._tokens[self._index]}'.")
                self._index += 1
                return self._call_function(token, arguments)
        if token not in self.varibles:
            raise NameError(f"name '{token}' is not defined.")
        return self.varibles[token]

    def _operate(self, operator, left, right):
        """按运算符计算两个操作数。"""
        if operator == '^':
            return self._power(left, right)
        try:
            return self.symbol.opsymbols[operator](left, right)
        except ZeroDivisionError:
            if operator == '/':
                raise ZeroDivisionError("division by zero.")
            raise ZeroDivisionError("integer division or modulo by zero.")

    def _power(self, base, exponent):
        """计算幂，整数指数使用 Fraction 精确计算。"""
        if isinstance(exponent, Fraction) and exponent.denominator == 1:
            exponent = exponent.numerator
        if isinstance(exponent, float) and exponent.is_integer():
            exponent = int(exponent)
        if isinstance(exponent, int):
            if abs(exponent) > self.max_exponent:
                raise OverflowError(f"the absolute value of the exponent must not be larger than "
                                    f"{self.max_exponent}.")
            if isinstance(base, float):
                if math.isinf(base) or math.isnan(base):
                    return base
                base = Fraction(str(base))
            try:
                return Fraction(base) ** exponent
            except ZeroDivisionError:
                raise ZeroDivisionError("division by zero.")
        if isinstance(base, float) and (math.isinf(base) or math.isnan(base)):
            return base
        if float(base) < 0:
            raise ValueError("math domain error.")
        result = basic.pow(float(base), float(exponent))
        if isinstance(result, list):
            return result[1]
        raise CalculateError(result)

    def _call_function(self, name, arguments):
        """调用 Basic 提供的函数。"""
        if name == 'sqrt':
            if not 1 <= len(arguments) <= 2:
                raise TypeError(f"sqrt() takes 1 or 2 arguments but {len(arguments)} were given.")
            result = basic.sqrt(*[float(argument) for argument in arguments])
        elif name in basic.one:
            if len(arguments) != 1:
                raise TypeError(f"{name}() takes 1 argument but {len(arguments)} were given.")
            result = getattr(basic, name)(float(arguments[0]))
        elif name in basic.two:
            if len(arguments) != 2:
                raise TypeError(f"{name}() takes 2 arguments but {len(arguments)} were given.")
            result = getattr(basic, name)(float(arguments[0]), float(arguments[1]))
        else:
            raise NameError(f"function '{name}' is not defined.")
        if isinstance(result, list):
            self._sqrt = result[3]
            return result[1]
        raise CalculateError(result)
