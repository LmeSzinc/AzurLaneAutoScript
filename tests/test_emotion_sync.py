"""Dependency-free regression tests for the production emotion methods.

Load their AST to avoid importing Android/OCR/GUI dependencies in unit tests.
"""
import ast
import copy
import unittest
from contextlib import nullcontext
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_method(path, class_name, method):
    tree = ast.parse((ROOT / path).read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method)
    namespace = {'datetime': datetime, 'DIC_RECOVER': {'not_in_dormitory': 20,
                 'dormitory_floor_1': 40, 'dormitory_floor_2': 50},
                 'DIC_RECOVER_MAX': {'not_in_dormitory': 119,
                 'dormitory_floor_1': 150, 'dormitory_floor_2': 150}, 'OATH_RECOVER': 10}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[method]


class Config:
    set_record = load_method('module/config/config.py', 'AzurLaneConfig', 'set_record')

    def __init__(self, data, task):
        self.data, self.overridden = data, {}
        self.bound = {f'Emotion_Fleet{i}{key}': f'{task}.Emotion.Fleet{i}{key}'
                      for i in (1, 2) for key in ('Value', 'Record')}

    def __setattr__(self, key, value):
        if key in self.__dict__.get('bound', {}):
            self.cross_set(self.bound[key], value)
        else:
            object.__setattr__(self, key, value)

    def cross_set(self, path, value):
        task, group, key = path.split('.')
        self.data[task][group][key] = value

    def multi_set(self):
        return nullcontext()


class Fleet:
    update = load_method('module/combat/emotion.py', 'FleetEmotion', 'update')

    def __init__(self, config, slot=1):
        self.config, self.fleet = config, slot
        self.value_name = f'Emotion_Fleet{slot}Value'
        task = config.bound[self.value_name].split('.')[0]
        settings = config.data[task]['Emotion']
        self.value = settings[f'Fleet{slot}Value']
        self.record = settings[f'Fleet{slot}Record']
        self.speed, self.max = 5, 150


class EmotionSyncTest(unittest.TestCase):
    def setUp(self):
        settings = {'Campaign': {'Mode': 'normal', 'Name': 'a1'},
                    'Fleet': {'Fleet1': 1, 'Fleet2': 2}, 'Emotion': {}}
        for i in (1, 2):
            settings['Emotion'].update({f'Fleet{i}Value': 140,
                f'Fleet{i}Record': datetime.now(), f'Fleet{i}Recover': 'dormitory_floor_2',
                f'Fleet{i}Oath': False, f'Fleet{i}Control': 'keep_exp_bonus'})
        self.data = {name: copy.deepcopy(settings) for name in ('Main', 'Event', 'Raid')}
        self.data['Event']['Fleet'] = {'Fleet1': 3, 'Fleet2': 1}

    def test_cross_slot_sync_and_isolation(self):
        before = copy.deepcopy(self.data)
        Config(self.data, 'Main').set_record(Emotion_Fleet1Value=78)
        self.assertEqual(self.data['Event']['Emotion']['Fleet2Value'], 78)
        self.assertEqual(self.data['Main']['Emotion']['Fleet1Record'],
                         self.data['Event']['Emotion']['Fleet2Record'])
        self.assertEqual(self.data['Event']['Emotion']['Fleet1Value'], 140)
        self.assertEqual(self.data['Raid'], before['Raid'])
        self.assertEqual(self.data['Event']['Emotion']['Fleet2Control'], 'keep_exp_bonus')

    def test_recovery_is_not_counted_twice(self):
        old = datetime.fromtimestamp((int(datetime.now().timestamp()) // 360 - 2) * 360)
        self.data['Main']['Emotion'].update(Fleet1Value=80, Fleet1Record=old)
        self.data['Event']['Emotion'].update(Fleet2Value=80, Fleet2Record=old)
        config = Config(self.data, 'Main')
        fleet = Fleet(config)
        fleet.update()
        self.assertEqual(fleet.current, 90)
        config.set_record(Emotion_Fleet1Value=fleet.current)
        other = Fleet(Config(copy.deepcopy(self.data), 'Event'), 2)
        other.update()
        self.assertEqual(other.current, 90)

    def test_legacy_lower_record_wins(self):
        self.data['Event']['Emotion']['Fleet2Value'] = 70
        fleet = Fleet(Config(self.data, 'Main'))
        fleet.update()
        self.assertEqual(fleet.current, 70)

    def test_special_stages_and_overrides_are_independent(self):
        self.data['Event']['Campaign']['Name'] = 'd3'
        Config(self.data, 'Main').set_record(Emotion_Fleet1Value=60)
        self.assertEqual(self.data['Event']['Emotion']['Fleet2Value'], 140)
        self.data['Event']['Campaign']['Name'] = 'a1'
        config = Config(self.data, 'Main')
        config.overridden['Fleet_Fleet1'] = 4
        config.set_record(Emotion_Fleet1Value=50)
        self.assertEqual(self.data['Event']['Emotion']['Fleet2Value'], 140)


if __name__ == '__main__':
    unittest.main()
