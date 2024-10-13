#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import sys

SYSTEM_STDOUT_LOGFORMAT = "<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> <level>[{level}]</level> <level>{message}</level>"


class Logger:
    """初始化系统日志格式。"""
    def __init__(self):
        from loguru import logger
        logger.remove()
        logger.add(sys.stderr,
                   colorize=True,
                   format=SYSTEM_STDOUT_LOGFORMAT,
                   level="INFO"
                   )
