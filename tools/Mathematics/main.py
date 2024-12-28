#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import os
import gc
import re
import string
from ast import literal_eval
from termcolor import colored
from config import Tools_DIR, PageReader
from sysmgr import TempManager
from tools.__built_in__.helptool import HelpTool

mathdir = os.path.join(Tools_DIR, "Mathematics")


def run():
    print('-' * 37)
    print('|   TSL-SYSTEM Mathematics Module   |')
    print('-' * 37)

    method = input('Please input a method which you want to use [basic/advanced]: ')
    if method.strip() == '':
        print()
        return 0
    try:
        exec(f"from tools.Mathematics.cal_{method.lower()} import {method[0].upper() + method[1:].lower()}")
        _ok = "True"
    except ModuleNotFoundError:
        _ok = "False"

    if _ok and method == 'basic':
        from tools.Mathematics.cal_basic import Basic
        basic = Basic()
        while True:
            cmd = input(colored('(basic)', color='magenta') + ' >> ').strip()
            if cmd == '':
                continue
            if cmd == '@exit':
                print()
                break
            if cmd == '@help':
                HelpTool(mathdir, PageReader, method)
                continue
            if cmd == '@flush':
                TempManager().Flush('Mathematics Basic Module')
                continue
            maincmd = cmd.split(' ')[0]
            try:
                exec(f"basic = Basic();basic.{maincmd if maincmd[0] in string.ascii_letters else exec('raise AttributeError')}") \
                    if maincmd not in ['ReturnError', 'resultformat'] else exec('raise NameError')
                num_argvs = cmd.split(' ', maxsplit=1)[1]
                ismanyargvs = cmd.split(' ', maxsplit=1)[1].count(',') > 1
                if ismanyargvs:
                    print("ValueError:cannot process too many arguments.")
                    continue
                numab = [float(num) for num in num_argvs.split(',') if num]
            except AttributeError:
                print(f"NameError:symbol '{maincmd}' is not defined in Basic.")
            except NameError:
                print(f"NameError:internal symbol '{maincmd}' cannot be called by users.")
            except IndexError:
                print('SyntaxError:invalid maincmd format.')
            except ValueError as e:
                if 'convert' in str(e):
                    print("ValueError:expression operation is not supported.")
            else:
                try:
                    nums = list(map(float, num_argvs.split(',')))
                except ValueError:
                    print('SyntaxError:invalid num_argvs format.')
                else:
                    error = 'SyntaxError:invalid num_argvs format.'
                    argvs = f'{numab[0]},{numab[1]}' if maincmd in basic.two and len(num_argvs.split(',')) == 2 \
                        else numab[0] if maincmd in basic.one and ',' not in num_argvs \
                        else nums if maincmd in basic.needlist \
                        else None
                    try:
                        result = (getattr(basic, maincmd)(numab[0], numab[1])
                                  if maincmd in basic.two and len(num_argvs.split(',')) == 2
                                  else getattr(basic, maincmd)(numab[0])
                                  if maincmd in basic.one and ',' not in num_argvs
                                  else getattr(basic, maincmd)(nums) if maincmd in basic.needlist
                                  else None) \
                            if 'NoneType' not in str(type(argvs)) else basic.ReturnError(error)
                        print(result[0] if "Error" not in result else result)
                    except SyntaxError:
                        print(f"SyntaxError:symbol '{maincmd}' was incorrectly used in called.\n")
            finally:
                print('')
    elif _ok and method == 'advanced':
        from tools.Mathematics.cal_advanced import Advanced
        advanced = Advanced()

        while True:
            cmd = input(colored('(advanced)', color='magenta') + ' >> ').strip()
            if cmd == '':
                continue
            if cmd == '@exit':
                print()
                break
            if cmd == '@help':
                HelpTool(mathdir, PageReader, method)
                continue
            if cmd == '@flush':
                TempManager().Flush('Mathematics Advanced Module')
                continue
            if cmd.count('(') > cmd.count(')'):
                print("SyntaxError: unexpected EOF while parsing.\n")
            elif cmd.count('(') < cmd.count(')'):
                print("SyntaxError: unmatched ')'.\n")
            else:
                maincmd = cmd.split('(')[0]
                try:
                    if maincmd in ['Solve_equations', 'Solve_equation']:
                        expressions = [exp for exp in '('.join([e.strip() for e in cmd.split('(')[1:]])[:-1].split(',')
                                       if exp != ''
                                       ]
                        result = getattr(advanced, maincmd)(expressions)

                        # 结果处理
                        if maincmd in ['Solve_equations']:
                            n = 1
                            for r in result:
                                fresult = f"Solve{n}: {r}"
                                print(fresult)
                                n = n + 1
                            del n
                            gc.collect()
                        elif maincmd in ['Solve_equation']:
                            n = 1
                            for r in result:
                                fresult = f"{r.split(' = ')[0]}{n} = {r.split(' = ')[1]}"
                                print(fresult)
                                n = n + 1
                            del n
                            gc.collect()
                        else:
                            print(result)
                    elif maincmd in ['P', 'A', 'C', 'Permutation', 'Combination']:
                        maincmd = 'Permutation' if maincmd in ['P', 'A'] \
                            else 'Combination' if maincmd == 'C' \
                            else maincmd
                        numstr = cmd.split(maincmd if cmd.count(maincmd) == 1 else '(')[1]
                        numstr = re.sub(r'^\((.*)\)$|^\((.*)|(.*)\)$', r'\1\2\3', numstr)
                        m, n, *_ = numstr.split(',') if len(numstr.split(',')) >= 2 else [None, numstr]
                        m = n if m is None else m
                        m, n = m.strip(), n.strip()
                        m, n = literal_eval(m) if m.isnumeric() else None, \
                            literal_eval(n) if n.isnumeric() else None
                        if m is None or n is None:
                            print("ValueError:invalid 'm' or 'n' format.\n")
                        else:
                            m, n = (n, m) if m > n else (m, n)
                            m = min(m, n)
                            numresult = getattr(advanced, maincmd)(n, m)
                            result = f'Expression: {maincmd}({m},{n})\nResult: {numresult}\n' \
                                if isinstance(numresult, int) else numresult
                            print(result)
                    else:
                        print(f"NameError:symbol '{maincmd}' is not defined in Advanced.\n")
                except AttributeError:
                    print(f"NameError:symbol '{maincmd}' is not defined in Advanced.\n")
    else:
        print(f"NameError:method '{method}' is not defined.")
