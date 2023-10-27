from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger


class CampaignBase(CampaignBase_):
    """
    In Ashen Simulacrum chapter BD, there will be siren dace.
    Dace appears at the beginning, disappear and re-appear after player moved, but doesn't move.
    Override full scan methods to make sure that, Dace can be kept when tracking siren movements.
    """
    dace = None

    def full_scan_movable(self, *args, **kwargs):
        self.dace = self.map.select(enemy_genre='Siren_Dace')
        logger.attr('Submarine_Dace', self.dace)

        super().full_scan_movable(*args, **kwargs)

    def full_scan(self, *args, **kwargs):
        super().full_scan(*args, **kwargs)

        if self.dace is not None:
            logger.attr('Submarine_Dace', self.dace)
            for grid in self.dace:
                grid.is_siren = True
                grid.enemy_genre = 'Siren_Dace'
            self.dace = None

    def get_map_clear_percentage(self):
        """
        map clear here is shorter than normal, about 70% at max

        Returns:
            float: 0 to 1.
        """
        value = super().get_map_clear_percentage()
        chapter, _ = self._campaign_separate_name(self.MAP.name.lower())
        chapter = self._campaign_get_chapter_index(chapter)
        if chapter == 1:
            value *= 1.4
        return value
