import argparse
import logging
import queue
import threading
import time
from datetime import datetime
from multiprocessing import Manager, Process
from multiprocessing.managers import SyncManager
from typing import Dict, Generator, List

# This must be the first to import
from module.logger import logger  # Change folder
import module.config.server as server
import module.webui.lang as lang
import module.webui.updater as updater
from filelock import FileLock
from module.config.config import AzurLaneConfig, Function
from module.config.config_updater import ConfigUpdater
from module.config.utils import (alas_instance, deep_get, deep_iter, deep_set,
                                 dict_to_kv, filepath_args, filepath_config,
                                 read_file, write_file)
from module.webui.base import Frame
from module.webui.config import WebuiConfig
from module.webui.discord_presence import close_discord_rpc, init_discord_rpc
from module.webui.fastapi import asgi_app
from module.webui.lang import _t, t
from module.webui.pin import put_input, put_select
from module.webui.translate import translate
from module.webui.utils import (Icon, QueueHandler, Switch, TaskHandler,
                                Thread, add_css, filepath_css,
                                get_window_visibility_state, login,
                                parse_pin_value, re_fullmatch)
from module.webui.widgets import (BinarySwitchButton, ScrollableCode,
                                  get_output, put_icon_buttons, put_none)
from pywebio import config as webconfig
from pywebio.exceptions import SessionClosedException, SessionNotFoundException
from pywebio.output import (clear, close_popup, popup, put_button, put_buttons,
                            put_collapse, put_column, put_error, put_html,
                            put_loading, put_markdown, put_row, put_scope,
                            put_text, toast, use_scope)
from pywebio.pin import pin, pin_wait_change
from pywebio.session import go_app, info, register_thread, run_js, set_env

config_updater = ConfigUpdater()
webui_config = WebuiConfig()
task_handler = TaskHandler()


class AlasManager:
    sync_manager: SyncManager
    all_alas: Dict[str, "AlasManager"] = {}

    def __init__(self, config_name: str = 'alas') -> None:
        self.config_name = config_name
        self.log_queue = self.sync_manager.Queue()
        self.log = []
        self.log_max_length = 500
        self.log_reduce_length = 100
        self._process = Process()
        self.thd_log_queue_handler = Thread()

    def start(self, func: str = 'Alas') -> None:
        if not self.alive:
            self._process = Process(
                target=AlasManager.run_alas,
                args=(self.config_name, func, self.log_queue, updater.event,))
            self._process.start()
            self.thd_log_queue_handler = Thread(
                target=self._thread_log_queue_handler)
            register_thread(self.thd_log_queue_handler)
            self.thd_log_queue_handler.start()
        else:
            toast(t("Gui.Toast.AlasIsRunning"), position='right', color='warn')

    def stop(self) -> None:
        lock = FileLock(f"{filepath_config(self.config_name)}.lock")
        with lock:
            if self.alive:
                self._process.terminate()
                self.log.append("Scheduler stopped.\n")
            if self.thd_log_queue_handler.is_alive():
                self.thd_log_queue_handler.stop()
        logger.info(f"Alas [{self.config_name}] stopped")

    def _thread_log_queue_handler(self) -> None:
        while self.alive:
            log = self.log_queue.get()
            self.log.append(log)
            if len(self.log) > self.log_max_length:
                self.log = self.log[self.log_reduce_length:]

    @property
    def alive(self) -> bool:
        return self._process.is_alive()

    @property
    def state(self) -> int:
        if self.alive:
            return 1
        elif len(self.log) == 0 or self.log[-1] == "Scheduler stopped.\n":
            return 2
        else:
            return 3

    @classmethod
    def get_alas(cls, config_name: str) -> "AlasManager":
        """
        Create a new alas if not exists.
        """
        if config_name not in cls.all_alas:
            cls.all_alas[config_name] = AlasManager(config_name)
        return cls.all_alas[config_name]

    @staticmethod
    def run_alas(config_name, func: str, q: queue.Queue, e: threading.Event) -> None:
        # Setup logger
        qh = QueueHandler(q)
        formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
        webconsole = logging.StreamHandler(stream=qh)
        webconsole.setFormatter(formatter)
        logging.getLogger('alas').addHandler(webconsole)

        # Set server before loading any buttons.
        config = AzurLaneConfig(config_name=config_name)
        server.server = deep_get(
            config.data, keys='Alas.Emulator.Server', default='cn')

        # Run alas
        if func == 'Alas':
            from alas import AzurLaneAutoScript
            AzurLaneAutoScript.stop_event = e
            AzurLaneAutoScript(config_name=config_name).loop()
        elif func == 'Daemon':
            from module.daemon.daemon import AzurLaneDaemon
            AzurLaneDaemon(config=config_name, task='Daemon').run()
        elif func == 'OpsiDaemon':
            from module.daemon.os_daemon import AzurLaneDaemon
            AzurLaneDaemon(config=config_name, task='OpsiDaemon').run()
        elif func == 'AzurLaneUncensored':
            from module.daemon.uncensored import AzurLaneUncensored
            AzurLaneUncensored(config=config_name,
                               task='AzurLaneUncensored').run()
            q.put("Scheduler stopped.\n")  # Prevent status turns to warning
        elif func == 'Benchmark':
            from module.daemon.benchmark import Benchmark
            Benchmark(config=config_name, task='Benchmark').run()
            q.put("Scheduler stopped.\n")  # Prevent status turns to warning
        elif func == 'GameManager':
            from module.daemon.game_manager import GameManager
            GameManager(config=config_name, task='GameManager').run()
            q.put("Scheduler stopped.\n")
        else:
            logger.critical("No function matched")

    @classmethod
    def running_instances(cls) -> List[str]:
        l = []
        for alas in cls.all_alas.values():
            if alas.alive:
                l.append(alas.config_name)
        return l


