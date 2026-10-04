#!/usr/bin/python3
import sys
from loguru import logger as log

FMT = ('<green>{time:MM-DD HH:mm:ss}</green> | '
       '<level>{level: <8}</level> | '
       # todo: remove in release version
       # '<cyan>{name}</cyan>:'
       '<cyan>{function}</cyan>:'
       '<cyan>{line}</cyan> - '
       '<level>{message}</level>')
log.remove()
log.add(sys.stderr, format=FMT, level='INFO')
log.add('log.txt', format=FMT, level='INFO', encoding='utf-8')

PROXY = 'http://127.0.0.1:7890'
DRYAD_KEY = r'E:/Linux/tree_crawler/key.txt'
