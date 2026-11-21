from collections import deque
from types import SimpleNamespace

import pytest

import module.island_handler.dock as dock_module
from module.island_handler.dock import IslandDock, dock_character_matches
from module.island_handler.dock_scanner import Character


class FakeButton:
    def __init__(self, name):
        self.name = name
        self.area = (name, name, name, name)

    def __repr__(self):
        return 'FakeButton({!r})'.format(self.name)


class FakeDetect:
    def load_color(self, image):
        self.image = image


def character(identity, *, status='free', emotion=100, emotion_limit=110, grade='B', page='p'):
    return Character(
        identity=identity,
        emotion=emotion,
        emotion_limit=emotion_limit,
        grade=grade,
        status=status,
        button=FakeButton('{}:{}'.format(page, identity)),
    )


def card_anchor(index):
    x, y = index % 6 * 140, 11 + index // 6 * 180
    return SimpleNamespace(area=(x, y, x + 18, y + 18))


def make_main(pages, selected=(), grid_size=None, grid_origins=None):
    main = object.__new__(IslandDock)
    main._pages = pages
    main._page_index = 0
    main._next_calls = 0
    main._prev_calls = 0
    main._sort_calls = []
    main._clicks = []
    main._selected_buttons = set(selected)
    main.device = SimpleNamespace(image=object(), click_record_remove=lambda name: None)

    def scan_page(disabled=()):
        characters = list(main._pages[min(main._page_index, len(main._pages) - 1)])
        count = len(characters) if grid_size is None else grid_size
        origin = (56, 139) if grid_origins is None else grid_origins[main._page_index]
        main.dock_grid = SimpleNamespace(buttons=[None] * count, origin=origin,
                                         grid_shape=(6, (count + 5) // 6))
        return characters

    def sort_method(enable=True, wait_loading=True):
        main._sort_calls.append(enable)

    def next_page(wait_loading=True):
        main._next_calls += 1
        main._terminal_transition = main._page_index >= len(main._pages) - 1
        main._page_index = min(main._page_index + 1, len(main._pages) - 1)

    def prev_page(wait_loading=True):
        main._prev_calls += 1
        main._terminal_transition = main._page_index == 0
        main._page_index = max(main._page_index - 1, 0)

    def appear(button, offset=0):
        return getattr(main, '_terminal_transition', False)

    main.island_dock_scan_page = scan_page
    main.island_dock_has_third_row = lambda: False
    main.island_dock_sort_method_dsc_set = sort_method
    main.next_dock_page = next_page
    main.prev_dock_page = prev_page
    main.appear = appear
    main.loop = lambda skip_first=True, timeout=None: range(len(pages) + 3)
    main.is_button_selected = lambda button, color=None: button in main._selected_buttons
    main.island_dock_select_one = lambda button: main._clicks.append(button) or True
    return main


def make_scanning_main(monkeypatch, frames, anchor_counts=None, grid_origins=None):
    main = object.__new__(IslandDock)
    images = [object() for _ in frames]
    screenshots = iter(images[1:])
    main.device = SimpleNamespace(image=images[0], click_record_remove=lambda name: None)
    main.device.screenshot = lambda: setattr(main.device, 'image', next(screenshots))
    if grid_origins is None:
        grid_origins = [(56, 139)] * len(frames)

    def get_grid():
        index = images.index(main.device.image)
        rows = (len(frames[index]) + 5) // 6
        return SimpleNamespace(buttons=[None] * (6 * rows), origin=grid_origins[index],
                               delta=(140, 180), grid_shape=(6, rows))

    main.get_dock_grid = get_grid
    main.dock_grid = get_grid()
    if anchor_counts is None:
        anchor_counts = [len(frame) for frame in frames]

    def loop(skip_first=True, timeout=None):
        for index in range(len(frames)):
            if index or not skip_first:
                main.device.screenshot()
            yield main.device.image

    def anchors():
        frame_index = images.index(main.device.image)
        y_offset = grid_origins[frame_index][1] - 139
        return [SimpleNamespace(area=(anchor.area[0], anchor.area[1] + y_offset,
                                      anchor.area[2], anchor.area[3] + y_offset))
                for anchor in (card_anchor(index) for index in range(anchor_counts[frame_index]))]

    main._get_dock_anchors = anchors
    main.loop = loop
    main.island_dock_has_third_row = lambda: False
    main.next_dock_page = lambda: pytest.fail('Swiped while confirming empty cards')
    main.prev_dock_page = lambda: pytest.fail('Swiped while confirming empty cards')
    scanned = []

    class Scanner:
        def __init__(self, grid, **kwargs):
            self.grid = grid

        def disable(self, *fields):
            main._disabled = fields

        def scan(self, image):
            index = images.index(image)
            frame = frames[index]
            scanned.append(image)
            if self.grid.origin != grid_origins[index]:
                return [character('unknown') for _ in frame]
            return list(frame)

    monkeypatch.setattr(dock_module, 'CharacterScanner', Scanner)
    return main, scanned, images


def install_search_stub(monkeypatch, main, specs):
    calls = []

    def search(handle_page, descending=True, timeout=40, disabled=(), reverse=False):
        spec = specs[len(calls)]
        calls.append(dict(descending=descending, reverse=reverse,
                          timeout=timeout, disabled=tuple(disabled)))
        for page in spec['pages']:
            result = handle_page(page)
            if result is not None:
                return result, True
        return None, spec.get('completed', True)

    monkeypatch.setattr(main, 'island_dock_search', search)
    return calls


def test_dock_character_matches_supports_exact_list_set_and_filters():
    candidate = character('Alice', emotion=80, emotion_limit=110, grade='B')

    assert dock_character_matches(candidate, identity='Alice', emotion=(70, 90),
                                  emotion_limit=(100, 120), grade='B', status='free')
    assert dock_character_matches(candidate, identity=['Alice', 'Bob'], grade={'A', 'B'})
    assert dock_character_matches(candidate, identity={'Alice'}, status='free')
    assert not dock_character_matches(candidate, identity='Alice', emotion=(81, 90))
    assert not dock_character_matches(candidate, identity='Alice', status='occupied')
    workerjuu = character('Workerjuu', emotion=999)
    assert not dock_character_matches(workerjuu, identity='any')
    assert dock_character_matches(workerjuu, identity='Workerjuu')


def test_emotion_only_search_does_not_require_identity_or_grade(monkeypatch):
    candidate = character(None, emotion=100, grade=None)
    main = make_main([[candidate]])
    calls = install_search_stub(monkeypatch, main, [dict(pages=[[candidate]])])

    selected = main.island_dock_select_character(
        lambda candidate: dock_character_matches(candidate, emotion=(80, 150)),
        descending=False, disabled=('identity', 'emotion_limit', 'grade'))
    assert selected is candidate
    assert selected.emotion == 100
    assert main._clicks == [candidate.button]
    assert calls[0]['descending'] is False
    assert set(calls[0]['disabled']) == {'identity', 'grade', 'emotion_limit'}
    assert dock_character_matches(character('unknown', grade=None), emotion=(80, 150))


def test_predicate_can_require_recognized_identity(monkeypatch):
    unknown = character(None)
    main = make_main([[unknown]])
    calls = install_search_stub(monkeypatch, main, [dict(pages=[[unknown]], completed=False)])

    assert main.island_dock_select_character(
        lambda candidate: dock_character_matches(candidate, identity='Alice')) is None
    assert 'identity' not in calls[0]['disabled']


def test_predicate_can_filter_grade(monkeypatch):
    lower = character(None, grade='C')
    higher = character(None, grade='A')
    main = make_main([[lower, higher]])
    calls = install_search_stub(monkeypatch, main, [dict(pages=[[lower, higher]])])

    assert main.island_dock_select_character(
        lambda candidate: dock_character_matches(candidate, grade='A')) is higher
    assert main._clicks == [higher.button]
    assert all('grade' not in call['disabled'] for call in calls)


def test_scan_page_without_identity_does_not_retry_name_recognition(monkeypatch):
    candidate = character(None, grade=None)
    main, scanned, images = make_scanning_main(monkeypatch, [[candidate]])

    assert main.island_dock_scan_page(disabled=('identity', 'grade')) == [candidate]
    assert len(scanned) == 1
    assert main._disabled == ('identity', 'grade')


@pytest.mark.parametrize(('last', 'disabled', 'scan_count'), [
    (character('unknown', emotion=0, emotion_limit=0), (), 3),
    (character('unknown', emotion=0, emotion_limit=150), (), 3),
    (character('unknown', emotion=100, emotion_limit=0), (), 3),
    (character('unknown', emotion=None, emotion_limit=None), ('emotion', 'emotion_limit'), 3),
    (character(None, emotion=0, emotion_limit=0), (), 3),
    (character(None, emotion=None, emotion_limit=None), ('identity', 'emotion', 'emotion_limit'), 1),
    (character('Bob', emotion=0, emotion_limit=0), (), 1),
])
def test_scan_page_keeps_anchored_cards_regardless_of_ocr(monkeypatch, last, disabled, scan_count):
    cards = [character('Alice'), last]
    main, scanned, images = make_scanning_main(monkeypatch, [cards] * scan_count)

    assert main.island_dock_scan_page(disabled=disabled) == cards
    assert len(scanned) == scan_count


@pytest.mark.parametrize('disabled', [(), ('identity', 'grade'), ('identity', 'emotion_limit', 'grade'),
                                      ('identity', 'emotion', 'emotion_limit', 'grade')])
def test_scan_page_uses_anchor_count_with_any_scanner_fields(monkeypatch, disabled):
    cards = [character('Alice'), character('unknown', emotion=80, emotion_limit=100)]
    main, scanned, images = make_scanning_main(monkeypatch, [cards], [1])

    assert main.island_dock_scan_page(disabled=disabled) == cards[:1]
    assert scanned == images


@pytest.mark.parametrize('missing', [1, 7])
def test_missing_interior_anchor_keeps_later_cards(monkeypatch, missing):
    cards = [character('Card{}'.format(index)) for index in range(11)]
    cards.append(character('unknown', emotion=0, emotion_limit=0))
    main, scanned, images = make_scanning_main(monkeypatch, [cards])
    main._get_dock_anchors = lambda: [card_anchor(index) for index in reversed(range(11)) if index != missing]

    assert main.island_dock_scan_page() == cards[:11]
    assert scanned == images


def test_scan_page_retries_an_unreadable_character_with_fresh_grid_coordinates(monkeypatch):
    frames = [[character('Alice'), character('unknown', emotion=0, emotion_limit=0)],
              [character('Alice', page='settled'), character('Bob', page='settled')]]
    main, scanned, images = make_scanning_main(
        monkeypatch, frames, grid_origins=[(56, 139), (56, 145)])

    assert main.island_dock_scan_page() == frames[-1]
    assert scanned == images
    assert main.dock_grid.origin == (56, 145)


def test_no_anchors_return_an_incomplete_page(monkeypatch):
    cards = [character('unknown', emotion=0, emotion_limit=0)] * 6
    main, scanned, images = make_scanning_main(monkeypatch, [cards], [0])

    assert main.island_dock_scan_page() == []
    assert scanned == []
    assert main.device.image is images[-1]


@pytest.mark.parametrize('reverse', [False, True])
def test_search_reads_a_short_page_without_swiping(monkeypatch, reverse):
    frames = [[character('Alice'), character('unknown', emotion=0, emotion_limit=0)]]
    main, scanned, images = make_scanning_main(monkeypatch, frames, [1])
    main.island_dock_sort_method_dsc_set = lambda **kwargs: None
    seen = []

    result, completed = main.island_dock_search(lambda page: seen.extend(page), reverse=reverse)

    assert result is None
    assert completed is True
    assert seen == [frames[-1][0]]
    assert scanned == images


def test_scan_page_keeps_an_unreadable_detected_card_on_timeout(monkeypatch):
    frames = [[character('Alice'), character('unknown', emotion=0, emotion_limit=0)]]
    main, scanned, images = make_scanning_main(monkeypatch, frames)

    assert main.island_dock_scan_page() == frames[0]
    assert scanned == images


def test_scan_without_identity_can_reach_a_reliable_end(monkeypatch):
    main = make_main([[character(None, grade=None)]])
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())

    result, completed = main.island_dock_search(lambda page: None, disabled=('identity', 'grade'))

    assert result is None
    assert completed is True


@pytest.mark.parametrize(('identity', 'emotion', 'emotion_limit'), [
    ('unknown', 0, 0),
    ('unknown', 0, 150),
    ('unknown', 100, 0),
    ('unknown', 80, 100),
    ('unknown', 0, None),
    (None, 0, 0),
    ('', 0, 0),
])
def test_unknown_cards_keep_search_incomplete(monkeypatch, identity, emotion, emotion_limit):
    candidate = character(identity, emotion=emotion, emotion_limit=emotion_limit)
    main = make_main([[candidate]])
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())
    seen = []

    result, completed = main.island_dock_search(lambda page: seen.extend(page))

    assert result is None
    assert completed is False
    assert candidate in seen


