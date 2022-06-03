from module.base.button import Button
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger

EVENT_ANIMATION = Button(
    area=(49, 229, 119, 400),
    color=(118, 215, 240),
    button=(49, 229, 119, 400),
    name="EVENT_ANIMATION",
)


class CampaignBase(CampaignBase_):
    """
    In event Vacation Lane (event_20201126_cn), DOA collaboration, maps are:
    Chapter 1: SP1, SP2, SP3, SP4.
    Chapter 2: VSP.
    Chapter 3: EX.
    Mode switch is meaningless.
    """

    @staticmethod
    def _campaign_get_chapter_index(name):
        """
        Args:
            name (str, int):

        Returns:
            int
        """
        if isinstance(name, int):
            return name
        else:
            if name.isdigit():
                return int(name)
            elif name in ["a", "c", "sp"]:
                return 1
            elif name in ["b", "d", "ex_sp"]:  # Difference
                return 2
            else:
                raise CampaignNameError

    def campaign_set_chapter(self, name, mode="normal"):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
        """
        chapter, stage = self._campaign_separate_name(name)

        if chapter.isdigit():
            self.ui_weigh_anchor()
            self.campaign_ensure_mode("normal")
            self.campaign_ensure_chapter(index=chapter)
            if mode == "hard":
                self.campaign_ensure_mode("hard")
                self.campaign_ensure_chapter(index=chapter)

        elif chapter in "abcd" or chapter == "ex_sp":
            self.ui_goto_event()
            if chapter in "ab":
                self.campaign_ensure_mode("normal")
            elif chapter in "cd":
                self.campaign_ensure_mode("hard")
            elif chapter == "ex_sp":
                pass  # Difference
            self.campaign_ensure_chapter(index=chapter)

        elif chapter == "sp":
            self.ui_goto_event()  # Difference
            self.campaign_ensure_chapter(index=chapter)

        else:
            logger.warning(f"Unknown campaign chapter: {name}")

    def is_event_animation(self):
        """
        Animation in events after cleared an enemy.

        Returns:
            bool: If animation appearing.
        """
        appear = self.appear(EVENT_ANIMATION)
        if appear:
            logger.info("DOA animation, waiting")
        return appear
