from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from campaign.campaign_main.campaign_1_1 import Config as ConfigBase, MAP

class Config(ConfigBase):
    pass

class Campaign(CampaignBase):
    MAP = MAP

    def run(self):
        logger.hr('Ambush Farming on 1-1', level=2)
        
        # Enter map
        self.map_get_info(star=True)
        self.ENTRANCE.area = self.ENTRANCE.button
        self.enter_map(self.ENTRANCE, mode=self.config.Campaign_Mode)

        # Map init
        self.handle_map_fleet_lock()
        self.map_init(self.MAP)

        # Start ambush loop
        logger.hr('Start Ambush Loop', level=2)
        locations = ['B1','C1']
        loc_index = 0
        
        run_limit = self.config.StopCondition_RunCount

        while True:
            target = locations[loc_index]
            logger.info(f'Moving to {target} to farm ambush.')
            loc_index = (loc_index + 1) % len(locations)
            
            # Use self.goto to move. It will handle ambush automatically.
            self.goto(target)
            
            # Clear click record to prevent GameTooManyClickError from oscillation
            self.device.click_record_clear()
            
            if run_limit > 0 and self.battle_count >= run_limit:
                logger.hr(f'Reached target run count: {run_limit}', level=2)
                break
            
            # If run_limit == 0, it means infinite runs.
            # We don't break. We also don't trigger StopCondition_RunCount decrement in run.py,
            # Because run.py handles the outer loop, but here we stay inside the map infinitely!
            if run_limit == 0 and hasattr(self, 'run_count'):
                # Set run_count>0 to bypass any outer loop conditions if applicable
                pass

        # Withdraw
        logger.info('Farming finished. Withdrawing...')
        from module.exception import CampaignEnd
        try:
            self.withdraw()
        except CampaignEnd:
            pass
        
        return True
