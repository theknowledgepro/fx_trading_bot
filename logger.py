import pandas as pd
from datetime import datetime
from config import TRADES_FILE, POSITIONS_FILE, CLOSED_FILE
import MetaTrader5 as mt5
import os

def _append_csv(file, data: dict):
    df = pd.DataFrame([data])
    df.to_csv(file, mode='a', header=not os.path.exists(file), index=False)

# ------------------ TRADE OPEN ------------------
def log_trade_open(info: dict):
    info["event"] = "OPEN"
    info["timestamp"] = datetime.now()
    _append_csv(TRADES_FILE, info)

# ------------------ POSITION UPDATE ------------------
def log_position_update(info: dict):
    info["event"] = "UPDATE"
    info["timestamp"] = datetime.now()
    _append_csv(POSITIONS_FILE, info)

# ------------------ TRADE CLOSE ------------------
def log_trade_close(info: dict):
    info["event"] = "CLOSE"
    info["timestamp"] = datetime.now()
    _append_csv(CLOSED_FILE, info)

def print_trade(trade_info: dict):
    print(f"{datetime.now()} → {trade_info['type']} | "
          f"Volume: {trade_info['volume']} | Price: {trade_info['price']} | "
          f"SL: {trade_info['sl']} | TP: {trade_info['tp']} | P/L: {trade_info.get('profit',0):.2f}")
