from module.base.timer import Timer
from module.combat.combat import Combat
from module.logger import logger
from module.meta_reward.assets import *
from module.os_ash.assets import DOSSIER_LIST
from module.ui.page import page_meta
from module.ui.ui import UI


class BeaconReward(Combat, UI):
    def meta_reward_notice_appear(self):
        """
        Returns:
            bool: If appear.

        Page:
            in: page_meta
        """
        if self.appear(META_REWARD_NOTICE, threshold=30):
            logger.info('Found meta reward red dot')
            return True
        else:
            logger.info('No meta reward red dot')
            return False

    def meta_reward_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_meta
            out: REWARD_CHECK
        """
        logger.info('Meta reward enter')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(REWARD_ENTER, offset=(20, 20), interval=3):
                continue

            # End
            if self.appear(REWARD_CHECK, offset=(20, 20)):
                break

    def meta_reward_receive(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            bool: If received.

        Pages:
            in: REWARD_CHECK
            out: REWARD_CHECK
        """
        logger.hr('Meta reward receive', level=1)
        confirm_timer = Timer(1, count=3).start()
        received = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(REWARD_RECEIVE, offset=(20, 20), interval=3) and REWARD_RECEIVE.match_appear_on(
                    self.device.image):
                self.device.click(REWARD_RECEIVE)
                confirm_timer.reset()
                continue
            if self.handle_popup_confirm('META_REWARD'):
                # Lock new META ships
                confirm_timer.reset()
                continue
            if self.handle_get_items():
                received = True
                confirm_timer.reset()
                continue
            if self.handle_get_ship():
                received = True
                confirm_timer.reset()
                continue

            # End
            if self.appear(REWARD_CHECK, offset=(20, 20)) and \
               self.image_color_count(REWARD_RECEIVE, color=(49, 52, 49), threshold=221, count=400):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

        logger.info(f'Meta reward receive finished, received={received}')
        return received

    def run(self):
        if self.config.SERVER in ['cn', 'en', 'jp']:
            pass
        else:
            logger.info(f'MetaReward is not supported in {self.config.SERVER}, please contact server maintainers')
            return

        self.ui_ensure(page_meta)

        if self.meta_reward_notice_appear():
            self.meta_reward_enter()
            self.meta_reward_receive()


class DossierReward(Combat, UI):
    def meta_reward_notice_appear(self):
        """
        Returns:
            bool: If appear.

        Page:
            in: dossier meta page
        """
        self.device.screenshot()
        if self.appear(DOSSIER_REWARD_RECEIVE, offset=(-40, 10, -10, 40), threshold=0.7):
            logger.info('Found dossier reward red dot')
            return True
        else:
            logger.info('No dossier reward red dot')
            return False

    def meta_reward_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: dossier meta page
            out: DOSSIER_REWARD_CHECK
        """
        logger.info('Dossier reward enter')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(DOSSIER_LIST, offset=(20, 20)):
                self.device.click(DOSSIER_REWARD_ENTER)
                continue

            # End
            if self.appear(DOSSIER_REWARD_CHECK, offset=(20, 20)):
                break

    def meta_reward_receive(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            bool: If received.

        Pages:
            in: DOSSIER_REWARD_CHECK
            out: DOSSIER_REWARD_CHECK
        """
        logger.hr('Dossier reward receive', level=1)
        confirm_timer = Timer(1, count=3).start()
        received = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(DOSSIER_REWARD_RECEIVE, offset=(20, 20), interval=3) and DOSSIER_REWARD_RECEIVE.match_appear_on(
                    self.device.image):
                self.device.click(DOSSIER_REWARD_RECEIVE)
                confirm_timer.reset()
                continue
            if self.handle_popup_confirm('DOSSIER_REWARD'):
                # Lock new META ships
                confirm_timer.reset()
                continue
            if self.handle_get_items():
                received = True
                confirm_timer.reset()
                continue
            if self.handle_get_ship():
                received = True
                confirm_timer.reset()
                continue

            # End
            if not self.appear(DOSSIER_REWARD_RECEIVE, offset=(20, 20)):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

        logger.info(f'Dossier reward receive finished, received={received}')
        return received

    def run(self):
        if self.config.SERVER in ['cn', 'en', 'jp']:
            pass
        else:
            logger.info(f'MetaReward is not supported in {self.config.SERVER}, please contact server maintainers')
            return

        from module.os_ash.meta import OpsiAshBeacon
        OpsiAshBeacon(self.config, self.device).ensure_dossier_page()
        if self.meta_reward_notice_appear():
            self.meta_reward_enter()
            self.meta_reward_receive()


class MetaReward(BeaconReward, DossierReward):
    def run(self, category="beacon"):
        if category == "beacon":
            BeaconReward(self.config, self.device).run()
        elif category == "dossier":
            DossierReward(self.config, self.device).run()
        else:
            logger.info(f'Possible wrong parameter {category}, please contact the developers.')
