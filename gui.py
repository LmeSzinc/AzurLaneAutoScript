import argparse
import logging
import queue
import time
from multiprocessing import Manager, Process
from multiprocessing.managers import SyncManager

from pywebio.exceptions import *
from pywebio.session import go_app, info, register_thread, set_env

import module.webui.lang as lang
from module.config.config import AzurLaneConfig, Function
from module.config.config_updater import ConfigUpdater
from module.config.utils import *
from module.logger import logger  # Change folder
from module.webui.base import Frame
from module.webui.lang import _t, t
from module.webui.translate import translate
from module.webui.utils import (Icon, QueueHandler, Thread, add_css,
                                 filepath_css, get_output, login,
                                 parse_pin_value)
from module.webui.widgets import *

all_alas = {}
config_updater = ConfigUpdater()


def get_alas(config_name: str) -> "Alas":
    """
    Create a new alas if not exists.
    """
    if config_name not in all_alas:
        all_alas[config_name] = Alas(config_name)
    return all_alas[config_name]


def run_alas(config_name, q: queue) -> None:
    # Setup logger
    qh = QueueHandler(q)
    formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    webconsole = logging.StreamHandler(stream=qh)
    webconsole.setFormatter(formatter)
    logging.getLogger('alas').addHandler(webconsole)

    # Run alas
    from alas import AzurLaneAutoScript
    AzurLaneAutoScript(config_name=config_name).loop()


class Alas:
    manager: SyncManager

    def __init__(self, config_name: str = 'alas') -> None:
        self.config_name = config_name
        self.log_queue = Alas.manager.Queue()
        self.log = []
        self.log_max_length = 500
        self.log_reduce_length = 100
        self.process = Process()
        self.thd_log_queue_handler = Thread()

    def start(self) -> None:
        if not self.process.is_alive():
            self.process = Process(target=run_alas, args=(
                self.config_name, self.log_queue,))
            self.process.start()
            self.thd_log_queue_handler = Thread(
                target=self._thread_log_queue_handler)
            register_thread(self.thd_log_queue_handler)
            self.thd_log_queue_handler.start()
        else:
            toast(t("Gui.Toast.AlasIsRunning"), position='right', color='warn')

    def stop(self) -> None:
        if self.process.is_alive():
            self.process.terminate()
            self.log.append("Scheduler stopped.\n")
        if self.thd_log_queue_handler.is_alive():
            self.thd_log_queue_handler.stop()

    def _thread_log_queue_handler(self) -> None:
        while self.process.is_alive():
            log = self.log_queue.get()
            self.log.append(log)
            if len(self.log) > self.log_max_length:
                self.log = self.log[self.log_reduce_length:]


ALAS_MENU = read_file(filepath_args('menu'))
ALAS_ARGS = read_file(filepath_args('args'))

# Reduce pin_wait_change() command content-length
# Using full path name will transfer ~16KB per command,
# may lag when remote control or in bad internet condition.
# Use ~4KB after doing this.
path_to_idx = {}
idx_to_path = {}


def shorten_path() -> None:
    i = 0
    for list_path, _ in deep_iter(ALAS_ARGS, depth=3):
        path_to_idx['.'.join(list_path)] = f'a{i}'
        idx_to_path[f'a{i}'] = '.'.join(list_path)
        i += 1


shorten_path()


