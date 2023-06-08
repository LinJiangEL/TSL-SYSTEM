import string


def run():
    print('-' * 37)
    print('|   TSL-SYSTEM Mathematics Module   |')
    print('-' * 37)

    method = input('Please input a method which you want to use [basic/advanced]: ')
    try:
        exec(f"from tools.Mathematics.cal_{method.lower()} import {method[0].upper() + method[1:].lower()}")
        _ok = "True"
    except ModuleNotFoundError:
        print(f"NameError:method '{method}' is not defined.")
        _ok = "False"

    if _ok and method == 'basic':
        from tools.Mathematics.cal_basic import Basic
        basic = Basic()
        while True:
            cmd = input('>> ')
            if cmd == '@exit':
                print()
                break
            maincmd = cmd.split(' ')[0]
            try:
                exec(f"basic.{maincmd if maincmd[0] in string.ascii_letters else exec('raise AttributeError')}") \
                    if maincmd not in ['ReturnError', 'resultformat'] else exec('raise NameError')
                num_argvs = cmd.split(' ')[1]
                numab = [num_argvs] if ',' not in num_argvs else num_argvs.split(',')
            except AttributeError:
                print(f"NameError:symbol '{maincmd}' is not defined in Basic.")
            except NameError:
                print(f"NameError:internal symbol '{maincmd}' cannot be called by users.")
            except IndexError:
                print('SyntaxError:invaild maincmd format.')
            else:
                try:
                    nums = list(map(float, num_argvs.split(',')))
                except ValueError:
                    print('SyntaxError:invaild num_argvs format.')
                else:
                    error = 'SyntaxError:invaild num_argvs format.'
                    argvs = numab[0] + ',' + numab[1] if maincmd in basic.two and len(num_argvs.split(',')) == 2 \
                        else numab[0] if maincmd in basic.one and ',' not in num_argvs \
                        else nums if maincmd in basic.needlist \
                        else exec('error')
                    exectext = maincmd + f'({argvs})' if 'NoneType' not in str(type(argvs)) \
                        else f"ReturnError('{error}')"
                    try:
                        result_dict = {}
                        exec(f"from tools.Mathematics.cal_basic import Basic;"
                             f"basic = Basic();"
                             f"result = basic.{exectext};", globals(), result_dict)
                        print(result_dict["result"])
                    except SyntaxError:
                        print(f"SyntaxError:symbol '{maincmd}' was incorrectly used in called.\n")
            finally:
                print('')
    elif _ok and method == 'advanced':
        from tools.Mathematics.cal_advanced import Advanced
        advanced = Advanced()

        while True:
            cmd = input('>> ')
            if cmd == '@exit':
                print()
                break
            maincmd = ...
    else:
        print(f"NameError:method '{method}' is not defined.")
        _ok = "False"
