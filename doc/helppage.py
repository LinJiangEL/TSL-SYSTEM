#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import os


def HelpPage(pagedir, reader, command):
    help_pagefile = os.path.join(pagedir, f"{command}.help")
    if os.path.exists(help_pagefile):
        os.system(f'"{reader}" -20 -d -f {help_pagefile}')
    else:
        print(f"FileNotFoundError:cannot found the file named '{command}.help' in doc directory.")
