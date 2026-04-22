import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# ---------- PAGE ----------
st.set_page_config(page_title="Alpha Fusion Engine", layout="wide")
st.title("🚀 Alpha Fusion Engine (Auto News + Signals)")

# 🔑 API KEY (इथे तुझा NEW key paste कर)
API_KEY = "6dc3a37840ff480b97ad7ac869f9652b"

# ---------- FETCH NEWS ----------
def fetch_news():
    url = f"https://newsapi.org/v2/top-headlines?category=business&country=in&apiKey={API_KEY}"
    res = requests.get(url)
    data = res.json()

    articles = data.get("articles", [])
    news_list = [a["title"] for a in articles[:5]]

    return news_list

# ---------- ANALYZE ----------
def analyze_news(news):
    news = news.lower()

    if "rbi" in news or "rate hike" in news:
        return "RBI", "Positive"
    elif "fall" in news or "loss" in news:
        return "General", "Negative"
    elif "growth" in news or "profit" in news:
        return "General", "Positive"
    
    return "General", "Neutral"

# ---------- PRICE ----------
def get_price(ticker):
    return yf.download(ticker, period="1d", interval="1m", progress=False)

def calculate_change(data):
    if data.empty:
        return 0
    start = float(data['Close'].iloc[0])
    end = float(data['Close'].iloc[-1])
    return round(((end - start) / start) * 100, 2)

# ---------- SIGNAL ----------
def generate_signal(sentiment, change):
    if sentiment == "Positive" and change > 0.5:
        return "BUY"
    elif sentiment == "Negative" and change < -0.5:
        return "SELL"
    return "NO TRADE"

# ---------- TICKERS ----------
tickers = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "RELIANCE": "RELIANCE.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "INFY": "INFY.NS"
}

# ---------- BUTTON ----------
if st.button("🚀 Run Auto Analysis"):

    news_list = fetch_news()

    st.subheader("📰 Latest News")
    for n in news_list:
        st.write("•", n)

    results = []

    for news in news_list:
        category, sentiment = analyze_news(news)

        for name, ticker in tickers.items():
            data = get_price(ticker)
            change = calculate_change(data)
            signal = generate_signal(sentiment, change)

            results.append({
                "Stock": name,
                "Change %": change,
                "Signal": signal,
                "Sentiment": sentiment
            })

    df = pd.DataFrame(results)

    # ---------- DISPLAY ----------
    st.subheader("📊 Market Signals")
    st.dataframe(df)

    # ---------- MARKET VIEW ----------
    pos = df[df["Change %"] > 0].shape[0]
    neg = df[df["Change %"] < 0].shape[0]

    st.subheader("📈 Market View")

    if pos > neg:
        st.success("Bullish Market 🚀")
    elif neg > pos:
        st.error("Bearish Market 📉")
    else:
        st.warning("Neutral Market ⚖️")