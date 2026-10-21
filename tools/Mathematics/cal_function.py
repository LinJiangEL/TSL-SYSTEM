#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.
"""高阶函数分析与绘图模块。

该模块提供独立的函数分析 REPL：可以定义函数（f(x)=...）、曲线（y1=...）、
变量（a=2），对函数求值（f(2)），并在窗口或终端中绘制函数图像。
"""

import math
import os
import re
import shutil
import subprocess
import sys
from fractions import Fraction

import sympy
from sympy.core.sympify import SympifyError
from sympy.parsing.sympy_parser import parse_expr
from prettytable import PrettyTable

from config import SYSTEM_DIR, Tools_DIR, PageReader
from sysmgr import TempManager
from tools.__built_in__ import style
from tools.__built_in__.helptool import HelpTool
from tools.Mathematics.cal_basic import (Basic, expression_text, format_error,
                                         to_fraction)

try:
    from sympy.parsing.sympy_parser import TokenError
except ImportError:  # pragma: no cover - only for very old sympy versions
    TokenError = SyntaxError

SYMBOL_X = sympy.Symbol('x')
BASIC = Basic()
MATHDIR = os.path.join(Tools_DIR, 'Mathematics')
DEFAULT_XRANGE = (-10.0, 10.0)
DEFAULT_WIDTH = 60
DEFAULT_HEIGHT = 20
MAX_RANGE = 10 ** 6
CURVE_SYMBOLS = '123456789abcdefghijklmnopqrstuvwxyz'
FUNCTIONS = {
    'sin': sympy.sin, 'cos': sympy.cos, 'tan': sympy.tan,
    'asin': sympy.asin, 'acos': sympy.acos, 'atan': sympy.atan,
    'sinh': sympy.sinh, 'cosh': sympy.cosh, 'tanh': sympy.tanh,
    'sqrt': sympy.sqrt, 'abs': sympy.Abs, 'exp': sympy.exp,
    'log': sympy.log, 'ln': sympy.log, 'log10': lambda value: sympy.log(value, 10),
    'floor': sympy.floor, 'ceil': sympy.ceiling, 'sign': sympy.sign,
}
CURVE_PATTERN = re.compile(r'^[yY](?P<index>\d*)\s*=\s*(?P<body>.+)$')
FUNCTION_PATTERN = re.compile(r'^(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\(\s*x\s*\)\s*=\s*(?P<body>.+)$')
VARIABLE_PATTERN = re.compile(r'^(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<body>.+)$')
CALL_PATTERN = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(')
NUMBER_PATTERN = re.compile(r'^[+\-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?$')


def _matplotlib_available():
    """判断当前环境是否可以使用 matplotlib。"""
    try:
        import matplotlib
        return True
    except ImportError:
        return False


def _parse_expression(text):
    """把用户输入的数学表达式转换成 sympy 表达式。"""
    text = text.strip()
    text = text.replace('^', '**')
    text = re.sub(r'(?<=\d)(?![eE][+\-]?\d)(?=[A-Za-z_(])', '*', text)
    text = re.sub(r'(?<=\))(?=[A-Za-z0-9_(])', '*', text)
    return parse_expr(text, local_dict=dict(FUNCTIONS))


def _lambdify(expression):
    """把 sympy 表达式转换成可调用的数值函数。"""
    modules = [{'Abs': abs, 'ceiling': math.ceil, 'floor': math.floor,
                'sign': lambda value: (value > 0) - (value < 0)}, 'math']
    return sympy.lambdify(SYMBOL_X, expression, modules=modules)


def _percentile(values, ratio):
    """取排序后列表的指定分位值。"""
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * ratio))
    return ordered[min(max(index, 0), len(ordered) - 1)]


