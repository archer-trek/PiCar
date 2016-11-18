#!/usr/bin/env python
# coding: utf-8

import logging
import sys

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '[%(levelname)s][%(asctime)s][%(module)s] %(message)s'
    ))
    logger.addHandler(handler)
    return logger
