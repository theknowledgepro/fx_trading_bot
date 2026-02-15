from config import DAILY_DRAWDOWN_LIMIT, RISK_PER_TRADE, LOTS_MIN, LOTS_MAX, SL_POINTS
from datetime import datetime
import pandas as pd
from alerts import send_alert

def calc_lot_size(bot_mt5, symbol, sl_points: float = SL_POINTS, risk_percent: float = RISK_PER_TRADE) -> float:
    balance = bot_mt5.safe_account_info().balance
    risk_amount = balance * risk_percent

    symbol_info = bot_mt5.safe_symbol_info(symbol)
    point = symbol_info.point

    tick_value = symbol_info.trade_tick_value
    contract_size = symbol_info.trade_contract_size

    lot = risk_amount / (sl_points * point * tick_value)
    return max(min(lot, LOTS_MAX), LOTS_MIN)

# DD = (Current Equity − Peak Equity Today) / Peak Equity Today
DAILY_PEAK_EQUITY = None
DAILY_DATE = None
DD_ALERT_SENT = False # Global alert flag to avoid spamming emails repeatedly in one day

def daily_drawdown_check(bot_mt5) -> bool:
    """
    Check daily drawdown and send email alert if limit is exceeded.
    Returns True if drawdown limit exceeded.
    """

    global DAILY_PEAK_EQUITY, DAILY_DATE, DD_ALERT_SENT

    now = datetime.now()
    account_info = bot_mt5.safe_account_info()
    equity = account_info.equity

    # Reset at new day
    if DAILY_DATE != now.date():
        DAILY_DATE = now.date()
        DAILY_PEAK_EQUITY = equity
        DD_ALERT_SENT = False  # reset alert flag for new day

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

    # If drawdown exceeds limit and email not sent yet
    if drawdown_pct <= -DAILY_DRAWDOWN_LIMIT * 100 and not DD_ALERT_SENT:
        subject = "⚠ DAILY DRAWDOWN LIMIT HIT"
        message = f"""
        PRO ICT Trading Bot Alert

        Date: {now.date()}
        Time: {now.time()}

        Daily Drawdown Limit Exceeded!

        Current Equity: {equity:.2f}
        Peak Equity Today: {DAILY_PEAK_EQUITY:.2f}
        Drawdown: {drawdown_pct:.2f}% (Limit: -{DAILY_DRAWDOWN_LIMIT*100:.2f}%)

        Trading has been disabled for today.

        -- PRO ICT Trading Bot
        """
        send_alert(subject, message)
        DD_ALERT_SENT = True  # prevent multiple emails on same day

    # Return True if drawdown exceeded
    return drawdown_pct <= -DAILY_DRAWDOWN_LIMIT * 100

   

    