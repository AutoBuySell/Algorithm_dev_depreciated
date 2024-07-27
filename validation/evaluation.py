from manual_algorithms.dkqp_231113.assets import Equity_Manual_v2 as ASSETCLASS
from manual_algorithms.dkqp_231113.judge import getNewPosition_Manual_v2 as JUDGEFUNC
from manual_algorithms.dkqp_231113.order import makeOrders_Manual_v2 as ORDERFUNC

from apis.data import req_data_historical

from validation.visualization import visualize_points

# SYMBOLS_FOR_EVALUATION = ['TSLA', 'AAPL', 'META', 'NVDA', 'NFLX', 'ROKU', 'NKLA']
SYMBOLS_FOR_EVALUATION = ['TSLA', 'MSFT', 'META', 'NVDA', 'AMD', 'AMZN', 'AAPL', 'LLY', 'ZG', 'PYPL']

def trading_point_evaluation(startDate: str, endDate: str):
  '''
  매수/매도 포인트 시각화
  visualize buying/selling points

  모델 예측 포인트, 지정 포인트, 매칭 포인트 리턴
  return: A dict of keys of symbols and values of (total_predicted_points, total_selected_points, matched_points).
  predicted_points: points predicted by the model
  selected_points: points selected by human
  '''

  results = {}

  checked_selected_points = {}
  predicted_points = {}

  for symbol in SYMBOLS_FOR_EVALUATION:
    asset = ASSETCLASS(symbol)

    req_data_historical(
      symbol=symbol,
      timeframe=asset.timeframe,
      startDate=startDate,
      endDate=endDate
    )

    checked_selected_points[symbol] = set([])
    predicted_points[symbol] = []

    data = asset.data[asset.data['t'] >= startDate][asset.data['t'] <= endDate]['o']

    judges = asset.data['judge']
    for i in data.index:
      buySig, sellSig, confidence = JUDGEFUNC(asset, i)
      if buySig:
        for j in range(i - 2, i + 3):
          if j not in checked_selected_points[symbol] and judges[j] == 1:
            checked_selected_points[symbol].add(j)
            break
        predicted_points[symbol].append(('buy', i, data[i]))
      elif sellSig:
        for j in range(i - 2, i + 3):
          if j not in checked_selected_points[symbol] and judges[j] == -1:
            checked_selected_points[symbol].add(j)
            break
        predicted_points[symbol].append(('sell', i, data[i]))

    results[symbol] = (
      len(predicted_points[symbol]),
      len(judges[judges != 0]),
      len(checked_selected_points[symbol])
    )

    visualize_points(asset, predicted_points[symbol])

  return results

def trading_margin_evaluation(symbol: str, startDate: str, endDate: str, initial_buying_power: float):
  '''
  매수/매도 포인트 시각화
  visualize buying/selling points

  종목별 예상 수익 반환 (최종 데이터 시점)
  return: A dict of keys of symbols and values of (estimated margins, current_buying_power, current_position_value)
  '''

  predicted_points = []
  estimated_margins = {
    'symbol': symbol,
    'startDate': startDate,
    'endDate': endDate
  }

  asset = ASSETCLASS(symbol)

  req_data_historical(
      symbol=symbol,
      timeframe=asset.timeframe,
      startDate=startDate,
      endDate=endDate
    )

  asset.check_data()

  asset.account_info['buying_power'] = initial_buying_power

  estimated_margins['margin'] = (asset.account_info['buying_power'], 0, 0)

  ordered = set([])

  data = asset.data[asset.data['t'] >= startDate][asset.data['t'] <= endDate]['o']

  if len(data) > 2:
    for i in data.index[1:]:
      buySig, sellSig, confidence = JUDGEFUNC(asset, i)
      currentPrice = data[i]
      if buySig:
        isOrder, qty = ORDERFUNC(asset=asset, side='buy', confidence=confidence)
        if isOrder and qty > 0:
          asset.account_info['buying_power'] -= qty * currentPrice
          asset.current_position += qty
          ordered.add(i)

          # If a buying or selling point has been appeared, renew start_point
          asset.start_point = len(asset.data['o']) - 2 if i == 0 else i

        predicted_points.append(('buy', i, currentPrice))
      elif sellSig:
        isOrder, qty = ORDERFUNC(asset=asset, side='sell', confidence=confidence)
        if isOrder and qty > 0:
          asset.account_info['buying_power'] += qty * currentPrice
          asset.current_position -= qty
          ordered.add(i)

          # If a buying or selling point has been appeared, renew start_point
          asset.start_point = len(asset.data['o']) - 2 if i == 0 else i

        predicted_points.append(('sell', i, currentPrice))

    estimated_margins['margin'] = (
      asset.account_info['buying_power'] + asset.current_position * data[i] - estimated_margins['margin'][0],
      asset.account_info['buying_power'],
      asset.current_position * data[i]
    )

    visualize_points(asset, predicted_points, ordered)

  return estimated_margins