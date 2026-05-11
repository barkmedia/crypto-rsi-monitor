import streamlit as st
import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

st.set_page_config(page_title="My Holdings Monitor", layout="wide", page_icon="📈")

# ====================== LOGIN ======================
if "config" not in st.session_state:
    config = {
        'credentials': {
            'usernames': {
                'user': {
                    'email': 'YOUR_EMAIL@gmail.com',      # ← CHANGE THIS
                    'name': 'Your Name',
                    'password': stauth.Hasher(['yourpassword123']).generate()[0]
                }
            }
        },
        'cookie': {'expiry_days': 30, 'key': 'holdings2026', 'name': 'holdings_auth'}
    }
    with open('users.yaml', 'w') as file:
        yaml.dump(config, file)

authenticator = stauth.Authenticate(
    config['credentials'], config['cookie']['name'],
    config['cookie']['key'], config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login()

if not authentication_status:
    st.stop()

user_email = config['credentials']['usernames'][username]['email']
st.sidebar.success(f"Welcome, {name}!")

# ====================== SIMPLE EMAIL ALERT ======================
def send_simple_alert(symbol, rsi, price):
    if rsi > 70:
        sentiment = "Bullish 🔥"
    elif rsi < 30:
        sentiment = "Bearish 🟢"
    else:
        sentiment = "Neutral ⚖️"

    try:
        sender = "YOUR_EMAIL@gmail.com"           # ← CHANGE
        app_password = "YOUR_GMAIL_APP_PASSWORD"  # ← CHANGE (Gmail App Password)

        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = user_email
        msg['Subject'] = f"Your {symbol} holding is {sentiment}"

        body = f"""
        <h2>📊 Holdings Update</h2>
        <p><strong>{symbol}</strong></p>
        <p>Current Price: ${{price:,.4f if price < 10 else :,.2f}}</p>
        <p>RSI: <strong>{rsi:.1f}</strong></p>
        <p><strong>Sentiment: {sentiment}</strong></p>
        <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <hr>
        <small>Your personal RSI Monitor</small>
        """
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, app_password)
        server.sendmail(sender, user_email, msg.as_string())
        server.quit()
        return True
    except:
        return False

# ====================== YOUR ASSETS ======================
assets = ["BTC", "ETH", "SOL", "DOGE", "XRP", "BNB", "ZEC", "PEPE", "TSLA", "GME", "MSTR"]
tickers = {a: f"{a}-USD" if a in ["BTC","ETH","SOL","DOGE","XRP","BNB","ZEC"] else a for a in assets}
tickers["PEPE"] = "PEPE24478-USD"

st.title("📈 My Holdings RSI Monitor")
st.caption("Simple Bullish / Neutral / Bearish alerts sent to your email")

if st.button("🔄 Refresh & Send Alerts"):
    st.cache_data.clear()

cols = st.columns(4)

for i, symbol in enumerate(assets):
    with cols[i % 4]:
        try:
            df = yf.download(tickers[symbol], period="3mo", progress=False)
            if df.empty: continue

            price = float(df['Close'][-1])
            change = ((price - float(df['Close'][-2])) / float(df['Close'][-2])) * 100 if len(df) > 1 else 0

            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = -delta.where(delta < 0, 0).rolling(14).mean()
            rs = gain / loss
            rsi = float((100 - (100 / (1 + rs)))[-1])

            # Send simple alert
            if send_simple_alert(symbol, rsi, price):
                st.success(f"📧 Alert sent for {symbol}")
            else:
                st.info(f"Alert for {symbol} (check email setup)")

            st.metric(
                label=f"{symbol} • ${{price:,.4f if price < 10 else :,.2f}}",
                value=f"{change:+.2f}%",
                delta=f"RSI {rsi:.1f} • {'Bullish 🔥' if rsi > 70 else 'Bearish 🟢' if rsi < 30 else 'Neutral ⚖️'}"
            )

        except:
            st.write(f"Loading {symbol}...")

st.info("Click Refresh to get new alerts. Update YOUR_EMAIL and Gmail App Password in the code.")

authenticator.logout('Logout', 'sidebar')