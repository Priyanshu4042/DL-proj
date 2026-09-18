import numpy as np
import pandas as pd

def run_backtest(dates, prices, predictions, initial_cash=1.0):
    """
    Simple directional backtest:
    - prices: array-like of true prices aligned with predictions (both 1D)
    - predictions: predicted prices for same timestamps
    Strategy: if predicted_price > current_price -> long 1 unit (buy at current, sell at next close)
    We assume prices[i] corresponds to the price at time t (current), and predictions[i] predicts price at time t (i.e., next target equals actual future price provided in `prices_next`).

    Returns dict with cumulative return, daily returns series, directional accuracy, and total trades.
    """
    prices = np.asarray(prices).astype(float).flatten()
    preds = np.asarray(predictions).astype(float).flatten()

    # ensure same length
    n = min(len(prices), len(preds))
    prices = prices[:n]
    preds = preds[:n]

    # true forward returns: we need next-day returns; shift prices by -1
    # for the last element we can't compute next return -> drop last
    if n < 2:
        return {'error': 'not enough data for backtest'}

    price_now = prices[:-1]
    price_next = prices[1:]
    pred_now = preds[:-1]

    true_returns = (price_next - price_now) / price_now

    # position: +1 for long, -1 for short
    position = np.where(pred_now > price_now, 1.0, -1.0)

    strategy_returns = position * true_returns

    cum_return = (1 + strategy_returns).prod() - 1
    daily_return_mean = strategy_returns.mean()
    daily_return_std = strategy_returns.std(ddof=1) if strategy_returns.size > 1 else 0.0
    sharpe = (daily_return_mean / daily_return_std * (252 ** 0.5)) if daily_return_std > 0 else None
    direction_accuracy = (np.sign(pred_now - price_now) == np.sign(price_next - price_now)).mean()

    out = {
        'cumulative_return': float(cum_return),
        'daily_returns': strategy_returns.tolist(),
        'sharpe': float(sharpe) if sharpe is not None else None,
        'direction_accuracy': float(direction_accuracy),
        'n_trades': int(len(strategy_returns)),
    }
    return out
