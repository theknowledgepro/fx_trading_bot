import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, time as dt_time
from config import TIMEFRAME
from typing import TypedDict, Literal

# This bot will only produce signals when market structure, displacement, and mitigation conditions are satisfied.
# This is normal ICT behavior — there will be periods of no signal.
# Make sure the get_candles() function fetches enough historical candles (≥100) so BOS and displacement detection works.

def get_candles(bot_mt5, symbol, n=200) -> pd.DataFrame:
    """Fetch historical candles and return as DataFrame"""
    df = bot_mt5.safe_candles(symbol, TIMEFRAME, n)
    # print(df.columns) # Check the DataFrame column names
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def detect_bos(df: pd.DataFrame, symbol) -> str | None:
    """
    Detect Break of Structure (BOS)
    """
    highs = df['high']
    lows = df['low']

     # recent swing highs/lows
    prev_high = highs.iloc[-10:-1].max()
    prev_low = lows.iloc[-10:-1].min()

    last_close = df['close'].iloc[-1]
    last_high = highs.iloc[-1]
    last_low = lows.iloc[-1]
    
    # Consider a BOS if high/low wick breaks the swing, even if close doesn’t
    # Check last 3 candles for wick or close break
    print(f"{datetime.now()} [{symbol}] → Checking last 3 candles for BOS → Prev high: {prev_high}, Prev low: {prev_low}")
    for i in range(-3, 0):
        last_close = df['close'].iloc[i]
        last_high = highs.iloc[i]
        last_low = lows.iloc[i]
        # print(f"{datetime.now()} [{symbol}] → Candle {i}: High={last_high}, Low={last_low}, Close={last_close}")

        if last_close > prev_high or last_high > prev_high:
            return 'BULLISH_BOS'
        elif last_close < prev_low or last_low < prev_low:
            return 'BEARISH_BOS'
    return None


def find_displacement(df: pd.DataFrame) -> int | None:
    """
    Find displacement candle (large impulse candle)
    """
    IMPULSE_FACTOR = 1.2  # PROD: instead of 1.5
    for i in range(len(df)-10, len(df)-1):
        body = abs(df['close'].iloc[i] - df['open'].iloc[i])
        prev_range = (df['high'].iloc[i-1] - df['low'].iloc[i-1])
        if body > prev_range * IMPULSE_FACTOR:
            return i
    return None


def find_order_block(df: pd.DataFrame, disp_index: int, direction: str):
    """
    Find last opposite candle before displacement
    """
    for i in range(disp_index-1, 0, -1):
        candle = df.iloc[i]
        if direction == 'BULLISH_BOS' and candle['close'] < candle['open']:
            return (candle['low'], candle['high'])
        if direction == 'BEARISH_BOS' and candle['close'] > candle['open']:
            return (candle['low'], candle['high'])
    return None


def find_fvg(df: pd.DataFrame, disp_index: int, direction: str):
    """
    Detect FVG created by displacement
    """
    if disp_index < 2:
        return None

    c1 = df.iloc[disp_index-2]
    c3 = df.iloc[disp_index]

    # Bullish FVG
    if direction == 'BULLISH_BOS' and c3['low'] > c1['high']:
        return (c1['high'], c3['low'])

    # Bearish FVG
    if direction == 'BEARISH_BOS' and c3['high'] < c1['low']:
        return (c3['high'], c1['low'])

    return None

class Signal(TypedDict):
    direction: Literal['BUY', 'SELL']
    entry_type: Literal['MITIGATION', 'MOMENTUM']

def generate_signal(df: pd.DataFrame, symbol, allow_momentum: bool = True) -> Signal | None:
    """
    TRUE ICT ENTRY MODEL
    Returns a dict with:
    - direction: 'BUY' or 'SELL'
    - entry_type: 'MITIGATION' or 'MOMENTUM'
    
    Parameters:
    - allow_momentum: whether to allow momentum entries (price outside OB/FVG)
    """
    if len(df) < 100:
        print(f"{datetime.now()} [{symbol}] → Not enough candles for signal")
        return None

    bos = detect_bos(df, symbol)
    if not bos:
        print(f"{datetime.now()} [{symbol}] → No BOS found")
        return None

    disp_index = find_displacement(df)
    if disp_index is None:
        print(f"{datetime.now()}  [{symbol}] → No displacement found")
        return None

    ob = find_order_block(df, disp_index, bos)
    fvg = find_fvg(df, disp_index, bos)
    last_price = df['close'].iloc[-1]

    print(f"{datetime.now()} [{symbol}] → BOS detected: {bos}")
    print(f"{datetime.now()} [{symbol}] → Displacement index: {disp_index}")
    print(f"{datetime.now()} [{symbol}] → Order block: {ob}")
    print(f"{datetime.now()} [{symbol}] → FVG: {fvg}")
    print(f"{datetime.now()} [{symbol}] → Last price: {last_price}")

     # --- Mitigation entry check ---
    if bos == 'BULLISH_BOS':
        if ob and ob[0] <= last_price <= ob[1]:
            return Signal(direction='BUY', entry_type='MITIGATION')
        if fvg and fvg[0] <= last_price <= fvg[1]:
            return Signal(direction='BUY', entry_type='MITIGATION')

        # --- Momentum entry (optional) ---
        if allow_momentum:
            return Signal(direction='BUY', entry_type='MOMENTUM')

    if bos == 'BEARISH_BOS':
        if ob and ob[0] <= last_price <= ob[1]:
            return Signal(direction='SELL', entry_type='MITIGATION')
        if fvg and fvg[0] <= last_price <= fvg[1]:
            return Signal(direction='SELL', entry_type='MITIGATION')

        if allow_momentum:
            return Signal(direction='SELL', entry_type='MOMENTUM')

    return None