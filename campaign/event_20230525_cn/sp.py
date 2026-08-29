def parse_move(movement: str, step: int):
    if step % len(movement) != 0:
        raise ScriptError('Invalid movement')
    movement = movement * int(step / len(movement))
    dx, dy = (0, 0)
    for direction in movement:
        dx += 1 if direction == 'R' else 0
        dx -= 1 if direction == 'L' else 0
        dy += 1 if direction == 'D' else 0
        dy -= 1 if direction == 'U' else 0
    return (dx, dy)

class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    siren_list = [C7, D6, G6, H7]
    patched = False
    action = []
    def execute_actions(self, step):
        for action in self.action[step]:
            fleet_index, movement, step, battle = action.split('_')
            src = self.__getattribute__(f'fleet_{fleet_index}_location')
            fleet = self.__getattribute__(f'fleet_{fleet_index}')
            step = int(step)
            dx, dy = parse_move(movement, step)
            dst = (src[0] + dx, src[1] + dy)
            logger.info(f'{fleet_index}{movement}({step}): {src} -> {dst}')
            for _ in range(3):
                if battle:
                    fleet.clear_chosen_enemy(location2node(dst))
                else:
                    fleet.goto(location2node(dst))
                fleet_location = self.__getattribute__(f'fleet_{fleet_index}_location')
                if fleet_location not in [src, dst]:
                    raise RequestHumanTakeover(f'Fleet{fleet_index} fail to move {src} -> {dst}, now on {fleet_location}')
                elif fleet_location == dst:
                    break
                else:
                    logger.warning(f'Fleet{fleet_index} did not move, retry')
        return True
    def battle_0(self):
        if not self.patched:
            for battle_count in range(1, 7):
                setattr(self, f'battle_{battle_count}', self.battle_0)
            self.patched = True
        if self.map_is_clear_mode:
            if self.siren_list:
                self.fleet_1.clear_chosen_enemy(self.siren_list.pop())
                return True
            elif self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
                return True
        else:
            if not self.action:
                self.action = actions[self.fleet_1_location[0]]
            return self.execute_actions(self.battle_count)
    def battle_7(self):
        return self.fleet_boss.clear_boss()
