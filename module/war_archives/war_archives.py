import copy
import importlib
import os

from campaign.campaign_war_archives.campaign_base import CampaignBase, CampaignNameError
from module.campaign.run import CampaignRun
from module.logger import logger


class CampaignWarArchives(CampaignRun, CampaignBase):
    def load_campaign(self, name, folder='campaign_war_archives'):
        """
        Overridden for the specific usage of war_archives

        Args:
            name (str): Name of .py file under module.campaign.
            folder (str): Name of the file folder under campaign.

        Returns:
            bool: If load.
        """
        if hasattr(self, 'name') and name == self.name:
            return False

        self.name = name
        self.folder = folder

        if folder.startswith('campaign_'):
            self.stage = '-'.join(name.split('_')[1:3])
        if folder.startswith('event'):
            self.stage = name

        try:
            self.module = importlib.import_module('.' + name, f'campaign.campaign_war_archives.{folder}')
        except ModuleNotFoundError:
            logger.warning(f'Map file not found: campaign.campaign_war_archives.{folder}.{name}')
            folder = f'./campaign/campaign_war_archives/{folder}'
            if not os.path.exists(folder):
                logger.warning(f'Folder not exists: {folder}')
            else:
                files = [f[:-3] for f in os.listdir(folder) if f[-3:] == '.py']
                logger.warning(f'Existing files: {files}')
            exit(1)

        config = copy.copy(self.config).merge(self.module.Config())
        device = self.device
        self.campaign = self.module.Campaign(config=config, device=device)
        self.campaign_name_set(name)

        return True