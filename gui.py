import argparse
import logging
import queue
import time
from multiprocessing import Manager, Process

from pywebio.exceptions import *
from pywebio.session import defer_call, go_app, register_thread, set_env

import module.webui.lang as lang
from module.config.config_updater import ConfigUpdater
from module.config.utils import *
from module.logger import logger  # Change folder
from module.webui.lang import _t, t
from module.webui.translate import translate
from module.webui.utils import Icon, QueueHandler
from module.webui.utils import ThreadWithException as Thread
from module.webui.utils import (add_css, filepath_css, get_output,
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
        self.process.terminate()
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
        lang.reload()
        self.modified_config_queue = queue.Queue()
        self._thread_kill_after_leave = []
        self.alas_name = 'alas'
        self.alive = True
        self.aside = output().style("container-aside")
        self.menu = output().style("container-menu")
        self.contents = output().style("container-contents")
        self.title = output().style("title-text-title")
        self.logs = ScrollableCode()
        self.main_area = output()

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

        # TODO: generate this from config
        self.aside.append(
            put_icon_buttons(Icon.RUN, buttons=[
                {"label": "Alas", "value": "alas", "color": "aside"}], onclick=self.ui_alas),
            put_icon_buttons(Icon.RUN, buttons=[
                {"label": "Alas2", "value": "alas2", "color": "aside"}], onclick=self.ui_alas),
        )

    def kill_thread(self):
        thd: Thread

        for thd in self._thread_kill_after_leave:
            thd.stop()

    # Alas

    def alas_set_menu(self):
        """
        Set menu for alas
        """
        self.menu.reset()
        self.contents.reset()
        self.kill_thread()

        self.menu.append(
            put_buttons([
                {"label": t("Gui.MenuAlas.Overview"),
                 "value": "Overview", "color": "menu"}
            ], onclick=[self.alas_overview]),
            # put_buttons([
            #     {"label": t("Gui.MenuAlas.Log"), "value": "Log", "color": "menu"}
            # ], onclick=[self.alas_log]),
        )
        for key, l in deep_iter(ALAS_MENU, depth=2):
            # path = '.'.join(key)
            menu = key[1]
            self.menu.append(
                put_collapse(t(f"Menu.{menu}.name"),
                             [put_buttons([
                                 {"label": t(f'Task.{task}.name'),
                                  "value": task, "color": "menu"}
                             ], onclick=self.alas_set_group) for task in l]
                             )
            )

    def alas_set_group(self, task):
        """
        Set arg groups from dict
        """
        self.title.reset(f"{self.alas_name} - {t(f'Task.{task}.name')}")
        self.contents.reset()
        self.kill_thread()

        group_area = output()
        navigator = output()
        content_alas = put_row([
            None,
            group_area,
            navigator,
        ], size=".5fr minmax(25rem, 5fr) 2fr")

        self.contents.append(content_alas)

        config = config_updater.update_config(self.alas_name)

        for group, arg_dict in deep_iter(ALAS_ARGS[task], depth=1):
            group = group[0]
            group_help = t(f"{group}._info.help")
            if group_help == "" or not group_help:
                group_help = None
            arg_group = put_group(t(f"{group}._info.name"), group_help)
            group_area.append(output(arg_group))
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

                arg_group.append(output(get_output(
                    arg_type=arg_type,
                    name=path_to_idx[f"{task}.{group}.{arg}"],
                    title=t(f"{group}.{arg}.name"),
                    arg_help=arg_help,
                    value=value,
                    options=option,
                )))

    def alas_overview(self):
        self.title.reset(f"{self.alas_name} - {t(f'Gui.MenuAlas.Overview')}")
        self.contents.reset()
        self.kill_thread()

        self.contents.append(
            put_column([
                put_html(self.logs._html),
                put_buttons(
                    buttons=['Start', 'Stop', 'Scroll ON', 'Scroll OFF'],
                    onclick=[
                        self.alas.start,
                        self.alas.stop,
                        lambda: self.logs.set_scroll(True),
                        lambda: self.logs.set_scroll(False)
                    ]
                ),
            ], size="auto 3rem").style("height: 100%")
        )
        thd = Thread(target=self._alas_thread_put_log)
        register_thread(thd)
        thd.start()
        self._thread_kill_after_leave.append(thd)

    def alas_log(self):
        toast('Not implemented', position='right', color='error')

    def _alas_thread_wait_config_change(self):
        paths = []
        for path, d in deep_iter(ALAS_ARGS, depth=3):
            if d['type'] == 'disable':
                continue
            paths.append(path_to_idx['.'.join(path)])
        while self.alive:
            try:
                val = pin_wait_change(paths, timeout=10)
                if val is None:
                    continue
                self.modified_config_queue.put(val)
            except SessionClosedException:
                break

    def _alas_thread_update_config(self):
        modified = {}
        while self.alive:
            try:
                d = self.modified_config_queue.get(timeout=10)
            except queue.Empty:
                continue
            modified[idx_to_path[d['name']]] = parse_pin_value(d['value'])
            while True:
                try:
                    d = self.modified_config_queue.get(timeout=1)
                    modified[idx_to_path[d['name']]] = parse_pin_value(d['value'])
                except queue.Empty:
                    config = read_file(filepath_config(self.alas_name))
                    for k in modified.keys():
                        deep_set(config, k, modified[k])
                    write_file(filepath_config(self.alas_name), config)
                    toast(t("Gui.Toast.ConfigSaved"),
                          duration=1, position='right', color='success')
                    break

    def _alas_thread_put_log(self):
        last_idx = len(self.alas.log)
        self.logs.append(''.join(self.alas.log))
        self.lines = 0
        time.sleep(1)
        while True:
            time.sleep(0.2)
            idx = len(self.alas.log)
            if idx < last_idx:
                last_idx -= self.alas.log_reduce_length
            if idx != last_idx:
                try:
                    self.logs.append(''.join(self.alas.log[last_idx:idx]))
                except SessionNotFoundException:
                    break
                self.lines += idx - last_idx
                last_idx = idx

    # Develop

    def dev_set_menu(self):
        self.menu.reset()
        self.contents.reset()
        self.title.reset(f"{t('Gui.Aside.Develop')}")
        self.kill_thread()

        self.menu.append(
            put_buttons([
                {"label": t("Gui.MenuDevelop.Translate"),
                 "value": "Translate", "color": "menu"}
            ], onclick=[self.dev_translate]),

            # put_buttons([
            #     {"label": t("Gui.MenuDevelop.Something"),
            #      "value": "Something", "color": "menu"}
            # ], onclick=[self.dev_something]),
        )

    def dev_translate(self):
        go_app('translate', new_window=True)
        lang.TRANSLATE_MODE = True
        run_js("location.reload();")

    # Aside UI route

    def ui_install(self):
        toast('Not implemented', position='right', color='error')

    def ui_develop(self):
        self.dev_set_menu()

    def ui_performance(self):
        toast('Not implemented', position='right', color='error')

    def ui_alas(self, config_name):
        self.alas_name = config_name
        self.alas = get_alas(config_name)
        self.title.reset(f"{self.alas_name}")
        self.alas_set_menu()

    def ui_setting(self):
        toast('Not implemented', position='right', color='error')

    def stop(self):
        self.alive = False

    def run(self):
        # setup gui
        set_env(title="Alas", output_animation=False)
        add_css(filepath_css('alas'))
        defer_call(self.stop)

        self.main_area = output(
            put_column([
                put_row([
                    put_html(Icon.ALAS).style("title-icon-alas"),
                    put_text("Alas").style("title-text-alas"),
                    self.title,
                ], size="5.6rem 11.75rem minmax(8rem, 65rem)").style("container-title"),
                put_row([
                    put_column([
                        self.aside,
                        None,
                        put_icon_buttons(
                            Icon.SETTING,
                            buttons=[
                                {"label": t("Gui.Aside.Setting"),
                                 "value": "setting", "color": "aside"}],
                            onclick=[self.ui_setting],
                        ).style("aside-icon-setting"),
                    ], size="auto 1fr auto").style("container-aside"),
                    self.menu,
                    self.contents,
                ], size="auto 12rem 1fr").style("container-main"),
            ], size="auto 1fr").style("container-all")
        ).style("container-gui")
        put_row(self.main_area)  # output an OutputHandler()
        self.set_aside()

        if lang.TRANSLATE_MODE:
            def _disable():
                lang.TRANSLATE_MODE = False
                run_js("location.reload();")

            toast(_t("Gui.Toast.DisableTranslateMode"), duration=0, position='right', onclick=_disable)

        # show something
        self.contents.append(output(output(
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
        self.contents.append(
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
        _thread_save_config = Thread(target=self._alas_thread_update_config)
        register_thread(_thread_save_config)
        _thread_save_config.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Alas web service')
    parser.add_argument("-d", "--debug", action="store_true",
                        help="show log")
    parser.add_argument('-p', '--port', type=int, default=22267,
                        help='Port to listen. Default to 22267')
    parser.add_argument('-b', '--backend', type=str, default='starlette',
                        help='Backend framework of web server, starlette or tornado. Default to starlette')
    args = parser.parse_args()

    def index():
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
