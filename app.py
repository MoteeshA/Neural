from flask import Flask, render_template
import yfinance as yf
import pandas as pd

app = Flask(__name__)

# 📄 Load stocks from CSV
def get_stock_list():
    try:
        df = pd.read_csv("nifty50.csv")
        return df["symbol"].dropna().tolist()
    except Exception as e:
        print("Error loading CSV:", e)
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS"]


# 🔥 Main Scanner Function
def get_opportunities():
    stocks = get_stock_list()
    results = []
    fallback_data = []  # always keep some data

    try:
        data = yf.download(
            tickers=stocks,
            period="2mo",
            interval="1d",
            group_by='ticker',
            threads=True
        )
    except Exception as e:
        print("Error fetching stock data:", e)
        return [{
            "stock": "ERROR",
            "price": "-",
            "score": 0,
            "signals": "Data fetch failed"
        }]

    for stock in stocks:
        try:
            if stock not in data:
                continue

            df = data[stock].copy()
            df.dropna(inplace=True)

            if len(df) < 20:
                continue

            latest = df.iloc[-1]
            prev = df.iloc[:-1]

            latest_close = float(latest['Close'])
            latest_volume = float(latest['Volume'])

            max_20 = float(prev['Close'].rolling(20).max().iloc[-1])
            avg_vol_10 = float(prev['Volume'].rolling(10).mean().iloc[-1])
            avg_price = float(prev['Close'].mean())

            breakout = latest_close > max_20
            volume_spike = latest_volume > 2 * avg_vol_10

            # 🔥 Improved scoring
            score = 0
            signals = []

            if breakout:
                score += 40
                signals.append("Breakout")

            if volume_spike:
                score += 30
                signals.append("Volume Spike")

            if latest_close > avg_price:
                score += 20
                signals.append("Uptrend")

            if latest_volume > avg_vol_10:
                score += 10
                signals.append("High Volume")

            # 🧠 Always store fallback candidates
            fallback_data.append({
                "stock": stock.replace(".NS", ""),
                "price": round(latest_close, 2),
                "score": score,
                "signals": ", ".join(signals) if signals else "Neutral"
            })

            # 🎯 Strong opportunities
            if score >= 20:
                results.append({
                    "stock": stock.replace(".NS", ""),
                    "price": round(latest_close, 2),
                    "score": score,
                    "signals": ", ".join(signals)
                })

        except Exception as e:
            print(f"Skipping {stock}: {e}")
            continue

    # 🔥 CASE 1: Strong signals exist
    if len(results) > 0:
        return sorted(results, key=lambda x: x["score"], reverse=True)[:10]

    # 🔥 CASE 2: No strong signals → show best available
    if len(fallback_data) > 0:
        fallback_sorted = sorted(fallback_data, key=lambda x: x["score"], reverse=True)[:10]

        for item in fallback_sorted:
            item["signals"] = item["signals"] + " (Weak Signal)"

        return fallback_sorted

    # 🔥 CASE 3: Total failure (rare)
    return [{
        "stock": "MARKET",
        "price": "-",
        "score": 0,
        "signals": "Market data unavailable"
    }]


# 🏠 Home Route
@app.route("/")
def home():
    data = get_opportunities()
    return render_template("index.html", data=data)


# ▶️ Run App
if __name__ == "__main__":
    app.run(debug=True)