def test_known_identity_with_zero_emotion_is_not_discarded():
    candidate = character('Alice', emotion=0, emotion_limit=0)
    main = make_main([[candidate]])

    result, completed = main.island_dock_search(lambda page: page[0])

    assert result is candidate
    assert completed is True


def test_unreadable_page_remains_incomplete():
    main = make_main([[]])

    result, completed = main.island_dock_search(lambda page: pytest.fail('Unreadable page was handled'))

    assert result is None
    assert completed is False
    assert main._next_calls == 0


def test_selected_identity_is_excluded_from_single_search(monkeypatch):
    selected = character('Alice', page='selected')
    replacement = character('Bob', page='replacement')
    main = make_main([[selected, replacement]], selected={selected.button})
    install_search_stub(monkeypatch, main, [dict(pages=[[selected, replacement]])])

    assert main.island_dock_select_character(
        lambda candidate: dock_character_matches(candidate, identity='any')) is replacement
    assert main._clicks == [replacement.button]


def test_occupied_character_is_not_selected_even_if_predicate_accepts_it(monkeypatch):
    busy = character('Alice', status='occupied')
    main = make_main([[busy]])
    install_search_stub(monkeypatch, main, [dict(pages=[[busy]])])

    assert main.island_dock_select_character(lambda candidate: True) is None
    assert main._clicks == []


