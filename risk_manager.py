import MetaTrader5 as mt5
from config import DAILY_DRAWDOWN_LIMIT, RISK_PER_TRADE, SYMBOL, LOTS_MIN, LOTS_MAX
from datetime import datetime, timedelta
import pandas as pd
 
def calc_lot_size(bot_mt5, sl_points: float, risk_percent: float = RISK_PER_TRADE) -> float:
    balance = bot_mt5.safe_account_info().balance
    risk_amount = balance * risk_percent

    symbol_info = bot_mt5.safe_symbol_info(SYMBOL)
    point = symbol_info.point

    tick_value = symbol_info.trade_tick_value
    contract_size = symbol_info.trade_contract_size

    lot = risk_amount / (sl_points * point * tick_value)
    return max(min(lot, LOTS_MAX), LOTS_MIN)

# DD = (Current Equity − Peak Equity Today) / Peak Equity Today
DAILY_PEAK_EQUITY = None
DAILY_DATE = None
def daily_drawdown_check(bot_mt5) -> bool:
    """
    trade_log: list of dicts [{'timestamp': datetime, 'pl': float}]
    """

    global DAILY_PEAK_EQUITY, DAILY_DATE

    now = datetime.now()
    equity = bot_mt5.safe_account_info().equity

    # Reset at new day
    if DAILY_DATE != now.date():
        DAILY_DATE = now.date()
        DAILY_PEAK_EQUITY = equity

    # Update peak
    if equity > DAILY_PEAK_EQUITY:
        DAILY_PEAK_EQUITY = equity

    # Real drawdown
    drawdown_pct = (equity - DAILY_PEAK_EQUITY) / DAILY_PEAK_EQUITY * 100

    print(
        f"{now} → Equity: {equity:.2f}, "
        f"Peak: {DAILY_PEAK_EQUITY:.2f}, "
        f"DD: {drawdown_pct:.2f}% "
        f"(Limit: -{DAILY_DRAWDOWN_LIMIT*100:.2f}%)"
    )

    return drawdown_pct <= -DAILY_DRAWDOWN_LIMIT * 100

   

    