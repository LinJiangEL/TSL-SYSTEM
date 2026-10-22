#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

import os
import subprocess

target = os.getlogin()
subprocess.run(['msg', '/server:localhost', target])