def test_selection_skips_occupied_alternative_even_if_predicate_accepts_it(monkeypatch):
    busy = character('Alice', status='occupied')
    free = character('Bob')
    main = make_main([[busy, free]])
    install_search_stub(monkeypatch, main, [dict(pages=[[busy, free]])])

    assert main.island_dock_select_character(lambda candidate: True) is free
    assert main._clicks == [free.button]


def test_search_stops_before_navigation_after_handler_decision(monkeypatch):
    first = character('First', page='first')
    second = character('Second', page='second')
    main = make_main([[first], [second]], grid_size=2)
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())

    result, completed = main.island_dock_search(
        lambda page: page[0] if page[0].identity == 'First' else None,
        descending=False,
    )

    assert result is first
    assert completed
    assert main._next_calls == 0
    assert main._sort_calls == [False]
    assert main._prev_calls == 0


def test_reverse_search_reads_current_page_backwards_before_moving_up(monkeypatch):
    highest = character('Highest', page='bottom')
    main = make_main([[character('Lower')], [character('High'), highest]],
                     grid_size=12, grid_origins=[(56, 139), (56, 206)])
    main._page_index = 1
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())

    assert main.island_dock_search(lambda page: page[0], descending=False, reverse=True) == (highest, True)
    assert main._sort_calls == [False]
    assert main._next_calls == main._prev_calls == 0


