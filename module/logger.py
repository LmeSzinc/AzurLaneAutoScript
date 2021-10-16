import datetime
import logging
import os
import sys
from collections import deque


def empty_function(*args, **kwargs):
    pass


# cnocr will set root logger in cnocr.utils
# Delete logging.basicConfig to avoid logging the same message twice.
logging.basicConfig = empty_function
logging.raiseExceptions = True  # Set True if wanna see encode errors on console

# Logger init
logger_debug = False
logger = logging.getLogger('alas')
logger.setLevel(logging.DEBUG if logger_debug else logging.INFO)
formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Add console logger
console = logging.StreamHandler(stream=sys.stdout)
console.setFormatter(formatter)
console.flush = sys.stdout.flush
logger.addHandler(console)

# Ensure running in Alas root folder
os.chdir(os.path.join(os.path.dirname(__file__), '../'))

# Add file logger
pyw_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]


def set_file_logger(name=pyw_name):
    if '_' in name:
        name = name.split('_', 1)[0]
    log_file = f'./log/{datetime.date.today()}_{name}.txt'
    try:
        file = logging.FileHandler(log_file, encoding='utf-8')
    except FileNotFoundError:
        os.mkdir('./log')
        file = logging.FileHandler(log_file, encoding='utf-8')
    file.setFormatter(formatter)

    logger.handlers = [h for h in logger.handlers if not isinstance(h, logging.FileHandler)]
    logger.addHandler(file)
    logger.log_file = log_file


def hr(title, level=3):
    title = str(title).upper()
    if level == 1:
        logger.info('=' * 20 + ' ' + title + ' ' + '=' * 20)
    if level == 2:
        logger.info('-' * 20 + ' ' + title + ' ' + '-' * 20)
    if level == 3:
        logger.info('<' * 3 + ' ' + title + ' ' + '>' * 3)
    if level == 0:
        middle = '|' + ' ' * 20 + title + ' ' * 20 + '|'
        border = '+' + '-' * (len(middle) - 2) + '+'
        logger.info(border)
        logger.info(middle)
        logger.info(border)


def attr(name, text):
    logger.info('[%s] %s' % (str(name), str(text)))


def attr_align(name, text, front='', align=22):
    name = str(name).rjust(align)
    if front:
        name = front + name[len(front):]
    logger.info('%s: %s' % (name, str(text)))


logger.hr = hr
logger.attr = attr
logger.attr_align = attr_align
logger.set_file_logger = set_file_logger
logger.log_file: str

logger.set_file_logger()
logger.hr('Start', level=0)
