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


def make_main(pages, selected=(), grid_size=None):
    main = object.__new__(IslandDock)
    main._pages = pages
    main._page_index = 0
    main._next_calls = 0
    main._sort_calls = []
    main._top_calls = 0
    main._clicks = []
    main._selected_buttons = set(selected)
    main.device = SimpleNamespace(image=object())

    def scan_page(disabled=()):
        characters = list(main._pages[min(main._page_index, len(main._pages) - 1)])
        count = len(characters) if grid_size is None else grid_size
        main.dock_grid = SimpleNamespace(buttons=[None] * count)
        return characters

    def sort_method(enable=True, wait_loading=True):
        main._sort_calls.append(enable)

    def ensure_top():
        main._top_calls += 1
        main._page_index = 0
        return True

    def next_page(wait_loading=True):
        main._next_calls += 1
        main._terminal_transition = main._page_index >= len(main._pages) - 1
        main._page_index = min(main._page_index + 1, len(main._pages) - 1)

    def appear(button, offset=0):
        return getattr(main, '_terminal_transition', False)

    main.island_dock_scan_page = scan_page
    main.island_dock_sort_method_dsc_set = sort_method
    main.ensure_dock_page_at_top = ensure_top
    main.next_dock_page = next_page
    main.appear = appear
    main.loop = lambda skip_first=True, timeout=None: range(len(pages) + 3)
    main.is_button_selected = lambda button, color=None: button in main._selected_buttons
    main.island_dock_select_one = lambda button: main._clicks.append(button) or True
    return main


