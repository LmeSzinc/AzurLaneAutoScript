import codecs
import configparser
import os
import shutil

from gooey import Gooey, GooeyParser

from alas import AzurLaneAutoScript
from module.config.dictionary import dic_true_eng_to_eng, dic_eng_to_true_eng
from module.logger import logger, pyw_name


def update_config_from_template(config, file):
    """
    Args:
        config (configparser.ConfigParser):

    Returns:
        configparser.ConfigParser:
    """
    template = configparser.ConfigParser(interpolation=None)
    template.read_file(codecs.open(f'./config/template.ini', "r", "utf8"))
    changed = False
    # Update section.
    for section in template.sections():
        if not config.has_section(section):
            config.add_section(section)
            changed = True
    for section in config.sections():
        if not template.has_section(section):
            config.remove_section(section)
            changed = True
    # Update option
    for section in template.sections():
        for option in template.options(section):
            if not config.has_option(section, option):
                config.set(section, option, value=template.get(section, option))
                changed = True
    for section in config.sections():
        for option in config.options(section):
            if not template.has_option(section, option):
                config.remove_option(section, option)
                changed = True
    # Save
    if changed:
        config.write(codecs.open(file, "w+", "utf8"))
    return config


@Gooey(
    optional_cols=2,
    program_name=pyw_name.capitalize(),
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
)
def main(ini_name=''):
    if not ini_name:
        ini_name = pyw_name
    ini_name = ini_name.lower()

    # Load default value from .ini file.
    config_file = f'./config/{ini_name}.ini'
    config = configparser.ConfigParser(interpolation=None)
    try:
        config.read_file(codecs.open(config_file, "r", "utf8"))
    except FileNotFoundError:
        logger.info('Config file not exists, copy from ./config/template.ini')
        shutil.copy('./config/template.ini', config_file)
        config.read_file(codecs.open(config_file, "r", "utf8"))

    config = update_config_from_template(config, file=config_file)

    event_folder = [dic_eng_to_true_eng.get(f, f) for f in os.listdir('./campaign') if f.startswith('event_')][::-1]

    saved_config = {}
    for opt, option in config.items():
        for key, value in option.items():
            key = dic_eng_to_true_eng.get(key, key)
            if value in dic_eng_to_true_eng:
                value = dic_eng_to_true_eng.get(value, value)
            if value == 'None':
                value = ''

            saved_config[key] = value

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

    parser = GooeyParser(description=f'AzurLaneAutoScript, An Azur Lane automation tool. Config: {config_file}')
    subs = parser.add_subparsers(help='commands', dest='command')

    # ==========setting==========
    setting_parser = subs.add_parser('setting')

    # 选择关卡
    stage = setting_parser.add_argument_group('Level settings', 'Need to run once to save options')
    stage.add_argument('--enable_stop_condition', default=default('--enable_stop_condition'), choices=['yes', 'no'])
    stage.add_argument('--enable_fast_forward', default=default('--enable_fast_forward'), choices=['yes', 'no'], help='Enable or disable clearing mode')

    stop = stage.add_argument_group('Stop condition', 'After triggering, it will not stop immediately. It will complete the current attack first, and fill in 0 if it is not needed.')
    stop.add_argument('--if_count_greater_than', default=default('--if_count_greater_than'), help='The previous setting will be used, and the number\n of deductions will be deducted after completion of the attack until it is cleared.')
    stop.add_argument('--if_time_reach', default=default('--if_time_reach'), help='Use the time within the next 24 hours, the previous setting will be used, and it will be cleared\n after the trigger. It is recommended to advance about\n 10 minutes to complete the current attack. Format 14:59')
    stop.add_argument('--if_oil_lower_than', default=default('--if_oil_lower_than'))
    stop.add_argument('--if_trigger_emotion_control', default=default('--if_trigger_emotion_control'), choices=['yes', 'no'], help='If yes, wait for reply, complete this time, stop \nIf no, wait for reply, complete this time, continue')
    stop.add_argument('--if_dock_full', default=default('--if_dock_full'), choices=['yes', 'no'])

    # 出击舰队
    fleet = setting_parser.add_argument_group('Attack fleet', 'No support for alternate lane squadrons, inactive map or weekly mode will ignore the step setting')
    fleet.add_argument('--enable_fleet_control', default=default('--enable_fleet_control'), choices=['yes', 'no'])
    fleet.add_argument('--enable_map_fleet_lock', default=default('--enable_map_fleet_lock'), choices=['yes', 'no'])

    f1 = fleet.add_argument_group('Mob Fleet', 'Players can choose a formation before battle. Though it has no effect appearance-wise, the formations applies buffs to certain stats.\nLine Ahead: Increases Firepower and Torpedo by 15%, but reduces Evasion by 10% (Applies only to Vanguard fleet)\nDouble Line: Increases Evasion by 30%, but decreases Firepower and Torpedo by 5% (Applies only to Vanguard fleet)\nDiamond: Increases Anti-Air by 20% (no penalties, applies to entire fleet)')
    f1.add_argument('--fleet_index_1', default=default('--fleet_index_1'), choices=['1', '2', '3', '4', '5', '6'])
    f1.add_argument('--fleet_formation_1', default=default('--fleet_formation_1'), choices=['Line Ahead', 'Double Line', 'Diamond'])
    f1.add_argument('--fleet_step_1', default=default('--fleet_step_1'), choices=['1', '2', '3', '4', '5', '6'], help='In event map, fleet has limit on moving, so fleet_step is how far can a fleet goes in one operation, if map cleared, it will be ignored')

    f2 = fleet.add_argument_group('Boss Fleet')
    f2.add_argument('--fleet_index_2', default=default('--fleet_index_2'), choices=['do_not_use', '1', '2', '3', '4', '5', '6'])
    f2.add_argument('--fleet_formation_2', default=default('--fleet_formation_2'), choices=['Line Ahead', 'Double Line', 'Diamond'])
    f2.add_argument('--fleet_step_2', default=default('--fleet_step_2'), choices=['1', '2', '3', '4', '5', '6'], help='In event map, fleet has limit on moving, so fleet_step is how far can a fleet goes in one operation, if map cleared, it will be ignored')

    f3 = fleet.add_argument_group('Alternate Mob Fleet')
    f3.add_argument('--fleet_index_3', default=default('--fleet_index_3'), choices=['do_not_use', '1', '2', '3', '4', '5', '6'])
    f3.add_argument('--fleet_formation_3', default=default('--fleet_formation_3'), choices=['Line Ahead', 'Double Line', 'Diamond'])
    f3.add_argument('--fleet_step_3', default=default('--fleet_step_3'), choices=['1', '2', '3', '4', '5', '6'], help='In event map, fleet has limit on moving, so fleet_step is how far can a fleet goes in one operation, if map cleared, it will be ignored')

    f4 = fleet.add_argument_group('Auto-mode')
    f4.add_argument('--combat_auto_mode', default=default('--combat_auto_mode'), choices=['combat_auto', 'combat_manual', 'stand_still_in_the_middle'])

    # 潜艇设置
    submarine = setting_parser.add_argument_group('Submarine settings', 'Only supported: hunt_only, do_not_use and every_combat')
    submarine.add_argument('--fleet_index_4', default=default('--fleet_index_4'), choices=['do_not_use', '1', '2'])
    submarine.add_argument('--submarine_mode', default=default('--submarine_mode'), choices=['do_not_use', 'hunt_only', 'every_combat', 'when_no_ammo', 'when_boss_combat', 'when_boss_combat_boss_appear'])

    # 心情控制
    emotion = setting_parser.add_argument_group('Mood control')
    emotion.add_argument('--enable_emotion_reduce', default=default('--enable_emotion_reduce'), choices=['yes', 'no'])
    emotion.add_argument('--ignore_low_emotion_warn', default=default('--ignore_low_emotion_warn'), choices=['yes', 'no'])

    e1 = emotion.add_argument_group('Mob Fleet')
    e1.add_argument('--emotion_recover_1', default=default('--emotion_recover_1'), choices=['not_in_dormitory', 'dormitory_floor_1', 'dormitory_floor_2'])
    e1.add_argument('--emotion_control_1', default=default('--emotion_control_1'), choices=['keep_high_emotion', 'avoid_green_face', 'avoid_yellow_face', 'avoid_red_face'])
    e1.add_argument('--hole_fleet_married_1', default=default('--hole_fleet_married_1'), choices=['yes', 'no'])

    e2 = emotion.add_argument_group('BOSS Fleet')
    e2.add_argument('--emotion_recover_2', default=default('--emotion_recover_2'), choices=['not_in_dormitory', 'dormitory_floor_1', 'dormitory_floor_2'])
    e2.add_argument('--emotion_control_2', default=default('--emotion_control_2'), choices=['keep_high_emotion', 'avoid_green_face', 'avoid_yellow_face', 'avoid_red_face'])
    e2.add_argument('--hole_fleet_married_2', default=default('--hole_fleet_married_2'), choices=['yes', 'no'])

    e3 = emotion.add_argument_group('Alternate Mob Fleet', 'Will be used when the first team triggers mood control')
    e3.add_argument('--emotion_recover_3', default=default('--emotion_recover_3'), choices=['not_in_dormitory', 'dormitory_floor_1', 'dormitory_floor_2'])
    e3.add_argument('--emotion_control_3', default=default('--emotion_control_3'), choices=['keep_high_emotion', 'avoid_green_face', 'avoid_yellow_face', 'avoid_red_face'])
    e3.add_argument('--hole_fleet_married_3', default=default('--hole_fleet_married_3'), choices=['yes', 'no'])

    # 血量平衡
    hp = setting_parser.add_argument_group('HP control', 'Fleet lock must be turned off to take effect')
    hp.add_argument('--enable_hp_balance', default=default('--enable_hp_balance'), choices=['yes', 'no'])
    hp.add_argument('--enable_low_hp_withdraw', default=default('--enable_low_hp_withdraw'), choices=['yes', 'no'])
    hp_balance = hp.add_argument_group('HP Balance', '')
    hp_balance.add_argument('--scout_hp_difference_threshold', default=default('--scout_hp_difference_threshold'), help='When the difference in HP volume is greater than the threshold, transpose')
    hp_balance.add_argument('--scout_hp_weights', default=default('--scout_hp_weights'), help='Should be repaired when there is a difference in Vanguard, format 1000,1000,1000')
    hp_add = hp.add_argument_group('Emergency repair', '')
    hp_add.add_argument('--emergency_repair_single_threshold', default=default('--emergency_repair_single_threshold'), help='Used when single shipgirl is below the threshold')
    hp_add.add_argument('--emergency_repair_hole_threshold', default=default('--emergency_repair_hole_threshold'), help='Used when all front rows or all back rows are below the threshold')
    hp_withdraw = hp.add_argument_group('Low HP volume withdrawal', '')
    hp_withdraw.add_argument('--low_hp_withdraw_threshold', default=default('--low_hp_withdraw_threshold'), help='When HP is below the threshold, retreat')

    # 退役选项
    retire = setting_parser.add_argument_group('Retirement settings', '')
    retire.add_argument('--enable_retirement', default=default('--enable_retirement'), choices=['yes', 'no'])
    retire.add_argument('--retire_method', default=default('--retire_method'), choices=['enhance', 'one_click_retire', 'old_retire'])
    retire.add_argument('--retire_amount', default=default('--retire_amount'), choices=['retire_all', 'retire_10'])
    retire.add_argument('--enhance_favourite', default=default('--enhance_favourite'), choices=['yes', 'no'])

    rarity = retire.add_argument_group('Retirement rarity', 'The ship type selection is not supported yet. Ignore the following options when using one-key retirement')
    rarity.add_argument('--retire_n', default=default('--retire_n'), choices=['yes', 'no'], help='N')
    rarity.add_argument('--retire_r', default=default('--retire_r'), choices=['yes', 'no'], help='R')
    rarity.add_argument('--retire_sr', default=default('--retire_sr'), choices=['yes', 'no'], help='SR')
    rarity.add_argument('--retire_ssr', default=default('--retire_ssr'), choices=['yes', 'no'], help='SSR')

    # 掉落记录
    drop = setting_parser.add_argument_group('Drop record', 'Save screenshots of dropped items, which will slow down the click speed when settlement is enabled')
    drop.add_argument('--enable_drop_screenshot', default=default('--enable_drop_screenshot'), choices=['yes', 'no'])
    drop.add_argument('--drop_screenshot_folder', default=default('--drop_screenshot_folder'))

    clear = setting_parser.add_argument_group('Wasteland mode', 'Unopened maps will stop after completion. Opened maps will ignore options, and its done if you do not open up')
    clear.add_argument('--enable_map_clear_mode', default=default('--enable_map_clear_mode'), choices=['yes', 'no'])
    clear.add_argument('--clear_mode_stop_condition', default=default('--clear_mode_stop_condition'), choices=['map_100', 'map_3_star', 'map_green'])
    clear.add_argument('--map_star_clear_all', default=default('--map_star_clear_all'), choices=['index_1', 'index_2', 'index_3', 'do_not_use'], help='The first few stars are to destroy all enemy ships')

    # ==========reward==========
    reward_parser = subs.add_parser('reward')
    reward_condition = reward_parser.add_argument_group('Triggering conditions', 'Need to run once to save the options, after running it will enter the on-hook vegetable collection mode')
    reward_condition.add_argument('--enable_reward', default=default('--enable_reward'), choices=['yes', 'no'])
    reward_condition.add_argument('--reward_interval', default=default('--reward_interval'), choices=['20', '30', '60'], help='How many minutes to trigger collection')

    reward_oil = reward_parser.add_argument_group('Oil supplies', '')
    reward_oil.add_argument('--enable_oil_reward', default=default('--enable_oil_reward'), choices=['yes', 'no'])
    reward_oil.add_argument('--enable_coin_reward', default=default('--enable_coin_reward'), choices=['yes', 'no'])

    reward_mission = reward_parser.add_argument_group('mission rewards', '')
    reward_mission.add_argument('--enable_mission_reward', default=default('--enable_mission_reward'), choices=['yes', 'no'])

    reward_commission = reward_parser.add_argument_group('Commission settings', '')
    reward_commission.add_argument('--enable_commission_reward', default=default('--enable_commission_reward'), choices=['yes', 'no'])
    reward_commission.add_argument('--commission_time_limit', default=default('--commission_time_limit'), help='Ignore orders whose completion time exceeds the limit, Format: 23:30')

    priority1 = reward_commission.add_argument_group('Commission priority by time duration', '')
    priority1.add_argument('--duration_shorter_than_2', default=default('--duration_shorter_than_2'), help='')
    priority1.add_argument('--duration_longer_than_6', default=default('--duration_longer_than_6'), help='')
    priority1.add_argument('--expire_shorter_than_2', default=default('--expire_shorter_than_2'), help='')
    priority1.add_argument('--expire_longer_than_6', default=default('--expire_longer_than_6'), help='')

    priority2 = reward_commission.add_argument_group('Daily Commission priority', '')
    priority2.add_argument('--daily_comm', default=default('--daily_comm'), help='Daily resource development, high-level tactical research and development')
    priority2.add_argument('--major_comm', default=default('--major_comm'), help='1200 oil / 1000 oil commission')

    priority3 = reward_commission.add_argument_group('Additional commission priority', '')
    priority3.add_argument('--extra_drill', default=default('--extra_drill'), help='Short-range Sailing Training, Coastal Defense Patrol')
    priority3.add_argument('--extra_part', default=default('--extra_part'), help='Small Merchant Escort, Forest Protection Commission')
    priority3.add_argument('--extra_cube', default=default('--extra_cube'), help='Fleet Exercise Ⅲ, Fleet Escort ExerciseFleet Exercise Ⅲ')
    priority3.add_argument('--extra_oil', default=default('--extra_oil'), help='Small-scale Oil Extraction, Large-scale Oil Extraction')
    priority3.add_argument('--extra_book', default=default('--extra_book'), help='Small Merchant Escort, Large Merchant Escort')

    priority4 = reward_commission.add_argument_group('Urgente commission priority', '')
    priority4.add_argument('--urgent_drill', default=default('--urgent_drill'), help='Defend the transport troops, annihilate the enemy elite troops')
    priority4.add_argument('--urgent_part', default=default('--urgent_part'), help='Support Vila Vela Island, support terror Banner')
    priority4.add_argument('--urgent_cube', default=default('--urgent_cube'), help='Rescue merchant ship, enemy attack')
    priority4.add_argument('--urgent_book', default=default('--urgent_book'), help='Support Tuhaoer Island, support Moe Island')
    priority4.add_argument('--urgent_box', default=default('--urgent_box'), help='BIW Gear Transport, NYB Gear Transport')
    priority4.add_argument('--urgent_gem', default=default('--urgent_gem'), help='BIW VIP Escort, NYB VIP Escort')
    priority4.add_argument('--urgent_ship', default=default('--urgent_ship'), help='Small Launch Ceremony, Fleet Launch Ceremony, Alliance Launch Ceremony')

    reward_tactical = reward_parser.add_argument_group('Classroom', 'Only support continuation of skill books, not new skills')
    reward_tactical.add_argument('--enable_tactical_reward', default=default('--enable_tactical_reward'), choices=['yes', 'no'])
    reward_tactical.add_argument('--tactical_night_range', default=default('--tactical_night_range'), help='Format 23:30-06:30')
    reward_tactical.add_argument('--tactical_book_tier', default=default('--tactical_book_tier'), choices=['3', '2', '1'], help='Wich skill book will use first\nT3 is a gold book, T2 is a purple book, T1 is a blue book')
    reward_tactical.add_argument('--tactical_exp_first', default=default('--tactical_exp_first'), choices=['yes', 'no'], help='Choose Yes, give priority to the 150% bonus \nSelect No, give priority to the skills book with the same rarity')
    reward_tactical.add_argument('--tactical_book_tier_night', default=default('--tactical_book_tier_night'), choices=['3', '2', '1'])
    reward_tactical.add_argument('--tactical_exp_first_night', default=default('--tactical_exp_first_night'), choices=['yes', 'no'])

    # ==========emulator==========
    emulator_parser = subs.add_parser('emulator')
    emulator = emulator_parser.add_argument_group('Emulator', 'Need to run once to save the options, it will check whether the game is started \nIf the game has not started, it will be started')
    emulator.add_argument('--serial', default=default('--serial'), help='Bluestacks 127.0.0.1:5555 \nNox 127.0.0.1:62001')
    emulator.add_argument('--package_name', default='com.YoStarEN.AzurLane', help='')

    debug = emulator_parser.add_argument_group('Debug settings', '')
    debug.add_argument('--enable_error_log_and_screenshot_save', default=default('--enable_error_log_and_screenshot_save'), choices=['yes', 'no'])
    debug.add_argument('--enable_perspective_error_image_save', default=default('--enable_perspective_error_image_save'), choices=['yes', 'no'])

    adb = emulator_parser.add_argument_group('ADB settings', '')
    adb.add_argument('--use_adb_screenshot', default=default('--use_adb_screenshot'), choices=['yes', 'no'], help='It is recommended to enable it to reduce CPU usage')
    adb.add_argument('--use_adb_control', default=default('--use_adb_control'), choices=['yes', 'no'], help='Recommended off, can speed up the click speed')
    adb.add_argument('--combat_screenshot_interval', default=default('--combat_screenshot_interval'), help='Slow down the screenshot speed during battle and reduce CPU')

    # ==========每日任务==========
    daily_parser = subs.add_parser('daily')

    # 选择每日
    daily = daily_parser.add_argument_group('Choose daily', 'Daily tasks, exercises, difficulty charts')
    daily.add_argument('--enable_daily_mission', default=default('--enable_daily_mission'), help='If there are records on the day, skip', choices=['yes', 'no'])
    daily.add_argument('--enable_hard_campaign', default=default('--enable_hard_campaign'), help='If there are records on the day, skip', choices=['yes', 'no'])
    daily.add_argument('--enable_exercise', default=default('--enable_exercise'), help='If there is a record after refreshing, skip', choices=['yes', 'no'])

    # 每日设置
    daily_task = daily_parser.add_argument_group('Daily settings', 'Does not support submarine daily')
    daily_task.add_argument('--tactical_training', default=default('--tactical_training'), choices=['daily_air', 'daily_gun', 'daily_torpedo'])
    daily_task.add_argument('--fierce_assault', default=default('--fierce_assault'), choices=['index_1', 'index_2', 'index_3'])
    daily_task.add_argument('--escort_mission', default=default('--escort_mission'), choices=['index_1', 'index_2', 'index_3'])
    daily_task.add_argument('--advance_mission', default=default('--advance_mission'), choices=['index_1', 'index_2', 'index_3'])
    daily_task.add_argument('--daily_fleet', default=default('--daily_fleet'), choices=['1', '2', '3', '4', '5', '6'])
    daily_task.add_argument('--daily_equipment', default=default('--daily_equipment'), help='Change equipment before playing, unload equipment after playing, do not need to fill in 0 \ncomma, such as 3, 1, 0, 1, 1, 0')

    # 困难设置
    hard = daily_parser.add_argument_group('Difficult setting', 'Need to turn on weekly mode, only support 10-1, 10-2 and 10-4 temporarily')
    hard.add_argument('--hard_campaign', default=default('--hard_campaign'), help='For example 10-4')
    hard.add_argument('--hard_fleet', default=default('--hard_fleet'), choices=['1', '2'])
    hard.add_argument('--hard_equipment', default=default('--hard_equipment'), help='Change equipment before playing, unload equipment after playing, do not need to fill in 0 \ncomma, such as 3, 1, 0, 1, 1, 0')

    # 演习设置
    exercise = daily_parser.add_argument_group('Exercise settings', 'Only support the most experience for the time being')
    exercise.add_argument('--exercise_choose_mode', default=default('--exercise_choose_mode'), choices=['max_exp', 'max_ranking', 'good_opponent'], help='Only support the most experience for the time being')
    exercise.add_argument('--exercise_preserve', default=default('--exercise_preserve'), help='Only 0 are temporarily reserved')
    exercise.add_argument('--exercise_try', default=default('--exercise_try'), help='The number of attempts by each opponent')
    exercise.add_argument('--exercise_hp_threshold', default=default('--exercise_hp_threshold'), help='HHP <Retreat at Threshold')
    exercise.add_argument('--exercise_low_hp_confirm', default=default('--exercise_low_hp_confirm'), help='After HP is below the threshold, it will retreat after a certain period of time \nRecommended 1.0 ~ 3.0')
    exercise.add_argument('--exercise_equipment', default=default('--exercise_equipment'), help='Change equipment before playing, unload equipment after playing, do not need to fill in 0 \ncomma, such as 3, 1, 0, 1, 1, 0')

    # ==========event_daily_ab==========
    event_ab_parser = subs.add_parser('event_daily_bonus')
    event_name = event_ab_parser.add_argument_group('Choose an event', 'bonus for first clear each day')
    event_name.add_argument('--event_name_ab', default=default('--event_name_ab'), choices=event_folder, help='There a dropdown menu with many options')
    # event_name.add_argument('--enable_hard_bonus', default=default('--enable_hard_bonus'), choices=['yes', 'no'], help='Will enable Daily bonus for Event hard maps') # Trying implement all event maps

    # ==========main==========
    main_parser = subs.add_parser('main')
    # 选择关卡
    stage = main_parser.add_argument_group('Choose a level', 'Main campaign, currently only supports the first six chapters and 7-2')
    stage.add_argument('--main_stage', default=default('--main_stage'), help='E.g 7-2')

    # ==========event==========
    event_parser = subs.add_parser('event')

    description = """
    Support "Iris of Light and Dark Rerun" (event_20200521_en), optimized for D2
    """
    event = event_parser.add_argument_group(
        'Choose a level', '\n'.join([line.strip() for line in description.strip().split('\n')]))
    event.add_argument('--event_stage', default=default('--event_stage'),
                             choices=['a1', 'a2', 'a3', 'b1', 'b2', 'b3', 'c1', 'c2', 'c3', 'd1', 'd2', 'd3'],
                             help='E.g d3')
    event.add_argument('--sp_stage', default=default('--sp_stage'),
                             choices=['sp1', 'sp2', 'sp3'],
                             help='E.g sp3')
    event.add_argument('--event_name', default=default('--event_name'), choices=event_folder, help='There a dropdown menu with many options')

    # ==========半自动==========
    semi_parser = subs.add_parser('semi_auto')
    semi = semi_parser.add_argument_group('Semi-automatic mode', 'Manual selection of enemies, automatic settlement, used to attack unsuited pictures')
    semi.add_argument('--enable_semi_map_preparation', default=default('--enable_semi_map_preparation'), help='', choices=['yes', 'no'])
    semi.add_argument('--enable_semi_story_skip', default=default('--enable_semi_story_skip'), help='Note that this will automatically confirm all the prompt boxes, including the red face attack', choices=['yes', 'no'])

    # ==========c72_mystery_farming==========
    c_7_2_parser = subs.add_parser('c7-2_mystery_farming')
    c_7_2 = c_7_2_parser.add_argument_group('c72_mystery_farming', '')
    c_7_2.add_argument('--boss_fleet_step_on_a3', default=default('--boss_fleet_step_on_a3'), choices=['yes', 'no'], help='A3 has enemies, G3, C3, E3')

    # ==========c122_leveling==========
    c_12_2_parser = subs.add_parser('c12-2_leveling')
    c_12_2 = c_12_2_parser.add_argument_group('12-2 enemy search settings', '')
    c_12_2.add_argument('--s3_enemy_tolerance', default=default('--s3_enemy_tolerance'), choices=['0', '1', '2', '10'], help='The maximum number of battles to fight against large enemies')

    # ==========c124_leveling==========
    c_12_4_parser = subs.add_parser('c12-4_leveling')
    c_12_4 = c_12_4_parser.add_argument_group('12-4 Search enemy settings', 'Need to ensure that the team has a certain strength')
    c_12_4.add_argument('--non_s3_enemy_enter_tolerance', default=default('--non_s3_enemy_enter_tolerance'), choices=['0', '1', '2'], help='Avoid enemy too strong')
    c_12_4.add_argument('--non_s3_enemy_withdraw_tolerance', default=default('--non_s3_enemy_withdraw_tolerance'), choices=['0', '1', '2', '10'], help='How many battles will be fought after there is no large scale')
    c_12_4.add_argument('--ammo_pick_up_124', default=default('--ammo_pick_up_124'), choices=['2', '3', '4', '5'], help='How much ammunition to pick after the battle')

    args = parser.parse_args()

    # Convert option from chinese to english.
    out = {}
    for key, value in vars(args).items():
        key = dic_true_eng_to_eng.get(key, key)
        value = dic_true_eng_to_eng.get(value, value)
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
