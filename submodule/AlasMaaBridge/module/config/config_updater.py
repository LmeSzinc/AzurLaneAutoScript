import sys
sys.path.append('i:/AzurLaneAutoScript')

from cached_property import cached_property

from module.base.timer import timer
from module.config import config_updater
from module.config.utils import *


class ConfigGenerator(config_updater.ConfigGenerator):
    @timer
    def generate(self):
        write_file(filepath_args(), self.args)
        write_file(filepath_args('menu'), self.menu)
        self.generate_code()
        for lang in LANGUAGES:
            self.generate_i18n(lang)

    @timer
    def generate_i18n(self, lang):
        """
        Load old translations and generate new translation file.

                     args.json ---+-----> i18n/<lang>.json
        (old) i18n/<lang>.json ---+

        """
        new = {}
        old = read_file(filepath_i18n(lang))

        def deep_load(keys, default=True, words=('name', 'help')):
            for word in words:
                k = keys + [str(word)]
                d = ".".join(k) if default else str(word)
                v = deep_get(old, keys=k, default=d)
                deep_set(new, keys=k, value=v)

        # Menu
        for path, data in deep_iter(self.task, depth=3):
            if 'tasks' not in path:
                continue
            task_group, _, task = path
            deep_load(['Menu', task_group])
            deep_load(['Task', task])
        # Arguments
        visited_group = set()
        for path, data in deep_iter(self.argument, depth=2):
            if path[0] not in visited_group:
                deep_load([path[0], '_info'])
                visited_group.add(path[0])
            deep_load(path)
            if 'option' in data:
                deep_load(path, words=data['option'], default=False)
        
        # GUI i18n
        for path, _ in deep_iter(self.gui, depth=2):
            group, key = path
            deep_load(keys=['Gui', group], words=(key,))

        # Copy stage names from MaaFight to MaaFightWeekly
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for stage, trans in deep_get(new, keys='MaaFight.Stage', default={}).items():
            if '-' not in stage:
                continue
            for day in day_names:
                if deep_get(new, keys=['MaaFightWeekly', day, stage]):
                    deep_set(new, keys=['MaaFightWeekly', day, stage], value=trans)

        write_file(filepath_i18n(lang), new)


class ConfigUpdater(config_updater.ConfigUpdater):
    redirection = []

    @cached_property
    def args(self):
        return read_file(filepath_args(mod_name='maa'))

    def read_file(self, config_name, is_template=False):
        old = read_file(filepath_config(config_name, 'maa'))
        return self.config_update(old, is_template=is_template)

    @staticmethod
    def write_file(config_name, data, mod_name='maa'):
        write_file(filepath_config(config_name, mod_name), data)

    def config_update(self, old, is_template=False):
        """
        Args:
            old (dict):
            is_template (bool):

        Returns:
            dict:
        """
        new = {}

        def deep_load(keys):
            data = deep_get(self.args, keys=keys, default={})
            value = deep_get(old, keys=keys, default=data['value'])
            if is_template or value is None or value == '' or data['type'] == 'lock' or data.get('display') == 'hide':
                value = data['value']
            value = parse_value(value, data=data)
            deep_set(new, keys=keys, value=value)

        for path, _ in deep_iter(self.args, depth=3):
            deep_load(path)

        if not is_template:
            new = self.config_redirect(old, new)

        return new


if __name__ == '__main__':
    """
    Process the whole config generation.

                 task.yaml -+----------------> menu.json
             argument.yaml -+-> args.json ---> config_generated.py
             override.yaml -+       |
                  gui.yaml --------\|
                                   ||
    (old) i18n/<lang>.json --------\\========> i18n/<lang>.json
    (old)    template.json ---------\========> template.json
    """
    # Ensure running in mod root folder
    import os
    os.chdir(os.path.join(os.path.dirname(__file__), "../../"))
    ConfigGenerator().generate()
    os.chdir('../../')
    ConfigUpdater().update_file('template', is_template=True)