@pytest.mark.parametrize('unknown', [False, True])
def test_reverse_search_scans_to_confirmed_top_even_with_a_third_row(monkeypatch, unknown):
    top = [character('unknown' if unknown else 'Low'), character('Higher')]
    bottom = [character('High'), character('Highest')]
    main = make_main([top, bottom], grid_size=12, grid_origins=[(56, 139), (56, 206)])
    main._page_index = 1
    main.island_dock_has_third_row = lambda: True
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())
    seen = []

    assert main.island_dock_search(
        lambda page: seen.append(page), descending=False, reverse=True) == (None, not unknown)
    assert seen == [list(reversed(bottom))] + [list(reversed(top))] * 2
    assert main._prev_calls == 2
    assert main._next_calls == 0


def test_reverse_search_selects_a_fresh_match_on_an_upper_page(monkeypatch):
    chosen = character('HighestEligible', page='upper')
    main = make_main([[character('LowerEligible'), chosen], [character('Other')]],
                     grid_size=12, grid_origins=[(56, 139), (56, 206)])
    main._page_index = 1
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())

    def select_page(page):
        for candidate in page:
            if candidate.identity.endswith('Eligible'):
                main.island_dock_select_one(candidate.button)
                return candidate
        return None

    assert main.island_dock_search(select_page, descending=False, reverse=True) == (chosen, True)
    assert main._clicks == [chosen.button]
    assert main._prev_calls == 1
    assert main._next_calls == 0


