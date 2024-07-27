import traceback

from .assets import Equity_Manual_v2

def makeOrders_Manual_v2(asset: Equity_Manual_v2, side: str, confidence: float) -> tuple:
    '''
    orders: (list of symbols to order, list of 'buy' or 'sell' orders per asset)
    obj_assets: dict of asset objects
    '''

    try:
        is_order = False
        qty = 0

        asset.update_before_order()

        target_value = asset.settings['target_value']
        value_diff = asset.value_diff
        buying_power = asset.account_info['buying_power']
        current_position = asset.current_position
        current_price = asset.data['o'].iloc[-1]

        if side == 'sell' and current_position > 0:
            amount = pow(2, - value_diff / target_value) * confidence * (target_value / 5)
            qty = min(amount // current_price, current_position)
            is_order = True

        elif side == 'buy':
            amount = pow(2, value_diff / target_value) * confidence * (target_value / 5)
            amount = min(amount, buying_power)
            qty = amount // current_price
            is_order = True

        return is_order, qty

    except:
        print(traceback.format_exc())
