"""Restaurant selection processes both roles before leaving each live page."""

from types import SimpleNamespace

import pytest

import module.island_handler.dock as dock
import module.island_handler.restaurant as restaurant
from module.island_handler.dock_scanner import Character


def character(identity, status='free', grade='B'):
    return Character(identity=identity, emotion=100, emotion_limit=110, grade=grade, status=status)


def restaurant_dialog(monkeypatch, requests, pages, blacklist=(), preselected=(), fail_select=None, grid_size=None):
    main = object.__new__(restaurant.IslandRestaurant)
    state = SimpleNamespace(page=0, frame=0, selected=list(preselected), events=[], buttons=[],
                            unchanged=False, committed=None)
    main.config = object()
    main.working_restaurant_id = 601
    main._restaurant_offset = (0, 0)
    main.loop = lambda **kwargs: range(len(pages) + 5)
    main.is_in_island_dock = lambda: True
    main.is_in_island_restaurant = lambda: True
    main.appear_then_click = lambda *args, **kwargs: False
    main.unavailable_waitress_list = lambda: list(blacklist)
    main.device = SimpleNamespace(image=object())
    monkeypatch.setattr(restaurant, 'get_waitress_slots', lambda *args: requests)
    monkeypatch.setattr(dock, 'ISLAND_DOCK_DETECT', SimpleNamespace(load_color=lambda image: None))

    def sort(enable=True, **kwargs):
        state.events.append(('sort', enable))

    def top():
        state.events.append(('top',))
        state.page = 0
        return True

    def scan(disabled=()):
        state.frame += 1
        state.events.append(('scan', state.page))
        # Every rescan changes coordinates. Keeping a button from a previous
        # scan, including a scan on the same page, is an error in this adapter.
        candidates = []
        for index, source in enumerate(pages[state.page]):
            button = SimpleNamespace(identity=source.identity, frame=state.frame,
                                     area=(index, state.frame, index + 1, state.frame + 1))
            candidates.append(Character(
                identity=source.identity, emotion=source.emotion, emotion_limit=source.emotion_limit,
                grade=source.grade, status=source.status, button=button))
        state.buttons = [candidate.button for candidate in candidates]
        main.dock_grid = SimpleNamespace(
            buttons=state.buttons if grid_size is None else [None] * grid_size)
        return candidates

    def next_page(**kwargs):
        state.events.append(('down', state.page))
        state.unchanged = state.page == len(pages) - 1
        state.page = min(state.page + 1, len(pages) - 1)
        state.buttons = []

    def select(button):
        assert any(current is button for current in state.buttons), 'stale dock button'
        assert button.frame == state.frame
        state.events.append(('select', button.identity, state.page))
        if button.identity == fail_select:
            return False
        assert button.identity not in state.selected
        assert len(state.selected) < 2
        state.selected.append(button.identity)
        return True

    def cancel():
        state.events.append(('cancel',))
        state.selected.clear()

    def confirm(*args, **kwargs):
        state.events.append(('confirm',))
        state.committed = list(state.selected)

    main.island_dock_sort_method_dsc_set = sort
    main.ensure_dock_page_at_top = top
    main.island_dock_scan_page = scan
    main.next_dock_page = next_page
    main.appear = lambda *args, **kwargs: state.unchanged
    main.is_button_selected = lambda button, **kwargs: button.identity in state.selected
    main.island_dock_select_one = select
    main.island_dock_quit = cancel
    main.island_dock_select_confirm = confirm
    return main, state


@pytest.mark.parametrize(('requests', 'identities', 'blacklist', 'expected'), [
    (['A', 'B'], [], (), True),
    (['A', 'B'], ['B', 'A'], (), True),
    (['A', 'any'], ['C', 'A'], (), True),
    ([{'A', 'B'}, {'A', 'B'}], ['B', 'A'], (), True),
    ([{'A', 'B'}, {'B'}], ['B', 'A'], (), True),
    ([{'A', 'B'}, {'B'}], ['B'], (), True),
    ([{'A', 'B'}, {'A', 'B'}], ['B', 'B'], (), False),
    (['A', 'any'], ['B', 'C'], (), False),
    (['A', 'any'], ['A', 'C'], {'A'}, False),
    (['any', 'any'], ['Workerjuu', 'A'], (), False),
])
def test_waitress_requests_match_unordered_roles(requests, identities, blacklist, expected):
    assert restaurant.waitress_requests_match(requests, identities, blacklist) is expected


def test_any_is_selected_before_required_identity_on_lower_page(monkeypatch):
    main, state = restaurant_dialog(monkeypatch, ['A', 'any'], [
        [character('B')], [character('A')],
    ])

    assert main.choose_waitress() is True
    assert state.committed == ['B', 'A']
    assert [event for event in state.events if event[0] in ('top', 'down', 'select')] == [
        ('select', 'B', 0), ('down', 0), ('select', 'A', 1),
    ]


def test_two_named_characters_are_selected_in_encounter_order(monkeypatch):
    main, state = restaurant_dialog(monkeypatch, ['A', 'B'], [
        [character('B')], [character('A')],
    ])

    assert main.choose_waitress() is True
    assert state.committed == ['B', 'A']
    assert state.events.count(('top',)) == 0


