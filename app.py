from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from functools import lru_cache
import time
from datetime import datetime, timedelta

# ==============================
# ✅ ENV
# ==============================
load_dotenv()

# ==============================
# 🤖 OPENAI
# ==============================
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")

USE_AI = False
client = None

if api_key:
    try:
        client = OpenAI(api_key=api_key)
        USE_AI = True
    except:
        print("OpenAI initialization failed")

print("AI Enabled:", USE_AI)

# ==============================
# 🚀 APP
# ==============================
app = Flask(__name__)

# ==============================
# 📄 COMPREHENSIVE STOCK LIST (NIFTY 50 + NIFTY NEXT 50 + SENSEX)
# ==============================
def get_stock_list():
    """
    Returns a comprehensive list of Indian stocks including:
    - NIFTY 50
    - NIFTY Next 50
    - Bank NIFTY
    - Major mid-caps
    """
    try:
        # Try to read from CSV first
        if os.path.exists("nifty50.csv"):
            df = pd.read_csv("nifty50.csv")
            stocks = df["symbol"].dropna().tolist()
            # Add .NS suffix if not already present
            stocks = [s if '.NS' in s else s + '.NS' for s in stocks]
            return stocks
    except:
        pass
    
    # Comprehensive Indian stock list (NIFTY 50 + major stocks)
    indian_stocks = [
        # NIFTY 50 Stocks
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
        "BAJFINANCE.NS", "LT.NS", "WIPRO.NS", "ASIANPAINT.NS", "AXISBANK.NS",
        "MARUTI.NS", "SUNPHARMA.NS", "HCLTECH.NS", "ULTRACEMCO.NS", "TITAN.NS",
        "ADANIPORTS.NS", "NTPC.NS", "POWERGRID.NS", "M&M.NS", "TATAMOTORS.NS",
        "TATASTEEL.NS", "JSWSTEEL.NS", "TECHM.NS", "INDUSINDBK.NS", "NESTLEIND.NS",
        
        # NIFTY Next 50 & Major Stocks
        "VEDL.NS", "BAJAJFINSV.NS", "DABUR.NS", "DIVISLAB.NS", "DRREDDY.NS",
        "EICHERMOT.NS", "GRASIM.NS", "HDFC.NS", "HEROMOTOCO.NS", "HINDALCO.NS",
        "HINDZINC.NS", "IOC.NS", "IRCTC.NS", "LICI.NS", "MUTHOOTFIN.NS",
        "NAUKRI.NS", "ONGC.NS", "PIDILITIND.NS", "SBILIFE.NS", "SHREECEM.NS",
        "SIEMENS.NS", "SUNTV.NS", "TORNTPHARM.NS", "UPL.NS", "COALINDIA.NS",
        "BPCL.NS", "BRITANNIA.NS", "CIPLA.NS", "DMART.NS", "GAIL.NS",
        
        # Bank NIFTY & Financials
        "BANKBARODA.NS", "CANBK.NS", "PNB.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS",
        "INDUSINDBK.NS", "RBLBANK.NS", "YESBANK.NS", "AUBANK.NS", "BANDHANBNK.NS",
        
        # IT & Tech
        "LTIM.NS", "MPHASIS.NS", "PERSISTENT.NS", "COFORGE.NS", "MINDTREE.NS",
        
        # Auto
        "BAJAJ-AUTO.NS", "TVSMOTOR.NS", "ASHOKLEY.NS", "BOSCHLTD.NS", "EXIDEIND.NS",
        
        # Pharma & Healthcare
        "APOLLOHOSP.NS", "MAXHEALTH.NS", "METROPOLIS.NS", "LAURUSLABS.NS",
        
        # FMCG
        "MARICO.NS", "GODREJCP.NS", "COLPAL.NS", "HAL.NS",
        
        # Real Estate & Infrastructure
        "DLF.NS", "GODREJPROP.NS", "L&T.NS", "IRB.NS", "NBCC.NS"
    ]
    
    return indian_stocks


