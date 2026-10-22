#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

import os

from tools.__built_in__.external import run


def HelpTool(pagedir, reader, name):
    """打印Tools帮助界面。"""
    help_pagefile = os.path.join(pagedir, f"{name}.help")
    if os.path.exists(help_pagefile):
        run([reader, '-20', '-d', '-f', help_pagefile])
    else:
        print(f"FileNotFoundError:cannot found the file named '{name}.help' in doc directory.")
