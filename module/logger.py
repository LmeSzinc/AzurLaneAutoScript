import logging
import datetime


logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)

log_file = './log/%s.txt' % datetime.date.today()
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

logger.hr('Start', level=0)