# ==============================
# 🔧 SAFE SERIES EXTRACTION
# ==============================
def get_series(df, col):
    """Safely extract a column as pandas Series"""
    if col not in df.columns:
        return pd.Series([0] * len(df))
    data = df[col]
    if isinstance(data, pd.DataFrame):
        data = data.iloc[:, 0]
    return data


# ==============================
# 📊 TECHNICAL INDICATORS
# ==============================
def calculate_rsi(series, period=14):
    """Calculate RSI indicator"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def calculate_macd(series, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(series, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, lower_band, sma


def calculate_obv(df):
    """Calculate On-Balance Volume"""
    close = get_series(df, "Close")
    volume = get_series(df, "Volume")
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv


def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    high = get_series(df, "High")
    low = get_series(df, "Low")
    close = get_series(df, "Close")
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr.fillna(0)


# ==============================
# 📊 PATTERN DETECTION
# ==============================
def detect_patterns(df):
    """Detect chart patterns"""
    patterns = []
    close = get_series(df, "Close")
    high = get_series(df, "High")
    low = get_series(df, "Low")
    
    if len(close) < 20:
        return patterns
    
    # Support and Resistance
    resistance = close.rolling(20).max()
    support = close.rolling(20).min()
    
    # Breakout detection
    if close.iloc[-1] > resistance.iloc[-2] * 0.99:
        patterns.append("Breakout")
    elif close.iloc[-1] < support.iloc[-2] * 1.01:
        patterns.append("Breakdown")
    
    # Candlestick patterns
    body = abs(close - get_series(df, "Open"))
    avg_body = body.rolling(20).mean()
    
    # Doji
    if body.iloc[-1] < avg_body.iloc[-1] * 0.3:
        patterns.append("Doji")
    
    # Bullish Engulfing
    if (close.iloc[-1] > get_series(df, "Open").iloc[-1] and 
        close.iloc[-2] < get_series(df, "Open").iloc[-2] and
        close.iloc[-1] > get_series(df, "Open").iloc[-2] and
        get_series(df, "Open").iloc[-1] < close.iloc[-2]):
        patterns.append("Bullish Engulfing")
    
    # Hammer
    lower_shadow = np.minimum(get_series(df, "Open"), close) - low
    upper_shadow = high - np.maximum(get_series(df, "Open"), close)
    if (lower_shadow.iloc[-1] > 2 * body.iloc[-1] and 
        upper_shadow.iloc[-1] < body.iloc[-1] * 0.5):
        patterns.append("Hammer")
    
    return patterns


# ==============================
# 🤖 AI INSIGHT GENERATION
# ==============================
def generate_ai_insight(data):
    """Generate AI-powered trading insight"""
    if USE_AI and client:
        try:
            prompt = f"""
            You are a professional technical analyst. Provide a concise trading insight (max 100 characters).
            
            Data:
            Price: ₹{data['price']}
            RSI: {data['rsi']:.1f}
            Pattern: {data['pattern']}
            Signal: {data['signal']}
            Score: {data.get('score', 50)}/100
            
            Give short actionable insight:
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=60,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"AI Error: {e}")
    
    # Fallback insights
    if data['signal'] == 'BUY':
        return f"Bullish momentum with RSI {data['rsi']:.0f}. Watch for continuation above resistance."
    elif data['signal'] == 'SELL':
        return f"Bearish pressure building. RSI {data['rsi']:.0f} suggests potential downside."
    else:
        return f"Consolidation phase. RSI {data['rsi']:.0f}. Wait for clear breakout."


