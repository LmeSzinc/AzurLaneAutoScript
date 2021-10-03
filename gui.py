import time
import queue
import logging
from multiprocessing import Process, Manager

from pywebio.exceptions import *
from pywebio.input import *
from pywebio.output import *
from pywebio.pin import *
from pywebio.session import *

from module.config.utils import *

import module.webui.lang as lang
from module.webui.widgets import *
from module.webui.utils import QueueHandler, add_css, Icon, filepath_css, get_output, parse_pin_value, thread_with_exception as Thread
from module.webui.lang import t, _t
from module.webui.translate import translate

all_alas = {}
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
    formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    webconsole = logging.StreamHandler(stream=qh)
    webconsole.setFormatter(formatter)
    logging.getLogger('alas').addHandler(webconsole)

    # Run alas
    from alas import AzurLaneAutoScript
    AzurLaneAutoScript(config_name=config_name).loop()





class Alas():
    def __init__(self, config_name='alas'):
        self.config_name = config_name
        self.manager = Manager()
        self.log_queue = self.manager.Queue()
        self.log = []
        self.log_max_length = 500
        self.log_reduce_length = 100
        self.process = Process()

    def start(self):
        if not self.process.is_alive():
            self.process = Process(target=run_alas, args=(self.config_name, self.log_queue,))
            self.process.start()
            self.thd_log_queue_handler = Thread(target=self._thread_log_queue_handler)
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
# Using full path name will transfered ~16KB per command, 
# may lag when remote control or in bad internet condition.
# Use ~4KB after doing this.
path_to_idx = {}
idx_to_path = {}
i = 0
for l, _ in deep_iter(ALAS_ARGS, depth=3):
    path_to_idx['.'.join(l)] = f'a{i}'
    idx_to_path[f'a{i}'] = '.'.join(l)
    i += 1
del i, l


