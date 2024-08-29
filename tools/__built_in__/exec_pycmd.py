#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import code


def exec_cmd(s):
    try:
        code_obj = code.compile_command(s)
    except:
        return None
    if code_obj is None:
        return None
    namespace = {}
    exec(code_obj, namespace)
    return namespace
