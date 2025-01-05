import logging
import os
import os.path as osp
import sys
from datetime import datetime

# LOG_FORMAT = "%(asctime)s %(levelname)s %(processName)s-%(threadName)s-%(thread)d %(filename)s:%(lineno)d %(funcName)-10s : %(message)s"
LOG_FORMAT = "%(asctime)s %(levelname)-10s %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S "

LOG_DIR = "logs"
if not osp.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

LOG_FILE = osp.join(LOG_DIR, f"pull-{datetime.now():%Y%m%d-%H%M%S}.log")


def init():
    logging.basicConfig(
        handlers=[
            logging.FileHandler(LOG_FILE, "a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )
