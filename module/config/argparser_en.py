import codecs
import sys

from gooey import Gooey, GooeyParser

import module.config.server as server
from alas import AzurLaneAutoScript
from module.config.dictionary import dic_true_eng_to_eng
from module.config.event import dic_event, dic_archives
from module.config.update import get_config
from module.logger import pyw_name
from module.research.preset import DICT_FILTER_PRESET

try:
    if sys.stdout.encoding != 'UTF-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'UTF-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
except Exception:
    pass


@Gooey(
    optional_cols=2,
    program_name=pyw_name.capitalize(),
    image_dir='assets/gooey',
    language_dir='assets/gooey',
    sidebar_title='Function',
    terminal_font_family='Consolas',
    language='english',
    default_size=(1110, 720),
    navigation='SIDEBAR',
    tabbed_groups=True,
    show_success_modal=False,
    show_failure_modal=False,
    # show_stop_warning=False,
    # load_build_config='gooey_config.json',
    # dump_build_config='gooey_config.json',
    richtext_controls=False, auto_start=False,
    menu=[{
        'name': 'File',
        'items': [{
            'type': 'AboutDialog',
            'menuTitle': 'About',
            'name': 'AzurLaneAutoScript',
            'description': 'Alas, an AzurLane automation tool with GUI (Support CN, EN, JP, able to support other servers).',
            'website': 'https://github.com/LmeSzinc/AzurLaneAutoScript'
        }, {
            'type': 'Link',
            'menuTitle': 'Visit our github repository',
            'url': 'https://github.com/LmeSzinc/AzurLaneAutoScript'
        }]
    }, {
        'name': 'Help',
        'items': [{
            'type': 'Link',
            'menuTitle': 'Wiki',
            'url': 'https://github.com/LmeSzinc/AzurLaneAutoScript/wiki'
        }, {
            'type': 'Link',
            'menuTitle': 'Github Token',
            'url': 'https://github.com/settings/tokens'
        }]
    }]
)

