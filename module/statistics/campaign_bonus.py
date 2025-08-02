from module.base.button import ButtonGrid
from module.base.utils import *
from module.handler.assets import AUTO_SEARCH_MENU_EXIT, AUTO_SEARCH_MENU_CONTINUE
from module.statistics.assets import CAMPAIGN_BONUS
from module.statistics.get_items import ITEM_GROUP, GetItemsStatistics
from module.statistics.item import Item, AmountOcr
from module.statistics.utils import *
from module.logger import logger
from module.base.timer import Timer
import time
import os
import cv2

class BonusItem(Item):
    def predict_valid(self):
        return np.mean(rgb2gray(self.image) > 160) > 0.1


class CampaignBonusStatistics(GetItemsStatistics,ButtonGrid,Timer):
    def appear_on(self, image):
        if AUTO_SEARCH_MENU_EXIT.match(image, offset=(200, 20)) \
                and CAMPAIGN_BONUS.match(image, offset=(20, 500)):
            return True

        return False

    def _stats_get_items_load(self, image):
        ITEM_GROUP.item_class = BonusItem
        ITEM_GROUP.similarity = 0.85
        ITEM_GROUP.amount_area = (35, 51, 63, 63)
        origin = area_offset(CAMPAIGN_BONUS.button, offset=(-7, 34))[:2]
        grids = ButtonGrid(origin=origin, button_shape=(64, 64), grid_shape=(7, 2), delta=(72 + 2 / 3, 75))

        reward_bottom = AUTO_SEARCH_MENU_EXIT.button[1]
        grids.buttons = [button for button in grids.buttons if button.area[3] < reward_bottom]
        ITEM_GROUP.grids = grids

    def stats_get_items(self, image, **kwargs):
        """
        Args:
            image (np.ndarray):

        Returns:
            list[Item]:
        """
        result = super().stats_get_items(image, **kwargs)
        valid = False
        for item in result:
            if item.name == 'Coin':
                valid = True
        if valid:
            return [self.revise_item(item) for item in result]
        else:
            raise ImageError('Campaign bonus image does not have coins, dropped')

    def revise_item(self, item):
        """
        Args:
            item (Item):

        Returns:
            Item:
        """
        # Campaign bonus drop 9 to 30+ chips, but sometimes 10 is detected as 1.
        if item.name == 'Chip' and 0 < item.amount < 4:
            item.amount *= 10

        return item

    def wait_until_reward_stable(self, timeout=8.6, required_consecutive_matches=3, similarity_threshold=0.999):
        """
        checks if all rewards have appeared, via first doing a predicted grid, 3 types to account for the Ui
        change due to Meta xp, then verifies via amount ocr, after that waits till the reward area has no changes
        e.g all drops appeared

        timeout: may or may not need adjustment, after gathering data\\
        required_consecutive_matches: 3 seems a good compromise\\
        similarity_threshold: in testing the similarity ranged in 0.002- 0.01 ranges so opted for 0.999
        """
        logger.info('wait until area stable')
        
        try:
            # 1. Setup debug directories
            os.makedirs('./screenshots/debug', exist_ok=True)
            os.makedirs('./screenshots/dropstats', exist_ok=True)
            
            # 2. Image handling separation, ocr uses non modified, area stable check uses modified
            self.device.screenshot()
            original_bgr = self.device.image.copy()
            gray_image = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2GRAY)
            
            # 3. Debugging/Reference visualization (BGR)
            exit_btn = AUTO_SEARCH_MENU_EXIT._button
            continue_btn = AUTO_SEARCH_MENU_CONTINUE._button
            debug_img = original_bgr.copy()
            cv2.rectangle(debug_img, (exit_btn[0], exit_btn[1]), (exit_btn[2], exit_btn[3]), (255,0,0), 2)
            cv2.rectangle(debug_img, (continue_btn[0], continue_btn[1]), (continue_btn[2], continue_btn[3]), (0,0,255), 2)
            cv2.imwrite('./screenshots/debug/reference_points.png', debug_img)

            # 4. Grid setup with single row, tested with EN, CN is fine due to same button,
            #continue button shift less of an issue, but alot of the measures depend on exit
            #TW might have grid too low and ocr area might miss the numbers area
            #compared to EN/CN: exit width -42, height -9, continue width -3, height -5
            #JP gonna have issues due to not using a default exit asset, ui moved due to meta xp sidebar
            #compared to EN/CN: exit width -1, height -1, but further on the left by 68px
            #continue width -1, height the same, but further on the right side by 72px
            GRID_PARAMS = {
                'button_shape': (64, 64),
                'grid_shape': (7, 1),  # need to only check first row
                'delta': (72 + 2/3, 0),
                'name': 'REWARD_GRID'
            }
            exit_x, exit_y = exit_btn[0], exit_btn[1]
            GRID_ORIGINS = [
                (exit_x + 22, exit_y - 417),    # Primary
                (exit_x + 22 - 72, exit_y - 417),  # Fallback 1
                (exit_x + 22 - 129, exit_y - 417)  # Fallback 2
            ]

            # 5. Grid verification with early exit
            for i, (grid_x, grid_y) in enumerate(GRID_ORIGINS):
                grid = ButtonGrid(origin=(grid_x, grid_y), **GRID_PARAMS)
                
                # Process all buttons but exit on first match
                matched = self._verify_grid_via_ocr(grid, i, original_bgr)
                if matched:
                    logger.info(f"Grid {i} validated")
                    continue_btn = AUTO_SEARCH_MENU_CONTINUE._button
                    monitor_area = (grid_x, grid_y, grid_x + (7 * (72 + 2/3)), continue_btn[1])
                    self.device.image = gray_image
                    return self.reward_area_stable_check(monitor_area,timeout,required_consecutive_matches,similarity_threshold)
            
            logger.warning("All grid positions failed")
            return False

        except Exception as e:
            logger.error(f'Stabilization failure: {str(e)}')
            return False

    def _verify_grid_via_ocr(self, grid, bgr_image):
        """
        double checks if grid correct via the item amount on the bottom right of grid buttons
        """
        amount_ocr = AmountOcr([], threshold=96, name='Amount_ocr')
        
        for i, btn in enumerate(grid.buttons):
            try:
                # 1. Get button image (keep as BGR)
                button_img = crop(bgr_image, btn.area)
                
                # 2. area should be big enough to catch random strays
                #mainly looking at JP since they used an exit button as reference where a meta ship gained xp on the side
                #whereas CN/EN/TW used the default one,
                h, w = button_img.shape[:2]
                amount_area = (int(w*0.6), int(h*0.8),w,h)
                amount_img = crop(button_img, amount_area)
                
                # 3. Ensure keep BGR format for OCR
                if len(amount_img.shape) == 2:
                    amount_img = cv2.cvtColor(amount_img, cv2.COLOR_GRAY2BGR)
                
                # 4. OCR just like the one in ItemGrid in item.py
                amount = amount_ocr.ocr([amount_img], direct_ocr=True)[0]
                logger.info(f"amount: {amount}")
                if amount > 0:
                    return True
                    
            except Exception as e:
                logger.warning(f"Button {i} check failed: {str(e)}")
                continue
        
        return False

    def reward_area_stable_check(self, monitor_area, timeout, required_matches, similarity_threshold):
        """
        checks if the previously assigned area has any changes

        returns True for being stable after 3 same consecutive matches, while similarity was met or beaten
        """
        start_time = time.time()
        stabilization_start = None
        consecutive_matches = 0
        check_count = 0
        
        last_luma = crop(self.device.image, monitor_area)
        cv2.imwrite('./screenshots/dropstats/0_initial.png', last_luma)

        while True:
            current_time = time.time()
            elapsed = current_time - start_time
            
            if elapsed >= timeout:
                logger.warning(f'Timeout after {elapsed:.2f}s (never stabilized)')
                return False

            if current_time - last_check >= 0.2:
                check_count += 1
                last_check = current_time
                
                self.device.screenshot()
                current_luma = cv2.cvtColor(self.device.image, cv2.COLOR_BGR2GRAY)
                current_luma = crop(current_luma, monitor_area)
                cv2.imwrite(f'./screenshots/dropstats/{check_count}_check.png', current_luma)

                res = cv2.matchTemplate(last_luma, current_luma, cv2.TM_CCOEFF_NORMED)
                similarity = cv2.minMaxLoc(res)[1]
                
                if similarity >= similarity_threshold:
                    consecutive_matches += 1
                    if stabilization_start is None:
                        stabilization_start = time.time()
                    
                    if consecutive_matches >= required_matches:
                        stabilization_time = time.time() - stabilization_start
                        total_time = time.time() - start_time
                        logger.info(f'Area stabilized after {total_time:.2f}s (took {stabilization_time:.2f}s to confirm)')
                        cv2.imwrite('./screenshots/dropstats/final_stable.png', current_luma)
                        return True
                else:
                    consecutive_matches = 0
                    stabilization_start = None

                last_luma = current_luma
