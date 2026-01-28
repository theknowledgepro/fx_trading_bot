import MetaTrader5 as mt5
from config import SYMBOL, MT5_FILLING_MODE, MT5_DEVIATION, MAGIC_NUMBER
from datetime import datetime, timedelta, timezone
from logger import log_trade_open, print_trade, log_trade_close

def place_order(bot_mt5, order_type: str, lot: float, sl: float, tp: float):
    tick = bot_mt5.safe_tick(SYMBOL)
    price = tick.ask if order_type == 'BUY' else tick.bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY if order_type == 'BUY' else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": MT5_DEVIATION,
        "magic": MAGIC_NUMBER,
        "comment": "Python Bot",
        "type_filling": MT5_FILLING_MODE,
        "type_time": mt5.ORDER_TIME_GTC,
    }

    result = bot_mt5.safe_order_send(request)

    trade_info = {
        "timestamp": datetime.now(),
        "ticket": result.order,
        "type": order_type,
        "volume": lot,
        "price": price,
        "sl": sl,
        "tp": tp,
        "retcode": result.retcode,
        "deal": result.deal,
    }

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"{datetime.now()} → ORDER FAILED")
        print(f"Retcode: {result.retcode}")
        print(f"Comment: {result.comment}")
        print(result)
        return False

    print(f"{datetime.now()} → ORDER EXECUTED | Ticket: {result.order}")
    print_trade(trade_info)
    log_trade_open(trade_info)
    return result


def check_closed_trades(bot_mt5):
    global LAST_PROCESSED_DEAL
    utc_now = datetime.now(timezone.utc)
    utc_from = utc_now - timedelta(minutes=30)
    deals = bot_mt5.safe_history_deals_get(utc_from, utc_now) 

    if deals:
        for d in deals:
            # Only process NEW deals
            if d.ticket <= LAST_PROCESSED_DEAL:
                continue
            if d.entry == mt5.DEAL_ENTRY_OUT:  # position closed
                log_trade_close({
                    "timestamp": datetime.now(),
                    "ticket": d.position_id,
                    "type": "CLOSE",
                    "profit": d.profit,
                    "price": d.price,
                    "volume": d.volume,
                })
                LAST_PROCESSED_DEAL = d.ticket
