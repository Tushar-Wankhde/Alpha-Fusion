import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time

st.set_page_config(page_title="Alpha Fusion", layout="wide")

# ---------- FULL UI CSS ----------
st.markdown("""
<style>

body {
    background: radial-gradient(circle at top, #020617, #000);
    color: white;
}

/* HEADER */
.header {
    font-size:45px;
    font-weight:800;
    text-align:center;
    background: linear-gradient(90deg,#22c55e,#38bdf8,#a855f7);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    margin-bottom:20px;
}

/* CARD */
.card {
    padding:25px;
    border-radius:20px;
    background: rgba(30,41,59,0.6);
    backdrop-filter: blur(15px);
    box-shadow: 0 0 25px rgba(0,0,0,0.7);
    transition: 0.3s;
}
.card:hover {
    transform: translateY(-5px) scale(1.02);
}

/* SIGNAL BADGES */
.buy {
    color:#22c55e;
    font-size:28px;
    font-weight:700;
}
.sell {
    color:#ef4444;
    font-size:28px;
    font-weight:700;
}
.wait {
    color:#facc15;
    font-size:28px;
    font-weight:700;
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(90deg,#22c55e,#16a34a);
    color:white;
    border:none;
    border-radius:12px;
    padding:10px 20px;
    font-size:16px;
    transition:0.3s;
}
.stButton>button:hover {
    transform: scale(1.05);
    box-shadow:0 0 15px #22c55e;
}

/* TABLE */
.css-1d391kg {
    border-radius:10px;
    overflow:hidden;
}

</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown('<div class="header">🚀 Alpha Fusion</div>', unsafe_allow_html=True)
st.caption("Next Gen AI Trading Dashboard")

# ---------- SESSION ----------
if "trades" not in st.session_state:
    st.session_state.trades = []

# ---------- PRICE ----------
def get_price(symbol):
    df = yf.download(symbol, period="1d", interval="5m", progress=False)
    if df.empty:
        return None, None, None
    
    price = df['Close'].iloc[-1]
    trend = "UP" if price > df['Close'].iloc[0] else "DOWN"

    return df, round(price,2), trend

# ---------- RSI ----------
def get_rsi(df):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    return round(100 - (100 / (1 + rs)).iloc[-1],2)

# ---------- OI ----------
def get_atm_oi(symbol):
    try:
        if symbol == "NIFTY":
            url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        elif symbol == "BANKNIFTY":
            url = "https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY"
        else:
            return None, None

        headers = {"User-Agent": "Mozilla/5.0"}
        s = requests.Session()
        s.get("https://www.nseindia.com", headers=headers)
        data = s.get(url, headers=headers).json()

        spot = data['records']['underlyingValue']
        closest = min(data['records']['data'], key=lambda x: abs(x['strikePrice'] - spot))

        return closest['CE']['openInterest'], closest['PE']['openInterest']
    except:
        return None, None

# ---------- SIGNAL ----------
def ai_signal(trend, rsi, ce, pe):

    if ce is None:
        return "WAIT", "wait"

    score = 0
    if trend == "UP": score += 1
    if rsi > 55: score += 1
    if pe > ce: score += 1

    if score >= 2:
        return "BUY 🚀", "buy"
    elif score == 0:
        return "SELL 🔻", "sell"

    return "WAIT ⚠️", "wait"

# ---------- MARKETS ----------
markets = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN"
}

cols = st.columns(3)

# ---------- CARDS ----------
for i, (name, ticker) in enumerate(markets.items()):

    df, price, trend = get_price(ticker)

    if df is None:
        continue

    rsi = get_rsi(df)
    ce, pe = get_atm_oi(name)
    signal, cls = ai_signal(trend, rsi, ce, pe)

    with cols[i]:
        st.markdown(f"""
        <div class="card">
            <h2>{name}</h2>
            <p>Price: {price}</p>
            <p>Trend: {trend}</p>
            <p>RSI: {rsi}</p>
            <p>CE: {ce}</p>
            <p>PE: {pe}</p>
            <div class="{cls}">{signal}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"⚡ Trade {name}"):
            st.session_state.trades.append({
                "Index": name,
                "Entry": price,
                "Type": signal
            })

# ---------- P&L ----------
st.subheader("💰 Live P&L")

pnl_data = []

for t in st.session_state.trades:
    ticker = markets[t["Index"]]
    df, price, _ = get_price(ticker)

    entry = t["Entry"]
    pnl = price - entry if "BUY" in t["Type"] else entry - price

    pnl_data.append({
        "Index": t["Index"],
        "Entry": entry,
        "Current": price,
        "Type": t["Type"],
        "P&L": round(pnl,2)
    })

df_pnl = pd.DataFrame(pnl_data)
st.dataframe(df_pnl, use_container_width=True)

# ---------- TOTAL ----------
if not df_pnl.empty:
    total = df_pnl["P&L"].sum()
    st.metric("🔥 Total P&L", round(total,2))

# ---------- CHART ----------
st.subheader("📈 Live Chart (BankNifty)")
df_chart = yf.download("^NSEBANK", period="1d", interval="5m", progress=False)
st.area_chart(df_chart["Close"])

# ---------- AUTO REFRESH ----------
time.sleep(10)
st.rerun()