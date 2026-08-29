"""Config generation/update facade (Phase 5.1: heavy parts split into mixins)."""
import typing as t

from module.base.decorator import cached_property
from module.base.timer import timer
from module.config.code_generation import CodeGenerationMixin
from module.config.deep import deep_default, deep_get, deep_iter, deep_set
from module.config.deploy_templates import DeployTemplatesMixin
from module.config.env import IS_ON_PHONE_CLOUD
from module.config.event_table import EventTableMixin
from module.config.redirect_utils.utils import *  # noqa: F403  (re-export facade)
from module.config.server import VALID_CHANNEL_PACKAGE, VALID_PACKAGE, VALID_SERVER_LIST, to_server
from module.config.utils import *  # noqa: F403  (re-export facade)
from module.tasks.registry import family_tasks


class ConfigGenerator(CodeGenerationMixin, EventTableMixin, DeployTemplatesMixin):
    @timer
    def generate(self):
        _ = self.args
        _ = self.menu
        _ = self.event
        self.insert_event()
        self.insert_package()
        self.insert_server()
        write_file(filepath_args(), self.args)
        write_file(filepath_args('menu'), self.menu)
        self.generate_code()
        for lang in LANGUAGES:
            self.generate_i18n(lang)
        self.generate_deploy_template()

    def insert_package(self):
        option = deep_get(self.argument, keys='Emulator.PackageName.option')
        option += list(VALID_PACKAGE.keys())
        option += list(VALID_CHANNEL_PACKAGE.keys())
        deep_set(self.argument, keys='Emulator.PackageName.option', value=option)
        deep_set(self.args, keys='Alas.Emulator.PackageName.option', value=option)

    def insert_server(self):
        option = deep_get(self.argument, keys='Emulator.ServerName.option')
        server_list = []
        for server, _list in VALID_SERVER_LIST.items():
            for index in range(len(_list)):
                server_list.append(f'{server}-{index}')
        option += server_list
        deep_set(self.argument, keys='Emulator.ServerName.option', value=option)
        deep_set(self.args, keys='Alas.Emulator.ServerName.option', value=option)


