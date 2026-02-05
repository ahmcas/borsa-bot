# ============================================================
# config.py — Tüm ayarlar burada
# ============================================================
# Bu dosyada API anahtarlarını ve mail ayarlarını doldurun.
# ============================================================

import os

# --- API ANAHTARLARI ---
# NewsAPI için ücretsiz anahtar: https://newsapi.org/register
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "YOUR_NEWS_API_KEY_HERE")

# Alpha Vantage için ücretsiz anahtar: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "YOUR_ALPHA_VANTAGE_KEY_HERE")

# --- MAIL AYARLARI (Gmail) ---
# Gmail'de 2FA açıksa → App Password yoluyla yeni şifre oluştur
# https://myaccount.google.com/apppasswords
MAIL_SENDER = os.environ.get("MAIL_SENDER", "senin_gmail_adresin@gmail.com")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "APP_PASSWORD_BURAYA")
MAIL_RECIPIENT = os.environ.get("MAIL_RECIPIENT", "alici_adres@gmail.com")  # kendin için aynı adres olabilir

# --- BORSALAR & HISSELER ---
# Yahoo Finance ticker formatı:
# Türkiye → XYZ.IS   (örn: AAPL.IS, THYAO.IS)
# ABD     → XYZ      (örn: AAPL, MSFT)
# Almanya → XYZ.DE
# Hindistan → XYZ.NS

TURKISH_STOCKS = [
    "THYAO.IS",  # Türk Hava Yolları
    "ASELS.IS",  # Aselsan
    "AKBANK.IS", # Akbank
    "ISA.IS",    # İş Bankası
    "GARAN.IS",  # Garanti BBVA
    "AKSA.IS",   # Aksa Enerji
    "TUPAS.IS",  # Türkiye Petrol
    "BLDYR.IS",  # Bilder
    "ENKA.IS",   # Enka
    "SISE.IS",   # Şişecam
    "TOASY.IS",  # Toasan
    "FROTO.IS",  # Ford Otomotiv
    "OTKAR.IS",  # Otokar
    "SAHOL.IS",  # Şaholding
    "DOAS.IS",   # Doğa Sigorta
    "EKGYO.IS",  # Emlak Konut
    "TTKOM.IS",  # Türk Telekom
    "TCELL.IS",  # Turkcell
]

GLOBAL_STOCKS = [
    "AAPL",   # Apple
    "MSFT",   # Microsoft
    "NVDA",   # Nvidia
    "TSLA",   # Tesla
    "AMZN",   # Amazon
    "GOOGL",  # Google
    "JPM",    # JPMorgan
    "XOM",    # Exxon Mobil
    "NEE",    # NextEra Energy
    "UNH",    # UnitedHealth
]

ALL_STOCKS = TURKISH_STOCKS + GLOBAL_STOCKS

# --- ANALIZ PARAMETRELERI ---
# Fibonacci seviyeler (yüzde olarak)
FIBONACCI_LEVELS = [0.236, 0.382, 0.500, 0.618, 0.786]

# Teknik indikatör dönemleri
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20
SMA_SHORT = 20
SMA_LONG = 50

# Skor ağırlıkları (toplam = 100)
WEIGHT_TECHNICAL = 40   # Teknik analiz ağırlığı
WEIGHT_FUNDAMENTAL = 30 # Temel analiz ağırlığı
WEIGHT_NEWS_SENTIMENT = 20 # Haber analiz ağırlığı
WEIGHT_MOMENTUM = 10    # Momentum ağırlığı

# --- ZAMANLAMA ---
# Her gün saat kaç'ta analiz yapılsın (24h format)
DAILY_RUN_HOUR = 9
DAILY_RUN_MINUTE = 30
