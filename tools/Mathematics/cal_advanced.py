#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

import re
from sympy import Eq, solve, factorial
from sympy.core import Symbol
from sympy.core.sympify import SympifyError
from sympy.parsing.sympy_parser import parse_expr
from scipy.special import comb
from cachetools import cached
from config import SYSTEM_DIGMAX, CACHE
from tools.Mathematics.cal_basic import format_error, expression_text, result_text

MULTIPLY_PATTERN = re.compile(r'(\d)\s*([a-zA-Z])')
INTEGER_PATTERN = re.compile(r'^[+\-]?\d+$')


def is_integer(text):
    """判断文本是否为一个合法的整数。"""
    return INTEGER_PATTERN.fullmatch(str(text).strip()) is not None


def parse_expression(expression):
    """把用户输入的表达式转换成 sympy 表达式。"""
    text = MULTIPLY_PATTERN.sub(r'\1*\2', expression.replace('^', '**'))
    return parse_expr(text)


class Advanced:
    def __init__(self):
        self.digmax = SYSTEM_DIGMAX
        self.error = ""

    def resultformat(self, cal_result, cal_fraction=None, cal_sqrt=None):
        return result_text(cal_result, cal_fraction, cal_sqrt, self.digmax)

    def ReturnError(self, errors):
        self.error = format_error(errors)
        return self.error

    def Solve_equation(self, expressions: list):
        """解一个等式，返回形如 'x = 2' 的解列表。"""
        if len(expressions) != 2:
            return self.ReturnError("TypeError: Solve_equation() takes 2 expressions but %d %s given."
                                    % (len(expressions), 'was' if len(expressions) == 1 else 'were'))
        for expression in expressions:
            if '=' in expression:
                return self.ReturnError("SyntaxError: '=' is not allowed in Solve_equation(), "
                                        "please use Solve_equations() instead.")
        try:
            expression1 = parse_expression(expressions[0])
            expression2 = parse_expression(expressions[1])
        except (SympifyError, SyntaxError, TypeError, ValueError):
            return self.ReturnError("SyntaxError: the expression is not valid, please check the operands.")
        eq_symbol1 = list(expression1.free_symbols)
        eq_symbol2 = list(expression2.free_symbols)

        variables = list(set(eq_symbol1 + eq_symbol2))
        if not variables:
            return self.ReturnError("ValueError: no unknown symbol was found in the equation.")
        equation = Eq(expression1, expression2)
        solution = []
        try:
            solutions = solve(equation, variables[0], dict=True)
        except (NotImplementedError, ValueError):
            return self.ReturnError("ValueError: the equation cannot be solved.")
        for sol in solutions:
            for var, expr in sol.items():
                solution.append(f"{var} = {expr}")
        if not solution:
            return self.ReturnError("ValueError: no solution was found.")
        return solution

    def Solve_equations(self, expressions):
        """解方程组，返回由解字典组成的列表。"""
        def _extract_variables(eqs):
            vars_set = set()
            for eq in eqs:
                for term in eq[0].as_ordered_terms() + eq[1].as_ordered_terms():
                    for atom in term.atoms():
                        if isinstance(atom, Symbol):
                            vars_set.add(atom)
            return list(vars_set)

        def _solve(eqs):
            _variables = _extract_variables(eqs)
            _equations = [Eq(eq[0], eq[1]) for eq in eqs]
            _solutions = solve(_equations, _variables)

            format_result = []
            if isinstance(_solutions, list):
                for sol in _solutions:
                    format_sol = {str(var): val for var, val in zip(_variables, sol)}
                    format_result.append(dict(sorted(format_sol.items(), key=lambda m: m[0])))
            else:
                format_sol = {str(var): val for var, val in _solutions.items()}
                format_result.append(dict(sorted(format_sol.items(), key=lambda m: m[0])))
            return format_result

        if len(expressions) < 2:
            return self.ReturnError("TypeError: Solve_equations() takes at least 2 equations but %d %s given."
                                    % (len(expressions), 'was' if len(expressions) == 1 else 'were'))

        equations = []
        for expression in expressions:
            if expression.count('=') == 1:
                try:
                    exp1 = parse_expression(expression.split('=')[0])
                    exp2 = parse_expression(expression.split('=')[1])
                except (SympifyError, SyntaxError, TypeError, ValueError):
                    return self.ReturnError("SyntaxError: the equation is not valid, please check the operands.")
                equations.append((exp1, exp2))
            elif expression.count('=') > 1:
                return self.ReturnError("SyntaxError: more than one '=' was found in the equation, "
                                        "it was unsupported.")
            else:
                return self.ReturnError("SyntaxError: '=' was not found in the equation, it was necessary.")

        try:
            solutions = _solve(equations)
        except (NotImplementedError, ValueError):
            return self.ReturnError("ValueError: the equations cannot be solved.")
        if not solutions:
            return self.ReturnError("ValueError: no solution was found.")
        return solutions

    @cached(cache=CACHE)
    def Permutation(self, n, m=None):
        m = n if m is None else m
        if not isinstance(n, int) or isinstance(n, bool) or not isinstance(m, int) or isinstance(m, bool):
            return self.ReturnError("TypeError: 'm' or 'n' must be a positive integer.")
        if n < 0 or m < 0:
            return self.ReturnError("ValueError: 'm' and 'n' must not be negative.")
        if not 0 <= m <= n:
            return self.ReturnError("ValueError: 'm' and 'n' must meet the condition '0<=m<=n'.")
        try:
            return int(factorial(n) // factorial(n - m))
        except (OverflowError, ValueError):
            return self.ReturnError("OverflowError: the result is too large to be calculated.")

    @cached(cache=CACHE)
    def Combination(self, n, m):
        if not isinstance(n, int) or isinstance(n, bool) or not isinstance(m, int) or isinstance(m, bool):
            return self.ReturnError("TypeError: 'm' or 'n' must be a positive integer.")
        if n < 0 or m < 0:
            return self.ReturnError("ValueError: 'm' and 'n' must not be negative.")
        if not 0 <= m <= n:
            return self.ReturnError("ValueError: 'm' and 'n' must meet the condition '0<=m<=n'.")
        try:
            return comb(n, m, exact=True)
        except OverflowError:
            return self.ReturnError("OverflowError: factorial() argument should not exceed 2147483647.")
