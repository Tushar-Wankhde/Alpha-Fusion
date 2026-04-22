
import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# ---------- CONFIG ----------
st.set_page_config(page_title="Alpha Fusion Pro", layout="wide")

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
body {
    background-color: #0f172a;
    color: white;
}
.stButton>button {
    background-color: #22c55e;
    color: white;
    font-size: 18px;
    border-radius: 10px;
    padding: 10px 20px;
}
.card {
    background-color: #1e293b;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------- TITLE ----------
st.markdown("<h1 style='text-align:center;'>🚀 Alpha Fusion Pro</h1>", unsafe_allow_html=True)

# 🔑 API KEY
API_KEY = "6dc3a37840ff480b97ad7ac869f9652b"

# ---------- NEWS FETCH ----------
def fetch_news():
    url = f"https://newsapi.org/v2/top-headlines?category=business&country=in&apiKey={API_KEY}"
    res = requests.get(url).json()
    return [a["title"] for a in res.get("articles", [])[:5]]

# ---------- SENTIMENT ----------
def analyze_news(news):
    news = news.lower()

    positive_words = ["growth", "profit", "rise", "gain", "bullish"]
    negative_words = ["fall", "loss", "crash", "bearish", "decline"]

    score = 0
    for word in positive_words:
        if word in news:
            score += 1
    for word in negative_words:
        if word in news:
            score -= 1

    if score > 0:
        return "Positive"
    elif score < 0:
        return "Negative"
    return "Neutral"

# ---------- PRICE ----------
def get_change(ticker):
    try:
        data = yf.download(ticker, period="1d", interval="5m", progress=False)
        if data.empty:
            return 0
        start = float(data['Close'].iloc[0])
        end = float(data['Close'].iloc[-1])
        return round(((end - start) / start) * 100, 2)
    except:
        return 0

# ---------- SIGNAL ----------
def generate_signal(sentiment, change):
    if sentiment == "Positive" and change > 0.4:
        return "BUY"
    elif sentiment == "Negative" and change < -0.4:
        return "SELL"
    return "HOLD"

# ---------- TICKERS ----------
tickers = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "RELIANCE": "RELIANCE.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS"
}

# ---------- BUTTON ----------
if st.button("🚀 Run Smart Analysis"):

    news_list = fetch_news()

    if not news_list:
        st.error("❌ News fetch failed")
        st.stop()

    st.subheader("📰 Latest News")

    sentiments = []
    for n in news_list:
        sentiment = analyze_news(n)
        sentiments.append(sentiment)

        color = "green" if sentiment == "Positive" else "red" if sentiment == "Negative" else "gray"

        st.markdown(f"<div class='card'>🔹 {n}<br><b style='color:{color}'>{sentiment}</b></div>", unsafe_allow_html=True)

    # ---------- STOCK ANALYSIS ----------
    results = []

    for name, ticker in tickers.items():
        change = get_change(ticker)

        # overall sentiment majority
        sentiment = max(set(sentiments), key=sentiments.count)

        signal = generate_signal(sentiment, change)

        results.append({
            "Stock": name,
            "Change %": change,
            "Signal": signal
        })

    df = pd.DataFrame(results)

    # ---------- METRICS ----------
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Stocks", len(df))
    col2.metric("Avg Change %", round(df["Change %"].mean(), 2))
    col3.metric("Best Performer", df.sort_values("Change %", ascending=False).iloc[0]["Stock"])

    # ---------- TABLE ----------
    st.subheader("📊 Market Signals")
    st.dataframe(df, use_container_width=True)

    # ---------- MARKET VIEW ----------
    pos = df[df["Change %"] > 0].shape[0]
    neg = df[df["Change %"] < 0].shape[0]

    st.subheader("📈 Market Trend")

    if pos > neg:
        st.success("🚀 Bullish Market")
    elif neg > pos:
        st.error("📉 Bearish Market")
    else:
        st.warning("⚖️ Sideways Market")