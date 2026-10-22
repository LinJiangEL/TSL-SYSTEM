#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

import os

from tools.__built_in__.external import run


def HelpPage(pagedir, reader, command):
    """打印命令的帮助界面。"""
    help_pagefile = os.path.join(pagedir, f"{command}.help")
    if os.path.exists(help_pagefile):
        run([reader, '-20', '-d', '-f', help_pagefile])
    else:
        print(f"FileNotFoundError:cannot found the file named '{command}.help' in doc directory.")