def install_search_stub(monkeypatch, main, specs):
    calls = []

    def search(handle_page, descending=True, start_at_top=False, timeout=40, disabled=()):
        spec = specs[len(calls)]
        calls.append(dict(descending=descending, start_at_top=start_at_top,
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
        emotion=(80, 150), descending=False, disabled=('emotion_limit',))
    assert selected is candidate
    assert selected.emotion == 100
    assert main._clicks == [candidate.button]
    assert calls[0]['descending'] is False
    assert set(calls[0]['disabled']) == {'identity', 'grade', 'emotion_limit'}
    assert dock_character_matches(character('unknown', grade=None), emotion=(80, 150))


@pytest.mark.parametrize('filters', [
    {'identity': 'Alice'}, {'identity': 'any'}, {'blacklist': {'Alice'}},
])
def test_identity_constraints_still_require_recognition(monkeypatch, filters):
    unknown = character(None)
    main = make_main([[unknown]])
    calls = install_search_stub(monkeypatch, main, [dict(pages=[[unknown]], completed=False)])

    assert main.island_dock_select_character(**filters) is None
    assert 'identity' not in calls[0]['disabled']
    with pytest.raises(ValueError, match='requires identity recognition'):
        main.island_dock_select_character(disabled=('identity',), **filters)


@pytest.mark.parametrize('filters', [{'grade': 'A'}, {'prefer_grade': True}])
def test_grade_filter_and_ranking_enable_grade_recognition(monkeypatch, filters):
    lower = character(None, grade='C')
    higher = character(None, grade='A')
    main = make_main([[lower, higher]])
    calls = install_search_stub(monkeypatch, main, [dict(pages=[[lower, higher]])])

    assert main.island_dock_select_character(**filters) is higher
    assert main._clicks == [higher.button]
    assert all('grade' not in call['disabled'] for call in calls)


def test_scan_page_without_identity_does_not_retry_name_recognition(monkeypatch):
    candidate = character(None, grade=None)
    main = object.__new__(IslandDock)
    main.device = SimpleNamespace(image=object())
    main.dock_grid = SimpleNamespace(buttons=[candidate.button])
    main.loop = lambda **kwargs: range(3)
    scanned = []
    disabled = []

    class Scanner:
        def __init__(self, grid, **kwargs):
            pass

        def disable(self, *fields):
            disabled.extend(fields)

        def scan(self, image):
            scanned.append(image)
            return [candidate]

    monkeypatch.setattr(dock_module, 'CharacterScanner', Scanner)

    assert main.island_dock_scan_page(disabled=('identity', 'grade')) == [candidate]
    assert len(scanned) == 1
    assert disabled == ['identity', 'grade']


@pytest.mark.parametrize(('cards', 'disabled', 'expected', 'scan_count'), [
    ([character('Alice'), character('unknown', emotion=0, emotion_limit=0),
      character('unknown', emotion=0, emotion_limit=0)], (), ['Alice'], 1),
    ([character('Alice'), character('unknown', emotion=0, emotion_limit=150)],
     (), ['Alice', 'unknown'], 3),
    ([character('Alice'), character('unknown', emotion=100, emotion_limit=0)],
     (), ['Alice', 'unknown'], 3),
    ([character('Alice'), character('unknown', emotion=None, emotion_limit=None, grade=None)],
     ('emotion', 'emotion_limit', 'grade'), ['Alice', 'unknown'], 3),
    ([character('Alice'), character(None, emotion=0, emotion_limit=0)],
     (), ['Alice', None], 3),
    ([character('Alice'), character('unknown', emotion=0, emotion_limit=0), character('Bob')],
     (), ['Alice', 'unknown', 'Bob'], 3),
    ([character('unknown', emotion=0, emotion_limit=0), character('unknown', emotion=0, emotion_limit=0)],
     (), ['unknown'], 3),
    ([character('Alice'), character('Bob', emotion=0, emotion_limit=0)],
     (), ['Alice', 'Bob'], 1),
])
def test_scan_page_drops_only_confirmed_empty_tail_before_retry(monkeypatch, cards, disabled, expected, scan_count):
    main = object.__new__(IslandDock)
    main.device = SimpleNamespace(image=object())
    main.dock_grid = SimpleNamespace(buttons=[c.button for c in cards])
    main.loop = lambda **kwargs: range(3)
    scanned = []

    class Scanner:
        def __init__(self, grid, **kwargs):
            pass

        def disable(self, *fields):
            pass

        def scan(self, image):
            scanned.append(image)
            return list(cards)

    monkeypatch.setattr(dock_module, 'CharacterScanner', Scanner)

    result = main.island_dock_scan_page(disabled=disabled)

    assert [c.identity for c in result] == expected
    assert len(scanned) == scan_count


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


def test_blacklist_wins_over_explicit_identity_and_occupied_is_reported(monkeypatch):
    busy = character('Alice', status='occupied', page='busy')
    unknown = character('unknown', page='unknown')
    main = make_main([[busy, unknown]])
    unavailable = set()
    calls = install_search_stub(monkeypatch, main, [dict(pages=[[busy, unknown]])])

    assert main.island_dock_select_character(
        identity='Alice', blacklist={'Alice'}, unavailable=unavailable
    ) is None
    assert unavailable == set()
    assert calls == []

    unavailable.clear()
    assert main.island_dock_select_character(
        identity='Alice', unavailable=unavailable
    ) is None
    assert unavailable == {'Alice'}


def test_selected_identity_is_excluded_from_single_search(monkeypatch):
    selected = character('Alice', page='selected')
    replacement = character('Bob', page='replacement')
    main = make_main([[selected, replacement]], selected={selected.button})
    install_search_stub(monkeypatch, main, [dict(pages=[[selected, replacement]])])

    assert main.island_dock_select_character(identity='any') is replacement
    assert main._clicks == [replacement.button]


def test_occupied_character_is_reported_without_selection_or_scrolling(monkeypatch):
    busy = character('Alice', status='occupied')
    main = make_main([[busy]])
    unavailable = set()
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())

    assert main.island_dock_select_character(
        identity='Alice', status=None, unavailable=unavailable) is None
    assert unavailable == {'Alice'}
    assert main._next_calls == 0
    assert main._clicks == []


def test_selection_skips_occupied_alternative_even_without_status_filter(monkeypatch):
    busy = character('Alice', status='occupied')
    free = character('Bob')
    main = make_main([[busy, free]])
    unavailable = set()
    install_search_stub(monkeypatch, main, [dict(pages=[[busy, free]])])

    assert main.island_dock_select_character(
        identity={'Alice', 'Bob'}, status=None, unavailable=unavailable) is free
    assert unavailable == {'Alice'}
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
    assert main._top_calls == 0


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
    assert [item.identity for item in seen] == ['First', 'Second', 'Second']
    assert seen[0].button is not seen[1].button
    assert main._next_calls == 3


def test_timeout_or_incomplete_absence_does_not_trigger_outside_fallback(monkeypatch):
    unknown = character('unknown', page='partial')
    fallback = character('Other', page='fallback')
    main = make_main([[unknown]])
    calls = install_search_stub(monkeypatch, main, [
        dict(pages=[[unknown]], completed=False),
        dict(pages=[[fallback]]),
    ])

    assert main.island_dock_select_character(identity='Alice', fallback=True) is None
    assert len(calls) == 1


