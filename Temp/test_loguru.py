import os
from loguru import logger

logger.remove(handler_id=None)
logger.add(os.path.join("logs", "log_{time:YYYY-MM}.log"),
           format="{time:YYYY-MM-DD HH:mm:ss} [{level}] {message}",
           level="DEBUG",
           rotation="32 MB",
           enqueue=True
           )

logger.info("This is a test.")
logger.debug("This is a test.")
logger.error("This is a test.")
