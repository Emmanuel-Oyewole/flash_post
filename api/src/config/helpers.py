import logging
from logging import Logger, getLogger

logger: Logger = getLogger("uvicorn")

# Configure logger
logger: Logger = getLogger("uvicorn")
logger.setLevel(logging.INFO)

# Add handler if no handlers exist
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