def test_occupied_required_name_allows_fallback_and_reacquires_current_button(monkeypatch):
    occupied = character('Alice', status='occupied', page='primary')
    unknown = character('unknown', page='partial')
    fallback = character('Other', page='fallback')
    main = make_main([[occupied, unknown]])
    unavailable = set()
    calls = install_search_stub(monkeypatch, main, [
        dict(pages=[[occupied, unknown]]),
        dict(pages=[[fallback]]),
    ])

    assert main.island_dock_select_character(
        identity='Alice', fallback=True, fallback_descending=False, unavailable=unavailable
    ) is fallback

    assert main._clicks == [fallback.button]
    assert unavailable == {'Alice'}
    assert [call['descending'] for call in calls] == [True, False]
    assert [call['start_at_top'] for call in calls] == [False, True]
    assert occupied.button not in main._clicks


def test_preferred_identity_beats_fallback_pass(monkeypatch):
    preferred = character('Alice', page='preferred')
    fallback = character('Other', page='fallback')
    main = make_main([[preferred]])
    calls = install_search_stub(monkeypatch, main, [
        dict(pages=[[preferred]]),
        dict(pages=[[fallback]]),
    ])

    assert main.island_dock_select_character(identity='Alice', fallback=True) is preferred
    assert main._clicks == [preferred.button]
    assert len(calls) == 1


def test_preferred_character_on_lower_page_beats_earlier_outside_candidate(monkeypatch):
    other = character('Other', page='top')
    preferred = character('Alice', page='lower')
    main = make_main([[other], [preferred]])
    monkeypatch.setattr(dock_module, 'ISLAND_DOCK_DETECT', FakeDetect())

    assert main.island_dock_select_character(identity={'Alice', 'Bob'}, fallback=True) is preferred
    assert main._clicks == [preferred.button]
    assert main._sort_calls == [True]
    assert main._top_calls == 0
    assert main._next_calls == 1


def test_fallback_after_returning_to_top_uses_new_coordinates(monkeypatch):
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
        identity='Alice', descending=False, fallback=True, fallback_descending=True)
    assert main._sort_calls == [False, True]
    assert main._top_calls == 1
    assert main._clicks == [new_other.button]
    assert old_other.button not in main._clicks


def test_blacklisted_preference_can_fall_back_without_selecting_excluded_name(monkeypatch):
    forbidden = character('Alice')
    other = character('Other')
    main = make_main([[forbidden, other]])
    calls = install_search_stub(monkeypatch, main, [dict(pages=[[forbidden, other]])])

    assert main.island_dock_select_character(identity='Alice', blacklist={'Alice'}, fallback=True)
    assert main._clicks == [other.button]
    assert len(calls) == 1
    assert calls[0]['start_at_top'] is False


def test_select_character_clicks_match_before_any_page_navigation(monkeypatch):
    candidate = character('Alice', page='current')
    main = make_main([[candidate]])
    install_search_stub(monkeypatch, main, [dict(pages=[[candidate]])])

    assert main.island_dock_select_character(identity='Alice')
    assert main._clicks == [candidate.button]
    assert main._next_calls == 0


def test_failed_click_does_not_trigger_outside_fallback(monkeypatch):
    preferred = character('Alice')
    other = character('Other')
    main = make_main([[preferred, other]])
    calls = install_search_stub(monkeypatch, main, [
        dict(pages=[[preferred, other]]), dict(pages=[[other]]),
    ])
    main.island_dock_select_one = lambda button: main._clicks.append(button) or False

    assert main.island_dock_select_character(identity='Alice', fallback=True) is None
    assert main._clicks == [preferred.button]
    assert len(calls) == 1


def test_workerjuu_visible_first_uses_no_top_recovery(monkeypatch):
    workerjuu = character('Workerjuu', page='first')
    main = make_main([[workerjuu]])
    calls = install_search_stub(monkeypatch, main, [dict(pages=[[workerjuu]])])

    assert main.island_dock_select_workerjuu() is workerjuu
    assert len(calls) == 1
    assert calls[0]['descending'] is False
    assert calls[0]['start_at_top'] is False
    assert main._top_calls == 0


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
        emotion=(100, 150), emotion_limit=(100, 149), descending=False) is None
    down_swipes = main._next_calls

    assert main.island_dock_select_workerjuu(descending=True) is workerjuu
    assert main._sort_calls == [False, True]
    assert main._top_calls == 0
    assert main._next_calls == down_swipes
    assert main._clicks == [workerjuu.button]


def test_missing_workerjuu_does_not_scroll_or_retry():
    main = make_main([[character('Other')], [character('Workerjuu')]])

    assert main.island_dock_select_workerjuu() is None
    assert main._sort_calls == [False]
    assert main._top_calls == 0
    assert main._next_calls == 0
    assert main._clicks == []