@pytest.mark.parametrize('reverse', [False, True])
def test_search_settles_boundary_bounce_before_checking_unchanged(monkeypatch, reverse):
    main = object.__new__(IslandDock)
    endpoint = (56, 139) if reverse else (56, 206)
    bouncing = (56, 143) if reverse else (56, 200)
    origins = {'initial': endpoint, 'bouncing': bouncing, 'settled': endpoint}
    cards = [character('Card{}'.format(index)) for index in range(12)]
    events = []
    clock = SimpleNamespace(elapsed=0)

    def screenshot():
        clock.elapsed += 0.1
        main.device.image = 'bouncing' if clock.elapsed < 0.6 else 'settled'
        events.append(('screenshot', main.device.image))

    def loop(skip_first=True, timeout=None):
        started = clock.elapsed
        for _ in range(20):
            if timeout is not None and clock.elapsed - started >= timeout:
                return
            if skip_first:
                skip_first = False
            else:
                main.device.screenshot()
            yield None

    main.device = SimpleNamespace(
        image='initial', click_record_remove=lambda name: None,
        screenshot=screenshot)
    main.get_dock_grid = lambda: SimpleNamespace(
        buttons=[card.button for card in cards], origin=origins[main.device.image], grid_shape=(6, 2))

    def scan(disabled=()):
        events.append(('scan', main.dock_grid.origin))
        return list(cards)

    def drag(*args, **kwargs):
        assert 'drag' not in events, 'Dragged again before the boundary finished settling'
        events.append('drag')
        main.device.image = 'bouncing'

    def unchanged(*args, **kwargs):
        events.append(('unchanged', main.device.image))
        return main.device.image == 'settled'

    main.island_dock_scan_page = scan
    main.island_dock_sort_method_dsc_set = lambda **kwargs: None
    main.island_dock_has_third_row = lambda: True
    main.device.drag = drag
    main.appear = unchanged
    main.loop = loop
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())

    assert main.island_dock_search(lambda page: None, reverse=reverse) == (None, True)
    assert [event for event in events if isinstance(event, tuple) and event[0] == 'unchanged'] == [
        ('unchanged', 'settled'),
    ]
    settled = events.index(('screenshot', 'settled'))
    assert events[settled + 1] == ('unchanged', 'settled')
    assert events[0] == events[-1] == ('scan', endpoint)


@pytest.mark.parametrize(('pages', 'completed', 'swipes'), [
    ([[character('Last')]], True, 0),
    ([[character('unknown')]], False, 0),
    ([[character('First'), character('Second')], [character('Last')]], True, 1),
    ([[character('unknown'), character('Second')], [character('Last')]], False, 1),
])
def test_search_processes_trimmed_bottom_page_without_another_swipe(monkeypatch, pages, completed, swipes):
    main = make_main(pages, grid_size=2)
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())
    seen = []

    result, finished = main.island_dock_search(lambda page: seen.extend(page))

    assert result is None
    assert finished is completed
    assert seen == [candidate for page in pages for candidate in page]
    assert main._next_calls == swipes


@pytest.mark.parametrize('grid_size', [None, 12])
def test_search_cannot_finish_with_one_row_away_from_end_positions(monkeypatch, grid_size):
    first = [character('First{}'.format(index)) for index in range(12)]
    last = [character('Last{}'.format(index)) for index in range(6)]
    main = make_main([first, last], grid_size=grid_size, grid_origins=[(56, 139), (56, 254)])
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())

    result, completed = main.island_dock_search(lambda page: None)

    assert result is None
    assert completed is False
    assert main._next_calls > 2


def test_search_checks_rows_after_two_unchanged_swipes(monkeypatch):
    full = [character('Full{}'.format(index)) for index in range(12)]
    partial = [character('Partial{}'.format(index)) for index in range(6)]
    main = make_main([full, full, partial], grid_origins=[(56, 139), (56, 250), (56, 254)])
    main.appear = lambda *args, **kwargs: True
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())
    seen = []

    result, completed = main.island_dock_search(lambda page: seen.append(len(page)))

    assert result is None
    assert completed is False
    assert seen[:3] == [12, 12, 6]
    assert main._next_calls > 2


