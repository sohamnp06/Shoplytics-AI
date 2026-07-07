"""
logger.py
---------
Shared logging configuration for all ETL modules and the Flask app.
"""

import logging
import sys


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger that writes to stdout."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False

    return logger
