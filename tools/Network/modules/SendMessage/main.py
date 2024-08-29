#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import os

target = os.getlogin()
os.system(f'msg /server:localhost "{target}"')