def test_search_keeps_scrolling_past_one_row_until_exact_bottom(monkeypatch):
    full = [character('Full{}'.format(index)) for index in range(12)]
    partial = [character('Partial{}'.format(index)) for index in range(6)]
    bottom = [character('Bottom{}'.format(index)) for index in range(7)]
    main = make_main([full, partial, bottom], grid_size=12,
                     grid_origins=[(56, 139), (56, 254), (56, 206)])
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())
    scans = []

    result, completed = main.island_dock_search(lambda page: scans.append(page))

    assert result is None
    assert completed is True
    assert scans == [full, partial, bottom]
    assert main._next_calls == 2


@pytest.mark.parametrize('origin', [(56, 205), (56, 207), (55, 206), (57, 206)])
@pytest.mark.parametrize('count', [7, 12])
def test_search_cannot_finish_at_a_nearby_unaligned_grid(monkeypatch, origin, count):
    page = [character('Card{}'.format(index)) for index in range(count)]
    main = make_main([page], grid_size=12, grid_origins=[origin])
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())

    assert main.island_dock_search(lambda page: None) == (None, False)
    assert main._next_calls > 2


@pytest.mark.parametrize('count, swipes', [(7, 0), (11, 0), (12, 1)])
def test_search_only_drags_at_exact_bottom_when_all_slots_are_filled(monkeypatch, count, swipes):
    page = [character('Card{}'.format(index)) for index in range(count)]
    main = make_main([page], grid_size=12, grid_origins=[(56, 206)])
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())
    scans = []

    assert main.island_dock_search(lambda page: scans.append(page)) == (None, True)
    assert scans == [page] * (swipes + 1)
    assert main._next_calls == swipes


def test_search_continues_past_bottom_aligned_middle_pages(monkeypatch):
    first = [character('First{}'.format(index)) for index in range(12)]
    middle = [character('Middle{}'.format(index)) for index in range(12)]
    bottom = [character('Last{}'.format(index)) for index in range(12)]
    main = make_main([first, middle, bottom], grid_size=12,
                     grid_origins=[(56, 139), (56, 206), (56, 206)])
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())
    scans = []

    assert main.island_dock_search(lambda page: scans.append(page)) == (None, True)
    assert scans == [first, middle, bottom, bottom]
    assert main._next_calls == 3


@pytest.mark.parametrize('reverse,swipes', [(False, 2), (True, 1)])
def test_search_confirms_full_short_dock_in_requested_direction(monkeypatch, reverse, swipes):
    page = [character('Card{}'.format(index)) for index in range(12)]
    main = make_main([page])
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())
    scans = []

    assert main.island_dock_search(lambda page: scans.append(page), reverse=reverse) == (None, True)
    assert len(scans) == swipes + 1
    assert main._next_calls == (0 if reverse else swipes)
    assert main._prev_calls == (swipes if reverse else 0)


def test_search_uses_anchor_count_with_disabled_fields(monkeypatch):
    cards = [character(None, emotion_limit=None, grade=None) for _ in range(11)]
    cards.append(character(None, emotion=0, emotion_limit=None, grade=None))
    main, scanned, images = make_scanning_main(monkeypatch, [cards], [11])
    main.island_dock_sort_method_dsc_set = lambda **kwargs: None

    assert main.island_dock_search(lambda page: None, disabled=('identity', 'emotion_limit', 'grade')) == (None, True)
    assert scanned == images


@pytest.mark.parametrize('count', [7, 12])
def test_third_row_rules_out_a_short_dock_despite_failed_drags(monkeypatch, count):
    page = [character('Card{}'.format(index)) for index in range(count)]
    main = make_main([page], grid_size=12)
    main.island_dock_has_third_row = lambda: True
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())

    assert main.island_dock_search(lambda page: None) == (None, False)
    assert main._next_calls > 2


def test_search_remembers_a_third_row_if_later_anchor_scans_miss_it(monkeypatch):
    page = [character('Card{}'.format(index)) for index in range(12)]
    main = make_main([page])
    detections = iter([True, False, False, False])
    main.island_dock_has_third_row = lambda: next(detections)
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())

    assert main.island_dock_search(lambda page: None) == (None, False)
    assert main._next_calls > 2


