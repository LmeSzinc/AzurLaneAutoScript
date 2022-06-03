from module.campaign.assets import *
from module.campaign.campaign_event import CampaignEvent
from module.campaign.campaign_ocr import CampaignOcr
from module.exception import CampaignNameError, ScriptEnd
from module.logger import logger
from module.ui.assets import CAMPAIGN_CHECK
from module.ui.switch import Switch

MODE_SWITCH_1 = Switch("Mode_switch_1", offset=(30, 10))
MODE_SWITCH_1.add_status("normal", SWITCH_1_NORMAL)
MODE_SWITCH_1.add_status("hard", SWITCH_1_HARD)
MODE_SWITCH_2 = Switch("Mode_switch_2", offset=(30, 10))
MODE_SWITCH_2.add_status("hard", SWITCH_2_HARD)
MODE_SWITCH_2.add_status("ex", SWITCH_2_EX)


class CampaignUI(CampaignEvent, CampaignOcr):
    ENTRANCE = Button(area=(), color=(), button=(), name="default_button")

    def campaign_ensure_chapter(self, index):
        """
        Args:
            index (int, str): Chapter. Such as 7, 'd', 'sp'.
        """
        index = self._campaign_get_chapter_index(index)

        # A tricky way to use ui_ensure_index.
        self.ui_ensure_index(
            index,
            letter=self.get_chapter_index,
            prev_button=CHAPTER_PREV,
            next_button=CHAPTER_NEXT,
            fast=True,
            skip_first_screenshot=True,
            finish_sleep=0,
        )

    def campaign_ensure_mode(self, mode="normal"):
        """
        Args:
            mode (str): 'normal', 'hard', 'ex'

        Returns:
            bool: If mode changed.
        """
        switch_2 = MODE_SWITCH_2.get(main=self)

        if switch_2 == "unknown":
            if mode == "ex":
                logger.warning("Trying to goto EX, but no EX mode switch")
            elif mode == "normal":
                MODE_SWITCH_1.set("hard", main=self)
            elif mode == "hard":
                MODE_SWITCH_1.set("normal", main=self)
            else:
                logger.warning(f"Unknown campaign mode: {mode}")
        else:
            if mode == "ex":
                MODE_SWITCH_2.set("hard", main=self)
            elif mode == "normal":
                MODE_SWITCH_2.set("ex", main=self)
                MODE_SWITCH_1.set("hard", main=self)
            elif mode == "hard":
                MODE_SWITCH_2.set("ex", main=self)
                MODE_SWITCH_1.set("normal", main=self)
            else:
                logger.warning(f"Unknown campaign mode: {mode}")

    def campaign_get_entrance(self, name):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.

        Returns:
            Button:
        """
        if name not in self.stage_entrance:
            logger.warning(f"Stage not found: {name}")
            raise CampaignNameError

        entrance = self.stage_entrance[name]
        entrance.name = name
        return entrance

    def campaign_set_chapter_main(self, chapter, mode="normal"):
        if chapter.isdigit():
            self.ui_goto_campaign()
            self.campaign_ensure_mode("normal")
            self.campaign_ensure_chapter(index=chapter)
            if mode == "hard":
                self.campaign_ensure_mode("hard")
                # info_bar shows: Hard mode for this map is not available yet.
                # There's also a game bug in EN, HM12 shows not available but it's actually available.
                self.handle_info_bar()
                self.campaign_ensure_chapter(index=chapter)
            return True
        else:
            return False

    def campaign_set_chapter_event(self, chapter, mode="normal"):
        if chapter in ["a", "b", "c", "d", "ex_sp", "as", "bs", "cs", "ds", "t"]:
            self.ui_goto_event()
            if chapter in ["a", "b", "as", "bs", "t"]:
                self.campaign_ensure_mode("normal")
            elif chapter in ["c", "d", "cs", "ds"]:
                self.campaign_ensure_mode("hard")
            elif chapter == "ex_sp":
                self.campaign_ensure_mode("ex")
            self.campaign_ensure_chapter(index=chapter)
            return True
        else:
            return False

    def campaign_set_chapter_sp(self, chapter, mode="normal"):
        if chapter == "sp":
            self.ui_goto_sp()
            self.campaign_ensure_chapter(index=chapter)
            return True
        else:
            return False

    def campaign_set_chapter(self, name, mode="normal"):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
        """
        chapter, _ = self._campaign_separate_name(name)

        if self.campaign_set_chapter_main(chapter, mode):
            pass
        elif self.campaign_set_chapter_event(chapter, mode):
            pass
        elif self.campaign_set_chapter_sp(chapter, mode):
            pass
        else:
            logger.warning(f"Unknown campaign chapter: {name}")

    def ensure_campaign_ui(self, name, mode="normal"):
        for n in range(20):
            try:
                self.campaign_set_chapter(name, mode)
                self.ENTRANCE = self.campaign_get_entrance(name=name)
                return True
            except CampaignNameError:
                pass

            self.device.screenshot()

        logger.warning("Campaign name error")
        raise ScriptEnd("Campaign name error")

    def commission_notice_show_at_campaign(self):
        """
        Returns:
            bool: If any commission finished.
        """
        return self.appear(CAMPAIGN_CHECK, offset=(20, 20)) and self.appear(
            COMMISSION_NOTICE_AT_CAMPAIGN
        )
