import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ccxt

def calculate_vpmv(df):
    df['price_raw'] = (df['close'] / df['close'].shift(10) - 1.0) * 100
    change = df['close'].diff()
    up, down = change.clip(lower=0), -1 * change.clip(upper=0)
    ma_up, ma_down = up.rolling(14).mean(), down.rolling(14).mean()
    df['mom_rsi'] = 100 - (100 / (1 + (ma_up / ma_down)))
    df['vol_score'] = (df['volume'] - df['volume'].rolling(20).min()) / (df['volume'].rolling(20).max() - df['volume'].rolling(20).min()) * 100
    z_p = np.tanh(df['price_raw'] / 4.0)
    z_v = np.tanh((df['vol_score'] - 50.0) / 20.0)
    z_m = np.tanh((df['mom_rsi'] - 50.0) / 20.0)
    vpmv = 50.0 + 50.0 * (0.70 * z_p + 0.15 * z_v + 0.15 * z_m)
    return vpmv.clip(0, 100)

st.set_page_config(layout="wide", page_title="VPMV Scanner")
st.title("VPMV Real-Time Scanner")

symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ARB/USDT', 'AVAX/USDT', 'OP/USDT', 'MATIC/USDT', 'LINK/USDT', 'SUI/USDT', 'TIA/USDT', 'APT/USDT', 'RNDR/USDT']

if st.button('Piyasayı Tara ve Ayrışanları Göster'):
    all_vpmv = {}
    ex = ccxt.binance({'options': {'defaultType': 'future'}})
    for s in symbols:
        try:
            ohlcv = ex.fetch_ohlcv(s, timeframe='1h', limit=100)
            df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
            all_vpmv[s] = calculate_vpmv(df)
        except: 
            continue

    fig = go.Figure()
    for s, data in all_vpmv.items():
        if s == 'BTC/USDT':
            fig.add_trace(go.Scatter(y=data, name=s, line=dict(color='yellow', width=6)))
        else:
            diff = data.iloc[-1] - all_vpmv['BTC/USDT'].iloc[-1]
            color = 'lime' if diff > 15 else 'rgba(150,150,150,0.3)'
            fig.add_trace(go.Scatter(y=data, name=s, line=dict(color=color, width=3 if diff > 15 else 1)))
    
    fig.update_layout(template="plotly_dark", height=700, yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig, use_container_width=True)
