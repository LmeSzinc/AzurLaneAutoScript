from module.reward.oil import RewardOil
from module.reward.mission import RewardMission


class Reward(RewardOil, RewardMission):
    def run(self):
        self.reward_oil()
        self.reward_mission()