class AlasGUI(Frame):
    alas: Alas

    def __init__(self) -> None:
        super().__init__()
        # modified keys, return values of pin_wait_change()
        self.modified_config_queue = queue.Queue()
        # alas config name
        self.alas_name = ''
        self.alas_config = AzurLaneConfig('template', '')
        self.alas_logs = ScrollableCode()
        self.alas_running = output().style("container-overview-task")
        self.alas_pending = output().style("container-overview-task")
        self.alas_waiting = output().style("container-overview-task")

    def set_aside(self) -> None:

        # note: value doesn't matters if onclick is a list, button binds to functions in order.
        # when onclick isn't a list, value will pass to function.
        self.aside.reset(
            put_icon_buttons(Icon.DEVELOP, buttons=[{"label": t(
                "Gui.Aside.Develop"), "value": "develop", "color": "aside"}], onclick=[self.ui_develop]),
            *[put_icon_buttons(Icon.RUN,
                               buttons=[{"label": name, "value": name, "color": "aside"}],
                               onclick=self.ui_alas)
              for name in alas_instance()]
        )

    def set_status(self, status: int) -> None:
        """
        Args:
            status (int): 
                1 (running),
                2 (not running),
                -1 (warning, stop unexpectedly),
                0 (hide)
        """
        if self._status == status:
            return
        self._status = status

        if status == 1:
            s = put_row([
                put_loading(color='success').style(
                    "width:1.5rem;height:1.5rem;border:.2em solid currentColor;border-right-color:transparent;"),
                None,
                put_text(t("Gui.Status.Running"))
            ], size='auto 2px 1fr')
        elif status == 2:
            s = put_row([
                put_loading(color='secondary').style("width:1.5rem;height:1.5rem;border:.2em solid currentColor;"),
                None,
                put_text(t("Gui.Status.Inactive"))
            ], size='auto 2px 1fr')
        elif status == -1:
            s = put_row([
                put_loading(shape='grow', color='warning').style("width:1.5rem;height:1.5rem;"),
                None,
                put_text(t("Gui.Status.Warning"))
            ], size='auto 2px 1fr')
        else:
            s = ''

        self.status.reset(s)

    # Alas

    def alas_set_menu(self) -> None:
        """
        Set menu for alas
        """
        self.menu.append(
            put_buttons([
                {"label": t("Gui.MenuAlas.Overview"),
                 "value": "Overview", "color": "menu"}
            ], onclick=[self.alas_overview]).style(f'--menu-Overview--'),
        )
        for key, tasks in deep_iter(ALAS_MENU, depth=2):
            # path = '.'.join(key)
            menu = key[1]
            self.menu.append(
                put_collapse(t(f"Menu.{menu}.name"),
                             [put_buttons([
                                 {"label": t(f'Task.{task}.name'),
                                  "value": task, "color": "menu"}
                             ], onclick=self.alas_set_group).style(f'--menu-{task}--') for task in tasks]
                             )
            )

        self.alas_overview()

    def alas_set_group(self, task: str) -> None:
        """
        Set arg groups from dict
        """
        self.init_menu(name=task)
        self.title.reset(f"{t(f'Task.{task}.name')}")

        group_area = output()
        navigator = output()

        if self.is_mobile:
            content_alas = group_area
        else:
            content_alas = put_row([
                None,
                group_area,
                navigator,
            ], size=".5fr minmax(25rem, 5fr) 2fr")

        self.content.append(content_alas)

        config = config_updater.update_config(self.alas_name)

        for group, arg_dict in deep_iter(ALAS_ARGS[task], depth=1):
            group = group[0]
            group_help = t(f"{group}._info.help")
            if group_help == "" or not group_help:
                group_help = None
            arg_group = put_group(t(f"{group}._info.name"), group_help)
            list_arg = []
            for arg, d in deep_iter(arg_dict, depth=1):
                arg = arg[0]
                arg_type = d['type']
                if arg_type == 'disable':
                    continue
                value = deep_get(config, f'{task}.{group}.{arg}', d['value'])
                value = str(value) if isinstance(value, datetime) else value

                # Option
                options = deep_get(d, 'option', None)
                if options:
                    option = []
                    for opt in options:
                        o = {"label": t(f"{group}.{arg}.{opt}"), "value": opt}
                        if value == opt:
                            o["selected"] = True
                        option.append(o)
                else:
                    option = None

                # Help
                arg_help = t(f"{group}.{arg}.help")
                if arg_help == "" or not arg_help:
                    arg_help = None

                if self.is_mobile:
                    width = '8rem'
                else:
                    width = '12rem'

                list_arg.append(get_output(
                    arg_type=arg_type,
                    name=path_to_idx[f"{task}.{group}.{arg}"],
                    title=t(f"{group}.{arg}.name"),
                    arg_help=arg_help,
                    value=value,
                    options=option,
                    width=width,
                ))
            if list_arg:
                group_area.append(arg_group)
                arg_group.append(*list_arg)

    def alas_overview(self) -> None:
        self.init_menu(name="Overview")
        self.title.reset(f"{t(f'Gui.MenuAlas.Overview')}")

        scheduler = put_row([
            put_text(t("Gui.Overview.Scheduler")).style(
                "font-size: 1.25rem; margin: auto .5rem auto;"),
            None,
            put_buttons(
                buttons=[
                    {"label": t("Gui.Button.Start"),
                     "value": "Start", "color": "scheduler-on"},
                    {"label": t("Gui.Button.Stop"),
                     "value": "Stop", "color": "scheduler-off"},
                ],
                onclick=[
                    self.alas.start,
                    self.alas.stop,
                ]
            )
        ], size="auto 1fr auto").style("container-overview-group")

        log = put_row([
            put_text(t("Gui.Overview.Log")).style(
                "font-size: 1.25rem; margin: auto .5rem auto;"),
            None,
            put_buttons(
                buttons=[
                    {"label": t("Gui.Button.ClearLog"),
                     "value": "ClearLog", "color": "scheduler-on"},
                    {"label": t("Gui.Button.ScrollON"),
                     "value": "ScrollON", "color": "scheduler-on"},
                    {"label": t("Gui.Button.ScrollOFF"),
                     "value": "ScrollOFF", "color": "scheduler-on"},
                ],
                onclick=[
                    self.alas_logs.reset,
                    lambda: self.alas_logs.set_scroll(True),
                    lambda: self.alas_logs.set_scroll(False),
                ],
            )
        ], size="auto 1fr auto").style("container-overview-group")

        running = put_column([
            put_text(t("Gui.Overview.Running")).style("group-overview-title"),
            put_html('<hr class="hr-group">'),
            self.alas_running,
        ], size="auto auto 1fr").style("container-overview-group")

        pending = put_column([
            put_text(t("Gui.Overview.Pending")).style("group-overview-title"),
            put_html('<hr class="hr-group">'),
            self.alas_pending,
        ], size="auto auto 1fr").style("container-overview-group")

        waiting = put_column([
            put_text(t("Gui.Overview.Waiting")).style("group-overview-title"),
            put_html('<hr class="hr-group">'),
            self.alas_waiting,
        ], size="auto auto 1fr").style("container-overview-group")

        if self.is_mobile:
            self.content.append(
                put_column([
                    scheduler,
                    running,
                    pending,
                    waiting,
                ], size="auto 7.75rem 13rem 13rem"),
                put_column([
                    log,
                    self.alas_logs.output
                ], size="auto 1fr").style("height: 100%; overflow-y: auto")
            )
        else:
            self.content.append(
                put_row([
                    put_column([
                        scheduler,
                        running,
                        pending,
                        waiting,
                    ], size="auto 7.75rem minmax(7.75rem, 13rem) minmax(7.75rem, 1fr)"
                    ).style("height: 100%; overflow-y: auto"),
                    put_column([
                        log,
                        self.alas_logs.output
                    ], size="auto 1fr").style("height: 100%; overflow-y: auto"),
                ], size="minmax(16rem, 20rem) minmax(24rem, 1fr)"
                ).style("height: 100%; overflow-y: auto"),
            )

        def refresh_overiew_tasks(self: AlasGUI):
            while True:
                yield self.alas_update_overiew_tasks()

        self.task_handler.add(refresh_overiew_tasks(self), 20, True)

        def put_log(self: AlasGUI):
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

        self.task_handler.add(put_log(self), 0.2, True)

    def _alas_thread_wait_config_change(self) -> None:
        paths = []
        for path, d in deep_iter(ALAS_ARGS, depth=3):
            if d['type'] == 'disable':
                continue
            paths.append(path_to_idx['.'.join(path)])
        while self.alive:
            try:
                val = pin_wait_change(paths)
                self.modified_config_queue.put(val)
            except SessionClosedException:
                break

    def _alas_thread_update_config(self) -> None:
        modified = {}
        while self.alive:
            try:
                d = self.modified_config_queue.get(timeout=10)
                config_name = self.alas_name
            except queue.Empty:
                continue
            modified[idx_to_path[d['name']]] = parse_pin_value(d['value'])
            while True:
                try:
                    d = self.modified_config_queue.get(timeout=1)
                    modified[idx_to_path[d['name']]] = parse_pin_value(d['value'])
                except queue.Empty:
                    config = read_file(filepath_config(config_name))
                    for k in modified.keys():
                        deep_set(config, k, modified[k])
                    logger.info(f'Save config {filepath_config(config_name)}, {dict_to_kv(modified)}')
                    write_file(filepath_config(config_name), config)
                    toast(t("Gui.Toast.ConfigSaved"),
                          duration=1, position='right', color='success')
                    modified = {}
                    break

    def alas_update_status(self) -> None:
        if hasattr(self, 'alas'):
            if self.alas.process.is_alive():
                self.set_status(1)
            elif len(self.alas.log) == 0 or self.alas.log[-1] == "Scheduler stopped.\n":
                self.set_status(2)
            else:
                self.set_status(-1)
        else:
            self.set_status(0)

    def alas_update_overiew_tasks(self) -> None:
        self.alas_config.load()
        self.alas_config.get_next_task()

        if len(self.alas_config.pending_task) >= 1:
            if self.alas.process.is_alive():
                running = self.alas_config.pending_task[:1]
                pending = self.alas_config.pending_task[1:]
            else:
                running = []
                pending = self.alas_config.pending_task[:]
        else:
            running = []
            pending = []
        waiting = self.alas_config.waiting_task

        def box(func: Function):
            return put_row([
                put_column([
                    put_text(t(f'Task.{func.command}.name')).style("arg-title"),
                    put_text(str(func.next_run)).style("arg-help"),
                ], size="auto auto"),
                put_button(
                    label=t("Gui.Button.Setting"),
                    onclick=lambda: self.alas_set_group(func.command),
                    color="scheduler-on"
                ),
            ], size="1fr auto").style("container-args")

        no_task_style = "text-align:center; font-size: 0.875rem; color: darkgrey;"

        if running:
            self.alas_running.reset(*[box(task) for task in running])
        else:
            self.alas_running.reset(
                put_text(t("Gui.Overview.NoTask")).style(no_task_style)
            )
        if pending:
            self.alas_pending.reset(*[box(task) for task in pending])
        else:
            self.alas_pending.reset(
                put_text(t("Gui.Overview.NoTask")).style(no_task_style)
            )
        if waiting:
            self.alas_waiting.reset(*[box(task) for task in waiting])
        else:
            self.alas_waiting.reset(
                put_text(t("Gui.Overview.NoTask")).style(no_task_style)
            )

    # Develop
    def dev_set_menu(self) -> None:
        self.init_menu(collapse_menu=False, name="Develop")

        self.menu.append(
            put_buttons([
                {"label": t("Gui.MenuDevelop.Translate"),
                 "value": "Translate", "color": "menu"}
            ], onclick=[self.dev_translate]).style(f'--menu-Translate--'),

            # put_buttons([
            #     {"label": t("Gui.MenuDevelop.Something"),
            #      "value": "Something", "color": "menu"}
            # ], onclick=[self.dev_something]).style(f'--menu-Something--'),
        )

    def dev_translate(self) -> None:
        go_app('translate', new_window=True)
        lang.TRANSLATE_MODE = True
        run_js("location.reload();")

    # Aside UI route

    def ui_develop(self) -> None:
        self.init_aside(name="Develop")
        self.title.reset(f"{t('Gui.Aside.Develop')}")
        self.dev_set_menu()
        self.alas_name = ''

    def ui_alas(self, config_name: str) -> None:
        if config_name == self.alas_name:
            self.expand_menu()
            return
        self.init_aside(name=config_name)
        self.content.reset()
        self.alas_name = config_name
        self.alas = get_alas(config_name)
        self.alas_config = AzurLaneConfig(config_name, '')
        self.alas_update_status()
        self.alas_set_menu()

    def ui_setting(self) -> None:
        toast('Not implemented', position='right', color='error')
        return
        self.init_aside(name="Setting")
        self.alas_name = ''

    def run(self) -> None:
        # setup gui
        set_env(title="Alas", output_animation=False)
        add_css(filepath_css('alas'))
        if self.is_mobile:
            add_css(filepath_css('alas-mobile'))

        self.main_area.show()
        self.set_aside()
        self.collapse_menu()

        if lang.TRANSLATE_MODE:
            lang.reload()

            def _disable():
                lang.TRANSLATE_MODE = False
                run_js("location.reload();")

            toast(_t("Gui.Toast.DisableTranslateMode"), duration=0, position='right', onclick=_disable)

        # show something
        self.content.append(output(output(
            put_markdown("""
            ## AzurLaneAutoScript
            This new UI is still under development.
            if you encounter any error or find a bug, [create new issue](https://github.com/LmeSzinc/AzurLaneAutoScript/issues/new/choose) or `@18870#0856` in discord with error logs.
            You may found logs in python console or browser console (`Ctrl`+`Shift`+`I` - `Console`)
            ![](https://i.loli.net/2021/10/03/5pNYoS8EFcvrhIs.png)
            ![](https://i.loli.net/2021/10/03/5xCaATjl6oK7S1f.png)

            ## Join in translation
            Go `Develop` - `Translate`
            """, strip_indent=12)).style('welcome')))

        # temporary buttons, there is no setting page now :(
        self.content.append(
            put_text("Select your language").style("text-align: center"),
            put_buttons(
                ["zh-CN", "zh-TW", "en-US", "ja-JP"],
                onclick=lambda s: lang.set_language(s, True)
            ).style("text-align: center")
        )

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

        def refresh_status(self: AlasGUI):
            while True:
                yield self.alas_update_status()

        self.task_handler.add(refresh_status(self), 2)
        self.task_handler.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Alas web service')
    parser.add_argument("-d", "--debug", action="store_true",
                        help="show log")
    parser.add_argument('-p', '--port', type=int, default=22267,
                        help='Port to listen. Default to 22267')
    parser.add_argument('-b', '--backend', type=str, default='starlette',
                        help='Backend framework of web server, starlette or tornado. Default to starlette')
    parser.add_argument('-k', '--key', type=str, default='',
                        help='Password of alas. No password by default')
    args = parser.parse_args()

    Alas.manager = Manager()
    
    def index():
        if args.key != '' and not login(args.key):
            logger.warning(f"{info.user_ip} login failed.")
            time.sleep(2)
            run_js('location.reload();')
            return
        AlasGUI().run()


    if args.backend == 'starlette':
        from pywebio.platform.fastapi import start_server
    else:
        from pywebio.platform.tornado import start_server

    try:
        start_server([index, translate], port=args.port, debug=args.debug)
    finally:
        for alas in all_alas.values():
            alas.stop()
        logger.info("Alas closed.")
