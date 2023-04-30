from module.base.timer import Timer
from module.base.utils import *
from module.combat.combat import Combat
from module.logger import logger
from module.meta_reward.assets import *
from module.template.assets import TEMPLATE_META_DOCK_RED_DOT
from module.ui.page import page_meta
from module.ui.ui import UI, BACK_ARROW


class MetaReward(Combat, UI):
    def _meta_dock_get_entrance(self):
        # Where the click buttons are
        detection_area = (8, 385, 147, 680)
        # Offset inside to avoid clicking on edge
        pad = 2

        dots = TEMPLATE_META_DOCK_RED_DOT.match_multi(self.image_crop(detection_area), threshold=5)
        logger.info(f'Possible meta ships found: {len(dots)}')
        for button in dots:
            button = button.move(vector=detection_area[:2])
            enter = button.crop(area=(-129, 3, 3, 42), name='META_SHIP_ENTRANCE')
            enter.area = area_limit(enter.area, detection_area)
            enter._button = area_pad(enter.area, pad)
        
        return enter   

    def _meta_dock_swipe(self, downward=True, skip_first_screenshot=True):
        """
        Swipe down meta dock to search for red dots.
        After clicking the ship icon will enlarge.
        Red dots means possible tactical skills finished or possible rewards, 
        so need to use meta_reward_notice_appear to check.
        
        Args:
            downward (boot): direction of vertical swipe
            skip_first_screenshot (bool):

        Returns:
            bool: If found possible red dot.
        """
        # Where meta dock scroll part is
        detection_area = (8, 392, 233, 680) # 140, 680 for click button area
        direction_vector = (0, -200) if downward else (0, 200)

        for _ in range(5):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            entrance = self._meta_dock_get_entrance()
            if len(entrance):
                return True
            
            p1, p2 = random_rectangle_vector(
                direction_vector, box=detection_area, random_range=(-30, -30, 30, 30), padding=20)
            self.device.drag(p1, p2, segments=2, shake=(0, 25), point_random=(0, 0, 0, 0), shake_random=(-3, 0, 3, 0))
            self.device.sleep(0.3)
        
        logger.warning('No more dossier reward for receiving')
        return False

    def dossier_reward_search(self):
        """
        Search for dossier rewards
        
        Pages: 
            in: page_meta
            out: page_meta
        """
        logger.hr('Search for dossier red dots')
        return self._meta_dock_swipe()


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
    
    def meta_reward_exit(self, skip_first_screenshot=True):
        """
        Pages:
            in: REWARD_CHECK
            out: page_meta
        """
        logger.info('Meta reward exit')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(BACK_ARROW, offset=(20, 20), interval=3):
                continue

            #End
            if self.ui_page_appear(page_meta):
                break

    def run(self, dossier=True):
        if self.config.SERVER in ['cn', 'en', 'jp']:
            pass
        else:
            logger.info(f'MetaReward is not supported in {self.config.SERVER}, please contact server maintainers')
            return

        self.ui_ensure(page_meta)

        if self.meta_reward_notice_appear():
            self.meta_reward_enter()
            self.meta_reward_receive()
            self.meta_reward_exit()

        # If dossier beacon is not enabled, or MetaReward is invoked by AshBeaconAssist, 
        # do not need to check dossier 
        if not dossier or self.config.OpsiAshBeacon_AttackMode != 'current_dossier':
            return
        
        while 1:
            if not self.dossier_reward_search():
                break