# ==============================
# 📈 IMPROVED BACKTESTING
# ==============================
def backtest(df):
    """Backtest trading strategy"""
    trades = 0
    wins = 0
    total_return = 0
    max_drawdown = 0
    peak = 0
    
    close = get_series(df, "Close")
    signals = df.get("Signal", pd.Series(["HOLD"] * len(df)))
    
    position = None
    entry_price = 0
    
    for i in range(1, len(df)):
        current_signal = signals.iloc[i] if i < len(signals) else "HOLD"
        
        if position is None:
            if current_signal == "BUY":
                position = "LONG"
                entry_price = close.iloc[i]
                trades += 1
            elif current_signal == "SELL":
                position = "SHORT"
                entry_price = close.iloc[i]
                trades += 1
        else:
            if position == "LONG" and (current_signal == "SELL" or i == len(df) - 1):
                exit_price = close.iloc[i]
                pnl = (exit_price - entry_price) / entry_price
                total_return += pnl
                if pnl > 0:
                    wins += 1
                position = None
            elif position == "SHORT" and (current_signal == "BUY" or i == len(df) - 1):
                exit_price = close.iloc[i]
                pnl = (entry_price - exit_price) / entry_price
                total_return += pnl
                if pnl > 0:
                    wins += 1
                position = None
        
        # Track drawdown
        current_value = close.iloc[i]
        if current_value > peak:
            peak = current_value
        drawdown = (peak - current_value) / peak if peak > 0 else 0
        max_drawdown = max(max_drawdown, drawdown)
    
    accuracy = (wins / trades * 100) if trades > 0 else 50
    total_return_pct = total_return * 100
    
    return round(accuracy, 2), round(total_return_pct, 2), round(max_drawdown * 100, 2)


# ==============================
# ⚡ CACHE DATA WITH RETRY
# ==============================
@lru_cache(maxsize=1)
def get_market_data_cached():
    """Fetch market data with caching"""
    stocks = get_stock_list()
    try:
        # Fetch in batches to avoid rate limiting
        all_data = {}
        batch_size = 20
        
        for i in range(0, len(stocks), batch_size):
            batch = stocks[i:i+batch_size]
            try:
                data = yf.download(
                    tickers=batch,
                    period="3mo",
                    interval="1d",
                    group_by='ticker',
                    threads=True,
                    progress=False
                )
                if not data.empty:
                    if len(batch) == 1:
                        all_data[batch[0]] = data
                    else:
                        for ticker in batch:
                            if ticker in data.columns.levels[0]:
                                all_data[ticker] = data[ticker]
            except Exception as e:
                print(f"Batch error: {e}")
            time.sleep(0.5)  # Rate limiting
        
        return all_data
    except Exception as e:
        print(f"Market data error: {e}")
        return {}