class ConfigUpdater:
    # Historical key migrations were removed in Phase 5.1 (all entries were
    # already commented out; migrations are far past their expiry window).
    # Add entries here as `(source, target)` or `(source, target, update_func)`.
    redirection: list = []

    @cached_property
    def args(self):
        return read_file(filepath_args())

    def config_update(self, old, is_template=False):
        """
        Args:
            old (dict):
            is_template (bool):

        Returns:
            dict:
        """
        new = {}

        for keys, data in deep_iter(self.args, depth=3):
            value = deep_get(old, keys=keys, default=data['value'])
            typ = data['type']
            display = data.get('display')
            if is_template or value is None or value == '' \
                    or typ in ['lock', 'state'] or (display == 'hide' and typ != 'stored'):
                value = data['value']
            value = parse_value(value, data=data)
            deep_set(new, keys=keys, value=value)

        # AzurStatsID
        if is_template:
            deep_set(new, 'Alas.DropRecord.AzurStatsID', None)
        else:
            deep_default(new, 'Alas.DropRecord.AzurStatsID', random_id())
        if deep_get(new, keys='OpsiHazard1Leveling.Scheduler.Enable'):
            deep_set(new, keys='OpsiMeowfficerFarming.Scheduler.Enable', value=True)
        # Update to latest event
        server = to_server(deep_get(new, 'Alas.Emulator.PackageName', 'cn'))
        if not is_template:
            for task in family_tasks('event') + family_tasks('raid') + family_tasks('coalition'):
                opts = deep_get(self.args, keys=f'{task}.Campaign.Event.option_{server}', default=[])
                if opts and deep_get(new, keys=f'{task}.Campaign.Event', default='campaign_main') not in opts:
                    deep_set(new,
                             keys=f'{task}.Campaign.Event',
                             value=opts[0])

            for task in family_tasks('gems'):
                opts = deep_get(self.args, keys=f'{task}.Campaign.Event.option_{server}', default=[])
                if opts and deep_get(new, keys=f'{task}.Campaign.Event', default='campaign_main') not in opts:
                    deep_set(new,
                             keys=f'{task}.Campaign.Event',
                             value=opts[0])
        # War archive does not allow campaign_main
        for task in family_tasks('war_archives'):
            opts = deep_get(self.args, keys=f'{task}.Campaign.Event.option_{server}', default=[])
            if opts and deep_get(new, keys=f'{task}.Campaign.Event', default='campaign_main') == 'campaign_main':
                deep_set(new,
                         keys=f'{task}.Campaign.Event',
                         value=opts[0])

        # Events does not allow default stage 12-4
        def default_stage(t, stage):
            if deep_get(new, keys=f'{t}.Campaign.Name', default='12-4') in ['7-2', '12-4']:
                deep_set(new, keys=f'{t}.Campaign.Name', value=stage)

        for task in family_tasks('event') + family_tasks('war_archives'):
            default_stage(task, 'D3')
        for task in family_tasks('coalition'):
            default_stage(task, 'area1-normal')

        if not is_template:
            new = self.config_redirect(old, new)
        new = self._override(new)

        return new

    def config_redirect(self, old, new):
        """
        Convert old settings to the new.

        Args:
            old (dict):
            new (dict):

        Returns:
            dict:
        """
        for row in self.redirection:
            if len(row) == 2:
                source, target = row
                update_func = None
            elif len(row) == 3:
                source, target, update_func = row
            else:
                continue

            if isinstance(source, tuple):
                value = []
                error = False
                for attribute in source:
                    tmp = deep_get(old, keys=attribute)
                    if tmp is None:
                        error = True
                        continue
                    value.append(tmp)
                if error:
                    continue
            else:
                value = deep_get(old, keys=source)
                if value is None:
                    continue

            if update_func is not None:
                value = update_func(value)

            if isinstance(target, tuple):
                for k, v in zip(target, value):
                    # Allow update same key
                    if (deep_get(old, keys=k) is None) or (source == target):
                        deep_set(new, keys=k, value=v)
            elif (deep_get(old, keys=target) is None) or (source == target):
                deep_set(new, keys=target, value=value)

        return new

    def _override(self, data):
        def remove_drop_save(key):
            value = deep_get(data, keys=key, default='do_not')
            if value == 'save_and_upload':
                value = 'upload'
                deep_set(data, keys=key, value=value)
            elif value == 'save':
                value = 'do_not'
                deep_set(data, keys=key, value=value)

        if IS_ON_PHONE_CLOUD:
            deep_set(data, 'Alas.Emulator.Serial', '127.0.0.1:5555')
            deep_set(data, 'Alas.Emulator.ScreenshotMethod', 'DroidCast_raw')
            deep_set(data, 'Alas.Emulator.ControlMethod', 'MaaTouch')
            for arg in deep_get(self.args, keys='Alas.DropRecord', default={}):
                remove_drop_save(arg)

        return data

    def save_callback(self, key: str, value: t.Any) -> t.Iterable[tuple[str, t.Any]]:
        """
        Args:
            key: Key path in config json, such as "Main.Emotion.Fleet1Value"
            value: Value set by user, such as "98"

        Yields:
            str: Key path to set config json, such as "Main.Emotion.Fleet1Record"
            any: Value to set, such as "2020-01-01 00:00:00"
        """
        if "Emotion" in key and "Value" in key:
            key = key.split(".")
            key[-1] = key[-1].replace("Value", "Record")
            yield ".".join(key), datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def read_file(self, config_name, is_template=False):
        """
        Read and update config file.

        Args:
            config_name (str): ./config/{file}.json
            is_template (bool):

        Returns:
            dict:
        """
        old = read_file(filepath_config(config_name))
        new = self.config_update(old, is_template=is_template)
        # The updated config did not write into file, although it doesn't matters.
        # Commented for performance issue
        # self.write_file(config_name, new)
        return new

    @staticmethod
    def write_file(config_name, data, mod_name='alas'):
        """
        Write config file.

        Args:
            config_name (str): ./config/{file}.json
            data (dict):
            mod_name (str):
        """
        write_file(filepath_config(config_name, mod_name), data)

    @timer
    def update_file(self, config_name, is_template=False):
        """
        Read, update and write config file.

        Args:
            config_name (str): ./config/{file}.json
            is_template (bool):

        Returns:
            dict:
        """
        data = self.read_file(config_name, is_template=is_template)
        self.write_file(config_name, data)
        return data


if __name__ == '__main__':
    """
    Process the whole config generation.

                 task.yaml -+----------------> menu.json
             argument.yaml -+-> args.json ---> config_generated.py
             override.yaml -+       |
                   gui.yaml --------+
                                    |
    (old) i18n/<lang>.json ---------+========> i18n/<lang>.json
    (old)    template.json ---------+========> template.json
    """
    # Ensure running in Alas root folder
    import os

    os.chdir(os.path.join(os.path.dirname(__file__), '../../'))

    ConfigGenerator().generate()
    ConfigUpdater().update_file('template', is_template=True)
