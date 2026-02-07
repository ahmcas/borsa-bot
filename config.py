# ============================================================
# config.py — Tüm Ayarlar (SendGrid Uyumlu)
# ============================================================
import os

# --- API ANAHTARLARI ---
# GitHub Secrets'tan okunur, yoksa tırnak içindeki değerler kullanılır
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "YOUR_NEWS_API_KEY_HERE")
ALPHA_VANTAGE_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "YOUR_ALPHA_VANTAGE_KEY_HERE")

# SendGrid API Anahtarı (Loglardaki hatayı çözen kritik satır)
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "YOUR_SENDGRID_API_KEY_HERE")

# --- MAIL AYARLARI ---
# İsteğiniz üzerine adresler ahm.cagil@hotmail.com olarak güncellendi
MAIL_SENDER = os.environ.get("MAIL_SENDER", "ahm.cagil@hotmail.com")
MAIL_RECIPIENT = os.environ.get("MAIL_RECIPIENT", "ahm.cagil@hotmail.com")

# --- BORSALAR & HISSELER ---
TURKISH_STOCKS = [
    "THYAO.IS", "ASELS.IS", "AKBANK.IS", "ISCTR.IS", "GARAN.IS", 
    "AKSEN.IS", "TUPRS.IS", "BIMAS.IS", "ENKAI.IS", "SISE.IS", 
    "TOASO.IS", "FROTO.IS", "OTKAR.IS", "SAHOL.IS", "DOAS.IS", 
    "EKGYO.IS", "TTKOM.IS", "TCELL.IS"
]

GLOBAL_STOCKS = [
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "JPM", "XOM", "NEE", "UNH"
]

ALL_STOCKS = TURKISH_STOCKS + GLOBAL_STOCKS

# --- ANALIZ PARAMETRELERI ---
FIBONACCI_LEVELS = [0.236, 0.382, 0.500, 0.618, 0.786]
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20
SMA_SHORT = 20
SMA_LONG = 50

# Skor ağırlıkları
WEIGHT_TECHNICAL = 40
WEIGHT_FUNDAMENTAL = 30
WEIGHT_NEWS_SENTIMENT = 20
WEIGHT_MOMENTUM = 10

# --- ZAMANLAMA ---
DAILY_RUN_HOUR = 9
DAILY_RUN_MINUTE = 30
