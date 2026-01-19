from module.base.base import ModuleBase
from module.base.timer import Timer
from module.combat.assets import *
from module.logger import logger


class SubmarineCall(ModuleBase):
    submarine_call_flag = False
    submarine_call_timer = Timer(5)
    submarine_call_click_timer = Timer(1)
    submarine_call_delay_timer = None
    submarine_call_delay_passed = True
    auto_search_battle_count = 0  # Track battle count in auto search

    def submarine_call_reset(self):
        """
        Call this method after in battle_execute.
        """
        try:
            delay = float(getattr(self.config, 'Submarine_CallDelay', 0) or 0)
        except (TypeError, ValueError):
            delay = 0
        delay = max(delay, 0)

        # Allow extra time for the delay before giving up on the call
        self.submarine_call_timer.limit = 5 + delay
        self.submarine_call_timer.reset()

        if delay > 0:
            self.submarine_call_delay_timer = Timer(delay).reset()
            self.submarine_call_delay_passed = False
        else:
            self.submarine_call_delay_timer = None
            self.submarine_call_delay_passed = True

        self.submarine_call_flag = False

    def _should_call_submarine_at_battle(self):
        """
        Check if submarine should be called at current battle in auto search mode.
        Only effective when Submarine_AutoSearchMode is 'sub_call_at_battle'.

        Returns:
            bool: If submarine should be called at this battle.
        """
        if self.config.Submarine_AutoSearchMode != 'sub_call_at_battle':
            return False

        try:
            call_at_battles = self.config.Submarine_CallAtBattle
            
            # Handle None or empty values
            if call_at_battles is None:
                return False
            
            # Convert to string if it's an integer
            if isinstance(call_at_battles, int):
                call_at_battles = str(call_at_battles)
            
            # Now check if it's a valid string
            if not isinstance(call_at_battles, str) or not call_at_battles.strip():
                return False
            
            # Parse comma-separated battle numbers
            battle_list = [int(x.strip()) for x in call_at_battles.split(',') if x.strip().isdigit()]
            return self.auto_search_battle_count in battle_list
        except (AttributeError, ValueError, TypeError) as e:
            logger.warning(f'Failed to parse Submarine_CallAtBattle: {e}')
            return False

    def handle_submarine_call(self, submarine='do_not_use'):
        """
        Returns:
            str: If call.
        """
        if self.submarine_call_flag:
            return False
        if submarine in ['do_not_use', 'hunt_only', 'hunt_and_boss']:
            self.submarine_call_flag = True
            return False

        # For 'sub_call_at_battle' mode, check if should call at this battle
        if hasattr(self, 'map_is_auto_search') and self.map_is_auto_search:
            auto_search_mode = getattr(self.config, 'Submarine_AutoSearchMode', 'sub_standby')
            if auto_search_mode == 'sub_call_at_battle':
                # Only call if specified in CallAtBattle list
                if not self._should_call_submarine_at_battle():
                    self.submarine_call_flag = True
                    return False
                # If should call, respect delay
            elif auto_search_mode in ['sub_standby', 'sub_auto_call']:
                # For standby and auto_call modes, ignore delay and don't actively call
                self.submarine_call_flag = True
                return False

        if not self.submarine_call_delay_passed:
            if self.submarine_call_delay_timer and self.submarine_call_delay_timer.reached():
                self.submarine_call_delay_passed = True
            else:
                return False

        if self.submarine_call_timer.reached():
            logger.info('Submarine call timer reached')
            self.submarine_call_flag = True
            return False

        if not self.appear(SUBMARINE_AVAILABLE_CHECK_1) or not self.appear(SUBMARINE_AVAILABLE_CHECK_2):
            return False

        if self.appear(SUBMARINE_CALLED):
            logger.info('Submarine called')
            self.submarine_call_flag = True
            return False
        elif self.submarine_call_click_timer.reached():
            if not self.appear_then_click(SUBMARINE_READY):
                logger.info('Incorrect submarine icon')
                self.device.click(SUBMARINE_READY)
            logger.info('Call submarine')
            self.submarine_call_click_timer.reset()
            return True
