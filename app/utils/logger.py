import logging
import os

os.makedirs("log", exist_ok=True)


def setup_logger(logger, is_root=False, level=logging.INFO):
    # Set up the log formatter
    msg_format = (
        "%(asctime)s [%(levelname)8s] %(message)s (%(name)s - %(pathname)s:%(lineno)d)"
    )
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=msg_format, datefmt=date_format)

    # File Handler
    file_handler = logging.FileHandler("log/backend.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Stream Handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if is_root:
        logger.propagate = False

    logger.setLevel(level)
