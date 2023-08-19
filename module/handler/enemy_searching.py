from module.base.decorator import del_cached_property
from module.base.timer import Timer
from module.exception import CampaignEnd
from module.handler.assets import *
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.map.assets import *
from module.ui.assets import CAMPAIGN_CHECK, EVENT_CHECK, SP_CHECK


class EnemySearchingHandler(InfoHandler):
    MAP_ENEMY_SEARCHING_OVERLAY_TRANSPARENCY_THRESHOLD = 0.5  # Usually (0.70, 0.80).
    MAP_ENEMY_SEARCHING_TIMEOUT_SECOND = 5
    in_stage_timer = Timer(0.5, count=2)
    stage_entrance = None

    map_is_100_percent_clear = False  # Will be override in fast_forward.py

    def enemy_searching_color_initial(self):
        pass

    def enemy_searching_appear(self):
        if not self.is_in_map():
            return False

        if MAP_ENEMY_SEARCHING.match_luma(self.device.image, offset=(5, 5)):
            return True

        return False

    def handle_enemy_flashing(self):
        self.device.sleep(1.2)

    def handle_in_stage(self):
        if self.is_in_stage():
            if self.in_stage_timer.reached():
                logger.info('In stage.')
                self.ensure_no_info_bar(timeout=1.2)
                raise CampaignEnd('In stage.')
            else:
                return False
        else:
            if self.appear(MAP_PREPARATION, offset=(20, 20)) or self.appear(FLEET_PREPARATION, offset=(20, 20)):
                self.device.click(MAP_PREPARATION_CANCEL)
            self.in_stage_timer.reset()
            return False

    def is_in_stage_page(self):
        for check in [CAMPAIGN_CHECK, EVENT_CHECK, SP_CHECK]:
            if self.appear(check, offset=(20, 20)):
                return True
        return False

    def is_stage_page_has_entrance(self):
        """
        Has any stage entrance, which means stage page is fully loaded
        """
        # campaign_extract_name_image in CampaignOcr.
        try:
            if hasattr(self, 'campaign_extract_name_image'):
                del_cached_property(self, '_stage_image')
                del_cached_property(self, '_stage_image_gray')
                if not len(self.campaign_extract_name_image(self.device.image)):
                    return False
        except IndexError:
            return False

        return True

    def is_in_stage(self):
        if not self.is_in_stage_page():
            return False
        if not self.is_stage_page_has_entrance():
            return False
        return True

    def is_in_map(self):
        return self.appear(IN_MAP)

    def is_event_animation(self):
        """
        Animation in events after cleared an enemy.

        Returns:
            bool: If animation appearing.
        """
        return False

    def handle_auto_search_exit(self, drop=None):
        """
        A placeholder, will be override in AutoSearchHandler.
        AutoSearchHandler inherits EnemySearchingHandler,
        but handle_in_map_with_enemy_searching() requires handle_auto_search_exit() to handle unexpected situation.
        """
        return False

    def handle_in_map_with_enemy_searching(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool: If handled.
        """
        if not self.is_in_map():
            return False

        timeout = Timer(self.MAP_ENEMY_SEARCHING_TIMEOUT_SECOND)
        appeared = False
        while 1:
            self.device.screenshot()
            if self.is_event_animation():
                continue
            if self.is_in_map():
                timeout.start()
            else:
                timeout.reset()

            # Stage might ends,
            # although here expects an enemy searching animation.
            if self.handle_in_stage():
                return True
            if self.handle_auto_search_exit(drop=drop):
                continue

            # Popups
            if self.handle_vote_popup():
                timeout.limit = 10
                timeout.reset()
                continue
            if self.handle_story_skip():
                self.ensure_no_story()
                timeout.limit = 10
                timeout.reset()
            if self.handle_guild_popup_cancel():
                timeout.limit = 10
                timeout.reset()
                continue
            if self.handle_urgent_commission(drop=drop):
                timeout.limit = 10
                timeout.reset()
                continue

            # End
            if self.enemy_searching_appear():
                appeared = True
            else:
                if appeared:
                    self.handle_enemy_flashing()
                    self.device.sleep(0.3)
                    logger.info('Enemy searching appeared.')
                    break
                self.enemy_searching_color_initial()
            if timeout.reached():
                logger.info('Enemy searching timeout.')
                break

        self.device.screenshot()
        return True

    def handle_in_map_no_enemy_searching(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool: If handled.
        """
        if not self.is_in_map():
            return False

        timeout = Timer(1, count=2).start()
        while 1:
            self.device.screenshot()

            # End
            if timeout.reached():
                break

            # Stage might ends,
            # although here expects an enemy searching animation.
            if self.handle_in_stage():
                return True
            if self.handle_auto_search_exit(drop=drop):
                continue

            # Popups
            if self.handle_vote_popup():
                timeout.reset()
                continue
            if self.handle_story_skip():
                self.ensure_no_story()
                timeout.reset()
            if self.handle_guild_popup_cancel():
                timeout.reset()
                continue
            if self.handle_urgent_commission(drop=drop):
                timeout.reset()
                continue

        return True
