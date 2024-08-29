#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import sys

SYSTEM_STDOUT_LOGFORMAT = "<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> <level>[{level}]</level> <level>{message}</level>"


class Logger:
    def __init__(self):
        from loguru import logger
        logger.remove()
        logger.add(sys.stderr,
                   colorize=True,
                   format=SYSTEM_STDOUT_LOGFORMAT,
                   level="INFO"
                   )
