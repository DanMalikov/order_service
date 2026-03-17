import logging
import sys

def configure_logging(level: str = logging.INFO):
    root_logger = logging.getLogger()

    if root_logger.handlers:
        return
    root_logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)

    strfmt = '[%(asctime)s] [%(name)s] [%(levelname)s] > %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'

    formatter = logging.Formatter(fmt=strfmt, datefmt=datefmt)
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)
