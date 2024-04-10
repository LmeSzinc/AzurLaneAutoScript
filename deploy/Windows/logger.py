import logging
import os
import sys

os.chdir(os.path.join(os.path.dirname(__file__), '../../'))

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


def attr(name, text):
    print(f'[{name}] {text}')


logger.hr = hr
logger.attr = attr


class Percentage:
    def __init__(self, progress):
        self.progress = progress

    def __call__(self, *args, **kwargs):
        logger.info(f'Process: [ {self.progress}% ]')


class Progress:
    Start = Percentage(0)
    ShowDeployConfig = Percentage(10)

    GitInit = Percentage(12)
    GitSetConfig = Percentage(13)
    GitSetRepo = Percentage(15)
    GitFetch = Percentage(40)
    GitReset = Percentage(45)
    GitCheckout = Percentage(48)
    GitShowVersion = Percentage(50)

    GitLatestCommit = Percentage(25)
    GitDownloadPack = Percentage(40)

    KillExisting = Percentage(60)
    UpdateDependency = Percentage(70)
    UpdateAlasApp = Percentage(75)

    AdbReplace = Percentage(80)
    AdbConnect = Percentage(95)

    # Must have a 100%
    Finish = Percentage(100)
