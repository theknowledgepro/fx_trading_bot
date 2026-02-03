## **1. Install Python & dependencies**

Make sure you have **Python 3.10+** installed. Then install the required packages:

```bash
pip install -r requirements.txt
```

This will install:

* MetaTrader5 (to connect to MT5 terminal)
* pandas (data handling)
* numpy (calculations)
* cryptography (for encrypted credentials)

---

## **2. Open MetaTrader 5**

* Make sure your **MT5 terminal is logged in** to the account where the bot will trade.
* Ensure **AutoTrading is enabled** in MT5.
* Confirm **the symbol is visible** in Market Watch (EURUSD in this project).

---

## Run credetials.py to generate your credentials (NOT NEEDED FOR NOW SEEMS WE USE MT5 TERMINAL)

## **3. Configure your settings**

Open **config.py**:

* Set `SYMBOLS` to the instrument(s) you want (e.g., `"EURUSD"`)
* Set `RISK_PER_TRADE` (0.01 = 1% risk, 0.02 = 2%)
* Adjust `DAILY_DRAWDOWN_LIMIT` if you want stricter rules
* Set SL_POINTS / TP_POINTS in points (5-digit broker → 200 points = 20 pips)

---

## **4. Run the bot**

From the project folder:

```bash
python bot.py
```

You should see logs like:

```
Connected to MT5
Bot started — running... (Ctrl+C to stop)
2026-01-27 22:00:00 → BUY signal detected
2026-01-27 22:00:00 → Open position: BUY, Volume: 0.01, Price: 1.19765, P/L: 0.00
```

* The bot **checks every CHECK_INTERVAL seconds** (default 60s).
* It will **skip trades if there’s an open position**.
* It **calculates lot size dynamically** based on account balance and risk.
* It **respects daily drawdown limits**.
* All trades are **logged in `trades.csv`**.

---

## **5. Stop the bot manually**

* Press **Ctrl + C** in the terminal.
* Open MT5 and **close open trades manually** if needed.

---

## **6. Optional: Backtesting**

You can test your strategy on historical data:

```python
from backtest import backtest
import pandas as pd

# Load historical CSV
df = pd.read_csv("EURUSD_1H.csv")
results = backtest(df)
print(results)
```