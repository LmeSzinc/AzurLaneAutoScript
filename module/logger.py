import datetime
import logging
import os
import sys
from collections import deque

logging.raiseExceptions = True  # Set True if wanna see encode errors on console

# Logger init
logger_debug = False
logger = logging.getLogger()
logger.setLevel(logging.DEBUG if logger_debug else logging.INFO)
formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Add console logger
console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)

# Ensure folder to be alas root folder when running inside alas module folder
if not os.path.exists('alas.py'):
    path = os.path.normpath(os.getcwd()).split(os.sep)
    path[0] = path[0] + os.sep
    changed = False
    for index in range(len(path), 0, -1):
        folder = os.path.join(*path[:index])
        if os.path.exists(os.path.join(folder, 'alas.py')):
            logger.info('[Folder_changed] ' + '../' * (len(path) - index))
            os.chdir(folder)
            changed = True
            break
    if not changed:
        logger.warning('Unable to locate Alas root folder')
        logger.warning(f'Current_folder: {os.getcwd()}')

# Add file logger
pyw_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
if '_' in pyw_name:
    pyw_name = '_'.join(pyw_name.split('_')[:-1])
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


def attr_align(name, text, front='', align=22):
    name = str(name).rjust(align)
    if front:
        name = front + name[len(front):]
    logger.info('%s: %s' % (name, str(text)))


logger.hr = hr
logger.attr = attr
logger.attr_align = attr_align
logger.screenshot_deque = deque(maxlen=60)

logger.hr('Start', level=0)
