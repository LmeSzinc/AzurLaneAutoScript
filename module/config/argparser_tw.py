import codecs
import sys

from gooey import Gooey, GooeyParser

import module.config.server as server
from alas import AzurLaneAutoScript
from module.config.dictionary import dic_tchi_to_eng
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
            'menuTitle': '關於',
            'name': 'AzurLaneAutoScript',
            'description': 'Alas, 一個帶GUI的碧藍航線腳本 (支援國服、國際服、日服及台服, 可以支援其他伺服器).',
            'website': 'https://github.com/LmeSzinc/AzurLaneAutoScript'
        }, {
            'type': 'Link',
            'menuTitle': '前往Github倉庫',
            'url': 'https://github.com/LmeSzinc/AzurLaneAutoScript'
        }]
    }, {
        'name': '幫助',
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
    dic_gui_to_ini = dic_tchi_to_eng  # GUI translation dictionary here.
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
        '藍疊模擬器:\t127.0.0.1:5555\n'
        '夜神模擬器:\t127.0.0.1:62001\n'
        'MuMu模擬器:\t127.0.0.1:7555\n'
        '逍遙模擬器:\t127.0.0.1:21503\n'
        '雷電模擬器:\temulator-5554\n'
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

    parser = GooeyParser(description=f'AzurLaneAutoScript, An Azur Lane automation tool. Config: {config_file}\n功能都是分別保存和執行的, 修改設定後別忘了點擊"開始"來保存')
    subs = parser.add_subparsers(help='commands', dest='command')

    # ==========出擊設定==========
    setting_parser = subs.add_parser('出擊設定')

    # 選擇關卡
    stage = setting_parser.add_argument_group('關卡設定', '需要執行一次來保存選項', gooey_options={'label_color': '#931D03'})
    stage.add_argument('--啟用彈窗提醒', default=default('--啟用彈窗提醒'), choices=['是', '否'], help='開啟彈窗提醒，僅windows10可用', gooey_options={'label_color': '#4B5F83'})
    # stage.add_argument('--啟用停止條件', default=default('--啟用停止條件'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    stage.add_argument('--啟用異常處理', default=default('--啟用異常處理'), choices=['是', '否'], help='處理部分異常, 執行出錯時撤退', gooey_options={'label_color': '#4B5F83'})
    stage.add_argument('--使用周回模式', default=default('--使用周回模式'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    stage.add_argument('--使用作戰指令書', default=default('--使用作戰指令書'), choices=['是', '否'], help='使用高效作戰指令書, 兩倍消耗兩次掉落結算', gooey_options={'label_color': '#4B5F83'})

    stop = stage.add_argument_group('停止條件', '出發後不會馬上停止, 會先完成目前出擊, 不需要就填0', gooey_options={'label_color': '#931D03'})
    stop.add_argument('--如果出擊數大於', default=default('--如果出擊數大於'), help='會沿用先前設定, 完成出擊將扣除次數, 直至為零', gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--如果時間超過', default=default('--如果時間超過'), help='使用未來24小時內的時間, 會沿用先前設定, 觸發後清零, 建議提前10分鐘左右, 以完成目前出擊。格式 14:59', gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--如果石油低於', default=default('--如果石油低於'), gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--如果獲得新船', default=default('--如果獲得新船'), choices=['是', '否'],
                      help='獲得新船後進入收穫循環',
                      gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--如果地圖開荒', default=default('--如果地圖開荒'), choices=['否', '地圖通關', '地圖三星', '地圖安海不打三星', '地圖安海'], help='', gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--如果觸發心情控制', default=default('--如果觸發心情控制'), choices=['是', '否'], help='若是, 等待回復, 完成本次, 停止\n若否, 等待回復, 完成本次, 繼續', gooey_options={'label_color': '#4B5F83'})
    stop.add_argument('--如果到達120級', default=default('--如果到達120級'), choices=['是', '否'], help='當艦船從119級升至120級时: \n若是, 完成本次, 停止出擊\n若否, 繼續出擊', gooey_options={'label_color': '#4B5F83'})
    # stop.add_argument('--如果船塢已滿', default=default('--如果船塢已滿'), choices=['是', '否'])

    # 出擊艦隊
    fleet = setting_parser.add_argument_group('出擊艦隊', '非活動圖或周回模式會忽略步長設定', gooey_options={'label_color': '#931D03'})
    fleet.add_argument('--啟用陣容鎖定', default=default('--啟用陣容鎖定'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    fleet.add_argument('--啟用困難圖艦隊反轉', default=default('--啟用困難圖艦隊反轉'), choices=['是', '否'], help='使用二隊打道中, 一隊打BOSS, 僅困難圖和活動困難圖生效, 開啟自律尋敵時此項不生效', gooey_options={'label_color': '#4B5F83'})
    fleet.add_argument('--啟用自律尋敵', default=default('--啟用自律尋敵'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    fleet.add_argument('--自律尋敵設置', default=default('--自律尋敵設置'), choices=['一隊道中二隊BOSS', '一隊BOSS二隊道中', '一隊全部二隊待機', '一隊待機二隊全部'], gooey_options={'label_color': '#4B5F83'})

    f1 = fleet.add_argument_group('道中隊', '開啟自律尋敵時, 這是一隊', gooey_options={'label_color': '#931D03'})
    f1.add_argument('--艦隊編號1', default=default('--艦隊編號1'), choices=['1', '2', '3', '4', '5', '6'], gooey_options={'label_color': '#4B5F83'})
    f1.add_argument('--艦隊陣型1', default=default('--艦隊陣型1'), choices=['單縱陣', '復縱陣', '輪型陣'], gooey_options={'label_color': '#4B5F83'})
    f1.add_argument('--自律模式1', default=default('--自律模式1'), choices=['自律', '手操', '中路站樁', '躲左下角'], gooey_options={'label_color': '#4B5F83'})
    f1.add_argument('--艦隊步長1', default=default('--艦隊步長1'), choices=['1', '2', '3', '4', '5', '6'], gooey_options={'label_color': '#4B5F83'})

    f2 = fleet.add_argument_group('BOSS队', '開啟自律尋敵時, 這是二隊', gooey_options={'label_color': '#931D03'})
    f2.add_argument('--艦隊編號2', default=default('--艦隊編號2'), choices=['不使用', '1', '2', '3', '4', '5', '6'], gooey_options={'label_color': '#4B5F83'})
    f2.add_argument('--艦隊陣型2', default=default('--艦隊陣型2'), choices=['單縱陣', '復縱陣', '輪型陣'], gooey_options={'label_color': '#4B5F83'})
    f2.add_argument('--自律模式2', default=default('--自律模式2'), choices=['自律', '手操', '中路站樁', '躲左下角'], gooey_options={'label_color': '#4B5F83'})
    f2.add_argument('--艦隊步長2', default=default('--艦隊步長2'), choices=['1', '2', '3', '4', '5', '6'], gooey_options={'label_color': '#4B5F83'})

    # 潛艇設定
    submarine = setting_parser.add_argument_group('潛艇設定', '僅支援：不使用、僅狩獵、每戰出擊', gooey_options={'label_color': '#931D03'})
    submarine.add_argument('--艦隊編號4', default=default('--艦隊編號4'), choices=['不使用', '1', '2'], gooey_options={'label_color': '#4B5F83'})
    submarine.add_argument('--潛艇出擊方案', default=default('--潛艇出擊方案'), choices=['不使用', '僅狩獵', '每戰出擊', '空彈出擊', 'BOSS戰出擊', 'BOSS戰BOSS出現後招喚'], gooey_options={'label_color': '#4B5F83'})

    # 心情控制
    emotion = setting_parser.add_argument_group('心情控制', gooey_options={'label_color': '#931D03'})
    emotion.add_argument('--啟用心情消耗', default=default('--啟用心情消耗'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    emotion.add_argument('--無視紅臉出擊警告', default=default('--無視紅臉出擊警告'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    e1 = emotion.add_argument_group('道中隊', gooey_options={'label_color': '#931D03'})
    e1.add_argument('--心情回復1', default=default('--心情回復1'), choices=['未放置於後宅', '後宅一樓', '後宅二樓'], gooey_options={'label_color': '#4B5F83'})
    e1.add_argument('--心情控制1', default=default('--心情控制1'), choices=['保持經驗加成', '防止綠臉', '防止黃臉', '防止紅臉'], gooey_options={'label_color': '#4B5F83'})
    e1.add_argument('--全員已婚1', default=default('--全員已婚1'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    e2 = emotion.add_argument_group('BOSS隊', gooey_options={'label_color': '#931D03'})
    e2.add_argument('--心情回復2', default=default('--心情回復2'), choices=['未放置於後宅', '後宅一樓', '後宅二樓'], gooey_options={'label_color': '#4B5F83'})
    e2.add_argument('--心情控制2', default=default('--心情控制2'), choices=['保持經驗加成', '防止綠臉', '防止黃臉', '防止紅臉'], gooey_options={'label_color': '#4B5F83'})
    e2.add_argument('--全員已婚2', default=default('--全員已婚2'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    # 血量平衡
    hp = setting_parser.add_argument_group('血量控制', '需關閉艦隊鎖定才能生效', gooey_options={'label_color': '#931D03'})
    hp.add_argument('--啟用血量平衡', default=default('--啟用血量平衡'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    hp.add_argument('--啟用低血量撤退', default=default('--啟用低血量撤退'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    hp_balance = hp.add_argument_group('血量平衡', '', gooey_options={'label_color': '#4B5F83'})
    hp_balance.add_argument('--先鋒血量平衡閾值', default=default('--先鋒血量平衡閾值'), help='血量差值大於閾值時, 換位', gooey_options={'label_color': '#4B5F83'})
    hp_balance.add_argument('--先鋒血量權重', default=default('--先鋒血量權重'), help='先鋒肉度有差別時應修改, 格式 1000,1000,1000', gooey_options={'label_color': '#4B5F83'})
    hp_add = hp.add_argument_group('緊急維修', '', gooey_options={'label_color': '#4B5F83'})
    hp_add.add_argument('--緊急維修單人閾值', default=default('--緊急維修單人閾值'), help='單人低於閾值時使用', gooey_options={'label_color': '#4B5F83'})
    hp_add.add_argument('--緊急維修全隊閾值', default=default('--緊急維修全隊閾值'), help='前排全部或後排全部低於閾值時使用', gooey_options={'label_color': '#4B5F83'})
    hp_withdraw = hp.add_argument_group('低血量撤退', '', gooey_options={'label_color': '#4B5F83'})
    hp_withdraw.add_argument('--低血量撤退閾值', default=default('--低血量撤退閾值'), help='任意一人血量低於閾值時, 撤退', gooey_options={'label_color': '#4B5F83'})

    # 退役選項
    retire = setting_parser.add_argument_group('退役設定', '', gooey_options={'label_color': '#931D03'})
    retire.add_argument('--啟用退役', default=default('--啟用退役'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--退役方案', default=default('--退役方案'), choices=['強化角色', '一鍵退役', '傳統退役'], help='若選擇強化, 當強化材料不足時, 將使用一鍵退役', gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--退役數量', default=default('--退役數量'), choices=['退役全部', '退役10個'], gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--強化常用角色', default=default('--強化常用角色'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--強化過濾字符串', default=default('--強化過濾字符串'), help='格式: "cv > bb > ...", 留空則使用默認強化方式', gooey_options={'label_color': '#4B5F83'})
    retire.add_argument('--強化每分類數量', default=default('--強化每分類數量'), help='每個艦船分類最多強化多少艦船, 在戰鬥中的艦船會被跳過且不計入', gooey_options={'label_color': '#4B5F83'})

    rarity = retire.add_argument_group('退役稀有度', '暫不支援艦種選擇, 使用一鍵退役時忽略以下選項', gooey_options={'label_color': '#931D03'})
    rarity.add_argument('--退役白皮', default=default('--退役白皮'), choices=['是', '否'], help='N', gooey_options={'label_color': '#4B5F83'})
    rarity.add_argument('--退役藍皮', default=default('--退役藍皮'), choices=['是', '否'], help='R', gooey_options={'label_color': '#4B5F83'})
    # rarity.add_argument('--退役紫皮', default=default('--退役紫皮'), choices=['是', '否'], help='SR', gooey_options={'label_color': '#4B5F83'})
    # rarity.add_argument('--退役金皮', default=default('--退役金皮'), choices=['是', '否'], help='SSR', gooey_options={'label_color': '#4B5F83'})

    # 掉落記錄
    drop = setting_parser.add_argument_group('掉落記錄', '保存掉落物品的截圖, 啟用後會放緩結算時的點擊速度', gooey_options={'label_color': '#931D03'})
    drop.add_argument('--啟用掉落記錄', default=default('--啟用掉落記錄'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    drop.add_argument('--啟用AzurStat', default=default('--啟用AzurStat'), choices=['是', '否'], help='將掉落截圖上傳至 azurstats.lyoko.io, 目前只支持科研統計', gooey_options={'label_color': '#4B5F83'})
    drop.add_argument('--掉落保存目錄', default=default('--掉落保存目錄'), gooey_options={'label_color': '#4B5F83'})

    # clear = setting_parser.add_argument_group('開荒模式', '未開荒地圖會在完成後停止, 已開荒的地圖會忽略此選項, 無腦開就結束了')
    # clear.add_argument('--啟用開荒', default=default('--啟用開荒'), choices=['是', '否'])
    # clear.add_argument('--開荒停止條件', default=default('--開荒停止條件'), choices=['地圖通關', '地圖三星', '地圖安海'])
    # clear.add_argument('--地圖全清星星', default=default('--地圖全清星星'), choices=['第一個', '第二個', '第三個', '不使用'], help='第幾顆星星是擊破所有敵艦')

    # ==========收成設定==========
    reward_parser = subs.add_parser('收成設定')
    reward_condition = reward_parser.add_argument_group('觸發條件', '需要執行一次來保存選項, 執行後會進入掛機收成模式', gooey_options={'label_color': '#931D03'})
    reward_condition.add_argument('--啟用收穫', default=default('--啟用收穫'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_condition.add_argument('--收成間隔', default=default('--收成間隔'), help='每隔多少分鐘觸發收成, 推薦使用時間區間, 比如"10, 40"', gooey_options={'label_color': '#4B5F83'})
    reward_condition.add_argument('--收成間隔關閉遊戲', default=default('--收成間隔關閉遊戲'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_condition.add_argument('--啟用每日收穫', default=default('--啟用每日收穫'), choices=['是', '否'], help='將每日任務困難演習作為收穫的一部份來執行', gooey_options={'label_color': '#4B5F83'})

    reward_general = reward_parser.add_argument_group('日常收穫', '', gooey_options={'label_color': '#931D03'})
    reward_general.add_argument('--啟用石油收穫', default=default('--啟用石油收穫'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_general.add_argument('--啟用物資收穫', default=default('--啟用物資收穫'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_general.add_argument('--啟用任務收穫', default=default('--啟用任務收穫'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_general.add_argument('--啟用檔案密鑰收穫', default=default('--啟用檔案密鑰收穫'), help='領取作戰檔案的檔案密鑰', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    reward_dorm = reward_parser.add_argument_group('後宅設定', '', gooey_options={'label_color': '#931D03'})
    reward_dorm.add_argument('--啟用後宅收穫', default=default('--啟用後宅收穫'), choices=['是', '否'], help='收穫好感度和家具幣', gooey_options={'label_color': '#4B5F83'})
    reward_dorm.add_argument('--啟用後宅餵食', default=default('--啟用後宅餵食'), choices=['是', '否'], help='後宅餵食', gooey_options={'label_color': '#4B5F83'})
    reward_dorm.add_argument('--後宅收穫間隔', default=default('--後宅收穫間隔'),
                             help='每隔多少分鐘觸發, 推薦使用時間區間, 比如"10, 40"', gooey_options={'label_color': '#4B5F83'})
    reward_dorm.add_argument('--後宅餵食間隔', default=default('--後宅餵食間隔'),
                             help='每隔多少分鐘觸發, 推薦使用時間區間, 比如"10, 40"\n後宅六船時, 使用六種食物分別需要間隔大於\n(14, 28, 42, 70, 139, 278)', gooey_options={'label_color': '#4B5F83'})
    reward_dorm.add_argument('--後宅餵食優先', default=default('--後宅餵食優先'), help='仿照科研過濾字符串', gooey_options={'label_color': '#4B5F83'})

    reward_commission = reward_parser.add_argument_group('委託設定', '', gooey_options={'label_color': '#931D03'})
    reward_commission.add_argument('--啟用委託收穫', default=default('--啟用委託收穫'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_commission.add_argument('--委託時間限制', default=default('--委託時間限制'), help='忽略完成時間超過限制的委託, 格式：23:30, 不需要就填0', gooey_options={'label_color': '#4B5F83'})

    priority1 = reward_commission.add_argument_group('委託耗時優先級', '', gooey_options={'label_color': '#931D03'})
    priority1.add_argument('--委託耗時小於2h', default=default('--委託耗時小於2h'), help='', gooey_options={'label_color': '#4B5F83'})
    priority1.add_argument('--委託耗時超過6h', default=default('--委託耗時超過6h'), help='', gooey_options={'label_color': '#4B5F83'})
    priority1.add_argument('--委託過期小於2h', default=default('--委託過期小於2h'), help='', gooey_options={'label_color': '#4B5F83'})
    priority1.add_argument('--委託過期大於6h', default=default('--委託過期大於6h'), help='', gooey_options={'label_color': '#4B5F83'})

    priority2 = reward_commission.add_argument_group('日常委託優先級', '', gooey_options={'label_color': '#931D03'})
    priority2.add_argument('--日常委託', default=default('--日常委託'), help='日常資源開發, 高階戰術研發', gooey_options={'label_color': '#4B5F83'})
    priority2.add_argument('--主要委託', default=default('--主要委託'), help='1200油/1000油委託', gooey_options={'label_color': '#4B5F83'})

    priority3 = reward_commission.add_argument_group('額外委託優先級', '', gooey_options={'label_color': '#931D03'})
    priority3.add_argument('--鑽頭類額外委託', default=default('--鑽頭類額外委託'), help='短距離航行訓練, 近海防衛巡邏', gooey_options={'label_color': '#4B5F83'})
    priority3.add_argument('--部件類額外委託', default=default('--部件類額外委託'), help='礦脈護衛委託, 林木護衛委託', gooey_options={'label_color': '#4B5F83'})
    priority3.add_argument('--魔方類額外委託', default=default('--魔方類額外委託'), help='艦隊高階演習, 艦隊護衛演習', gooey_options={'label_color': '#4B5F83'})
    priority3.add_argument('--石油類額外委託', default=default('--石油類額外委託'), help='小型油田開發, 大型油田開發', gooey_options={'label_color': '#4B5F83'})
    priority3.add_argument('--教材類額外委託', default=default('--教材類額外委託'), help='小型商船護衛, 大型商船護衛', gooey_options={'label_color': '#4B5F83'})

    priority4 = reward_commission.add_argument_group('緊急委託優先級', '', gooey_options={'label_color': '#931D03'})
    priority4.add_argument('--鑽頭類緊急委託', default=default('--鑽頭類緊急委託'), help='保衛運輸部隊, 殲滅敵精銳部隊', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--部件類緊急委託', default=default('--部件類緊急委託'), help='支援維拉維拉島, 支援恐班納', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--魔方類緊急委託', default=default('--魔方類緊急委託'), help='解救商船, 敵襲', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--教材類緊急委託', default=default('--教材類緊急委託'), help='支援土豪爾島, 支援萌島', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--裝備類緊急委託', default=default('--裝備類緊急委託'), help='BIW裝備運輸, NYB裝備研發', gooey_options={'label_color': '#4B5F83' })
    priority4.add_argument('--鑽石類緊急委託', default=default('--鑽石類緊急委託'), help='BIW要員護衛, NYB巡視護衛', gooey_options={'label_color': '#4B5F83'})
    priority4.add_argument('--觀艦類緊急委託', default=default('--觀艦類緊急委託'), help='小型觀艦儀式, 同盟觀艦儀式', gooey_options={'label_color': '#4B5F83'})

    reward_tactical = reward_parser.add_argument_group('戰術學院', '只支援續技能書, 不支援學新技能', gooey_options={'label_color': '#931D03'})
    reward_tactical.add_argument('--啟用戰術學院收穫', default=default('--啟用戰術學院收穫'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83' })
    # reward_tactical.add_argument('--戰術學院夜間時段', default=default('--戰術學院夜間時段'), help='格式 23:30-06:30')
    reward_tactical.add_argument('--技能書優先使用同類型', default=default('--技能書優先使用同類型'), choices=['是', '否'], help='選是, 優先使用有150%加成的\n選否, 優先使用同稀有度的技能書', gooey_options={'label_color': '#4B5F83'})
    reward_tactical.add_argument('--技能書最大稀有度', default=default('--技能書最大稀有度'), choices=['3', '2', '1'], help='最高使用T幾的技能書\nT3是金書, T2是紫書, T1是藍書\n最大值需要大於等於最小值', gooey_options={'label_color': '#4B5F83'})
    reward_tactical.add_argument('--技能書最小稀有度', default=default('--技能書最小稀有度'), choices=['3', '2', '1'], help='最低使用T幾的技能書\n', gooey_options={'label_color': '#4B5F83'})
    # reward_tactical.add_argument('--技能書夜間稀有度', default=default('--技能書夜間稀有度'), choices=['3', '2', '1'])
    # reward_tactical.add_argument('--技能書夜間優先使用同類型', default=default('--技能書夜間優先使用同類型'), choices=['是', '否'])
    reward_tactical.add_argument('--如果無技能書可用', default=default('--如果無技能書可用'), choices=['停止學習', '使用第一本'], gooey_options={'label_color': '#4B5F83'})

    reward_research = reward_parser.add_argument_group('科研項目', '科研預設選擇為自定義時, 須先閱讀 doc/filter_string_en_cn.md\n科研項目的選擇將同時滿足投入和產出設定\n正在進行科研統計，打開出擊設置-掉落記錄-啟用AzurStat並保存，將自動上傳', gooey_options={'label_color': '#931D03'})
    reward_research.add_argument('--啟用科研項目收穫', default=default('--啟用科研項目收穫'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83' })
    research_input = reward_research.add_argument_group('科研投入', '', gooey_options={'label_color': '#931D03'})
    research_input.add_argument('--科研項目使用魔方', default=default('--科研項目使用魔方'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83' })
    research_input.add_argument('--科研項目使用金幣', default=default('--科研項目使用金幣'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83' })
    research_input.add_argument('--科研項目使用部件', default=default('--科研項目使用部件'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83' })
    research_output = reward_research.add_argument_group('科研產出', '', gooey_options={'label_color': '#931D03'})
    research_output.add_argument('--科研項目選擇預設', default=default('--科研項目選擇預設'), choices=research_preset, gooey_options={'label_color': '#4B5F83'})
    research_output.add_argument('--科研過濾字符串', default=default('--科研過濾字符串'), help='僅在科研預設選擇為自定義時啟用', gooey_options={'label_color': '#4B5F83'})

    reward_meowfficer = reward_parser.add_argument_group('商店購買', '如果已經買過則自動跳過', gooey_options={'label_color': '#931D03'})
    reward_meowfficer.add_argument('--買指揮喵', default=default('--買指揮喵'), help='從0到15, 不需要就填0', gooey_options={'label_color': '#4B5F83'})
    reward_meowfficer.add_argument('--訓練指揮喵', default=default('--訓練指揮喵'), help='啟用指揮喵訓練, 每天收一隻, 週日收穫全部', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    reward_guild = reward_parser.add_argument_group('大艦隊', '檢查大艦隊後勤和大艦隊作戰', gooey_options={'label_color': '#931D03'})
    reward_guild.add_argument('--啟用大艦隊後勤', default=default('--啟用大艦隊後勤'), help='領取大艦隊任務, 提交籌備物資, 領取艦隊獎勵', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_guild.add_argument('--啟用大艦隊作戰', default=default('--啟用大艦隊作戰'), help='執行大艦隊作戰派遣, 打大艦隊BOSS', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_guild.add_argument('--大艦隊作戰參加閾值', default=default('--大艦隊作戰參加閾值'), help='從0到1. 比如\'0.5\' 表示只在作戰進度 未達到一半時加入, \'1\'表示 不管進度直接加入', gooey_options={'label_color': '#4B5F83'})
    reward_guild.add_argument('--大艦隊收穫間隔', default=default('--大艦隊收穫間隔'), help='每隔多少分鐘觸發, 推薦使用時間區間, 比如"10, 40"', gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_items = reward_guild.add_argument_group('籌備物品提交順序', '可用字符: t1, t2, t3, oxycola, coolant, coins, oil, and merit. 省略某個字符來跳過該物品的提交', gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_items.add_argument('--物品提交順序', default=default('--物品提交順序'), gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_plates = reward_guild.add_argument_group('籌備部件提交順序', '可用字符: torpedo, antiair, plane, gun, and general. 省略某個字符來跳過該物品的提交', gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_plates.add_argument('--部件提交順序T1', default=default('--部件提交順序T1'), gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_plates.add_argument('--部件提交順序T2', default=default('--部件提交順序T2'), gooey_options={'label_color': '#4B5F83'})
    reward_guild_logistics_plates.add_argument('--部件提交順序T3', default=default('--部件提交順序T3'), gooey_options={'label_color': '#4B5F83'})
    reward_guild_operations_boss = reward_guild.add_argument_group('Operations guild raid boss input', '', gooey_options={'label_color': '#4B5F83'})
    reward_guild_operations_boss.add_argument('--啟用大艦隊BOSS出擊', default=default('--啟用大艦隊BOSS出擊'), help='自動打大艦隊BOSS, 需要預先在遊戲內設置隊伍', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    reward_guild_operations_boss.add_argument('--啟用大艦隊BOSS隊伍推薦', default=default('--啟用大艦隊BOSS隊伍推薦'), help='使用遊戲自動推薦的隊伍打BOSS', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    # ==========設備設定==========
    emulator_parser = subs.add_parser('設備設定')
    emulator = emulator_parser.add_argument_group('模擬器', '需要運行一次來保存選項, 會檢查遊戲是否啟動\n若啟動了遊戲, 觸發一次收菜', gooey_options={'label_color': '#931D03'})
    emulator.add_argument('--設備', default=default('--設備'), help='例如 127.0.0.1:62001', gooey_options={'label_color': '#4B5F83'})
    emulator.add_argument('--包名', default=default('--包名'), help='', gooey_options={'label_color': '#4B5F83'})
    emulator.add_argument(
        '默認serial列表',
        default=message,
        widget='Textarea',
        help="以下是一些常見模擬器的默認serial\n如果你使用了模擬器多開, 它們將不使用默認的serial",
        gooey_options={
            'height': 150,
            'show_help': True,
            'show_label': True,
            'readonly': True,
            'label_color': '#4B5F83'
        }
    )

    debug = emulator_parser.add_argument_group('調試設定', '', gooey_options={'label_color': '#931D03'})
    debug.add_argument('--出錯時保存log和截圖', default=default('--出錯時保存log和截圖'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    debug.add_argument('--保存透視識別出錯的圖像', default=default('--保存透視識別出錯的圖像'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    adb = emulator_parser.add_argument_group('ADB設定', '', gooey_options={'label_color': '#931D03'})
    adb.add_argument('--設備截圖方案', default=default('--設備截圖方案'), choices=['aScreenCap', 'uiautomator2', 'ADB'], help='速度: aScreenCap >> uiautomator2 > ADB', gooey_options={'label_color': '#4B5F83'})
    adb.add_argument('--設備控制方案', default=default('--設備控制方案'), choices=['minitouch','uiautomator2', 'ADB'], help='速度: minitouch >> uiautomator2 >> ADB', gooey_options={'label_color': '#4B5F83'})
    adb.add_argument('--戰鬥中截圖間隔', default=default('--戰鬥中截圖間隔'), help='戰鬥中放慢截圖速度, 降低CPU使用', gooey_options={'label_color': '#4B5F83'})

    update = emulator_parser.add_argument_group('更新檢查', '', gooey_options={'label_color': '#931D03'})
    update.add_argument('--啟用更新檢查', default=default('--啟用更新檢查'), choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    update.add_argument('--更新檢查方法', default=default('--更新檢查方法'), choices=['api', 'web'], help='使用api時建議填寫tokens, 使用web則不需要', gooey_options={'label_color': '#4B5F83'})
    update.add_argument('--github_token', default=default('--github_token'), help='Github API限制為每小時60次, 獲取tokens https://github.com/settings/tokens', gooey_options= {'label_color': '#4B5F83'})
    update.add_argument('--更新檢查代理', default=default('--更新檢查代理'), help='本地http或socks代理, 如果github很慢, 請使用代理, example: http://127.0 .0.1:10809', gooey_options={'label_color': '#4B5F83'})

    # ==========每日任務==========
    daily_parser = subs.add_parser('每日任務困難演習')

    # 選擇每日
    daily = daily_parser.add_argument_group('選擇每日', '每日任務, 演習, 困難圖', gooey_options={'label_color': '#931D03'})
    daily.add_argument('--打每日', default=default('--打每日'), help='若當天有記錄, 則跳過', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--打困難', default=default('--打困難'), help='若當天有記錄, 則跳過', choices=['是', '否'], gooey_options= {'label_color': '#4B5F83'})
    daily.add_argument('--打演習', default=default('--打演習'), help='若在刷新後有記錄, 則跳過', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--打共鬥每日15次', default=default('--打共鬥每日15次'), help='若當天有記錄, 則跳過', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--打活動圖每日三倍PT', default=default('--打活動圖每日三倍PT'), help='若當天有記錄, 則跳過', choices= ['是', '否'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--打活動每日SP圖', default=default('--打活動每日SP圖'), help='若當天有記錄, 則跳過', choices=['是' , '否'], gooey_options={'label_color': '#4B5F83'})
    daily.add_argument('--打大世界餘燼信標支援', default=default('--打大世界餘燼信標支援'), help='若當天有記錄, 則跳過', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    # 每日設定
    daily_task = daily_parser.add_argument_group('每日設定', '', gooey_options={'label_color': '#931D03'})
    daily_task.add_argument('--使用每日掃蕩', default=default('--使用每日掃蕩'), help='每日掃蕩可用時使用掃蕩', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--戰術研修', default=default('--戰術研修'), choices=['航空', '砲擊', '雷擊'], gooey_options={'label_color': '#4B5F83' })
    daily_task.add_argument('--斬首行動', default=default('--斬首行動'), choices=['第一個', '第二個', '第三個'], gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--破交作戰', default=default('--破交作戰'), choices=['第一個', '第二個', '第三個'], help='需要解鎖掃蕩, 未解鎖時跳過', gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--商船護航', default=default('--商船護航'), choices=['第一個', '第二個', '第三個'], gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--海域突進', default=default('--海域突進'), choices=['第一個', '第二個', '第三個'], gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--每日艦隊', default=default('--每日艦隊'), help='如果使用同一隊, 填艦隊編號, 例如5\n如果使用不同隊, 用半形逗號分割, 順序為商船護送, 海域突進, 斬首行動, 戰術研修\n例如5, 5, 5, 6', gooey_options={'label_color': '#4B5F83'})
    daily_task.add_argument('--每日艦隊快速換裝', default=default('--每日艦隊快速換裝'), help='打之前換裝備, 打完後卸裝備, 不需要就填0 \n半形逗號分割, 例如3, 1, 0, 1, 1, 0', gooey_options={'label_color': '#4B5F83'})

    # 困難設定
    hard = daily_parser.add_argument_group('困難設定', '需要地圖達到週回模式', gooey_options={'label_color': '#931D03'})
    hard.add_argument('--困難地圖', default=default('--困難地圖'), help='比如 10-4', gooey_options={'label_color': '#4B5F83'})
    hard.add_argument('--困難艦隊', default=default('--困難艦隊'), choices=['1', '2'], gooey_options={'label_color': '#4B5F83'})
    hard.add_argument('--困難艦隊快速換裝', default=default('--困難艦隊快速換裝'), help='打之前換裝備, 打完後卸裝備, 不需要就填0\n半形逗號分割, 例如3, 1, 0, 1, 1, 0', gooey_options={'label_color': '#4B5F83'})


    # 演習設定
    exercise = daily_parser.add_argument_group('演習設定', '', gooey_options={'label_color': '#931D03'})
    exercise.add_argument('--演習對手選擇', default=default('--演習對手選擇'), choices=['經驗最多', '最簡單', '最左边', '先最簡單再經驗最多'], help= '', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--演習次數保留', default=default('--演習次數保留'), help='例如 1, 表示打到1/10停止', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--演習嘗試次數', default=default('--演習嘗試次數'), help='每個對手的嘗試次數, 打不過就換', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--演習SL閾值', default=default('--演習SL閾值'), help='HP<閾值時撤退', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--演習低血量確認時長', default=default('--演習低血量確認時長'), help='HP低於閾值後, 過一定時長才會撤退\n推薦1.0 ~ 3.0', gooey_options={'label_color': '#4B5F83'})
    exercise.add_argument('--演習快速換裝', default=default('--演習快速換裝'), help='打之前換裝備, 打完後卸裝備, 不需要就填0\n半形逗號分割, 例如3, 1, 0, 1, 1, 0', gooey_options={'label_color': '#4B5F83'})

    # 每日活動圖三倍PT
    event_bonus = daily_parser.add_argument_group('活動設定', '', gooey_options={'label_color': '#931D03'})
    event_bonus.add_argument('--活動獎勵章節', default=default('--活動獎勵章節'), choices=['AB圖', 'ABCD圖', 'T圖', 'HT圖'], help ='有額外PT獎勵章節', gooey_options={'label_color': '#4B5F83'})
    event_bonus.add_argument('--活動SP圖道中隊', default=default('--活動SP圖道中隊'), choices=['1', '2'], help='', gooey_options={'label_color': '#4B5F83'})
    event_bonus.add_argument('--活動名稱ab', default=event_latest, choices=event_folder, help='例如 event_20200326_cn', gooey_options={'label_color': '#4B5F83'})

    # 共鬥每日設定
    raid_bonus = daily_parser.add_argument_group('共鬥設定', '', gooey_options={'label_color': '#931D03'})
    raid_bonus.add_argument('--共鬥每日名稱', default=raid_latest, choices=raid_folder, help='', gooey_options={'label_color': '#4B5F83'})
    raid_bonus.add_argument('--共鬥困難', default=default('--共鬥困難'), choices=['是', '否'], help='', gooey_options={'label_color': '#4B5F83'})
    raid_bonus.add_argument('--共鬥普通', default=default('--共鬥普通'), choices=['是', '否'], help='', gooey_options={'label_color': '#4B5F83'})
    raid_bonus.add_argument('--共鬥簡單', default=default('--共鬥簡單'), choices=['是', '否'], help='', gooey_options={'label_color': '#4B5F83'})

    # 大世界每日設置
    raid_bonus = daily_parser.add_argument_group('大世界設置', '', gooey_options={'label_color': '#931D03'})
    raid_bonus.add_argument('--大世界信標支援強度', default=default('--大世界信標支援強度'), help='尋找大於等於此強度的信標', gooey_options={'label_color': '#4B5F83'})

    # # ==========每日活動圖三倍PT==========
    # event_ab_parser = subs.add_parser('每日活動圖三倍PT')
    # event_name = event_ab_parser.add_argument_group('選擇活動', '')
    # event_name.add_argument('--活動名稱ab', default=event_latest, choices=event_folder, help='例如 event_20200326_cn')

    # ==========主線圖==========
    main_parser = subs.add_parser('主線圖')
    # 選擇關卡
    stage = main_parser.add_argument_group('選擇關卡', '', gooey_options={'label_color': '#931D03'})
    stage.add_argument('--主線地圖出擊', default=default('--主線地圖出擊'), help='例如 7-2', gooey_options={'label_color': '#4B5F83'})
    stage.add_argument('--主線地圖模式', default=default('--主線地圖模式'), help='僅困難圖開荒時使用, 週回模式後請使用每日困難', choices=['普通', '困難'], gooey_options={'label_color': '#4B5F83'})

    # ==========活動圖==========
    event_parser = subs.add_parser('活動圖')

    description = """
    出擊未優化關卡或地圖未達到安全海域時, 使用開荒模式運行(較慢)
    """
    event = event_parser.add_argument_group(
        '選擇關卡', '\n'.join([line.strip() for line in description.strip().split('\n')]), gooey_options={'label_color': '#931D03'})
    event.add_argument('--活動地圖', default=default('--活動地圖'), help='輸入地圖名稱, 不分大小寫, 例如D3, SP3, HT6', gooey_options={'label_color': '#4B5F83'})
    event.add_argument('--活動名稱', default=event_latest, choices=event_folder, help='例如 event_20200312_cn', gooey_options={'label_color': '#4B5F83'})

    # ==========潛艇圖==========
    sos_parser = subs.add_parser('潛艇圖')
    sos = sos_parser.add_argument_group(
        '潛艇圖設定', '設定每張潛艇圖的隊伍, 順序: 一隊二隊潛艇隊\n例如"4, 6", "4, 0", "4, 6, 1"\n填0跳過不打', gooey_options={'label_color': '#931D03'})
    sos.add_argument('--第3章潛艇圖隊伍', default=default('--第3章潛艇圖隊伍'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--第4章潛艇圖隊伍', default=default('--第4章潛艇圖隊伍'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--第5章潛艇圖隊伍', default=default('--第5章潛艇圖隊伍'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--第6章潛艇圖隊伍', default=default('--第6章潛艇圖隊伍'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--第7章潛艇圖隊伍', default=default('--第7章潛艇圖隊伍'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--第8章潛艇圖隊伍', default=default('--第8章潛艇圖隊伍'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--第9章潛艇圖隊伍', default=default('--第9章潛艇圖隊伍'), gooey_options={'label_color': '#4B5F83'})
    sos.add_argument('--第10章潛艇圖隊伍', default=default('--第10章潛艇圖隊伍'), gooey_options={'label_color': '#4B5F83'})

    # ==========作戰檔案==========
    war_archives_parser = subs.add_parser('作戰檔案')
    war_archives = war_archives_parser.add_argument_group(
        '作戰檔案設置', '輸入地圖名稱, 然後選擇對應的活動', gooey_options={'label_color': '#931D03'})
    war_archives.add_argument('--作戰檔案地圖', default=default('--作戰檔案地圖'), help='輸入地圖名稱, 不分大小寫, 例如D3, SP3, HT6', gooey_options={'label_color': '#4B5F83'})
    war_archives.add_argument('--作戰檔案活動', default=default('--作戰檔案活動'), choices=archives_folder, help='在下拉菜單中選擇活動', gooey_options={'label_color': '#4B5F83'})

    # ==========共鬥活動==========
    raid_parser = subs.add_parser('共鬥活動')
    raid = raid_parser.add_argument_group('選擇共鬥', '', gooey_options={'label_color': '#931D03'})
    raid.add_argument('--共鬥名稱', default=raid_latest, choices=raid_folder, help='', gooey_options={'label_color': '#4B5F83'})
    raid.add_argument('--共鬥難度', default=default('--共鬥難度'), choices=['困難', '普通', '簡單'], help='', gooey_options={'label_color': '#4B5F83'})
    raid.add_argument('--共鬥使用挑戰券', default=default('--共鬥使用挑戰券'), choices=['是', '否'], help='', gooey_options={'label_color': '#4B5F83'})

    # ==========半自動==========
    semi_parser = subs.add_parser('半自動輔助點擊')
    semi = semi_parser.add_argument_group('半自動模式', '手動選敵, 自動結算, 用於出擊未適配的圖', gooey_options={'label_color': '#931D03'})
    semi.add_argument('--進圖準備', default=default('--進圖準備'), help='', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})
    semi.add_argument('--跳過劇情', default=default('--跳過劇情'), help='注意, 這會自動確認所有提示框, 包括紅臉出擊', choices=['是', '否'], gooey_options={'label_color': '#4B5F83'})

    # ==========1-1Affinity farming==========
    c_1_1_parser = subs.add_parser('1-1伏擊刷好感')
    c_1_1 = c_1_1_parser.add_argument_group('1-1伏擊刷好感', '會自動關閉週回模式\n有MVP, 8場戰鬥漲1點好感, 無MVP, 16場戰鬥漲1點好感', gooey_options={'label_color': '#931D03'})
    c_1_1.add_argument('--刷好感戰斗場數', default=default('--刷好感戰斗場數'), help='例如: 32', gooey_options={'label_color': '#4B5F83'})

    # ==========7-2三戰撿垃圾==========
    c_7_2_parser = subs.add_parser('7-2三戰撿垃圾')
    c_7_2 = c_7_2_parser.add_argument_group('7-2三戰撿垃圾', '', gooey_options={'label_color': '#931D03'})
    c_7_2.add_argument('--BOSS隊踩A3', default=default('--BOSS隊踩A3'), choices=['是', '否'], help='A3有敵人就G3, C3, E3', gooey_options={'label_color': '#4B5F83'})

    # ==========12-2打中型練級==========
    c_12_2_parser = subs.add_parser('12-2打中型練級')
    c_12_2 = c_12_2_parser.add_argument_group('12-2索敵設定', '', gooey_options={'label_color': '#931D03'})
    c_12_2.add_argument('--大型敵人忍耐', default=default('--大型敵人忍耐'), choices=['0', '1', '2', '10'], help='最多打多少戰大型敵人, 不挑敵人選10', gooey_options={'label_color': '#4B5F83'})

    # ==========12-4打大型練級==========
    c_12_4_parser = subs.add_parser('12-4打大型練級')
    c_12_4 = c_12_4_parser.add_argument_group('12-4索敵設定', '需保證隊伍有一定強度', gooey_options={'label_color': '#931D03'})
    c_12_4.add_argument('--非大型敵人進圖忍耐', default=default('--非大型敵人進圖忍耐'), choices=['0', '1', '2'], help='忍受進場多少戰沒有大型', gooey_options={'label_color': '#4B5F83'})
    c_12_4.add_argument('--非大型敵人撤退忍耐', default=default('--非大型敵人撤退忍耐'), choices=['0', '1', '2', '10'], help ='沒有大型之後還會打多少戰, 不挑敵人選10', gooey_options={'label_color': '#4B5F83'})
    c_12_4.add_argument('--撿彈藥124', default=default('--撿彈藥124'), choices=['2', '3', '4', '5'], help='多少戰後撿彈藥', gooey_options={'label_color': '#4B5F83'})

    # ==========OS semi auto==========
    os_semi_parser = subs.add_parser('大世界輔助點擊')
    os_semi = os_semi_parser.add_argument_group('大世界輔助點擊', '自動點擊戰鬥準備和戰鬥結算\n僅推薦在普通海域和安全海域中開啟', gooey_options={'label_color': '#931D03'})
    os_semi.add_argument('--大世界跳過劇情', default=default('--大世界跳過劇情'), choices=['是', '否'], help='注意, 這會自動點擊地圖交互的選項', gooey_options={'label_color': '#4B5F83'})

    # ==========OS clear map==========
    # os_semi_parser = subs.add_parser('大世界地圖全清')
    # os_semi = os_semi_parser.add_argument_group('大世界地圖全清', '僅在安全海域中使用, 在普通海域使用時需要先執行空域搜索\n使用方法: 先手動進入地圖, 再運行\n運行結束後, 最好手動檢查是否有遺漏', gooey_options={'label_color': '#931D03'})
    # os_semi.add_argument('--打大世界餘燼信標', default=default('--打大世界餘燼信標'), choices=['是', '否'], help='信標數據滿了之後, 打飛龍', gooey_options={'label_color': '#4B5F83'})

    # ==========OS clear world==========
    os_world_parser = subs.add_parser('大世界每月全清')
    os_world = os_world_parser.add_argument_group('大世界每月全清',
                                                  '在運行之前, 必須通關大世界主線, 購買並使用戰役信息記錄儀 (5000油道具)\n'
                                                  '這個模塊將從低侵蝕到高侵蝕地清理海域\n'
                                                  '請確保你的艦隊和適應性足夠對付高侵蝕海域',
                                                  gooey_options={'label_color': '#931D03'})
    os_world.add_argument('--大世界全清侵蝕下限', default=default('--大世界全清侵蝕下限'), help='上限和下限一樣時, 只清理特定侵蝕等級', choices=['1', '2', '3', '4', '5', '6'], gooey_options={'label_color': '#4B5F83'})
    os_world.add_argument('--大世界全清侵蝕上限', default=default('--大世界全清侵蝕上限'), help='', choices=['1', '2', '3', '4', '5', '6'], gooey_options={'label_color': '#4B5F83'})

    # ==========OS fully auto==========
    os_parser = subs.add_parser('大世界全自動')
    os = os_parser.add_argument_group('大世界全自動', '運行順序: 接每日買補給 > 做每日 > 打隱秘海域 > 短貓相接\n港口補給是有限池, 總量恆定隨機出現, 想要買好東西需要全買\n商店優先級格式: ActionPoint > PurpleCoins > TuringSample > RepairPack', gooey_options={'label_color': '#931D03'})
    os.add_argument('--在每日中完成大世界', default=default('--在每日中完成大世界'), choices=['是', '否'], help='將大世界全自動作為每日的一部分來完成', gooey_options={'label_color': '#4B5F83'})

    os_daily = os.add_argument_group('大世界每日', '', gooey_options={'label_color': '#931D03'})
    os_daily.add_argument('--大世界接每日任務', default=default('--大世界接每日任務'), choices=['是', '否'], help='在港口領取每日任務', gooey_options={'label_color': '#4B5F83'})
    os_daily.add_argument('--大世界完成每日', default=default('--大世界完成每日'), choices=['是', '否'], help='前往每日的海域, 並清理', gooey_options={'label_color': '#4B5F83'})
    os_daily.add_argument('--大世界港口補給', default=default('--大世界港口補給'), choices=['是', '否'], help='買光所有的港口補給', gooey_options={'label_color': '#4B5F83'})
    os_daily.add_argument('--打大世界餘燼信標', default=default('--打大世界餘燼信標'), choices=['是', '否'], help='信標數據滿了之後, 打飛龍', gooey_options={'label_color': '#4B5F83'})

    os_farm = os.add_argument_group('打大世界', '', gooey_options={'label_color': '#931D03'})
    os_farm.add_argument('--打大世界隱秘海域', default=default('--打大世界隱秘海域'), choices=['是', '否'], help='[開發中]清理所有隱秘海域', gooey_options={'label_color': '#4B5F83'})
    os_farm.add_argument('--大世界短貓相接', default=default('--大世界短貓相接'), choices=['是', '否'], help='反复打圖揀貓點', gooey_options={'label_color': '#4B5F83'})
    os_farm.add_argument('--短貓相接侵蝕等級', default=default('--短貓相接侵蝕等級'), choices=['1', '2', '3', '4', '5', '6'], help='侵蝕3和5有更高的貓點/行動力比, 建議選侵蝕5', gooey_options={'label_color': '#4B5F83'})

    os_setting = os.add_argument_group('大世界設置', '', gooey_options={'label_color': '#931D03'})
    os_setting.add_argument('--大世界買行動力', default=default('--大世界買行動力'), choices=['是', '否'], help='用石油買行動力, 先買再開箱子', gooey_options={'label_color': '#4B5F83'})
    os_setting.add_argument('--大世界行動力保留', default=default('--大世界行動力保留'), help='低於此值後停止, 含行動力箱子', gooey_options={'label_color': '#4B5F83'})
    os_setting.add_argument('--大世界修船閾值', default=default('--大世界修船閾值'), help='任意一艘船血量低於此值時, 前往最近港口修理. 從0到1.', gooey_options={'label_color': '#4B5F83'})

    os_shop = os.add_argument_group('大世界商店', '', gooey_options={'label_color': '#931D03'})
    os_shop.add_argument('--明石商店購買', default=default('--明石商店購買'), choices=['是', '否'], help='', gooey_options={'label_color': '#4B5F83'})
    os_shop.add_argument('--明石商店優先級', default=default('--明石商店優先級'), help='', gooey_options={'label_color': '#4B5F83'})

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
