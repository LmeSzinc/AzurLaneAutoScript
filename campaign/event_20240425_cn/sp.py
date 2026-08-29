class Campaign(CampaignBase):

    def map_data_init(self, map_):
        super().map_data_init(map_)
        D4.is_siren = True
        D6.is_siren = True
        F4.is_siren = True
        F6.is_siren = True

    def is_event_animation(self):
        if self.image_color_count((1193, 322, 1273, 329), color=(255, 255, 255), count=500):
            logger.info('Live start!')
            return True
        return False