class FunctionAnalyzer:
    """函数分析器，负责解析输入、求值与绘图。"""

    def __init__(self, backend='auto', width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        if backend == 'auto':
            backend = 'window' if _matplotlib_available() else 'ascii'
        self.backend = backend
        self.width = width
        self.height = height
        self.x_range = DEFAULT_XRANGE
        self.y_range = None
        self.curves = []
        self.functions = {}
        self.variables = {}
        self.figure = None
        self.axes = None

    def _fraction_of(self, value):
        """把 sympy 数值转换成 Basic 可以显示的分数。"""
        try:
            if value.is_Integer:
                return Fraction(int(value))
            if value.is_Rational:
                return Fraction(int(value.p), int(value.q))
        except (AttributeError, TypeError):
            pass
        try:
            return to_fraction(float(value), BASIC.digmax)
        except (TypeError, ValueError, OverflowError):
            return None

    def _substitute(self, expression):
        """代入已经定义的变量。"""
        if not self.variables:
            return expression
        return expression.subs({sympy.Symbol(name): value
                                for name, value in self.variables.items()})

    def _check_symbols(self, expression):
        """检查表达式中的未知符号。"""
        known = set(self.variables) | {'x'}
        for symbol in sorted(expression.free_symbols, key=str):
            if str(symbol) not in known:
                raise NameError("name '%s' is not defined." % symbol)

    def _expand_calls(self, text):
        """把已定义函数的调用展开成对应的表达式。"""
        if not self.functions:
            return text
        names = sorted(self.functions, key=len, reverse=True)
        pattern = re.compile(r'\b(%s)\s*\(' % '|'.join(re.escape(name) for name in names))
        for _ in range(64):
            match = pattern.search(text)
            if match is None:
                return text
            start = match.end()
            depth = 1
            index = start
            while index < len(text):
                if text[index] == '(':
                    depth = depth + 1
                elif text[index] == ')':
                    depth = depth - 1
                    if depth == 0:
                        break
                index = index + 1
            if depth != 0:
                return text
            argument = text[start:index]
            body = self.functions[match.group(1)]['body']
            replaced = re.sub(r'(?<![A-Za-z_])x(?![A-Za-z0-9_])',
                              '(%s)' % argument, body)
            text = text[:match.start()] + '(%s)' % replaced + text[index + 1:]
        raise SyntaxError('the function call is nested too deeply.')

    def _check_calls(self, text):
        """检查表达式里未定义的函数名。"""
        for name in CALL_PATTERN.findall(text):
            if name not in FUNCTIONS and name not in self.functions:
                raise NameError("function '%s' is not defined." % name)

    def add_curve(self, name, body):
        """添加或替换一条曲线。"""
        try:
            self._check_calls(body)
            expression = _parse_expression(self._expand_calls(body))
            self._check_symbols(expression)
        except (SympifyError, TokenError, SyntaxError, TypeError, ValueError) as error:
            return format_error('SyntaxError: %s' % (error or 'invalid syntax.'))
        except NameError:
            raise
        index = 0
        for position, curve in enumerate(self.curves):
            if curve['name'] == name:
                index = position
                break
        curve = {'name': name, 'kind': 'curve', 'body': body,
                 'expression': expression}
        if index or any(item['name'] == name for item in self.curves):
            self.curves[index] = curve
        else:
            self.curves.append(curve)
        return "Curve '%s = %s' was added." % (name, body)

    def define_function(self, name, body):
        """定义函数 f(x)=... 并同时把它的图像加入图中。"""
        if name in FUNCTIONS:
            return format_error("NameError: '%s' is a built-in function." % name)
        if name in self.variables:
            return format_error("NameError: '%s' is already a variable." % name)
        try:
            self._check_calls(body)
            expression = _parse_expression(self._expand_calls(body))
            self._check_symbols(expression)
        except (SympifyError, TokenError, SyntaxError, TypeError, ValueError) as error:
            return format_error('SyntaxError: %s' % (error or 'invalid syntax.'))
        except NameError:
            raise
        self.functions[name] = {'body': body, 'expression': expression}
        label = '%s(x)' % name
        curve = {'name': label, 'kind': 'function', 'body': body,
                 'expression': expression}
        for position, item in enumerate(self.curves):
            if item['name'] == label:
                self.curves[position] = curve
                break
        else:
            self.curves.append(curve)
        return "Function '%s(x) = %s' was defined." % (name, body)

    def define_variable(self, name, body):
        """定义一个数值变量。"""
        if name in FUNCTIONS:
            return format_error("NameError: '%s' is a built-in function." % name)
        if name == 'x':
            return format_error("NameError: 'x' is reserved for functions and curves.")
        if name in self.functions:
            return format_error("NameError: '%s' is already a function." % name)
        try:
            self._check_calls(body)
            expression = _parse_expression(self._expand_calls(body))
            self._check_symbols(expression)
        except (SympifyError, TokenError, SyntaxError, TypeError, ValueError) as error:
            return format_error('SyntaxError: %s' % (error or 'invalid syntax.'))
        except NameError:
            raise
        expression = self._substitute(expression)
        if expression.free_symbols:
            return format_error("ValueError: the value of '%s' must be a number." % name)
        try:
            float(expression)
        except (TypeError, ValueError):
            return format_error("ValueError: the value of '%s' must be a real number." % name)
        self.variables[name] = expression
        return "Variable '%s = %s' was defined." % (name, self._variable_text(expression))

    @staticmethod
    def _variable_text(expression):
        """把变量值转换成便于阅读的文本。"""
        try:
            if expression.is_Integer:
                return str(int(expression))
        except AttributeError:
            pass
        try:
            return str(sympy.N(expression, 12))
        except (TypeError, ValueError):
            return str(expression)

    def evaluate(self, text):
        """计算一个不含 x 的表达式。"""
        try:
            self._check_calls(text)
            expression = _parse_expression(self._expand_calls(text))
            self._check_symbols(expression)
            expression = self._substitute(expression)
            if SYMBOL_X in expression.free_symbols:
                return format_error("ValueError: 'x' cannot be evaluated here, "
                                    "please define a curve like 'y1=...' or a function like 'f(x)=...'.")
            if expression.free_symbols:
                return format_error("NameError: name '%s' is not defined."
                                    % sorted(expression.free_symbols, key=str)[0])
            value = sympy.N(expression, 15)
            if value == sympy.zoo:
                return format_error('ZeroDivisionError: division by zero.')
            if value.is_real is False:
                raise ValueError('math domain error.')
            number = float(value)
        except NameError:
            raise
        except (SympifyError, TokenError, SyntaxError, TypeError, ValueError, OverflowError) as error:
            return format_error('%s: %s' % (type(error).__name__, error or 'invalid value.'))
        if value.has(sympy.oo, -sympy.oo, sympy.nan):
            return format_error('ValueError: the result is not a real number.')
        fraction = self._fraction_of(value)
        block = BASIC.resultformat(cal_result=number, cal_fraction=fraction)[0]
        return expression_text(text) + '\n' + block

    def describe(self):
        """列出当前定义的曲线、函数与变量。"""
        lines = []
        if self.curves:
            table = PrettyTable(['Name', 'Kind', 'Expression'])
            table.align = 'l'
            for curve in self.curves:
                table.add_row([curve['name'], curve['kind'], curve['body']])
            lines.append('Functions and curves:')
            lines.append(str(table))
        else:
            lines.append('No function or curve is defined yet.')
        if self.variables:
            table = PrettyTable(['Variable', 'Value'])
            table.align = 'l'
            for name in self.variables:
                table.add_row([name, self._variable_text(self.variables[name])])
            lines.append('Variables:')
            lines.append(str(table))
        return '\n'.join(lines)

    def set_range(self, arguments):
        """设置 x 轴与（可选的）y 轴显示范围。"""
        parts = [item for item in re.split(r'\s*,\s*|\s+', arguments.strip()) if item]
        if len(parts) not in (2, 4):
            return format_error("CommandUsageError: range needs 'XMIN XMAX' or 'XMIN XMAX YMIN YMAX'.")
        for part in parts:
            if not NUMBER_PATTERN.fullmatch(part):
                return format_error("ValueError: '%s' is not a valid number." % part)
        numbers = [float(part) for part in parts]
        for number in numbers:
            if not math.isfinite(number) or abs(number) > MAX_RANGE:
                return format_error('ValueError: the range must be a finite number '
                                    'whose absolute value is not larger than %d.' % MAX_RANGE)
        if len(numbers) == 2:
            if numbers[0] >= numbers[1]:
                return format_error('ValueError: XMIN must be smaller than XMAX.')
            self.x_range = (numbers[0], numbers[1])
            self.y_range = None
        else:
            if numbers[0] >= numbers[1] or numbers[2] >= numbers[3]:
                return format_error('ValueError: MIN must be smaller than MAX.')
            self.x_range = (numbers[0], numbers[1])
            self.y_range = (numbers[2], numbers[3])
        return ('The display range is x:[%g, %g], y:%s.'
                % (self.x_range[0], self.x_range[1],
                   'automatic' if self.y_range is None
                   else '[%g, %g]' % self.y_range))

    def remove(self, name):
        """删除一条曲线或一个函数。"""
        for position, curve in enumerate(self.curves):
            if curve['name'] == name or curve['name'].split('(')[0] == name:
                del self.curves[position]
                self.functions.pop(name, None)
                return "'%s' was removed." % name
        return format_error("NameError: '%s' was not defined." % name)

    def clear(self):
        """清空全部函数、曲线与变量。"""
        self.curves = []
        self.functions = {}
        self.variables = {}
        return 'All functions, curves and variables were cleared.'

    def _sample(self, curve, points=400):
        """对一条曲线采样，返回有限值的坐标列表。"""
        expression = self._substitute(curve['expression'])
        if expression.free_symbols - {SYMBOL_X}:
            raise NameError("name '%s' is not defined."
                            % sorted(expression.free_symbols - {SYMBOL_X}, key=str)[0])
        function = _lambdify(expression)
        x_min, x_max = self.x_range
        xs, ys = [], []
        for index in range(points):
            x_value = x_min + (x_max - x_min) * index / (points - 1)
            try:
                y_value = function(x_value)
            except (TypeError, ValueError, ZeroDivisionError, OverflowError):
                continue
            if isinstance(y_value, complex):
                continue
            if y_value is None or not math.isfinite(y_value):
                continue
            xs.append(x_value)
            ys.append(y_value)
        return xs, ys

    def _limits(self, samples):
        """根据采样结果计算 y 轴的显示范围。"""
        values = []
        for _, _, ys in samples:
            values.extend(ys)
        if not values:
            return None
        if self.y_range is not None:
            return self.y_range
        low = _percentile(values, 0.02)
        high = _percentile(values, 0.98)
        if low == high:
            padding = abs(low) * 0.1 if low else 1.0
            low, high = low - padding, high + padding
        else:
            padding = (high - low) * 0.05
            low, high = low - padding, high + padding
        return low, high

    def _samples(self):
        """对全部曲线采样。"""
        samples = []
        for curve in self.curves:
            xs, ys = self._sample(curve)
            samples.append((curve, xs, ys))
        return samples

    def legend(self):
        """生成图例文本列表。"""
        return ['[%s] %s = %s' % (CURVE_SYMBOLS[index % len(CURVE_SYMBOLS)],
                                  curve['name'], curve['body'])
                for index, curve in enumerate(self.curves)]

    def ascii_plot(self):
        """在终端里绘制函数图像。"""
        if not self.curves:
            return 'No function or curve is defined yet, please input like "y1=x+2".'
        samples = self._samples()
        limits = self._limits(samples)
        if limits is None:
            return 'No finite value could be sampled in the current range.'
        y_min, y_max = limits
        x_min, x_max = self.x_range
        grid = [[' '] * self.width for _ in range(self.height)]

        def row_of(value):
            row = int(round((y_max - value) / (y_max - y_min) * (self.height - 1)))
            return min(max(row, 0), self.height - 1)

        def column_of(value):
            column = int(round((value - x_min) / (x_max - x_min) * (self.width - 1)))
            return min(max(column, 0), self.width - 1)

        for index, (curve, xs, ys) in enumerate(samples):
            symbol = CURVE_SYMBOLS[index % len(CURVE_SYMBOLS)]
            for x_value, y_value in zip(xs, ys):
                if y_min <= y_value <= y_max:
                    grid[row_of(y_value)][column_of(x_value)] = symbol
        if y_min <= 0 <= y_max:
            axis_row = row_of(0)
            for column in range(self.width):
                if grid[axis_row][column] == ' ':
                    grid[axis_row][column] = '-'
        if x_min <= 0 <= x_max:
            axis_column = column_of(0)
            for row in range(self.height):
                if grid[row][axis_column] == ' ':
                    grid[row][axis_column] = '|'

        lines = ['y: [%g, %g]' % (y_min, y_max)]
        for row in grid:
            lines.append('  ' + ''.join(row))
        lines.append('x: [%g, %g]' % (x_min, x_max))
        lines.append('')
        lines.extend('  ' + item for item in self.legend())
        return '\n'.join(lines)

    def _draw_axes(self, axes, samples, limits):
        """在 matplotlib 的坐标系里绘制全部曲线。"""
        import matplotlib.pyplot as plt
        y_min, y_max = limits
        for index, (curve, xs, ys) in enumerate(samples):
            axes.plot(xs, ys, linewidth=1.6,
                      color='C%d' % (index % 10), label=curve['name'] + ' = ' + curve['body'])
        axes.set_xlim(self.x_range)
        axes.set_ylim(y_min, y_max)
        axes.grid(True, linestyle=':', linewidth=0.6, alpha=0.7)
        axes.axhline(0, color='black', linewidth=0.8)
        axes.axvline(0, color='black', linewidth=0.8)
        axes.set_xlabel('x')
        axes.set_ylabel('y')
        axes.set_title('TSL-SYSTEM Function Analysis')
        axes.legend(loc='best', fontsize=8)
        plt.tight_layout()

    def render(self):
        """刷新函数图像。"""
        if not self.curves:
            return 'No function or curve is defined yet, please input like "y1=x+2".'
        samples = self._samples()
        limits = self._limits(samples)
        if limits is None:
            return 'No finite value could be sampled in the current range.'
        if self.backend == 'ascii':
            return self.ascii_plot()
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            self.backend = 'ascii'
            return ('ModuleNotFoundError:matplotlib is not installed, '
                    'the ASCII plot is used instead.\n' + self.ascii_plot())
        if self.figure is None:
            try:
                plt.ion()
                self.figure, self.axes = plt.subplots(figsize=(7.5, 4.8))
            except Exception:
                self.backend = 'ascii'
                return ('RuntimeError:the graphic window cannot be opened, '
                        'the ASCII plot is used instead.\n' + self.ascii_plot())
            try:
                self.figure.canvas.manager.set_window_title('TSL-SYSTEM Function Analysis')
            except AttributeError:
                pass
        self.axes.clear()
        self._draw_axes(self.axes, samples, limits)
        self.figure.canvas.draw_idle()
        try:
            plt.pause(0.05)
        except (ValueError, RuntimeError):
            pass
        return 'The plot was refreshed with %d curve(s).' % len(self.curves)

    def save(self, path=None):
        """把当前函数图像保存成 PNG 文件。"""
        if not self.curves:
            return format_error('ValueError: no function or curve is defined yet.')
        samples = self._samples()
        limits = self._limits(samples)
        if limits is None:
            return format_error('ValueError: no finite value could be sampled '
                                'in the current range.')
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg
        except ImportError:
            return format_error('ModuleNotFoundError:matplotlib is not installed.')
        if path is None:
            path = os.path.join(SYSTEM_DIR, 'Temp', 'function_plot.png')
        path = os.path.abspath(os.path.expanduser(path))
        directory = os.path.dirname(path)
        if directory and not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except OSError as error:
                return format_error('OSError: %s' % error)
        figure = Figure(figsize=(7.5, 4.8))
        canvas = FigureCanvasAgg(figure)
        axes = figure.add_subplot(1, 1, 1)
        self._draw_axes(axes, samples, limits)
        try:
            canvas.print_png(path)
        except OSError as error:
            return format_error('OSError: %s' % error)
        return "The function plot was saved to '%s'." % path

    def handle(self, text):
        """处理一行函数分析输入，返回需要打印的文本。"""
        text = text.strip()
        if text == '':
            return ''
        match = CURVE_PATTERN.match(text)
        if match is not None:
            index = match.group('index') or str(self._next_curve_index())
            name = 'y%s' % index
            try:
                return self.add_curve(name, match.group('body'))
            except NameError as error:
                return format_error('NameError: %s' % error)
        match = FUNCTION_PATTERN.match(text)
        if match is not None:
            try:
                return self.define_function(match.group('name'), match.group('body'))
            except NameError as error:
                return format_error('NameError: %s' % error)
        match = VARIABLE_PATTERN.match(text)
        if match is not None:
            try:
                return self.define_variable(match.group('name'), match.group('body'))
            except NameError as error:
                return format_error('NameError: %s' % error)
        try:
            return self.evaluate(text)
        except NameError as error:
            return format_error('NameError: %s' % error)

    def _next_curve_index(self):
        """计算下一条曲线的默认编号。"""
        indexes = []
        for curve in self.curves:
            match = re.match(r'^[yY](\d+)$', curve['name'])
            if match is not None:
                indexes.append(int(match.group(1)))
        return max(indexes, default=0) + 1

    def close(self):
        """关闭绘图窗口。"""
        if self.figure is not None:
            try:
                import matplotlib.pyplot as plt
                plt.close(self.figure)
            except (ImportError, ValueError, RuntimeError):
                pass
            self.figure = None
            self.axes = None


def open_function_window():
    """在独立窗口中打开函数分析 REPL，返回提示文本。"""
    command = [sys.executable, '-m', 'tools.Mathematics.cal_function']
    try:
        if sys.platform == 'win32':
            subprocess.Popen(command, cwd=SYSTEM_DIR,
                             creationflags=subprocess.CREATE_NEW_CONSOLE)
            return 'A new function-analysis window was opened.'
        for terminal, option in (('x-terminal-emulator', '-e'),
                                 ('gnome-terminal', '--'),
                                 ('konsole', '-e'), ('xterm', '-e')):
            executable = shutil.which(terminal)
            if executable:
                subprocess.Popen([executable, option] + command, cwd=SYSTEM_DIR,
                                 start_new_session=True)
                return 'A new function-analysis window was opened with %s.' % terminal
    except OSError as error:
        return format_error('OSError: %s' % error)
    return ('RuntimeError: no terminal emulator was found, please run '
            "'python -m tools.Mathematics.cal_function' by yourself.")


def _read_input(prompt):
    """读取一行输入，遇到中断时返回 None。"""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def _show(analyzer, text):
    """打印结果并刷新图像。"""
    if text:
        print(text)
    try:
        result = analyzer.render()
    except NameError as error:
        result = format_error('NameError: %s' % error)
    if result:
        print(result)
    print()


def run(backend='auto'):
    """函数分析 REPL。"""
    style.banner('TSL-SYSTEM Function Analysis', width=37)
    analyzer = FunctionAnalyzer(backend=backend)
    print("Input 'y1=x+2' or 'f(x)=2x+1' to add a curve, 'f(2)' to evaluate it,\n"
          "'@help' to show the help page, '@exit' to return to the terminal.\n")
    while True:
        command = _read_input(style.prompt('(function)'))
        if command is None:
            break
        if command == '':
            continue
        lowered = command.lower()
        if lowered == '@exit':
            print()
            break
        if lowered == '@help':
            HelpTool(MATHDIR, PageReader, 'function')
            continue
        if lowered == '@flush':
            TempManager().Flush('Function Analysis Module')
            continue
        if lowered in ('@plot', '@draw', '@show'):
            result = analyzer.render()
            print(result if result else '')
            print()
            continue
        if lowered in ('@list', '@ls'):
            print(analyzer.describe())
            print()
            continue
        if lowered in ('@clear', '@reset'):
            print(analyzer.clear())
            analyzer.close()
            print()
            continue
        if lowered.startswith('range ') or lowered.startswith('range:'):
            print(analyzer.set_range(command[6:].lstrip(': ')))
            _show(analyzer, '')
            continue
        if lowered.startswith('ylim '):
            print(analyzer.set_range('%g %g %s' % (analyzer.x_range[0],
                                                   analyzer.x_range[1],
                                                   command[5:].strip())))
            _show(analyzer, '')
            continue
        if lowered.startswith('remove ') or lowered.startswith('del ') or lowered.startswith('rm '):
            print(analyzer.remove(command.split(None, 1)[1].strip()))
            _show(analyzer, '')
            continue
        if lowered.startswith('save'):
            path = command[4:].strip() or None
            print(analyzer.save(path))
            print()
            continue
        if lowered in ('@window', '@new'):
            print('This REPL already has its own window.')
            print()
            continue
        bare = {'list': '@list', 'ls': '@list', 'plot': '@plot', 'draw': '@plot',
                'show': '@plot', 'clear': '@clear', 'reset': '@clear',
                'window': '@window', 'new': '@window', 'help': '@help',
                'exit': '@exit', 'flush': '@flush'}
        if lowered in bare:
            print("NameError: the command '%s' needs no argument, please input '%s'."
                  % (command, bare[lowered]))
            print()
            continue
        try:
            message = analyzer.handle(command)
        except NameError as error:
            message = format_error('NameError: %s' % error)
        _show(analyzer, message)
    analyzer.close()
    return 0


if __name__ == '__main__':
    sys.exit(run())
