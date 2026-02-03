# -------------------------------
# CONFIGURATION
# -------------------------------
import MetaTrader5 as mt5
from credentials import decrypt_secret
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Decrypt credentials
MT5_LOGIN = decrypt_secret(os.getenv("MT5_LOGIN_ENC"))
MT5_PASSWORD = decrypt_secret(os.getenv("MT5_PASSWORD_ENC"))
MT5_SERVER = os.getenv("MT5_SERVER")

SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
TIMEFRAME = mt5.TIMEFRAME_M5 # 5-minute candles

CHECK_INTERVAL = 30       # seconds between checks
LOTS_MIN = 0.01
LOTS_MAX = 5.0
RISK_PER_TRADE = 0.01     # 1% of equity
DAILY_DRAWDOWN_LIMIT = 0.05  # 5% of equity

SL_POINTS = 200           # Stop-loss in points
TP_POINTS = 200           # Take-profit in points

MT5_FILLING_MODE = mt5.ORDER_FILLING_FOK      # FOK
MT5_DEVIATION = 10        # Max slippage
MAGIC_NUMBER = 234000

# risk to reward ration - 1:1.5 or 1:2
# breakeven at 40% win rate
