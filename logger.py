import pandas as pd
from datetime import datetime
import MetaTrader5 as mt5
import os
from pathlib import Path

BASE_LOG_DIR = Path("logs")
BASE_LOG_DIR.mkdir(exist_ok=True)

def get_symbol_log_paths(symbol: str):
    symbol_dir = BASE_LOG_DIR / symbol.upper()
    symbol_dir.mkdir(exist_ok=True)
    
    return {
        "trades": symbol_dir / "trades.csv", # entries 
        "positions": symbol_dir / "positions.csv", # floating updates
        "closed": symbol_dir / "closed_trades.csv" # final P/L
    }


def _append_csv(file, trade_info: dict):
    df = pd.DataFrame([trade_info])
    df.to_csv(file, mode='a', header=not os.path.exists(file), index=False)

# ------------------ TRADE OPEN ------------------
def log_trade_open(info: dict):
    info["event"] = "OPEN"
    info["timestamp"] = datetime.now()
    _append_csv(get_symbol_log_paths(info['symbol'])['trades'], info)

# ------------------ POSITION UPDATE ------------------
def log_position_update(info: dict):
    info["event"] = "UPDATE"
    info["timestamp"] = datetime.now()
    _append_csv(get_symbol_log_paths(info['symbol'])['positions'], info)

# ------------------ TRADE CLOSE ------------------
def log_trade_close(info: dict):
    info["event"] = "CLOSE"
    info["timestamp"] = datetime.now()
    _append_csv(get_symbol_log_paths(info['symbol'])['closed'], info)

def print_trade(trade_info: dict):
    print(f"{datetime.now()} [{trade_info['symbol']}] → {trade_info['type']} | "
          f"Volume: {trade_info['volume']} | Price: {trade_info['price']} | "
          f"SL: {trade_info['sl']} | TP: {trade_info['tp']} | P/L: {trade_info.get('profit',0):.2f}")
