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
            logger.info(f'Submarine_AutoSearchMode is not sub_call_at_battle: {self.config.Submarine_AutoSearchMode}')
            return False

        try:
            call_at_battles = self.config.Submarine_CallAtBattle
            logger.info(f'Submarine_CallAtBattle config: {repr(call_at_battles)} (type: {type(call_at_battles).__name__})')
            
            # Handle None or empty values
            if call_at_battles is None:
                logger.info('CallAtBattle is None')
                return False
            
            # Convert to string if it's an integer
            if isinstance(call_at_battles, int):
                call_at_battles = str(call_at_battles)
                logger.info(f'Converted int to string: {repr(call_at_battles)}')
            
            # Now check if it's a valid string
            if not isinstance(call_at_battles, str) or not call_at_battles.strip():
                logger.info('CallAtBattle is empty or invalid type')
                return False
            
            # Parse comma-separated battle numbers
            battle_list = [int(x.strip()) for x in call_at_battles.split(',') if x.strip().isdigit()]
            logger.info(f'Parsed battle list: {battle_list}, current count: {self.auto_search_battle_count}')
            result = self.auto_search_battle_count in battle_list
            logger.info(f'Should call submarine: {result}')
            return result
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

        logger.info(f'handle_submarine_call: submarine={submarine}')
        # For 'sub_call_at_battle' mode, check if should call at this battle
        map_is_auto = getattr(self, 'map_is_auto_search', False)
        logger.info(f'map_is_auto_search: {map_is_auto}')
        if map_is_auto:
            auto_search_mode = getattr(self.config, 'Submarine_AutoSearchMode', 'sub_standby')
            logger.info(f'auto_search_mode: {auto_search_mode}')
            if auto_search_mode == 'sub_call_at_battle':
                # Only call if specified in CallAtBattle list
                if not self._should_call_submarine_at_battle():
                    logger.info('Not calling submarine at this battle')
                    self.submarine_call_flag = True
                    return False
                # If should call, respect delay
                logger.info('Proceeding to call submarine')
            elif auto_search_mode in ['sub_standby', 'sub_auto_call']:
                # For standby and auto_call modes, ignore delay and don't actively call
                logger.info('Standby/auto_call mode, not calling actively')
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
