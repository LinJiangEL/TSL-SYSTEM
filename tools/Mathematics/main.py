#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.
from tools.__built_in__ import style

import os
import re
from config import Tools_DIR, PageReader
from sysmgr import TempManager
from tools.__built_in__.helptool import HelpTool
from tools.Mathematics.cal_basic import format_error, is_number, expression_text

mathdir = os.path.join(Tools_DIR, "Mathematics")

IDENTIFY_PATTERN = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*(?:\((.*)\)|(.*))$', re.S)
ADVANCED_ALIASES = {'p': 'Permutation', 'a': 'Permutation', 'c': 'Combination',
                    'permutation': 'Permutation', 'combination': 'Combination',
                    'solve_equation': 'Solve_equation', 'solve_equations': 'Solve_equations'}
METHODS = ('basic', 'advanced', 'compound', 'function')


def _read_input(prompt):
    """读取一行输入，遇到中断时返回 None。"""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def _bare_command_hint(command, extra=None):
    """提示无参数命令必须带 '@' 前缀，命中时返回 True。"""
    name = command.lower()
    if extra is not None and name in extra:
        target = extra[name]
    elif name in ('help', 'exit', 'flush'):
        target = '@' + name
    else:
        return False
    print("NameError: the command '%s' needs no argument, please input '%s'."
          % (command, target))
    print()
    return True


def _split_arguments(text):
    """按逗号或空白切分参数列表。"""
    if text.strip() == '':
        return []
    return [item for item in re.split(r'\s*,\s*|\s+', text.strip()) if item]


def _split_top_level(text):
    """只按最外层的逗号切分参数，括号内的逗号会被保留。"""
    items = []
    depth = 0
    current = []
    for char in text:
        if char == '(':
            depth = depth + 1
        elif char == ')':
            depth = depth - 1
        if char == ',' and depth == 0:
            items.append(''.join(current))
            current = []
        else:
            current.append(char)
    items.append(''.join(current))
    return [item.strip() for item in items if item.strip() != '']


def _number_text(value):
    """把数值还原成便于阅读的表达式片段。"""
    return ('%g' % value) if isinstance(value, float) else str(value)


def _basic_command(basic, command):
    """解析并执行一条 Basic 模块的命令，返回输出文本。"""
    if command.count('(') != command.count(')'):
        return ("SyntaxError: unexpected EOF while parsing."
                if command.count('(') > command.count(')')
                else "SyntaxError: unmatched ')'.")
    match = IDENTIFY_PATTERN.fullmatch(command)
    if match is None:
        return "SyntaxError: invalid syntax, please input like 'add 1,2'."
    name = match.group(1).lower()
    text = match.group(2) if match.group(2) is not None else (match.group(3) or '')
    if name in ('returnerror', 'resultformat', 'iseven'):
        return "NameError: '%s' is an internal symbol of Basic and cannot be called." % name
    available = set(basic.one + basic.two + basic.needlist)
    if name not in available:
        return "NameError: '%s' is not defined in Basic." % name

    arguments = _split_arguments(text)
    if name == 'sqrt':
        expected, counts = '1 or 2', (1, 2)
    elif name in basic.needlist:
        expected, counts = 'at least 1', None
    elif name in basic.one:
        expected, counts = '1', (1,)
    else:
        expected, counts = '2', (2,)
    if counts is not None and len(arguments) not in counts:
        return ("TypeError: %s() takes %s argument%s but %d %s given."
                % (name, expected, '' if expected == '1' else 's', len(arguments),
                   'was' if len(arguments) == 1 else 'were'))
    if len(arguments) == 0:
        return "TypeError: %s() takes %s arguments but 0 were given." % (name, expected)
    for argument in arguments:
        if not is_number(argument):
            return "ValueError: '%s' is not a valid operand." % argument

    values = [float(argument) for argument in arguments]
    expression = '%s(%s)' % (name, ', '.join(_number_text(value) for value in values))
    try:
        if name == 'sqrt':
            outcome = basic.sqrt(*values)
        elif len(values) == 1:
            outcome = getattr(basic, name)(values[0])
        else:
            outcome = getattr(basic, name)(values[0], values[1])
    except (TypeError, ValueError, ZeroDivisionError, OverflowError) as error:
        return format_error('%s: %s' % (type(error).__name__, error))
    resulttext = outcome[0] if isinstance(outcome, list) else str(outcome)
    return expression_text(expression) + '\n' + resulttext


