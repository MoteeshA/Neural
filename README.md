# 🚀 AI Radar Pro — Neural Trading Intelligence Dashboard

## 📌 Overview

AI Radar Pro is a real-time AI-powered stock analysis dashboard built using Flask, Python, and modern frontend technologies.
It analyzes Indian stock market data (NSE) using technical indicators and AI to generate trading signals, insights, and visualizations.

---

## ✨ Features

### 📊 Core Features

* 🔍 Stock scanning across 50+ NSE stocks
* 🤖 AI-based BUY / SELL / WATCH signals
* 📈 Interactive candlestick charts (Plotly)
* 📉 Technical indicators:

  * RSI
  * MACD
  * Moving Averages (MA20, EMA9)
  * Bollinger Bands
  * ATR (Volatility)

### 🧠 AI Features

* AI-generated trade explanations
* Market sentiment analysis
* AI chatbot for trading queries

### ⚡ Real-Time Features

* Live stock price updates (every 10s)
* Auto-refresh opportunities (every 30s)
* Dynamic dashboard stats

### 🎨 UI/UX

* Dark/Light mode toggle
* Responsive design (mobile-friendly)
* Autocomplete stock search
* Watchlist (localStorage)
* Animated trading dashboard

---

## 📸 Screenshots

### 🖥️ Dashboard — AI Opportunity Radar

![Dashboard](screenshots/screen1.png)

### 📊 Stock Detail — Neural Terminal Overview

![Stock Detail](screenshots/screen2.png)

### 📉 Advanced Chart with Indicators

![Indicators](screenshots/screen3.png)

### 📈 Technical Analysis (Zoomed View)

![Analysis](screenshots/screen4.png)

### 🧠 AI Insight + Trading Signals

![Insights](screenshots/screen5.png)

---

## 🏗️ Tech Stack

### Backend

* Python (Flask)
* yfinance (market data)
* Pandas, NumPy (data processing)
* OpenAI API (AI insights)

### Frontend

* HTML, CSS (custom + Tailwind)
* JavaScript (Vanilla)
* Plotly.js (charts)
* Chart.js (dashboard visuals)

---

## 📂 Project Structure

```
AI_ANALYZER/
│
├── app.py
├── requirements.txt
├── .env
│
├── templates/
│   ├── index.html
│   └── stock.html
│
├── screenshots/
│   ├── screen1.png
│   ├── screen2.png
│   ├── screen3.png
│   ├── screen4.png
│   └── screen5.png
│
└── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```
git clone https://github.com/your-username/AI-Radar.git
cd AI-Radar
```

### 2️⃣ Create Virtual Environment

```
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

### 3️⃣ Install Dependencies

```
pip install -r requirements.txt
```

### 4️⃣ Setup Environment Variables

Create a `.env` file:

```
OPENAI_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key
```

---

## ▶️ Run the Application

```
python app.py
```

Open in browser:

```
http://127.0.0.1:5001
```

---

## 🔌 API Endpoints

| Endpoint                   | Description      |
| -------------------------- | ---------------- |
| `/api/stock-data/<symbol>` | Full chart data  |
| `/api/live-price/<symbol>` | Live price       |
| `/api/opportunities`       | AI-ranked stocks |
| `/api/stocks`              | Stock list       |
| `/chatbot`                 | AI assistant     |

---

## 📊 How It Works

1. Fetches stock data using `yfinance`
2. Calculates technical indicators
3. Applies scoring algorithm (0–100)
4. Generates signals:

   * **BUY** (score ≥ 70)
   * **SELL** (score ≤ 35)
   * **WATCH** (otherwise)
5. Enhances insights using AI (if enabled)

---

## ⚠️ Known Limitations

* NSE data via `yfinance` may be delayed
* Not suitable for high-frequency trading
* AI insights depend on API availability
* Occasional API throttling possible

---

## 🧠 Future Improvements

* WebSocket real-time streaming
* Portfolio tracking
* Backtesting UI
* Broker integration (Zerodha/Kite)
* Advanced ML models

---

## 📜 Disclaimer

This project is for **educational and informational purposes only**.
It is **not financial advice**. Always do your own research before investing.

---

## 👨‍💻 Author

**Nikhil T. Nainan**
B.E. Computer Science Engineering (2026)
Developer | AI Enthusiast

---

## ⭐ Support

If you like this project:

* ⭐ Star the repo
* 🍴 Fork it
* 🚀 Build on it

---

**AI Radar Pro — Turning data into decisions 🧠📈**
