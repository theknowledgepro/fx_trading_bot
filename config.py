# -------------------------------
# CONFIGURATION
# -------------------------------
import MetaTrader5 as mt5

SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]

# Maximum acceptable spreads per symbol
# The bot will skip trades if the broker's spread exceeds these values.
# Values are in price units, not pips.
# Adjust these based on your broker's typical ECN spreads.
MAX_SPREAD = {
    "EURUSD": 0.0003,  # ~3 pips, typical low-spread FX pair
    "GBPUSD": 0.0005,  # ~5 pips, slightly wider than EURUSD
    "USDJPY": 0.03,    # ~3 pips, JPY pairs use 2 decimal pricing
    "XAUUSD": 0.4      # ~40 cents, gold tends to have wider spreads
}

TIMEFRAME = mt5.TIMEFRAME_M5 # 5-minute candles

CHECK_INTERVAL = 30       # seconds between checks
LOTS_MIN = 0.01
LOTS_MAX = 5.0
RISK_PER_TRADE = 0.01     # 1% of equity
RISK_TO_REWARD_RATIO=1.5
DAILY_DRAWDOWN_LIMIT = 0.05  # 5% of equity

SL_POINTS = 200           # Stop-loss in points
TP_POINTS = 200           # Take-profit in points

MT5_FILLING_MODE = mt5.ORDER_FILLING_FOK      # FOK
MT5_DEVIATION = 10        # Max slippage
MAGIC_NUMBER = 234000

# risk to reward ration - 1:1.5 or 1:2
# breakeven at 40% win rate
