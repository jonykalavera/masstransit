"""Utils for masstransit."""

import logging
import logging.config
import os
from importlib import import_module
from typing import Any

logger = logging.getLogger(__name__)


def import_string(dotted_path: str) -> Any:
    """Import a dotted module path and return the attribute/class designated by the last name in the path.

    Raise ImportError if the import fails. Stolen from pydantic v1.
    """
    try:
        module_path, class_name = dotted_path.strip(" ").rsplit(".", 1)
    except ValueError as e:
        raise ImportError(f'"{dotted_path}" doesn\'t look like a module path') from e

    module = import_module(module_path)
    try:
        return getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(f'Module "{module_path}" does not define a "{class_name}" attribute') from e


def filter_maker(level):
    """Log level X and above filter factory."""
    _level = getattr(logging, level)

    def filter(record):
        return record.levelno <= _level

    return filter


def django_setup(django_settings: str):
    """Initializes django application settings."""
    try:
        django = import_module("django")
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", django_settings)
        django.setup()
        logger.debug("Django initialized")
    except ImportError:
        logger.error("Could not import django")


def logging_setup(log_level="INFO"):
    """Initializes logging configuration."""
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(process)d] [%(name)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "class": "logging.Formatter",
            }
        },
        "filters": {"warnings_and_below": {"()": f"{__name__}.filter_maker", "level": "WARNING"}},
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": "ext://sys.stdout",
                "filters": ["warnings_and_below"],
            },
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "default",
                "stream": "ext://sys.stderr",
            },
        },
        "loggers": {
            "pika": {"handlers": ["stderr"], "level": logging.ERROR},
            "masstransit": {"handlers": ["stderr", "stdout"], "level": log_level, "propagate": False},
            "": {"handlers": ["stderr", "stdout"], "level": log_level},
        },
        "root": {"level": log_level, "handlers": ["stderr", "stdout"]},
    }

    logging.config.dictConfig(LOGGING)