# ==============================
# 🔥 ENHANCED SCANNER
# ==============================
def get_opportunities():
    """Generate trading opportunities with enhanced scoring"""
    stocks = get_stock_list()
    results = []
    
    try:
        market_data = get_market_data_cached()
    except Exception as e:
        print(f"Data fetch error: {e}")
        return []
    
    for stock in stocks[:50]:  # Limit to 50 stocks for performance
        try:
            if stock not in market_data or market_data[stock].empty:
                continue
            
            df = market_data[stock].dropna()
            if len(df) < 30:
                continue
            
            close = get_series(df, "Close")
            volume = get_series(df, "Volume")
            high = get_series(df, "High")
            low = get_series(df, "Low")
            
            # Technical Indicators
            df["MA20"] = close.rolling(20).mean()
            df["MA50"] = close.rolling(50).mean()
            df["RSI"] = calculate_rsi(close)
            
            macd, macd_signal, macd_hist = calculate_macd(close)
            df["MACD"] = macd
            df["MACD_SIGNAL"] = macd_signal
            df["MACD_HIST"] = macd_hist
            
            upper_bb, lower_bb, sma_bb = calculate_bollinger_bands(close)
            df["BB_UPPER"] = upper_bb
            df["BB_LOWER"] = lower_bb
            
            df["ATR"] = calculate_atr(df)
            df["OBV"] = calculate_obv(df)
            
            patterns = detect_patterns(df)
            
            # Current values
            latest_close = float(close.iloc[-1])
            latest_volume = float(volume.iloc[-1])
            avg_volume = float(volume.rolling(20).mean().iloc[-1])
            rsi = float(df["RSI"].iloc[-1])
            
            # ======================
            # 🎯 ENHANCED SCORING SYSTEM
            # ======================
            score = 50  # Base score
            
            # Trend Score (20 pts)
            if df["MA20"].iloc[-1] > df["MA50"].iloc[-1]:
                score += 12
                if df["MA20"].iloc[-1] > df["MA50"].iloc[-5]:
                    score += 8  # Trending strongly
            else:
                score -= 5
            
            # Momentum Score (20 pts)
            if rsi > 60 and rsi < 80:
                score += 15  # Strong momentum, not overbought
            elif rsi > 50:
                score += 10
            elif rsi < 30:
                score -= 10  # Oversold but could bounce
            elif rsi < 40:
                score -= 5
            
            # MACD Score (15 pts)
            if df["MACD"].iloc[-1] > df["MACD_SIGNAL"].iloc[-1]:
                score += 10
                if df["MACD_HIST"].iloc[-1] > df["MACD_HIST"].iloc[-2]:
                    score += 5  # Increasing momentum
            else:
                score -= 5
            
            # Volume Score (10 pts)
            volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 1
            if volume_ratio > 1.5:
                score += 10  # High volume confirmation
            elif volume_ratio > 1.2:
                score += 5
            elif volume_ratio < 0.5:
                score -= 5
            
            # Volatility/Bollinger Score (10 pts)
            if latest_close > df["BB_UPPER"].iloc[-1]:
                score += 8  # Breakout
            elif latest_close < df["BB_LOWER"].iloc[-1]:
                score -= 5  # Breakdown
            elif latest_close > df["MA20"].iloc[-1]:
                score += 3
            
            # Pattern Score (15 pts)
            pattern_bonus = 0
            if "Breakout" in patterns:
                pattern_bonus += 12
            if "Bullish Engulfing" in patterns:
                pattern_bonus += 10
            if "Hammer" in patterns:
                pattern_bonus += 8
            if "Doji" in patterns:
                pattern_bonus += 3
            
            score += min(pattern_bonus, 15)
            
            # Normalize score
            score = max(0, min(100, score))
            
            # ======================
            # SIGNAL DETERMINATION
            # ======================
            if score >= 70:
                label = "BUY"
            elif score <= 35:
                label = "SELL"
            else:
                label = "WATCH"
            
            # ======================
            # RISK MANAGEMENT
            # ======================
            atr_value = float(df["ATR"].iloc[-1]) if not pd.isna(df["ATR"].iloc[-1]) else latest_close * 0.02
            stop_loss = round(latest_close - (atr_value * 1.5), 2)
            target_1 = round(latest_close + (atr_value * 2), 2)
            target_2 = round(latest_close + (atr_value * 3.5), 2)
            
            confidence = min(score, 100)
            
            insight = generate_ai_insight({
                "price": latest_close,
                "rsi": rsi,
                "pattern": ", ".join(patterns) if patterns else "None",
                "signal": label,
                "score": score
            })
            
            results.append({
                "stock": stock.replace(".NS", ""),
                "price": round(latest_close, 2),
                "score": score,
                "confidence": confidence,
                "signals": label,
                "pattern": ", ".join(patterns[:2]) if patterns else "Sideways",
                "insight": insight,
                "sl": stop_loss,
                "target": target_1,
                "target2": target_2,
                "rsi": round(rsi, 1),
                "volume_ratio": round(volume_ratio, 2)
            })
            
        except Exception as e:
            print(f"Error processing {stock}: {e}")
            continue
    
    # Sort by score and return top 20
    return sorted(results, key=lambda x: x["score"], reverse=True)[:20]


# ==============================
# 🏠 HOME ROUTE
# ==============================
@app.route("/")
def home():
    opportunities = get_opportunities()
    return render_template("index.html", data=opportunities)


