# This must be the first to import
from module.logger import logger  # Change folder
import deploy.Windows.logger

deploy.Windows.logger.logger = logger
