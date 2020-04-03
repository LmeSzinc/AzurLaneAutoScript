dic_bool = {
    'yes': True,
    'no': False,
    'do_not_use': False,
}
dic_emotion_limit = {
    'keep_high_emotion': 120,
    'avoid_green_face': 40,
    'avoid_yellow_face': 30,
    'avoid_red_face': 2,
}
dic_emotion_recover = {
    'not_in_dormitory': 20,
    'dormitory_floor_1': 40,
    'dormitory_floor_2': 50,
}
dic_daily = {
    'daily_air': 1,
    'daily_gun': 2,
    'daily_torpedo': 3,
    'lv_70': 1,
    'lv_50': 2,
    'lv_35': 3,
}
dic_chi_to_eng = {
    # Function
    '出击设置': 'setting',
    '收菜设置': 'reward',
    '设备设置': 'emulator',
    '每日任务困难演习': 'daily',
    '每日活动图三倍PT': 'event_daily_ab',
    '主线图': 'main',
    '活动图': 'event',
    '半自动辅助点击': 'semi_auto',
    '7-2三战拣垃圾': 'c72_mystery_farming',
    '12-4打大型练级': 'c124_leveling',

    # Argument
    '启用停止条件': 'enable_stop_condition',
    '如果出击次数大于': 'if_count_greater_than',
    '如果时间超过': 'if_time_reach',
    '如果石油低于': 'if_oil_lower_than',
    '如果触发心情控制': 'if_trigger_emotion_control',
    '如果船舱已满': 'if_dock_full',
    '启用舰队控制': 'enable_fleet_control',
    '舰队编号1': 'fleet_index_1',
    '舰队阵型1': 'fleet_formation_1',
    '舰队编号2': 'fleet_index_2',
    '舰队阵型2': 'fleet_formation_2',
    '舰队编号3': 'fleet_index_3',
    '舰队阵型3': 'fleet_formation_3',
    '舰队编号4': 'fleet_index_4',
    '潜艇出击方案': 'submarine_mode',
    '启用心情消耗': 'enable_emotion_reduce',
    '无视红脸出击警告': 'ignore_low_emotion_warn',
    '心情回复1': 'emotion_recover_1',
    '心情控制1': 'emotion_control_1',
    '全员已婚1': 'hole_fleet_married_1',
    '心情回复2': 'emotion_recover_2',
    '心情控制2': 'emotion_control_2',
    '全员已婚2': 'hole_fleet_married_2',
    '心情回复3': 'emotion_recover_3',
    '心情控制3': 'emotion_control_3',
    '全员已婚3': 'hole_fleet_married_3',
    '启用血量平衡': 'enable_hp_balance',
    '启用退役': 'enable_retirement',
    '退役方案': 'retire_mode',
    '退役白皮': 'retire_n',
    '退役蓝皮': 'retire_r',
    '退役紫皮': 'retire_sr',
    '退役金皮': 'retire_ssr',
    '启用掉落记录': 'enable_drop_screenshot',
    '掉落保存目录': 'drop_screenshot_folder',
    '启用收获': 'enable_reward',
    '收菜间隔': 'reward_interval',
    '启用石油收获': 'enable_oil_reward',
    '启用物资收获': 'enable_coin_reward',
    '启用任务收获': 'enable_mission_reward',
    '设备': 'serial',
    '打每日': 'enable_daily_mission',
    '打困难': 'enable_hard_campaign',
    '打演习': 'enable_exercise',
    '战术研修': 'daily_mission_1',
    '斩首行动': 'daily_mission_2',
    '商船护航': 'daily_mission_4',
    '海域突进': 'daily_mission_5',
    '每日舰队': 'daily_fleet',
    '每日舰队快速换装': 'daily_equipment',
    '困难地图': 'hard_campaign',
    '困难舰队': 'hard_fleet',
    '困难舰队快速换装': 'hard_equipment',
    '演习对手选择': 'exercise_choose_mode',
    '演习次数保留': 'exercise_preserve',
    '演习尝试次数': 'exercise_try',
    '演习SL阈值': 'exercise_hp_threshold',
    '演习低血量确认时长': 'exercise_low_hp_confirm',
    '演习快速换装': 'exercise_equipment',
    '主线地图出击': 'main_stage',
    '活动地图': 'event_stage',
    'sp地图': 'sp_stage',
    '活动名称': 'event_name',
    '活动名称ab': 'event_name_ab',
    '进图准备': 'enable_semi_map_preparation',
    '跳过剧情': 'enable_semi_story_skip',
    'BOSS队踩A3': 'boss_fleet_step_on_a3',
    '非大型敌人进图忍耐': 'non_s3_enemy_enter_tolerance',
    '非大型敌人撤退忍耐': 'non_s3_enemy_withdraw_tolerance',
    '拣弹药124': 'ammo_pick_up_124',

    # Option
    '是': 'yes',
    '否': 'no',
    '单纵阵': 'formation_1',
    '复纵阵': 'formation_2',
    '轮形阵': 'formation_3',
    '不使用': 'do_not_use',
    '仅狩猎': 'hunt_only',
    '每战出击': 'every_combat',
    '空弹出击': 'when_no_ammo',
    'BOSS战出击': 'when_boss_combat',
    'BOSS战BOSS出现后召唤': 'when_boss_combat_boss_appear',
    '未放置于后宅': 'not_in_dormitory',
    '后宅一楼': 'dormitory_floor_1',
    '后宅二楼': 'dormitory_floor_2',
    '保持经验加成': 'keep_high_emotion',
    '防止绿脸': 'avoid_green_face',
    '防止黄脸': 'avoid_yellow_face',
    '防止红脸': 'avoid_red_face',
    '退役全部': 'retire_all',
    '退役10个': 'retire_10',
    '航空': 'daily_air',
    '炮击': 'daily_gun',
    '雷击': 'daily_torpedo',
    '70级': 'lv_70',
    '50级': 'lv_50',
    '35级': 'lv_35',
    '经验最多': 'max_exp',
    '排名最前': 'max_ranking',
    '福利队': 'good_opponent',

    # Event
    '北境序曲': 'event_20200227_cn',
    '复刻斯图尔特的硝烟': 'event_20200312_cn',
    '微层混合': 'event_20200326_cn',

}
dic_eng_to_chi = {v: k for k, v in dic_chi_to_eng.items()}


def to_bool(string):
    return dic_bool.get(string, string)


def equip(string):
    if string.isdigit():
        return None

    out = [int(letter.strip()) for letter in string.split(',')]
    assert len(out) == 6
    return out
