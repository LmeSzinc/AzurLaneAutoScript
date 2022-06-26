import logging
import sys

logger = logging.getLogger("deploy")
_logger = logger

formatter = logging.Formatter(fmt="%(message)s")
hdlr = logging.StreamHandler(stream=sys.stdout)
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)


def hr(title, level=3):
    if logger is not _logger:
        return logger.hr(title, level)
        
    title = str(title).upper()
    if level == 0:
        middle = "|" + " " * 20 + title + " " * 20 + "|"
        border = "+" + "-" * (len(middle) - 2) + "+"
        logger.info(border)
        logger.info(middle)
        logger.info(border)
    if level == 1:
        logger.info("=" * 20 + " " + title + " " + "=" * 20)
    if level == 2:
        logger.info("-" * 20 + " " + title + " " + "-" * 20)
    if level == 3:
        logger.info(f"<<< {title} >>>")


logger.hr = hr