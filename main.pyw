import codecs
import configparser
import os

from gooey import Gooey, GooeyParser

from main import AzurLaneAutoScript
from module.config.dictionary import dic_chi_to_eng, dic_eng_to_chi

running = True


@Gooey(
    optional_cols=2,
    program_name="AzurLaneAutoScript",
    sidebar_title='功能',
    terminal_font_family='Consolas',
    language='chinese',
    default_size=(800, 850),
    navigation='SIDEBAR',
    tabbed_groups=True,
    show_success_modal=False,
    show_failure_modal=False,
    # show_stop_warning=False,
    # load_build_config='gooey_config.json',
    # dump_build_config='gooey_config.json',
)
def main():
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # Load default value from .ini file.
    config_file = f'./config/{script_name}.ini'
    config = configparser.ConfigParser(interpolation=None)
    config.read_file(codecs.open(config_file, "r", "utf8"))

    saved_config = {}
    for opt, option in config.items():
        for key, value in option.items():
            key = dic_eng_to_chi.get(key, key)
            if value in dic_eng_to_chi:
                value = dic_eng_to_chi.get(value, value)
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

    parser = GooeyParser(description='An Azur Lane Automation Tool.')
    subs = parser.add_subparsers(help='commands', dest='command')

    # ==========出击设置==========
    setting_parser = subs.add_parser('出击设置')

    # 选择关卡
    stage = setting_parser.add_argument_group('关卡设置', '需要运行一次来保存选项')
    stage.add_argument('--启用停止条件', default=default('--启用停止条件'), choices=['是', '否'])

    stop = stage.add_argument_group('停止条件', '触发后不会马上停止会先完成当前出击, 不需要就填0')
    stop.add_argument('--如果出击次数大于', default=default('--如果出击次数大于'), help='会沿用先前设置, 完成出击将扣除次数, 直至清零')
    stop.add_argument('--如果时间超过', default=default('--如果时间超过'), help='使用未来24小时内的时间, 会沿用先前设置, 触发后清零. 建议提前10分钟左右, 以完成当前出击. 格式 14:59')
    stop.add_argument('--如果石油低于', default=default('--如果石油低于'))
    stop.add_argument('--如果触发心情控制', default=default('--如果触发心情控制'), choices=['是', '否'], help='若是, 等待回复, 完成本次, 停止\n若否, 等待回复, 完成本次, 继续')
    stop.add_argument('--如果船舱已满', default=default('--如果船舱已满'), choices=['是', '否'])

    # 出击舰队
    fleet = setting_parser.add_argument_group('出击舰队', '暂不支持阵型选择, 暂不支持备用道中队')
    fleet.add_argument('--启用舰队控制', default=default('--启用舰队控制'), choices=['是', '否'])

    f1 = fleet.add_argument_group('道中队')
    f1.add_argument('--舰队编号1', default=default('--舰队编号1'), choices=['1', '2', '3', '4', '5', '6'])
    f1.add_argument('--舰队阵型1', default=default('--舰队阵型1'), choices=['单纵阵', '复纵阵', '轮形阵'])

    f2 = fleet.add_argument_group('BOSS队')
    f2.add_argument('--舰队编号2', default=default('--舰队编号2'), choices=['不使用', '1', '2', '3', '4', '5', '6'])
    f2.add_argument('--舰队阵型2', default=default('--舰队阵型2'), choices=['单纵阵', '复纵阵', '轮形阵'])

    f3 = fleet.add_argument_group('备用道中队')
    f3.add_argument('--舰队编号3', default=default('--舰队编号3'), choices=['不使用', '1', '2', '3', '4', '5', '6'])
    f3.add_argument('--舰队阵型3', default=default('--舰队阵型3'), choices=['单纵阵', '复纵阵', '轮形阵'])

    # 潜艇设置
    submarine = setting_parser.add_argument_group('潜艇设置', '暂不支持潜艇, 最好避免潜艇进图')
    submarine.add_argument('--舰队编号4', default=default('--舰队编号4'), choices=['不使用', '1', '2'])
    submarine.add_argument('--潜艇出击方案', default=default('--潜艇出击方案'), choices=['不使用', '仅狩猎', '每战出击', '空弹出击', 'BOSS战出击', 'BOSS战BOSS出现后召唤'])

    # 心情控制
    emotion = setting_parser.add_argument_group('心情控制')
    emotion.add_argument('--启用心情消耗', default=default('--启用心情消耗'), choices=['是', '否'])
    emotion.add_argument('--无视红脸出击警告', default=default('--无视红脸出击警告'), choices=['是', '否'])

    e1 = emotion.add_argument_group('道中队')
    e1.add_argument('--心情回复1', default=default('--心情回复1'), choices=['未放置于后宅', '后宅一楼', '后宅二楼'])
    e1.add_argument('--心情控制1', default=default('--心情控制1'), choices=['保持经验加成', '防止绿脸', '防止黄脸', '防止红脸'])
    e1.add_argument('--全员已婚1', default=default('--全员已婚1'), choices=['是', '否'])

    e2 = emotion.add_argument_group('BOSS队')
    e2.add_argument('--心情回复2', default=default('--心情回复2'), choices=['未放置于后宅', '后宅一楼', '后宅二楼'])
    e2.add_argument('--心情控制2', default=default('--心情控制2'), choices=['保持经验加成', '防止绿脸', '防止黄脸', '防止红脸'])
    e2.add_argument('--全员已婚2', default=default('--全员已婚2'), choices=['是', '否'])

    e3 = emotion.add_argument_group('备用道中队', '会在主队触发心情控制时使用')
    e3.add_argument('--心情回复3', default=default('--心情回复3'), choices=['未放置于后宅', '后宅一楼', '后宅二楼'])
    e3.add_argument('--心情控制3', default=default('--心情控制3'), choices=['保持经验加成', '防止绿脸', '防止黄脸', '防止红脸'])
    e3.add_argument('--全员已婚3', default=default('--全员已婚3'), choices=['是', '否'])

    # 血量平衡
    balance = setting_parser.add_argument_group('血量平衡', '目前无效, 不要使用')
    balance.add_argument('--启用血量平衡', default=default('--启用血量平衡'), choices=['是', '否'])

    # 退役选项
    retire = setting_parser.add_argument_group('退役设置', '')
    retire.add_argument('--启用退役', default=default('--启用退役'), choices=['是', '否'])
    retire.add_argument('--退役方案', default=default('--退役方案'), choices=['退役全部', '退役10个'])

    rarity = retire.add_argument_group('退役稀有度', '暂不支持舰种选择')
    rarity.add_argument('--退役白皮', default=default('--退役白皮'), choices=['是', '否'], help='N')
    rarity.add_argument('--退役蓝皮', default=default('--退役蓝皮'), choices=['是', '否'], help='R')
    rarity.add_argument('--退役紫皮', default=default('--退役紫皮'), choices=['是', '否'], help='SR')
    rarity.add_argument('--退役金皮', default=default('--退役金皮'), choices=['是', '否'], help='SSR')

    # 掉落记录
    drop = setting_parser.add_argument_group('掉落记录', '保存掉落物品的截图, 启用后会减慢结算时的点击速度')
    drop.add_argument('--启用掉落记录', default=default('--启用掉落记录'), choices=['是', '否'])
    drop.add_argument('--掉落保存目录', default=default('--掉落保存目录'))

    # ==========收菜设置==========
    reward_parser = subs.add_parser('收菜设置')
    reward_condition = reward_parser.add_argument_group('触发条件', '')
    reward_condition.add_argument('--启用收获', default=default('--启用收获'), choices=['是', '否'])
    reward_condition.add_argument('--收菜间隔', default=default('--收菜间隔'), choices=['20', '30', '60'], help='每隔多少分钟触发收菜')

    reward_oil = reward_parser.add_argument_group('石油物资', '')
    reward_oil.add_argument('--启用石油收获', default=default('--启用石油收获'), choices=['是', '否'])
    reward_oil.add_argument('--启用物资收获', default=default('--启用物资收获'), choices=['是', '否'])

    reward_mission = reward_parser.add_argument_group('任务奖励', '')
    reward_mission.add_argument('--启用任务收获', default=default('--启用任务收获'), choices=['是', '否'])

    # ==========模拟器==========
    emulator_parser = subs.add_parser('模拟器')
    emulator = emulator_parser.add_argument_group('模拟器', '')
    emulator.add_argument('--设备', default=default('--设备'), help='例如 127.0.0.1:62001')

    # ==========每日任务==========
    daily_parser = subs.add_parser('每日任务')

    # 选择每日
    daily = daily_parser.add_argument_group('选择每日', '每日任务, 演习, 困难图')
    daily.add_argument('--打每日', default=default('--打每日'), help='若当天有记录, 则跳过', choices=['是', '否'])
    daily.add_argument('--打困难', default=default('--打困难'), help='若当天有记录, 则跳过', choices=['是', '否'])
    daily.add_argument('--打演习', default=default('--打演习'), help='若在刷新后有记录, 则跳过', choices=['是', '否'])

    # 每日设置
    daily_task = daily_parser.add_argument_group('每日设置', '不支持潜艇每日')
    daily_task.add_argument('--战术研修', default=default('--战术研修'), choices=['航空', '炮击', '雷击'])
    daily_task.add_argument('--斩首行动', default=default('--斩首行动'), choices=['70级', '50级', '35级'])
    daily_task.add_argument('--商船护航', default=default('--商船护航'), choices=['70级', '50级', '35级'])
    daily_task.add_argument('--海域突进', default=default('--海域突进'), choices=['70级', '50级', '35级'])
    daily_task.add_argument('--每日舰队', default=default('--每日舰队'), choices=['1', '2', '3', '4', '5', '6'])
    daily_task.add_argument('--每日舰队快速换装', default=default('--每日舰队快速换装'), help='打之前换装备, 打完后卸装备, 不需要就填0\n逗号分割, 例如 \"3, 1, 0, 1, 1, 0\"')

    # 困难设置
    hard = daily_parser.add_argument_group('困难设置', '暂时仅支持 10-4')
    hard.add_argument('--困难地图', default=default('--困难地图'), help='比如 10-4')
    hard.add_argument('--困难舰队', default=default('--困难舰队'), choices=['1', '2'])
    hard.add_argument('--困难舰队快速换装', default=default('--困难舰队快速换装'), help='打之前换装备, 打完后卸装备, 不需要就填0\n逗号分割, 例如 \"3, 1, 0, 1, 1, 0\"')

    # 演习设置
    exercise = daily_parser.add_argument_group('演习设置', '暂时不支持挑选福利队')
    exercise.add_argument('--演习对手选择', default=default('--演习对手选择'), choices=['经验最多', '排名最前', '福利队'], help='暂时仅支持经验最多')
    exercise.add_argument('--演习次数保留', default=default('--演习次数保留'), help='暂时仅支持保留0个')
    exercise.add_argument('--演习尝试次数', default=default('--演习尝试次数'), help='每个对手的尝试次数, 打不过就换')
    exercise.add_argument('--演习SL阈值', default=default('--演习SL阈值'), help='HP<阈值时撤退')
    exercise.add_argument('--演习低血量确认时长', default=default('--演习低血量确认时长'), help='HP低于阈值后, 过一定时长才会撤退\n推荐 1.0 ~ 3.0')
    exercise.add_argument('--演习快速换装', default=default('--演习快速换装'), help='打之前换装备, 打完后卸装备, 不需要就填0\n逗号分割, 例如 \"3, 1, 0, 1, 1, 0\"')

    # ==========主线图==========
    main_parser = subs.add_parser('主线图')
    # 选择关卡
    stage = main_parser.add_argument_group('选择关卡', '主线图出击, 目前仅支持7-2')
    stage.add_argument('--主线地图出击', default=default('--主线地图出击'), help='例如 7-2')

    # ==========活动图==========
    event_parser = subs.add_parser('活动图')
    event_folder = [dic_eng_to_chi.get(f, f) for f in os.listdir('./campaign') if f.startswith('event_')][::-1]

    event = event_parser.add_argument_group('选择关卡', '')
    event.add_argument('--活动地图', default=default('--活动地图'),
                             choices=['a1', 'a2', 'a3', 'b1', 'b2', 'b3', 'c1', 'c2', 'c3', 'd1', 'd2', 'd3'],
                             help='例如 d3')
    event.add_argument('--sp地图', default=default('--sp地图'),
                             choices=['sp3', 'sp2', 'sp1'],
                             help='例如 sp3')
    event.add_argument('--活动名称', default=default('--活动名称'), choices=event_folder, help='例如 event_20200312_cn')

    # ==========活动AB图每日三倍==========
    event_ab_parser = subs.add_parser('活动AB图每日三倍')
    event_name = event_ab_parser.add_argument_group('选择活动', '')
    event_name.add_argument('--活动名称ab', default=default('--活动名称ab'), choices=event_folder, help='例如 event_20200326_cn')

    # ==========半自动==========
    semi_parser = subs.add_parser('半自动')
    semi = semi_parser.add_argument_group('半自动模式', '手动选敌, 自动结算, 用于出击未适配的图')
    semi.add_argument('--进图准备', default=default('--进图准备'), help='', choices=['是', '否'])
    semi.add_argument('--跳过剧情', default=default('--跳过剧情'), help='注意, 这会自动确认所有提示框, 包括红脸出击', choices=['是', '否'])

    # ==========7-2三战拣垃圾==========
    c_7_2_parser = subs.add_parser('7-2三战拣垃圾')
    c_7_2 = c_7_2_parser.add_argument_group('7-2三战拣垃圾', '')
    c_7_2.add_argument('--BOSS队踩A3', default=default('--BOSS队踩A3'), choices=['是', '否'], help='A3有敌人就G3, C3, E3')
    # c_12_4.add_argument('--非大型敌人撤退忍耐', default=default('--非大型敌人撤退忍耐'), choices=['0', '1', '2', '10'],
    #                     help='没有大型之后还会打多少战, 不挑敌人选10')
    # c_12_4.add_argument('--拣弹药124', default=default('--拣弹药124'), choices=['2', '3', '4', '5'], help='多少战后拣弹药')

    # ==========12-4打大型练级==========
    c_12_4_parser = subs.add_parser('12-4打大型练级')
    c_12_4 = c_12_4_parser.add_argument_group('12-4索敌设置', '需保证队伍有一定强度')
    c_12_4.add_argument('--非大型敌人进图忍耐', default=default('--非大型敌人进图忍耐'), choices=['0', '1', '2'], help='忍受进场多少战没有大型')
    c_12_4.add_argument('--非大型敌人撤退忍耐', default=default('--非大型敌人撤退忍耐'), choices=['0', '1', '2', '10'], help='没有大型之后还会打多少战, 不挑敌人选10')
    c_12_4.add_argument('--拣弹药124', default=default('--拣弹药124'), choices=['2', '3', '4', '5'], help='多少战后拣弹药')



    args = parser.parse_args()

    # Convert option from chinese to english.
    out = {}
    for key, value in vars(args).items():
        key = dic_chi_to_eng.get(key, key)
        value = dic_chi_to_eng.get(value, value)
        out[key] = value
    args = out

    # Update option to .ini file.
    command = args['command'].capitalize()
    config['Command']['command'] = command
    for key, value in args.items():
        config[command][key] = str(value)
    config.write(codecs.open(config_file, "w+", "utf8"))

    # Call AzurLaneAutoScript
    alas = AzurLaneAutoScript(config_name=script_name)
    alas.__getattribute__(command.lower())()


if __name__ == '__main__':
    main()