def test_occupied_required_identity_aborts_before_clicking_same_page(monkeypatch):
    main, state = restaurant_dialog(monkeypatch, ['A', 'any'], [
        [character('B'), character('A', status='occupied')], [character('C')],
    ])

    assert main.choose_waitress() is False
    assert main.waitress_occupied is True
    assert not any(event[0] in ('select', 'down', 'confirm') for event in state.events)
    assert state.events[-1] == ('cancel',)


def test_occupied_required_identity_cancels_earlier_tentative_choice(monkeypatch):
    main, state = restaurant_dialog(monkeypatch, ['A', 'any'], [
        [character('B')], [character('A', status='occupied')], [character('C')],
    ])

    assert main.choose_waitress() is False
    assert main.waitress_occupied is True
    assert state.committed is None
    assert state.selected == []
    assert [event for event in state.events if event[0] in ('select', 'down', 'cancel')] == [
        ('select', 'B', 0), ('down', 0), ('cancel',),
    ]


def test_any_skips_occupied_candidates(monkeypatch):
    main, state = restaurant_dialog(monkeypatch, ['A', 'any'], [
        [character('B', status='occupied'), character('C')], [character('A')],
    ])

    assert main.choose_waitress() is True
    assert main.waitress_occupied is False
    assert state.committed == ['C', 'A']


def test_occupied_reason_is_reset_for_next_selection_attempt(monkeypatch):
    pages = [[character('A', status='occupied'), character('B')]]
    main, state = restaurant_dialog(monkeypatch, ['A', 'any'], pages)

    assert main.choose_waitress() is False
    assert main.waitress_occupied is True

    pages[0] = [character('A'), character('B')]
    assert main.choose_waitress() is True
    assert main.waitress_occupied is False
    assert state.committed == ['A', 'B']


def test_required_blacklisted_identity_cannot_be_replaced(monkeypatch):
    main, state = restaurant_dialog(monkeypatch, ['A', 'any'], [
        [character('A'), character('B'), character('C')],
    ], blacklist={'A'})

    assert main.choose_waitress() is False
    assert state.committed is None
    assert not any(event[0] == 'select' for event in state.events)


def test_any_blacklist_and_grade_preference_remain_in_force(monkeypatch):
    main, state = restaurant_dialog(monkeypatch, ['any', 'any'], [
        [character('A', grade='S'), character('B', grade='C'), character('C', grade='A')],
    ], blacklist={'A'})

    assert main.choose_waitress() is True
    assert state.committed == ['C', 'B']


def test_two_characters_on_same_page_use_fresh_buttons_after_first_click(monkeypatch):
    main, state = restaurant_dialog(monkeypatch, ['A', 'B'], [
        [character('B'), character('A'), character('C')],
    ])

    assert main.choose_waitress() is True
    assert state.committed == ['B', 'A']
    assert state.frame >= 2
    assert not any(event[0] == 'down' for event in state.events)


def test_missing_required_identity_does_not_turn_into_any(monkeypatch):
    main, state = restaurant_dialog(monkeypatch, ['A', 'any'], [
        [character('B')], [character('C')],
    ])

    assert main.choose_waitress() is False
    assert state.committed is None
    assert [event for event in state.events if event[0] == 'select'] == [('select', 'B', 0)]


def test_missing_required_identity_cancels_at_empty_tail_without_extra_swipes(monkeypatch):
    main, state = restaurant_dialog(monkeypatch, ['A', 'any'], [
        [character('B'), character('C')], [character('D')],
    ], grid_size=2)

    assert main.choose_waitress() is False
    assert state.committed is None
    assert state.selected == []
    assert [event for event in state.events if event[0] in ('select', 'down', 'cancel')] == [
        ('select', 'B', 0), ('down', 0), ('cancel',),
    ]


def test_visible_existing_selection_counts_toward_two_character_limit(monkeypatch):
    main, state = restaurant_dialog(monkeypatch, ['A', 'any'], [
        [character('B'), character('A'), character('C')],
    ], preselected=['B'])

    assert main.choose_waitress() is True
    assert state.committed == ['B', 'A']
    assert [event for event in state.events if event[0] == 'select'] == [('select', 'A', 0)]


def test_failed_click_cancels_without_confirming(monkeypatch):
    main, state = restaurant_dialog(monkeypatch, ['A', 'any'], [
        [character('A'), character('B')],
    ], fail_select='A')

    assert main.choose_waitress() is False
    assert main.waitress_occupied is False
    assert state.events[-1] == ('cancel',)
    assert state.committed is None


def test_single_active_role_selects_only_one_character(monkeypatch):
    main, state = restaurant_dialog(monkeypatch, ['A', 'none'], [
        [character('A'), character('B')],
    ])

    assert main.choose_waitress() is True
    assert state.committed == ['A']


def test_restaurant_does_not_start_after_selection_failure():
    main = object.__new__(restaurant.IslandRestaurant)
    main.restaurant_running = lambda: False
    main.receive_revenue = lambda: None
    main.restaurant_resting = lambda: False
    main.choose_waitress = lambda: False
    # select_dishes and restaurant_start deliberately remain unconfigured.
    assert main.run() is False
