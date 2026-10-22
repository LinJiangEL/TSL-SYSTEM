#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

from selfcheck import check_command
from tools.__built_in__.external import run

if check_command('git'):
    run(['git', 'pull'])
else:
    raise RuntimeError("'git' is not in the path, please install it and try again.")