def main(ini_name=''):
    if not ini_name:
        ini_name = pyw_name
    config_file = f'./config/{ini_name}.ini'
    config = get_config(ini_name.lower())

    # Load translation dictionary
    dic_gui_to_ini = dic_true_eng_to_eng  # GUI translation dictionary here.
    dic_gui_to_ini.update(dic_event[server.server])
    dic_gui_to_ini.update(dic_archives[server.server])
    dic_ini_to_gui = {v: k for k, v in dic_gui_to_ini.items()}
    # Event list
    event_folder = [f for f in dic_event[server.server].values() if f.startswith('event_')]
    event_latest = event_folder[-1]
    event_folder = [dic_ini_to_gui.get(f, f) for f in event_folder][::-1]
    event_latest = dic_ini_to_gui.get(event_latest, event_latest)
    # Archives list
    archives_folder = [f for f in dic_archives[server.server].values() if f.startswith('war_archives_')]
    archives_folder = [dic_ini_to_gui.get(f, f) for f in archives_folder][::-1]
    # Raid list
    raid_folder = [f for f in dic_event[server.server].values() if f.startswith('raid_')]
    raid_latest = raid_folder[-1]
    raid_folder = [dic_ini_to_gui.get(f, f) for f in raid_folder][::-1]
    raid_latest = dic_ini_to_gui.get(raid_latest, raid_latest)
    # Research preset list
    research_preset = [dic_ini_to_gui.get(f, f) for f in ['customized'] + list(DICT_FILTER_PRESET.keys())]
    # Translate settings in ini file
    saved_config = {}
    for opt, option in config.items():
        for key, value in option.items():
            key = dic_ini_to_gui.get(key, key)
            if value in dic_ini_to_gui:
                value = dic_ini_to_gui.get(value, value)
            if value == 'None':
                value = ''
            saved_config[key] = value
    message = (
        'BlueStacks:\t127.0.0.1:5555\n'
        'NoxPlayer:\t127.0.0.1:62001\n'
        'MuMuPlayer:\t127.0.0.1:7555\n'
        'MemuPlayer:\t127.0.0.1:21503\n'
        'LDPlayer:\t\temulator-5554\n'
    )

    def default(name):
        """Get default value in .ini file.
        Args:
            name (str): option, in chinese.

        Returns:
            str: Default value, in chinese.
        """
        name = name.strip('-')
        return saved_config.get(name, '')

    def choice_list(total):
        return [str(index) for index in range(1, total + 1)]

    # Don't use checkbox in gooey, use drop box instead.
    # https://github.com/chriskiehl/Gooey/issues/148
    # https://github.com/chriskiehl/Gooey/issues/485

    parser = GooeyParser(description=f'AzurLaneAutoScript, An Azur Lane automation tool. Config: {config_file}\nDo not forget to Press start button to save your settings in each function that modifies')
    subs = parser.add_subparsers(help='commands', dest='command')

    # ==========setting==========
    setting_parser = subs.add_parser('setting')

    # 选择关卡
    stage = setting_parser.add_argument_group('Level settings', 'Need to Press start to save your settings.', gooey_options={'label_color': '#931D03'})
    stage.add_argument('--enable_notifications', default=default('--enable_notifications'), choices=['yes', 'no'],
                       help='If enabled will send toast notifications, Windows 10 Only.',
                       gooey_options={'label_color': '#4B5F83'})
    # stage.add_argument('--enable_stop_condition', default=default('--enable_stop_condition'), choices=['yes', 'no'], help='If enabled will start reward loop when triggered any filter below', gooey_options={'label_color': '#4B5F83'})
    stage.add_argument('--enable_exception', default=default('--enable_exception'), choices=['yes', 'no'], help='Enable or disable some exceptions, ALAS will withdraw from the map when it occurs instead of stopping', gooey_options={'label_color': '#4B5F83'})
    stage.add_argument('--enable_fast_forward', default=default('--enable_fast_forward'), choices=['yes', 'no'], help='Enable or disable clearing mode', gooey_options={'label_color': '#4B5F83'})
    stage.add_argument('--enable_2x_book', default=default('--enable_2x_book'), choices=['yes', 'no'], help='Enable or disable 2x book (spends 2x oil/emotion for 2x item drops)', gooey_options={'label_color': '#4B5F83'})

    stop = stage.add_argument_group('Stop condition', 'After triggering, it will not stop immediately. It will complete the current attack first, Set 0 to disable', gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--if_count_greater_than', default=default('--if_count_greater_than'), help='How many map completions\n until ALAS enter in Reward loop.', gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--if_time_reach', default=default('--if_time_reach'), help='How many time in minutes run ALAS until stop\n. It is recommended about\n 10 minutes to complete the current attack. Format 14:59', gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--if_oil_lower_than', default=default('--if_oil_lower_than'), help='Will enter in reward loop when\ntriggered Oil limit', gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--if_get_ship', default=default('--if_get_ship'), choices=['yes', 'no'],
                      help='Will enter in reward loop when\nget a new ship',
                      gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--if_map_reach', default=default('--if_map_reach'), choices=['no', 'map_100', 'map_3_star', 'map_green_without_3_star', 'map_green'], help='', gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--if_trigger_emotion_control', default=default('--if_trigger_emotion_control'), choices=['yes', 'no'], help='Will enter in reward loop when\ntriggered Mood limit', gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--if_reach_lv120', default=default('--if_reach_lv120'), choices=['yes', 'no'], help='Will enter in reward loop when\na ship of lv119 reached lv120 in combat', gooey_options={'label_color': '#4B5F83'})
    # stop.add_argument('--if_dock_full', default=default('--if_dock_full'), choices=['yes', 'no'])

    # 出击舰队
    fleet = setting_parser.add_argument_group('Attack fleet', 'Fleet step enables only in event maps without clear mode', gooey_options={'label_color': '#931D03'})
    fleet.add_argument('--enable_map_fleet_lock', default=default('--enable_map_fleet_lock'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    fleet.add_argument('--enable_fleet_reverse_in_hard', default=default('--enable_fleet_reverse_in_hard'), choices=['yes', 'no'], help='Use fleet 2 for mobs, fleet 1 for boss, only enabled in hard mode and event hard. If enable auto search, this option will be disabled', gooey_options={'label_color': '#4B5F83'})
    fleet.add_argument('--enable_auto_search', default=default('--enable_auto_search'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    fleet.add_argument('--auto_search_setting', default=default('--auto_search_setting'), choices=['fleet1_mob_fleet2_boss', 'fleet1_boss_fleet2_mob', 'fleet1_all_fleet2_standby', 'fleet1_standby_fleet2_all'], gooey_options={'label_color': '#4B5F83'})

    f1 = fleet.add_argument_group('Mob Fleet', 'Players can choose a formation before battle. Though it has no effect appearance-wise, the formations applies buffs to certain stats.\nLine Ahead: Increases Firepower and Torpedo by 15%, but reduces Evasion by 10% (Applies only to Vanguard fleet)\nDouble Line: Increases Evasion by 30%, but decreases Firepower and Torpedo by 5% (Applies only to Vanguard fleet)\nDiamond: Increases Anti-Air by 20% (no penalties, applies to entire fleet).\nIf enable auto search, this is fleet 1', gooey_options={'label_color': '#4B5F83'})
    f1.add_argument('--fleet_index_1', default=default('--fleet_index_1'), choices=['1', '2', '3', '4', '5', '6'], gooey_options={'label_color': '#4B5F83'})
    f1.add_argument('--fleet_formation_1', default=default('--fleet_formation_1'), choices=['Line Ahead', 'Double Line', 'Diamond'], gooey_options={'label_color': '#4B5F83'})
    f1.add_argument('--fleet_auto_mode_1', default=default('--fleet_auto_mode_1'), choices=['combat_auto', 'combat_manual', 'stand_still_in_the_middle', 'hide_in_bottom_left'], gooey_options={'label_color': '#4B5F83'})
    f1.add_argument('--fleet_step_1', default=default('--fleet_step_1'), choices=['1', '2', '3', '4', '5', '6'], help='In event map, fleet has limit on moving, so fleet_step is how far can a fleet goes in one operation, if map cleared, it will be ignored', gooey_options={'label_color': '#4B5F83'})

    f2 = fleet.add_argument_group('Boss Fleet', 'If enable auto search, this is fleet 2', gooey_options={'label_color': '#4B5F83'})
    f2.add_argument('--fleet_index_2', default=default('--fleet_index_2'), choices=['1', '2', '3', '4', '5', '6'], gooey_options={'label_color': '#4B5F83'})
    f2.add_argument('--fleet_formation_2', default=default('--fleet_formation_2'), choices=['Line Ahead', 'Double Line', 'Diamond'], gooey_options={'label_color': '#4B5F83'})
    f2.add_argument('--fleet_auto_mode_2', default=default('--fleet_auto_mode_2'), choices=['combat_auto', 'combat_manual', 'stand_still_in_the_middle', 'hide_in_bottom_left'], gooey_options={'label_color': '#4B5F83'})
    f2.add_argument('--fleet_step_2', default=default('--fleet_step_2'), choices=['1', '2', '3', '4', '5', '6'], help='In event map, fleet has limit on moving, so fleet_step is how far can a fleet goes in one operation, if map cleared, it will be ignored', gooey_options={'label_color': '#4B5F83'})

    # 潜艇设置
    submarine = setting_parser.add_argument_group('Submarine settings', 'Only supported: hunt_only, do_not_use and every_combat', gooey_options={'label_color': '#931D03'})
    submarine.add_argument('--fleet_index_4', default=default('--fleet_index_4'), choices=['do_not_use', '1', '2'], gooey_options={'label_color': '#4B5F83'})
    submarine.add_argument('--submarine_mode', default=default('--submarine_mode'), choices=['do_not_use', 'hunt_only', 'every_combat', 'when_no_ammo', 'when_boss_combat', 'when_boss_combat_boss_appear'], gooey_options={'label_color': '#4B5F83'})

    # 心情控制
    emotion = setting_parser.add_argument_group('Mood control', gooey_options={'label_color': '#931D03'})
    emotion.add_argument('--enable_emotion_reduce', default=default('--enable_emotion_reduce'), help='Set No to disable MOOD control by ALAS', choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    emotion.add_argument('--ignore_low_emotion_warn', default=default('--ignore_low_emotion_warn'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})

    e1 = emotion.add_argument_group('Mob Fleet', 'Emotion limit:\nkeep_high_emotion: 120\navoid_green_face: 40\navoid_yellow_face: 30\navoid_red_face: 2', gooey_options={'label_color': '#4B5F83'})
    e1.add_argument('--emotion_recover_1', default=default('--emotion_recover_1'), choices=['not_in_dormitory', 'dormitory_floor_1', 'dormitory_floor_2'], gooey_options={'label_color': '#4B5F83'})
    e1.add_argument('--emotion_control_1', default=default('--emotion_control_1'), choices=['keep_high_emotion', 'avoid_green_face', 'avoid_yellow_face', 'avoid_red_face'], gooey_options={'label_color': '#4B5F83'})
    e1.add_argument('--hole_fleet_married_1', default=default('--hole_fleet_married_1'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})

    e2 = emotion.add_argument_group('BOSS Fleet', gooey_options={'label_color': '#4B5F83'})
    e2.add_argument('--emotion_recover_2', default=default('--emotion_recover_2'), choices=['not_in_dormitory', 'dormitory_floor_1', 'dormitory_floor_2'], gooey_options={'label_color': '#4B5F83'})
    e2.add_argument('--emotion_control_2', default=default('--emotion_control_2'), choices=['keep_high_emotion', 'avoid_green_face', 'avoid_yellow_face', 'avoid_red_face'], gooey_options={'label_color': '#4B5F83'})
    e2.add_argument('--hole_fleet_married_2', default=default('--hole_fleet_married_2'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})

    # 血量平衡
    hp = setting_parser.add_argument_group('HP control', 'Fleet lock must be turned off to take effect', gooey_options={'label_color': '#931D03'})
    hp.add_argument('--enable_hp_balance', default=default('--enable_hp_balance'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    hp.add_argument('--enable_low_hp_withdraw', default=default('--enable_low_hp_withdraw'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    hp_balance = hp.add_argument_group('HP Balance', '', gooey_options={'label_color': '#4B5F83'})
    hp_balance.add_argument('--scout_hp_difference_threshold', default=default('--scout_hp_difference_threshold'), help='When the difference in HP volume is greater than the threshold, transpose', gooey_options={'label_color': '#4B5F83'})
    hp_balance.add_argument('--scout_hp_weights', default=default('--scout_hp_weights'), help='Should be repaired when there is a difference in Vanguard, format 1000,1000,1000', gooey_options={'label_color': '#4B5F83'})
    hp_add = hp.add_argument_group('Emergency repair', '', gooey_options={'label_color': '#4B5F83'})
    hp_add.add_argument('--emergency_repair_single_threshold', default=default('--emergency_repair_single_threshold'), help='Used when single shipgirl is below the threshold', gooey_options={'label_color': '#4B5F83'})
    hp_add.add_argument('--emergency_repair_hole_threshold', default=default('--emergency_repair_hole_threshold'), help='Used when all front rows or all back rows are below the threshold', gooey_options={'label_color': '#4B5F83'})
    hp_withdraw = hp.add_argument_group('Low HP volume withdrawal', '', gooey_options={'label_color': '#4B5F83'})
    hp_withdraw.add_argument('--low_hp_withdraw_threshold', default=default('--low_hp_withdraw_threshold'), help='When HP is below the threshold, retreat', gooey_options={'label_color': '#4B5F83'})

    # 退役选项
    retire = setting_parser.add_argument_group('Retirement settings', '', gooey_options={'label_color': '#931D03'})
    retire.add_argument('--enable_retirement', default=default('--enable_retirement'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--retire_method', default=default('--retire_method'), choices=['enhance', 'one_click_retire', 'old_retire'], help='If choosing enhance, when not having enough enhance material, will use one click retire', gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--retire_amount', default=default('--retire_amount'), choices=['retire_all', 'retire_10'], gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--enhance_favourite', default=default('--enhance_favourite'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--enhance_order_string', default=default('--enhance_order_string'),
                        help='Use example format "cv > bb > ..." may omit a ship type category altogether to skip otherwise insert at least one white space character to not apply an index filter. Using \'?\' will have ALAS select a category at random, may use multiple in same string',
                        gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--enhance_check_per_category', default=default('--enhance_check_per_category'),
                        help='How many ships at maximum are viewed before moving onto the next category, ships that are \'in battle\' do not count towards this number and are skipped to the next available ship for enhancement',
                        gooey_options={'label_color': '#4B5F83'})

    rarity = retire.add_argument_group('Retirement rarity', 'The ship type selection is not supported yet. Ignore the following options when using one-key retirement', gooey_options={'label_color': '#4B5F83'})
    rarity.add_argument('--retire_n', default=default('--retire_n'), choices=['yes', 'no'], help='N', gooey_options={'label_color': '#4B5F83'})
    rarity.add_argument('--retire_r', default=default('--retire_r'), choices=['yes', 'no'], help='R', gooey_options={'label_color': '#4B5F83'})
    # rarity.add_argument('--retire_sr', default=default('--retire_sr'), choices=['yes', 'no'], help='SR', gooey_options={'label_color': '#4B5F83'})
    # rarity.add_argument('--retire_ssr', default=default('--retire_ssr'), choices=['yes', 'no'], help='SSR', gooey_options={'label_color': '#4B5F83'})

    # 掉落记录
    drop = setting_parser.add_argument_group('Drop record', 'Save screenshots of dropped items, which will slow down the click speed when settlement is enabled', gooey_options={'label_color': '#931D03'})
    drop.add_argument('--enable_drop_screenshot', default=default('--enable_drop_screenshot'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    drop.add_argument('--enable_azurstat', default=default('--enable_azurstat'), choices=['yes', 'no'], help='Upload drop screenshots to azurstats.lyoko.io, only supports research now', gooey_options={'label_color': '#4B5F83'})
    drop.add_argument('--drop_screenshot_folder', default=default('--drop_screenshot_folder'), gooey_options={'label_color': '#4B5F83'})

    # clear = setting_parser.add_argument_group('Wasteland mode', 'Unopened maps will stop after completion. Opened maps will ignore options, and its done if you do not open up')
    # clear.add_argument('--enable_map_clear_mode', default=default('--enable_map_clear_mode'), choices=['yes', 'no'])
    # clear.add_argument('--clear_mode_stop_condition', default=default('--clear_mode_stop_condition'), choices=['map_100', 'map_3_star', 'map_green'])
    # clear.add_argument('--map_star_clear_all', default=default('--map_star_clear_all'), choices=['index_1', 'index_2', 'index_3', 'do_not_use'], help='The first few stars are to destroy all enemy ships')


    # ==========reward==========
    reward_parser = subs.add_parser('reward')
    reward_condition = reward_parser.add_argument_group('Triggering conditions', 'Need to Press start to save your settings, after running it will enter the on-hook vegetable collection mode', gooey_options={'label_color': '#931D03'})
    reward_condition.add_argument('--enable_reward', default=default('--enable_reward'),
                                  choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    reward_condition.add_argument('--reward_interval', default=default('--reward_interval'),
                                  help='How many minutes to trigger collection. Recommend to set a time range, such as "10, 40"', gooey_options={'label_color': '#4B5F83'})
    reward_condition.add_argument('--reward_stop_game_during_interval',
                                  default=default('--reward_stop_game_during_interval'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    reward_condition.add_argument('--enable_daily_reward', default=default('--enable_daily_reward'), choices=['yes', 'no'],
                                  help='Run daily as a part of reward', gooey_options={'label_color': '#4B5F83'})

    reward_general = reward_parser.add_argument_group('General', '', gooey_options={'label_color': '#931D03'})
    reward_general.add_argument('--enable_oil_reward', default=default('--enable_oil_reward'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    reward_general.add_argument('--enable_coin_reward', default=default('--enable_coin_reward'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    reward_general.add_argument('--enable_mission_reward', default=default('--enable_mission_reward'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    reward_general.add_argument('--enable_data_key_collect', default=default('--enable_data_key_collect'), help='Enable collection of data key in war archives.', choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})

    reward_dorm = reward_parser.add_argument_group('Dorm', '', gooey_options={'label_color': '#931D03'})
    reward_dorm.add_argument('--enable_dorm_reward', default=default('--enable_dorm_reward'), choices=['yes', 'no'], help='Dorm collect coins and loves', gooey_options={'label_color': '#4B5F83'})
    reward_dorm.add_argument('--enable_dorm_feed', default=default('--enable_dorm_feed'), choices=['yes', 'no'], help='Dorm replace feed', gooey_options={'label_color': '#4B5F83'})
    reward_dorm.add_argument('--dorm_collect_interval', default=default('--dorm_collect_interval'),
                             help='How many minutes to trigger collection. Recommend to set a time range, such as "10, 40"', gooey_options={'label_color': '#4B5F83'})
    reward_dorm.add_argument('--dorm_feed_interval', default=default('--dorm_feed_interval'),
                             help='How many minutes to replace feed. Recommend to set a time range, such as "10, 40"\nIf 6 ships in dorm, to use 6 kind of food, interval needs to greater than (14, 28, 42, 70, 139, 278)', gooey_options={'label_color': '#4B5F83'})
    reward_dorm.add_argument('--dorm_feed_filter', default=default('--dorm_feed_filter'), help='Like research filter string', gooey_options={'label_color': '#4B5F83'})

    reward_commission = reward_parser.add_argument_group('Commission settings', '', gooey_options={'label_color': '#931D03'})
    reward_commission.add_argument('--enable_commission_reward', default=default('--enable_commission_reward'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    reward_commission.add_argument('--commission_time_limit', default=default('--commission_time_limit'),
                                   help='Ignore orders whose completion time exceeds the limit, Format: 23:30. Fill in 0 if it is not needed', gooey_options={'label_color': '#4B5F83'})

    priority1 = reward_commission.add_argument_group('Commission priority by time duration', '', gooey_options={'label_color': '#931D03'})
    priority1.add_argument('--duration_shorter_than_2', default=default('--duration_shorter_than_2'), help='', gooey_options={'label_color': '#4B5F83'})
    priority1.add_argument('--duration_longer_than_6', default=default('--duration_longer_than_6'), help='', gooey_options={'label_color': '#4B5F83'})
    priority1.add_argument('--expire_shorter_than_2', default=default('--expire_shorter_than_2'), help='', gooey_options={'label_color': '#4B5F83'})
    priority1.add_argument('--expire_longer_than_6', default=default('--expire_longer_than_6'), help='', gooey_options={'label_color': '#4B5F83'})

    priority2 = reward_commission.add_argument_group('Daily Commission priority', '', gooey_options={'label_color': '#931D03'})
    priority2.add_argument('--daily_comm', default=default('--daily_comm'), help='Daily resource development, high-level tactical research and development', gooey_options={'label_color': '#4B5F83'})
    priority2.add_argument('--major_comm', default=default('--major_comm'), help='1200 oil / 1000 oil commission', gooey_options={'label_color': '#4B5F83'})

    priority3 = reward_commission.add_argument_group('Additional commission priority', '', gooey_options={'label_color': '#931D03'})
    priority3.add_argument('--extra_drill', default=default('--extra_drill'), help='Short-range Sailing Training, Coastal Defense Patrol', gooey_options={'label_color': '#4B5F83'})
    priority3.add_argument('--extra_part', default=default('--extra_part'), help='Small Merchant Escort, Forest Protection Commission', gooey_options={'label_color': '#4B5F83'})
    priority3.add_argument('--extra_cube', default=default('--extra_cube'), help='Fleet Exercise Ⅲ, Fleet Escort ExerciseFleet Exercise Ⅲ', gooey_options={'label_color': '#4B5F83'})
    priority3.add_argument('--extra_oil', default=default('--extra_oil'), help='Small-scale Oil Extraction, Large-scale Oil Extraction', gooey_options={'label_color': '#4B5F83'})
    priority3.add_argument('--extra_book', default=default('--extra_book'), help='Small Merchant Escort, Large Merchant Escort', gooey_options={'label_color': '#4B5F83'})

    priority4 = reward_commission.add_argument_group('Urgent commission priority', '', gooey_options={'label_color': '#931D03'})
    priority4.add_argument('--urgent_drill', default=default('--urgent_drill'), help='Defend the transport troops, annihilate the enemy elite troops', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--urgent_part', default=default('--urgent_part'), help='Support Vila Vela Island, support terror Banner', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--urgent_cube', default=default('--urgent_cube'), help='Rescue merchant ship, enemy attack', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--urgent_book', default=default('--urgent_book'), help='Support Tuhaoer Island, support Moe Island', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--urgent_box', default=default('--urgent_box'), help='BIW Gear Transport, NYB Gear Transport', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--urgent_gem', default=default('--urgent_gem'), help='BIW VIP Escort, NYB VIP Escort', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--urgent_ship', default=default('--urgent_ship'), help='Small Launch Ceremony, Fleet Launch Ceremony, Alliance Launch Ceremony', gooey_options={'label_color': '#4B5F83'})

    reward_tactical = reward_parser.add_argument_group('Classroom', 'Only support continuation of skill books, not new skills', gooey_options={'label_color': '#931D03'})
    reward_tactical.add_argument('--enable_tactical_reward', default=default('--enable_tactical_reward'),
                                 choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    reward_tactical.add_argument('--tactical_exp_first', default=default('--tactical_exp_first'),
                                 choices=['yes', 'no'], help='Choose Yes, give priority to the 150% bonus \nSelect No, give priority to the skills book with the same rarity', gooey_options={'label_color': '#4B5F83'})
    # reward_tactical.add_argument('--tactical_night_range', default=default('--tactical_night_range'), help='Format 23:30-06:30')
    reward_tactical.add_argument('--tactical_book_tier_max', default=default('--tactical_book_tier_max'),
                                 choices=['3', '2', '1'], help='Wich skill book will use first\nT3 is a gold book, T2 is a purple book, T1 is a blue book\ntier_max should greater than or equal to tier_min', gooey_options={'label_color': '#4B5F83'})
    reward_tactical.add_argument('--tactical_book_tier_min', default=default('--tactical_book_tier_min'),
                                 choices=['3', '2', '1'], help='Minimal tier to choose.', gooey_options={'label_color': '#4B5F83'})
    # reward_tactical.add_argument('--tactical_book_tier_night', default=default('--tactical_book_tier_night'), choices=['3', '2', '1'])
    # reward_tactical.add_argument('--tactical_exp_first_night', default=default('--tactical_exp_first_night'), choices=['yes', 'no'])
    reward_tactical.add_argument('--tactical_if_no_book_satisfied', default=default('--tactical_if_no_book_satisfied'),
                                 choices=['cancel_tactical', 'use_the_first_book'], gooey_options={'label_color': '#4B5F83'})

    reward_research = reward_parser.add_argument_group('Research', 'If set research_filter_preset=customized, read https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/filter_string_en first\nThe selection of research projects will satiesfy both input and output settings\nCarrying out research statistics, turn on setting - Drop record - enable_azurstat and save, to upload data automatically', gooey_options={'label_color': '#931D03'})
    reward_research.add_argument('--enable_research_reward', default=default('--enable_research_reward'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    research_input = reward_research.add_argument_group('Research input', '', gooey_options={'label_color': '#4B5F83'})
    research_input.add_argument('--research_use_cube', default=default('--research_use_cube'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    research_input.add_argument('--research_use_coin', default=default('--research_use_coin'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    research_input.add_argument('--research_use_part', default=default('--research_use_part'), choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    research_output = reward_research.add_argument_group('Research output', '', gooey_options={'label_color': '#4B5F83'})
    research_output.add_argument('--research_filter_preset', default=default('--research_filter_preset'),
                                 choices=research_preset, gooey_options={'label_color': '#4B5F83'})
    research_output.add_argument('--research_filter_string', default=default('--research_filter_string'),
                                 help='Only if you are using custom preset.', gooey_options={'label_color': '#4B5F83'})

    reward_meowfficer = reward_parser.add_argument_group('Meowfficer', 'If already bought, skip', gooey_options={'label_color': '#931D03'})
    reward_meowfficer.add_argument('--buy_meowfficer', default=default('--buy_meowfficer'), help='From 0 to 15. If no need, fill 0.', gooey_options={'label_color': '#4B5F83'})
    reward_meowfficer.add_argument('--enable_train_meowfficer', default=default('--enable_train_meowfficer'),
                                   help='Enable collection of trained meowfficer and queue all slots for training on Sunday.',
                                   choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})

    reward_guild = reward_parser.add_argument_group('Guild', 'Check Guild Logistics and Operations. Running for every reward loop.', gooey_options={'label_color': '#931D03'})
    reward_guild.add_argument('--enable_guild_logistics', default=default('--enable_guild_logistics'), help='Enable logistics actions if applicable.', choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    reward_guild.add_argument('--enable_guild_operations', default=default('--enable_guild_operations'), help='Enable operations actions if applicable.', choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    reward_guild.add_argument('--guild_operations_join_threshold', default=default('--guild_operations_join_threshold'), help='Enter between 0 and 1\nEx) \'0.5\' join if current progress roughly less than half or \'1\' join regardless of progress', gooey_options={'label_color': '#4B5F83'})
    reward_guild.add_argument('--guild_interval', default=default('--guild_interval'),
                             help='How many minutes to trigger checking. Recommend to set a time range, such as "10, 40"', gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_items = reward_guild.add_argument_group('Logistics item input', 'Available items: t1, t2, t3, oxycola, coolant, coins, oil, and merit. Omitting an item will skip it. Less error-prone with many specified', gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_items.add_argument('--guild_logistics_item_order_string', default=default('--guild_logistics_item_order_string'),
                        gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_plates = reward_guild.add_argument_group('Logistics plate input', 'Available plates: torpedo, antiair, plane, gun, and general. Omitting a plate will skip it. Less error-prone with many specified', gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_plates.add_argument('--guild_logistics_plate_t1_order_string', default=default('--guild_logistics_plate_t1_order_string'),
                        gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_plates.add_argument('--guild_logistics_plate_t2_order_string', default=default('--guild_logistics_plate_t2_order_string'),
                        gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_plates.add_argument('--guild_logistics_plate_t3_order_string', default=default('--guild_logistics_plate_t3_order_string'),
                        gooey_options={'label_color': '#4B5F83'})
    reward_guild_operations_boss = reward_guild.add_argument_group('Operations guild raid boss input', '', gooey_options={'label_color': '#4B5F83'})
    reward_guild_operations_boss.add_argument('--enable_guild_operations_boss_auto', default=default('--enable_guild_operations_boss_auto'),
                                              help='Enable auto-battle of guild raid boss. If fleet composition with or without guild support is incomplete, does not attempt. Enable boss recommend to bypass',
                                              choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    reward_guild_operations_boss.add_argument('--enable_guild_operations_boss_recommend', default=default('--enable_guild_operations_boss_recommend'),
                                              help='Enable auto-recommend a fleet composition for guild raid boss, all guild support is removed if any', choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})

    # ==========emulator==========
    emulator_parser = subs.add_parser('emulator')
    emulator = emulator_parser.add_argument_group('Emulator', 'Need to Press start to save your settings, it will check whether the game is started \nIf the game has not started, it will be started', gooey_options={'label_color': '#931D03'})
    emulator.add_argument('--serial', default=default('--serial'),
                          help='', gooey_options={'label_color': '#4B5F83'})
    emulator.add_argument('--package_name', default='com.YoStarEN.AzurLane', help='', gooey_options={'label_color': '#4B5F83'})
    emulator.add_argument(
        'default_serial_list',
        default=message,
        widget='Textarea',
        help="Some default SERIAL for most popular emulators, Only base values and may change according to the version you use",
        gooey_options={
            'height': 150,
            'show_help': True,
            'show_label': True,
            'readonly': True,
            'label_color': '#4B5F83'
        }
    )

    debug = emulator_parser.add_argument_group('Debug settings', '', gooey_options={'label_color': '#931D03'})
    debug.add_argument('--enable_error_log_and_screenshot_save', default=default('--enable_error_log_and_screenshot_save'),
                       choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    debug.add_argument('--enable_perspective_error_image_save', default=default('--enable_perspective_error_image_save'),
                       choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})

    adb = emulator_parser.add_argument_group('ADB settings', '', gooey_options={'label_color': '#931D03'})
    adb.add_argument('--device_screenshot_method', default=default('--device_screenshot_method'),
                     choices=['aScreenCap', 'uiautomator2', 'ADB'], help='Speed: aScreenCap >> uiautomator2 > ADB', gooey_options={'label_color': '#4B5F83'})
    adb.add_argument('--device_control_method', default=default('--device_control_method'),
                     choices=['minitouch','uiautomator2', 'ADB'], help='Speed: minitouch >> uiautomator2 >> ADB', gooey_options={'label_color': '#4B5F83'})
    adb.add_argument('--combat_screenshot_interval', default=default('--combat_screenshot_interval'),
                     help='Slow down the screenshot speed during battle and reduce CPU', gooey_options={'label_color': '#4B5F83'})

    update = emulator_parser.add_argument_group('ALAS Update Check', '', gooey_options={'label_color': '#931D03'})
    update.add_argument('--enable_update_check', default=default('--enable_update_check'),
                        choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    update.add_argument('--update_method', default=default('--update_method'),
                        choices=['api', 'web'], help='', gooey_options={'label_color': '#4B5F83'})
    update.add_argument('--github_token', default=default('--github_token'),
                        help='To generate your token visit https://github.com/settings/tokens or Help menu above', gooey_options={'label_color': '#4B5F83'})
    update.add_argument('--update_proxy', default=default('--update_proxy'),
                        help='Local http or socks proxy, example: http://127.0.0.1:10809', gooey_options={'label_color': '#4B5F83'})

    # ==========每日任务==========
    daily_parser = subs.add_parser('daily')

    # 选择每日
    daily = daily_parser.add_argument_group('Choose daily', 'Daily tasks, exercises, difficulty charts', gooey_options={'label_color': '#931D03'})
    daily.add_argument('--enable_daily_mission', default=default('--enable_daily_mission'),
                       help='If there are records on the day, skip', choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--enable_hard_campaign', default=default('--enable_hard_campaign'),
                       help='If there are records on the day, skip', choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--enable_exercise', default=default('--enable_exercise'),
                       help='If there is a record after refreshing, skip', choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--enable_raid_daily', default=default('--enable_raid_daily'),
                       help='If there is a record after refreshing, skip', choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--enable_event_ab', default=default('--enable_event_ab'),
                       help='If there is a record after refreshing, skip', choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--enable_event_sp', default=default('--enable_event_sp'),
                       help='If there is a record after refreshing, skip', choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--enable_os_ash_assist', default=default('--enable_os_ash_assist'),
                       help='If there is a record after refreshing, skip', choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})

    # 每日设置
    daily_task = daily_parser.add_argument_group('Daily settings', '', gooey_options={'label_color': '#931D03'})
    daily_task.add_argument('--use_daily_skip', default=default('--use_daily_skip'), help='Use daily skip if available',
                            choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--tactical_training', default=default('--tactical_training'),
                            choices=['daily_air', 'daily_gun', 'daily_torpedo'], gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--fierce_assault', default=default('--fierce_assault'),
                            choices=['high_level', 'medium_level', 'low_level', 'index_1', 'index_2', 'index_3'], gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--supply_line_disruption', default=default('--supply_line_disruption'),
                            choices=['high_level', 'medium_level', 'low_level', 'index_1', 'index_2', 'index_3'], help='Needs to unlock daily skip, if not unlocked, skip', gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--escort_mission', default=default('--escort_mission'),
                            choices=['firepower_high_level', 'air_high_level', 'firepower_low_level', 'index_1', 'index_2', 'index_3'], gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--advance_mission', default=default('--advance_mission'),
                            choices=['high_level', 'medium_level', 'low_level', 'index_1', 'index_2', 'index_3'], gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--daily_fleet', default=default('--daily_fleet'),
                            help='If use one fleet, fill in the index of the fleet, such as 5\nIf use different fleets in different daily, separate index with commas, order: Escort Mission, Advance Mission, Fierce Assault, Tactical Training, such as 5, 5, 5, 6', gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--daily_equipment', default=default('--daily_equipment'),
                            help='Change equipment before playing, unload equipment after playing, do not need to fill in 0 \ncomma, such as 3, 1, 0, 1, 1, 0', gooey_options={'label_color': '#4B5F83'})

    # 困难设置
    hard = daily_parser.add_argument_group('Hard setting', 'Needs to reach clear mode before run', gooey_options={'label_color': '#931D03'})
    hard.add_argument('--hard_campaign', default=default('--hard_campaign'),
                      help='For example 10-4', gooey_options={'label_color': '#4B5F83'})
    hard.add_argument('--hard_fleet', default=default('--hard_fleet'),
                      choices=['1', '2'], help='', gooey_options={'label_color': '#4B5F83'})
    hard.add_argument('--hard_equipment', default=default('--hard_equipment'),
                      help='Change equipment before playing, unload equipment after playing, do not need to fill in 0 \ncomma, such as 3, 1, 0, 1, 1, 0', gooey_options={'label_color': '#4B5F83'})

    # 演习设置
    exercise = daily_parser.add_argument_group('Exercise settings', '', gooey_options={'label_color': '#931D03'})
    exercise.add_argument('--exercise_choose_mode', default=default('--exercise_choose_mode'),
                          choices=['max_exp', 'easiest', 'leftmost', 'easiest_else_exp'], help='', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--exercise_preserve', default=default('--exercise_preserve'),
                          help='Such as 1, which means run until 1/10', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--exercise_try', default=default('--exercise_try'), help='The number of attempts by each opponent', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--exercise_hp_threshold', default=default('--exercise_hp_threshold'),
                          help='HHP <Retreat at Threshold', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--exercise_low_hp_confirm', default=default('--exercise_low_hp_confirm'),
                          help='After HP is below the threshold, it will retreat after a certain period of time \nRecommended 1.0 ~ 3.0', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--exercise_equipment', default=default('--exercise_equipment'),
                          help='Change equipment before playing, unload equipment after playing, do not need to fill in 0 \ncomma, such as 3, 1, 0, 1, 1, 0', gooey_options={'label_color': '#4B5F83'})

    # event_daily_ab
    event_bonus = daily_parser.add_argument_group('Event Daily Bonus', 'bonus for first clear each day', gooey_options={'label_color': '#931D03'})
    event_bonus.add_argument('--event_ab_chapter', default=default('--event_ab_chapter'), choices=['chapter_ab', 'chapter_abcd', 'chapter_t', 'chapter_ht'],
                             help='Chapter with PT bonus', gooey_options={'label_color': '#4B5F83'})
    event_bonus.add_argument('--event_sp_mob_fleet', default=default('--event_sp_mob_fleet'), choices=['1', '2'],
                             help='', gooey_options={'label_color': '#4B5F83'})
    event_bonus.add_argument('--event_name_ab', default=event_latest, choices=event_folder,
                             help='There a dropdown menu with many options', gooey_options={'label_color': '#4B5F83'})

    # Raid daily
    raid_bonus = daily_parser.add_argument_group('Raid settings', '', gooey_options={'label_color': '#931D03'})
    raid_bonus.add_argument('--raid_daily_name', default=raid_latest, choices=raid_folder, help='', gooey_options={'label_color': '#4B5F83'})
    raid_bonus.add_argument('--raid_hard', default=default('--raid_hard'), choices=['yes', 'no'], help='', gooey_options={'label_color': '#4B5F83'})
    raid_bonus.add_argument('--raid_normal', default=default('--raid_normal'), choices=['yes', 'no'], help='', gooey_options={'label_color': '#4B5F83'})
    raid_bonus.add_argument('--raid_easy', default=default('--raid_easy'), choices=['yes', 'no'], help='', gooey_options={'label_color': '#4B5F83'})

    # OS daily
    raid_bonus = daily_parser.add_argument_group('OS settings', '', gooey_options={'label_color': '#931D03'})
    raid_bonus.add_argument('--os_ash_assist_tier', default=default('--os_ash_assist_tier'), help='Find beacons with tier greater or equal than this', gooey_options={'label_color': '#4B5F83'})

    # ==========event_daily_ab==========
    # event_ab_parser = subs.add_parser('event_daily_bonus')
    # event_name = event_ab_parser.add_argument_group('Choose an event', 'bonus for first clear each day')
    # event_name.add_argument('--event_name_ab', default=event_latest, choices=event_folder, help='There a dropdown menu with many options')
    # event_name.add_argument('--enable_hard_bonus', default=default('--enable_hard_bonus'), choices=['yes', 'no'], help='Will enable Daily bonus for Event hard maps') # Trying implement all event maps

    # ==========main==========
    main_parser = subs.add_parser('Main_campaign')
    # 选择关卡
    stage = main_parser.add_argument_group('Choose a level',
                                           'Main campaign, Currently, not all maps are being supported, check the folder /doc/development_en.md to know how add new maps',
                                           gooey_options={'label_color': '#931D03'})
    stage.add_argument('--main_stage', default=default('--main_stage'), help='E.g 7-2',
                       gooey_options={'label_color': '#4B5F83'})
    stage.add_argument('--campaign_mode', default=default('--campaign_mode'), help='Useful if you want to clear a hard mode map',
                       choices=['normal', 'hard'], gooey_options={'label_color': '#4B5F83'})

    # ==========event==========
    event_parser = subs.add_parser('event')

    description = """

    """
    event = event_parser.add_argument_group(
        'Choose a level', '\n'.join([line.strip() for line in description.strip().split('\n')]), gooey_options={'label_color': '#931D03'})
    event.add_argument('--event_stage', default=default('--event_stage'), help='Type stage name, not case sensitive, E.g D3, SP3, HT6', gooey_options={'label_color': '#4B5F83'})
    event.add_argument('--event_name', default=event_latest, choices=event_folder, help='There a dropdown menu with many options', gooey_options={'label_color': '#4B5F83'})

    # ==========sos==========
    sos_parser = subs.add_parser('sos')
    sos = sos_parser.add_argument_group(
        'sos settings', 'Set fleets for SOS maps, order: fleet_1, fleet_2, submarine_fleet\nsuch as "4, 6", "4, 0", "4, 6, 1"\nFill 0 to skip a map', gooey_options={'label_color': '#931D03'})
    sos.add_argument('--sos_fleets_chapter_3', default=default('--sos_fleets_chapter_3'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--sos_fleets_chapter_4', default=default('--sos_fleets_chapter_4'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--sos_fleets_chapter_5', default=default('--sos_fleets_chapter_5'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--sos_fleets_chapter_6', default=default('--sos_fleets_chapter_6'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--sos_fleets_chapter_7', default=default('--sos_fleets_chapter_7'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--sos_fleets_chapter_8', default=default('--sos_fleets_chapter_8'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--sos_fleets_chapter_9', default=default('--sos_fleets_chapter_9'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--sos_fleets_chapter_10', default=default('--sos_fleets_chapter_10'), gooey_options={'label_color': '#4B5F83'})

    # ==========war_archives==========
    war_archives_parser = subs.add_parser('war_archives')
    war_archives = war_archives_parser.add_argument_group(
        'war archives settings', 'Type a stage and select a corresponding event for that stage', gooey_options={'label_color': '#931D03'})
    war_archives.add_argument('--war_archives_stage', default=default('--war_archives_stage'), help='Type stage name, not case sensitive, E.g D3, SP3, HT6', gooey_options={'label_color': '#4B5F83'})
    war_archives.add_argument('--war_archives_name', default=default('--war_archives_name'), choices=archives_folder, help='There a dropdown menu with many options', gooey_options={'label_color': '#4B5F83'})

    # ==========Raid==========
    raid_parser = subs.add_parser('raid')
    raid = raid_parser.add_argument_group('Choose a raid', '', gooey_options={'label_color': '#931D03'})
    raid.add_argument('--raid_name', default=raid_latest, choices=raid_folder, help='', gooey_options={'label_color': '#4B5F83'})
    raid.add_argument('--raid_mode', default=default('--raid_mode'), choices=['hard', 'normal', 'easy'], help='', gooey_options={'label_color': '#4B5F83'})
    raid.add_argument('--raid_use_ticket', default=default('--raid_use_ticket'), choices=['yes', 'no'], help='', gooey_options={'label_color': '#4B5F83'})

    # ==========半自动==========
    semi_parser = subs.add_parser('semi_auto')
    semi = semi_parser.add_argument_group('Semi-automatic mode', 'Manual selection of enemies, automatic settlement, used to attack unsuited pictures', gooey_options={'label_color': '#931D03'})
    semi.add_argument('--enable_semi_map_preparation', default=default('--enable_semi_map_preparation'), help='',
                      choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})
    semi.add_argument('--enable_semi_story_skip', default=default('--enable_semi_story_skip'), help='Note that this will automatically confirm all the prompt boxes, including the red face attack',
                      choices=['yes', 'no'], gooey_options={'label_color': '#4B5F83'})

    # ==========c11_affinity_farming==========
    c_1_1_parser = subs.add_parser('c1-1_affinity_farming')
    c_1_1 = c_1_1_parser.add_argument_group('c1-1_affinity_farming', 'Will auto turn off clearing mode\nWith MVP, 8 battle to 1 affnity. Without MVP, 16 battle to 1 affnity.',
                                            gooey_options={'label_color': '#931D03'})
    c_1_1.add_argument('--affinity_battle_count', default=default('--affinity_battle_count'), help='Example: 32', gooey_options={'label_color': '#4B5F83'})

    # ==========c72_mystery_farming==========
    c_7_2_parser = subs.add_parser('c7-2_mystery_farming')
    c_7_2 = c_7_2_parser.add_argument_group('c7-2_mystery_farming', '', gooey_options={'label_color': '#931D03'})
    c_7_2.add_argument('--boss_fleet_step_on_a3', default=default('--boss_fleet_step_on_a3'),
                       choices=['yes', 'no'], help='A3 has enemies, G3, C3, E3', gooey_options={'label_color': '#4B5F83'})

    # ==========c122_leveling==========
    c_12_2_parser = subs.add_parser('c12-2_leveling')
    c_12_2 = c_12_2_parser.add_argument_group('12-2 enemy search settings', '', gooey_options={'label_color': '#931D03'})
    c_12_2.add_argument('--s3_enemy_tolerance', default=default('--s3_enemy_tolerance'),
                        choices=['0', '1', '2', '10'], help='The maximum number of battles to fight against large enemies', gooey_options={'label_color': '#4B5F83'})

    # ==========c124_leveling==========
    c_12_4_parser = subs.add_parser('c12-4_leveling')
    c_12_4 = c_12_4_parser.add_argument_group('12-4 Search enemy settings', 'Need to ensure that the team has a certain strength', gooey_options={'label_color': '#931D03'})
    c_12_4.add_argument('--non_s3_enemy_enter_tolerance', default=default('--non_s3_enemy_enter_tolerance'),
                        choices=['0', '1', '2'], help='Avoid enemy too strong', gooey_options={'label_color': '#4B5F83'})
    c_12_4.add_argument('--non_s3_enemy_withdraw_tolerance', default=default('--non_s3_enemy_withdraw_tolerance'),
                        choices=['0', '1', '2', '10'], help='How many battles will be fought after there is no large scale enemy', gooey_options={'label_color': '#4B5F83'})
    c_12_4.add_argument('--ammo_pick_up_124', default=default('--ammo_pick_up_124'),
                        choices=['2', '3', '4', '5'], help='How many battles before pick ammo, the recommended is 3', gooey_options={'label_color': '#4B5F83'})

    # ==========OS semi auto==========
    os_semi_parser = subs.add_parser('os_semi_auto')
    os_semi = os_semi_parser.add_argument_group('os_semi_auto', 'Start and finish combat automatically\nOnly recommended to use in normal zones and safe zones', gooey_options={'label_color': '#931D03'})
    os_semi.add_argument('--enable_os_semi_story_skip', default=default('--enable_os_semi_story_skip'), choices=['yes', 'no'], help='Note that this will automatically choose the options in map events', gooey_options={'label_color': '#4B5F83'})

    # ==========OS clear map==========
    # os_semi_parser = subs.add_parser('os_clear_map')
    # os_semi = os_semi_parser.add_argument_group('os_clear_map', 'Only recommended to use in save zones. To use in normal zones, execute air search manually first.\nUsage: Enter map manually and run\nRecommend to re-check map manually after run', gooey_options={'label_color': '#931D03'})
    # os_semi.add_argument('--enable_os_ash_attack', default=default('--enable_os_ash_attack'), choices=['yes', 'no'], help='Attack ash if beacon data is full', gooey_options={'label_color': '#4B5F83'})

    # ==========OS clear world==========
    os_world_parser = subs.add_parser('os_world_clear')
    os_world = os_world_parser.add_argument_group('OS world clear',
                                                  'Must clear story mode of all available chapters and '
                                                  'purchase the OS logger item in main supply shop for '
                                                  '5k oil before using this module\n\n'
                                                  'Explore all unsafe zones between configured range inclusive and turn into safe\n'
                                                  'Captains should configure appropriately based on current adaptibility numbers '
                                                  'and fleet formation',
                                                  gooey_options={'label_color': '#931D03'})
    os_world.add_argument('--os_world_min_level', default=default('--os_world_min_level'),
                          help='Use same number in both fields for exactly 1 range',
                          choices=['1', '2', '3', '4', '5', '6'],
                          gooey_options={'label_color': '#4B5F83'})
    os_world.add_argument('--os_world_max_level', default=default('--os_world_max_level'),
                          help='Recommend 4 or lower for single fleet clear, 5 and higher '
                               'can be difficult with low adaptibility',
                          choices=['1', '2', '3', '4', '5', '6'],
                          gooey_options={'label_color': '#4B5F83'})

    # ==========OS fully auto==========
    os_parser = subs.add_parser('os_fully_auto')
    os = os_parser.add_argument_group('OS fully auto', 'Run sequence: Accept dailies and buy supplies > do dailies > do obscure zone > meowfficer farming\nPort shop is a limited pool of items. Ports have the same items, but appear randomly. Buy all if you want good items\nShop priority format: ActionPoint > PurpleCoins > TuringSample > RepairPack', gooey_options={'label_color': '#931D03'})
    os.add_argument('--do_os_in_daily', default=default('--do_os_in_daily'), choices=['yes', 'no'], help='Do OS as a part of daily', gooey_options={'label_color': '#4B5F83'})

    os_daily = os.add_argument_group('OS daily', '', gooey_options={'label_color': '#931D03'})
    os_daily.add_argument('--enable_os_mission_accept', default=default('--enable_os_mission_accept'), choices=['yes', 'no'], help='Accept all missions in port', gooey_options={'label_color': '#4B5F83'})
    os_daily.add_argument('--enable_os_mission_finish', default=default('--enable_os_mission_finish'), choices=['yes', 'no'], help='Goto the zone of daily and clear', gooey_options={'label_color': '#4B5F83'})
    os_daily.add_argument('--enable_os_supply_buy', default=default('--enable_os_supply_buy'), choices=['yes', 'no'], help='Buy all daily supplies', gooey_options={'label_color': '#4B5F83'})
    os_daily.add_argument('--enable_os_ash_attack', default=default('--enable_os_ash_attack'), choices=['yes', 'no'], help='Attack ash if beacon data is full', gooey_options={'label_color': '#4B5F83'})

    os_farm = os.add_argument_group('Operation Siren', '', gooey_options={'label_color': '#931D03'})
    os_farm.add_argument('--enable_os_obscure_finish', default=default('--enable_os_obscure_finish'), choices=['yes', 'no'], help='[Developing]Clear all obscured zones', gooey_options={'label_color': '#4B5F83'})
    os_farm.add_argument('--enable_os_meowfficer_farming', default=default('--enable_os_meowfficer_farming'), choices=['yes', 'no'], help='Do meowfficer searching point farming', gooey_options={'label_color': '#4B5F83'})
    os_farm.add_argument('--os_meowfficer_farming_level', default=default('--os_meowfficer_farming_level'), choices=['1', '2', '3', '4', '5', '6'], help='Corruption 3 and 5 have higher meowfficer point per action point. Corruption 5 is recommended', gooey_options={'label_color': '#4B5F83'})

    os_setting = os.add_argument_group('OS setting', '', gooey_options={'label_color': '#931D03'})
    os_setting.add_argument('--enable_os_action_point_buy', default=default('--enable_os_action_point_buy'), choices=['yes', 'no'], help='Use oil to buy action points, buy first then use AP boxes', gooey_options={'label_color': '#4B5F83'})
    os_setting.add_argument('--os_action_point_preserve', default=default('--os_action_point_preserve'), help='Include AP boxes, stop if lower than this', gooey_options={'label_color': '#4B5F83'})
    os_setting.add_argument('--os_repair_threshold', default=default('--os_repair_threshold'), help='Retreat to nearest azur port for repairs if any ship\'s HP in fleet is below configured threshold after zone clear, limit between 0 and 1', gooey_options={'label_color': '#4B5F83'})

    os_shop = os.add_argument_group('OS shop', '', gooey_options={'label_color': '#931D03'})
    os_shop.add_argument('--enable_os_akashi_shop_buy', default=default('--enable_os_akashi_shop_buy'), choices=['yes', 'no'], help='', gooey_options={'label_color': '#4B5F83'})
    os_shop.add_argument('--os_akashi_shop_priority', default=default('--os_akashi_shop_priority'), help='', gooey_options={'label_color': '#4B5F83'})

    args = parser.parse_args()

    # Convert option from chinese to english.
    out = {}
    for key, value in vars(args).items():
        key = dic_gui_to_ini.get(key, key)
        value = dic_gui_to_ini.get(value, value)
        out[key] = value
    args = out

    # Update option to .ini file.
    command = args['command'].capitalize()
    config['Command']['command'] = command
    for key, value in args.items():
        config[command][key] = str(value)
    config.write(codecs.open(config_file, "w+", "utf8"))

    # Call AzurLaneAutoScript
    alas = AzurLaneAutoScript(ini_name=ini_name)
    alas.run(command=command)
