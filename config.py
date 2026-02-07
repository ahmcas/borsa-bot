import os

# --- API ANAHTARLARI ---
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
ALPHA_VANTAGE_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "")
# Bu satır SendGrid hatasını çözer
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "") 

# --- MAIL AYARLARI ---
# İsteğiniz üzerine adresler sabitlendi
MAIL_SENDER = os.environ.get("MAIL_SENDER", "ahm.cagilgmail.com")
MAIL_RECIPIENT = os.environ.get("MAIL_RECIPIENT", "ahm.cagil@gmail.com")

# --- BORSALAR & HISSELER ---
# Hatalı Yahoo Finance kodları (ISA, TUPAS vb.) düzeltildi
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

# Skor ağırlıkları
WEIGHT_TECHNICAL, WEIGHT_FUNDAMENTAL = 40, 30
WEIGHT_NEWS_SENTIMENT, WEIGHT_MOMENTUM = 20, 10

DAILY_RUN_HOUR, DAILY_RUN_MINUTE = 9, 30