class AlasGUI:
    alas: Alas

    def __init__(self):
        lang.reload()
        self.modified_config_queue = queue.Queue()
        self._thread_kill_after_leave = []

    def set_aside(self):
        self.aside.reset()

        # note: value doesn't matters if onclick is a list, button binds to functions in order.
        # when onclick isn't a list, value will pass to function.
        
        self.aside.append(
            # put_icon_buttons(Icon.INSTALL, buttons=[{"label": t("Gui.Aside.Install"), "value": "install", "color": "aside"}], onclick=[self.ui_install]),
            put_icon_buttons(Icon.DEVELOP, buttons=[{"label": t("Gui.Aside.Develop"), "value": "develop", "color": "aside"}], onclick=[self.ui_develop]),
            # put_icon_buttons(Icon.PERFORMANCE, buttons=[{"label": t("Gui.Aside.Performance"), "value": "performance", "color": "aside"}], onclick=[self.ui_performance]),
        )

        # TODO: generate this from config
        self.aside.append(
            put_icon_buttons(Icon.RUN, buttons=[{"label": "Alas", "value": "alas", "color": "aside"}], onclick=self.ui_alas),
            put_icon_buttons(Icon.RUN, buttons=[{"label": "Alas2", "value": "alas2", "color": "aside"}], onclick=self.ui_alas),
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
                {"label": t("Gui.MenuAlas.Overview"), "value": "Overview", "color": "menu"}
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
                        {"label": t(f'Task.{task}.name'), "value": task, "color": "menu"}
                    ], onclick=self.alas_set_group) for task in l]
                )
            )

    def alas_set_group(self, task:str):
        """
        Set arg groups from dict
        """
        self.title.reset(f"{self.alas_name} - {t(f'Task.{task}.name')}")
        self.contents.reset()
        self.kill_thread()

        group_area = output()
        navigator = output()
        menu_alas = put_row([
            None,
            group_area,
            navigator,
        ], size=".5fr minmax(25rem, 5fr) 2fr")

        self.contents.append(menu_alas)

        config = read_file(filepath_config(self.alas_name))

        for group, arg_dict in deep_iter(ALAS_ARGS[task], depth=1):
            group = group[0]
            help = t(f"{group}._info.help")
            if help == "" or not help:
                help = None
            arg_group = put_group(t(f"{group}._info.name"), help)
            group_area.append(output(arg_group))
            for arg, d in deep_iter(arg_dict, depth=1):
                arg = arg[0]
                type = d['type']
                value = deep_get(config, f'{task}.{group}.{arg}', d['value'])

                # Option
                options = deep_get(d, 'option', None)
                if options:
                    option = []
                    for o in options:
                        d = {"label": t(f"{group}.{arg}.{o}"), "value": o}
                        if value == o:
                            d["selected"] = True
                        option.append(d)
                else:
                    option = None
                
                # Help
                arg_help = t(f"{group}.{arg}.help")
                if arg_help == "" or not arg_help:
                    arg_help = None

                arg_group.append(output(get_output(
                    type=type,
                    name=path_to_idx[f"{task}.{group}.{arg}"],
                    title=t(f"{group}.{arg}.name"),
                    help=arg_help,
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
                put_buttons(['Start', 'Stop', 'Scroll ON', 'Scroll OFF'],
                    onclick=[self.alas.start, self.alas.stop, lambda: self.logs.set_scroll(True), lambda: self.logs.set_scroll(False)]),
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
        for l, d in deep_iter(ALAS_ARGS, depth=3):
            if d['type'] == 'disable':
                continue
            paths.append(path_to_idx['.'.join(l)])
        while True:
            try:
                self.modified_config_queue.put(pin_wait_change(paths))
            except SessionClosedException:
                break

    def _alas_thread_update_config(self):
        modified = {}
        while self.alive:
            try:
                d = self.modified_config_queue.get(timeout=10)
            except:
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
                    toast(t("Gui.Toast.ConfigSaved"), duration=1, position='right')
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
        self.kill_thread()

        self.menu.append(
            put_buttons([
                {"label": t("Gui.MenuDevelop.Translate"), "value": "Translate", "color": "menu"}
            ], onclick=[self.dev_translate]),

            # put_buttons([
            #     {"label": t("Gui.MenuDevelop.Something"), "value": "Something", "color": "menu"}
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



    def run(self):
        # setup gui
        set_env(title="Alas", output_animation=False)
        add_css(filepath_css('alas'))
        self.aside = output().style("container-aside")
        self.menu = output().style("container-menu")
        self.contents = output().style("container-contents")
        self.title = output().style("title-text-title")
        self.logs = ScrollableCode()

        self.btn_setting = put_icon_buttons(Icon.SETTING, 
                            buttons=[{"label": t("Gui.Aside.Setting"), "value": "setting", "color": "aside"}],
                            onclick=[self.ui_setting],
                        ).style("aside-icon-setting")

        self.main = output(
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
                        self.btn_setting,
                    ], size="auto 1fr auto").style("container-aside"),
                    self.menu,
                    self.contents,
                ], size="auto 12rem 1fr").style("container-main"),
            ], size="auto 1fr").style("container-all")
        ).style("container-gui")
        put_row(self.main) # output an OutputHandler()
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
            You may found logs in python console or browser console (`F12`-`console`)
            ![](https://i.loli.net/2021/10/03/5pNYoS8EFcvrhIs.png)
            ![](https://i.loli.net/2021/10/03/5xCaATjl6oK7S1f.png)

            ## Join in translation
            Go `Develop` - `Translate`, or [here](./?app=translate)
            """, strip_indent=12)).style('welcome')))
        
        # temporary buttons, there is no setting page now :(
        self.contents.append(put_text("Select your language").style("text-align: center"))
        self.contents.append(put_buttons(
            ["zh-CN", "zh-TW", "en-US", "ja-JP"]
            , onclick=lambda s: lang.set_language(s, True)
        ).style("text-align: center"))
        
        

        # detect config change
        _thread_wait_config_change = Thread(target=self._alas_thread_wait_config_change)
        register_thread(_thread_wait_config_change)
        _thread_wait_config_change.start()

        # save config
        _thread_save_config = Thread(target=self._alas_thread_update_config)
        register_thread(_thread_save_config)
        _thread_save_config.start()

        hold()



if __name__ == "__main__":
    def index():
        AlasGUI().run()
    
    port = 80
    debug = False
    backend = 'starlette'

    if backend == 'starlette':
        # pip install starlette uvicorn[standard]
        from pywebio.platform.fastapi import start_server
    else:
        from pywebio.platform.tornado import start_server
    
    start_server([index, translate], port=port, debug=debug)
    
    for alas in all_alas.values():
        alas.stop()

    print("Alas closed.")