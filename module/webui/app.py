import argparse
import queue
import threading
import time
from datetime import datetime
from typing import Dict, List

import module.webui.lang as lang
from module.config.config import AzurLaneConfig, Function
from module.config.utils import (
    alas_instance,
    deep_get,
    deep_iter,
    deep_set,
    dict_to_kv,
    filepath_args,
    filepath_config,
    read_file,
    write_file,
)
from module.logger import logger
from module.ocr.rpc import start_ocr_server_process, stop_ocr_server_process
from module.webui.base import Frame
from module.webui.discord_presence import close_discord_rpc, init_discord_rpc
from module.webui.fastapi import asgi_app
from module.webui.lang import _t, t
from module.webui.pin import put_input, put_select
from module.webui.process_manager import ProcessManager
from module.webui.remote_access import RemoteAccess
from module.webui.setting import State
from module.webui.translate import translate
from module.webui.updater import updater
from module.webui.utils import (
    Icon,
    Switch,
    TaskHandler,
    add_css,
    filepath_css,
    get_localstorage,
    get_window_visibility_state,
    login,
    parse_pin_value,
    raise_exception,
    re_fullmatch,
)
from module.webui.widgets import (
    BinarySwitchButton,
    RichLog,
    get_output,
    put_icon_buttons,
    put_none,
)
from pywebio import config as webconfig
from pywebio.exceptions import SessionClosedException
from pywebio.output import (
    clear,
    close_popup,
    popup,
    put_button,
    put_buttons,
    put_collapse,
    put_column,
    put_error,
    put_html,
    put_link,
    put_loading,
    put_markdown,
    put_row,
    put_scope,
    put_table,
    put_text,
    put_warning,
    toast,
    use_scope,
)
from pywebio.pin import pin, pin_wait_change
from pywebio.session import go_app, info, register_thread, run_js, set_env

task_handler = TaskHandler()


