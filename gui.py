import argparse
import logging
import queue
import time
from multiprocessing import Manager, Process

from pywebio.exceptions import *
from pywebio.session import defer_call, go_app, info, register_thread, set_env

from module.logger import logger  # Change folder
import module.webui.lang as lang
from module.config.config import AzurLaneConfig, Function
from module.config.config_updater import ConfigUpdater
from module.config.utils import *
from module.webui.lang import _t, t
from module.webui.translate import translate
from module.webui.utils import Icon, QueueHandler
from module.webui.utils import ThreadWithException as Thread
from module.webui.utils import (active_button, add_css, collapse_menu,
                                expand_menu, filepath_css, get_output, login,
                                parse_pin_value)
from module.webui.widgets import *

all_alas = {}
config_updater = ConfigUpdater()


def get_alas(config_name):
    """
    Create a new alas if not exists.
    """
    if config_name not in all_alas:
        all_alas[config_name] = Alas(config_name)
    return all_alas[config_name]


def run_alas(config_name, q):
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
    def __init__(self, config_name='alas'):
        self.config_name = config_name
        self.manager = Manager()
        self.log_queue = self.manager.Queue()
        self.log = []
        self.log_max_length = 500
        self.log_reduce_length = 100
        self.process = Process()
        self.thd_log_queue_handler = Thread()

    def start(self):
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

    def stop(self):
        if self.process.is_alive():
            self.process.terminate()
            self.log.append("Scheduler stopped.\n")
        if self.thd_log_queue_handler.is_alive():
            self.thd_log_queue_handler.stop()

    def _thread_log_queue_handler(self):
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


def shorten_path():
    i = 0
    for list_path, _ in deep_iter(ALAS_ARGS, depth=3):
        path_to_idx['.'.join(list_path)] = f'a{i}'
        idx_to_path[f'a{i}'] = '.'.join(list_path)
        i += 1


shorten_path()


