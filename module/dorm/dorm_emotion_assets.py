"""
Buttons, grids and pixel thresholds of the dorm ship management panel.

Everything here is a frozen constant measured pixel by pixel on 1280x720
screenshots of the CN client, see docs for the raw measurement data. Kept in a
separate module so that the reader in dorm_emotion.py stays below the 500 lines
limit of the Alas style guide.

Layout
    Six slots in a row, 170 pixels apart. Numbers in every slot are right
    aligned to 288 + 170 * i no matter how many digits they have, so a fixed
    grid reads them all without ship name recognition.

Recover speed is the ground truth of floor and oath
    The value shown in game matches DIC_RECOVER exactly, floor 1 is 40, floor 2
    is 50 and oath adds 10, so the selected tab gives the floor and the speed
    gives the oath status. Users don't need to register any ship by hand.
"""
from module.base.button import Button
from module.ocr.ocr import Digit
from module.ui.assets import DORM_INFO

SLOT_COUNT = 6
MOOD_MAX = 150
# Recover speed shown in game, floor 1, floor 2, and oathed floor 2
RECOVER_SPEEDS = (40, 50, 60)
# Median of slot background, occupied is 43~61 and empty is 221
SLOT_BACKGROUND_THRESHOLD = 150
SLOT_BACKGROUND_OCCUPIED = (20, 70)
SLOT_BACKGROUND_EMPTY = (190, 255)

# Panel entrance, the "training / rest 4/4" pill at the bottom-left of dorm main page.
# The whole pill can't be used as a template because the slot counter inside changes.
DORM_SHIP_PANEL_ENTER = Button(
    area=(62, 660, 114, 694), color=(220, 220, 220), button=(62, 660, 114, 694))
# Panel tab, training is dormitory floor 1
DORM_SHIP_PANEL_TAB_TRAIN = Button(
    area=(180, 80, 302, 120), color=(120, 120, 120), button=(180, 80, 302, 120))
# Panel tab, rest is dormitory floor 2
DORM_SHIP_PANEL_TAB_REST = Button(
    area=(398, 80, 508, 120), color=(230, 230, 230), button=(398, 80, 508, 120))
# Close button at the top-right of the panel header, a white cross spanning
# (1119, 87) to (1145, 113). The furniture panel has a close button at the same
# x but 25 pixels lower, reusing DORM_MANAGE_CHECK misses and the panel stays
# opened, which makes every page unknown to Alas.
DORM_SHIP_PANEL_QUIT = Button(
    area=(1119, 87, 1146, 114), color=(249, 249, 249), button=(1119, 87, 1146, 114))

# The header behind the close button is dark grey, measured 98 on the panel and
# 204 on the main page, whose top right holds a row of light buttons. Used as a
# second opinion of dorm_panel_appear(), slot backgrounds alone can be fooled by
# a page that happens to have six grey areas where the slots sit.
DORM_SHIP_PANEL_HEADER = Button(
    area=(1119, 87, 1146, 114), color=(98, 98, 98), button=(1119, 87, 1146, 114))

# Confirm button of the dorm exp popup, the one that says the ships had a good
# rest and gained exp. Alas already ships a template of it, reuse that asset
# instead of cutting a new one. Measured on the client of the author, template
# matching scores 0.86 on the popup and 0.15 to 0.34 on every other page, so
# the 0.75 of Alas has a wide margin.
DORM_EXP_CONFIRM = DORM_INFO

# Mood area reaches 4px beyond the right edge, the oath card frame starts at x=803
# and its bright pixels would pollute a wider area.
DORM_SHIP_MOOD_GRIDS = [
    (288 + 170 * i - 34, 578, 288 + 170 * i + 4, 597) for i in range(SLOT_COUNT)]
# Speed area is narrower, the oath card frame rises from x=799 here, 4px lefter
DORM_SHIP_SPEED_GRIDS = [
    (288 + 170 * i - 48, 605, 288 + 170 * i - 11, 625) for i in range(SLOT_COUNT)]
# Slot background sample area
DORM_SHIP_SLOT_BACKGROUND = [
    (141 + 170 * i + 20, 520, 141 + 170 * i + 80, 560) for i in range(SLOT_COUNT)]

# Letters are neutral white grey, R equals G equals B, so both rows share one setting.
#
# The threshold is 192 instead of the 160 used at first. extract_letters() scales
# by 255 / threshold and then saturates, so a lower threshold *brightens* the
# strokes of an already bright letter instead of darkening them, and the model
# loses confidence on the narrow glyphs. Measured on the digits of the author,
# the 6 of "146" scores 0.10 at 160 and is dropped by the 0.5 confidence cut in
# AlOcr._gen_line_pred_chars, which reads 14. 176 is still 0.44, 192 reaches
# 0.998 while every other screenshot keeps its result.
OCR_LETTER_THRESHOLD = 192
OCR_DORM_SHIP_MOOD = Digit(
    DORM_SHIP_MOOD_GRIDS, letter=(255, 255, 255), threshold=OCR_LETTER_THRESHOLD,
    name='OCR_DORM_SHIP_MOOD')
OCR_DORM_SHIP_SPEED = Digit(
    DORM_SHIP_SPEED_GRIDS, letter=(255, 255, 255), threshold=OCR_LETTER_THRESHOLD,
    name='OCR_DORM_SHIP_SPEED')


def is_dorm_panel_opened(medians):
    """
    Whether the ship panel is opened, judged from slot backgrounds.

    With the panel opened, all six slot backgrounds fall into either the
    occupied or the empty range. Without it they are scattered, the main page
    scores 5 of 6 in measurement.

    No tolerance on purpose. A false "opened" sends the caller clicking the
    close button on an unrelated page and the game goes anywhere, which is far
    worse than missing a real panel, that only skips one reading and keeps the
    calculated value.

    Args:
        medians (list[int]): Median of every slot background, 0 to 255.

    Returns:
        bool:
    """
    return all(
        SLOT_BACKGROUND_OCCUPIED[0] <= m <= SLOT_BACKGROUND_OCCUPIED[1]
        or SLOT_BACKGROUND_EMPTY[0] <= m <= SLOT_BACKGROUND_EMPTY[1]
        for m in medians
    )