class AlasGUI(Frame):
    ALAS_MENU: Dict[str, Dict[str, List[str]]]
    ALAS_ARGS: Dict[str, Dict[str, Dict[str, Dict[str, str]]]]
    path_to_idx: Dict[str, str] = {}
    idx_to_path: Dict[str, str] = {}
    theme = "default"

    @classmethod
    def shorten_path(cls, prefix="a") -> None:
        """
        Reduce pin_wait_change() command content-length
        Using full path name will transfer ~16KB per command,
        may lag when remote control or in bad internet condition.
        Use ~4KB after doing this.
        Args:
            prefix: all idx need to be a valid html, so a random character here
        """
        cls.ALAS_MENU = read_file(filepath_args("menu"))
        cls.ALAS_ARGS = read_file(filepath_args("args"))
        i = 0
        for list_path, _ in deep_iter(cls.ALAS_ARGS, depth=3):
            cls.path_to_idx[".".join(list_path)] = f"{prefix}{i}"
            cls.idx_to_path[f"{prefix}{i}"] = ".".join(list_path)
            i += 1

    def __init__(self) -> None:
        super().__init__()
        # modified keys, return values of pin_wait_change()
        self.modified_config_queue = queue.Queue()
        # alas config name
        self.alas_name = ""
        self.alas_config = AzurLaneConfig("template")

    @use_scope("aside", clear=True)
    def set_aside(self) -> None:
        # TODO: update put_icon_buttons()
        put_icon_buttons(
            Icon.DEVELOP,
            buttons=[
                {"label": t("Gui.Aside.Develop"), "value": "Develop", "color": "aside"}
            ],
            onclick=[self.ui_develop],
        ),
        for name in alas_instance():
            put_icon_buttons(
                Icon.RUN,
                buttons=[{"label": name, "value": name, "color": "aside"}],
                onclick=self.ui_alas,
            )
        put_icon_buttons(
            Icon.ADD,
            buttons=[
                {"label": t("Gui.Aside.AddAlas"), "value": "AddAlas", "color": "aside"}
            ],
            onclick=[self.ui_add_alas],
        ),

    @use_scope("header_status")
    def set_status(self, state: int) -> None:
        """
        Args:
            state (int):
                1 (running)
                2 (not running)
                3 (warning, stop unexpectedly)
                4 (stop for update)
                0 (hide)
                -1 (*state not changed)
        """
        if state == -1:
            return
        clear()

        if state == 1:
            put_row(
                [
                    put_loading(color="success").style("--loading-border--"),
                    None,
                    put_text(t("Gui.Status.Running")),
                ],
                size="auto 2px 1fr",
            )
        elif state == 2:
            put_row(
                [
                    put_loading(color="secondary").style("--loading-border-fill--"),
                    None,
                    put_text(t("Gui.Status.Inactive")),
                ],
                size="auto 2px 1fr",
            )
        elif state == 3:
            put_row(
                [
                    put_loading(shape="grow", color="warning").style(
                        "--loading-grow--"
                    ),
                    None,
                    put_text(t("Gui.Status.Warning")),
                ],
                size="auto 2px 1fr",
            )
        elif state == 4:
            put_row(
                [
                    put_loading(shape="grow", color="success").style(
                        "--loading-grow--"
                    ),
                    None,
                    put_text(t("Gui.Status.Updating")),
                ],
                size="auto 2px 1fr",
            )

    @classmethod
    def set_theme(cls, theme="default") -> None:
        cls.theme = theme
        State.deploy_config.Theme = theme
        State.theme = theme
        webconfig(theme=theme)

    @use_scope("menu", clear=True)
    def alas_set_menu(self) -> None:
        """
        Set menu
        """
        put_buttons(
            [
                {
                    "label": t("Gui.MenuAlas.Overview"),
                    "value": "Overview",
                    "color": "menu",
                }
            ],
            onclick=[self.alas_overview],
        ).style(f"--menu-Overview--"),

        for key, tasks in deep_iter(self.ALAS_MENU, depth=2):
            # path = '.'.join(key)
            menu = key[1]

            if menu == "Tool":
                _onclick = self.alas_daemon_overview
            else:
                _onclick = self.alas_set_group

            task_btn_list = []
            for task in tasks:
                task_btn_list.append(
                    put_buttons(
                        [
                            {
                                "label": t(f"Task.{task}.name"),
                                "value": task,
                                "color": "menu",
                            }
                        ],
                        onclick=_onclick,
                    ).style(f"--menu-{task}--")
                )

            put_collapse(title=t(f"Menu.{menu}.name"), content=task_btn_list)

        self.alas_overview()

    @use_scope("content", clear=True)
    def alas_set_group(self, task: str) -> None:
        """
        Set arg groups from dict
        """
        self.init_menu(name=task)
        self.set_title(t(f"Task.{task}.name"))

        put_scope("_groups", [put_none(), put_scope("groups"), put_scope("navigator")])
        config = State.config_updater.read_file(self.alas_name)
        for group, arg_dict in deep_iter(self.ALAS_ARGS[task], depth=1):
            self.set_group(group, arg_dict, config, task)
            self.set_navigator(group)

    @use_scope("groups")
    def set_group(self, group, arg_dict, config, task):
        group_name = group[0]
        with use_scope(f"group_{group_name}"):
            put_text(t(f"{group_name}._info.name"))
            group_help = t(f"{group_name}._info.help")
            if group_help != "":
                put_text(group_help)
            put_html('<hr class="hr-group">')

            for arg, d in deep_iter(arg_dict, depth=1):
                arg = arg[0]
                arg_type = d["type"]
                if arg_type == "hide":
                    continue
                value = deep_get(config, f"{task}.{group_name}.{arg}", d["value"])
                value = str(value) if isinstance(value, datetime) else value

                # Option
                options = deep_get(d, "option", None)
                if options:
                    option = []
                    for opt in options:
                        o = {"label": t(f"{group_name}.{arg}.{opt}"), "value": opt}
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
                invalid_feedback = t("Gui.Text.InvalidFeedBack").format(d["value"])

                get_output(
                    arg_type=arg_type,
                    name=self.path_to_idx[f"{task}.{group_name}.{arg}"],
                    title=t(f"{group_name}.{arg}.name"),
                    arg_help=arg_help,
                    value=value,
                    options=option,
                    invalid_feedback=invalid_feedback,
                ).show()

    @use_scope("navigator")
    def set_navigator(self, group):
        js = f"""
            $("#pywebio-scope-groups").scrollTop(
                $("#pywebio-scope-group_{group[0]}").position().top
                + $("#pywebio-scope-groups").scrollTop() - 59
            )
        """
        put_button(
            label=t(f"{group[0]}._info.name"),
            onclick=lambda: run_js(js),
            color="navigator",
        )

    @use_scope("content", clear=True)
    def alas_overview(self) -> None:
        self.init_menu(name="Overview")
        self.set_title(t(f"Gui.MenuAlas.Overview"))

        put_scope("overview", [put_scope("schedulers"), put_scope("logs")])

        with use_scope("schedulers"):
            put_scope(
                "scheduler-bar",
                [
                    put_text(t("Gui.Overview.Scheduler")).style(
                        "font-size: 1.25rem; margin: auto .5rem auto;"
                    ),
                    put_scope("scheduler_btn"),
                ],
            )
            put_scope(
                "running",
                [
                    put_text(t("Gui.Overview.Running")),
                    put_html('<hr class="hr-group">'),
                    put_scope("running_tasks"),
                ],
            )
            put_scope(
                "pending",
                [
                    put_text(t("Gui.Overview.Pending")),
                    put_html('<hr class="hr-group">'),
                    put_scope("pending_tasks"),
                ],
            )
            put_scope(
                "waiting",
                [
                    put_text(t("Gui.Overview.Waiting")),
                    put_html('<hr class="hr-group">'),
                    put_scope("waiting_tasks"),
                ],
            )

        switch_scheduler = BinarySwitchButton(
            label_on=t("Gui.Button.Stop"),
            label_off=t("Gui.Button.Start"),
            onclick_on=lambda: self.alas.stop(),
            onclick_off=lambda: self.alas.start("Alas", updater.event),
            get_state=lambda: self.alas.alive,
            color_on="off",
            color_off="on",
            scope="scheduler_btn",
        )

        log = RichLog("log")

        with use_scope("logs"):
            put_scope(
                "log-bar",
                [
                    put_text(t("Gui.Overview.Log")).style(
                        "font-size: 1.25rem; margin: auto .5rem auto;"
                    ),
                    put_scope(
                        "log-bar-btns",
                        [
                            put_button(
                                label=t("Gui.Button.ClearLog"),
                                onclick=log.reset,
                                color="off",
                            ),
                            put_scope("log_scroll_btn"),
                        ],
                    ),
                ],
            ),
            put_scope("log", [put_html("")])

        log.console.width = log.get_width()

        switch_log_scroll = BinarySwitchButton(
            label_on=t("Gui.Button.ScrollON"),
            label_off=t("Gui.Button.ScrollOFF"),
            onclick_on=lambda: log.set_scroll(False),
            onclick_off=lambda: log.set_scroll(True),
            get_state=lambda: log.keep_bottom,
            color_on="on",
            color_off="off",
            scope="log_scroll_btn",
        )

        self.task_handler.add(switch_scheduler.g(), 1, True)
        self.task_handler.add(switch_log_scroll.g(), 1, True)
        self.task_handler.add(self.alas_update_overview_task, 10, True)
        self.task_handler.add(log.put_log(self.alas), 0.25, True)

    def _alas_thread_wait_config_change(self) -> None:
        paths = []
        for path, d in deep_iter(self.ALAS_ARGS, depth=3):
            if d["type"] in ["lock", "disable", "hide"]:
                continue
            paths.append(self.path_to_idx[".".join(path)])
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
            modified[self.idx_to_path[d["name"]]] = d["value"]
            while True:
                try:
                    d = self.modified_config_queue.get(timeout=1)
                    modified[self.idx_to_path[d["name"]]] = d["value"]
                except queue.Empty:
                    config = State.config_updater.read_file(config_name)
                    for k, v in modified.copy().items():
                        valuetype = deep_get(self.ALAS_ARGS, k + ".valuetype")
                        v = parse_pin_value(v, valuetype)
                        validate = deep_get(self.ALAS_ARGS, k + ".validate")
                        if not len(str(v)):
                            default = deep_get(self.ALAS_ARGS, k + ".value")
                            deep_set(config, k, default)
                            valid.append(self.path_to_idx[k])
                            modified[k] = default
                        elif not validate or re_fullmatch(validate, v):
                            deep_set(config, k, v)
                            valid.append(self.path_to_idx[k])

                            # update Emotion Record if Emotion Value is changed
                            if "Emotion" in k and "Value" in k:
                                k = k.split(".")
                                k[-1] = k[-1].replace("Value", "Record")
                                k = ".".join(k)
                                v = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                modified[k] = v
                                deep_set(config, k, v)
                                valid.append(self.path_to_idx[k])
                                pin[self.path_to_idx[k]] = v

                        else:
                            modified.pop(k)
                            invalid.append(self.path_to_idx[k])
                            logger.warning(
                                f"Invalid value {v} for key {k}, skip saving."
                            )
                            # toast(t("Gui.Toast.InvalidConfigValue").format(
                            #       t('.'.join(k.split('.')[1:] + ['name']))),
                            #       duration=0, position='right', color='warn')
                    self.pin_remove_invalid_mark(valid)
                    self.pin_set_invalid_mark(invalid)
                    if modified:
                        toast(
                            t("Gui.Toast.ConfigSaved"),
                            duration=1,
                            position="right",
                            color="success",
                        )
                        logger.info(
                            f"Save config {filepath_config(config_name)}, {dict_to_kv(modified)}"
                        )
                        State.config_updater.write_file(config_name, config)
                    modified.clear()
                    valid.clear()
                    invalid.clear()
                    break

    def alas_update_overview_task(self) -> None:
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
            with use_scope(f"overview-task_{func.command}"):
                put_column(
                    [
                        put_text(t(f"Task.{func.command}.name")).style("--arg-title--"),
                        put_text(str(func.next_run)).style("--arg-help--"),
                    ],
                    size="auto auto",
                )
                put_button(
                    label=t("Gui.Button.Setting"),
                    onclick=lambda: self.alas_set_group(func.command),
                    color="off",
                )

        clear("running_tasks")
        clear("pending_tasks")
        clear("waiting_tasks")
        with use_scope("running_tasks"):
            if running:
                for task in running:
                    put_task(task)
            else:
                put_text(t("Gui.Overview.NoTask")).style("--overview-notask-text--")
        with use_scope("pending_tasks"):
            if pending:
                for task in pending:
                    put_task(task)
            else:
                put_text(t("Gui.Overview.NoTask")).style("--overview-notask-text--")
        with use_scope("waiting_tasks"):
            if waiting:
                for task in waiting:
                    put_task(task)
            else:
                put_text(t("Gui.Overview.NoTask")).style("--overview-notask-text--")

    @use_scope("content", clear=True)
    def alas_daemon_overview(self, task: str) -> None:
        self.init_menu(name=task)
        self.set_title(t(f"Task.{task}.name"))

        log = RichLog("log")

        if self.is_mobile:
            put_scope(
                "daemon-overview",
                [
                    put_scope("scheduler-bar"),
                    put_scope("groups"),
                    put_scope("log-bar"),
                    put_scope("log", [put_html("")]),
                ],
            )
        else:
            put_scope(
                "daemon-overview",
                [
                    put_none(),
                    put_scope(
                        "_daemon",
                        [
                            put_scope(
                                "_daemon_upper",
                                [put_scope("scheduler-bar"), put_scope("log-bar")],
                            ),
                            put_scope("groups"),
                            put_scope("log", [put_html("")]),
                        ],
                    ),
                    put_none(),
                ],
            )

        log.console.width = log.get_width()

        with use_scope("scheduler-bar"):
            put_text(t("Gui.Overview.Scheduler")).style(
                "font-size: 1.25rem; margin: auto .5rem auto;"
            )
            put_scope("scheduler_btn")

        switch_scheduler = BinarySwitchButton(
            label_on=t("Gui.Button.Stop"),
            label_off=t("Gui.Button.Start"),
            onclick_on=lambda: self.alas.stop(),
            onclick_off=lambda: self.alas.start(task),
            get_state=lambda: self.alas.alive,
            color_on="off",
            color_off="on",
            scope="scheduler_btn",
        )

        with use_scope("log-bar"):
            put_text(t("Gui.Overview.Log")).style(
                "font-size: 1.25rem; margin: auto .5rem auto;"
            )
            put_scope(
                "log-bar-btns",
                [
                    put_button(
                        label=t("Gui.Button.ClearLog"),
                        onclick=log.reset,
                        color="off",
                    ),
                    put_scope("log_scroll_btn"),
                ],
            )

        switch_log_scroll = BinarySwitchButton(
            label_on=t("Gui.Button.ScrollON"),
            label_off=t("Gui.Button.ScrollOFF"),
            onclick_on=lambda: log.set_scroll(False),
            onclick_off=lambda: log.set_scroll(True),
            get_state=lambda: log.keep_bottom,
            color_on="on",
            color_off="off",
            scope="log_scroll_btn",
        )

        config = State.config_updater.read_file(self.alas_name)
        for group, arg_dict in deep_iter(self.ALAS_ARGS[task], depth=1):
            self.set_group(group, arg_dict, config, task)

        self.task_handler.add(switch_scheduler.g(), 1, True)
        self.task_handler.add(switch_log_scroll.g(), 1, True)
        self.task_handler.add(log.put_log(self.alas), 0.25, True)

    @use_scope("menu", clear=True)
    def dev_set_menu(self) -> None:
        self.init_menu(collapse_menu=False, name="Develop")

        put_button(
            label=t("Gui.MenuDevelop.HomePage"),
            onclick=self.show,
            color="menu",
        ).style(f"--menu-HomePage--")

        # put_button(
        #     label=t("Gui.MenuDevelop.Translate"),
        #     onclick=self.dev_translate,
        #     color="menu",
        # ).style(f"--menu-Translate--")

        put_button(
            label=t("Gui.MenuDevelop.Update"),
            onclick=self.dev_update,
            color="menu",
        ).style(f"--menu-Update--")

        put_button(
            label=t("Gui.MenuDevelop.Remote"),
            onclick=self.dev_remote,
            color="menu",
        ).style(f"--menu-Remote--")

        put_button(
            label=t("Gui.MenuDevelop.Utils"),
            onclick=self.dev_utils,
            color="menu",
        ).style(f"--menu-Utils--")

    def dev_translate(self) -> None:
        go_app("translate", new_window=True)
        lang.TRANSLATE_MODE = True
        self.show()

    @use_scope("content", clear=True)
    def dev_update(self) -> None:
        self.init_menu(name="Update")
        self.set_title(t("Gui.MenuDevelop.Update"))

        if State.restart_event is None:
            put_warning(t("Gui.Update.DisabledWarn"))

        put_row(
            content=[put_scope("updater_loading"), None, put_scope("updater_state")],
            size="auto .25rem 1fr",
        )

        put_scope("updater_btn")
        put_scope("updater_info")

        def update_table():
            with use_scope("updater_info", clear=True):
                local_commit = updater.get_commit(short_sha1=True)
                upstream_commit = updater.get_commit(
                    f"origin/{updater.Branch}", short_sha1=True
                )
                put_table(
                    [
                        [t("Gui.Update.Local"), *local_commit],
                        [t("Gui.Update.Upstream"), *upstream_commit],
                    ],
                    header=[
                        "",
                        "SHA1",
                        t("Gui.Update.Author"),
                        t("Gui.Update.Time"),
                        t("Gui.Update.Message"),
                    ],
                )
            with use_scope("updater_detail", clear=True):
                put_text(t("Gui.Update.DetailedHistory"))
                history = updater.get_commit(
                    f"origin/{updater.Branch}", n=20, short_sha1=True
                )
                put_table(
                    [commit for commit in history],
                    header=[
                        "SHA1",
                        t("Gui.Update.Author"),
                        t("Gui.Update.Time"),
                        t("Gui.Update.Message"),
                    ],
                )

        def u(state):
            if state == -1:
                return
            clear("updater_loading")
            clear("updater_state")
            clear("updater_btn")
            if state == 0:
                put_loading("border", "secondary", "updater_loading").style(
                    "--loading-border-fill--"
                )
                put_text(t("Gui.Update.UpToDate"), scope="updater_state")
                put_button(
                    t("Gui.Button.CheckUpdate"),
                    onclick=updater.check_update,
                    color="info",
                    scope="updater_btn",
                )
                update_table()
            elif state == 1:
                put_loading("grow", "success", "updater_loading").style(
                    "--loading-grow--"
                )
                put_text(t("Gui.Update.HaveUpdate"), scope="updater_state")
                put_button(
                    t("Gui.Button.ClickToUpdate"),
                    onclick=updater.run_update,
                    color="success",
                    scope="updater_btn",
                )
                update_table()
            elif state == "checking":
                put_loading("border", "primary", "updater_loading").style(
                    "--loading-border--"
                )
                put_text(t("Gui.Update.UpdateChecking"), scope="updater_state")
            elif state == "failed":
                put_loading("grow", "danger", "updater_loading").style(
                    "--loading-grow--"
                )
                put_text(t("Gui.Update.UpdateFailed"), scope="updater_state")
                put_button(
                    t("Gui.Button.RetryUpdate"),
                    onclick=updater.run_update,
                    color="primary",
                    scope="updater_btn",
                )
            elif state == "start":
                put_loading("border", "primary", "updater_loading").style(
                    "--loading-border--"
                )
                put_text(t("Gui.Update.UpdateStart"), scope="updater_state")
                put_button(
                    t("Gui.Button.CancelUpdate"),
                    onclick=updater.cancel,
                    color="danger",
                    scope="updater_btn",
                )
            elif state == "wait":
                put_loading("border", "primary", "updater_loading").style(
                    "--loading-border--"
                )
                put_text(t("Gui.Update.UpdateWait"), scope="updater_state")
                put_button(
                    t("Gui.Button.CancelUpdate"),
                    onclick=updater.cancel,
                    color="danger",
                    scope="updater_btn",
                )
            elif state == "run update":
                put_loading("border", "primary", "updater_loading").style(
                    "--loading-border--"
                )
                put_text(t("Gui.Update.UpdateRun"), scope="updater_state")
                put_button(
                    t("Gui.Button.CancelUpdate"),
                    onclick=updater.cancel,
                    color="danger",
                    scope="updater_btn",
                    disabled=True,
                )
            elif state == "reload":
                put_loading("grow", "success", "updater_loading").style(
                    "--loading-grow--"
                )
                put_text(t("Gui.Update.UpdateSuccess"), scope="updater_state")
                update_table()
            elif state == "finish":
                put_loading("grow", "success", "updater_loading").style(
                    "--loading-grow--"
                )
                put_text(t("Gui.Update.UpdateFinish"), scope="updater_state")
                update_table()
            elif state == "cancel":
                put_loading("border", "danger", "updater_loading").style(
                    "--loading-border--"
                )
                put_text(t("Gui.Update.UpdateCancel"), scope="updater_state")
                put_button(
                    t("Gui.Button.CancelUpdate"),
                    onclick=updater.cancel,
                    color="danger",
                    scope="updater_btn",
                    disabled=True,
                )
            else:
                put_text(
                    "Something went wrong, please contact develops",
                    scope="updater_state",
                )
                put_text(f"state: {state}", scope="updater_state")

        updater_switch = Switch(
            status=u, get_state=lambda: updater.state, name="updater"
        )

        update_table()
        self.task_handler.add(updater_switch.g(), delay=0.5, pending_delete=True)

        updater.check_update()

    @use_scope("content", clear=True)
    def dev_utils(self) -> None:
        self.init_menu(name="Utils")
        self.set_title(t("Gui.MenuDevelop.Utils"))
        put_button(label="Raise exception", onclick=raise_exception)

        def _force_restart():
            if State.restart_event is not None:
                toast("Alas will restart in 3 seconds", duration=0, color="error")
                clearup()
                State.restart_event.set()
            else:
                toast("Reload not enabled", color="error")

        put_button(label="Force restart", onclick=_force_restart)

    @use_scope("content", clear=True)
    def dev_remote(self) -> None:
        self.init_menu(name="Remote")
        self.set_title(t("Gui.MenuDevelop.Remote"))
        put_row(
            content=[put_scope("remote_loading"), None, put_scope("remote_state")],
            size="auto .25rem 1fr",
        )
        put_scope("remote_info")

        def u(state):
            if state == -1:
                return
            clear("remote_loading")
            clear("remote_state")
            clear("remote_info")
            if state in (1, 2):
                put_loading("grow", "success", "remote_loading").style(
                    "--loading-grow--"
                )
                put_text(t("Gui.Remote.Running"), scope="remote_state")
                put_text(t("Gui.Remote.EntryPoint"), scope="remote_info")
                entrypoint = RemoteAccess.get_entry_point()
                if entrypoint:
                    if State.electron:  # Prevent click into url in electron client
                        put_text(entrypoint, scope="remote_info").style(
                            "text-decoration-line: underline"
                        )
                    else:
                        put_link(name=entrypoint, url=entrypoint, scope="remote_info")
                else:
                    put_text("Loading...", scope="remote_info")
            elif state in (0, 3):
                put_loading("border", "secondary", "remote_loading").style(
                    "--loading-border-fill--"
                )
                if (
                    State.deploy_config.EnableRemoteAccess
                    and State.deploy_config.Password
                ):
                    put_text(t("Gui.Remote.NotRunning"), scope="remote_state")
                else:
                    put_text(t("Gui.Remote.NotEnable"), scope="remote_state")
                put_text(t("Gui.Remote.ConfigureHint"), scope="remote_info")
                url = "http://app.azurlane.cloud" + (
                    "" if State.deploy_config.Language.startswith("zh") else "/en.html"
                )
                put_html(f'<a href="{url}" target="_blank">{url}</a>', scope="remote_info")
                if state == 3:
                    put_warning(t("Gui.Remote.SSHNotInstall"), closable=False, scope="remote_info")

        remote_switch = Switch(
            status=u, get_state=RemoteAccess.get_state, name="remote"
        )

        self.task_handler.add(remote_switch.g(), delay=1, pending_delete=True)

    def ui_develop(self) -> None:
        self.init_aside(name="Develop")
        self.set_title(t("Gui.Aside.Develop"))
        self.dev_set_menu()
        self.alas_name = ""
        if hasattr(self, "alas"):
            del self.alas
        self.state_switch.switch()

    def ui_alas(self, config_name: str) -> None:
        if config_name == self.alas_name:
            self.expand_menu()
            return
        self.init_aside(name=config_name)
        clear("content")
        self.alas_name = config_name
        self.alas = ProcessManager.get_manager(config_name)
        self.alas_config = AzurLaneConfig(config_name, "")
        self.state_switch.switch()
        self.alas_set_menu()

    def ui_add_alas(self) -> None:
        with popup(t("Gui.AddAlas.PopupTitle")) as s:

            def get_unused_name():
                all_name = alas_instance()
                for i in range(2, 100):
                    if f"alas{i}" not in all_name:
                        return f"alas{i}"
                else:
                    return ""

            def add():
                name = pin["AddAlas_name"]
                origin = pin["AddAlas_copyfrom"]

                if name not in alas_instance():
                    r = State.config_updater.read_file(origin)
                    State.config_updater.write_file(name, r)
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
                    scope=s,
                ),
                put_select(
                    name="AddAlas_copyfrom",
                    label=t("Gui.AddAlas.CopyFrom"),
                    options=["template"] + alas_instance(),
                    value=origin or "template",
                    scope=s,
                ),
                put_button(label=t("Gui.AddAlas.Confirm"), onclick=add, scope=s)

            put()

    def show(self) -> None:
        self._show()
        self.init_aside(name="Home")
        self.set_aside()
        self.collapse_menu()
        self.alas_name = ""
        if hasattr(self, "alas"):
            del self.alas
        self.set_status(0)

        def set_language(l):
            lang.set_language(l)
            self.show()

        def set_theme(t):
            self.set_theme(t)
            run_js("location.reload()")

        with use_scope("content"):
            put_text("Select your language / 选择语言").style("text-align: center")
            put_buttons(
                [
                    {"label": "简体中文", "value": "zh-CN"},
                    {"label": "繁體中文", "value": "zh-TW"},
                    {"label": "English", "value": "en-US"},
                    {"label": "日本語", "value": "ja-JP"},
                ],
                onclick=lambda l: set_language(l),
            ).style("text-align: center")
            put_text("Change theme / 更改主题").style("text-align: center")
            put_buttons(
                [
                    {"label": "Light", "value": "default", "color": "light"},
                    {"label": "Dark", "value": "dark", "color": "dark"},
                ],
                onclick=lambda t: set_theme(t),
            ).style("text-align: center")

            # show something
            put_markdown(
                """
            Alas is a free open source software, if you paid for Alas from any channel, please refund.
            Alas 是一款免费开源软件，如果你在任何渠道付费购买了Alas，请退款。
            Project repository 项目地址：`https://github.com/LmeSzinc/AzurLaneAutoScript`
            """
            ).style("text-align: center")

        if lang.TRANSLATE_MODE:
            lang.reload()

            def _disable():
                lang.TRANSLATE_MODE = False
                self.show()

            toast(
                _t("Gui.Toast.DisableTranslateMode"),
                duration=0,
                position="right",
                onclick=_disable,
            )

    def run(self) -> None:
        # setup gui
        set_env(title="Alas", output_animation=False)
        add_css(filepath_css("alas"))
        if self.is_mobile:
            add_css(filepath_css("alas-mobile"))
        else:
            add_css(filepath_css("alas-pc"))

        if self.theme == "dark":
            add_css(filepath_css("dark-alas"))
        else:
            add_css(filepath_css("light-alas"))

        # Auto refresh when lost connection
        # [For develop] Disable by run `reload=0` in console
        run_js(
            """
        reload = 1;
        WebIO._state.CurrentSession.on_session_close(
            ()=>{
                setTimeout(
                    ()=>{
                        if (reload == 1){
                            location.reload();
                        }
                    }, 4000
                )
            }
        );
        """
        )

        aside = get_localstorage("aside")
        self.show()

        # detect config change
        _thread_wait_config_change = threading.Thread(
            target=self._alas_thread_wait_config_change
        )
        register_thread(_thread_wait_config_change)
        _thread_wait_config_change.start()

        # save config
        _thread_save_config = threading.Thread(target=self._alas_thread_update_config)
        register_thread(_thread_save_config)
        _thread_save_config.start()

        visibility_state_switch = Switch(
            status={
                True: [
                    lambda: self.__setattr__("visible", True),
                    lambda: self.alas_update_overview_task()
                    if self.page == "Overview"
                    else 0,
                    lambda: self.task_handler._task.__setattr__("delay", 15),
                ],
                False: [
                    lambda: self.__setattr__("visible", False),
                    lambda: self.task_handler._task.__setattr__("delay", 1),
                ],
            },
            get_state=get_window_visibility_state,
            name="visibility_state",
        )

        self.state_switch = Switch(
            status=self.set_status,
            get_state=lambda: getattr(getattr(self, "alas", -1), "state", 0),
            name="state",
        )

        def goto_update():
            self.ui_develop()
            self.dev_update()

        update_switch = Switch(
            status={
                1: lambda: toast(
                    t("Gui.Toast.ClickToUpdate"),
                    duration=0,
                    position="right",
                    color="success",
                    onclick=goto_update,
                )
            },
            get_state=lambda: updater.state,
            name="update_state",
        )

        self.task_handler.add(self.state_switch.g(), 2)
        self.task_handler.add(visibility_state_switch.g(), 15)
        self.task_handler.add(update_switch.g(), 1)
        self.task_handler.start()

        # Return to previous page
        if aside not in ["Develop", "Home", None]:
            self.ui_alas(aside)


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
    State.init()
    AlasGUI.shorten_path()
    lang.reload()
    updater.event = State.manager.Event()
    if updater.delay > 0:
        task_handler.add(updater.check_update, updater.delay)
    task_handler.add(updater.schedule_update(), 86400)
    task_handler.start()
    if State.deploy_config.DiscordRichPresence:
        init_discord_rpc()
    if State.deploy_config.StartOcrServer:
        start_ocr_server_process(State.deploy_config.OcrServerPort)
    if (
        State.deploy_config.EnableRemoteAccess
        and State.deploy_config.Password is not None
    ):
        task_handler.add(RemoteAccess.keep_ssh_alive(), 60)