class AlasGUI:
    alas: Alas

    def __init__(self):
        # modified keys, return values of pin_wait_change()
        self.modified_config_queue = queue.Queue()
        # list of threads, kill all when call `kill_thread()`
        self._thread_kill_after_leave = []
        # alas config name
        self.alas_name = ''
        self.alive = True
        self.aside = output()
        self.menu = output().style("container-menu")
        self.content = output().style("container-content")
        self.title = output().style("title-text-title")
        self.status = output().style("title-status")
        self._status = 0
        self.header = put_row([
            put_html(Icon.ALAS).style("title-icon-alas"),
            put_text("Alas").style("title-text-alas"),
            self.status,
            self.title,
        ], size="5.6rem 3.75rem 8rem minmax(5rem, 65rem)").style("container-title")

        self.asides = put_column([
            self.aside,
            None,
            put_icon_buttons(
                Icon.SETTING,
                buttons=[
                    {"label": t("Gui.Aside.Setting"),
                    "value": "setting", "color": "aside"}],
                onclick=[self.ui_setting],
            ).style("aside-icon-setting"),
        ], size="auto 1fr auto").style("container-aside")

        if info.user_agent.is_mobile:
            self.contents = put_row([
                self.asides,
                self.menu,
                None,
                self.content,
            ], size="auto auto 1fr").style("container-main")
        else:
            self.contents = put_row([
                self.asides,
                self.menu,
                self.content,
            ], size="auto auto 1fr").style("container-main")

        self.main_area = output(
            put_column([
                self.header,
                self.contents,
            ], size="auto 1fr").style("container-all")
        ).style("container-gui")

        self.alas_logs = ScrollableCode()
        self.alas_running = output().style("container-overview-task")
        self.alas_pending = output().style("container-overview-task")
        self.alas_waiting = output().style("container-overview-task")
        

    def set_aside(self):
        self.aside.reset()

        # note: value doesn't matters if onclick is a list, button binds to functions in order.
        # when onclick isn't a list, value will pass to function.

        self.aside.append(
            # put_icon_buttons(Icon.INSTALL, buttons=[{"label": t(
            #     "Gui.Aside.Install"), "value": "install", "color": "aside"}], onclick=[self.ui_install]),
            put_icon_buttons(Icon.DEVELOP, buttons=[{"label": t(
                "Gui.Aside.Develop"), "value": "develop", "color": "aside"}], onclick=[self.ui_develop]),
            # put_icon_buttons(Icon.PERFORMANCE, buttons=[{"label": t(
            #     "Gui.Aside.Performance"), "value": "performance", "color": "aside"}], onclick=[self.ui_performance]),
        )

        self.aside.append(
            *[put_icon_buttons(
                Icon.RUN, buttons=[{"label": name, "value": name, "color": "aside"}],
                onclick=self.ui_alas)
                for name in alas_instance()]
        )

    def kill_thread(self):
        thd: Thread

        for thd in self._thread_kill_after_leave:
            thd.stop()

    def set_status(self, status:int):
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
                put_loading(color='success').style("width:1.5rem;height:1.5rem;border:.2em solid currentColor;border-right-color:transparent;"),
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

    def alas_set_menu(self):
        """
        Set menu for alas
        """
        self.menu.reset()
        self.content.reset()
        self.kill_thread()

        self.menu.append(
            put_buttons([
                {"label": t("Gui.MenuAlas.Overview"),
                 "value": "Overview", "color": "menu"}
            ], onclick=[self.alas_overview]).style(f'--menu-Overview--'),
            put_buttons([
                {"label": t("Gui.MenuAlas.Log"),
                 "value": "Log", "color": "menu"}
            ], onclick=[self.alas_log]).style(f'--menu-Log--'),
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

    def alas_set_group(self, task):
        """
        Set arg groups from dict
        """
        self.title.reset(f"{t(f'Task.{task}.name')}")
        self.content.reset()
        self.kill_thread()
        active_button('menu', task)
        collapse_menu()

        group_area = output()
        navigator = output()

        if info.user_agent.is_mobile:
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
            group_area.append(arg_group)
            for arg, d in deep_iter(arg_dict, depth=1):
                arg = arg[0]
                arg_type = d['type']
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

                if info.user_agent.is_mobile:
                    width = '8rem'
                else:
                    width = '12rem'

                arg_group.append(get_output(
                    arg_type=arg_type,
                    name=path_to_idx[f"{task}.{group}.{arg}"],
                    title=t(f"{group}.{arg}.name"),
                    arg_help=arg_help,
                    value=value,
                    options=option,
                    width=width,
                ))

    def alas_overview(self):
        self.title.reset(f"{t(f'Gui.MenuAlas.Overview')}")
        self.content.reset()
        self.kill_thread()
        active_button('menu', 'Overview')
        collapse_menu()

        scheduler = put_row([
            put_text(t("Gui.Overview.Scheduler")).style(
                "font-size: 1.5rem; margin: 0 .5rem 0;"),
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
                "font-size: 1.5rem; margin: 0 .5rem 0;"),
            None,
            put_buttons(
                buttons=[
                    {"label": t("Gui.Button.ScrollON"), 
                    "value": "ScrollON", "color": "scheduler-on"},
                    {"label": t("Gui.Button.ScrollOFF"), 
                    "value": "ScrollOFF", "color": "scheduler-on"},
                ],
                onclick=[
                    lambda: self.alas_logs.set_scroll(True),
                    lambda: self.alas_logs.set_scroll(False),
                ]
            )
        ], size="auto 1fr auto").style("container-overview-group")

        running = put_column([
            put_text(t("Gui.Overview.Running")).style("group-title"),
            put_html('<hr class="hr-group">'),
            self.alas_running,
        ], size="auto auto 1fr").style("container-overview-group")

        pending = put_column([
            put_text(t("Gui.Overview.Pending")).style("group-title"),
            put_html('<hr class="hr-group">'),
            self.alas_pending,
        ], size="auto auto 1fr").style("container-overview-group")

        waiting = put_column([
            put_text(t("Gui.Overview.Waiting")).style("group-title"),
            put_html('<hr class="hr-group">'),
            self.alas_waiting,
        ], size="auto auto 1fr").style("container-overview-group")

        if info.user_agent.is_mobile:
            self.content.append(
                put_column([
                    scheduler,
                    running,
                    pending,
                    waiting,
                ], size="auto 7.25rem 12.5rem 12.5rem"),
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
                    ], size="auto 7.25rem minmax(7.25rem, 13rem) minmax(7.25rem, 1fr)"
                    ).style("height: 100%; overflow-y: auto"),
                    put_column([
                        log,
                        self.alas_logs.output
                    ], size="auto 1fr").style("height: 100%; overflow-y: auto"),
                ], size="minmax(16rem, 20rem) minmax(24rem, 1fr)"
                ).style("height: 100%; overflow-y: auto"),
            )

        thd_task = Thread(target=self._alas_thread_refresh_overiew_tasks)
        register_thread(thd_task)
        thd_task.start()
        self._thread_kill_after_leave.append(thd_task)

        thd_log = Thread(target=self._alas_thread_put_log)
        register_thread(thd_log)
        thd_log.start()
        self._thread_kill_after_leave.append(thd_log)

    def alas_log(self):
        self.title.reset(f"{t(f'Gui.MenuAlas.Log')}")
        self.content.reset()
        self.kill_thread()
        active_button('menu', 'Log')
        collapse_menu()

        self.content.append(
            put_column([
                self.alas_logs.output,
                put_buttons(
                    buttons=[
                        {'label': t('Gui.Button.Start'), 'value': 'Start'},
                        {'label': t('Gui.Button.Stop'), 'value': 'Stop'},
                        {'label': t('Gui.Button.ScrollON'), 'value': 'ScrollON'},
                        {'label': t('Gui.Button.ScrollOFF'), 'value': 'ScrollOFF'},
                    ],
                    onclick=[
                        self.alas.start,
                        self.alas.stop,
                        lambda: self.alas_logs.set_scroll(True),
                        lambda: self.alas_logs.set_scroll(False)
                    ]
                ),
            ], size="auto 3rem").style("height: 100%")
        )
        thd = Thread(target=self._alas_thread_put_log)
        register_thread(thd)
        thd.start()
        self._thread_kill_after_leave.append(thd)

    def _alas_thread_wait_config_change(self):
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

    def _alas_thread_update_config(self):
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

    def _alas_thread_put_log(self):
        last_idx = len(self.alas.log)
        self.alas_logs.append(''.join(self.alas.log))
        self.lines = 0
        time.sleep(1)
        while True:
            time.sleep(0.2)
            idx = len(self.alas.log)
            if idx < last_idx:
                last_idx -= self.alas.log_reduce_length
            if idx != last_idx:
                try:
                    self.alas_logs.append(''.join(self.alas.log[last_idx:idx]))
                except SessionNotFoundException:
                    break
                self.lines += idx - last_idx
                last_idx = idx

    def alas_update_status(self):
        if hasattr(self, 'alas'):
            if self.alas.process.is_alive():
                self.set_status(1)
            elif len(self.alas.log) == 0 or self.alas.log[-1] == "Scheduler stopped.\n":
                self.set_status(2)
            else:
                self.set_status(-1)
        else:
            self.set_status(0)

    def _alas_thread_refresh_status(self):
        while self.alive:
            self.alas_update_status()
            time.sleep(5)

    def alas_update_overiew_tasks(self):
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

        def box(func:Function):
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

    def _alas_thread_refresh_overiew_tasks(self):
        while self.alive:
            self.alas_update_overiew_tasks()
            time.sleep(20)

    # Develop

    def dev_set_menu(self):
        self.menu.reset()
        self.title.reset(f"{t('Gui.Aside.Develop')}")
        self.kill_thread()

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

    def dev_translate(self):
        go_app('translate', new_window=True)
        lang.TRANSLATE_MODE = True
        run_js("location.reload();")

    # Aside UI route

    def ui_develop(self):
        expand_menu()
        self.dev_set_menu()
        active_button('aside', 'develop')
        self.alas_name = ''

    def ui_performance(self):
        toast('Not implemented', position='right', color='error')

    def ui_alas(self, config_name):
        if config_name == self.alas_name:
            expand_menu()
            return
        self.alas_name = config_name
        self.alas = get_alas(config_name)
        self.alas_config = AzurLaneConfig(config_name, '')
        self.title.reset()
        self.alas_update_status()
        active_button('aside', config_name)
        self.alas_set_menu()

    def ui_setting(self):
        toast('Not implemented', position='right', color='error')
        return
        expand_menu()
        active_button('aside', 'setting')
        self.alas_name = ''

    def stop(self):
        self.kill_thread()
        self.alive = False

    def run(self):
        # setup gui
        set_env(title="Alas", output_animation=False)
        add_css(filepath_css('alas'))
        defer_call(self.stop)
        self.main_area.show()
        self.set_aside()
        collapse_menu()
        if info.user_agent.is_mobile:
            add_css(filepath_css('alas-mobile'))

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

        # refresh status
        _thread_refresh_status = Thread(
            target=self._alas_thread_refresh_status)
        register_thread(_thread_refresh_status)
        _thread_refresh_status.start()


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
