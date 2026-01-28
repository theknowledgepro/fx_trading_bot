import pandas as pd
from strategy_engine import generate_signal
from market_engine import detect_market_regime
from risk_manager import calc_lot_size

def backtest(df: pd.DataFrame, sl_points: float, tp_points: float):
    """
    Backtesting loop for historical data.
    Returns DataFrame with trade signals and P/L.
    """
    balance = 1000
    results = []

    for i in range(50, len(df)):
        sub_df = df.iloc[:i+1]
        signal = generate_signal(sub_df)
        regime = detect_market_regime(sub_df)

        if signal and regime == "TRENDING":
            open_price = df['close'].iloc[i]
            sl = open_price - sl_points * df['close'].iloc[i] * 0.0001 if signal == 'BUY' else open_price + sl_points * df['close'].iloc[i] * 0.0001
            tp = open_price + tp_points * df['close'].iloc[i] * 0.0001 if signal == 'BUY' else open_price - tp_points * df['close'].iloc[i] * 0.0001
            pl = tp - open_price if signal == 'BUY' else open_price - tp
            balance += pl
            results.append({"index": i, "signal": signal, "pl": pl, "balance": balance})

    return pd.DataFrame(results)
