import time
import cv2
import datetime
import numpy as np
from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.logger import logger
from module.base.utils import crop
from module.handler.assets import AUTO_SEARCH_MENU_EXIT, AUTO_SEARCH_MENU_CONTINUE
from module.statistics.item import AmountOcr
from module.statistics.azurstats import AzurStats

class AutosearchReward(ButtonGrid, Timer, AzurStats):
    def wait_until_reward_stable(self, timeout=8.6, required_consecutive_matches=3, similarity_threshold=0.999):
        """
        checks if all rewards have appeared, via first doing a predicted grid, 3 types to account for the Ui
        change due to Meta xp, then verifies via amount ocr, after that waits till the reward area has no changes
        e.g all drops appeared

        timeout: may or may not need adjustment, after gathering data; 5.23s longest atm\\
        required_consecutive_matches: 3 seems a good compromise\\
        similarity_threshold: in testing the similarity ranged in 0.002- 0.01 ranges so opted for 0.999
        """
        logger.info('wait until area stable')

        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # 1. Image handling separation, ocr uses non modified, area stable check uses modified
            self.device.screenshot()
            original_bgr = self.device.image.copy()
            gray_image = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2GRAY)

            # 2. Debugging/Reference visualization (BGR)
            exit_btn = AUTO_SEARCH_MENU_EXIT._button
            continue_btn = AUTO_SEARCH_MENU_CONTINUE._button
            debug_img = original_bgr.copy()
            cv2.rectangle(debug_img, (exit_btn[0], exit_btn[1]), (exit_btn[2], exit_btn[3]), (255,0,0), 2)
            cv2.rectangle(debug_img, (continue_btn[0], continue_btn[1]), (continue_btn[2], continue_btn[3]), (0,0,255), 2)
            self._save(debug_img, 'debug', f'{timestamp}_reference_points.png')

            # 3. Grid setup with single row, tested with EN, CN is fine due to same button,
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
                (exit_x + 22, exit_y - 417),         # Grid 0 - Primary
                (exit_x + 22 - 72, exit_y - 417),   # Grid 1 - Fallback 1 (one button left)
                (exit_x + 22 - 129, exit_y - 417)   # Grid 2 - Fallback 2
            ]

            # 4. Enhanced grid verification logic
            validated_grids = []
            
            for i, (grid_x, grid_y) in enumerate(GRID_ORIGINS):
                grid = ButtonGrid(origin=(grid_x, grid_y), **GRID_PARAMS)
                matched = self._verify_grid_via_ocr(grid, i, original_bgr)
                
                if matched:
                    logger.info(f"Grid {i} validated")
                    validated_grids.append((i, grid_x, grid_y))
                    
                    # Special case: If Grid 0 validates, also check Grid 1
                    if i == 0 and len(GRID_ORIGINS) > 1:
                        logger.info("Grid 0 validated, checking Grid 1 for potentially more rewards...")
                        grid1_x, grid1_y = GRID_ORIGINS[1]
                        grid1 = ButtonGrid(origin=(grid1_x, grid1_y), **GRID_PARAMS)
                        grid1_matched = self._verify_grid_via_ocr(grid1, 1, original_bgr, check_first_button_only=True)
                        
                        if grid1_matched:
                            logger.info("Grid 1 also validated - using Grid 1 for wider coverage")
                            validated_grids.append((1, grid1_x, grid1_y))
                        else:
                            logger.info("Grid 1 failed validation - sticking with Grid 0")
                    
                    break  # Found at least one valid grid, proceed
            
            # 5. Select the best grid (prefer Grid 1 over Grid 0 if both validate)
            if not validated_grids:
                logger.warning("All grid positions failed")
                return False
                
            # Choose Grid 1 if available (better coverage), otherwise use the first validated grid
            best_grid = None
            for grid_info in validated_grids:
                grid_idx, grid_x, grid_y = grid_info
                if grid_idx == 1:  # Prefer Grid 1
                    best_grid = grid_info
                    break
            
            if best_grid is None:
                best_grid = validated_grids[0]  # Use first validated grid
            
            selected_idx, selected_x, selected_y = best_grid
            logger.info(f"Using Grid {selected_idx} for monitoring (x={selected_x}, y={selected_y})")
            
            # 6. Set up monitoring area with selected grid
            continue_btn = AUTO_SEARCH_MENU_CONTINUE._button
            monitor_area = (
                int(selected_x), 
                int(selected_y), 
                int(selected_x + (7 * 72.67)), 
                int(continue_btn[1])
            )
            
            logger.info(f"DEBUG - Selected Grid {selected_idx}: x={selected_x}, y={selected_y}")
            logger.info(f"DEBUG - Monitor area: {monitor_area}")
            
            self.device.image = gray_image
            return self.reward_area_stable_check(monitor_area, timeout, required_consecutive_matches, similarity_threshold, timestamp)

        except Exception as e:
            logger.error(f'Stabilization failure: {str(e)}')
            return False

    def _verify_grid_via_ocr(self, grid, grid_idx, bgr_image, check_first_button_only=False):
        """
        double checks if grid correct via the item amount on the bottom right of grid buttons
        special handling for grid0 vs grid1
        """
        amount_ocr = AmountOcr([], threshold=96, name='Amount_ocr')
        detected_amounts = []
        first_button_has_amount = False

        for btn_idx, btn in enumerate(grid.buttons):
            try:
                # 1. Get button image (keep as BGR)
                button_img = crop(bgr_image, btn.area)
                if button_img is None or button_img.size == 0:
                    continue

                # 2. Extract amount area (bottom-right portion)
                h, w = button_img.shape[:2]
                amount_area = (int(w*0.6), int(h*0.8), w, h)
                amount_img = crop(button_img, amount_area)

                # 3. Ensure BGR format for OCR
                if len(amount_img.shape) == 2:
                    amount_img = cv2.cvtColor(amount_img, cv2.COLOR_GRAY2BGR)

                # 4. OCR just like the one in ItemGrid in item.py
                amount = amount_ocr.ocr([amount_img], direct_ocr=True)[0]
                if amount > 0:
                    detected_amounts.append(amount)
                    logger.info(f"Grid {grid_idx}, Button {btn_idx}: amount={amount}")
                    
                    # Track if first button (index 0) has amount
                    if btn_idx == 0:
                        first_button_has_amount = True

            except Exception as e:
                logger.warning(f"Grid {grid_idx}, Button {btn_idx} check failed: {str(e)}")
                continue

        # Determine validation result
        total_detected = len(detected_amounts)
        
        if check_first_button_only:
            # For Grid 1 validation: only valid if first button has amount
            if first_button_has_amount:
                logger.info(f"Grid {grid_idx} summary: First button validated with amount - Grid 1 captures additional reward!")
                return True
            else:
                logger.info(f"Grid {grid_idx} summary: First button has no amount - Grid 1 offers no advantage")
                return False
        else:
            # Standard validation: any button with amount is sufficient
            if total_detected > 0:
                logger.info(f"Grid {grid_idx} summary: {total_detected} buttons with amounts detected")
                return True
            else:
                logger.info(f"Grid {grid_idx} summary: No amounts detected")
                return False

    def reward_area_stable_check(self, monitor_area, timeout, required_matches, similarity_threshold, timestamp=""):
        """
        checks if the previously assigned area has any changes
        returns True for being stable after 3 same consecutive matches, while similarity was met or beaten
        """
        start_time = time.time()
        last_check = start_time
        stabilization_start = None
        consecutive_matches = 0
        check_count = 0

        last_luma = crop(self.device.image, monitor_area)
        self._save(last_luma, 'debug/dropstats', f'{timestamp}_0_initial.png')

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
                self._save(current_luma, 'debug/dropstats', f'{timestamp}_{check_count}_check.png')

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
                        self._save(current_luma, 'debug/dropstats', f'{timestamp}_final_stable.png')
                        return True
                else:
                    consecutive_matches = 0
                    stabilization_start = None

                last_luma = current_luma
