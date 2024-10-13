#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import os
import sys


def GetResourcePath(path):
    """获取文件的绝对路径。"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, path)


def get_packagemgr(mgrlist):
    """获取系统软件包管理工具。"""
    from selfcheck import check_command

    for manager in mgrlist:
        if check_command(manager):
            return manager
    return None