class AlasGUI(Frame):
    ALAS_MENU: Dict[str, Dict[str, List[str]]]
    ALAS_ARGS: Dict[str, Dict[str, Dict[str, Dict[str, str]]]]
    path_to_idx: Dict[str, str] = {}
    idx_to_path: Dict[str, str] = {}
    theme = 'default'

    @classmethod
    def shorten_path(cls, prefix='a') -> None:
        """
        Reduce pin_wait_change() command content-length
        Using full path name will transfer ~16KB per command,
        may lag when remote control or in bad internet condition.
        Use ~4KB after doing this.
        Args:
            prefix: all idx need to be a valid html, so a random character here
        """
        cls.ALAS_MENU = read_file(filepath_args('menu'))
        cls.ALAS_ARGS = read_file(filepath_args('args'))
        i = 0
        for list_path, _ in deep_iter(cls.ALAS_ARGS, depth=3):
            cls.path_to_idx['.'.join(list_path)] = f'{prefix}{i}'
            cls.idx_to_path[f'{prefix}{i}'] = '.'.join(list_path)
            i += 1

    def __init__(self) -> None:
        super().__init__()
        # modified keys, return values of pin_wait_change()
        self.modified_config_queue = queue.Queue()
        # alas config name
        self.alas_name = ''
        self.alas_config = AzurLaneConfig('template')
        self.alas_logs = ScrollableCode()

    @use_scope('aside', clear=True)
    def set_aside(self) -> None:
        # TODO: update put_icon_buttons()
        put_icon_buttons(Icon.DEVELOP, buttons=[{"label": t(
            "Gui.Aside.Develop"), "value": "Develop", "color": "aside"}], onclick=[self.ui_develop]),
        for name in alas_instance():
            put_icon_buttons(Icon.RUN,
                             buttons=[
                                 {"label": name, "value": name, "color": "aside"}],
                             onclick=self.ui_alas)
        put_icon_buttons(Icon.ADD, buttons=[{"label": t(
            "Gui.Aside.AddAlas"), "value": "AddAlas", "color": "aside"}], onclick=[self.ui_add_alas]),

    @use_scope('header_status')
    def set_status(self, state: int) -> None:
        """
        Args:
            state (int): 
                1 (running)
                2 (not running)
                3 (warning, stop unexpectedly)
                0 (hide)
                -1 (*state not changed)
        """
        if not self.visible:
            return
        if state == -1:
            return
        clear()

        if state == 1:
            put_row([
                put_loading(color='success').style(
                    "width:1.5rem;height:1.5rem;border:.2em solid currentColor;border-right-color:transparent;"),
                None,
                put_text(t("Gui.Status.Running"))
            ], size='auto 2px 1fr')
        elif state == 2:
            put_row([
                put_loading(color='secondary').style(
                    "width:1.5rem;height:1.5rem;border:.2em solid currentColor;"),
                None,
                put_text(t("Gui.Status.Inactive"))
            ], size='auto 2px 1fr')
        elif state == 3:
            put_row([
                put_loading(shape='grow', color='warning').style(
                    "width:1.5rem;height:1.5rem;"),
                None,
                put_text(t("Gui.Status.Warning"))
            ], size='auto 2px 1fr')

    @classmethod
    def set_theme(cls, theme='default') -> None:
        cls.theme = theme
        webui_config.Theme = theme
        webconfig(theme=theme)

    @use_scope('menu', clear=True)
    def alas_set_menu(self) -> None:
        """
        Set menu
        """
        put_buttons([
            {"label": t("Gui.MenuAlas.Overview"),
                "value": "Overview", "color": "menu"}
        ], onclick=[self.alas_overview]).style(f'--menu-Overview--'),

        for key, tasks in deep_iter(self.ALAS_MENU, depth=2):
            # path = '.'.join(key)
            menu = key[1]

            if menu == 'Tool':
                _onclick = self.alas_daemon_overview
            else:
                _onclick = self.alas_set_group

            task_btn_list = []
            for task in tasks:
                task_btn_list.append(
                    put_buttons([
                        {"label": t(f'Task.{task}.name'),
                         "value": task, "color": "menu"}
                    ], onclick=_onclick).style(f'--menu-{task}--')
                )

            put_collapse(
                title=t(f"Menu.{menu}.name"),
                content=task_btn_list
            )

        self.alas_overview()

    @use_scope('content', clear=True)
    def alas_set_group(self, task: str) -> None:
        """
        Set arg groups from dict
        """
        self.init_menu(name=task)
        self.set_title(t(f'Task.{task}.name'))

        put_scope('_groups', [
            put_none(),
            put_scope('groups'),
            put_scope('navigator')
        ])
        config = config_updater.update_config(self.alas_name)
        for group, arg_dict in deep_iter(self.ALAS_ARGS[task], depth=1):
            self.set_group(group, arg_dict, config, task)
            self.set_navigator(group)

    @use_scope('groups')
    def set_group(self, group, arg_dict, config, task):
        group_name = group[0]
        with use_scope(f'group_{group_name}'):
            put_text(t(f"{group_name}._info.name"))
            group_help = t(f"{group_name}._info.help")
            if group_help != "":
                put_text(group_help)
            put_html('<hr class="hr-group">')

            for arg, d in deep_iter(arg_dict, depth=1):
                arg = arg[0]
                arg_type = d['type']
                if arg_type == 'disable':
                    continue
                value = deep_get(
                    config, f'{task}.{group_name}.{arg}', d['value'])
                value = str(value) if isinstance(value, datetime) else value

                # Option
                options = deep_get(d, 'option', None)
                if options:
                    option = []
                    for opt in options:
                        o = {"label": t(
                            f"{group_name}.{arg}.{opt}"), "value": opt}
                        if value == opt:
                            o["selected"] = True
                        option.append(o)
                else:
                    option = None

                # Help
                arg_help = t(f"{group_name}.{arg}.help")
                if arg_help == "" or not arg_help:
                    arg_help = None

                # Invalid feedback
                invalid_feedback = t(
                    "Gui.Text.InvalidFeedBack").format(d['value'])

                get_output(
                    arg_type=arg_type,
                    name=self.path_to_idx[f"{task}.{group_name}.{arg}"],
                    title=t(f"{group_name}.{arg}.name"),
                    arg_help=arg_help,
                    value=value,
                    options=option,
                    invalid_feedback=invalid_feedback,
                ).show()

    @use_scope('navigator')
    def set_navigator(self, group):
        js = f'''
            $("#pywebio-scope-groups").scrollTop(
                $("#pywebio-scope-group_{group[0]}").position().top
                + $("#pywebio-scope-groups").scrollTop() - 59
            )
        '''
        put_button(
            label=t(f"{group[0]}._info.name"),
            onclick=lambda: run_js(js),
            color='navigator'
        )

    @use_scope('content', clear=True)
    def alas_overview(self) -> None:
        self.init_menu(name="Overview")
        self.set_title(t(f'Gui.MenuAlas.Overview'))

        put_scope('overview', [
            put_scope('schedulers'),
            put_scope('logs')
        ])

        with use_scope('schedulers'):
            put_scope('scheduler-bar', [
                put_text(t("Gui.Overview.Scheduler")).style(
                    "font-size: 1.25rem; margin: auto .5rem auto;"),
                put_scope('scheduler_btn')
            ])
            put_scope('running', [
                put_text(t("Gui.Overview.Running")),
                put_html('<hr class="hr-group">'),
                put_scope('running_tasks')
            ])
            put_scope('pending', [
                put_text(t("Gui.Overview.Pending")),
                put_html('<hr class="hr-group">'),
                put_scope('pending_tasks')
            ])
            put_scope('waiting', [
                put_text(t("Gui.Overview.Waiting")),
                put_html('<hr class="hr-group">'),
                put_scope('waiting_tasks')
            ])

        switch_scheduler = BinarySwitchButton(
            label_on=t("Gui.Button.Stop"),
            label_off=t("Gui.Button.Start"),
            onclick_on=lambda: self.alas.stop(),
            onclick_off=lambda: self.alas.start('Alas'),
            get_state=lambda: self.alas.alive,
            color_on='off',
            color_off='on',
            scope='scheduler_btn'
        )

        with use_scope('logs'):
            put_scope('log-bar', [
                put_text(t("Gui.Overview.Log")).style(
                    "font-size: 1.25rem; margin: auto .5rem auto;"),
                put_scope('log-bar-btns', [
                    put_button(
                        label=t("Gui.Button.ClearLog"),
                        onclick=self.alas_logs.reset,
                        color='off',
                    ),
                    put_scope('log_scroll_btn')
                ])
            ])
            self.alas_logs.output()

        switch_log_scroll = BinarySwitchButton(
            label_on=t("Gui.Button.ScrollON"),
            label_off=t("Gui.Button.ScrollOFF"),
            onclick_on=lambda: self.alas_logs.set_scroll(False),
            onclick_off=lambda: self.alas_logs.set_scroll(True),
            get_state=lambda: self.alas_logs.keep_bottom,
            color_on='on',
            color_off='off',
            scope='log_scroll_btn'
        )

        self.task_handler.add(switch_scheduler.g(), 1, True)
        self.task_handler.add(switch_log_scroll.g(), 1, True)
        self.task_handler.add(self.alas_update_overiew_task, 10, True)
        self.task_handler.add(self.alas_put_log(), 0.2, True)

    def alas_put_log(self) -> Generator[None, None, None]:
        yield
        last_idx = len(self.alas.log)
        self.alas_logs.append(''.join(self.alas.log))
        lines = 0
        while True:
            yield
            idx = len(self.alas.log)
            if idx < last_idx:
                last_idx -= self.alas.log_reduce_length
            if idx != last_idx:
                try:
                    self.alas_logs.append(''.join(self.alas.log[last_idx:idx]))
                except SessionNotFoundException:
                    break
                lines += idx - last_idx
                last_idx = idx

    def _alas_thread_wait_config_change(self) -> None:
        paths = []
        for path, d in deep_iter(self.ALAS_ARGS, depth=3):
            if d['type'] == 'disable':
                continue
            paths.append(self.path_to_idx['.'.join(path)])
        while self.alive:
            try:
                val = pin_wait_change(*paths)
                self.modified_config_queue.put(val)
            except SessionClosedException:
                break

    def _alas_thread_update_config(self) -> None:
        modified = {}
        valid = []
        invalid = []
        while self.alive:
            try:
                d = self.modified_config_queue.get(timeout=10)
                config_name = self.alas_name
            except queue.Empty:
                continue
            modified[self.idx_to_path[d['name']]] = parse_pin_value(d['value'])
            while True:
                try:
                    d = self.modified_config_queue.get(timeout=1)
                    modified[self.idx_to_path[d['name']]
                             ] = parse_pin_value(d['value'])
                except queue.Empty:
                    config = read_file(filepath_config(config_name))
                    for k, v in modified.copy().items():
                        validate = deep_get(self.ALAS_ARGS, k + '.validate')
                        if not len(str(v)):
                            default = deep_get(self.ALAS_ARGS, k + '.value')
                            deep_set(config, k, default)
                            valid.append(self.path_to_idx[k])
                            modified[k] = default
                        elif not validate or re_fullmatch(validate, v):
                            deep_set(config, k, v)
                            valid.append(self.path_to_idx[k])
                        else:
                            modified.pop(k)
                            invalid.append(self.path_to_idx[k])
                            logger.warning(
                                f'Invalid value {v} for key {k}, skip saving.')
                            # toast(t("Gui.Toast.InvalidConfigValue").format(
                            #       t('.'.join(k.split('.')[1:] + ['name']))),
                            #       duration=0, position='right', color='warn')
                    self.pin_remove_invalid_mark(valid)
                    self.pin_set_invalid_mark(invalid)
                    if modified:
                        toast(t("Gui.Toast.ConfigSaved"),
                              duration=1, position='right', color='success')
                        logger.info(
                            f'Save config {filepath_config(config_name)}, {dict_to_kv(modified)}')
                        write_file(filepath_config(config_name), config)
                    modified.clear()
                    valid.clear()
                    invalid.clear()
                    break

    def alas_update_overiew_task(self) -> None:
        if not self.visible:
            return
        self.alas_config.load()
        self.alas_config.get_next_task()

        if len(self.alas_config.pending_task) >= 1:
            if self.alas.alive:
                running = self.alas_config.pending_task[:1]
                pending = self.alas_config.pending_task[1:]
            else:
                running = []
                pending = self.alas_config.pending_task[:]
        else:
            running = []
            pending = []
        waiting = self.alas_config.waiting_task

        def put_task(func: Function):
            with use_scope(f'overview-task_{func.command}'):
                put_column([
                    put_text(t(f'Task.{func.command}.name')
                             ).style("--arg-title--"),
                    put_text(str(func.next_run)).style("--arg-help--"),
                ], size="auto auto")
                put_button(
                    label=t("Gui.Button.Setting"),
                    onclick=lambda: self.alas_set_group(func.command),
                    color="off"
                )
        with use_scope('running_tasks', clear=True):
            if running:
                for task in running:
                    put_task(task)
            else:
                put_text(t("Gui.Overview.NoTask")).style(
                    "--overview-notask-text--")
        with use_scope('pending_tasks', clear=True):
            if pending:
                for task in pending:
                    put_task(task)
            else:
                put_text(t("Gui.Overview.NoTask")).style(
                    "--overview-notask-text--")
        with use_scope('waiting_tasks', clear=True):
            if waiting:
                for task in waiting:
                    put_task(task)
            else:
                put_text(t("Gui.Overview.NoTask")).style(
                    "--overview-notask-text--")

    @use_scope('content', clear=True)
    def alas_daemon_overview(self, task: str) -> None:
        self.init_menu(name=task)
        self.set_title(t(f'Task.{task}.name'))

        if self.is_mobile:
            put_scope('daemon-overview', [
                put_scope('scheduler-bar'),
                put_scope('groups'),
                put_scope('log-bar'),
                self.alas_logs.output()
            ])
        else:
            put_scope('daemon-overview', [
                put_none(),
                put_scope('_daemon', [
                    put_scope('_daemon_upper', [
                        put_scope('scheduler-bar'),
                        put_scope('log-bar')
                    ]),
                    put_scope('groups'),
                    self.alas_logs.output()
                ]),
                put_none(),
            ])

        with use_scope('scheduler-bar'):
            put_text(t("Gui.Overview.Scheduler")).style(
                "font-size: 1.25rem; margin: auto .5rem auto;")
            put_scope('scheduler_btn')

        switch_scheduler = BinarySwitchButton(
            label_on=t("Gui.Button.Stop"),
            label_off=t("Gui.Button.Start"),
            onclick_on=lambda: self.alas.stop(),
            onclick_off=lambda: self.alas.start(task),
            get_state=lambda: self.alas.alive,
            color_on='on',
            color_off='off',
            scope='scheduler_btn'
        )

        with use_scope('log-bar'):
            put_text(t("Gui.Overview.Log")).style(
                "font-size: 1.25rem; margin: auto .5rem auto;")
            put_scope('log-bar-btns', [
                put_button(
                    label=t("Gui.Button.ClearLog"),
                    onclick=self.alas_logs.reset,
                    color='off',
                ),
                put_scope('log_scroll_btn')
            ])

        switch_log_scroll = BinarySwitchButton(
            label_on=t("Gui.Button.ScrollON"),
            label_off=t("Gui.Button.ScrollOFF"),
            onclick_on=lambda: self.alas_logs.set_scroll(False),
            onclick_off=lambda: self.alas_logs.set_scroll(True),
            get_state=lambda: self.alas_logs.keep_bottom,
            color_on='on',
            color_off='off',
            scope='log_scroll_btn'
        )

        config = config_updater.update_config(self.alas_name)
        for group, arg_dict in deep_iter(self.ALAS_ARGS[task], depth=1):
            self.set_group(group, arg_dict, config, task)

        self.task_handler.add(switch_scheduler.g(), 1, True)
        self.task_handler.add(switch_log_scroll.g(), 1, True)
        self.task_handler.add(self.alas_put_log(), 0.2, True)

    @use_scope('menu', clear=True)
    def dev_set_menu(self) -> None:
        self.init_menu(collapse_menu=False, name="Develop")

        put_button(
            label=t("Gui.MenuDevelop.HomePage"),
            onclick=self.show,
            color="menu"
        ).style(f'--menu-HomePage--')

        put_button(
            label=t("Gui.MenuDevelop.Translate"),
            onclick=self.dev_translate,
            color="menu"
        ).style(f'--menu-Translate--')

    def dev_translate(self) -> None:
        go_app('translate', new_window=True)
        lang.TRANSLATE_MODE = True
        self.show()

    def ui_develop(self) -> None:
        self.init_aside(name="Develop")
        self.set_title(t('Gui.Aside.Develop'))
        self.dev_set_menu()
        self.alas_name = ''
        if hasattr(self, 'alas'):
            del self.alas
        self.state_switch.switch()

    def ui_alas(self, config_name: str) -> None:
        if config_name == self.alas_name:
            self.expand_menu()
            return
        self.init_aside(name=config_name)
        clear('content')
        self.alas_name = config_name
        self.alas = AlasManager.get_alas(config_name)
        self.alas_config = AzurLaneConfig(config_name, '')
        self.state_switch.switch()
        self.alas_set_menu()

    def ui_add_alas(self) -> None:
        with popup(t("Gui.AddAlas.PopupTitle")) as s:
            def get_unused_name():
                all_name = alas_instance()
                for i in range(2, 100):
                    if f'alas{i}' not in all_name:
                        return f'alas{i}'
                else:
                    return ''

            def add():
                name = pin["AddAlas_name"]
                origin = pin["AddAlas_copyfrom"]

                if name not in alas_instance():
                    r = read_file(filepath_config(origin))
                    write_file(filepath_config(name), r)
                    self.set_aside()
                    self.active_button("aside", self.alas_name)
                    close_popup()
                else:
                    clear(s)
                    put(name, origin)
                    put_error(t("Gui.AddAlas.FileExist"), scope=s)

            def put(name=None, origin=None):
                put_input(
                    name="AddAlas_name",
                    label=t("Gui.AddAlas.NewName"),
                    value=name or get_unused_name(),
                    scope=s
                ),
                put_select(
                    name="AddAlas_copyfrom",
                    label=t("Gui.AddAlas.CopyFrom"),
                    options=['template'] + alas_instance(),
                    value=origin or 'template',
                    scope=s
                ),
                put_button(
                    label=t("Gui.AddAlas.Confirm"),
                    onclick=add,
                    scope=s
                )

            put()

    def show(self) -> None:
        self._show()
        self.set_aside()
        self.collapse_menu()
        self.alas_name = ''
        if hasattr(self, 'alas'):
            del self.alas
        self.set_status(0)

        def set_language(l):
            lang.set_language(l)
            self.show()

        def set_theme(t):
            self.set_theme(t)
            run_js("location.reload()")

        with use_scope('content'):
            put_text("Select your language / 选择语言").style("text-align: center")
            put_buttons(
                [{"label": "简体中文", "value": "zh-CN"},
                 {"label": "繁體中文", "value": "zh-TW"},
                 {"label": "English", "value": "en-US"},
                 {"label": "日本語", "value": "ja-JP"}],
                onclick=lambda l: set_language(l),
            ).style("text-align: center")
            put_text("Change theme / 更改主题").style("text-align: center")
            put_buttons(
                [{"label": "Light", "value": "default", "color": "light"},
                 {"label": "Dark", "value": "dark", "color": "dark"}],
                onclick=lambda t: set_theme(t),
            ).style("text-align: center")

            # show something
            put_markdown("""
            Alas is a free open source software, if you paid for Alas from any channel, please refund.
            Alas 是一款免费开源软件，如果你在任何渠道付费购买了Alas，请退款。
            Project repository 项目地址：`https://github.com/LmeSzinc/AzurLaneAutoScript`
            """).style('text-align: center')

        if lang.TRANSLATE_MODE:
            lang.reload()

            def _disable():
                lang.TRANSLATE_MODE = False
                self.show()

            toast(_t("Gui.Toast.DisableTranslateMode"),
                  duration=0, position='right', onclick=_disable)

    def run(self) -> None:
        # setup gui
        set_env(title="Alas", output_animation=False)
        add_css(filepath_css('alas'))
        if self.is_mobile:
            add_css(filepath_css('alas-mobile'))
        else:
            add_css(filepath_css('alas-pc'))

        if self.theme == 'dark':
            add_css(filepath_css('dark-alas'))
        else:
            add_css(filepath_css('light-alas'))

        self.show()

        # detect config change
        _thread_wait_config_change = Thread(
            target=self._alas_thread_wait_config_change)
        register_thread(_thread_wait_config_change)
        _thread_wait_config_change.start()

        # save config
        _thread_save_config = Thread(
            target=self._alas_thread_update_config)
        register_thread(_thread_save_config)
        _thread_save_config.start()

        visibility_state_switch = Switch(
            status={
                True: [
                    lambda: self.__setattr__('visible', True),
                    lambda: self.alas_update_overiew_task() if self.page == 'Overview' else 0,
                    lambda: self.task_handler._task.__setattr__('delay', 15)
                ],
                False: [
                    lambda: self.__setattr__('visible', False),
                    lambda: self.task_handler._task.__setattr__('delay', 1)
                ]
            },
            get_state=get_window_visibility_state,
            name='visibility_state'
        )

        self.state_switch = Switch(
            status=self.set_status,
            get_state=lambda: getattr(getattr(self, 'alas', -1), 'state', -1),
            name='state'
        )

        self.task_handler.add(self.state_switch.g(), 2)
        self.task_handler.add(visibility_state_switch.g(), 15)
        self.task_handler.start()


