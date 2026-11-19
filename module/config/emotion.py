"""Map task-local emotion slots to normal-game fleet numbers."""
import re

TASKS = {'Main', 'Main2', 'Main3', 'Event', 'Event2', 'EventA',
         'EventB', 'EventC', 'EventD', 'EventSp', 'WarArchives'}


def fleet_number(task, data, slot):
    # Hard maps and special modes use their own formations.
    if task not in TASKS or data.get('Campaign', {}).get('Mode') == 'hard':
        return None
    if task not in {'Main', 'Main2', 'Main3'}:
        # Only ordinary A/B stages are known to select numbered dock fleets.
        # C/D, SP/EX and special event stages can use independent formations.
        if not re.fullmatch(r'[ab]\d+', str(data.get('Campaign', {}).get('Name', '')).lower()):
            return None
    value = data.get('Fleet', {}).get('Fleet' + str(slot))
    if type(value) is int and 1 <= value <= 6:
        return value
    return None


def peers(data, task, slot):
    number = fleet_number(task, data.get(task, {}), slot)
    if number is None:
        return []
    return [(name, index) for name, settings in data.items()
            for index in (1, 2)
            if 'Emotion' in settings
            and fleet_number(name, settings, index) == number]
