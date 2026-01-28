# market_engine.py
import pandas as pd
from datetime import datetime

def detect_market_regime(df: pd.DataFrame, allow_momentum=False, session_hours=None) -> str:
    """
    ICT-Inspired Market Regime Detection

    Returns one of:
    - 'TREND_UP'       : Strong bullish trend
    - 'TREND_DOWN'     : Strong bearish trend
    - 'RANGING'        : Sideways market
    - 'VOLATILE'       : High volatility zone, price swings large
    - 'CONSOLIDATION'  : Low volatility, low probability zones (Asian session)
    
    Enhancements over simple EMA + ATR:
    - EMA slope + cross
    - ATR volatility
    - Session filter (optional)
    - Avoid trades in low-probability zones
    """

    if len(df) < 50:
        return "RANGING"

    # ---- Session Filter ----
    if session_hours:
        current_hour = df['time'].iloc[-1].hour
        start, end = session_hours
        if not (start <= current_hour < end):
            return "CONSOLIDATION"

    point = 0.00001  # EURUSD 5-digit
    pip = point * 10

    # ---- EMA Trend Detection ----
    ema_fast = df['close'].ewm(span=20, adjust=False).mean()
    ema_slow = df['close'].ewm(span=50, adjust=False).mean()
    ema_fast_now = ema_fast.iloc[-1]
    ema_fast_prev = ema_fast.iloc[-2]
    ema_slow_now = ema_slow.iloc[-1]
    price = df['close'].iloc[-1]

    ema_slope = ema_fast_now - ema_fast_prev
    ema_pip_diff = abs(ema_fast_now - ema_slow_now) / pip
    ema_pct_diff = abs(ema_fast_now - ema_slow_now) / price

    TREND_THRESHOLD_PIPS = 0.2 if allow_momentum else 0.5
    TREND_THRESHOLD_PCT = 0.0001 if allow_momentum else 0.0002

    if ema_fast_now > ema_slow_now and ema_slope > 0 and ema_pip_diff > TREND_THRESHOLD_PIPS:
        trend = "TREND_UP"
    elif ema_fast_now < ema_slow_now and ema_slope < 0 and ema_pip_diff > TREND_THRESHOLD_PIPS:
        trend = "TREND_DOWN"
    else:
        trend = "RANGING"

    # if ema_fast_now > ema_slow_now and ema_slope > 0 and ema_pct_diff > TREND_THRESHOLD_PCT:
    #     trend = "TREND_UP"
    # elif ema_fast_now < ema_slow_now and ema_slope < 0 and ema_pct_diff > TREND_THRESHOLD_PCT:
    #     trend = "TREND_DOWN"
    # else:
    #     trend = "RANGING"

    # ---- ATR Volatility ----
    hl = df['high'] - df['low']
    atr = hl.rolling(14).mean().iloc[-1]
    atr_pips = atr / pip

    
    # print(f"{datetime.now()} → atr_pips {atr_pips:.2f}")

    VOLATILE_THRESHOLD = 12
    CONSOLIDATION_THRESHOLD = 4

    # Treat as trend temporarily for momentum entries
    if allow_momentum:
        if trend == "RANGING" and atr_pips > 8:
            trend = "TREND_UP" if ema_fast_now > ema_slow_now else "TREND_DOWN"

    volatility = None
    if atr_pips < CONSOLIDATION_THRESHOLD:
        volatility = "CONSOLIDATION"
    elif atr_pips > VOLATILE_THRESHOLD:
        volatility = "VOLATILE"

    # ---- Combine Trend + Volatility ----
    if volatility == "CONSOLIDATION":
        return "CONSOLIDATION"
    elif volatility == "VOLATILE" and trend == "RANGING":
        return "VOLATILE"
    else:
        return trend
