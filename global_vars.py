#!/usr/bin/python3
import logging

import coloredlogs

FMT = '%(asctime)s %(levelname)-8s %(message)s'
DATEFMT = '%H:%M:%S'
logging.basicConfig(format=FMT, datefmt=DATEFMT, level=logging.INFO)
log = logging.getLogger('fetch_tree')
fmt = logging.Formatter(FMT, DATEFMT)
file_handler = logging.FileHandler('log.txt', 'a')
file_handler.setFormatter(fmt)
log.addHandler(file_handler)
coloredlogs.install(level=logging.INFO, fmt=FMT, datefmt=DATEFMT)