import MetaTrader5 as mt5
from config import MT5_FILLING_MODE, MT5_DEVIATION, MAGIC_NUMBER
from datetime import datetime, timedelta, timezone
from logger import log_trade_open, print_trade, log_trade_close
from alerts import send_alert

def place_order(bot_mt5, symbol, order_type: str, lot: float, sl: float, tp: float):
    tick = bot_mt5.safe_tick(symbol)
    price = tick.ask if order_type == 'BUY' else tick.bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
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
        "symbol": symbol,
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
        
        # Send email alert
        subject = f"Trade Execution Failed | {symbol} | {order_type}"
        message = f"""
        TRADE EXECUTION FAILURE

        Timestamp: {datetime.now()}
        Symbol: {symbol}
        Order Type: {order_type}
        Volume (Lots): {lot}
        Requested Price: {price}
        Stop Loss: {sl}
        Take Profit: {tp}

        Retcode: {result.retcode}
        Broker Comment: {result.comment}

        The order was NOT executed.

        Immediate review may be required.

        -- PRO ICT Trading Bot
        """
        send_alert(subject, message)
        return False

    print(f"{datetime.now()} → ORDER EXECUTED | Ticket: {result.order}")
    print_trade(trade_info)
    log_trade_open(trade_info)

    # Send email alert
    subject = f"Trade Executed | {symbol} | {order_type}"
    message = f"""
    TRADE EXECUTION CONFIRMATION

    Timestamp: {trade_info['timestamp']}
    Symbol: {trade_info['symbol']}
    Order Type: {trade_info['type']}
    Volume (Lots): {trade_info['volume']}
    Entry Price: {trade_info['price']}
    Stop Loss: {trade_info['sl']}
    Take Profit: {trade_info['tp']}
    Ticket ID: {trade_info['ticket']}
    Deal ID: {trade_info['deal']}

    The order was successfully executed on the MT5 server.

    -- PRO ICT Trading Bot
    """
    send_alert(subject, message)

    return result


def check_closed_trades(bot_mt5, symbol):
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
                    "symbol": symbol,
                    "ticket": d.position_id,
                    "type": "CLOSE",
                    "profit": d.profit,
                    "price": d.price,
                    "volume": d.volume,
                })
                LAST_PROCESSED_DEAL = d.ticket


def manage_trade(bot_mt5, symbol: str, ticket: int, entry_price: float, tp: float, sl: float, move_pct=0.5, partial_pct=0.5):
    """
    Adjust SL to breakeven and take partial profits.
    """
    pos = bot_mt5.safe_position_get_by_ticket(ticket)
    if pos is None:
        return

    tick = bot_mt5.safe_tick(symbol)
    current_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
    lot = pos.volume

    # --- Breakeven SL ---
    tp_move = abs(tp - entry_price)
    threshold_price = entry_price + tp_move * move_pct if pos.type == mt5.ORDER_TYPE_BUY else entry_price - tp_move * move_pct

    if (pos.type == mt5.ORDER_TYPE_BUY and current_price >= threshold_price) or \
       (pos.type == mt5.ORDER_TYPE_SELL and current_price <= threshold_price):
        
        if pos.sl != entry_price:
            # Move SL to entry price
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": mt5.positions_get(ticket=ticket)[0].symbol,
                "position": ticket,
                "sl": entry_price,
                "tp": tp,
                "deviation": MT5_DEVIATION,
                "magic": MAGIC_NUMBER,
            }
            bot_mt5.safe_order_send(request)
        
            # Send email
            subject = f"SL Moved to Breakeven | {symbol}"
            message = f"""
            STOP LOSS UPDATED

            Symbol: {symbol}
            Ticket: {ticket}
            New SL: {entry_price}

            Risk on trade is now neutral.

            -- PRO ICT Trading Bot
            """
            send_alert(subject, message)
            print(f"{datetime.now()} [{symbol}] → SL moved to breakeven for ticket {ticket}")

    # --- Partial close at 80% TP ---
    partial_price = entry_price + tp_move * 0.8 if pos.type == mt5.ORDER_TYPE_BUY else entry_price - tp_move * 0.8
    # Only try partial close if lots remain
    if lot > 0 and ((pos.type == mt5.ORDER_TYPE_BUY and current_price >= partial_price) or (pos.type == mt5.ORDER_TYPE_SELL and current_price <= partial_price)):
                
        partial_lot = round(lot * partial_pct, 2)  # round to 2 decimal places or broker's step size
        if partial_lot > lot:                     # prevent closing more than remaining
            partial_lot = lot
            
        if partial_lot <= 0:
            print(f"{symbol} → Calculated lot is 0 — skipping order")
            return

        # send partial close request
        result = bot_mt5.safe_order_send({
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": partial_lot,
            "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "price": current_price,
            "position": ticket,
            "deviation": MT5_DEVIATION,
            "magic": MAGIC_NUMBER,
            "comment": "Partial close (Python Bot)",
            "type_time": mt5.ORDER_TIME_GTC,
        })
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"{datetime.now()} → ORDER FAILED")
            print(f"Retcode: {result.retcode}")
            print(f"Comment: {result.comment}")

            # Send emails
            subject = f"Partial Close FAILED | {symbol}"
            message = f"""
            PARTIAL CLOSE FAILURE

            Symbol: {symbol}
            Ticket: {ticket}
            Attempted Close Volume: {partial_lot}
            Price: {current_price}

            Retcode: {result.retcode}
            Broker Comment: {result.comment}

            Manual review may be required.

            -- PRO ICT Trading Bot
            """
            send_alert(subject, message)
            print(result)
            return
    
        # update lot in memory
        lot -= partial_lot
        print(f"{datetime.now()} [{symbol}] → Closed {partial_lot} lots (partial) at {current_price} for ticket {ticket}")

        # Send emails
        subject = f"Partial Close Executed | {symbol}"
        message = f"""
        PARTIAL PROFIT TAKEN

        Symbol: {symbol}
        Ticket: {ticket}
        Closed Volume: {partial_lot}
        Execution Price: {current_price}

        Remaining Position: {lot}

        -- PRO ICT Trading Bot
        """
        send_alert(subject, message)

