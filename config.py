# ============================================================
# config.py — Tüm Ayarlar (SendGrid & Algoritmik Tarama)
# ============================================================
import os

# --- API ANAHTARLARI ---
# GitHub Secrets'tan okunur. Loglardaki 'attribute' hatasını bu satır çözer.
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
ALPHA_VANTAGE_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "")

# --- MAIL AYARLARI ---
# Yeni güncellenen adresiniz: ahm.cagil@gmail.com
MAIL_SENDER = os.environ.get("MAIL_SENDER", "ahm.cagil@gmail.com")
MAIL_RECIPIENT = os.environ.get("MAIL_RECIPIENT", "ahm.cagil@gmail.com")

# --- BORSALAR & HISSELER ---
# Yahoo Finance formatına uygun (ISA -> ISCTR, TUPAS -> TUPRS) düzeltilmiş liste.
TURKISH_STOCKS = [
    "THYAO.IS", "ASELS.IS", "AKBANK.IS", "ISCTR.IS", "GARAN.IS", 
    "AKSEN.IS", "TUPRS.IS", "BIMAS.IS", "ENKAI.IS", "SISE.IS", 
    "TOASO.IS", "FROTO.IS", "OTKAR.IS", "SAHOL.IS", "DOAS.IS", 
    "EKGYO.IS", "TTKOM.IS", "TCELL.IS", "AKSA.IS"
]

GLOBAL_STOCKS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]
ALL_STOCKS = TURKISH_STOCKS + GLOBAL_STOCKS

# --- ANALIZ PARAMETRELERI ---
FIBONACCI_LEVELS = [0.236, 0.382, 0.500, 0.618, 0.786]
RSI_PERIOD = 14
MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9
BOLLINGER_PERIOD = 20
SMA_SHORT, SMA_LONG = 20, 50

# Skor ağırlıkları (Toplam = 100)
WEIGHT_TECHNICAL = 40   # Teknik analiz ağırlığı
WEIGHT_FUNDAMENTAL = 30 # Temel analiz ağırlığı
WEIGHT_NEWS_SENTIMENT = 20 # Haber analiz ağırlığı
WEIGHT_MOMENTUM = 10    # Momentum ağırlığı

# --- ZAMANLAMA ---
DAILY_RUN_HOUR = 9
DAILY_RUN_MINUTE = 30
