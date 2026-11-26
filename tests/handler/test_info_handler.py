"""Tests for InfoHandler._continuous_story_skip.

The method only inspects device.click_record, so the handler is built with
object.__new__ to avoid creating a real config and device.

A real Device stores str(button) in click_record, which is the format the
method compares against str(STORY_SKIP). Both the deque used by Device and a
plain list are covered here.
"""
from collections import deque
from types import SimpleNamespace

from module.handler.assets import STORY_SKIP, STORY_SKIP_3
from module.handler.info_handler import InfoHandler

STORY_SKIP_NAME = str(STORY_SKIP)
STORY_SKIP_3_NAME = str(STORY_SKIP_3)


def make_handler(history):
    """Build an InfoHandler backed by the given click history."""
    handler = object.__new__(InfoHandler)
    handler.device = SimpleNamespace(click_record=deque(history, maxlen=15))
    return handler


class TestContinuousStorySkip:
    def test_empty_history(self):
        assert make_handler([])._continuous_story_skip() is False

    def test_single_story_skip(self):
        assert make_handler([STORY_SKIP_NAME])._continuous_story_skip() is False

    def test_two_story_skip(self):
        assert make_handler([STORY_SKIP_NAME, STORY_SKIP_NAME])._continuous_story_skip() is True

    def test_two_story_skip_at_end_of_longer_history(self):
        history = ['STORY_SKIP_3', 'POPUP_CONFIRM_STORY_SKIP', STORY_SKIP_NAME, STORY_SKIP_NAME]
        assert make_handler(history)._continuous_story_skip() is True

    def test_story_skip_separated_by_other_click(self):
        history = [STORY_SKIP_NAME, 'POPUP_CONFIRM_STORY_SKIP', STORY_SKIP_NAME]
        assert make_handler(history)._continuous_story_skip() is False

    def test_only_last_click_is_story_skip(self):
        assert make_handler([STORY_SKIP_3_NAME, STORY_SKIP_NAME])._continuous_story_skip() is False

    def test_only_previous_click_is_story_skip(self):
        assert make_handler([STORY_SKIP_NAME, STORY_SKIP_3_NAME])._continuous_story_skip() is False

    def test_story_skip_3_is_not_story_skip(self):
        assert make_handler([STORY_SKIP_3_NAME, STORY_SKIP_3_NAME])._continuous_story_skip() is False

    def test_renamed_popup_confirm_is_not_story_skip(self):
        history = ['POPUP_CONFIRM_STORY_SKIP', 'POPUP_CONFIRM_STORY_SKIP']
        assert make_handler(history)._continuous_story_skip() is False

    def test_plain_list_click_record(self):
        handler = object.__new__(InfoHandler)
        handler.device = SimpleNamespace(click_record=[STORY_SKIP_NAME, STORY_SKIP_NAME])
        assert handler._continuous_story_skip() is True

    def test_deque_drops_older_clicks(self):
        """Only the two newest clicks matter, even after the deque overflows."""
        history = ['OLDER_CLICK'] * 20 + [STORY_SKIP_NAME, STORY_SKIP_NAME]
        assert make_handler(history)._continuous_story_skip() is True
