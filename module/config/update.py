import codecs
import configparser
import random
import shutil
import string

from module.logger import logger


def random_id(length=32):
    """
    Args:
        length (int):

    Returns:
        str: Random azurstat id.
    """
    return ''.join(random.sample(string.ascii_lowercase + string.digits, length))


def update_config_from_template(config, file):
    """
    Args:
        config (configparser.ConfigParser):
        file: Save file when changed

    Returns:
        configparser.ConfigParser:
    """
    template = configparser.ConfigParser(interpolation=None)
    template.read_file(codecs.open(f'./config/template.ini', "r", "utf8"))
    changed = False
    # Update section.
    for section in template.sections():
        if not config.has_section(section):
            config.add_section(section)
            changed = True
    for section in config.sections():
        if not template.has_section(section):
            config.remove_section(section)
            changed = True
    # Update option
    for section in template.sections():
        for option in template.options(section):
            if not config.has_option(section, option):
                config.set(section, option, value=template.get(section, option))
                changed = True
    for section in config.sections():
        for option in config.options(section):
            if not template.has_option(section, option):
                config.remove_option(section, option)
                changed = True
    # AzueStat id
    if config['Setting']['azurstat_id'] == '':
        config['Setting']['azurstat_id'] = random_id()
    # Save
    if changed:
        config.write(codecs.open(file, "w+", "utf8"))
    return config


def get_config(ini_name):
    """
    Args:
        ini_name (str):

    Returns:
        configparser.ConfigParser:
    """
    config_file = f'./config/{ini_name}.ini'
    config = configparser.ConfigParser(interpolation=None)
    try:
        config.read_file(codecs.open(config_file, "r", "utf8"))
    except FileNotFoundError:
        logger.info('Config file not exists, copy from ./config/template.ini')
        shutil.copy('./config/template.ini', config_file)
        config.read_file(codecs.open(config_file, "r", "utf8"))

    config = update_config_from_template(config, file=config_file)
    return config
