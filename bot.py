import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import datetime
from config import SYMBOL, CHECK_INTERVAL, SL_POINTS, TP_POINTS
from strategy_engine import generate_signal, get_candles
from market_engine import detect_market_regime
from risk_manager import calc_lot_size, daily_drawdown_check
from execution import place_order
from logger import log_position_update
from mt5 import ResilientMT5


# Initialize MT5
bot_mt5 = ResilientMT5(retry_interval=10, max_retries=5)
print("Bot started — running... (Ctrl+C to stop)")

try:
    while True:
        df = get_candles(bot_mt5, n=200)
        signal = generate_signal(df, allow_momentum=True)
        # regime = detect_market_regime(df, session_hours=(8,17)) # Only trade during London/New York - London + early NY hours (adjust to your broker TZ)
        regime = detect_market_regime(df, allow_momentum=True)

         # Log open positions
        positions = bot_mt5.safe_positions_get(SYMBOL)
        if positions and len(positions) > 0:
            total_pl = sum([pos.profit for pos in positions])
            for pos in positions:
                print(f"{datetime.now()} → Open position: {'BUY' if pos.type == 0 else 'SELL'}, "
                    f"Volume: {pos.volume}, Price: {pos.price_open:.5f}, "
                    f"P/L: {pos.profit:.2f}")
                log_position_update({
                    "timestamp": datetime.now(),
                    "ticket": pos.ticket,
                    "type": "BUY" if pos.type == 0 else "SELL",
                    "volume": pos.volume,
                    "open_price": pos.price_open,
                    "current_price": pos.price_current,
                    "floating_pl": pos.profit,
                })
            print(f"{datetime.now()} → Total P/L: {total_pl:.2f}")
                    
        if daily_drawdown_check(bot_mt5):
            print(f"{datetime.now()} → Daily drawdown limit reached — stopping trading")
            break

         # --- Trade logic based on regime ---
        if signal:
            # Skip trades in low-probability regimes
            if regime in ["CONSOLIDATION", "RANGING"]:
                print(f"{datetime.now()} → Market regime unsuitable ({regime}) — skipping trade")
            else:
                if not positions:  # only open new if no positions
                    # --- Calculate trade parameters & place order---
                    signal_direction = signal['direction']
                    lot = calc_lot_size(bot_mt5, SL_POINTS)
                    tick = bot_mt5.safe_tick(SYMBOL)
                    point = bot_mt5.safe_symbol_info(SYMBOL).point
                    
                    sl = tick.ask + SL_POINTS*point if signal_direction=='SELL' else tick.bid - SL_POINTS*point # SELL uses tick.ask for SL/TP
                    tp = tick.ask - TP_POINTS*point if signal_direction=='SELL' else tick.bid + TP_POINTS*point # BUY uses tick.bid for SL/TP

                    place_order(bot_mt5, signal_direction, lot, sl, tp)
                else:
                    print(f"{datetime.now()} → Existing position detected — skipping {signal_direction}, Entry type: {signal['entry_type']}")
        else:
            print(f"{datetime.now()} → No signal")
            
        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    print("Bot stopped by user")

bot_mt5.shutdown()
