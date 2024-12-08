# -*- coding: utf-8 -*-
""" Settings for logging over all files. """

import logging
import os

if not os.path.exists("logs/"):
    os.makedirs("logs/")

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
formatter = logging.Formatter(
    # fmt = "%(asctime)s ( %(levelname)s ) %(message)s",
    # fmt = "%(asctime)-15s %(name)-8s %(threadName)s %(levelname)s: %(message)s",
    fmt = "%(asctime)-15s [%(threadName)s] [%(filename)s->%(funcName)s(%(lineno)d)] "
          "%(levelname)s: %(message)s",
)

file_handler = logging.FileHandler("logs/app.log", mode="w", encoding="utf-8")
file_handler.setLevel("DEBUG")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel("DEBUG")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.setLevel(logging.DEBUG)
