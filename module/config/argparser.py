import codecs
import sys

from gooey import Gooey, GooeyParser

import module.config.server as server
from alas import AzurLaneAutoScript
from module.config.dictionary import dic_chi_to_eng
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
    richtext_controls=False, auto_start=False,
    menu=[{
        'name': '文件',
        'items': [{
            'type': 'AboutDialog',
            'menuTitle': '关于',
            'name': 'AzurLaneAutoScript',
            'description': 'Alas, 一个带GUI的碧蓝航线脚本 (支持国服, 国际服, 日服, 可以支持其他服务器).',
            'website': 'https://github.com/LmeSzinc/AzurLaneAutoScript'
        }, {
            'type': 'Link',
            'menuTitle': '访问Github仓库',
            'url': 'https://github.com/LmeSzinc/AzurLaneAutoScript'
        }]
    }, {
        'name': '帮助',
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
    dic_gui_to_ini = dic_chi_to_eng  # GUI translation dictionary here.
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
        '蓝叠模拟器:\t127.0.0.1:5555\n'
        '夜神模拟器:\t127.0.0.1:62001\n'
        'MuMu模拟器:\t127.0.0.1:7555\n'
        '逍遥模拟器:\t127.0.0.1:21503\n'
        '雷电模拟器:\temulator-5554\n'
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

    parser = GooeyParser(description=f'AzurLaneAutoScript, An Azur Lane automation tool. Config: {config_file}\n功能都是分别保存和运行的, 修改设置后别忘了点击"开始"来保存')
    subs = parser.add_subparsers(help='commands', dest='command')

    # ==========出击设置==========
    setting_parser = subs.add_parser('出击设置')

    # 选择关卡
    stage = setting_parser.add_argument_group('关卡设置', '需要运行一次来保存选项', gooey_options={'label_color': '#931D03'})
    stage.add_argument('--启用弹窗提醒', default=default('--启用弹窗提醒'), choices=['是', '否'], help='开启弹窗提醒, 仅 windows10 可用', gooey_options={'label_color': '#4B5F83'})
    # stage.add_argument('--启用停止条件', default=default('--启用停止条件'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    stage.add_argument('--启用异常处理', default=default('--启用异常处理'), choices=['是', '否'], help='处理部分异常, 运行出错时撤退', gooey_options={'label_color': '#4B5F83'})
    stage.add_argument('--使用周回模式', default=default('--使用周回模式'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    stage.add_argument('--使用作战指令书', default=default('--使用作战指令书'), choices=['是', '否'], help='使用高效作战指令书, 两倍消耗两次掉落结算', gooey_options={'label_color': '#4B5F83'})

    stop = stage.add_argument_group('停止条件', '触发后不会马上停止会先完成当前出击, 不需要就填0', gooey_options={'label_color': '#931D03'})
    stop.add_argument('--如果出击次数大于', default=default('--如果出击次数大于'), help='会沿用先前设置, 完成出击将扣除次数, 直至清零', gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--如果时间超过', default=default('--如果时间超过'), help='使用未来24小时内的时间, 会沿用先前设置, 触发后清零. 建议提前10分钟左右, 以完成当前出击. 格式 14:59', gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--如果石油低于', default=default('--如果石油低于'), gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--如果获得新船', default=default('--如果获得新船'), choices=['是', '否'],
                      help='获得新船后进入收获循环',
                      gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--如果地图开荒', default=default('--如果地图开荒'), choices=['否', '地图通关', '地图三星', '地图绿海不打三星', '地图绿海'], help='', gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--如果触发心情控制', default=default('--如果触发心情控制'), choices=['是', '否'], help='若是, 等待回复, 完成本次, 停止\n若否, 等待回复, 完成本次, 继续', gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--如果到达120级', default=default('--如果到达120级'), choices=['是', '否'], help='当舰船从119级升至120级时: \n若是, 完成本次, 停止出击\n若否, 继续出击', gooey_options={'label_color': '#4B5F83'})
    # stop.add_argument('--如果船舱已满', default=default('--如果船舱已满'), choices=['是', '否'])

    # 出击舰队
    fleet = setting_parser.add_argument_group('出击舰队', '非活动图或周回模式会忽略步长设置', gooey_options={'label_color': '#931D03'})
    fleet.add_argument('--启用阵容锁定', default=default('--启用阵容锁定'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    fleet.add_argument('--启用困难图舰队反转', default=default('--启用困难图舰队反转'), choices=['是', '否'], help='使用二队打道中, 一队打BOSS, 仅困难图和活动困难图生效, 开启自律寻敌时此项不生效', gooey_options={'label_color': '#4B5F83'})
    fleet.add_argument('--启用自律寻敌', default=default('--启用自律寻敌'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    fleet.add_argument('--自律寻敌设置', default=default('--自律寻敌设置'), choices=['一队道中二队BOSS', '一队BOSS二队道中', '一队全部二队待机', '一队待机二队全部'], gooey_options={'label_color': '#4B5F83'})

    f1 = fleet.add_argument_group('道中队', '开启自律寻敌时, 这是一队', gooey_options={'label_color': '#931D03'})
    f1.add_argument('--舰队编号1', default=default('--舰队编号1'), choices=['1', '2', '3', '4', '5', '6'], gooey_options={'label_color': '#4B5F83'})
    f1.add_argument('--舰队阵型1', default=default('--舰队阵型1'), choices=['单纵阵', '复纵阵', '轮形阵'], gooey_options={'label_color': '#4B5F83'})
    f1.add_argument('--自律模式1', default=default('--自律模式1'), choices=['自律', '手操', '中路站桩', '躲左下角'], gooey_options={'label_color': '#4B5F83'})
    f1.add_argument('--舰队步长1', default=default('--舰队步长1'), choices=['1', '2', '3', '4', '5', '6'], gooey_options={'label_color': '#4B5F83'})

    f2 = fleet.add_argument_group('BOSS队', '开启自律寻敌时, 这是二队', gooey_options={'label_color': '#931D03'})
    f2.add_argument('--舰队编号2', default=default('--舰队编号2'), choices=['不使用', '1', '2', '3', '4', '5', '6'], gooey_options={'label_color': '#4B5F83'})
    f2.add_argument('--舰队阵型2', default=default('--舰队阵型2'), choices=['单纵阵', '复纵阵', '轮形阵'], gooey_options={'label_color': '#4B5F83'})
    f2.add_argument('--自律模式2', default=default('--自律模式2'), choices=['自律', '手操', '中路站桩', '躲左下角'], gooey_options={'label_color': '#4B5F83'})
    f2.add_argument('--舰队步长2', default=default('--舰队步长2'), choices=['1', '2', '3', '4', '5', '6'], gooey_options={'label_color': '#4B5F83'})

    # 潜艇设置
    submarine = setting_parser.add_argument_group('潜艇设置', '仅支持: 不使用, 仅狩猎, 每战出击', gooey_options={'label_color': '#931D03'})
    submarine.add_argument('--舰队编号4', default=default('--舰队编号4'), choices=['不使用', '1', '2'], gooey_options={'label_color': '#4B5F83'})
    submarine.add_argument('--潜艇出击方案', default=default('--潜艇出击方案'), choices=['不使用', '仅狩猎', '每战出击', '空弹出击', 'BOSS战出击', 'BOSS战BOSS出现后召唤'], gooey_options={'label_color': '#4B5F83'})

    # 心情控制
    emotion = setting_parser.add_argument_group('心情控制', gooey_options={'label_color': '#931D03'})
    emotion.add_argument('--启用心情消耗', default=default('--启用心情消耗'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    emotion.add_argument('--无视红脸出击警告', default=default('--无视红脸出击警告'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    e1 = emotion.add_argument_group('道中队', gooey_options={'label_color': '#931D03'})
    e1.add_argument('--心情回复1', default=default('--心情回复1'), choices=['未放置于后宅', '后宅一楼', '后宅二楼'], gooey_options={'label_color': '#4B5F83'})
    e1.add_argument('--心情控制1', default=default('--心情控制1'), choices=['保持经验加成', '防止绿脸', '防止黄脸', '防止红脸'], gooey_options={'label_color': '#4B5F83'})
    e1.add_argument('--全员已婚1', default=default('--全员已婚1'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    e2 = emotion.add_argument_group('BOSS队', gooey_options={'label_color': '#931D03'})
    e2.add_argument('--心情回复2', default=default('--心情回复2'), choices=['未放置于后宅', '后宅一楼', '后宅二楼'], gooey_options={'label_color': '#4B5F83'})
    e2.add_argument('--心情控制2', default=default('--心情控制2'), choices=['保持经验加成', '防止绿脸', '防止黄脸', '防止红脸'], gooey_options={'label_color': '#4B5F83'})
    e2.add_argument('--全员已婚2', default=default('--全员已婚2'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    # 血量平衡
    hp = setting_parser.add_argument_group('血量控制', '需关闭舰队锁定才能生效', gooey_options={'label_color': '#931D03'})
    hp.add_argument('--启用血量平衡', default=default('--启用血量平衡'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    hp.add_argument('--启用低血量撤退', default=default('--启用低血量撤退'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    hp_balance = hp.add_argument_group('血量平衡', '', gooey_options={'label_color': '#4B5F83'})
    hp_balance.add_argument('--先锋血量平衡阈值', default=default('--先锋血量平衡阈值'), help='血量差值大于阈值时, 换位', gooey_options={'label_color': '#4B5F83'})
    hp_balance.add_argument('--先锋血量权重', default=default('--先锋血量权重'), help='先锋肉度有差别时应修改, 格式 1000,1000,1000', gooey_options={'label_color': '#4B5F83'})
    hp_add = hp.add_argument_group('紧急维修', '', gooey_options={'label_color': '#4B5F83'})
    hp_add.add_argument('--紧急维修单人阈值', default=default('--紧急维修单人阈值'), help='单人低于阈值时使用', gooey_options={'label_color': '#4B5F83'})
    hp_add.add_argument('--紧急维修全队阈值', default=default('--紧急维修全队阈值'), help='前排全部或后排全部低于阈值时使用', gooey_options={'label_color': '#4B5F83'})
    hp_withdraw = hp.add_argument_group('低血量撤退', '', gooey_options={'label_color': '#4B5F83'})
    hp_withdraw.add_argument('--低血量撤退阈值', default=default('--低血量撤退阈值'), help='任意一人血量低于阈值时, 撤退', gooey_options={'label_color': '#4B5F83'})

    # 退役选项
    retire = setting_parser.add_argument_group('退役设置', '', gooey_options={'label_color': '#931D03'})
    retire.add_argument('--启用退役', default=default('--启用退役'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--退役方案', default=default('--退役方案'), choices=['强化角色', '一键退役', '传统退役'], help='若选择强化, 当强化材料不足时, 将使用一键退役', gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--退役数量', default=default('--退役数量'), choices=['退役全部', '退役10个'], gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--强化常用角色', default=default('--强化常用角色'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--强化过滤字符串', default=default('--强化过滤字符串'), help='格式: "cv > bb > ...", 留空则使用默认强化方式', gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--强化每分类数量', default=default('--强化每分类数量'), help='每个舰船分类最多强化多少舰船, 在战斗中的舰船会被跳过且不计入', gooey_options={'label_color': '#4B5F83'})

    rarity = retire.add_argument_group('退役稀有度', '暂不支持舰种选择, 使用一键退役时忽略以下选项', gooey_options={'label_color': '#931D03'})
    rarity.add_argument('--退役白皮', default=default('--退役白皮'), choices=['是', '否'], help='N', gooey_options={'label_color': '#4B5F83'})
    rarity.add_argument('--退役蓝皮', default=default('--退役蓝皮'), choices=['是', '否'], help='R', gooey_options={'label_color': '#4B5F83'})
    # rarity.add_argument('--退役紫皮', default=default('--退役紫皮'), choices=['是', '否'], help='SR', gooey_options={'label_color': '#4B5F83'})
    # rarity.add_argument('--退役金皮', default=default('--退役金皮'), choices=['是', '否'], help='SSR', gooey_options={'label_color': '#4B5F83'})

    # 掉落记录
    drop = setting_parser.add_argument_group('掉落记录', '保存掉落物品的截图, 启用后会放缓结算时的点击速度', gooey_options={'label_color': '#931D03'})
    drop.add_argument('--启用掉落记录', default=default('--启用掉落记录'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    drop.add_argument('--启用AzurStat', default=default('--启用AzurStat'), choices=['是', '否'], help='将掉落截图上传至 azurstats.lyoko.io, 目前只支持科研统计', gooey_options={'label_color': '#4B5F83'})
    drop.add_argument('--掉落保存目录', default=default('--掉落保存目录'), gooey_options={'label_color': '#4B5F83'})

    # clear = setting_parser.add_argument_group('开荒模式', '未开荒地图会在完成后停止, 已开荒的地图会忽略选项, 无脑开就完事了')
    # clear.add_argument('--启用开荒', default=default('--启用开荒'), choices=['是', '否'])
    # clear.add_argument('--开荒停止条件', default=default('--开荒停止条件'), choices=['地图通关', '地图三星', '地图绿海'])
    # clear.add_argument('--地图全清星星', default=default('--地图全清星星'), choices=['第一个', '第二个', '第三个', '不使用'], help='第几颗星星是击破所有敌舰')

    # ==========收菜设置==========
    reward_parser = subs.add_parser('收菜设置')
    reward_condition = reward_parser.add_argument_group('触发条件', '需要运行一次来保存选项, 运行后会进入挂机收菜模式', gooey_options={'label_color': '#931D03'})
    reward_condition.add_argument('--启用收获', default=default('--启用收获'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_condition.add_argument('--收菜间隔', default=default('--收菜间隔'), help='每隔多少分钟触发收菜, 推荐使用时间区间, 比如"10, 40"', gooey_options={'label_color': '#4B5F83'})
    reward_condition.add_argument('--收菜间隔关闭游戏', default=default('--收菜间隔关闭游戏'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_condition.add_argument('--启用每日收获', default=default('--启用每日收获'), choices=['是', '否'], help='将每日任务困难演习作为收获的一部分来运行', gooey_options={'label_color': '#4B5F83'})

    reward_general = reward_parser.add_argument_group('日常收获', '', gooey_options={'label_color': '#931D03'})
    reward_general.add_argument('--启用石油收获', default=default('--启用石油收获'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_general.add_argument('--启用物资收获', default=default('--启用物资收获'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_general.add_argument('--启用任务收获', default=default('--启用任务收获'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_general.add_argument('--启用档案密钥收获', default=default('--启用档案密钥收获'), help='领取作战档案的档案密钥, 如果已经领取则自动跳过', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})


    reward_dorm = reward_parser.add_argument_group('后宅设置', '', gooey_options={'label_color': '#931D03'})
    reward_dorm.add_argument('--启用后宅收获', default=default('--启用后宅收获'), choices=['是', '否'], help='收获好感度和家具币', gooey_options={'label_color': '#4B5F83'})
    reward_dorm.add_argument('--启用后宅喂食', default=default('--启用后宅喂食'), choices=['是', '否'], help='后宅喂食', gooey_options={'label_color': '#4B5F83'})
    reward_dorm.add_argument('--后宅收获间隔', default=default('--后宅收获间隔'),
                             help='每隔多少分钟触发, 推荐使用时间区间, 比如"10, 40"', gooey_options={'label_color': '#4B5F83'})
    reward_dorm.add_argument('--后宅喂食间隔', default=default('--后宅喂食间隔'),
                             help='每隔多少分钟触发, 推荐使用时间区间, 比如"10, 40"\n后宅六船时, 使用六种食物分别需要间隔大于\n(14, 28, 42, 70, 139, 278)', gooey_options={'label_color': '#4B5F83'})
    reward_dorm.add_argument('--后宅喂食优先', default=default('--后宅喂食优先'), help='仿照科研过滤字符串', gooey_options={'label_color': '#4B5F83'})

    reward_commission = reward_parser.add_argument_group('委托设置', '', gooey_options={'label_color': '#931D03'})
    reward_commission.add_argument('--启用委托收获', default=default('--启用委托收获'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_commission.add_argument('--委托时间限制', default=default('--委托时间限制'), help='忽略完成时间超过限制的委托, 格式: 23:30, 不需要就填0', gooey_options={'label_color': '#4B5F83'})

    priority1 = reward_commission.add_argument_group('委托耗时优先级', '', gooey_options={'label_color': '#931D03'})
    priority1.add_argument('--委托耗时小于2h', default=default('--委托耗时小于2h'), help='', gooey_options={'label_color': '#4B5F83'})
    priority1.add_argument('--委托耗时超过6h', default=default('--委托耗时超过6h'), help='', gooey_options={'label_color': '#4B5F83'})
    priority1.add_argument('--委托过期小于2h', default=default('--委托过期小于2h'), help='', gooey_options={'label_color': '#4B5F83'})
    priority1.add_argument('--委托过期大于6h', default=default('--委托过期大于6h'), help='', gooey_options={'label_color': '#4B5F83'})

    priority2 = reward_commission.add_argument_group('日常委托优先级', '', gooey_options={'label_color': '#931D03'})
    priority2.add_argument('--日常委托', default=default('--日常委托'), help='日常资源开发, 高阶战术研发', gooey_options={'label_color': '#4B5F83'})
    priority2.add_argument('--主要委托', default=default('--主要委托'), help='1200油/1000油委托', gooey_options={'label_color': '#4B5F83'})

    priority3 = reward_commission.add_argument_group('额外委托优先级', '', gooey_options={'label_color': '#931D03'})
    priority3.add_argument('--钻头类额外委托', default=default('--钻头类额外委托'), help='短距离航行训练, 近海防卫巡逻', gooey_options={'label_color': '#4B5F83'})
    priority3.add_argument('--部件类额外委托', default=default('--部件类额外委托'), help='矿脉护卫委托, 林木护卫委托', gooey_options={'label_color': '#4B5F83'})
    priority3.add_argument('--魔方类额外委托', default=default('--魔方类额外委托'), help='舰队高阶演习, 舰队护卫演习', gooey_options={'label_color': '#4B5F83'})
    priority3.add_argument('--石油类额外委托', default=default('--石油类额外委托'), help='小型油田开发, 大型油田开发', gooey_options={'label_color': '#4B5F83'})
    priority3.add_argument('--教材类额外委托', default=default('--教材类额外委托'), help='小型商船护卫, 大型商船护卫', gooey_options={'label_color': '#4B5F83'})

    priority4 = reward_commission.add_argument_group('紧急委托优先级', '', gooey_options={'label_color': '#931D03'})
    priority4.add_argument('--钻头类紧急委托', default=default('--钻头类紧急委托'), help='保卫运输部队, 歼灭敌精锐部队', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--部件类紧急委托', default=default('--部件类紧急委托'), help='支援维拉维拉岛, 支援恐班纳', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--魔方类紧急委托', default=default('--魔方类紧急委托'), help='解救商船, 敌袭', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--教材类紧急委托', default=default('--教材类紧急委托'), help='支援土豪尔岛, 支援萌岛', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--装备类紧急委托', default=default('--装备类紧急委托'), help='BIW装备运输, NYB装备研发', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--钻石类紧急委托', default=default('--钻石类紧急委托'), help='BIW要员护卫, NYB巡视护卫', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--观舰类紧急委托', default=default('--观舰类紧急委托'), help='小型观舰仪式, 同盟观舰仪式', gooey_options={'label_color': '#4B5F83'})

    reward_tactical = reward_parser.add_argument_group('战术学院', '只支持续技能书, 不支持学新技能', gooey_options={'label_color': '#931D03'})
    reward_tactical.add_argument('--启用战术学院收获', default=default('--启用战术学院收获'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    # reward_tactical.add_argument('--战术学院夜间时段', default=default('--战术学院夜间时段'), help='格式 23:30-06:30')
    reward_tactical.add_argument('--技能书优先使用同类型', default=default('--技能书优先使用同类型'), choices=['是', '否'], help='选是, 优先使用有150%加成的\n选否, 优先使用同稀有度的技能书', gooey_options={'label_color': '#4B5F83'})
    reward_tactical.add_argument('--技能书最大稀有度', default=default('--技能书最大稀有度'), choices=['3', '2', '1'], help='最高使用T几的技能书\nT3是金书, T2是紫书, T1是蓝书\n最大值需要大于等于最小值', gooey_options={'label_color': '#4B5F83'})
    reward_tactical.add_argument('--技能书最小稀有度', default=default('--技能书最小稀有度'), choices=['3', '2', '1'], help='最低使用T几的技能书\n', gooey_options={'label_color': '#4B5F83'})
    # reward_tactical.add_argument('--技能书夜间稀有度', default=default('--技能书夜间稀有度'), choices=['3', '2', '1'])
    # reward_tactical.add_argument('--技能书夜间优先使用同类型', default=default('--技能书夜间优先使用同类型'), choices=['是', '否'])
    reward_tactical.add_argument('--如果无技能书可用', default=default('--如果无技能书可用'), choices=['停止学习', '使用第一本'], gooey_options={'label_color': '#4B5F83'})

    reward_research = reward_parser.add_argument_group('科研项目', '科研预设选择为自定义时, 须先阅读 doc/filter_string_en_cn.md\n科研项目的选择将同时满足投入和产出设定\n正在进行科研统计，打开出击设置-掉落记录-启用AzurStat并保存，将自动上传', gooey_options={'label_color': '#931D03'})
    reward_research.add_argument('--启用科研项目收获', default=default('--启用科研项目收获'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    research_input = reward_research.add_argument_group('科研投入', '', gooey_options={'label_color': '#931D03'})
    research_input.add_argument('--科研项目使用魔方', default=default('--科研项目使用魔方'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    research_input.add_argument('--科研项目使用金币', default=default('--科研项目使用金币'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    research_input.add_argument('--科研项目使用部件', default=default('--科研项目使用部件'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    research_output = reward_research.add_argument_group('科研产出', '', gooey_options={'label_color': '#931D03'})
    research_output.add_argument('--科研项目选择预设', default=default('--科研项目选择预设'), choices=research_preset, gooey_options={'label_color': '#4B5F83'})
    research_output.add_argument('--科研过滤字符串', default=default('--科研过滤字符串'), help='仅在科研预设选择为自定义时启用', gooey_options={'label_color': '#4B5F83'})

    reward_meowfficer = reward_parser.add_argument_group('商店购买', '如果已经买过则自动跳过', gooey_options={'label_color': '#931D03'})
    reward_meowfficer.add_argument('--买指挥喵', default=default('--买指挥喵'), help='从0到15, 不需要就填0', gooey_options={'label_color': '#4B5F83'})
    reward_meowfficer.add_argument('--训练指挥喵', default=default('--训练指挥喵'), help='启用指挥喵训练, 每天收一只, 周日收获全部', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    reward_guild = reward_parser.add_argument_group('大舰队', '检查大舰队后勤和大舰队作战', gooey_options={'label_color': '#931D03'})
    reward_guild.add_argument('--启用大舰队后勤', default=default('--启用大舰队后勤'), help='领取大舰队任务, 提交筹备物资, 领取舰队奖励', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_guild.add_argument('--启用大舰队作战', default=default('--启用大舰队作战'), help='执行大舰队作战派遣, 打大舰队BOSS', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_guild.add_argument('--大舰队作战参加阈值', default=default('--大舰队作战参加阈值'), help='从0到1. 比如\'0.5\' 表示只在作战进度 未达到一半时加入, \'1\'表示 不管进度直接加入', gooey_options={'label_color': '#4B5F83'})
    reward_guild.add_argument('--大舰队收获间隔', default=default('--大舰队收获间隔'), help='每隔多少分钟触发, 推荐使用时间区间, 比如"10, 40"', gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_items = reward_guild.add_argument_group('筹备物品提交顺序', '可用字符: t1, t2, t3, oxycola, coolant, coins, oil, and merit. 省略某个字符来跳过该物品的提交', gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_items.add_argument('--物品提交顺序', default=default('--物品提交顺序'), gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_plates = reward_guild.add_argument_group('筹备部件提交顺序', '可用字符: torpedo, antiair, plane, gun, and general. 省略某个字符来跳过该物品的提交', gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_plates.add_argument('--部件提交顺序T1', default=default('--部件提交顺序T1'), gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_plates.add_argument('--部件提交顺序T2', default=default('--部件提交顺序T2'), gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_plates.add_argument('--部件提交顺序T3', default=default('--部件提交顺序T3'), gooey_options={'label_color': '#4B5F83'})
    reward_guild_operations_boss = reward_guild.add_argument_group('大舰队BOSS', '', gooey_options={'label_color': '#4B5F83'})
    reward_guild_operations_boss.add_argument('--启用大舰队BOSS出击', default=default('--启用大舰队BOSS出击'), help='自动打大舰队BOSS, 需要预先在游戏内设置队伍', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_guild_operations_boss.add_argument('--启用大舰队BOSS队伍推荐', default=default('--启用大舰队BOSS队伍推荐'), help='使用游戏自动推荐的队伍打BOSS', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    # ==========设备设置==========
    emulator_parser = subs.add_parser('设备设置')
    emulator = emulator_parser.add_argument_group('模拟器', '需要运行一次来保存选项, 会检查游戏是否启动\n若启动了游戏, 触发一次收菜', gooey_options={'label_color': '#931D03'})
    emulator.add_argument('--设备', default=default('--设备'), help='例如 127.0.0.1:62001', gooey_options={'label_color': '#4B5F83'})
    emulator.add_argument('--包名', default=default('--包名'), help='', gooey_options={'label_color': '#4B5F83'})
    emulator.add_argument(
        '默认serial列表',
        default=message,
        widget='Textarea',
        help="以下是一些常见模拟器的默认serial\n如果你使用了模拟器多开, 它们将不使用默认的serial",
        gooey_options={
            'height': 150,
            'show_help': True,
            'show_label': True,
            'readonly': True,
            'label_color': '#4B5F83'
        }
    )

    debug = emulator_parser.add_argument_group('调试设置', '', gooey_options={'label_color': '#931D03'})
    debug.add_argument('--出错时保存log和截图', default=default('--出错时保存log和截图'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    debug.add_argument('--保存透视识别出错的图像', default=default('--保存透视识别出错的图像'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    adb = emulator_parser.add_argument_group('ADB设置', '', gooey_options={'label_color': '#931D03'})
    adb.add_argument('--设备截图方案', default=default('--设备截图方案'), choices=['aScreenCap', 'uiautomator2', 'ADB'], help='速度: aScreenCap >> uiautomator2 > ADB', gooey_options={'label_color': '#4B5F83'})
    adb.add_argument('--设备控制方案', default=default('--设备控制方案'), choices=['minitouch','uiautomator2', 'ADB'], help='速度: minitouch >> uiautomator2 >> ADB', gooey_options={'label_color': '#4B5F83'})
    adb.add_argument('--战斗中截图间隔', default=default('--战斗中截图间隔'), help='战斗中放慢截图速度, 降低CPU使用', gooey_options={'label_color': '#4B5F83'})

    update = emulator_parser.add_argument_group('更新检查', '', gooey_options={'label_color': '#931D03'})
    update.add_argument('--启用更新检查', default=default('--启用更新检查'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    update.add_argument('--更新检查方法', default=default('--更新检查方法'), choices=['api', 'web'], help='使用api时建议填写tokens, 使用web则不需要', gooey_options={'label_color': '#4B5F83'})
    update.add_argument('--github_token', default=default('--github_token'), help='Github API限制为每小时60次, 获取tokens https://github.com/settings/tokens', gooey_options={'label_color': '#4B5F83'})
    update.add_argument('--更新检查代理', default=default('--更新检查代理'), help='本地http或socks代理, 如果github很慢, 请使用代理, example: http://127.0.0.1:10809', gooey_options={'label_color': '#4B5F83'})

    # ==========每日任务==========
    daily_parser = subs.add_parser('每日任务困难演习')

    # 选择每日
    daily = daily_parser.add_argument_group('选择每日', '每日任务, 演习, 困难图', gooey_options={'label_color': '#931D03'})
    daily.add_argument('--打每日', default=default('--打每日'), help='若当天有记录, 则跳过', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--打困难', default=default('--打困难'), help='若当天有记录, 则跳过', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--打演习', default=default('--打演习'), help='若在刷新后有记录, 则跳过', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--打共斗每日15次', default=default('--打共斗每日15次'), help='若当天有记录, 则跳过', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--打活动图每日三倍PT', default=default('--打活动图每日三倍PT'), help='若当天有记录, 则跳过', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--打活动每日SP图', default=default('--打活动每日SP图'), help='若当天有记录, 则跳过', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--打大世界余烬信标支援', default=default('--打大世界余烬信标支援'), help='若当天有记录, 则跳过', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    # 每日设置
    daily_task = daily_parser.add_argument_group('每日设置', '', gooey_options={'label_color': '#931D03'})
    daily_task.add_argument('--使用每日扫荡', default=default('--使用每日扫荡'), help='每日扫荡可用时使用扫荡', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--战术研修', default=default('--战术研修'), choices=['航空', '炮击', '雷击'], gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--斩首行动', default=default('--斩首行动'), choices=['第一个', '第二个', '第三个'], gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--破交作战', default=default('--破交作战'), choices=['第一个', '第二个', '第三个'], help='需要解锁扫荡, 未解锁时跳过', gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--商船护航', default=default('--商船护航'), choices=['第一个', '第二个', '第三个'], gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--海域突进', default=default('--海域突进'), choices=['第一个', '第二个', '第三个'], gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--每日舰队', default=default('--每日舰队'), help='如果使用同一队, 填舰队编号, 例如 5\n如果使用不同队, 用逗号分割, 顺序为商船护送, 海域突进, 斩首行动, 战术研修\n例如 5, 5, 5, 6', gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--每日舰队快速换装', default=default('--每日舰队快速换装'), help='打之前换装备, 打完后卸装备, 不需要就填0\n逗号分割, 例如 3, 1, 0, 1, 1, 0', gooey_options={'label_color': '#4B5F83'})

    # 困难设置
    hard = daily_parser.add_argument_group('困难设置', '需要地图达到周回模式', gooey_options={'label_color': '#931D03'})
    hard.add_argument('--困难地图', default=default('--困难地图'), help='比如 10-4', gooey_options={'label_color': '#4B5F83'})
    hard.add_argument('--困难舰队', default=default('--困难舰队'), choices=['1', '2'], gooey_options={'label_color': '#4B5F83'})
    hard.add_argument('--困难舰队快速换装', default=default('--困难舰队快速换装'), help='打之前换装备, 打完后卸装备, 不需要就填0\n逗号分割, 例如 3, 1, 0, 1, 1, 0', gooey_options={'label_color': '#4B5F83'})

    # 演习设置
    exercise = daily_parser.add_argument_group('演习设置', '', gooey_options={'label_color': '#931D03'})
    exercise.add_argument('--演习对手选择', default=default('--演习对手选择'), choices=['经验最多', '最简单', '最左边', '先最简单再经验最多'], help='', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--演习次数保留', default=default('--演习次数保留'), help='例如 1, 表示打到1/10停止', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--演习尝试次数', default=default('--演习尝试次数'), help='每个对手的尝试次数, 打不过就换', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--演习SL阈值', default=default('--演习SL阈值'), help='HP<阈值时撤退', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--演习低血量确认时长', default=default('--演习低血量确认时长'), help='HP低于阈值后, 过一定时长才会撤退\n推荐 1.0 ~ 3.0', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--演习快速换装', default=default('--演习快速换装'), help='打之前换装备, 打完后卸装备, 不需要就填0\n逗号分割, 例如 3, 1, 0, 1, 1, 0', gooey_options={'label_color': '#4B5F83'})

    # 每日活动图三倍PT
    event_bonus = daily_parser.add_argument_group('活动设置', '', gooey_options={'label_color': '#931D03'})
    event_bonus.add_argument('--活动奖励章节', default=default('--活动奖励章节'), choices=['AB图', 'ABCD图', 'T图', 'HT图'], help='有额外PT奖励章节', gooey_options={'label_color': '#4B5F83'})
    event_bonus.add_argument('--活动SP图道中队', default=default('--活动SP图道中队'), choices=['1', '2'], help='', gooey_options={'label_color': '#4B5F83'})
    event_bonus.add_argument('--活动名称ab', default=event_latest, choices=event_folder, help='例如 event_20200326_cn', gooey_options={'label_color': '#4B5F83'})

    # 共斗每日设置
    raid_bonus = daily_parser.add_argument_group('共斗设置', '', gooey_options={'label_color': '#931D03'})
    raid_bonus.add_argument('--共斗每日名称', default=raid_latest, choices=raid_folder, help='', gooey_options={'label_color': '#4B5F83'})
    raid_bonus.add_argument('--共斗困难', default=default('--共斗困难'), choices=['是', '否'], help='', gooey_options={'label_color': '#4B5F83'})
    raid_bonus.add_argument('--共斗普通', default=default('--共斗普通'), choices=['是', '否'], help='', gooey_options={'label_color': '#4B5F83'})
    raid_bonus.add_argument('--共斗简单', default=default('--共斗简单'), choices=['是', '否'], help='', gooey_options={'label_color': '#4B5F83'})

    # 大世界每日设置
    raid_bonus = daily_parser.add_argument_group('大世界设置', '', gooey_options={'label_color': '#931D03'})
    raid_bonus.add_argument('--大世界信标支援强度', default=default('--大世界信标支援强度'), help='寻找大于等于此强度的信标', gooey_options={'label_color': '#4B5F83'})

    # # ==========每日活动图三倍PT==========
    # event_ab_parser = subs.add_parser('每日活动图三倍PT')
    # event_name = event_ab_parser.add_argument_group('选择活动', '')
    # event_name.add_argument('--活动名称ab', default=event_latest, choices=event_folder, help='例如 event_20200326_cn')

    # ==========主线图==========
    main_parser = subs.add_parser('主线图')
    # 选择关卡
    stage = main_parser.add_argument_group('选择关卡', '', gooey_options={'label_color': '#931D03'})
    stage.add_argument('--主线地图出击', default=default('--主线地图出击'), help='例如 7-2', gooey_options={'label_color': '#4B5F83'})
    stage.add_argument('--主线地图模式', default=default('--主线地图模式'), help='仅困难图开荒时使用, 周回模式后请使用每日困难', choices=['普通', '困难'], gooey_options={'label_color': '#4B5F83'})

    # ==========活动图==========
    event_parser = subs.add_parser('活动图')

    description = """
    出击未优化关卡或地图未达到安全海域时, 使用开荒模式运行(较慢)
    """
    event = event_parser.add_argument_group(
        '选择关卡', '\n'.join([line.strip() for line in description.strip().split('\n')]), gooey_options={'label_color': '#931D03'})
    event.add_argument('--活动地图', default=default('--活动地图'), help='输入地图名称, 不分大小写, 例如 D3, SP3, HT6', gooey_options={'label_color': '#4B5F83'})
    event.add_argument('--活动名称', default=event_latest, choices=event_folder, help='例如 event_20200312_cn', gooey_options={'label_color': '#4B5F83'})

    # ==========潜艇图==========
    sos_parser = subs.add_parser('潜艇图')
    sos = sos_parser.add_argument_group(
        '潜艇图设置', '设置每张潜艇图的队伍, 顺序: 一队二队潜艇队\n例如 "4, 6", "4, 0", "4, 6, 1"\n填0跳过不打', gooey_options={'label_color': '#931D03'})
    sos.add_argument('--第3章潜艇图队伍', default=default('--第3章潜艇图队伍'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--第4章潜艇图队伍', default=default('--第4章潜艇图队伍'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--第5章潜艇图队伍', default=default('--第5章潜艇图队伍'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--第6章潜艇图队伍', default=default('--第6章潜艇图队伍'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--第7章潜艇图队伍', default=default('--第7章潜艇图队伍'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--第8章潜艇图队伍', default=default('--第8章潜艇图队伍'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--第9章潜艇图队伍', default=default('--第9章潜艇图队伍'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--第10章潜艇图队伍', default=default('--第10章潜艇图队伍'), gooey_options={'label_color': '#4B5F83'})

    # ==========作战档案==========
    war_archives_parser = subs.add_parser('作战档案')
    war_archives = war_archives_parser.add_argument_group(
        '作战档案设置', '输入地图名称, 然后选择对应的活动', gooey_options={'label_color': '#931D03'})
    war_archives.add_argument('--作战档案地图', default=default('--作战档案地图'), help='输入地图名称, 不分大小写, 例如 D3, SP3, HT6', gooey_options={'label_color': '#4B5F83'})
    war_archives.add_argument('--作战档案活动', default=default('--作战档案活动'), choices=archives_folder, help='在下拉菜单中选择活动', gooey_options={'label_color': '#4B5F83'})

    # ==========共斗活动==========
    raid_parser = subs.add_parser('共斗活动')
    raid = raid_parser.add_argument_group('选择共斗', '', gooey_options={'label_color': '#931D03'})
    raid.add_argument('--共斗名称', default=raid_latest, choices=raid_folder, help='', gooey_options={'label_color': '#4B5F83'})
    raid.add_argument('--共斗难度', default=default('--共斗难度'), choices=['困难', '普通', '简单'], help='', gooey_options={'label_color': '#4B5F83'})
    raid.add_argument('--共斗使用挑战券', default=default('--共斗使用挑战券'), choices=['是', '否'], help='', gooey_options={'label_color': '#4B5F83'})

    # ==========半自动==========
    semi_parser = subs.add_parser('半自动辅助点击')
    semi = semi_parser.add_argument_group('半自动模式', '手动选敌, 自动结算, 用于出击未适配的图', gooey_options={'label_color': '#931D03'})
    semi.add_argument('--进图准备', default=default('--进图准备'), help='', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    semi.add_argument('--跳过剧情', default=default('--跳过剧情'), help='注意, 这会自动确认所有提示框, 包括红脸出击', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    # ==========1-1Affinity farming==========
    c_1_1_parser = subs.add_parser('1-1伏击刷好感')
    c_1_1 = c_1_1_parser.add_argument_group('1-1伏击刷好感', '会自动关闭周回模式\n有MVP, 8场战斗涨1点好感, 无MVP, 16场战斗涨1点好感', gooey_options={'label_color': '#931D03'})
    c_1_1.add_argument('--刷好感战斗场数', default=default('--刷好感战斗场数'), help='例如: 32', gooey_options={'label_color': '#4B5F83'})

    # ==========7-2三战拣垃圾==========
    c_7_2_parser = subs.add_parser('7-2三战拣垃圾')
    c_7_2 = c_7_2_parser.add_argument_group('7-2三战拣垃圾', '', gooey_options={'label_color': '#931D03'})
    c_7_2.add_argument('--BOSS队踩A3', default=default('--BOSS队踩A3'), choices=['是', '否'], help='A3有敌人就G3, C3, E3', gooey_options={'label_color': '#4B5F83'})

    # ==========12-2打中型练级==========
    c_12_2_parser = subs.add_parser('12-2打中型练级')
    c_12_2 = c_12_2_parser.add_argument_group('12-2索敌设置', '', gooey_options={'label_color': '#931D03'})
    c_12_2.add_argument('--大型敌人忍耐', default=default('--大型敌人忍耐'), choices=['0', '1', '2', '10'], help='最多打多少战大型敌人, 不挑敌人选10', gooey_options={'label_color': '#4B5F83'})

    # ==========12-4打大型练级==========
    c_12_4_parser = subs.add_parser('12-4打大型练级')
    c_12_4 = c_12_4_parser.add_argument_group('12-4索敌设置', '需保证队伍有一定强度', gooey_options={'label_color': '#931D03'})
    c_12_4.add_argument('--非大型敌人进图忍耐', default=default('--非大型敌人进图忍耐'), choices=['0', '1', '2'], help='忍受进场多少战没有大型', gooey_options={'label_color': '#4B5F83'})
    c_12_4.add_argument('--非大型敌人撤退忍耐', default=default('--非大型敌人撤退忍耐'), choices=['0', '1', '2', '10'], help='没有大型之后还会打多少战, 不挑敌人选10', gooey_options={'label_color': '#4B5F83'})
    c_12_4.add_argument('--拣弹药124', default=default('--拣弹药124'), choices=['2', '3', '4', '5'], help='多少战后拣弹药', gooey_options={'label_color': '#4B5F83'})

    # ==========OS semi auto==========
    os_semi_parser = subs.add_parser('大世界辅助点击')
    os_semi = os_semi_parser.add_argument_group('大世界辅助点击', '自动点击战斗准备和战斗结算\n仅推荐在普通海域和安全海域中开启', gooey_options={'label_color': '#931D03'})
    os_semi.add_argument('--大世界跳过剧情', default=default('--大世界跳过剧情'), choices=['是', '否'], help='注意, 这会自动点击地图交互的选项', gooey_options={'label_color': '#4B5F83'})

    # ==========OS clear map==========
    # os_semi_parser = subs.add_parser('大世界地图全清')
    # os_semi = os_semi_parser.add_argument_group('大世界地图全清', '仅在安全海域中使用, 在普通海域使用时需要先执行空域搜索\n使用方法: 先手动进入地图, 再运行\n运行结束后, 最好手动检查是否有遗漏', gooey_options={'label_color': '#931D03'})
    # os_semi.add_argument('--打大世界余烬信标', default=default('--打大世界余烬信标'), choices=['是', '否'], help='信标数据满了之后, 打飞龙', gooey_options={'label_color': '#4B5F83'})

    # ==========OS clear world==========
    os_world_parser = subs.add_parser('大世界每月全清')
    os_world = os_world_parser.add_argument_group('大世界每月全清',
                                                  '在运行之前, 必须通关大世界主线, 购买并使用战役信息记录仪 (5000油道具)\n'
                                                  '这个模块将从低侵蚀到高侵蚀地清理海域\n'
                                                  '请确保你的舰队和适应性足够对付高侵蚀海域',
                                                  gooey_options={'label_color': '#931D03'})
    os_world.add_argument('--大世界全清侵蚀下限', default=default('--大世界全清侵蚀下限'), help='上限和下限一样时, 只清理特定侵蚀等级', choices=['1', '2', '3', '4', '5', '6'], gooey_options={'label_color': '#4B5F83'})
    os_world.add_argument('--大世界全清侵蚀上限', default=default('--大世界全清侵蚀上限'), help='', choices=['1', '2', '3', '4', '5', '6'], gooey_options={'label_color': '#4B5F83'})

    # ==========OS fully auto==========
    os_parser = subs.add_parser('大世界全自动')
    os = os_parser.add_argument_group('大世界全自动', '运行顺序: 接每日买补给 > 做每日 > 打隐秘海域 > 短猫相接\n港口补给是有限池, 总量恒定随机出现, 想要买好东西需要全买\n商店优先级格式: ActionPoint > PurpleCoins > TuringSample > RepairPack', gooey_options={'label_color': '#931D03'})
    os.add_argument('--在每日中完成大世界', default=default('--在每日中完成大世界'), choices=['是', '否'], help='将大世界全自动作为每日的一部分来完成', gooey_options={'label_color': '#4B5F83'})

    os_daily = os.add_argument_group('大世界每日', '', gooey_options={'label_color': '#931D03'})
    os_daily.add_argument('--大世界接每日任务', default=default('--大世界接每日任务'), choices=['是', '否'], help='在港口领取每日任务', gooey_options={'label_color': '#4B5F83'})
    os_daily.add_argument('--大世界完成每日', default=default('--大世界完成每日'), choices=['是', '否'], help='前往每日的海域, 并清理', gooey_options={'label_color': '#4B5F83'})
    os_daily.add_argument('--大世界港口补给', default=default('--大世界港口补给'), choices=['是', '否'], help='买光所有的港口补给', gooey_options={'label_color': '#4B5F83'})
    os_daily.add_argument('--打大世界余烬信标', default=default('--打大世界余烬信标'), choices=['是', '否'], help='信标数据满了之后, 打飞龙', gooey_options={'label_color': '#4B5F83'})

    os_farm = os.add_argument_group('打大世界', '', gooey_options={'label_color': '#931D03'})
    os_farm.add_argument('--打大世界隐秘海域', default=default('--打大世界隐秘海域'), choices=['是', '否'], help='[开发中]清理所有隐秘海域', gooey_options={'label_color': '#4B5F83'})
    os_farm.add_argument('--大世界短猫相接', default=default('--大世界短猫相接'), choices=['是', '否'], help='反复打图拣猫点', gooey_options={'label_color': '#4B5F83'})
    os_farm.add_argument('--短猫相接侵蚀等级', default=default('--短猫相接侵蚀等级'), choices=['1', '2', '3', '4', '5', '6'], help='侵蚀3和5有更高的猫点/行动力比, 建议选侵蚀5', gooey_options={'label_color': '#4B5F83'})

    os_setting = os.add_argument_group('大世界设置', '', gooey_options={'label_color': '#931D03'})
    os_setting.add_argument('--大世界买行动力', default=default('--大世界买行动力'), choices=['是', '否'], help='用石油买行动力, 先买再开箱子', gooey_options={'label_color': '#4B5F83'})
    os_setting.add_argument('--大世界行动力保留', default=default('--大世界行动力保留'), help='低于此值后停止, 含行动力箱子', gooey_options={'label_color': '#4B5F83'})
    os_setting.add_argument('--大世界修船阈值', default=default('--大世界修船阈值'), help='任意一艘船血量低于此值时, 前往最近港口修理. 从0到1.', gooey_options={'label_color': '#4B5F83'})

    os_shop = os.add_argument_group('大世界商店', '', gooey_options={'label_color': '#931D03'})
    os_shop.add_argument('--明石商店购买', default=default('--明石商店购买'), choices=['是', '否'], help='', gooey_options={'label_color': '#4B5F83'})
    os_shop.add_argument('--明石商店优先级', default=default('--明石商店优先级'), help='', gooey_options={'label_color': '#4B5F83'})

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