def test_search_continues_from_a_trimmed_middle_page_to_the_aligned_bottom(monkeypatch):
    full = [character('First{}'.format(index)) for index in range(12)]
    middle = [character('Middle{}'.format(index)) for index in range(7)]
    bottom = [character('Last{}'.format(index)) for index in range(7)]
    main = make_main([full, middle, bottom], grid_size=12,
                     grid_origins=[(56, 139), (56, 250), (56, 206)])
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())
    scans = []

    assert main.island_dock_search(lambda page: scans.append(page)) == (None, True)
    assert scans == [full, middle, bottom]
    assert main._next_calls == 2


@pytest.mark.parametrize('count', [5, 6])
def test_search_can_finish_in_a_dock_that_only_has_one_row(monkeypatch, count):
    page = [character('Only{}'.format(index)) for index in range(count)]
    main = make_main([page], grid_size=6)
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())

    assert main.island_dock_search(lambda page: None) == (None, True)


def test_search_can_select_a_current_one_row_match_after_seeing_two(monkeypatch):
    full = [character('Full{}'.format(index)) for index in range(12)]
    candidate = character('Alice', page='current')
    main = make_main([full, [candidate]], grid_size=12)
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())

    assert main.island_dock_select_character(lambda candidate: candidate.identity == 'Alice') is candidate
    assert main._clicks == [candidate.button]
    assert main._next_calls == 1


def test_search_refreshes_pages_and_ends_with_bounded_navigation(monkeypatch):
    first = character('First', page='first')
    second = character('Second', page='second')
    main = make_main([[first], [second]])
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())
    seen = []

    result, completed = main.island_dock_search(
        lambda page: seen.append(page[0]) or None,
        descending=False,
        timeout=1,
    )

    assert result is None
    assert completed
    assert [item.identity for item in seen] == ['First', 'Second', 'Second', 'Second']
    assert seen[0].button is not seen[1].button
    assert main._next_calls == 3


def test_incomplete_search_returns_no_character_without_extra_pass(monkeypatch):
    unknown = character('unknown', page='partial')
    fallback = character('Other', page='fallback')
    main = make_main([[unknown]])
    calls = install_search_stub(monkeypatch, main, [
        dict(pages=[[unknown]], completed=False),
        dict(pages=[[fallback]]),
    ])

    assert main.island_dock_select_character(lambda candidate: candidate.identity == 'Alice') is None
    assert len(calls) == 1


def test_predicate_can_skip_current_page_for_a_later_match(monkeypatch):
    other = character('Other', page='top')
    preferred = character('Alice', page='lower')
    main = make_main([[other], [preferred]])
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())

    assert main.island_dock_select_character(
        lambda candidate: candidate.identity in {'Alice', 'Bob'}) is preferred
    assert main._clicks == [preferred.button]
    assert main._sort_calls == [True]
    assert main._prev_calls == 0
    assert main._next_calls == 1


def test_reverse_search_after_a_completed_pass_uses_new_coordinates(monkeypatch):
    old_other = character('Other', page='before-sort')
    new_other = character('Other', page='after-sort')
    busy = character('Alice', status='occupied', page='lower')
    main = make_main([[old_other], [busy]])
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())
    original_sort = main.island_dock_sort_method_dsc_set

    def sort(enable=True, **kwargs):
        original_sort(enable=enable, **kwargs)
        if len(main._sort_calls) == 2:
            main._pages = [[new_other], [busy]]

    main.island_dock_sort_method_dsc_set = sort

    assert main.island_dock_select_character(
        lambda candidate: candidate.identity == 'Alice', descending=False) is None

    def select_page(page):
        for candidate in page:
            if candidate.identity == 'Other':
                main.island_dock_select_one(candidate.button)
                return candidate
        return None

    assert main.island_dock_search(select_page, descending=True, reverse=True) == (new_other, True)
    assert main._sort_calls == [False, True]
    assert main._prev_calls == 1
    assert main._clicks == [new_other.button]
    assert old_other.button not in main._clicks


