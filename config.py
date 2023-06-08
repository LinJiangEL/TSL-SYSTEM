import os
import sys
import uuid
from setuptools.errors import PlatformError

SYSTEM_FILES = ['bin', 'backup', 'Database', 'tools', 'modules', 'Temp', 'loading.py', 'selfcheck.py', 'system.py', 'config.py', 'services.py',
                      'upgrade.py', 'sysmgr.py', 'motd', 'terminal.py', 'linuxrequirements.txt', 'win32requirements.txt', 'loading.py', 'motd', 'LICENSE',
                      'motd.jpg', 'README.md', 'VERSION']
SYSTEM_ID = str(uuid.uuid3(uuid.NAMESPACE_X500, 'TSL-SYSTEM'))
SYSTEM_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_LOGPATH = os.path.join(SYSTEM_DIR, "Temp/logs")
SYSTEM_LOGFORMAT = "{time:YYYY-MM-DD HH:mm:ss} [{level}] {message}"
SYSTEM_LOGSTDOUT = False
Tools_DIR = SYSTEM_DIR + '/tools/'
SYSTEM_DIGMAX = 8
SuperUser = ['root']
SYSTEM_PRINTER = 'cat' if sys.platform == 'linux' else 'type' if sys.platform == 'win32' else 0
requirements_file = os.path.join(SYSTEM_DIR, f'{sys.platform}requirements.txt')

if sys.platform == 'win32':
    Bin_DIR = SYSTEM_DIR + '/bin/win32/'
elif sys.platform == 'linux':
    Bin_DIR = SYSTEM_DIR + '/bin/linux/'
else:
    raise PlatformError('TSL-SYSTEM can only run on the win32 or linux platform!')

help_keys = []
help_values = []
with open(os.path.join(SYSTEM_DIR, f'bin/{sys.platform}bin.help'), 'r') as binhelpdictfile:
    for line in binhelpdictfile.readlines():
        if line.startswith('#') or line.strip() == '':
            continue
        else:
            help_keys.append(line.split(':')[0])
            help_values.append(line.split(':')[1])

if sys.platform == 'win32':
    binhelp_win32dict = dict(zip(help_keys, help_values))
elif sys.platform == 'linux':
    binhelp_linuxdict = dict(zip(help_keys, help_values))
else:
    raise PlatformError('TSL-SYSTEM can only run on the win32 or linux platform!')
