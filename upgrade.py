import os
from selfcheck import check_command

if check_command('git'):
    os.system('git pull')
else:
    raise RuntimeError("'git' is not in the path, please install it and try again.")
