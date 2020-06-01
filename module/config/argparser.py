import codecs
import configparser
import os
import shutil

from gooey import Gooey, GooeyParser

from alas import AzurLaneAutoScript
from module.config.dictionary import dic_chi_to_eng, dic_eng_to_chi
from module.logger import logger, pyw_name

running = True


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

    event_folder = [dic_eng_to_chi.get(f, f) for f in os.listdir('./campaign') if f.startswith('event_')][::-1]

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

    parser = GooeyParser(description=f'AzurLaneAutoScript, An Azur Lane automation tool. Config: {config_file}')
    subs = parser.add_subparsers(help='commands', dest='command')

    # ==========出击设置==========
    setting_parser = subs.add_parser('出击设置')

    # 选择关卡
    stage = setting_parser.add_argument_group('关卡设置', '需要运行一次来保存选项')
    stage.add_argument('--启用停止条件', default=default('--启用停止条件'), choices=['是', '否'])
    stage.add_argument('--使用周回模式', default=default('--使用周回模式'), choices=['是', '否'])

    stop = stage.add_argument_group('停止条件', '触发后不会马上停止会先完成当前出击, 不需要就填0')
    stop.add_argument('--如果出击次数大于', default=default('--如果出击次数大于'), help='会沿用先前设置, 完成出击将扣除次数, 直至清零')
    stop.add_argument('--如果时间超过', default=default('--如果时间超过'), help='使用未来24小时内的时间, 会沿用先前设置, 触发后清零. 建议提前10分钟左右, 以完成当前出击. 格式 14:59')
    stop.add_argument('--如果石油低于', default=default('--如果石油低于'))
    stop.add_argument('--如果触发心情控制', default=default('--如果触发心情控制'), choices=['是', '否'], help='若是, 等待回复, 完成本次, 停止\n若否, 等待回复, 完成本次, 继续')
    stop.add_argument('--如果船舱已满', default=default('--如果船舱已满'), choices=['是', '否'])

    # 出击舰队
    fleet = setting_parser.add_argument_group('出击舰队', '暂不支持备用道中队, 非活动图或周回模式会忽略步长设置')
    fleet.add_argument('--启用舰队控制', default=default('--启用舰队控制'), choices=['是', '否'])
    fleet.add_argument('--启用阵容锁定', default=default('--启用阵容锁定'), choices=['是', '否'])

    f1 = fleet.add_argument_group('道中队')
    f1.add_argument('--舰队编号1', default=default('--舰队编号1'), choices=['1', '2', '3', '4', '5', '6'])
    f1.add_argument('--舰队阵型1', default=default('--舰队阵型1'), choices=['单纵阵', '复纵阵', '轮形阵'])
    f1.add_argument('--舰队步长1', default=default('--舰队步长1'), choices=['1', '2', '3', '4', '5', '6'])

    f2 = fleet.add_argument_group('BOSS队')
    f2.add_argument('--舰队编号2', default=default('--舰队编号2'), choices=['不使用', '1', '2', '3', '4', '5', '6'])
    f2.add_argument('--舰队阵型2', default=default('--舰队阵型2'), choices=['单纵阵', '复纵阵', '轮形阵'])
    f2.add_argument('--舰队步长2', default=default('--舰队步长2'), choices=['1', '2', '3', '4', '5', '6'])

    f3 = fleet.add_argument_group('备用道中队')
    f3.add_argument('--舰队编号3', default=default('--舰队编号3'), choices=['不使用', '1', '2', '3', '4', '5', '6'])
    f3.add_argument('--舰队阵型3', default=default('--舰队阵型3'), choices=['单纵阵', '复纵阵', '轮形阵'])
    f3.add_argument('--舰队步长3', default=default('--舰队步长3'), choices=['1', '2', '3', '4', '5', '6'])

    f4 = fleet.add_argument_group('自律模式')
    f4.add_argument('--战斗自律模式', default=default('--战斗自律模式'), choices=['自律', '手操', '中路站桩'])

    # 潜艇设置
    submarine = setting_parser.add_argument_group('潜艇设置', '仅支持: 不使用, 仅狩猎, 每战出击')
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
    hp = setting_parser.add_argument_group('血量控制', '需关闭舰队锁定才能生效')
    hp.add_argument('--启用血量平衡', default=default('--启用血量平衡'), choices=['是', '否'])
    hp.add_argument('--启用低血量撤退', default=default('--启用低血量撤退'), choices=['是', '否'])
    hp_balance = hp.add_argument_group('血量平衡', '')
    hp_balance.add_argument('--先锋血量平衡阈值', default=default('--先锋血量平衡阈值'), help='血量差值大于阈值时, 换位')
    hp_balance.add_argument('--先锋血量权重', default=default('--先锋血量权重'), help='先锋肉度有差别时应修改, 格式 1000,1000,1000')
    hp_add = hp.add_argument_group('紧急维修', '')
    hp_add.add_argument('--紧急维修单人阈值', default=default('--紧急维修单人阈值'), help='单人低于阈值时使用')
    hp_add.add_argument('--紧急维修全队阈值', default=default('--紧急维修全队阈值'), help='前排全部或后排全部低于阈值时使用')
    hp_withdraw = hp.add_argument_group('低血量撤退', '')
    hp_withdraw.add_argument('--低血量撤退阈值', default=default('--低血量撤退阈值'), help='任意一人血量低于阈值时, 撤退')

    # 退役选项
    retire = setting_parser.add_argument_group('退役设置', '')
    retire.add_argument('--启用退役', default=default('--启用退役'), choices=['是', '否'])
    retire.add_argument('--退役方案', default=default('--退役方案'), choices=['强化角色', '一键退役', '传统退役'])
    retire.add_argument('--退役数量', default=default('--退役数量'), choices=['退役全部', '退役10个'])
    retire.add_argument('--强化常用角色', default=default('--强化常用角色'), choices=['是', '否'])

    rarity = retire.add_argument_group('退役稀有度', '暂不支持舰种选择, 使用一键退役时忽略以下选项')
    rarity.add_argument('--退役白皮', default=default('--退役白皮'), choices=['是', '否'], help='N')
    rarity.add_argument('--退役蓝皮', default=default('--退役蓝皮'), choices=['是', '否'], help='R')
    rarity.add_argument('--退役紫皮', default=default('--退役紫皮'), choices=['是', '否'], help='SR')
    rarity.add_argument('--退役金皮', default=default('--退役金皮'), choices=['是', '否'], help='SSR')

    # 掉落记录
    drop = setting_parser.add_argument_group('掉落记录', '保存掉落物品的截图, 启用后会放缓结算时的点击速度')
    drop.add_argument('--启用掉落记录', default=default('--启用掉落记录'), choices=['是', '否'])
    drop.add_argument('--掉落保存目录', default=default('--掉落保存目录'))

    clear = setting_parser.add_argument_group('开荒模式', '未开荒地图会在完成后停止, 已开荒的地图会忽略选项, 无脑开就完事了')
    clear.add_argument('--启用开荒', default=default('--启用开荒'), choices=['是', '否'])
    clear.add_argument('--开荒停止条件', default=default('--开荒停止条件'), choices=['地图通关', '地图三星', '地图绿海'])
    clear.add_argument('--地图全清星星', default=default('--地图全清星星'), choices=['第一个', '第二个', '第三个', '不使用'], help='第几颗星星是击破所有敌舰')

    # ==========收菜设置==========
    reward_parser = subs.add_parser('收菜设置')
    reward_condition = reward_parser.add_argument_group('触发条件', '需要运行一次来保存选项, 运行后会进入挂机收菜模式')
    reward_condition.add_argument('--启用收获', default=default('--启用收获'), choices=['是', '否'])
    reward_condition.add_argument('--收菜间隔', default=default('--收菜间隔'), choices=['20', '30', '60'], help='每隔多少分钟触发收菜')

    reward_oil = reward_parser.add_argument_group('石油物资', '')
    reward_oil.add_argument('--启用石油收获', default=default('--启用石油收获'), choices=['是', '否'])
    reward_oil.add_argument('--启用物资收获', default=default('--启用物资收获'), choices=['是', '否'])

    reward_mission = reward_parser.add_argument_group('任务奖励', '')
    reward_mission.add_argument('--启用任务收获', default=default('--启用任务收获'), choices=['是', '否'])

    reward_commission = reward_parser.add_argument_group('委托设置', '')
    reward_commission.add_argument('--启用委托收获', default=default('--启用委托收获'), choices=['是', '否'])
    reward_commission.add_argument('--委托时间限制', default=default('--委托时间限制'), help='忽略完成时间超过限制的委托, 格式: 23:30')

    priority1 = reward_commission.add_argument_group('委托耗时优先级', '')
    priority1.add_argument('--委托耗时小于2h', default=default('--委托耗时小于2h'), help='')
    priority1.add_argument('--委托耗时超过6h', default=default('--委托耗时超过6h'), help='')
    priority1.add_argument('--委托过期小于2h', default=default('--委托过期小于2h'), help='')
    priority1.add_argument('--委托过期大于6h', default=default('--委托过期大于6h'), help='')

    priority2 = reward_commission.add_argument_group('日常委托优先级', '')
    priority2.add_argument('--日常委托', default=default('--日常委托'), help='日常资源开发, 高阶战术研发')
    priority2.add_argument('--主要委托', default=default('--主要委托'), help='1200油/1000油委托')

    priority3 = reward_commission.add_argument_group('额外委托优先级', '')
    priority3.add_argument('--钻头类额外委托', default=default('--钻头类额外委托'), help='短距离航行训练, 近海防卫巡逻')
    priority3.add_argument('--部件类额外委托', default=default('--部件类额外委托'), help='矿脉护卫委托, 林木护卫委托')
    priority3.add_argument('--魔方类额外委托', default=default('--魔方类额外委托'), help='舰队高阶演习, 舰队护卫演习')
    priority3.add_argument('--石油类额外委托', default=default('--石油类额外委托'), help='小型油田开发, 大型油田开发')
    priority3.add_argument('--教材类额外委托', default=default('--教材类额外委托'), help='小型商船护卫, 大型商船护卫')

    priority4 = reward_commission.add_argument_group('紧急委托优先级', '')
    priority4.add_argument('--钻头类紧急委托', default=default('--钻头类紧急委托'), help='保卫运输部队, 歼灭敌精锐部队')
    priority4.add_argument('--部件类紧急委托', default=default('--部件类紧急委托'), help='支援维拉维拉岛, 支援恐班纳')
    priority4.add_argument('--魔方类紧急委托', default=default('--魔方类紧急委托'), help='解救商船, 敌袭')
    priority4.add_argument('--教材类紧急委托', default=default('--教材类紧急委托'), help='支援土豪尔岛, 支援萌岛')
    priority4.add_argument('--装备类紧急委托', default=default('--装备类紧急委托'), help='BIW装备运输, NYB装备研发')
    priority4.add_argument('--钻石类紧急委托', default=default('--钻石类紧急委托'), help='BIW要员护卫, NYB巡视护卫')
    priority4.add_argument('--观舰类紧急委托', default=default('--观舰类紧急委托'), help='小型观舰仪式, 同盟观舰仪式')

    reward_tactical = reward_parser.add_argument_group('战术学院', '只支持续技能书, 不支持学新技能')
    reward_tactical.add_argument('--启用战术学院收获', default=default('--启用战术学院收获'), choices=['是', '否'])
    reward_tactical.add_argument('--战术学院夜间时段', default=default('--战术学院夜间时段'), help='格式 23:30-06:30')
    reward_tactical.add_argument('--技能书稀有度', default=default('--技能书稀有度'), choices=['3', '2', '1'], help='最多使用T几的技能书\nT3是金书, T2是紫书, T1是蓝书')
    reward_tactical.add_argument('--技能书优先使用同类型', default=default('--技能书优先使用同类型'), choices=['是', '否'], help='选是, 优先使用有150%加成的\n选否, 优先使用同稀有度的技能书')
    reward_tactical.add_argument('--技能书夜间稀有度', default=default('--技能书夜间稀有度'), choices=['3', '2', '1'])
    reward_tactical.add_argument('--技能书夜间优先使用同类型', default=default('--技能书夜间优先使用同类型'), choices=['是', '否'])

    # ==========设备设置==========
    emulator_parser = subs.add_parser('设备设置')
    emulator = emulator_parser.add_argument_group('模拟器', '需要运行一次来保存选项, 会检查游戏是否启动\n若启动了游戏, 触发一次收菜')
    emulator.add_argument('--设备', default=default('--设备'), help='例如 127.0.0.1:62001')
    emulator.add_argument('--包名', default=default('--包名'), help='')

    debug = emulator_parser.add_argument_group('调试设置', '')
    debug.add_argument('--出错时保存log和截图', default=default('--出错时保存log和截图'), choices=['是', '否'])
    debug.add_argument('--保存透视识别出错的图像', default=default('--保存透视识别出错的图像'), choices=['是', '否'])

    adb = emulator_parser.add_argument_group('ADB设置', '')
    adb.add_argument('--使用ADB截图', default=default('--使用ADB截图'), choices=['是', '否'], help='建议开启, 能减少CPU占用')
    adb.add_argument('--使用ADB点击', default=default('--使用ADB点击'), choices=['是', '否'], help='建议关闭, 能加快点击速度')
    adb.add_argument('--战斗中截图间隔', default=default('--战斗中截图间隔'), help='战斗中放慢截图速度, 降低CPU使用')

    # ==========每日任务==========
    daily_parser = subs.add_parser('每日任务困难演习')

    # 选择每日
    daily = daily_parser.add_argument_group('选择每日', '每日任务, 演习, 困难图')
    daily.add_argument('--打每日', default=default('--打每日'), help='若当天有记录, 则跳过', choices=['是', '否'])
    daily.add_argument('--打困难', default=default('--打困难'), help='若当天有记录, 则跳过', choices=['是', '否'])
    daily.add_argument('--打演习', default=default('--打演习'), help='若在刷新后有记录, 则跳过', choices=['是', '否'])

    # 每日设置
    daily_task = daily_parser.add_argument_group('每日设置', '不支持潜艇每日')
    daily_task.add_argument('--战术研修', default=default('--战术研修'), choices=['航空', '炮击', '雷击'])
    daily_task.add_argument('--斩首行动', default=default('--斩首行动'), choices=['第一个', '第二个', '第三个'])
    daily_task.add_argument('--商船护航', default=default('--商船护航'), choices=['第一个', '第二个', '第三个'])
    daily_task.add_argument('--海域突进', default=default('--海域突进'), choices=['第一个', '第二个', '第三个'])
    daily_task.add_argument('--每日舰队', default=default('--每日舰队'), choices=['1', '2', '3', '4', '5', '6'])
    daily_task.add_argument('--每日舰队快速换装', default=default('--每日舰队快速换装'), help='打之前换装备, 打完后卸装备, 不需要就填0\n逗号分割, 例如 3, 1, 0, 1, 1, 0')

    # 困难设置
    hard = daily_parser.add_argument_group('困难设置', '需要开启周回模式, 暂时仅支持 10-4')
    hard.add_argument('--困难地图', default=default('--困难地图'), help='比如 10-4')
    hard.add_argument('--困难舰队', default=default('--困难舰队'), choices=['1', '2'])
    hard.add_argument('--困难舰队快速换装', default=default('--困难舰队快速换装'), help='打之前换装备, 打完后卸装备, 不需要就填0\n逗号分割, 例如 3, 1, 0, 1, 1, 0')

    # 演习设置
    exercise = daily_parser.add_argument_group('演习设置', '暂时仅支持经验最多')
    exercise.add_argument('--演习对手选择', default=default('--演习对手选择'), choices=['经验最多', '排名最前', '福利队'], help='暂时仅支持经验最多')
    exercise.add_argument('--演习次数保留', default=default('--演习次数保留'), help='暂时仅支持保留0个')
    exercise.add_argument('--演习尝试次数', default=default('--演习尝试次数'), help='每个对手的尝试次数, 打不过就换')
    exercise.add_argument('--演习SL阈值', default=default('--演习SL阈值'), help='HP<阈值时撤退')
    exercise.add_argument('--演习低血量确认时长', default=default('--演习低血量确认时长'), help='HP低于阈值后, 过一定时长才会撤退\n推荐 1.0 ~ 3.0')
    exercise.add_argument('--演习快速换装', default=default('--演习快速换装'), help='打之前换装备, 打完后卸装备, 不需要就填0\n逗号分割, 例如 3, 1, 0, 1, 1, 0')

    # ==========每日活动图三倍PT==========
    event_ab_parser = subs.add_parser('每日活动图三倍PT')
    event_name = event_ab_parser.add_argument_group('选择活动', '')
    event_name.add_argument('--活动名称ab', default=default('--活动名称ab'), choices=event_folder, help='例如 event_20200326_cn')

    # ==========主线图==========
    main_parser = subs.add_parser('主线图')
    # 选择关卡
    stage = main_parser.add_argument_group('选择关卡', '主线图出击, 目前仅支持前六章和7-2')
    stage.add_argument('--主线地图出击', default=default('--主线地图出击'), help='例如 7-2')

    # ==========活动图==========
    event_parser = subs.add_parser('活动图')

    description = """
    支持「穹顶下的圣咏曲」(event_20200521_cn), 针对D1D3有优化
    D3第一次进图和100%通关时均有剧情战斗, 会导致报错
    出击未优化关卡或地图未达到安全海域时, 使用开荒模式运行(较慢)
    """
    event = event_parser.add_argument_group(
        '选择关卡', '\n'.join([line.strip() for line in description.strip().split('\n')]))
    event.add_argument('--活动地图', default=default('--活动地图'),
                             choices=['a1', 'a2', 'a3', 'b1', 'b2', 'b3', 'c1', 'c2', 'c3', 'd1', 'd2', 'd3'],
                             help='例如 d3')
    event.add_argument('--sp地图', default=default('--sp地图'),
                             choices=['sp1', 'sp2', 'sp3'],
                             help='例如 sp3')
    event.add_argument('--活动名称', default=default('--活动名称'), choices=event_folder, help='例如 event_20200312_cn')

    # ==========半自动==========
    semi_parser = subs.add_parser('半自动辅助点击')
    semi = semi_parser.add_argument_group('半自动模式', '手动选敌, 自动结算, 用于出击未适配的图')
    semi.add_argument('--进图准备', default=default('--进图准备'), help='', choices=['是', '否'])
    semi.add_argument('--跳过剧情', default=default('--跳过剧情'), help='注意, 这会自动确认所有提示框, 包括红脸出击', choices=['是', '否'])

    # ==========7-2三战拣垃圾==========
    c_7_2_parser = subs.add_parser('7-2三战拣垃圾')
    c_7_2 = c_7_2_parser.add_argument_group('7-2三战拣垃圾', '')
    c_7_2.add_argument('--BOSS队踩A3', default=default('--BOSS队踩A3'), choices=['是', '否'], help='A3有敌人就G3, C3, E3')

    # ==========12-2打中型练级==========
    c_12_2_parser = subs.add_parser('12-2打中型练级')
    c_12_2 = c_12_2_parser.add_argument_group('12-2索敌设置', '')
    c_12_2.add_argument('--大型敌人忍耐', default=default('--大型敌人忍耐'), choices=['0', '1', '2', '10'], help='最多打多少战大型敌人, 不挑敌人选10')

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
    alas = AzurLaneAutoScript(ini_name=ini_name)
    alas.run(command=command)
