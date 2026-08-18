# This must be the first to import
import deploy.logger
from module.logger import logger  # Change folder

deploy.logger.logger = logger
