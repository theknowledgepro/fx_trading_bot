import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import datetime
from config import SYMBOLS, CHECK_INTERVAL, RISK_PER_TRADE, MAX_SPREAD
from strategy_engine import in_kill_zone, generate_signal, get_candles, trend_filter, htf_trend_check, liquidity_sweep, atr_sl_tp, is_inverted_fvg
from market_engine import detect_market_regime
from risk_manager import calc_lot_size, daily_drawdown_check
from execution import place_order, manage_trade
from logger import log_position_update
from mt5 import ResilientMT5

# ------------------ Initialize MT5 ------------------ #
bot_mt5 = ResilientMT5(retry_interval=10, max_retries=5)
print("Bot started — running... (Ctrl+C to stop)")

try:
    while True:
        if daily_drawdown_check(bot_mt5):
            print(f"{datetime.now()} → Daily drawdown limit reached — stopping trading")
            break

        if not in_kill_zone():
            print(f"{datetime.now()} → Outside kill zones — skipping all new trades")
            time.sleep(CHECK_INTERVAL)
            continue

        for symbol in SYMBOLS:
            try:
                df = get_candles(bot_mt5, symbol, n=200)
                
                df_htf_h1 = get_candles(bot_mt5, symbol, n=200, timeframe=mt5.TIMEFRAME_H1)
                df_htf_h4 = get_candles(bot_mt5, symbol, n=200, timeframe=mt5.TIMEFRAME_H4)
                
                signal = generate_signal(df, symbol, allow_momentum=True)
                regime = detect_market_regime(df, allow_momentum=True)
                positions = bot_mt5.safe_positions_get(symbol)

                # ----- Log open positions per symbol -----
                if positions and len(positions) > 0:
                    total_pl = sum([pos.profit for pos in positions])
                    for pos in positions:
                        manage_trade(
                            bot_mt5,
                            symbol=symbol,
                            ticket=pos.ticket,
                            entry_price=pos.price_open,
                            tp=pos.tp,
                            sl=pos.sl,
                            move_pct=0.4, # breakeven at 40% win rate
                            partial_pct=0.5  # close half at 80% TP
                        )
                        print(f"{datetime.now()} [{symbol}] → Open: {'BUY' if pos.type == 0 else 'SELL'}, "
                            f"Volume: {pos.volume}, Open Price: {pos.price_open:.5f}, "
                            f"P/L: {pos.profit:.2f}")
                        log_position_update({
                            "timestamp": datetime.now(),
                            "symbol": symbol,
                            "ticket": pos.ticket,
                            "type": "BUY" if pos.type == 0 else "SELL",
                            "volume": pos.volume,
                            "open_price": pos.price_open,
                            "current_price": pos.price_current,
                            "floating_pl": pos.profit,
                        })
                    print(f"{datetime.now()} [{symbol}] → Total P/L: {total_pl:.2f}")

                # --- Trade logic based on regime ---
                if signal:
                    signal_direction = signal['direction']
                    
                    # Skip trades in unsuitable regimes
                    if regime in ["CONSOLIDATION", "RANGING"]:
                        print(f"{datetime.now()} → Market regime unsuitable ({regime}) — skipping trade")
                        continue

                    # Skip if already holding positions
                    if positions:
                        print(f"{datetime.now()} [{symbol}] → Existing position detected — skipping {signal_direction}, Entry type: {signal['entry_type']}")
                        continue

                    # Filters before order
                    if not trend_filter(df, signal_direction):
                        print(f"{datetime.now()} [{symbol}] → Trend filter failed — skipping trade")
                        continue

                    if not htf_trend_check(df_htf_h1, signal_direction):
                        print(f"{datetime.now()} [{symbol}] → HTF H1 bias mismatch — signal: {signal_direction} skipped")
                        continue

                    if not htf_trend_check(df_htf_h4, signal_direction):
                        print(f"{datetime.now()} [{symbol}] → HTF H4 bias mismatch — signal: {signal_direction} skipped")
                        continue

                    ls_sweep = liquidity_sweep(df, session_candles=20, lookback_candles=5)
                    if ls_sweep != signal_direction:
                        print(f"{datetime.now()} [{symbol}] → Liquidity sweep failed — signal: {signal_direction} skipped")
                        continue

                    if signal['type'] == 'FVG' and not is_inverted_fvg(signal, df):
                        print(f"{datetime.now()} [{symbol}] → Waiting for IFVG confirmation — skipping trade")
                        continue

                    # Calculate ATR-based SL/TP
                    sl, tp = atr_sl_tp(df, signal_direction)
                    lot = calc_lot_size(bot_mt5, symbol, sl, risk_pct=RISK_PER_TRADE)  # max 1% risk

                    tick = bot_mt5.safe_tick(symbol)

                    # Handle single MAX_SPREAD value or per-symbol dict
                    current_spread = tick.ask - tick.bid
                    max_spread = MAX_SPREAD[symbol] if isinstance(MAX_SPREAD, dict) else MAX_SPREAD

                    if current_spread > max_spread:
                        print(f"{datetime.now()} [{symbol}] → Spread too high ({current_spread:.5f}) — skipping trade")
                        continue

                    # Place order
                    place_order(bot_mt5, symbol, signal_direction, lot, sl, tp)
                                            
                else:
                    print(f"{datetime.now()} [{symbol}] → No signal")
                    
            except Exception as e:
                print(f"{datetime.now()} [{symbol}] → ERROR: {e}")
        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    print("Bot stopped by user")

bot_mt5.shutdown()
