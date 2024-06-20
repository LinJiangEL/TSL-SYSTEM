import re
from scipy.special import comb
from sympy import Eq, solve, factorial
from sympy.core import Symbol
from sympy.parsing.sympy_parser import parse_expr
from cachetools import cached
from config import SYSTEM_DIGMAX, CACHE


class Advanced:
    def __init__(self):
        self.digmax = SYSTEM_DIGMAX

    def ReturnError(self, errors):
        self.error = errors
        return self.error

    @cached(cache=CACHE)
    def Solve_equation(self, expressions: list):
        ecount = ','.join(expressions).count(',')
        if ecount != 1:
            self.ReturnError("ValueError:Solve_equation() takes 2 positional expression but "
                             f"{ecount + 1 if '' not in expressions else len(expressions) - expressions.count('')}"
                             " were given."
                             )
            return self.error
        if '=' in expressions[0] or '=' in expressions[1]:
            return self.ReturnError("ValueError:one more '=' was found in the equation, it was unnecessary.")

        # (\d)([a-zA-Z]) 包含两个捕获组：
        #     (\d)：匹配一个数字字符，即0-9之间的任意一个数字。
        #     ([a - zA - Z])：匹配一个英文字母，即大小写字母a到z之间的任意一个字符。
        # r'\1*\2'：
        #     \1：表示第一个捕获组匹配到的内容，即数字字符。
        #     * ：表示乘法操作符。我们希望在数字和字母之间插入这个乘法操作符。
        #     \2：表示第二个捕获组匹配到的内容，即英文字母。

        expression1 = parse_expr(re.sub(r'(\d)\s*([a-zA-Z])', r'\1*\2', expressions[0].replace("^", "**")))
        expression2 = parse_expr(re.sub(r'(\d)\s*([a-zA-Z])', r'\1*\2', expressions[1].replace("^", "**")))
        eq_symbol1 = list(expression1.free_symbols)
        eq_symbol2 = list(expression2.free_symbols)

        variables = list(set(eq_symbol1 + eq_symbol2))
        equation = Eq(expression1, expression2)
        solution = []
        for variable in variables:
            solutions = solve(equation, variable, dict=True)
            for sol in solutions:
                for var, expr in sol.items():
                    solution.append(f"{var} = {expr}")

        return solution

    @cached(cache=CACHE)
    def Solve_equations(self, expressions):
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

        if len(expressions) == 1:
            return self.ReturnError("ValueError:Solve_equations() takes two more equations but one was given.")

        equations = []
        for expression in expressions:
            if expression.count('=') == 1:
                exp1 = parse_expr(re.sub(r'(\d)\s*([a-zA-Z])', r'\1*\2', expression.split('=')[0].replace("^", "**")))
                exp2 = parse_expr(re.sub(r'(\d)\s*([a-zA-Z])', r'\1*\2', expression.split('=')[1].replace("^", "**")))
                equations.append((exp1, exp2))
            elif expression.count('=') > 1:
                return self.ReturnError("ValueError:one more '=' was found in the equation, it was unsupported.")
            else:
                return self.ReturnError("ValueError:'=' was not found in the equation, it was necessary.")

        return _solve(equations)

    @cached(cache=CACHE)
    def Permutation(self, n, m=None):
        m = n if m is None else m
        if n * m < 0 or isinstance(n, float) or isinstance(m, float):
            return self.ReturnError('m or n must be a positive integer.')
        elif not 0 <= m <= n:
            return self.ReturnError("ValueError:'m' and 'n' must meet the condition '0<=m<=n'.")
        else:
            return int(factorial(n) // factorial(n - m))

    @cached(cache=CACHE)
    def Combination(self, n, m):
        if n * m < 0 or isinstance(n, float) or isinstance(m, float):
            return self.ReturnError("TypeError:'m' or 'n' must be a positive integer.\n")
        elif not 0 <= m <= n:
            return self.ReturnError("ValueError:'m' and 'n' must meet the condition '0<=m<=n'.\n")
        else:
            try:
                return comb(n, m, exact=True)
            except OverflowError:
                return self.ReturnError("OverflowError: factorial() argument should not exceed 2147483647.\n")
