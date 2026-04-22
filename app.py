import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time

st.set_page_config(page_title="Alpha Fusion", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
body {background: #020617; color: white;}
.header {
    font-size:40px;
    font-weight:700;
    text-align:center;
    background: linear-gradient(90deg,#22c55e,#38bdf8);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}
.card {
    padding:20px;
    border-radius:15px;
    background:#1e293b;
}
.buy {color:#22c55e; font-size:22px;}
.sell {color:#ef4444; font-size:22px;}
.wait {color:#facc15; font-size:22px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header">🚀 Alpha Fusion</div>', unsafe_allow_html=True)
st.caption("Stable AI Trading Dashboard")

# ---------- SESSION ----------
if "trades" not in st.session_state:
    st.session_state.trades = []

# ---------- SAFE PRICE ----------
def get_price(symbol):
    try:
        df = yf.download(symbol, period="1d", interval="5m", progress=False)

        if df is None or df.empty or 'Close' not in df.columns:
            return None, None, None

        df = df.dropna()

        if len(df) < 2:
            return None, None, None

        first_price = float(df['Close'].iloc[0])
        last_price = float(df['Close'].iloc[-1])

        trend = "UP" if last_price > first_price else "DOWN"

        return df, round(last_price,2), trend

    except:
        return None, None, None

# ---------- RSI ----------
def get_rsi(df):
    try:
        delta = df['Close'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return round(float(rsi.iloc[-1]),2)
    except:
        return 50

# ---------- SAFE OI ----------
def get_atm_oi(symbol):
    try:
        if symbol not in ["NIFTY", "BANKNIFTY"]:
            return None, None

        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}

        s = requests.Session()
        s.get("https://www.nseindia.com", headers=headers, timeout=5)
        data = s.get(url, headers=headers, timeout=5).json()

        spot = data['records']['underlyingValue']
        records = data['records']['data']

        valid = [x for x in records if 'CE' in x and 'PE' in x]

        if not valid:
            return None, None

        closest = min(valid, key=lambda x: abs(x['strikePrice'] - spot))

        ce = closest['CE'].get('openInterest', 0)
        pe = closest['PE'].get('openInterest', 0)

        return ce, pe

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
        cols[i].warning("No Data")
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

        if st.button(f"Trade {name}"):
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

    if df is None:
        continue

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

if not df_pnl.empty:
    total = df_pnl["P&L"].sum()
    st.metric("Total P&L", round(total,2))

# ---------- CHART ----------
st.subheader("📈 Live Chart")

df_chart = yf.download("^NSEBANK", period="1d", interval="5m", progress=False)

if df_chart is not None and not df_chart.empty:
    st.line_chart(df_chart["Close"])
else:
    st.warning("Chart data not available")

# ---------- AUTO REFRESH ----------
time.sleep(10)
st.rerun()