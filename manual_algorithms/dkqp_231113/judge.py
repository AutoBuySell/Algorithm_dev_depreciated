import numpy as np
import traceback

from .assets import Equity_Manual_v2

def getNewPosition_Manual_v2(asset: Equity_Manual_v2, test_end_point: int = 0) -> tuple[bool | float]:
    '''
    asset: asset object
    test_end_point: set to 0 for real-time judging, or set as a number larger than 0 for testing
    '''

    try:
        data_np = np.array(asset.data['o'])

        # For testing, use sliced data
        if test_end_point != 0:
            data_np = data_np[:test_end_point + 1]

        # The last point is the moment of judging
        current_price = data_np[-1]

        # For judging, use sliced data referred to start_point and duration
        data_np = data_np[max(-(len(data_np) - asset.start_point), -(1 + asset.settings['duration'])):-1]

        min_price = np.min(data_np)
        max_price = np.max(data_np)

        # For buying points: only when satisfying both above specific price and tending to decreased
        thr_buy_sig_on = (1 - asset.settings['thr_buy']) * max_price >= current_price
        reb_buy_sig_on = (1 + asset.settings['rebound']) * data_np[-1] <= current_price

        # For selling points
        thr_sell_sig_on = (1 + asset.settings['thr_sell']) * min_price <= current_price
        reb_sell_sig_on = (1 - asset.settings['rebound']) * data_np[-1] >= current_price

        buy_flag = thr_buy_sig_on and reb_buy_sig_on
        sell_flag = thr_sell_sig_on and reb_sell_sig_on

        # If a buying or selling point has been appeared, renew start_point
        if buy_flag or sell_flag:
            asset.start_point = len(asset.data['o']) - 2 if test_end_point == 0 else test_end_point

        # If a buying or selling point has been appeared, calculate confidence
        confidence = 0
        if buy_flag:
            confidence = pow(2, (1 - current_price / max_price) / asset.settings['thr_buy'] - 2)

        if sell_flag:
            confidence = pow(2, (current_price / min_price - 1) / asset.settings['thr_sell'] - 2)

        confidence = max(confidence, 0.5)
        confidence = min(confidence, 2)

        return buy_flag, sell_flag, confidence

    except:
        print(traceback.format_exc())