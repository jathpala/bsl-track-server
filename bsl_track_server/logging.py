"""
Copyright (C) 2024 Jath Palasubramaniam
Licensed under the Affero General Public License version 3
"""

import inspect
import logging
import logging.config
from functools import wraps

import yaml

_CONFIG_FILE="logging.yaml"

def setup_logging(func):
    """
    Configure the logger the first time we get a new logger
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not hasattr(wrapper, "configured"):
            with open(_CONFIG_FILE, encoding="utf-8") as config:
                logging.config.dictConfig(yaml.safe_load(config))
            wrapper.configured = True
        return func(*args, **kwargs)
    return wrapper


@setup_logging
def get_logger():
    """
    Get a logger instance
    """

    # Get name of module calling this function
    # Stack item 0 is the module of this function (logging)
    # Stake item 1 is the module of the wrapping function (logging)
    # Stack item 2 sit he module of the calling function (what we want)
    module = inspect.getmodule(inspect.stack()[2][0]).__name__

    return logging.getLogger(module)