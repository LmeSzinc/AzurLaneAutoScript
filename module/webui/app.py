# 此文件是 Alas WebUI 的核心逻辑入口类文件。
# 基于 PyWebIO 框架构建了整个可视化控制台，包括任务配置渲染、仪表盘展示、多实例切换及实时日志流转发等前端功能。
import os
import re
import argparse
import json
import queue
import requests
import threading
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from functools import partial
from typing import Dict, List, Optional, Any

# Import fake module before import pywebio to avoid importing unnecessary module PIL
from module.webui.fake_pil_module import import_fake_pil_module

import_fake_pil_module()

from pywebio import config as webconfig
from pywebio.input import file_upload, input, input_group, select
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
from pywebio.session import download, go_app, info, local, register_thread, run_js, set_env, eval_js

import module.webui.lang as lang
from module.config.config import AzurLaneConfig, Function
from module.config.deep import deep_get, deep_iter, deep_set
from module.config.env import IS_ON_PHONE_CLOUD
from module.config.server import to_server
from module.config.utils import (
    alas_instance,
    alas_template,
    dict_to_kv,
    filepath_args,
    filepath_config,
    read_file,
    readable_time,
)
from module.config.utils import time_delta
from module.log_res.log_res import LogRes
from module.logger import logger
from module.log_res import LogRes
from module.ocr.rpc import start_ocr_server_process, stop_ocr_server_process
from module.submodule.submodule import load_config
from module.submodule.utils import get_config_mod
from module.webui.base import Frame
from module.webui.discord_presence import close_discord_rpc, init_discord_rpc
from module.webui.fastapi import asgi_app
from module.webui.lang import _t, t
from module.webui.patch import fix_py37_subprocess_communicate, patch_executor, patch_mimetype
from module.webui.pin import put_input, put_select
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
    set_localstorage,
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
from module.base.device_id import get_device_id

patch_executor()
patch_mimetype()
fix_py37_subprocess_communicate()
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
    time_delta_name_prefix = 'Gui.Dashboard.'
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


def read_webapp_template(filename: str) -> str:
    template_path = Path(os.getcwd()) / 'webapp' / filename
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def build_title_block(title: str, margin_top: int = 12, margin_bottom: int = 8, font_weight: int = 600) -> str:
    tpl = read_webapp_template('title_block.html')
    return tpl.format(
        title=title,
        margin_top=margin_top,
        margin_bottom=margin_bottom,
        font_weight=font_weight,
    )


def build_muted_notice(text: str) -> str:
    tpl = read_webapp_template('muted_notice.html')
    return tpl.format(text=text)


def build_simple_table(headers, rows, extra_style: str = '') -> str:
    tpl = read_webapp_template('simple_table.html')
    thead_cells = ''.join([f'<th style="text-align:left;padding:6px">{h}</th>' for h in headers])
    tbody_rows = ''.join([
        '<tr>' + ''.join([f'<td style="text-align:center;padding:6px">{v}</td>' for v in row]) + '</tr>'
        for row in rows
    ])
    return tpl.format(
        thead_cells=thead_cells,
        tbody_rows=tbody_rows,
        extra_style=extra_style,
    )


def build_recommendation_box(text: str) -> str:
    tpl = read_webapp_template('recommendation_box.html')
    return tpl.format(text=text)


def build_copyable_device_id(device_id: str) -> str:
    tpl = read_webapp_template('copyable_device_id.html')
    return tpl.format(device_id=device_id)


def build_app_manage_title(title: str) -> str:
    tpl = read_webapp_template('app_manage_title.html')
    return tpl.format(title=title)


