# PRO ICT ALGORITHMIC TRADING BOT

### Professional-Grade Institutional Strategy Engine

**License Price: $1,000 USD**

---

## Overview

This professional trading system is built around institutional-grade ICT (Inner Circle Trader) concepts combined with quantitative validation, strict risk controls, and automated execution via MetaTrader 5.

The bot is engineered for serious traders who demand disciplined execution, volatility awareness, capital protection, and statistical robustness.

This is not a retail indicator script.
This is a fully structured strategy engine with embedded safeguards.

---

# Core Features

## 1. Strategy Engine (ICT Framework)

* EMA + RSI signal generation
* Multi-Timeframe Market Structure validation
* Fair Value Gap (FVG) detection
* Inversion Fair Value Gap (IFVG) confirmation
* Breaker Block validation logic
* Liquidity Sweep (Liquidity Purge) detection
* Market Structure Shift (MSS) requirement before entry
* High-Timeframe (HTF) directional bias enforcement
* 200 EMA macro trend filter
* ATR-based volatility-adjusted Stop Loss

The bot does not blindly trade every signal.
It trades only when institutional conditions align.

---

## 2. Kill Zone Time Filtering (Time is Price)

The bot trades exclusively during high-liquidity institutional windows:

* **London Kill Zone:** 2:00 AM – 5:00 AM EST
* **New York Kill Zone:** 7:00 AM – 10:00 AM EST
* **London Close:** 10:00 AM – 12:00 PM EST

If current time is outside these windows:

> No new trades are allowed.

This prevents trading during low-probability “zombie hours.”

---

## 3. Market Regime Detection

* Detects trending vs. consolidating conditions
* Avoids statistically low-probability Asian session consolidations
* Volatility-aware trading logic
* Skips trades when spread is abnormally high
* Automatically pauses trading if market is closed

---

## 4. Advanced Risk Management

Capital preservation is embedded at the engine level.

### Dynamic Position Sizing

* Automatically calculates lot size based on account equity
* Never risks more than 1–2% per trade (configurable)

### Daily Drawdown Protection

* Hard 5% daily loss cap
* Bot disables trading once limit is reached

### Risk-to-Reward Discipline

* Minimum RR: 1:1.5 or 1:2
* Designed to remain profitable even at ~40% win rate

### Volatility-Based Stops

* Stop Loss calculated using ATR
* Adjusts to real-time market conditions

---

## 5. Institutional Entry Validation Logic

To avoid common ICT bot failures, this system includes:

### High-Timeframe Bias Enforcement

* Checks 1H / 4H market structure
* If 4H is bearish → only Sell trades allowed
* Never trades against HTF direction

### Liquidity Sweep Requirement

* Identifies prior session highs/lows (e.g., Asian range)
* Requires price to pierce liquidity
* Must show reversal confirmation
* Only then scans for MSS + FVG

### Inversion Gap Confirmation

* Waits for FVG to invert before entry
* Prevents premature entries
* Confirms smart money participation

---

## 6. Execution & Order Management

* Stop Loss and Take Profit automatically attached
* FILLING_MODE = FOK for broker reliability
* Ensures only one trade at a time
* Logs trade type, volume, entry price, and P/L
* Calculates cumulative open P/L
* Supports partial close & breakeven logic
* Graceful shutdown handling (Ctrl+C safe exit)

---

## 7. Backtesting & Validation

* Supports historical backtesting
* Strategy validation before live deployment
* Quantifiable entry and exit rules
* Performance verification capability

---

## 8. Security Architecture

* API keys encrypted
* Credentials encrypted using symmetric cryptography
* No plain-text secrets required
* Defensive handling if exchange/API connectivity fails
* Safe reconnection logic

---

## 9. Failure Handling, Resilience & Alerting

* Detects API or broker feed downtime
* Automatically skips trading if market data becomes unavailable
* Prevents duplicate trade execution
* Handles unexpected shutdown safely (graceful termination)
* Designed for stable 24/7 VPS deployment
* Sends real-time email alerts via **Gmail SMTP** to the configured alert email addresses (trade execution and failures, stop loss moved to breakeven, partial closures, daily drawdown limit reached, API disconnection, errors, risk limits hit, and critical system events)

The system includes secure SMTP authentication using Gmail App Passwords to ensure reliable delivery of operational notifications.

---

# Designed For

* Professional discretionary traders seeking automation
* Prop firm traders requiring strict risk control
* ICT strategy practitioners
* Capital allocators demanding controlled drawdown
* Traders who value discipline over impulse

---

# What This Bot Is Not

* Not a martingale system
* Not a grid strategy
* Not a “spray and pray” scalper
* Not a retail indicator mashup

It is a rules-based institutional execution engine.

---

# Technical Stack

* Python-based architecture
* Fully compatible with MetaTrader 5
* Broker-agnostic (works with MT5-supported brokers)
* VPS-ready for 24/7 uptime

---

# Performance Philosophy

This bot prioritizes:

1. Capital preservation
2. Statistical edge
3. Controlled risk exposure
4. Institutional timing
5. Long-term sustainability

Consistency > Gambling.

---

# Pricing

**$1,000 USD – One-Time License**

Includes:

* Full bot package
* Encrypted configuration system
* Setup documentation
* Deployment guidance

---

# Important Disclaimer

Trading foreign exchange and leveraged instruments involves substantial risk.
Past performance does not guarantee future results.
The user assumes all responsibility for trading decisions and capital management.

---
