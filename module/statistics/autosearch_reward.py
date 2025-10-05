import time
import cv2
import datetime
from module.logger import logger
from module.base.utils import crop
from module.statistics.assets import REWARD_HEADER2, REWARD_AREA

class AutosearchReward():

    def wait_until_reward_stable(self, timeout=6.6, required_consecutive_matches=3):
        """
        checks if all rewards have appeared, via offset matching header 2, after that waits till the reward area has no changes
        e.g all drops appeared

        timeout: may need adjustment after gathering data; 5.84s longest atm\\
        required_consecutive_matches: 3 seems a good compromise
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            self.device.screenshot()
            
            # 1. Detect header2
            if not self.appear(REWARD_HEADER2, offset=(200,0)):
                logger.warning("Header not found within search area")
                return False
                
            # 2. Apply detected offset to reward area
            REWARD_AREA.load_offset(REWARD_HEADER2)
            logger.info(f"Applied offset: {REWARD_HEADER2._button_offset}")
            
            # 3. Get adjusted coordinates
            adjusted_area = REWARD_AREA.button
            
            # 4. Validate (prevent negative width)
            if adjusted_area[0] >= adjusted_area[2]:
                logger.warning(f"Invalid area after offset: {adjusted_area}")
                return False
                
            # 5. stable area check
            # similarity_threshold: in testing the similarity ranged in 0.002- 0.01 ranges so opted for 0.999

            return self.reward_area_stable_check(monitor_area=adjusted_area, timeout=timeout, required_matches=required_consecutive_matches,similarity_threshold=0.999, timestamp=timestamp)
            
        except Exception as e:
            logger.error(f"Offset application failed: {e}")
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

        initial_gray = cv2.cvtColor(self.device.image, cv2.COLOR_BGR2GRAY)
        last_luma = crop(initial_gray, monitor_area)

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

                        return True
                else:
                    consecutive_matches = 0
                    stabilization_start = None

                last_luma = current_luma