class AlasGUI(Frame):
    ALAS_MENU: Dict[str, Dict[str, List[str]]]
    ALAS_ARGS: Dict[str, Dict[str, Dict[str, Dict[str, str]]]]
    theme = "default"
    _log = RichLog

    def initial(self) -> None:
        self.ALAS_MENU = read_file(filepath_args("menu", self.alas_mod))
        self.ALAS_ARGS = read_file(filepath_args("args", self.alas_mod))
        self.ALAS_MENU = read_file(filepath_args("menu", self.alas_mod))
        self.ALAS_ARGS = read_file(filepath_args("args", self.alas_mod))
        self._init_alas_config_watcher()

        if self.theme == "apple":
            add_css(filepath_css("apple-alas"))

    def __init__(self) -> None:
        super().__init__()
        # modified keys, return values of pin_wait_change()
        self.modified_config_queue = queue.Queue()
        # alas config name
        self.alas_name = ""
        self.alas_mod = "alas"
        self.alas_config = AzurLaneConfig("template")
        self.initial()
        # rendered state cache
        self.rendered_cache = []
        self.inst_cache = []
        self.load_home = False
        self.af_flag = False
        self._last_announcement_id = None
        self._announcement_result = None
        self._announcement_fetching = False
        self._announcement_force = False



    @use_scope("aside", clear=True)
    def set_aside(self) -> None:
        # TODO: update put_icon_buttons()
        put_icon_buttons(
            Icon.DEVELOP,
            "false",
            buttons=[{"label": t("Gui.Aside.Home"), "value": "Home", "color": "aside"}],
            onclick=[self.ui_develop],
        )
        put_scope("aside_instance", [
            put_scope(f"alas-instance-{i}", [])
            for i, _ in enumerate(alas_instance())
        ])
        self.set_aside_status()
        put_icon_buttons(
            Icon.SETTING,
            "false",
            buttons=[
                {
                    "label": t("Gui.AddAlas.Manage"),
                    "value": "AddAlas",
                    "color": "aside",
                }
            ],
            onclick=[lambda: go_app("manage", new_window=False)],
        )

        current_date = datetime.now().date()
        if current_date.month == 4 and current_date.day == 1:
            self.af_flag = True

    @use_scope("aside_instance")
    def set_aside_status(self) -> None:
        flag = True

        def update(name, seq):
            with use_scope(f"alas-instance-{seq}", clear=True):
                icon_html = Icon.RUN
                rendered_state = ProcessManager.get_manager(name).state
                if rendered_state == 1 and getattr(self, "af_flag", False):
                    icon_html = icon_html[:31] + ' anim-rotate' + icon_html[31:]
                rendered_state = put_icon_buttons(
                    icon_html,
                    "true",
                    buttons=[{"label": name, "value": name, "color": "aside"}],
                    onclick=self.ui_alas,
                )
            return rendered_state


        if not len(self.rendered_cache) or self.load_home:
            # Reload when add/delete new instance | first start app.py | go to HomePage (HomePage load call force reload)
            flag = False
            self.inst_cache.clear()
            self.inst_cache = alas_instance()
        if flag:
            for index, inst in enumerate(self.inst_cache):
                # Check for state change
                state = ProcessManager.get_manager(inst).state
                if state != self.rendered_cache[index]:
                    self.rendered_cache[index] = update(inst, index)
                    flag = False
        else:
            self.rendered_cache.clear()
            clear("aside_instance")
            for index, inst in enumerate(self.inst_cache):
                self.rendered_cache.append(update(inst, index))
            self.load_home = False
        if not flag:
            # Redraw lost focus, now focus on aside button
            aside_name = get_localstorage("aside")
            self.active_button("aside", aside_name)


        return

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
        pywebio_theme = theme if theme in ("default", "dark", "light") else "dark"
        if theme == "socialism":
            pywebio_theme = "default"
        if theme == "apple":
            pywebio_theme = "default"

        webconfig(theme=pywebio_theme)

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

        # 智能调度显示所有统计，侵蚀1练级只显示每日经验检测
        if task in ("OpsiScheduling", "OpsiHazard1Leveling"):
            def _render_opsi_stats():
                try:
                    from module.statistics.opsi_month import get_opsi_stats, compute_monthly_cl1_akashi_ap, get_ap_timeline
                    from module.statistics.cl1_database import db as cl1_db
                    from module.statistics.ship_exp_stats import get_ship_exp_stats
                    # 使用当前实例名称获取统计数据，确保不为空
                    instance_name = self.alas_name if hasattr(self, 'alas_name') and self.alas_name else None
                    if not instance_name:
                        # 使用第一个可用的实例
                        from module.config.utils import alas_instance
                        all_instances = alas_instance()
                        instance_name = all_instances[0] if all_instances else None
                    s = get_opsi_stats(instance_name=instance_name).summary()
                except Exception as e:
                    with use_scope("opsi_stats", clear=True):
                        put_text(f"Failed to load OpSi stats: {e}")
                    return

                # 侵蚀1练级只显示每日经验检测
                if task == "OpsiHazard1Leveling":
                    try:
                        exp_stats = get_ship_exp_stats(instance_name=instance_name)
                        exp_data = exp_stats.data
                        ships_data = exp_data.get("ships", []) if exp_data else []
                        target_level = exp_data.get("target_level", 125) if exp_data else 125
                        last_check_time = exp_data.get("last_check_time", "-") if exp_data else "-"
                    except Exception as e:
                        with use_scope("opsi_stats", clear=True):
                            put_text(f"Failed to load exp stats: {e}")
                        return

                    with use_scope("opsi_stats", clear=True):
                        put_html(build_title_block('每日经验检测'))
                        put_row([put_text(f"检测时间: {last_check_time}"), put_text(f"目标等级: {target_level}")])
                        if ships_data:
                            exp_labels = ["舰位", "等级", "当前经验(本级)", "总经验", "距目标经验", "还需出击", "预计时间"]
                            exp_rows = []
                            from module.statistics.opsi_month import get_opsi_stats as get_opsi_stats_inner
                            current_battles = get_opsi_stats_inner(instance_name=instance_name).summary().get('total_battles', 0)
                            for ship in ships_data:
                                progress = exp_stats.calculate_progress(ship, target_level, current_battles)
                                exp_rows.append([
                                    progress['position'],
                                    progress['level'],
                                    progress['current_exp'],
                                    progress['total_exp'],
                                    progress['exp_needed'] if progress['exp_needed'] > 0 else "-",
                                    progress['battles_needed'] if progress['battles_needed'] > 0 else "-",
                                    progress['time_needed']
                                ])

                            put_html(build_simple_table(exp_labels, exp_rows))
                        else:
                            put_html(build_muted_notice('暂无经验数据，运行侵蚀1练级后将自动记录'))
                    return

                # 智能调度显示所有统计
                labels = ["月份", "战斗场次", "战斗轮次", "出击消耗", "遇见明石次数", "遇见明石概率", "平均体力", "净赚体力", "循环效率", "平均战斗时间", "平均一轮时长"]
                month = s.get("month", "-")
                total = s.get("total_battles", "-")
                try:
                    tb = int(total)
                    rounds = (tb + 1) // 2
                    sortie_cost = rounds * 5
                except Exception:
                    tb = total
                    rounds = "-"
                    sortie_cost = "-"

                akashi = s.get("akashi_encounters", 0)
                try:
                    ak = int(akashi)
                except Exception:
                    ak = akashi

                try:
                    if isinstance(rounds, int) and rounds > 0:
                        rate = float(ak) / float(rounds)
                        akashi_rate = f"{rate * 100:.2f}%"
                    else:
                        akashi_rate = "-"
                except Exception:
                    akashi_rate = "-"

                try:
                    ap_bought = compute_monthly_cl1_akashi_ap(instance_name=instance_name)
                except Exception:
                    ap_bought = "-"

                try:
                    if isinstance(ap_bought, (int, float)) and isinstance(ak, int) and ak > 0:
                        avg_ap = int(float(ap_bought) / ak + 0.5)
                    else:
                        try:
                            ap_tmp = int(ap_bought)
                            if isinstance(ak, int) and ak > 0:
                                avg_ap = int(ap_tmp / ak + 0.5)
                            else:
                                avg_ap = "-"
                        except Exception:
                            avg_ap = "-"
                except Exception:
                    avg_ap = "-"

                try:
                    net_ap = int(ap_bought) - int(sortie_cost)
                except Exception:
                    net_ap = "-"

                try:
                    eff = int(net_ap) / int(sortie_cost) * 100
                    loop_eff = f"{eff:.2f}%"
                except Exception:
                    loop_eff = "-"

                # 获取侵蚀1的平均时长
                try:
                    exp_stats = get_ship_exp_stats(instance_name=instance_name)
                    avg_cl1_battle_time = exp_stats.get_average_battle_time()
                    avg_cl1_round_time = exp_stats.get_average_round_time()
                    exp_per_hour = exp_stats.get_exp_per_hour()
                    today_stats = exp_stats.get_today_stats()
                    
                    # 今日统计
                    if today_stats:
                        today_battles = today_stats.get('battle_count', 0)
                        today_exp = today_stats.get('total_exp_gained', 0)
                        today_run_time = int(today_stats.get('total_run_time', 0) // 60)
                        today_exp_str = f"{today_exp:,}"
                        today_run_str = f"{today_run_time}分钟"
                    else:
                        today_battles = 0
                        today_exp_str = "-"
                        today_run_str = "-"
                    
                    avg_cl1_battle_str = f"{avg_cl1_battle_time:.1f}秒"
                    avg_cl1_round_str = f"{avg_cl1_round_time:.1f}秒"
                    exp_per_hour_str = f"{exp_per_hour:.0f}/小时"
                except Exception:
                    avg_cl1_battle_str = "-"
                    avg_cl1_round_str = "-"
                    exp_per_hour_str = "-"
                    today_battles = 0
                    today_exp_str = "-"
                    today_run_str = "-"

                labels = ["月份", "战斗场次", "战斗轮次", "出击消耗", "遇见明石次数", "遇见明石概率", "平均体力", "净赚体力", "循环效率", "经验效率", "平均战斗时间", "平均一轮时长", "今日战斗", "今日经验", "今日运行"]

                values = [month, tb, rounds, sortie_cost, ak, akashi_rate, avg_ap, net_ap, loop_eff, exp_per_hour_str, avg_cl1_battle_str, avg_cl1_round_str, today_battles, today_exp_str, today_run_str]

                table = [labels, values]

                with use_scope("opsi_stats", clear=True):
                    put_html(build_title_block('雪风大人的侵蚀一数据收集'))
                    put_row([put_text(f"当月购买体力: {ap_bought}")])
                    put_html(build_simple_table(labels, [values]))

                    # ========== 短猫统计数据 ==========
                    try:
                        from datetime import datetime
                        now = datetime.now()
                        meow_data = cl1_db.get_meow_stats(instance_name or "default", now.year, now.month)
                    except Exception as e:
                        meow_data = {}

                    meow_round_times = meow_data.get("round_times", [])
                    meow_battle_count = meow_data.get("battle_count", 0)
                    meow_avg_time = meow_data.get("avg_round_time", 0.0)
                    meow_avg_battle_time = meow_data.get("avg_battle_time", 0.0)

                    try:
                        meow_rounds = len(meow_round_times) if meow_round_times else 0
                    except Exception:
                        meow_rounds = 0

                    if meow_round_times:
                        avg_time_str = f"{meow_avg_time:.1f}秒"
                    else:
                        avg_time_str = "-"

                    if meow_avg_battle_time > 0:
                        avg_battle_time_str = f"{meow_avg_battle_time:.1f}秒"
                    else:
                        avg_battle_time_str = "-"

                    meow_values = [
                        meow_data.get("month", "-"),
                        meow_battle_count,
                        meow_rounds,
                        avg_battle_time_str,  # 平均单场战斗时间
                        avg_time_str,         # 平均一轮短猫时长
                    ]
                    meow_labels = ["月份", "战斗场次", "出击轮次", "平均战斗时间", "平均一轮短猫时长"]

                    put_html(build_title_block('短猫相接数据收集', margin_top=20, margin_bottom=8))
                    put_html(build_simple_table(meow_labels, [meow_values]))

                    # ========== 短猫提前开始建议 ==========
                    try:
                        from module.os.tasks.scheduling import OpsiScheduling
                        # 创建临时实例来调用计算方法
                        scheduling = OpsiScheduling(self.config, task='OpsiScheduling')
                        advance_calc = scheduling.get_meow_advance_calculation()
                    except Exception as e:
                        advance_calc = {}

                    if advance_calc:
                        mode_name = advance_calc.get('mode_name', '-')
                        current_ap = advance_calc.get('current_ap', '-')
                        meow_round_ap = advance_calc.get('meow_round_ap', '-')
                        avg_meow_round_time = advance_calc.get('avg_meow_round_time', 0)
                        available_rounds = advance_calc.get('available_rounds', 0)
                        hours_ahead = advance_calc.get('hours_ahead', 0)
                        recommendation = advance_calc.get('recommendation', '-')

                        put_html(build_title_block('短猫提前开始建议', margin_top=20, margin_bottom=8))
                        put_row([
                            put_text(f"当前AP: {current_ap}"),
                            put_text(f"每轮消耗: {meow_round_ap} AP"),
                            put_text(f"可运行轮数: {available_rounds:.1f}轮"),
                        ])
                        put_row([
                            put_text(f"平均每轮耗时: {avg_meow_round_time:.1f}秒"),
                            put_text(f"当前模式: {mode_name}"),
                            put_text(f"建议提前: {hours_ahead:.1f}小时"),
                        ])
                        put_html(build_recommendation_box(recommendation))

                    def export_opsi_csv(save_to_desktop: bool = True):
                        import io
                        try:
                            from module.statistics.opsi_month import get_opsi_stats, compute_monthly_cl1_akashi_ap
                        except Exception as e:
                            toast(f"导出失败：无法加载统计模块：{e}", color="error")
                            return

                        try:
                            instance_name_local = self.alas_name if hasattr(self, 'alas_name') and self.alas_name else None
                            s_local = get_opsi_stats(instance_name=instance_name_local).summary() or {}
                        except Exception:
                            s_local = {}

                        month_local = s_local.get("month") or datetime.now().strftime("%Y-%m")
                        total_battles_local = int(s_local.get("total_battles") or 0)
                        total_rounds_local = int(s_local.get("total_rounds") or ((total_battles_local + 1) // 2))
                        ap_spent_local = int(s_local.get("ap_spent") or (total_rounds_local * 5))
                        akashi_count_local = int(s_local.get("akashi_encounters") or s_local.get("akashi_count") or 0)

                        if "akashi_percent" in s_local:
                            try:
                                akashi_percent_local = float(s_local.get("akashi_percent") or 0)
                            except Exception:
                                akashi_percent_local = 0.0
                        elif total_rounds_local > 0:
                            akashi_percent_local = (akashi_count_local / total_rounds_local) * 100
                        else:
                            akashi_percent_local = 0.0

                        try:
                            purchased_local = compute_monthly_cl1_akashi_ap(instance_name=instance_name_local) or 0
                        except Exception:
                            purchased_local = 0

                        if akashi_count_local > 0:
                            try:
                                avg_ap_local = int(float(purchased_local) / akashi_count_local + 0.5)
                            except Exception:
                                avg_ap_local = "-"
                        else:
                            avg_ap_local = "-"

                        try:
                            net_ap_local = int((purchased_local or 0) - ap_spent_local)
                        except Exception:
                            net_ap_local = "-"

                        if isinstance(net_ap_local, (int, float)) and ap_spent_local:
                            try:
                                eff_local = (net_ap_local / ap_spent_local) * 100
                            except Exception:
                                eff_local = "-"
                        else:
                            eff_local = "-"

                        labels_local = ["月份", "战斗场次", "战斗轮次", "出击消耗", "遇见明石次数", "遇见明石概率(%)", "平均体力", "净赚体力", "循环效率(%)", "当月购买体力"]
                        values_local = [
                            month_local,
                            total_battles_local,
                            total_rounds_local,
                            ap_spent_local,
                            akashi_count_local,
                            f"{akashi_percent_local:.2f}" if isinstance(akashi_percent_local, (int, float)) else akashi_percent_local,
                            avg_ap_local,
                            net_ap_local,
                            f"{eff_local:.2f}" if isinstance(eff_local, (int, float)) else eff_local,
                            purchased_local,
                        ]

                        output = io.StringIO()
                        output.write(','.join(labels_local) + "\n")
                        def _escape(cell):
                            s = str(cell)
                            if ',' in s or '"' in s or '\n' in s:
                                s = '"' + s.replace('"', '""') + '"'
                            return s
                        output.write(','.join([_escape(c) for c in values_local]) + "\n")
                        csv_bytes = output.getvalue().encode('utf-8-sig')

                        filename_local = f"侵蚀1练级_{month_local}_详细数据.csv"

                        if save_to_desktop:
                            try:
                                desktop_local = Path.home() / 'Desktop'
                                desktop_local.mkdir(parents=True, exist_ok=True)
                                fpath = desktop_local / filename_local
                                with open(fpath, 'wb') as _f:
                                    _f.write(csv_bytes)
                                toast(f"已保存至桌面：{fpath}", color="success")
                            except Exception as e:
                                logger.exception(e)
                                toast(f"保存桌面失败：{e}", color="error")

                    put_row([
                        put_button("刷新", onclick=_render_opsi_stats, color="off"),
                        put_button("导出并保存到桌面", onclick=lambda: export_opsi_csv(True), color="off"),
                    ], size="auto")

            put_scope("opsi_stats", [])
            _render_opsi_stats()
            self.task_handler.add(_render_opsi_stats, 60, True)

            # ========== 体力K线图 ==========
            # 当前视图状态: 'month' 或 'day' 或 'line'
            if not hasattr(self, '_ap_chart_view'):
                self._ap_chart_view = 'line'

            def _render_ap_chart():
                try:
                    from module.statistics.opsi_month import get_ap_timeline
                    instance_name = self.alas_name if hasattr(self, 'alas_name') and self.alas_name else None
                    if not instance_name:
                        from module.config.utils import alas_instance
                        all_instances = alas_instance()
                        instance_name = all_instances[0] if all_instances else None
                    timeline = get_ap_timeline(instance_name=instance_name)
                except Exception as e:
                    with use_scope("ap_chart", clear=True):
                        put_text(f"加载体力数据失败: {e}")
                    return

                if not timeline:
                    with use_scope("ap_chart", clear=True):
                        put_html(build_muted_notice('暂无体力变化数据，运行侵蚀1任务后将自动记录'))
                        put_button("刷新", onclick=_render_ap_chart, color="off")
                    return

                # 解析原始数据点
                from datetime import datetime as _dt
                import json as _json
                raw_points = []
                for pt in timeline:
                    ts_raw = pt.get('ts', '')
                    try:
                        dt = _dt.fromisoformat(ts_raw)
                    except Exception:
                        continue
                    raw_points.append({'dt': dt, 'ap': int(pt.get('ap', 0))})

                if not raw_points:
                    with use_scope("ap_chart", clear=True):
                        put_html(build_muted_notice('暂无有效体力数据'))
                    return

                raw_points.sort(key=lambda p: p['dt'])
                current_view = getattr(self, '_ap_chart_view', 'line')

                labels = []
                opens = []
                highs = []
                lows = []
                closes = []
                counts = []
                ap_list = []

                if current_view == 'line':
                    for p in raw_points:
                        labels.append(p['dt'].strftime('%m-%d %H:%M'))
                        ap_list.append(p['ap'])
                    view_title = "分时曲线 (详细波动)"
                else:
                    from collections import OrderedDict
                    candles = OrderedDict()
                    if current_view == 'day':
                        today = _dt.now().date()
                        today_points = [p for p in raw_points if p['dt'].date() == today]
                        if not today_points:
                            last_date = raw_points[-1]['dt'].date()
                            today_points = [p for p in raw_points if p['dt'].date() == last_date]
                            today = last_date
                        for p in today_points:
                            hour_key = p['dt'].strftime('%H:00')
                            if hour_key not in candles:
                                candles[hour_key] = {'open': p['ap'], 'high': p['ap'], 'low': p['ap'], 'close': p['ap'], 'count': 1}
                            else:
                                c = candles[hour_key]
                                c['high'] = max(c['high'], p['ap'])
                                c['low'] = min(c['low'], p['ap'])
                                c['close'] = p['ap']
                                c['count'] += 1
                        view_title = f"天视图 ({today.strftime('%m-%d')} 小时K线)"
                    else:
                        for p in raw_points:
                            day_key = p['dt'].strftime('%m-%d')
                            if day_key not in candles:
                                candles[day_key] = {'open': p['ap'], 'high': p['ap'], 'low': p['ap'], 'close': p['ap'], 'count': 1}
                            else:
                                c = candles[day_key]
                                c['high'] = max(c['high'], p['ap'])
                                c['low'] = min(c['low'], p['ap'])
                                c['close'] = p['ap']
                                c['count'] += 1
                        view_title = "月视图 (日K线)"
                        
                    if not candles:
                        with use_scope("ap_chart", clear=True):
                            put_html(build_muted_notice('无法聚合K线数据'))
                            put_button("分时", onclick=lambda: (setattr(self, '_ap_chart_view', 'line'), _render_ap_chart()), color="off")
                        return
                    for k, v in candles.items():
                        labels.append(k)
                        opens.append(v['open'])
                        highs.append(v['high'])
                        lows.append(v['low'])
                        closes.append(v['close'])
                        counts.append(v['count'])

                all_ap = [p['ap'] for p in raw_points]
                ap_max = max(all_ap)
                ap_min = min(all_ap)
                ap_avg = int(sum(all_ap) / len(all_ap))
                ap_cur = all_ap[-1]
                if current_view == 'line':
                    ap_change = ap_list[-1] - ap_list[0] if len(ap_list) >= 2 else 0
                    data_points_text = f"共 {len(labels)} 个点"
                else:
                    ap_change = closes[-1] - opens[0] if len(closes) > 0 else 0
                    data_points_text = f"共 {len(labels)} 根K线"
                change_color = '#ef5350' if ap_change >= 0 else '#26a69a'
                change_sign = '+' if ap_change >= 0 else ''

                chart_id = f"ap_cv_{id(self)}"

                html_tpl = read_webapp_template('ap_chart_panel.html')
                html = html_tpl.format(
                    chart_id=chart_id,
                    view_title=view_title,
                    ap_cur=ap_cur,
                    change_color=change_color,
                    change_sign=change_sign,
                    ap_change=ap_change,
                    ap_max=ap_max,
                    ap_min=ap_min,
                    ap_avg=ap_avg,
                    data_points_text=data_points_text,
                )

                js_tpl = read_webapp_template('ap_chart.js')
                js_code = (js_tpl
                    .replace('__CHART_TYPE__', current_view)
                    .replace('__LABELS__', _json.dumps(labels, ensure_ascii=False))
                    .replace('__OPENS__', _json.dumps(opens))
                    .replace('__HIGHS__', _json.dumps(highs))
                    .replace('__LOWS__', _json.dumps(lows))
                    .replace('__CLOSES__', _json.dumps(closes))
                    .replace('__COUNTS__', _json.dumps(counts))
                    .replace('__AP__', _json.dumps(ap_list))
                    .replace('__AVG__', str(ap_avg))
                    .replace('__CHART_ID__', chart_id)
                )
                from pywebio.session import run_js
                with use_scope("ap_chart", clear=True):
                    put_html(html)
                    run_js(js_code)
                    def _switch_view(v):
                        self._ap_chart_view = v
                        _render_ap_chart()
                    put_row([
                        put_button("分时(详细波动)", onclick=lambda: _switch_view('line'), color="off" if current_view!='line' else "primary"),
                        put_button("天视图(小时K)", onclick=lambda: _switch_view('day'), color="off" if current_view!='day' else "primary"),
                        put_button("月视图(日K)", onclick=lambda: _switch_view('month'), color="off" if current_view!='month' else "primary"),
                        put_button("刷新", onclick=_render_ap_chart, color="off"),
                    ], size="auto")

            # 只在 OpsiScheduling 任务下显示体力K线图
            if task == "OpsiScheduling":
                put_scope("ap_chart", [])
                _render_ap_chart()
                self.task_handler.add(_render_ap_chart, 60, True)

            # ========== 舰船经验检测表格 ==========
            def _render_ship_exp():
                try:
                    from module.statistics.ship_exp_stats import get_ship_exp_stats
                    from module.statistics.opsi_month import get_opsi_stats as get_opsi_stats_func
                    # 使用当前实例名称获取统计数据，确保不为空
                    instance_name = self.alas_name if hasattr(self, 'alas_name') and self.alas_name else None
                    if not instance_name:
                        # 使用第一个可用的实例
                        from module.config.utils import alas_instance
                        all_instances = alas_instance()
                        instance_name = all_instances[0] if all_instances else None
                    stats = get_ship_exp_stats(instance_name=instance_name)
                    if not stats.data or not stats.data.get('ships'):
                        with use_scope("ship_exp_table", clear=True):
                            put_html(build_muted_notice('暂无舰船经验数据，请先运行"每日经验检测"任务'))
                        return
                    
                    current_battles = get_opsi_stats_func(instance_name=instance_name).summary().get('total_battles', 0)
                    target_level = stats.data.get('target_level', 125)
                    avg_battle_time = stats.get_average_battle_time()
                    exp_per_hour = stats.get_exp_per_hour()
                    today_stats = stats.get_today_stats()
                    
                    # 从daily_stats获取今日战斗场次
                    today_battles = today_stats.get('battle_count', 0) if today_stats else 0
                    
                    labels = ["舰位", "等级", "当前经验(本级)", "总经验", 
                              "目标等级所需经验", "已战斗场次", "还需经验", 
                              "还需出击", "预计时间"]
                    
                    rows = []
                    for ship in stats.data.get('ships', []):
                        progress = stats.calculate_progress(ship, target_level, current_battles)
                        # 使用今日daily_stats的battle_count作为已战斗场次
                        rows.append([
                            progress['position'],
                            progress['level'],
                            progress['current_exp'],
                            progress['total_exp'],
                            progress['target_exp'],
                            today_battles,  # 使用今日battle_count而非计算值
                            progress['exp_needed'],
                            progress['battles_needed'],
                            progress['time_needed']
                        ])
                    
                    with use_scope("ship_exp_table", clear=True):
                        put_html(build_title_block('每日经验检测：识别到的舰娘等级与升级进度', margin_top=16, margin_bottom=8))
                        put_text(f"上次检查时间: {stats.data.get('last_check_time', '-')}")
                        
                        # 显示效率统计
                        put_row([
                            put_text(f"平均战斗时间: {avg_battle_time:.1f}秒"),
                            put_text(f"平均一轮侵蚀1时长: {stats.get_average_round_time():.1f}秒"),
                            put_text(f"经验效率: {exp_per_hour:.0f}/小时"),
                        ])
                        
                        # 显示今日统计
                        if today_stats:
                            run_minutes = int(today_stats.get('total_run_time', 0) // 60)
                            put_row([
                                put_text(f"今日战斗: {today_stats.get('battle_count', 0)}场"),
                                put_text(f"今日经验: {today_stats.get('total_exp_gained', 0)}"),
                                put_text(f"今日运行: {run_minutes}分钟"),
                            ])
                        else:
                            put_text("暂无今日战斗数据，运行战斗后将自动更新")
                        
                        put_html(build_simple_table(labels, rows, extra_style=' margin-top:8px;'))
                        
                        put_button("刷新", onclick=_render_ship_exp, color="off")
                except Exception as e:
                    with use_scope("ship_exp_table", clear=True):
                        put_text(f"加载舰船经验数据失败: {e}")

                if task == "OpsiScheduling":
                    put_scope("ship_exp_table", [])
                    _render_ship_exp()
                    self.task_handler.add(_render_ship_exp, 60, True)

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
            options = output_kwargs.pop("option", [])
            server = to_server(deep_get(config, 'Alas.Emulator.PackageName', 'cn'))
            available_events = deep_get(self.ALAS_ARGS, keys=f'{task}.{group_name}.{arg_name}.option_{server}')
            if available_events is not None:
                options = [opt for opt in options if opt in available_events]
            output_kwargs["options"] = options
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

            # 在掉落记录组中显示可复制的设备ID
            if group_name == "DropRecord":
                device_id = get_device_id()
                put_html(build_copyable_device_id(device_id))

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
            # version
            local_commit = updater.get_commit(short_sha1=True)
            version = local_commit[0] if local_commit and local_commit[0] else "Unknown"
            put_scope("log-container", [
                put_scope("log", [put_html("")])
            ]).style(f"--device-id: '{get_device_id()}'; --version: 'Ver.{version}';")

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
        if hasattr(self, 'alas') and self.alas is not None:
            self.task_handler.add(log.put_log(self.alas), 0.25, True)

    def set_dashboard_display(self, b):
        self._log.set_dashboard_display(b)
        self.alas_update_dashboard(True)

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
                    # ==================== 自定义弹窗逻辑 ====================
                    # 当保存侵蚀1兑换凭证保留值为 0 时弹出提示
                    if k in [
                        "OpsiHazard1Leveling.OpsiHazard1Leveling.OperationCoinsPreserve",
                        "OpsiScheduling.OpsiScheduling.OperationCoinsPreserve"
                    ] and int(v) == 0:
                        from pywebio.output import popup, put_html, PopupSize
                        popup("你在干什么？", [put_html('<div style="line-height:1.8;font-size:14px;">'
                            '任务帮助文本这里都写了，你是完全不看啊，写了跟白写了一样还问问问我就要我偏不，你就是找骂<br><br>'
                            '为什么保留黄币没有暴露在前端，因为那是用来防呆的，防的就是像你一样的脑瘫自以为是71魔怔人，盲目地将保留数量改成0，然后没有黄币买不起行动力，然后跑跑跑黄币和行动力全亏完又回来瞎鸡巴乱叫，像你妈的个弱智睁大你的马眼看看猫商店的行动力箱子是要用黄币买的，没黄币你买鸡巴还做春秋大梦赚行动力<br><br>'
                            '为什么 Alas社区准则 不允许讨论71，就是因为像你一样的71魔怔人太多了，然后大魔怔人带小魔怔人，跟苍蝇吃屎一样一生生一窝，我不骂你那不知道的还以为你这是主流玩法，我是不知道你从哪里看的狗屎攻略还是民科搞发明创造出来的，你只需要打开功能开始运行就能获得顶尖玩家的决策水平，但是有现成的功能你不用，十足超人高中生发现了世界的真理，只有你是聪明逼剩余都是傻逼<br><br>'
                            '我来告诉你71怎么刷，那就是帮助文本里写的可惜你没看，告诉你答案你不服气我就要改，改改改改你妈了个臭嗨改，能力没有皮是比包皮还皮，能耐得飞起比性无能还能，说白了你不是来寻求最大收益的，你是来砸场子的，你非要Alas对着你那收益屌差的游戏玩法去设计，连同全体Alas用户跟着运行<br><br>'
                            '我来告诉你71魔怔人是怎么样的魔怔，首先第一个就是打死不留黄币，第二大就是打死不短猫<br><br>'
                            '1.打死不留黄币，完全不知道71要消耗黄币，觉得自己很多黄币以为行动力是无中生有超级摸牌<br>'
                            '2.打死不短猫，完全不知道黄币靠短猫回，屯几千行动力当天地银元留给亲妈下葬<br>'
                            '3.打死不带奶，带一摞低级船不带输出不带奶贪经验贪到死，打一回合死一百万人修一百万次<br>'
                            '4.幻想当赌神，年轻人第一次网络菠菜，行动力亏没了不仅大声叫还要继续刷，裤衩子亏没了还要梭哈<br>'
                            '5.幻想刷委托，跑图又慢概率又低，觉得能无限打怪当2-4代餐<br>'
                            '6.幻想有魔法，什么只留蓝箱子能提高猫商店刷新概率，哇说出这话的人不枪毙两小时概率论老师真是死不瞑目<br><br>'
                            '反正我讲了这么多我知道你是肯定不会听的，你的内心肯定是屌你妈逼臭傻逼，完全听不进去，但是我还是要把整个71的玩法再念叨一遍，不是讲给你听的，是讲给看我骂你的人听的<br><br>'
                            '1.71的收益是经验和金菜金材料，以及让你的Alas一直运行虽然不知道在干什么但是感觉很爽。71的经验是每10w黄币73w（单个角色没有心情加成）就像天上掉金子一样稍微接点就够发一辈子的那种。如果你的帐号进入游戏末期，经验没用因为卡心智那收益就是每10w黄币换9.36金菜，石油就2-4刷委托这样能获得经验物资魔方金菜钻石等等所有的游戏资源<br>'
                            '2.71的收益来源是黄币，行动力是催化剂，71大量消耗黄币获取行动力，短猫消耗多余行动力补充部分黄币，二者是相辅相成的，Alas会自动保持他们之间的动态平衡。20小时71能消耗10w黄币多884行动力，再短猫4小时返还3.5w，每月能获取的黄币是有限的因此71的收益也是有限的<br>'
                            '3.运行71的前提是你能完成大世界每日商店深渊隐秘balabala全部来获得金彩材料，多余的黄币再来运行71，否则就是本末倒置<br>'
                            '4.千万不要买紫币，紫币的主要来源是要塞，白票的主要来源是月度boss，只要你大世界用Alas全勤紫币和白票都是不缺的，猫商店紫币多20%那是多20%白票，但在71里白票的价值体系直接作废所有东西用黄币来衡量，买紫币相当于用稀缺资源兑换溢出资源<br>'
                            '5.71本质是赛博菠菜，消耗5行动力赌5%猫商店刷新，外加两个装置各4%其中一个拆了能爆点行动力，赌赢了你别笑赌输了你别叫，没有抽卡保底就是嗯roll， 猫商店刷新权重 解包都有也没有玄学，只能说从数学期望的角度是赚的，但没保底的随机是真的恶心。有1000行动力本钱就是90%概率不翻车，2000就是98%，已经边际效应了再高不能了不如赶紧转换为黄币<br>'
                            '6.建议行动力买满，这样玩输了还有加仓的机会能再次转起来，丢10000油进71产出的经验也比丢主线图高出一个数量级<br>'
                            '7.开启71的任务后Alas的运行逻辑会发生变化，用来提高收益和减少呆瓜，包括前面说的71短猫动态平衡，全局不买紫币，还有最少留100行动力防止明天不够做每日，月初用赚来的行动力做隐秘深渊要塞防止行动力被秒吸干转不起来，月底停71防止浪费'
                            '</div>')], size=PopupSize.LARGE)
                    # ========================================================
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
            group = LogRes(self.alas_config).group(group_name)
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
            _color = f"""background-color:{deep_get(group, 'Color').replace('^', '#')}"""
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
                                            t(f"Gui.Dashboard.{group_name}") + " - " + delta
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
        if hasattr(self, 'alas') and self.alas is not None:
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
            label=t("Gui.MenuDevelop.Announcement"),
            onclick=lambda: self.ui_check_announcement(force=True),
            color="menu",
        ).style(f"--menu-Announcement--")

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
        put_button(label=t("GUI测试 抛出异常事件"), onclick=raise_exception)

        def _force_restart():
            if State.restart_event is not None:
                toast(t("Gui.Toast.AlasRestart"), duration=0, color="error")
                clearup()
                State.restart_event.set()
            else:
                toast(t("Gui.Toast.ReloadEnabled"), color="error")

        put_button(label=t("重启Alas"), onclick=_force_restart)

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
        if hasattr(self, 'state_switch'):
            try:
                self.state_switch.switch()
            except Exception:
                pass

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
        if hasattr(self, 'state_switch'):
            try:
                self.state_switch.switch()
            except Exception:
                # best-effort: ignore if switch not ready
                pass
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
        self.load_home = True
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
                    {"label": "喵体中文", "value": "zh-MIAO"},
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

                    {"label": "新春 ", "value": "socialism", "color": "danger"},
                    {"label": "Apple", "value": "apple", "color": "primary"},
                ],
                onclick=lambda t: set_theme(t),
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

    def _fetch_announcement_thread(self, force=False):
        """
        在后台线程中获取公告数据（非阻塞）
        """
        try:
            from module.base.api_client import ApiClient
            data = ApiClient.get_announcement(timeout=10)
            self._announcement_result = (data, force)
        except Exception as e:
            logger.error(f"Announcement fetch failed: {e}")
            self._announcement_result = (None, force, str(e))
        finally:
            self._announcement_fetching = False

    def _start_announcement_fetch(self, force=False):
        """
        启动异步公告获取。如果已在获取中则跳过。
        """
        if self._announcement_fetching:
            return
        self._announcement_fetching = True
        self._announcement_force = force
        self._announcement_result = None
        threading.Thread(
            target=self._fetch_announcement_thread,
            args=(force,),
            daemon=True
        ).start()

    def _process_announcement_result(self):
        """
        处理异步获取的公告结果并推送到前端。
        在 TaskHandler 循环中调用（非阻塞）。
        Returns:
            True 如果结果已处理，False 如果还在等待
        """
        if self._announcement_fetching or self._announcement_result is None:
            return False

        result = self._announcement_result
        self._announcement_result = None

        # 解包结果
        if len(result) == 3:
            # 有错误
            _, force, error = result
            if force:
                toast(f"Check failed: {error}", color="error")
            return True

        data, force = result

        if data:
            announcement_id = data.get('announcementId')

            # If force is False, check if we need to update
            if not force:
                if announcement_id and announcement_id == self._last_announcement_id:
                    return True

                # Check if browser has seen it (only if not forced)
                try:
                    announcement_id_json = json.dumps(announcement_id)
                    has_shown = eval_js(f"window.alasHasBeenShown({announcement_id_json})")
                    if has_shown:
                        self._last_announcement_id = announcement_id
                        return True
                except Exception:
                    pass

            title_json = json.dumps(data.get('title', ''))
            content_json = json.dumps(data.get('content', ''))
            announcement_id_json = json.dumps(announcement_id)
            url_json = json.dumps(data.get('url', ''))
            force_json = "true" if force else "false"

            logger.info(f"Pushing announcement: {data.get('title')}")
            run_js(f"window.alasShowAnnouncement({title_json}, {content_json}, {announcement_id_json}, {url_json}, {force_json});")

            self._last_announcement_id = announcement_id

        elif force:
            toast("暂无公告 / No announcement", color="info")

        return True

    def ui_check_announcement(self, force=False) -> None:
        """
        Check for announcements (non-blocking).
        Starts async fetch; result is processed in announcement_checker.
        Args:
            force (bool): If True, show announcement even if already shown.
        """
        self._start_announcement_fetch(force=force)
        if force:
            toast("正在获取公告... / Fetching announcement...", color="info")

    def run(self) -> None:
        # setup gui
        set_env(title="Alas", output_animation=False)
        run_js('document.head.append(Object.assign(document.createElement(\'link\'), { rel: \'manifest\', href: \'/static/assets/spa/manifest.json\' }))')
        add_css(filepath_css("alas"))
        if self.is_mobile:
            add_css(filepath_css("alas-mobile"))
        else:
            add_css(filepath_css("alas-pc"))

        if self.theme == "dark":
            add_css(filepath_css("dark-alas"))

        elif self.theme == "socialism":
            add_css(filepath_css("socialism-alas"))
        else:
            add_css(filepath_css("light-alas"))

        # 加载静态 JS 工具文件（公告弹窗、截图查看器、自动刷新等）
        # 替代原来的多个 run_js() 运行时注入
        run_js(
            "var s=document.createElement('script');"
            "s.src='/static/assets/gui/js/alas-utils.js';"
            "document.head.appendChild(s);"
        
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

        def show_update_toast():
            gradient = 'linear-gradient(90deg, #00b894, #0984e3)'
            toast(t("Gui.Toast.ClickToUpdate"), duration=0, position="right", color=gradient, onclick=goto_update)

            run_js(r"""
                setTimeout(function(){
                    var el = document.querySelector('.toastify.toastify-top.toastify-right') || document.querySelector('.toastify.toastify-top') || document.querySelector('.toastify');
                    if (!el) return;
                    el.classList.add('alas-force-text');
                    el.style.boxShadow = '0 6px 18px rgba(0,0,0,0.22)';
                    el.style.zIndex = '2147483647';
                    /* children inherit via .alas-force-text */
                    try{
                        if (el.classList && el.classList.contains('toastify-right')){
                            el.style.position = 'fixed';
                            el.style.top = '8px';
                            el.style.right = '8px';
                            el.style.left = 'auto';
                            el.style.transform = 'none';
                            el.style.margin = '0';
                        } else {
                            el.style.position = 'fixed';
                            el.style.top = '8px';
                            el.style.left = '50%';
                            el.style.right = 'auto';
                            el.style.transform = 'translateX(-50%)';
                            el.style.margin = '0';
                        }
                    }catch(e){}
                }, 80);
            """)

        update_switch = Switch(
            status={
                1: show_update_toast
            },
            get_state=lambda: updater.state,
            name="update_state",
        )

        self.task_handler.add(self.state_switch.g(), 2)
        self.task_handler.add(self.set_aside_status, 2)
        self.task_handler.add(visibility_state_switch.g(), 15)
        self.task_handler.add(update_switch.g(), 1)
        self.task_handler.add(update_switch.g(), 1)
        
        # 公告检查功能（非阻塞）
        def announcement_checker():
            logger.info("公告检查任务启动")
            th = yield  # 获取任务处理器引用
            # 首次检查：触发异步获取
            self._start_announcement_fetch(force=False)
            next_periodic_check = time.time() + 5
            th._task.delay = 0.1   # 始终保持短间隔轮询
            yield
            while True:
                # 处理已有结果（来自定期检查或手动点击）
                self._process_announcement_result()
                # 定期触发新的异步获取
                if not self._announcement_fetching and time.time() >= next_periodic_check:
                    self._start_announcement_fetch(force=False)
                    next_periodic_check = time.time() + 5
                yield

        # 添加公告检查任务（初始延迟5秒）
        self.task_handler.add(announcement_checker(), delay=5)
        
        # 启动任务处理器
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

    put_html(build_app_manage_title(t('Gui.AppManage.PageTitle')))
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

    from deploy.atomic import atomic_failure_cleanup
    atomic_failure_cleanup('./config')

    static_path = os.getcwd()

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
        static_dir=static_path,
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
