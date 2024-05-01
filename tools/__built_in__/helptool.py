import os


def HelpPage(pagedir, reader, name):
    help_pagefile = os.path.join(pagedir, f"{name}.help")
    if os.path.exists(help_pagefile):
        os.system(f'"{reader}" -20 -d -f {help_pagefile}')
    else:
        print(f"FileNotFoundError:cannot found the file named '{name}.help' in doc directory.")
