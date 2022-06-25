# This must be the first to import
from module.logger import logger  # Change folder
import deploy.logger

deploy.logger.logger = logger
