import pandas as pd
import json
import os
from dotenv import load_dotenv

from apis.alpaca.infos import get_infos, get_current_positions

load_dotenv(verbose=True)

PATH_MARKET_DATA = os.getenv('PATH_MARKET_DATA')
PATH_SETTING_DATA = os.getenv('PATH_SETTING_DATA')
PATH_DEFAULT_SETTING = os.getenv('PATH_DEFAULT_SETTING')

class Equity_Manual_v2():
    '''
    Equity class has its own history and properties for deciding to open or close positions of a specific stock.

    ### parameters
        * symbol: (ticker) alphabet abbreviation for a specific stock
        * settings:
            * threshold: minimum percentage of value change to decide buy or sell
            * duration: minimum duration of consistency of value change to decide buy or sell
            * thr_grad: minimum average of gradient to decide buy or sell
            * rebound: gradient of change as a trigger of action
            * limit: maximum amount of total value per action
            * target_value: target value to decide to enhance or diminish the order amount
    '''
    def __init__(
        self,
        symbol: str,
    ) -> None:
        self.symbol = symbol
        self.data = None
        self.start_point = 0

        # loading setting values
        self.settings = None
        if os.path.isfile(PATH_SETTING_DATA + self.symbol + '_settings.json'):
            with open(PATH_SETTING_DATA + self.symbol + '_settings.json', 'r') as fp:
                self.settings = json.load(fp)
        else:
            print(f'[Warning] {self.symbol} has no setting files. The default settings will be used instead.')
            with open(PATH_DEFAULT_SETTING, 'r') as fp:
                self.settings = json.load(fp)['default']
            self.set()

        self.timeframe = self.settings['data_interval']
        self.data_path = PATH_MARKET_DATA + self.symbol + '_' + self.timeframe + '.csv'

        # loading historical data values
        self.load_data() # Initialize self.data

        self.value_diff = self.settings['target_value']
        self.current_position = 0
        self.account_info = {}

    def __repr__(self) -> str:
        return 'ASSET variable {' + f'symbol: {self.symbol}, settings: {self.settings}' + '}'

    def check_data(self) -> bool: # must required method
        '''
        갱신된 실시간 데이터가 있는지 확인하고, 있다면 업데이트
        Check if there is new data, and then update
        '''

        if os.path.isfile(self.data_path):
            if self.data is not None:
                temp_data_pd = pd.read_csv(self.data_path)
                if temp_data_pd['t'].iloc[-1] == self.data['t'].iloc[-1]:
                    return False
                else:
                    self.data = temp_data_pd
                    return True
            else:
                self.data = pd.read_csv(self.data_path)

        return False

    def load_data(self) -> None:
        if os.path.isfile(self.data_path):
            self.data = pd.read_csv(self.data_path)
        else:
            self.data = None
            print(f'[Warning] {self.symbol} has no data available.')

        self.start_point = 0

    def set(self, **args) -> None: # must required method
        '''
        Apply and save new setting values
        '''

        for key, val in args.items():
            if key in self.settings:
                self.settings[key] = val

        with open(PATH_SETTING_DATA + self.symbol + '_settings.json', 'w', encoding='utf-8') as fp:
            json.dump(self.settings, fp, indent='\t', ensure_ascii=False)

    def update_before_order(self):
        # update asset states
        self._update_asset_states()

        # update account states
        # self._update_account_states() # only for real trading

    def _update_asset_states(self) -> None:
        # all_positions = get_current_positions(symbols=[self.symbol]) # only for real trading
        # self.current_position = all_positions[self.symbol]['qty'] if self.symbol in all_positions else 0 # only for real trading
        currentPrice = self.data['o'].iloc[-1]
        currentValue = self.current_position * currentPrice
        self.value_diff = self.settings['target_value'] - currentValue

    def _update_account_states(self) -> None:
        infos = get_infos()
        self.account_info['buying_power'] = float(infos['buying_power'])
