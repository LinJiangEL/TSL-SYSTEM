import string
from pprint import pprint
from termcolor import colored


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
            maincmd = cmd.split(' ')[0]
            try:
                exec(f"basic.{maincmd if maincmd[0] in string.ascii_letters else exec('raise AttributeError')}") \
                    if maincmd not in ['ReturnError', 'resultformat'] else exec('raise NameError')
                num_argvs = cmd.split(' ')[1]
                numab = [float(num) for num in num_argvs.split(',') if num != '']
            except AttributeError:
                print(f"NameError:symbol '{maincmd}' is not defined in Basic.")
            except NameError:
                print(f"NameError:internal symbol '{maincmd}' cannot be called by users.")
            except IndexError:
                print('SyntaxError:invaild maincmd format.')
            except ValueError as e:
                if 'convert' in str(e):
                    print("ValueError:expression operation is not supported.")
            else:
                try:
                    nums = list(map(float, num_argvs.split(',')))
                except ValueError:
                    print('SyntaxError:invaild num_argvs format.')
                else:
                    error = 'SyntaxError:invaild num_argvs format.'
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
            if cmd.count('(') > cmd.count(')'):
                print("SyntaxError: unexpected EOF while parsing.")
            elif cmd.count('(') < cmd.count(')'):
                print("SyntaxError: unmatched ')'.")
            else:
                maincmd = cmd.split('(')[0]
                expressions = [exp for exp in '('.join([e.strip() for e in cmd.split('(')[1:]])[:-1].split(',')
                               if exp != ''
                               ]
                try:
                    result = getattr(advanced, maincmd)(expressions)
                    pprint(result)
                except AttributeError:
                    print(f"NameError:symbol '{maincmd}' is not defined in Advanced.")
    else:
        print(f"NameError:method '{method}' is not defined.")
