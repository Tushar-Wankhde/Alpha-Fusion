import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import joblib
import time
from tensorflow.keras.models import load_model

# ---------------- PAGE ----------------
st.set_page_config(page_title="Alpha Fusion PRO", layout="wide")

# ---------------- CSS ----------------
st.markdown("""
<style>
.stApp {background:#0b0f1a; color:white;}
.title {
    font-size:42px;
    text-align:center;
    font-weight:900;
    background:linear-gradient(90deg,#00ff99,#00ccff,#ff00ff);
    -webkit-background-clip:text;
    color:transparent;
}
.card {
    background:#121a2b;
    padding:18px;
    border-radius:15px;
    margin:10px 0;
    box-shadow:0px 0px 15px rgba(0,255,200,0.15);
}
.btn {
    background:linear-gradient(90deg,#00ff99,#00ccff);
    padding:10px;
    border-radius:10px;
    text-align:center;
    font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>🚀 ALPHA FUSION PRO AI TRADING</div>", unsafe_allow_html=True)

# ---------------- LOAD MODELS ----------------
try:
    model = load_model("lstm_model.keras")
    scaler = joblib.load("scaler.save")
except:
    model = None
    scaler = None

# ---------------- SESSION ----------------
if "trades" not in st.session_state:
    st.session_state.trades = []

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ CONTROL PANEL")

symbol = st.sidebar.selectbox("Index", ["^NSEI", "^NSEBANK", "^BSESN"])
capital = st.sidebar.number_input("Capital", 100000)
risk = st.sidebar.slider("Risk %", 1, 5, 2)

# ---------------- DATA ----------------
def get_data(tf):
    df = yf.download(symbol, period="5d", interval=tf, progress=False)
    return df.dropna()

df5 = get_data("5m")
df15 = get_data("15m")
df1h = get_data("60m")

if df5.empty:
    st.error("No Data Found")
    st.stop()

price = float(df5["Close"].iloc[-1])

# ---------------- CHART ----------------
fig = go.Figure(data=[go.Candlestick(
    x=df5.index,
    open=df5["Open"],
    high=df5["High"],
    low=df5["Low"],
    close=df5["Close"]
)])
fig.update_layout(template="plotly_dark", height=450)

st.plotly_chart(fig, use_container_width=True)

# ---------------- INDICATORS ----------------
def rsi(df):
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    return 100 - (100/(1+rs))

rsi_val = float(rsi(df5).iloc[-1])
trend = "UP" if df5["Close"].iloc[-1] > df5["Close"].iloc[0] else "DOWN"

# ---------------- LSTM ----------------
def lstm_signal(df):
    if model is None:
        return "NO MODEL", 0

    data = df["Close"].values[-60:]
    if len(data) < 60:
        return "NO DATA", 0

    data = scaler.transform(data.reshape(-1,1))
    X = np.array(data).reshape(1,60,1)

    pred = model.predict(X, verbose=0)
    pred_price = scaler.inverse_transform(pred)[0][0]

    change = ((pred_price - price)/price)*100

    if change > 0.3:
        return "BUY", change
    elif change < -0.3:
        return "SELL", change
    return "WAIT", change

lstm_sig, lstm_conf = lstm_signal(df5)

# ---------------- FINAL ENGINE ----------------
score = 0

if trend == "UP": score += 2
else: score -= 2

if rsi_val > 60: score += 2
elif rsi_val < 40: score -= 2

if lstm_sig == "BUY": score += 3
elif lstm_sig == "SELL": score -= 3

if score >= 4:
    final_signal = "STRONG BUY 🚀"
elif score <= -4:
    final_signal = "STRONG SELL 🔻"
else:
    final_signal = "WAIT ⚠️"

# ---------------- RISK ----------------
sl = price * 0.995
target = price * 1.01
risk_amt = capital * (risk/100)
qty = int(risk_amt / abs(price - sl))

# ---------------- DASHBOARD ----------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"<div class='card'><h3>Price</h3><h2>{price:.2f}</h2></div>", unsafe_allow_html=True)

with col2:
    st.markdown(f"<div class='card'><h3>Trend</h3><h2>{trend}</h2></div>", unsafe_allow_html=True)

with col3:
    st.markdown(f"<div class='card'><h3>RSI</h3><h2>{rsi_val:.2f}</h2></div>", unsafe_allow_html=True)

# ---------------- FINAL SIGNAL ----------------
st.markdown(f"""
<div class='card'>
<h2>🤖 FINAL AI SIGNAL</h2>
<h1>{final_signal}</h1>
<p>LSTM: {lstm_sig} ({lstm_conf:.2f}%)</p>
<p>Score: {score}</p>
<p>Suggested Qty: {qty}</p>
<p>SL: {sl:.2f} | Target: {target:.2f}</p>
</div>
""", unsafe_allow_html=True)

# ---------------- TRADE BUTTON ----------------
if st.button("🚀 EXECUTE TRADE"):
    st.session_state.trades.append({
        "symbol": symbol,
        "entry": price,
        "sl": sl,
        "target": target,
        "qty": qty,
        "status": "OPEN"
    })
    st.success("Trade Executed!")

# ---------------- TRADE HISTORY ----------------
st.subheader("📊 Trade History")

for t in st.session_state.trades:
    pnl = (price - t["entry"]) * t["qty"]

    st.write({
        "Symbol": symbol,
        "Entry": t["entry"],
        "Current": price,
        "P&L": round(pnl,2),
        "Status": t["status"]
    })

# ---------------- AUTO REFRESH ----------------
time.sleep(10)
st.rerun()