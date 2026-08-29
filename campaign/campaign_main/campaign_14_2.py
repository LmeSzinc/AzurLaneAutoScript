class Campaign(CampaignBase):

    def battle_0(self):
        if not self.picked_flare and H7.is_accessible and A5.is_accessible:
            self.fleet_boss.pick_up_flare(H7)
            self.fleet_boss.pick_up_flare(A5)
            self.fleet_boss.goto(D6)
            self.fleet_1.switch_to()
        if self.clear_roadblocks([road_A5, road_H7], weakest=True):
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True
        return self.battle_default()
