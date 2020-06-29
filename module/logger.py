import logging
import datetime
import os
import sys
from collections import deque

logging.raiseExceptions = False  # Set True if wanna see encode errors on console

pyw_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
if '_' in pyw_name:
    pyw_name = '_'.join(pyw_name.split('_')[:-1])

logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)

log_file = f'./log/{datetime.date.today()}_{pyw_name}.txt'
try:
    file = logging.FileHandler(log_file)
except FileNotFoundError:
    os.mkdir('./log')
    file = logging.FileHandler(log_file)
file.setFormatter(formatter)
logger.addHandler(file)


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


logger.hr = hr
logger.attr = attr
logger.screenshot_deque = deque(maxlen=60)

logger.hr('Start', level=0)