@pytest.mark.parametrize('reverse', [False, True])
def test_search_clears_only_previous_dock_swipe_history(monkeypatch, reverse):
    from module.device.device import Device

    pages = [[character(str(index))] for index in range(7)]
    main = make_main(pages, grid_size=12,
                     grid_origins=[(56, 139)] + [(56, 250)] * 5 + [(56, 206)])
    main._page_index = 6 if reverse else 0
    main.island_dock_has_third_row = lambda: True
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())
    main.device = object.__new__(Device)
    main.device.image = object()
    down = 'ISLAND_DOCK_NEXT_PAGE_SWIPE'
    up = 'ISLAND_DOCK_PREV_PAGE_SWIPE'
    main.device.click_record = deque([down] * 6 + [up] * 5 + ['OTHER_ACTION'], maxlen=15)
    swipe = up if reverse else down
    scroll = main.prev_dock_page if reverse else main.next_dock_page

    def scroll_page():
        main.device.click_record_add(swipe)
        main.device.click_record_check()
        scroll()

    if reverse:
        main.prev_dock_page = scroll_page
    else:
        main.next_dock_page = scroll_page
    target = pages[0 if reverse else -1][0]
    assert main.island_dock_search(
        lambda page: page[0] if page[0].identity == target.identity else None,
        descending=not reverse, reverse=reverse) == (target, True)
    assert list(main.device.click_record) == ['OTHER_ACTION'] + [swipe] * 6


def test_select_character_clicks_match_before_any_page_navigation(monkeypatch):
    candidate = character('Alice', page='current')
    main = make_main([[candidate]])
    install_search_stub(monkeypatch, main, [dict(pages=[[candidate]])])

    assert main.island_dock_select_character(lambda candidate: candidate.identity == 'Alice')
    assert main._clicks == [candidate.button]
    assert main._next_calls == 0


def test_failed_click_returns_none_without_trying_another_character(monkeypatch):
    preferred = character('Alice')
    other = character('Other')
    main = make_main([[preferred, other]])
    calls = install_search_stub(monkeypatch, main, [
        dict(pages=[[preferred, other]]), dict(pages=[[other]]),
    ])
    main.island_dock_select_one = lambda button: main._clicks.append(button) or False

    assert main.island_dock_select_character(lambda candidate: True) is None
    assert main._clicks == [preferred.button]
    assert len(calls) == 1


def test_workerjuu_visible_first_uses_no_navigation(monkeypatch):
    workerjuu = character('Workerjuu', page='first')
    main = make_main([[workerjuu]])
    calls = install_search_stub(monkeypatch, main, [dict(pages=[[workerjuu]])])

    assert main.island_dock_select_workerjuu() is workerjuu
    assert len(calls) == 1
    assert calls[0]['descending'] is False
    assert main._prev_calls == 0


def test_workerjuu_after_failed_ascending_search_is_selected_locally_in_descending_order(monkeypatch):
    low_emotion = character('Other', emotion=99, page='top')
    mature = character('Mature', emotion_limit=150, page='bottom')
    workerjuu = character('Workerjuu', page='sorted-bottom')
    main = make_main([[low_emotion], [mature]])
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())
    original_sort = main.island_dock_sort_method_dsc_set

    def sort(enable=True, **kwargs):
        original_sort(enable=enable, **kwargs)
        if enable:
            main._pages = [[mature], [workerjuu]]

    main.island_dock_sort_method_dsc_set = sort
    assert main.island_dock_select_character(
        lambda candidate: dock_character_matches(candidate, emotion=(100, 150), emotion_limit=(100, 149)),
        descending=False) is None
    down_swipes = main._next_calls

    assert main.island_dock_select_workerjuu(descending=True) is workerjuu
    assert main._sort_calls == [False, True]
    assert main._prev_calls == 0
    assert main._next_calls == down_swipes
    assert main._clicks == [workerjuu.button]


def test_missing_workerjuu_does_not_scroll_or_retry():
    main = make_main([[character('Other')], [character('Workerjuu')]])

    assert main.island_dock_select_workerjuu() is None
    assert main._sort_calls == [False]
    assert main._prev_calls == 0
    assert main._next_calls == 0
    assert main._clicks == []


def test_workerjuu_can_keep_current_sort_without_navigation():
    workerjuu = character('Workerjuu', page='current')
    main = make_main([[workerjuu]])

    assert main.island_dock_select_workerjuu(descending=None) is workerjuu
    assert main._sort_calls == []
    assert main._next_calls == main._prev_calls == 0
    assert main._clicks == [workerjuu.button]