# ==============================
# 📊 STOCK DETAIL PAGE
# ==============================
@app.route("/stock/<symbol>")
def stock_detail(symbol):
    """Display detailed chart for a specific stock"""
    tf = request.args.get("tf", "3mo")
    interval = request.args.get("int", "1d")
    
    try:
        ticker = symbol + ".NS" if not symbol.endswith(".NS") else symbol
        df = yf.download(ticker, period=tf, interval=interval, progress=False)
        
        if df.empty:
            return f"No data available for {symbol}", 404
        
        df.reset_index(inplace=True)
        
        close = get_series(df, "Close")
        
        # Calculate indicators
        df["MA20"] = close.rolling(20).mean()
        df["EMA9"] = close.ewm(span=9, adjust=False).mean()
        df["RSI"] = calculate_rsi(close)
        
        macd, macd_signal, _ = calculate_macd(close)
        df["MACD"] = macd
        df["MACD_SIGNAL"] = macd_signal
        
        upper_bb, lower_bb, _ = calculate_bollinger_bands(close)
        df["BB_UPPER"] = upper_bb
        df["BB_LOWER"] = lower_bb
        
        # Generate signals
        signals = []
        for i in range(len(df)):
            if i == 0:
                signals.append("HOLD")
                continue
            
            buy_conditions = (
                df["EMA9"].iloc[i] > df["MA20"].iloc[i] and 
                df["RSI"].iloc[i] > 50 and
                df["MACD"].iloc[i] > df["MACD_SIGNAL"].iloc[i]
            )
            
            sell_conditions = (
                df["RSI"].iloc[i] > 70 or
                (df["EMA9"].iloc[i] < df["MA20"].iloc[i] and df["RSI"].iloc[i] < 45)
            )
            
            if buy_conditions:
                signals.append("BUY")
            elif sell_conditions:
                signals.append("SELL")
            else:
                signals.append("HOLD")
        
        df["Signal"] = signals
        
        # Backtest
        accuracy, profit, max_dd = backtest(df)
        patterns = detect_patterns(df)
        
        insight = generate_ai_insight({
            "price": float(close.iloc[-1]),
            "rsi": float(df["RSI"].iloc[-1]),
            "pattern": ", ".join(patterns) if patterns else "None",
            "signal": signals[-1],
            "score": 70
        })
        
        # Prepare data for template
        date_column = "Date" if "Date" in df.columns else df.columns[0]
        
        return render_template(
            "stock.html",
            symbol=symbol,
            dates=df[date_column].astype(str).tolist(),
            open=get_series(df, "Open").tolist(),
            high=get_series(df, "High").tolist(),
            low=get_series(df, "Low").tolist(),
            close=close.tolist(),
            volume=get_series(df, "Volume").tolist(),
            ma20=df["MA20"].fillna(0).tolist(),
            ema9=df["EMA9"].fillna(0).tolist(),
            rsi=df["RSI"].fillna(50).tolist(),
            signals=signals,
            insight=insight,
            accuracy=accuracy,
            pattern=", ".join(patterns[:2]) if patterns else "None",
            profit=profit,
            max_drawdown=max_dd
        )
        
    except Exception as e:
        print(f"Stock detail error: {e}")
        return f"Error loading {symbol}: {str(e)}", 500


# ==============================
# 📊 MARKET OVERVIEW ROUTE
# ==============================
@app.route("/market")
def market_overview():
    """Market overview with indices"""
    indices = {
        "NIFTY 50": "^NSEI",
        "BANK NIFTY": "^NSEBANK",
        "SENSEX": "^BSESN"
    }
    
    market_data = {}
    for name, symbol in indices.items():
        try:
            data = yf.download(symbol, period="5d", interval="1d", progress=False)
            if not data.empty:
                close = get_series(data, "Close")
                change = ((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100
                market_data[name] = {
                    "value": round(close.iloc[-1], 2),
                    "change": round(change, 2)
                }
        except:
            market_data[name] = {"value": "N/A", "change": 0}
    
    return render_template("market.html", market_data=market_data)


# ==============================
# ▶️ RUN APPLICATION
# ==============================
if __name__ == "__main__":
    print(f"Starting AI Radar Pro...")
    print(f"Available stocks: {len(get_stock_list())}")
    app.run(debug=True, host="0.0.0.0", port=5001)