import re
import argparse
import json
import queue
import threading
import time
from datetime import datetime
from functools import partial
from typing import Dict, List, Optional

from pywebio import config as webconfig
from pywebio.input import file_upload, input_group, input, select
from pywebio.output import (
    Output,
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
from pywebio.pin import pin, pin_on_change
from pywebio.session import (
    go_app,
    info,
    local,
    register_thread,
    run_js,
    set_env,
    download,
)

import module.webui.lang as lang
from module.config.config import AzurLaneConfig, Function
from module.config.env import IS_ON_PHONE_CLOUD
from module.config.utils import (
    alas_instance,
    alas_template,
    deep_get,
    deep_iter,
    deep_set,
    dict_to_kv,
    filepath_args,
    filepath_config,
    read_file,
)
from module.config.utils import time_delta
from module.log_res.log_res import LogRes
from module.logger import logger
from module.ocr.rpc import start_ocr_server_process, stop_ocr_server_process
from module.submodule.submodule import load_config
from module.submodule.utils import get_config_mod
from module.webui.base import Frame
from module.webui.discord_presence import close_discord_rpc, init_discord_rpc
from module.webui.fastapi import asgi_app
from module.webui.lang import _t, t
from module.webui.pin import put_input, put_select, pin_update
from module.webui.process_manager import ProcessManager
from module.webui.remote_access import RemoteAccess
from module.webui.setting import State
from module.webui.updater import updater
from module.webui.utils import (
    Icon,
    Switch,
    TaskHandler,
    add_css,
    filepath_css,
    get_alas_config_listen_path,
    get_localstorage,
    get_window_visibility_state,
    login,
    parse_pin_value,
    raise_exception,
    re_fullmatch,
    to_pin_value,
)
from module.webui.widgets import (
    BinarySwitchButton,
    RichLog,
    T_Output_Kwargs,
    put_icon_buttons,
    put_loading_text,
    put_none,
    put_output,
)

task_handler = TaskHandler()


def timedelta_to_text(delta=None):
    time_delta_name_suffix_dict = {
        'Y': 'YearsAgo',
        'M': 'MonthsAgo',
        'D': 'DaysAgo',
        'h': 'HoursAgo',
        'm': 'MinutesAgo',
        's': 'SecondsAgo',
    }
    time_delta_name_prefix = 'Gui.Overview.'
    time_delta_name_suffix = 'NoData'
    time_delta_display = ''
    if isinstance(delta, dict):
        for _key in delta:
            if delta[_key]:
                time_delta_name_suffix = time_delta_name_suffix_dict[_key]
                time_delta_display = delta[_key]
                break
    time_delta_display = str(time_delta_display)
    time_delta_name = time_delta_name_prefix + time_delta_name_suffix
    return time_delta_display + t(time_delta_name)


class AlasGUI(Frame):
    ALAS_MENU: Dict[str, Dict[str, List[str]]]
    ALAS_ARGS: Dict[str, Dict[str, Dict[str, Dict[str, str]]]]
    theme = "default"
    _log = RichLog

    def initial(self) -> None:
        self.ALAS_MENU = read_file(filepath_args("menu", self.alas_mod))
        self.ALAS_ARGS = read_file(filepath_args("args", self.alas_mod))
        self._init_alas_config_watcher()

    def __init__(self) -> None:
        super().__init__()
        # modified keys, return values of pin_wait_change()
        self.modified_config_queue = queue.Queue()
        # alas config name
        self.alas_name = ""
        self.alas_mod = "alas"
        self.alas_config = AzurLaneConfig("template")
        self.initial()

    @use_scope("aside", clear=True)
    def set_aside(self) -> None:
        # TODO: update put_icon_buttons()
        put_icon_buttons(
            Icon.DEVELOP,
            buttons=[{"label": t("Gui.Aside.Home"), "value": "Home", "color": "aside"}],
            onclick=[self.ui_develop],
        )
        for name in alas_instance():
            put_icon_buttons(
                Icon.RUN,
                buttons=[{"label": name, "value": name, "color": "aside"}],
                onclick=self.ui_alas,
            )
        put_icon_buttons(
            Icon.SETTING,
            buttons=[
                {
                    "label": t("Gui.AddAlas.Manage"),
                    "value": "AddAlas",
                    "color": "aside",
                }
            ],
            onclick=[lambda: go_app("manage", new_window=False)],
        )

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
            put_loading_text(t("Gui.Status.Running"), color="success")
        elif state == 2:
            put_loading_text(t("Gui.Status.Inactive"), color="secondary", fill=True)
        elif state == 3:
            put_loading_text(t("Gui.Status.Warning"), shape="grow", color="warning")
        elif state == 4:
            put_loading_text(t("Gui.Status.Updating"), shape="grow", color="success")

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
        ).style(f"--menu-Overview--")

        for menu, task_data in self.ALAS_MENU.items():
            if task_data.get("page") == "tool":
                _onclick = self.alas_daemon_overview
            else:
                _onclick = self.alas_set_group

            if task_data.get("menu") == "collapse":
                task_btn_list = [
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
                    for task in task_data.get("tasks", [])
                ]
                put_collapse(title=t(f"Menu.{menu}.name"), content=task_btn_list)
            else:
                title = t(f"Menu.{menu}.name")
                put_html(
                    '<div class="hr-task-group-box">'
                    '<span class="hr-task-group-line"></span>'
                    f'<span class="hr-task-group-text">{title}</span>'
                    '<span class="hr-task-group-line"></span>'
                    '</div>'
                )
                for task in task_data.get("tasks", []):
                    put_buttons(
                        [
                            {
                                "label": t(f"Task.{task}.name"),
                                "value": task,
                                "color": "menu",
                            }
                        ],
                        onclick=_onclick,
                    ).style(f"--menu-{task}--").style(f"padding-left: 0.75rem")

        self.alas_overview()

    @use_scope("content", clear=True)
    def alas_set_group(self, task: str) -> None:
        """
        Set arg groups from dict
        """
        self.init_menu(name=task)
        self.set_title(t(f"Task.{task}.name"))

        put_scope("_groups", [put_none(), put_scope("groups"), put_scope("navigator")])

        task_help: str = t(f"Task.{task}.help")
        if task_help:
            put_scope(
                "group__info",
                scope="groups",
                content=[put_text(task_help).style("font-size: 1rem")],
            )

        config = self.alas_config.read_file(self.alas_name)
        for group, arg_dict in deep_iter(self.ALAS_ARGS[task], depth=1):
            if self.set_group(group, arg_dict, config, task):
                self.set_navigator(group)

    @use_scope("groups")
    def set_group(self, group, arg_dict, config, task):
        group_name = group[0]

        output_list: List[Output] = []
        for arg, arg_dict in deep_iter(arg_dict, depth=1):
            output_kwargs: T_Output_Kwargs = arg_dict.copy()

            # Skip hide
            display: Optional[str] = output_kwargs.pop("display", None)
            if display == "hide":
                continue
            # Disable
            elif display == "disabled":
                output_kwargs["disabled"] = True
            # Output type
            output_kwargs["widget_type"] = output_kwargs.pop("type")

            arg_name = arg[0]  # [arg_name,]
            # Internal pin widget name
            output_kwargs["name"] = f"{task}_{group_name}_{arg_name}"
            # Display title
            output_kwargs["title"] = t(f"{group_name}.{arg_name}.name")

            # Get value from config
            value = deep_get(
                config, [task, group_name, arg_name], output_kwargs["value"]
            )
            # idk
            value = str(value) if isinstance(value, datetime) else value
            # Default value
            output_kwargs["value"] = value
            # Options
            output_kwargs["options"] = options = output_kwargs.pop("option", [])
            # Options label
            options_label = []
            for opt in options:
                options_label.append(t(f"{group_name}.{arg_name}.{opt}"))
            output_kwargs["options_label"] = options_label
            # Help
            arg_help = t(f"{group_name}.{arg_name}.help")
            if arg_help == "" or not arg_help:
                arg_help = None
            output_kwargs["help"] = arg_help
            # Invalid feedback
            output_kwargs["invalid_feedback"] = t("Gui.Text.InvalidFeedBack", value)

            o = put_output(output_kwargs)
            if o is not None:
                # output will inherit current scope when created, override here
                o.spec["scope"] = f"#pywebio-scope-group_{group_name}"
                output_list.append(o)

        if not output_list:
            return 0

        with use_scope(f"group_{group_name}"):
            put_text(t(f"{group_name}._info.name"))
            group_help = t(f"{group_name}._info.help")
            if group_help != "":
                put_text(group_help)
            put_html('<hr class="hr-group">')
            for output in output_list:
                output.show()

        return len(output_list)

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
            onclick_off=lambda: self.alas.start(None, updater.event),
            get_state=lambda: self.alas.alive,
            color_on="off",
            color_off="on",
            scope="scheduler_btn",
        )

        log = RichLog("log")
        self._log = log
        self._log.dashboard_arg_group = LogRes(self.alas_config).groups

        with use_scope("logs"):
            if 'Maa' in self.ALAS_ARGS:
                put_scope(
                    "log-bar",
                    [
                        put_text(t("Gui.Overview.Log")).style(
                            "font-size: 1.25rem; margin: auto .5rem auto;"
                        ),
                        put_scope(
                            "log-bar-btns",
                            [
                                put_scope("log_scroll_btn"),
                            ],
                        ),
                    ],
                ),
            else:
                put_scope(
                    "log-bar",
                    [
                        put_text(t("Gui.Overview.Log")).style(
                            "font-size: 1.25rem; margin: auto .5rem auto;"
                        ),
                        put_scope(
                            "log-bar-btns",
                            [
                                put_scope("log_scroll_btn"),
                                put_scope("dashboard_btn"),
                            ],
                        ),
                        put_html('<hr class="hr-group">'),
                        put_scope("dashboard"),
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
        switch_dashboard = BinarySwitchButton(
            label_on=t("Gui.Button.DashboardON"),
            label_off=t("Gui.Button.DashboardOFF"),
            onclick_on=lambda: self.set_dashboard_display(False),
            onclick_off=lambda: self.set_dashboard_display(True),
            get_state=lambda: log.display_dashboard,
            color_on="off",
            color_off="on",
            scope="dashboard_btn",
        )
        self.task_handler.add(switch_scheduler.g(), 1, True)
        self.task_handler.add(switch_log_scroll.g(), 1, True)
        if 'Maa' not in self.ALAS_ARGS:
            self.task_handler.add(switch_dashboard.g(), 1, True)
        self.task_handler.add(self.alas_update_overview_task, 10, True)
        if 'Maa' not in self.ALAS_ARGS:
            self.task_handler.add(self.alas_update_dashboard, 10, True)
        self.task_handler.add(log.put_log(self.alas), 0.25, True)

    def set_dashboard_display(self, b):
        self._log.set_dashboard_display(b)
        self.alas_update_dashboard(True)

    def _init_alas_config_watcher(self) -> None:
        def put_queue(path, value):
            self.modified_config_queue.put({"name": path, "value": value})

        for path in get_alas_config_listen_path(self.ALAS_ARGS):
            pin_on_change(
                name="_".join(path), onchange=partial(put_queue, ".".join(path))
            )
        logger.info("Init config watcher done.")

    def _alas_thread_update_config(self) -> None:
        modified = {}
        while self.alive:
            try:
                d = self.modified_config_queue.get(timeout=10)
                config_name = self.alas_name
                config_updater = self.alas_config
            except queue.Empty:
                continue
            modified[d["name"]] = d["value"]
            while True:
                try:
                    d = self.modified_config_queue.get(timeout=1)
                    modified[d["name"]] = d["value"]
                except queue.Empty:
                    self._save_config(modified, config_name, config_updater)
                    modified.clear()
                    break

    def _save_config(
            self,
            modified: Dict[str, str],
            config_name: str,
            config_updater: AzurLaneConfig = State.config_updater,
    ) -> None:
        try:
            skip_time_record = False
            valid = []
            invalid = []
            config = config_updater.read_file(config_name)
            n = datetime.now()
            for p, v in deep_iter(config, depth=3):
                if p[-1].endswith('un') and not isinstance(v, bool):
                    if (v - n).days >= 31:
                        deep_set(config, p, '')
            for k, v in modified.copy().items():
                valuetype = deep_get(self.ALAS_ARGS, k + ".valuetype")
                v = parse_pin_value(v, valuetype)
                validate = deep_get(self.ALAS_ARGS, k + ".validate")
                if not len(str(v)):
                    default = deep_get(self.ALAS_ARGS, k + ".value")
                    modified[k] = default
                    deep_set(config, k, default)
                    valid.append(k)
                    pin["_".join(k.split("."))] = default

                elif not validate or re_fullmatch(validate, v):
                    deep_set(config, k, v)
                    modified[k] = v
                    valid.append(k)
                    for set_key, set_value in config_updater.save_callback(k, v):
                        modified[set_key] = set_value
                        deep_set(config, set_key, set_value)
                        valid.append(set_key)
                        pin["_".join(set_key.split("."))] = to_pin_value(set_value)
                else:
                    modified.pop(k)
                    invalid.append(k)
                    logger.warning(f"Invalid value {v} for key {k}, skip saving.")
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
                config_updater.write_file(config_name, config)
        except Exception as e:
            logger.exception(e)

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

    def _update_dashboard(self, num=None, groups_to_display=None):
        x = 0
        _num = 10000 if num is None else num
        _arg_group = self._log.dashboard_arg_group if groups_to_display is None else groups_to_display
        time_now = datetime.now().replace(microsecond=0)
        for group_name in _arg_group:
            group = deep_get(d=self.alas_config.data, keys=f'Dashboard.{group_name}')
            if group is None:
                continue

            value = str(group['Value'])
            if 'Limit' in group.keys():
                value_limit = f' / {group["Limit"]}'
                value_total = ''
            elif 'Total' in group.keys():
                value_total = f' ({group["Total"]})'
                value_limit = ''
            elif group_name == 'Pt':
                value_limit = ' / ' + re.sub(r'[,.\'"，。]', '',
                                             str(deep_get(self.alas_config.data, 'EventGeneral.EventGeneral.PtLimit')))
                if value_limit == ' / 0':
                    value_limit = ''
            else:
                value_limit = ''
                value_total = ''
            # value = value + value_limit + value_total

            value_time = group['Record']
            if value_time is None or value_time == datetime(2020, 1, 1, 0, 0, 0):
                value_time = datetime(2023, 1, 1, 0, 0, 0)

            # Handle time delta
            if value_time == datetime(2023, 1, 1, 0, 0, 0):
                value = 'None'
                delta = timedelta_to_text()
            else:
                delta = timedelta_to_text(time_delta(value_time - time_now))
            if group_name not in self._log.last_display_time.keys():
                self._log.last_display_time[group_name] = ''
            if self._log.last_display_time[group_name] == delta and not self._log.first_display:
                continue
            self._log.last_display_time[group_name] = delta

            # if self._log.first_display:
            # Handle width
            # value_width = len(value) * 0.7 + 0.6 if value != 'None' else 4.5
            # value_width = str(value_width/1.12) + 'rem' if self.is_mobile else str(value_width) + 'rem'
            value_limit = '' if value == 'None' else value_limit
            # limit_width = len(value_limit) * 0.7
            # limit_width = str(limit_width) + 'rem'
            value_total = '' if value == 'None' else value_total
            limit_style = '--dashboard-limit--' if value_limit else '--dashboard-total--'
            value_limit = value_limit if value_limit else value_total
            # Handle dot color
            _color = f"""background-color:{deep_get(d=group, keys='Color').replace('^', '#')}"""
            color = f'<div class="status-point" style={_color}>'
            with use_scope(group_name, clear=True):
                put_row(
                    [
                        put_html(color),
                        put_scope(
                            f"{group_name}_group",
                            [
                                put_column(
                                    [
                                        put_row(
                                            [
                                                put_text(value
                                                         ).style(f'--dashboard-value--'),
                                                put_text(value_limit
                                                         ).style(limit_style),
                                            ],
                                        ).style('grid-template-columns:min-content auto;align-items: baseline;'),
                                        put_text(
                                            t(f'Gui.Overview.{group_name}') + " - " + delta
                                        ).style('---dashboard-help--')
                                    ],
                                    size="auto auto",
                                ),
                            ],
                        ),
                    ],
                    size="20px 1fr"
                ).style("height: 1fr"),
            x += 1
            if x >= _num:
                break
        if self._log.first_display:
            self._log.first_display = False

    def alas_update_dashboard(self, _clear=False):
        if not self.visible:
            return
        with use_scope("dashboard", clear=_clear):
            if not self._log.display_dashboard:
                self._update_dashboard(num=4, groups_to_display=['Oil', 'Coin', 'Gem', 'Pt'])
            elif self._log.display_dashboard:
                self._update_dashboard()

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

        config = self.alas_config.read_file(self.alas_name)
        for group, arg_dict in deep_iter(self.ALAS_ARGS[task], depth=1):
            if group[0] == "Storage":
                continue
            self.set_group(group, arg_dict, config, task)

        run_js(
            """
            $("#pywebio-scope-log").css(
                "grid-row-start",
                -2 - $("#pywebio-scope-_daemon").children().filter(
                    function(){
                        return $(this).css("display") === "none";
                    }
                ).length
            );
            $("#pywebio-scope-log").css(
                "grid-row-end",
                -1
            );
        """
        )

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
        put_button(label=t("Gui.MenuDevelop.RaiseException"), onclick=raise_exception)

        def _force_restart():
            if State.restart_event is not None:
                toast(t("Gui.Toast.AlasRestart"), duration=0, color="error")
                clearup()
                State.restart_event.set()
            else:
                toast(t("Gui.Toast.ReloadEnabled"), color="error")

        put_button(label=t("Gui.MenuDevelop.ForceRestart"), onclick=_force_restart)

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
                put_html(
                    f'<a href="{url}" target="_blank">{url}</a>', scope="remote_info"
                )
                if state == 3:
                    put_warning(
                        t("Gui.Remote.SSHNotInstall"),
                        closable=False,
                        scope="remote_info",
                    )

        remote_switch = Switch(
            status=u, get_state=RemoteAccess.get_state, name="remote"
        )

        self.task_handler.add(remote_switch.g(), delay=1, pending_delete=True)

    def ui_develop(self) -> None:
        if not self.is_mobile:
            self.show()
            return
        self.init_aside(name="Home")
        self.set_title(t("Gui.Aside.Home"))
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
        self.alas_mod = get_config_mod(config_name)
        self.alas = ProcessManager.get_manager(config_name)
        self.alas_config = load_config(config_name)
        self.state_switch.switch()
        self.initial()
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

                if name in alas_instance():
                    err = "Gui.AddAlas.FileExist"
                elif set(name) & set(".\\/:*?\"'<>|"):
                    err = "Gui.AddAlas.InvalidChar"
                elif name.lower().startswith("template"):
                    err = "Gui.AddAlas.InvalidPrefixTemplate"
                else:
                    err = ""
                if err:
                    clear(s)
                    put(name, origin)
                    put_error(t(err), scope=s)
                    return

                r = load_config(origin).read_file(origin)
                State.config_updater.write_file(name, r, get_config_mod(origin))
                self.set_aside()
                self.active_button("aside", self.alas_name)
                close_popup()

            def put(name=None, origin=None):
                put_input(
                    name="AddAlas_name",
                    label=t("Gui.AddAlas.NewName"),
                    value=name or get_unused_name(),
                    scope=s,
                )
                put_select(
                    name="AddAlas_copyfrom",
                    label=t("Gui.AddAlas.CopyFrom"),
                    options=alas_template() + alas_instance(),
                    value=origin or "template-alas",
                    scope=s,
                )
                put_buttons(
                    buttons=[
                        {"label": t("Gui.AddAlas.Confirm"), "value": "confirm"},
                        {"label": t("Gui.AddAlas.Manage"), "value": "manage"},
                    ],
                    onclick=[
                        add,
                        lambda: go_app("manage", new_window=False),
                    ],
                    scope=s,
                )

            put()

    def show(self) -> None:
        self._show()
        self.set_aside()
        self.init_aside(name="Home")
        self.dev_set_menu()
        self.init_menu(name="HomePage")
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
        set_env(title="AlasGG", output_animation=False)
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

        # init config watcher
        self._init_alas_config_watcher()

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
        if aside not in ["Home", None]:
            self.ui_alas(aside)


def app_manage():
    def _import():
        resp = file_upload(
            label=t("Gui.AppManage.Import"),
            placeholder=t("Gui.Text.ChooseFile"),
            help_text=t("Gui.AppManage.OverrideWarning"),
            accept=".json",
            required=False,
            max_size="1M",
        )

        if resp is None:
            return

        file: bytes = resp["content"]
        file_name: str = resp["filename"]

        if IS_ON_PHONE_CLOUD:
            config_name = mod_name = "alas"
        elif len(file_name.split(".")) == 2:
            config_name, _ = file_name.split(".")
            mod_name = "alas"
        else:
            config_name, mod_name, _ = file_name.rsplit(".", maxsplit=2)

        config = json.loads(file.decode(encoding="utf-8"))
        State.config_updater.write_file(config_name, config, mod_name)
        toast(t("Gui.AppManage.ImportSuccess"), color="success")

        _show_table()

    def _export(config_name: str):
        mod_name = get_config_mod(config_name)
        if mod_name == "alas":
            filename = f"{config_name}.json"
        else:
            filename = f"{config_name}.{mod_name}.json"
        with open(filepath_config(config_name, mod_name), "rb") as f:
            download(filename, f.read())

    def _new():
        def get_unused_name():
            all_name = alas_instance()
            for i in range(2, 100):
                if f"alas{i}" not in all_name:
                    return f"alas{i}"
            else:
                return ""

        def validate(s: str):
            if s in alas_instance():
                return t("Gui.AppManage.NameExist")
            if set(s) & set(".\\/:*?\"'<>|"):
                return t("Gui.AppManage.InvalidChar")
            if s.lower().startswith("template"):
                return t("Gui.AppManage.InvalidPrefixTemplate")
            return None

        resp = input_group(
            label=t("Gui.AppManage.TitleNew"),
            inputs=[
                input(
                    label=t("Gui.AppManage.NewName"),
                    name="config_name",
                    value=get_unused_name(),
                    validate=validate,
                ),
                select(
                    label=t("Gui.AppManage.CopyFrom"),
                    name="copy_from",
                    options=alas_template() + alas_instance(),
                    value="template-alas",
                ),
            ],
            cancelable=True,
        )

        if resp is None:
            return

        config_name = resp["config_name"]
        origin = resp["copy_from"]

        r = load_config(origin).read_file(origin)
        State.config_updater.write_file(config_name, r, get_config_mod(origin))
        toast(t("Gui.AppManage.NewSuccess"), color="success")
        _show_table()

    def _show_table():
        clear("config_table")
        put_table(
            tdata=[
                (
                    name,
                    get_config_mod(name),
                    put_buttons(
                        buttons=[
                            {"label": t("Gui.AppManage.Export"), "value": name},
                            # {
                            #     "label": t("Gui.AppManage.Delete"),
                            #     "value": name,
                            #     "disabled": True,
                            #     "color": "danger",
                            # },
                        ],
                        onclick=[
                            partial(_export, name),
                            # partial(_delete, name),
                        ],
                        group=True,
                        small=True,
                    ),
                )
                for name in alas_instance()
            ],
            header=[
                t("Gui.AppManage.Name"),
                t("Gui.AppManage.Mod"),
                t("Gui.AppManage.Actions"),
            ],
            scope="config_table",
        )

    set_env(title="Alas", output_animation=False)
    run_js("$('head').append('<style>.footer{display:none}</style>')")

    put_html(f"<h2>{t('Gui.AppManage.PageTitle')}</h2>")
    put_scope("config_table")
    put_buttons(
        buttons=[
            {
                "label": t("Gui.AppManage.New"),
                "value": "new",
                "disabled": IS_ON_PHONE_CLOUD,
            },
            {"label": t("Gui.AppManage.Import"), "value": "import"},
            {"label": t("Gui.AppManage.Back"), "value": "back"},
        ],
        onclick=[
            (lambda: None) if IS_ON_PHONE_CLOUD else _new,
            _import,
            partial(go_app, "index", new_window=False),
        ],
    )
    _show_table()


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
        "--run",
        nargs="+",
        type=str,
        help="Run alas by config names on startup",
    )
    args, _ = parser.parse_known_args()

    # Apply config
    AlasGUI.set_theme(theme=State.deploy_config.Theme)
    lang.LANG = State.deploy_config.Language
    key = args.key or State.deploy_config.Password
    cdn = args.cdn if args.cdn else State.deploy_config.CDN
    runs = None
    if args.run:
        runs = args.run
    elif State.deploy_config.Run:
        # TODO: refactor poor_yaml_read() to support list
        tmp = State.deploy_config.Run.split(",")
        runs = [l.strip(" ['\"]") for l in tmp if len(l)]
    instances: List[str] = runs

    logger.hr("Webui configs")
    logger.attr("Theme", State.deploy_config.Theme)
    logger.attr("Language", lang.LANG)
    logger.attr("Password", True if key else False)
    logger.attr("CDN", cdn)
    logger.attr("IS_ON_PHONE_CLOUD", IS_ON_PHONE_CLOUD)

    def index():
        if key is not None and not login(key):
            logger.warning(f"{info.user_ip} login failed.")
            time.sleep(1.5)
            run_js("location.reload();")
            return
        gui = AlasGUI()
        local.gui = gui
        gui.run()

    def manage():
        if key is not None and not login(key):
            logger.warning(f"{info.user_ip} login failed.")
            time.sleep(1.5)
            run_js("location.reload();")
            return
        app_manage()

    app = asgi_app(
        applications=[index, manage],
        cdn=cdn,
        static_dir=None,
        debug=True,
        on_startup=[
            startup,
            lambda: ProcessManager.restart_processes(
                instances=instances, ev=updater.event
            ),
        ],
        on_shutdown=[clearup],
    )

    return app
