import os
import pandas as pd
import re


SHIP_RETIRE_COINS = {
    'dd': 12,   # 驱逐
    'cl': 14,   # 轻巡
    'ca': 18,   # 重巡
    'cb': 19,   # 超巡
    'bc': 22,   # 战巡
    'bb': 26,   # 战列
    'cvl': 16,  # 轻航
    'cv': 24,   # 正航
    'bm': 13,   # 重炮
    'ar': 13,   # 维修
    "ss": 24,   # 潜艇
}

class CoinStatistics:
    DROP_FOLDER = './screenshots'
    CSV_FILE = 'drop_result.csv'
    MAP_BATTLE_COUNT = 6
    OIL_PER_BATTTLE = 3
    HAS_ENTER_OIL = True
    SHIP_EQUIP_COINS = [
        8, 8, 8, 4,
        8, 5, 5, 4, 
        4, 4, 8, 4,
        2, 5, 5, 2,
        1, 1, 5, 8,
        6, 6,
    ]
    SHIP_REGEX = '|'.join(SHIP_RETIRE_COINS.keys())

    @property
    def csv_file(self):
        return os.path.join(CoinStatistics.DROP_FOLDER, CoinStatistics.CSV_FILE)

    def _read_csv(self):
        column_name = ['timestamp', 'campaign', 'enemy_name', 'drop_type', 'item', 'amount']
        return pd.read_csv(self.csv_file, header=None, names=column_name)

    def get_total_profits(self):
        data = self._read_csv()

        coins = data.loc[data['item'] == 'Coin', 'amount'].sum()

        ship_rows = data[data['item'].str.contains('ship')].copy()
        ship_rows[['ship_info', 'ship_type', 'ship_name']] = ship_rows['item'].str.extract(
            r'ship(({})(\d+))'.format(self.SHIP_REGEX))

        # sort by key of SHIP_RETIRE_COINS
        def sort_key(s):
            ship_type, amount = re.match(r'({})(\d+)'.format(self.SHIP_REGEX), s).groups()
            return (
                list(SHIP_RETIRE_COINS.keys()).index(ship_type),
                int(amount)
            )
        ship_names = sorted(ship_rows['ship_info'].unique(), key=sort_key)
        ship_equip_coins = dict(zip(ship_names, self.SHIP_EQUIP_COINS))
        # print(ship_equip_coins)

        ship_rows['profit'] = (ship_rows['ship_type'].map(SHIP_RETIRE_COINS) + \
            ship_rows['ship_info'].map(ship_equip_coins)) * ship_rows['amount']
        ship_profit = ship_rows.groupby('ship_type')['profit'].sum().sum()

        total_profit = coins + ship_profit
        play_times = data['timestamp'].nunique()
        oil_cost = play_times * (10 * self.HAS_ENTER_OIL + self.OIL_PER_BATTTLE * self.MAP_BATTLE_COUNT)
        print(f'Total Coins: {total_profit}')
        print(f'Coins / Oil: {total_profit / oil_cost}')
        print(f'=========={self.OIL_PER_BATTTLE}油T3==========')
        print('*含退役舰船及拆解自带装备的物资')
        print(f'统计局数: {play_times}')
        print(f'总物资: {total_profit}')
        print(f'物资比: {total_profit / oil_cost}')

if __name__ == '__main__':
    # Drop screenshot folder. Default to './screenshots'
    CoinStatistics.DROP_FOLDER = './screenshots'
    # Name of the input csv file.
    # This will read from {DROP_FOLDER}/{CSV_FILE}.
    CoinStatistics.CSV_FILE = 'drop_results.csv'
    # Total battle count of this map
    CoinStatistics.MAP_BATTLE_COUNT = 6
    # Oil used for each battle
    CoinStatistics.OIL_PER_BATTTLE = 3
    # If has 10 oil for entering map
    CoinStatistics.HAS_ENTER_OIL = True

    stat = CoinStatistics()

    """
    Step 1:
        Set CoinStatistics.SHIP_EQUIP_COINS by the order of SHIP_RETIRE_COINS first.
        Run these code.
    """
    stat.get_total_profits()