def _advanced_command(advanced, command):
    """解析并执行一条 Advanced 模块的命令，返回输出文本。"""
    if command.count('(') != command.count(')'):
        return ("SyntaxError: unexpected EOF while parsing."
                if command.count('(') > command.count(')')
                else "SyntaxError: unmatched ')'.")
    match = IDENTIFY_PATTERN.fullmatch(command)
    if match is None:
        return "SyntaxError: invalid function call, please input like 'P(9,8)'."
    name = match.group(1)
    text = match.group(2) if match.group(2) is not None else (match.group(3) or '')
    function = ADVANCED_ALIASES.get(name.lower())
    if function is None:
        return "NameError: '%s' is not defined in Advanced." % name

    if function in ('Permutation', 'Combination'):
        arguments = _split_arguments(text)
        if function == 'Combination' and len(arguments) != 2:
            return ("TypeError: Combination() takes 2 arguments but %d were given."
                    % len(arguments))
        if function == 'Permutation' and len(arguments) not in (1, 2):
            return ("TypeError: Permutation() takes 1 or 2 arguments but %d were given."
                    % len(arguments))
        for argument in arguments:
            if not re.fullmatch(r'[+\-]?\d+', argument):
                return "ValueError: '%s' is not a valid integer." % argument
        numbers = [int(argument) for argument in arguments]
        n = numbers[0]
        m = numbers[1] if len(numbers) == 2 else n
        if n < 0 or m < 0:
            return "ValueError: 'm' or 'n' must not be negative."
        m, n = min(m, n), max(m, n)
        try:
            outcome = getattr(advanced, function)(n, m)
        except (TypeError, ValueError, OverflowError) as error:
            return format_error('%s: %s' % (type(error).__name__, error))
        if isinstance(outcome, str):
            return outcome
        expression = '%s(%d, %d)' % (function, n, m)
        return expression_text(expression) + '\n' + advanced.resultformat(outcome)

    arguments = _split_top_level(text)
    if function == 'Solve_equation':
        if len(arguments) != 2:
            return ("TypeError: Solve_equation() takes 2 expressions but %d %s given."
                    % (len(arguments), 'was' if len(arguments) == 1 else 'were'))
        try:
            outcome = advanced.Solve_equation(arguments)
        except (TypeError, ValueError, OverflowError) as error:
            return format_error('%s: %s' % (type(error).__name__, error))
        if isinstance(outcome, str):
            return outcome
        lines = [expression_text('Solve_equation(%s)' % ', '.join(arguments))]
        for index, solution in enumerate(outcome, 1):
            if ' = ' in solution:
                variable, value = solution.split(' = ', 1)
                lines.append('%s%d = %s' % (variable, index, value))
            else:
                lines.append(solution)
        return '\n'.join(lines)

    if function == 'Solve_equations':
        if len(arguments) < 2:
            return ("TypeError: Solve_equations() takes at least 2 equations but %d %s given."
                    % (len(arguments), 'was' if len(arguments) == 1 else 'were'))
        try:
            outcome = advanced.Solve_equations(arguments)
        except (TypeError, ValueError, OverflowError) as error:
            return format_error('%s: %s' % (type(error).__name__, error))
        if isinstance(outcome, str):
            return outcome
        lines = [expression_text('Solve_equations(%s)' % ', '.join(arguments))]
        for index, solution in enumerate(outcome, 1):
            pairs = ', '.join('%s = %s' % (key, solution[key]) for key in solution)
            lines.append('Solution %d: %s' % (index, pairs))
        return '\n'.join(lines)

    return "NameError: '%s' is not defined in Advanced." % name


def _basic_loop():
    from tools.Mathematics.cal_basic import Basic
    basic = Basic()
    print("Input '@help' to show the help page, '@exit' to return to the terminal.\n")
    while True:
        command = _read_input(style.prompt('(basic)'))
        if command is None:
            return True
        if command == '':
            continue
        if command.lower() == '@exit':
            print()
            return False
        if command.lower() == '@help':
            HelpTool(mathdir, PageReader, 'basic')
            continue
        if command.lower() == '@flush':
            TempManager().Flush('Mathematics Basic Module')
            continue
        if _bare_command_hint(command):
            continue
        print(_basic_command(basic, command))
        print()


def _advanced_loop():
    from tools.Mathematics.cal_advanced import Advanced
    advanced = Advanced()
    print("Input '@help' to show the help page, '@exit' to return to the terminal.\n")
    while True:
        command = _read_input(style.prompt('(advanced)'))
        if command is None:
            return True
        if command == '':
            continue
        if command.lower() == '@exit':
            print()
            return False
        if command.lower() == '@help':
            HelpTool(mathdir, PageReader, 'advanced')
            continue
        if command.lower() == '@flush':
            TempManager().Flush('Mathematics Advanced Module')
            continue
        if command.lower() == '@window':
            from tools.Mathematics.cal_function import open_function_window
            print(open_function_window())
            print()
            continue
        if _bare_command_hint(command, {'window': '@window'}):
            continue
        print(_advanced_command(advanced, command))
        print()


def _compound_loop():
    from tools.Mathematics.cal_compound import Compound
    compound = Compound()
    print("Input '@help' to show the help page, '@exit' to return to the terminal.\n")
    while True:
        command = _read_input(style.prompt('(compound)'))
        if command is None:
            return True
        if command == '':
            continue
        if command.lower() == '@exit':
            print()
            return False
        if command.lower() == '@help':
            HelpTool(mathdir, PageReader, 'compound')
            continue
        if command.lower() == '@flush':
            compound.reset()
            TempManager().Flush('Mathematics Compound Module')
            continue
        if _bare_command_hint(command):
            continue
        print(compound.base(command)[0])
        print()


def _function_loop():
    """进入函数分析 REPL，结束后直接返回终端。"""
    from tools.Mathematics.cal_function import run
    run()
    print()
    return False


def _select_method():
    """读取用户选择的模块，输入为空或 '@exit' 时返回 None。"""
    while True:
        selected = _read_input(style.label(
            'Please input a method which you want to use [basic/advanced/compound/function]: '))
        if selected is None:
            return None
        selected = selected.lower()
        if selected in ('', '@exit'):
            return None
        if selected in METHODS:
            return selected
        if selected == 'exit':
            print("NameError: the command 'exit' was replaced by '@exit'.")
            print()
            continue
        print("NameError: method '%s' is not defined, please choose one from "
              "'basic', 'advanced', 'compound' and 'function'." % selected)


def run():
    style.banner('TSL-SYSTEM Mathematics Module', width=37)

    while True:
        method = _select_method()
        if method is None:
            return 0
        if method == 'basic':
            keep_running = _basic_loop()
        elif method == 'advanced':
            keep_running = _advanced_loop()
        elif method == 'compound':
            keep_running = _compound_loop()
        else:
            keep_running = _function_loop()
        if not keep_running:
            return 0