def clearup():
    """
    Notice: Ensure run it before uvicorn reload app,
    all process will NOT EXIT after close electron app.
    """
    logger.info("Start clearup")
    RemoteAccess.kill_ssh_process()
    close_discord_rpc()
    stop_ocr_server_process()
    for alas in ProcessManager._processes.values():
        alas.stop()
    State.clearup()
    task_handler.stop()
    logger.info("Alas closed.")


def app():
    parser = argparse.ArgumentParser(description="Alas web service")
    parser.add_argument(
        "-k", "--key", type=str, help="Password of alas. No password by default"
    )
    parser.add_argument(
        "--cdn",
        action="store_true",
        help="Use jsdelivr cdn for pywebio static files (css, js). Self host cdn by default.",
    )
    parser.add_argument(
        "--electron", action="store_true", help="Runs by electron client."
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Able to use auto update and builtin updater",
    )
    args, _ = parser.parse_known_args()

    # Apply config
    AlasGUI.set_theme(theme=State.deploy_config.Theme)
    lang.LANG = State.deploy_config.Language
    key = args.key or State.deploy_config.Password
    if args.cdn:
        cdn = args.cdn
    else:
        cdn = State.deploy_config.CDN
    State.electron = args.electron

    logger.hr("Webui configs")
    logger.attr("Theme", State.deploy_config.Theme)
    logger.attr("Language", lang.LANG)
    logger.attr("Password", True if key else False)
    logger.attr("CDN", cdn)
    logger.attr("Electron", args.electron)

    def index():
        if key is not None and not login(key):
            logger.warning(f"{info.user_ip} login failed.")
            time.sleep(1.5)
            run_js("location.reload();")
            return
        AlasGUI().run()

    app = asgi_app(
        applications=[index],
        cdn=cdn,
        static_dir=None,
        debug=True,
        on_startup=[
            startup,
            lambda: ProcessManager.restart_processes(ev=updater.event),
        ],
        on_shutdown=[clearup],
    )

    return app
