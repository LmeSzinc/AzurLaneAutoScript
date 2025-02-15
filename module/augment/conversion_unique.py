from module.augment.assets import *
from module.base.timer import Timer
#from module.base.base import ModuleBase
from module.exception import ScriptError
from module.logger import logger
#from module.ocr.ocr import Digit
from module.retire.dock import CARD_GRIDS, DOCK_EMPTY, Dock, SHIP_DETAIL_CHECK
from module.equipment.equipment import *
from module.equipment.assets import SHIP_INFO_EQUIPMENT_CHECK, SWIPE_AREA
from module.ui.assets import BACK_ARROW
from module.ui.page import page_dock, page_main

#used awaken task as a sort of blueprint and modified accordingly

class ConversionUnique(Dock):

    # not sure if even needed, also unsure how having no conversion material looks like
    #  def _get_button_state(self, button: Button):
    #     """
    #     Args:
    #         button: COST_CONVT2

    #     Returns:
    #         bool: True if having sufficient resource, False if not
    #     """
    #     if button.match(self.device.image):
    #         if self.image_color_count(area, color=(214, 53, 33), threshold=180, count=16):
    #             return False
    #         else:
    #             return True

    #maybe not a standalone def needed for this one
    def handle_convt2_finish(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

        return self.appear_then_click(CONVT2_FINISH, offset=(20, 20), interval=1)
    
    # checking if we are actually in gear page
    def is_in_gear(self):
        interval= Timer (3)
        interval.reached
        return AUGMENT_INGEAR_CONFIRM.appear_on(self.device.image) and SHIP_INFO_EQUIPMENT_CHECK.appear_on(self.device.image)

    # closing augment popup
    def augment_popup_close(self, skip_first_screenshot=True):
        logger.info('Augment popup close')
        #self.interval_clear(AUGMENT_CANCEL)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.is_in_gear():
                return
            if self.appear_then_click(AUGMENT_CANCEL):
                continue
            if self.appear_then_click(AUGMENT_CANCEL2):
                continue

            # if self.handle_convt2_finish():
            #     continue

    #get out of gear or dock to main page
    def augment_exit(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_in_gear or dock
            out: MAIN
        """
        logger.info('Gear exit')
        interval = Timer(3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.ui_page_appear(page_dock):
                logger.info(f'Gear exit at {page_dock}')
                continue
            # if self.appear_then_click(AUGMENT_CANCEL, interval=3, similarity=0.55):
            # if self.augment_popup_close():
            #     continue
            # if self.handle_convt2_finish():
            #     continue            
            if interval.reached() and self.is_in_gear():
                logger.info(f'is_in_gear -> {BACK_ARROW}')
                self.device.click(BACK_ARROW)
                self.device.click(BACK_ARROW)
                interval.reset()
                continue
            if self.is_in_main(interval=5):
                break
    #one cycle of augment enhancing
    def conv_uniq_enhance(self, skip_first_screenshot=False):
        
        logger.hr('Enhance unique module', level=2)
        while not self.appear(AUGMENT_EMPTY):

            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            self.not_appear_then_click(AUGMENT_EMPTY, AUGMENT_INGEAR_CONFIRM, interval=3)

            if skip_first_screenshot:
                 skip_first_screenshot = False
            else:
                 self.device.screenshot()

            logger.hr('Unique module found', level=2)
            if self.appear_then_click(CONVT2_SELECT, screenshot=False, interval=3):
             logger.hr('Convertible module found', level=2)   
             #self.appear_then_click(CONVT2_SELECT, interval=3)         
             while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False 
                else:
                    self.device.screenshot()

                #augment already has max conversion
                if self.appear(CONVT2_MAX, interval=3):
                    logger.hr('Conversion at max')
                    break
                #in case of misclick into crafting menu, maybe not needed
                # if self.appear(AUGMENT_CRAFT):
                #     break

                #when already enhanced but augment not yet max
                if self.handle_convt2_finish():
                    logger.hr('Conversion in progress')
                    continue
                #actual conversion enhancing part
                if self.appear(CONVT2_START, interval=3):
                    logger.hr('Conversion start')
                    self.appear_then_click(CONVT2_START_COST, interval=3)
                 #interval.reset()
                    self.appear_then_click(CONVT2_START, interval=3)
                    self.appear_then_click(CONVT2_NEW, interval=3)
                    continue
                self.augment_popup_close()
                break
            return
        else:
            return 'no unique equipped'
            
    def not_appear_then_click(self, button, checkbutton, screenshot=False, genre='items', offset=0, interval=3, similarity=0.85, threshold=30):
        button = self.ensure_button(button)
        checkbutton = self.ensure_button(checkbutton)
        appear = self.appear(button, offset=offset, interval=interval, similarity=similarity, threshold=threshold)
        checkappear = self.appear(checkbutton, offset=offset, interval=interval, similarity=similarity, threshold=threshold)
        if not appear and checkappear:  # Execute click when appear is False and checkappear is True
            if screenshot:
                self.device.sleep(self.config.WAIT_BEFORE_SAVING_SCREEN_SHOT)
                self.device.screenshot()
                self.device.save_screenshot(genre=genre)
            self.device.click(button)
        return
    
#modified version of the original inside module.equipment.equipment.py; didn't know how to exclude the retire specific if
    def _ship_view_swipe(self, distance, check_button=AUGMENT_INGEAR_CONFIRM):
        swipe_count = 0
        swipe_timer = Timer(5, count=10)
        self.handle_info_bar()
        SWIPE_CHECK.load_color(self.device.image)
        SWIPE_CHECK._match_init = True  # Disable ensure_template() on match(), allows ship to be properly determined
        # whether actually different or not
        while 1:
            if not swipe_timer.started() or swipe_timer.reached():
                swipe_timer.reset()
                self.device.swipe_vector(vector=(distance, 0), box=SWIPE_AREA.area, random_range=SWIPE_RANDOM_RANGE,
                                         padding=0, duration=(0.1, 0.12), name='SHIP_SWIPE')
                # self.wait_until_appear(check_button, offset=(30, 30))
                skip_first_screenshot = True
                while 1:
                    if skip_first_screenshot:
                        skip_first_screenshot = False
                    else:
                        self.device.screenshot()
                    if self.appear(check_button, offset=(30, 30)):
                        break
                swipe_count += 1

            self.device.screenshot()

            swipe_result = SWIPE_CHECK.match(self.device.image)  # Capture the match result

            if swipe_result:
                if swipe_count > 1:
                    logger.info('Same ship on multiple swipes')
                    return False, #swipe_result
                continue

            if self.appear(check_button, offset=(30, 30)) and not swipe_result:
                logger.info('New ship detected on swipe')
                return True, #swipe_result
            
        # def ship_view_next(self, check_button=AUGMENT_INGEAR_CONFIRM):
        #  return self._ship_view_swipe(distance=-SWIPE_DISTANCE, check_button=check_button)

    def conv_uniq_cycle(self, skip_first_screenshot=False):
        logger.hr('Augment conversion: Uniques', level = 3)
        interval =Timer(3)
        while interval.reached():
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.is_in_gear():
                self.conv_uniq_enhance()
                continue
            if self._ship_view_swipe(-400) is True:
                continue
            if self._ship_view_swipe(-400) is False:
                break



    def conv_uniq_run(self):
        """
        Navigation towards menu in order to enhance unique augments only and exit after

        Returns:
            str: 'dock empty', 'finish', 'timeout'

        Pages:
            in: Any
            out: page_dock
        """
        logger.hr('Unique augment conversion run', level=1)
        self.ui_ensure(page_dock)
        self.dock_favourite_set(wait_loading=False)
        self.dock_sort_method_dsc_set(wait_loading=False)
        extra = ['unique_augment_module']
        self.dock_filter_set(extra=extra)

        if self.appear(DOCK_EMPTY, offset=(20, 20)):
            logger.info('no ships with unique modules owned')
            self.augment_exit()
            return 'dock empty'
        
        elif self.ship_info_enter(CARD_GRIDS[(0, 0)], check_button=SHIP_DETAIL_CHECK, long_click=False) or (self.ship_side_navbar_ensure(bottom=2)):
            self.conv_uniq_cycle()
            # while 1:
            #     if self.conv_uniq_cycle():
            #          continue
            #     if self._ship_view_swipe(-400) is True:
            #           continue
            #     if self._ship_view_swipe(-400) is False:
            #         #logger
            #          return 'finish'
# reevaluete gear assets, maybe include 'gear' 
   
        # elif self.appear_then_click(GEAR_ENTER_DEFAULT, offset = 0) or self.appear_then_click(GEAR_ENTER_RETRO, offset = 0) or self.appear_then_click(GEAR_ENTER_META_PRDR, offset = 0):
        #     while 1:
        #         if self.conv_uniq_cycle():
        #              continue
        #         if self._ship_view_swipe(200) is True:
        #              continue
        #         if self._ship_view_swipe(200) is False:
        #             #logger
        #              return 'finished'                
            
            # page_dock -> SHIP_DETAIL_CHECK
        else:
            raise ScriptError(f'STH went wrong in conv uniq run')

        
            
            # is_in_gear

 #           break
#                if self._ship_view_swipe():

#                 return False
    

        # page_dock empty

#                result = 'finish'
            # # 'insufficient', 'maxed value', 'timeout'
            # if result in ('no module','max value'):
            #     # Next module conversion, due to no unique equipped or due to current unique reaching maxed value
            #     continue
            # if result == 'insufficient':
            #     logger.info('conv_uniq_run finished, resources exhausted')
            #     break
            # if result == 'timeout':
            #     logger.info(f'conv_uniq_run finished, result={result}')
            #     break
#                    else:
#         raise ScriptError(f'Unexpected conv_uniq result: {result}')

#        else:
 #        raise ScriptError(f'Unexpected conv_uniq result: Neither empty dock nor clickable ship')


    def run(self):
        if self.config.SERVER not in ['cn', 'en']:
            logger.error(f'Task "Augment" is not available on server {self.config.SERVER} yet, '
                         f'please contact server maintainers')
            self.config.task_stop()

        if self.config.Augment_ConversionUnique == True:
            self.conv_uniq_run()
            self.augment_exit()
        else:
            raise ScriptError(f'Tried to run an yet undeveloped/unknown Augment Task')

        # Reset dock filters
        logger.hr('Augment run exit', level=1)
        self.dock_filter_set(wait_loading=False)

        # Scheduler
        self.config.task_stop(message= 'Augment Task Conversion_unique has finished')