def debug():
    """For interactive python.
        $ python3
        >>> from module.webui.app import *
        >>> debug()
        >>> 
    """
    startup()
    AlasGUI().run()


def startup():
    AlasManager.sync_manager = Manager()
    AlasGUI.shorten_path()
    lang.reload()
    updater.event = AlasManager.sync_manager.Event()
    task_handler.add(updater.update_state(), updater.delay)
    task_handler.start()
    init_discord_rpc()


def start_alas():
    """
    After update and reload, restart all alas that running before update
    """


def clearup():
    """
    Notice: Ensure run it before uvicorn reload app,
    all process will NOT EXIT after close electron app.
    """
    close_discord_rpc()
    for alas in AlasManager.all_alas.values():
        alas.stop()
    AlasManager.sync_manager.shutdown()
    logger.info("Alas closed.")


def reload():
    def r():
        clearup()
        put_loading(color='success')
        run_js('setTimeout(function(){window.location.href = "/";}, 3000);')
        with open('./reloadflag', mode='w'):
            pass

    put_button(
        label='Reload',
        onclick=r,
        color='danger'
    )


def app():
    parser = argparse.ArgumentParser(description='Alas web service')
    parser.add_argument('-k', '--key', type=str,
                        help='Password of alas. No password by default')
    parser.add_argument("--cdn", action="store_true",
                        help="Use jsdelivr cdn for pywebio static files (css, js). Self host cdn by default.")
    args, _ = parser.parse_known_args()

    # Apply config
    AlasGUI.set_theme(theme=webui_config.Theme)
    lang.LANG = webui_config.Language
    key = args.key or webui_config.Password
    cdn = args.cdn or (webui_config.CDN == 'true') or False

    logger.hr('Webui configs')
    logger.attr('Theme', webui_config.Theme)
    logger.attr('Language', lang.LANG)
    logger.attr('Password', True if key else False)
    logger.attr('CDN', cdn)


    def index():
        if key != '' and not login(key):
            logger.warning(f"{info.user_ip} login failed.")
            time.sleep(1.5)
            run_js('location.reload();')
            return
        AlasGUI().run()

    app = asgi_app(
        [index, translate, reload],
        cdn=cdn,
        static_dir=None,
        debug=True,
        on_startup=[startup, start_alas],
        on_shutdown=[clearup]
    )

    return app
