class Campaign(CampaignBase):
    grid_class = CurrentFleetGrid

    def in_sight(self, location, sight=None):
        logger.info('In sight: %s' % location2node(location))
        x, y = location
        if x >= 7 and y <= 4:
            x = 7
            location = (x, y)
            logger.info('In sight: %s' % location2node(location))
            return super().focus_to(location)
        if x <= 4 and y <= 4:
            x = 3
            location = (x, y)
            logger.info('In sight: %s' % location2node(location))
            return super().focus_to(location)
        return super().in_sight(location, sight=sight)
