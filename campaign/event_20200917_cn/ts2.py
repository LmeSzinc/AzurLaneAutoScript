class Campaign(CampaignBase):
    def battle_0(self):
        self.goto(A8, expected='story')
        self.goto(E7, expected='story')
        self.goto(B1, expected='story')
        self.goto(G8, expected='story')
        raise CampaignEnd()
