import MetaTrader5 as mt5
import time
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from credentials import decrypt_secret
from alerts import send_alert
import os

# Load the .env file
load_dotenv()

# ------------------ MT5 Resilient Wrapper ------------------
class ResilientMT5:
    def __init__(self, path=None, retry_interval=10, max_retries=5):
        self.retry_interval = retry_interval
        self.max_retries = max_retries

        # --- Load encrypted values ---
        login_enc = os.getenv("MT5_LOGIN_ENC")
        password_enc = os.getenv("MT5_PASSWORD_ENC")
        server = os.getenv("MT5_SERVER")

        # --- Decrypt ---
        login = decrypt_secret(login_enc)
        password = decrypt_secret(password_enc)

        if not login or not password:
            raise Exception("Failed to decrypt MT5 credentials.")

        login = int(login)

        # --- Initialize MT5 ---
        if not mt5.initialize(path):
            raise Exception(f"Initialize failed: {mt5.last_error()}")

        authorized = mt5.login(login, password=password, server=server)

        if not authorized:
            raise Exception(f"Login failed: {mt5.last_error()}")

        print(f"{datetime.now()} → ✅ Connected to MT5 successfully")

    def safe_account_info(self) -> float:
        """Fetch account balance safely with retries and alerts"""
        retries = 0
        while retries < self.max_retries:
            info = mt5.account_info()
            if info is not None:
                return info
            else:
                retries += 1
                msg = f"Failed to fetch account balance (attempt {retries})"
                print(f"{datetime.now()} → {msg}")
                send_alert("MT5 API Balance Error", msg)
                time.sleep(self.retry_interval)
        # After max retries
        raise ConnectionError(f"Account balance unavailable after {self.max_retries} retries")

    def safe_tick(self, symbol: str):
        """Get tick info with retries and alerts"""
        retries = 0
        while retries < self.max_retries:
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return tick
            else:
                retries += 1
                msg = f"Failed to get tick for {symbol} (attempt {retries})"
                print(f"{datetime.now()} → {msg}")
                send_alert("MT5 API Tick Error", msg)
                time.sleep(self.retry_interval)
        # After max retries
        raise ConnectionError(f"MT5 tick unavailable for {symbol} after {self.max_retries} retries")
    
    def safe_symbol_info(self, symbol: str):
        """Get symbol_info info with retries and alerts"""
        retries = 0
        while retries < self.max_retries:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                return symbol_info
            else:
                retries += 1
                msg = f"Failed to get symbol_info for {symbol} (attempt {retries})"
                print(f"{datetime.now()} → {msg}")
                send_alert("MT5 API Symbol Info Error", msg)
                time.sleep(self.retry_interval)
        # After max retries
        raise ConnectionError(f"MT5 symbol_info unavailable for {symbol} after {self.max_retries} retries")

    def safe_order_send(self, request):
        """Send order safely with retries and alerts"""
        retries = 0
        while retries < self.max_retries:
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                return result
            else:
                retries += 1
                msg = f"Order send failed: {result} (attempt {retries})"
                print(f"{datetime.now()} → {msg}")
                send_alert("MT5 API Order Error", msg)
                time.sleep(self.retry_interval)
        raise ConnectionError(f"MT5 order failed after {self.max_retries} retries")

    def safe_candles(self, symbol: str, timeframe, n: int):
        """Get historical candles safely with retries and alerts"""
        retries = 0
        while retries < self.max_retries:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
            if rates is not None and len(rates) > 0:
                return pd.DataFrame(rates)
            else:
                retries += 1
                msg = f"Failed to fetch {n} candles for {symbol} (attempt {retries})"
                print(f"{datetime.now()} → {msg}")
                send_alert("MT5 API Candle Error", msg)
                time.sleep(self.retry_interval)
        # After max retries
        raise ConnectionError(f"MT5 candles unavailable for {symbol} after {self.max_retries} retries")

    def safe_positions_get(self, symbol: str):
        """Fetch open positions safely"""
        retries = 0
        while retries < self.max_retries:
            positions = mt5.positions_get(symbol=symbol)
            if positions is not None:
                return positions
            retries += 1
            msg = f"Failed to get positions for {symbol} (attempt {retries})"
            print(f"{datetime.now()} → {msg}")
            send_alert("MT5 API Positions Error", msg)
            time.sleep(self.retry_interval)
        raise ConnectionError(f"MT5 positions unavailable for {symbol} after {self.max_retries} retries")

    def safe_position_get_by_ticket(self, ticket: int):
        """
        Fetch a single open position by ticket safely.
        Retries if MT5 API returns None.
        """
        retries = 0
        while retries < self.max_retries:
            try:
                positions = mt5.positions_get()
                if positions is not None:
                    for pos in positions:
                        if pos.ticket == ticket:
                            return pos
                    return None  # ticket not found
            except Exception as e:
                print(f"{datetime.now()} → Error fetching position: {e}")

            retries += 1
            msg = f"Failed to get position for ticket {ticket} (attempt {retries})"
            print(f"{datetime.now()} → {msg}")
            send_alert("MT5 API Position Error", msg)
            time.sleep(self.retry_interval)

        raise ConnectionError(f"MT5 position unavailable for ticket {ticket} after {self.max_retries} retries")

    def safe_history_deals_get(self, utc_from: datetime, utc_to: datetime):
        """
        Safely fetch MT5 deal history between utc_from and utc_to.
        Retries if MT5 API fails or returns None.
        Returns empty list on repeated failures.
        """
        retries = 0
        while retries < self.max_retries:
            deals = mt5.history_deals_get(utc_from, utc_to)
            if deals is not None:
                return deals
            else:
                retries += 1
                msg = f"Failed to fetch deals (attempt {retries})"
                print(f"{datetime.now()} → {msg}")
                send_alert("MT5 API Deals History Error", msg)
                time.sleep(self.retry_interval)

        # After max retries
        print(f"{datetime.now()} → Failed to fetch deals after {self.max_retries} retries. Returning empty list.")
        return []


    def shutdown(self):
        mt5.shutdown()
        print(f"{datetime.now()} → MT5 shutdown")


# ------------------ Example Usage ------------------
if __name__ == "__main__":
    bot_mt5 = ResilientMT5()

    try:
        tick = bot_mt5.safe_tick("EURUSD")
        print(f"Current price: {tick.bid}")
    except ConnectionError as e:
        print(f"Fatal error: {e}")
    finally:
        bot_mt5.shutdown()
