import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, time as dt_time
from pytz import timezone
from datetime import datetime, time as dt_time
from config import TIMEFRAME, RISK_TO_REWARD_RATIO, RISK_PER_TRADE
from typing import TypedDict, Literal, Optional
import ta

# ------------------ Helper Functions ------------------ #
def in_kill_zone():
    est = timezone('US/Eastern')
    now = datetime.now(est).time()
    # London Open 2AM-5AM, NY Open 7AM-10AM, London Close 10AM-12PM
    if (dt_time(2,0) <= now <= dt_time(5,0)) or \
       (dt_time(7,0) <= now <= dt_time(10,0)) or \
       (dt_time(10,0) <= now <= dt_time(12,0)):
        return True
    return False

def trend_filter(df, direction):
    """200 EMA Trend Filter"""
    ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
    last_close = df['close'].iloc[-1]
    if direction == 'BUY' and last_close < ema200:
        return False
    if direction == 'SELL' and last_close > ema200:
        return False
    return True

def htf_trend_check(df_htf, direction):
    """Check HTF bias: only trade in direction of higher timeframe trend"""
    htf_ema = df_htf['close'].ewm(span=50, adjust=False).mean().iloc[-1]
    last_close = df_htf['close'].iloc[-1]
    
    if direction == 'BUY' and last_close < htf_ema:
        return False  # Don't allow buy if HTF trend is bearish
    if direction == 'SELL' and last_close > htf_ema:
        return False  # Don't allow sell if HTF trend is bullish
    return True

def liquidity_sweep(df, session_candles=20, lookback_candles=5):
    """
    Enhanced liquidity sweep detection:
    - Uses the previous session's high/low (first `session_candles`)
    - Checks the last `lookback_candles` for price piercing and reversal
    - Returns 'BUY' or 'SELL' if sweep conditions are met, else None
    """
    # Define previous session high/low
    session_high = df['high'].iloc[:session_candles].max()
    session_low = df['low'].iloc[:session_candles].min()
    
    # Check last few candles for sweep + rejection
    for i in range(-lookback_candles, 0):
        candle = df.iloc[i]
        
        # Bearish liquidity sweep: price pierces session high then closes below it
        if candle['high'] > session_high and candle['close'] < session_high:
            return 'SELL'
        
        # Bullish liquidity sweep: price pierces session low then closes above it
        if candle['low'] < session_low and candle['close'] > session_low:
            return 'BUY'
    
    return None

def atr_sl_tp(df, direction, rr_ratio=RISK_TO_REWARD_RATIO):
    """Calculate ATR-based SL and TP"""
    atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range().iloc[-1]
    last_close = df['close'].iloc[-1]
    if direction == 'BUY':
        sl = last_close - atr
        tp = last_close + atr*rr_ratio
    else:
        sl = last_close + atr
        tp = last_close - atr*rr_ratio
    return sl, tp

def is_inverted_fvg(signal, df: pd.DataFrame) -> bool:
    """
    Checks if a Fair Value Gap (FVG) has been inverted, i.e.,
    price has closed past the FVG in the opposite direction and can now be considered valid.

    Args:
        signal: dict with 'direction' and 'entry_type'
        df: pandas DataFrame of candles (must include 'open', 'high', 'low', 'close')
    
    Returns:
        True if FVG is inverted and ready for mitigation entry, False otherwise
    """
    if signal['entry_type'] != 'MITIGATION':
        # Only FVG mitigation entries need this
        return True

    last_close = df['close'].iloc[-1]

    # Extract FVG from the last displacement
    # Assuming generate_signal() returned 'fvg' in some way, otherwise adjust this
    # Example: signal['fvg'] = (low, high)
    if 'fvg' not in signal or signal['fvg'] is None:
        return False

    fvg_low, fvg_high = signal['fvg']

    # Bullish BOS → price must close above previous bearish FVG to invert it
    if signal['direction'] == 'BUY' and last_close > fvg_high:
        return True
    # Bearish BOS → price must close below previous bullish FVG
    if signal['direction'] == 'SELL' and last_close < fvg_low:
        return True

    return False


# This bot will only produce signals when market structure, displacement, and mitigation conditions are satisfied.
# This is normal ICT behavior — there will be periods of no signal.
# Make sure the get_candles() function fetches enough historical candles (≥100) so BOS and displacement detection works.
def get_candles(bot_mt5, symbol, n=200, timeframe=None) -> pd.DataFrame:
    """
    Fetch historical candles and return as DataFrame.

    Args:
        bot_mt5: ResilientMT5 instance
        symbol: string, e.g., "EURUSD"
        n: number of candles
        timeframe: optional MT5 timeframe, e.g., mt5.TIMEFRAME_H1
    """
    tf = timeframe if timeframe else TIMEFRAME
    df = bot_mt5.safe_candles(symbol, tf, n)

    # Ensure numeric types for TA calculations
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['tick_volume'] = df['tick_volume'].astype(float)
    
    # Convert MT5 timestamp to datetime
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)

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
    type: Literal['FVG', 'OB', 'MOMENTUM']
    fvg: Optional[tuple[float, float]]  # None if not an FVG

def generate_signal(df: pd.DataFrame, symbol, allow_momentum: bool = True) -> Signal | None:
    """
    TRUE ICT ENTRY MODEL
    Returns a dict with:
    - direction: 'BUY' or 'SELL'
    - entry_type: 'MITIGATION' or 'MOMENTUM'
    - type: 'FVG', 'OB', or 'MOMENTUM'
    - fvg: tuple[low, high] if type=='FVG', else None
    
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
            return Signal(direction='BUY', entry_type='MITIGATION', type='OB', fvg=None)
        if fvg and fvg[0] <= last_price <= fvg[1]:
            return Signal(direction='BUY', entry_type='MITIGATION', type='FVG', fvg=fvg)

        # --- Momentum entry (optional) ---
        if allow_momentum:
            return Signal(direction='BUY', entry_type='MOMENTUM', type='MOMENTUM', fvg=None)


    if bos == 'BEARISH_BOS':
        if ob and ob[0] <= last_price <= ob[1]:
            return Signal(direction='SELL', entry_type='MITIGATION', type='OB', fvg=None)
        if fvg and fvg[0] <= last_price <= fvg[1]:
            return Signal(direction='SELL', entry_type='MITIGATION', type='FVG', fvg=fvg)

        if allow_momentum:
            return Signal(direction='SELL', entry_type='MOMENTUM', type='MOMENTUM', fvg=None)

    return None