# 📊 Borsa Analiz Botu - Otomatik Hisse Önerisi

Dünya haberlerini ve teknik analizi birleştiren, her gün size en iyi 1-3 hisse öneren tamamen otomatik sistem.

## 🎯 Özellikler

✅ **Haber Analizi** - NewsAPI ile dünya haberlerini çeker ve sentiment analizi yapar  
✅ **Teknik Analiz** - RSI, MACD, Bollinger Band, Fibonacci, SMA hesaplar  
✅ **Akıllı Skor** - Haber + Teknik analizi birleştirerek nihai skor üretir  
✅ **Sektör Çeşitlendirme** - Aynı sektörden birden fazla hisse seçmez  
✅ **Profesyonel Grafikler** - Her hisse için detaylı teknik analiz grafiği  
✅ **Günlük Email** - Sonuçları HTML formatında mail atar  
✅ **Tamamen Ücretsiz** - GitHub Actions ile 7/24 otomatik çalışır  
✅ **Mobil Uyumlu** - iPhone/iPad'den kurulur ve yönetilir  

## 📱 Mobil Kurulum (15 dakika)

### Gereksinimler
- Gmail hesabı
- [NewsAPI](https://newsapi.org/register) anahtarı (ücretsiz)
- [Gmail App Password](https://myaccount.google.com/apppasswords)
- GitHub hesabı

### Hızlı Başlangıç

1. **Bu repo'yu fork edin** (sağ üstte Fork butonu)

2. **Secrets ekleyin** → Settings → Secrets and variables → Actions
   ```
   NEWS_API_KEY       = (newsapi.org'dan)
   MAIL_SENDER        = sizin@gmail.com
   MAIL_PASSWORD      = (gmail app password)
   MAIL_RECIPIENT     = alici@gmail.com
   ```

3. **Aktif edin** → Actions → Enable workflows

4. **Manuel test** → Borsa Bot - Günlük Analiz → Run workflow

5. **Mail'inizi kontrol edin!** (5-10 dakika içinde gelir)

Detaylı kurulum: [HIZLI_BASLANGIC.txt](HIZLI_BASLANGIC.txt)

## 🔧 Özelleştirme

### Hisse Listesi Değiştirme
`config.py` dosyasını düzenleyin:
```python
TURKISH_STOCKS = [
    "THYAO.IS",  # Türk Hava Yolları
    "ASELS.IS",  # Aselsan
    # Yeni hisseler ekleyin...
]
```

### Çalışma Saati
`.github/workflows/daily_analysis.yml`:
```yaml
cron: '0 6 * * 1-5'  # Her gün 09:00 TR (6 UTC)
```

## 📊 Mail İçeriği Örneği

```
📊 Borsa Analiz Raporu
01 Şubat 2026 | Günlük Analiz

Piyasa Duygusu: 🟢 Olumlu

🎯 Bugün Önerilen Hisseler (3 adet)

#1 THYAO.IS - 🔥 GÜÇLÜ AL
Skor: 78/100 | Fiyat: 245.50
→ RSI 42.3 → Düşük Bölge
→ MACD → Bullish Crossover
→ Bollinger → Alt Bant Yakınında
Risk: -8.5% | Potansiyel: +15.2%

[Detaylı Teknik Grafik Ektedir]
```

## 🏗️ Sistem Mimarisi

```
┌─────────────────────┐
│   NewsAPI           │ → Haber Çekme
│   (Sentiment)       │ → Sektörel Analiz
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   yfinance          │ → Hisse Verileri
│   (Technical)       │ → RSI, MACD, BB, Fib
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Master Scorer     │ → Skor Hesaplama
│                     │ → Sektör Filtresi
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Chart Generator   │ → Grafik Üretimi
│   + Mail Sender     │ → HTML Email
└─────────────────────┘
```

## 📝 Dosya Yapısı

```
borsa_bot/
├── config.py              # Tüm ayarlar
├── news_analyzer.py       # Haber analizi
├── technical_analyzer.py  # Teknik analiz
├── scorer.py              # Master skor
├── chart_generator.py     # Grafik üretimi
├── mail_sender.py         # Email sistemi
├── main_bot.py            # Ana orchestrator
├── requirements.txt       # Python paketleri
├── .github/workflows/     # GitHub Actions
│   └── daily_analysis.yml
└── README.md              # Bu dosya
```

## 📊 Performans Takibi & Backtesting

Sistem artık her önerinin performansını otomatik takip eder!

### Otomatik Takip
- ✅ Her gün yapılan öneriler SQLite DB'ye kaydedilir
- ✅ 7, 14, 30 gün sonra gerçek sonuçlar kontrol edilir
- ✅ Başarı oranı, ortalama getiri hesaplanır
- ✅ Her Pazartesi haftalık performans raporu mail'e gelir

### Manuel Kontrol

**Performans raporu görüntüle:**
```bash
python check_performance.py --report --days 30
```

**Geçmiş önerileri görüntüle:**
```bash
python check_performance.py --history --limit 20
```

**Performansları yeniden hesapla:**
```bash
python check_performance.py --check
```

**Raporu email olarak gönder:**
```bash
python check_performance.py --report --email
```

### Backtesting (Geçmişe Dönük Test)

Sistemi geçmiş verilerde test ederek gerçek başarı oranını görebilirsiniz:

**Son 90 günü test et:**
```bash
python backtest.py --days 90
```

**Belirli tarih aralığı:**
```bash
python backtest.py --start 2024-01-01 --end 2025-01-01
```

**Sadece belirli hisseleri test et:**
```bash
python backtest.py --days 60 --tickers THYAO.IS ASELS.IS AAPL
```

### Performans Metrikleri

Sistem şu metrikleri hesaplar:
- **Win Rate**: Başarılı işlem yüzdesi (>%5 kazanç)
- **Average Return**: Ortalama getiri yüzdesi
- **Risk/Reward Ratio**: Başarılı işlem getirisi / Zararlı işlem kaybı
- **Best/Worst Sector**: En iyi ve en kötü performans gösteren sektörler
- **Hit Rate**: Fibonacci direnç/destek seviyelerine ulaşma oranı

### Örnek Performans Raporu

```
📊 PERFORMANS RAPORU - Son 30 Gün

📈 GENEL İSTATİSTİKLER:
   Toplam Öneri      : 45
   Kontrol Edilen    : 38
   Başarılı          : 24 ✅
   Nötr              : 8 ⚖️
   Zarar             : 6 ❌

🎯 BAŞARI ORANI:
   63.2% 🔥 (MÜKEMMEL)

💰 ORTALAMA GETİRİ:
   +4.8% 📈

🏆 SEKTÖR ANALİZİ:
   En İyi Sektör     : teknoloji
   En Kötü Sektör    : finans
```

## 🧪 Lokal Test

```bash
# Paketleri kur
pip install -r requirements.txt

# API anahtarlarını config.py'ye ekle

# Hızlı test (2 hisse)
python main_bot.py --mode test

# Tam analiz
python main_bot.py --mode run

# Otomatik zamanlayıcı
python main_bot.py --mode schedule
```

## 💰 Maliyetler

| Servis | Ücret | Limit |
|--------|-------|-------|
| GitHub Actions | **Ücretsiz** | 2000 dk/ay |
| NewsAPI | **Ücretsiz** | 100 çağrı/gün |
| yfinance | **Ücretsiz** | Sınırsız |
| Gmail SMTP | **Ücretsiz** | 500 mail/gün |

**Toplam: 0 TL** ✅

## ⚠️ Yasal Uyarı

Bu sistem otomatik analiz yapar ve **yatırım tavsiyesi değildir**.

- Geçmiş performans gelecek sonuçların garantisi değildir
- Borsa işlemleri ciddi risk taşır
- Kendi araştırmanızı yapın
- Profesyonel danışman ile görüşün

## 📚 Dokümantasyon

- [Hızlı Başlangıç](HIZLI_BASLANGIC.txt) - 15 dakikada kurulum
- [Mobil Kurulum](MOBIL_KURULUM.txt) - iPhone/iPad detayları
- [Pythonista Rehberi](PYTHONISTA_REHBERI.txt) - iPad'de lokal çalıştırma
- [Tam Kurulum](KURULUM_REHBERI.txt) - Detaylı açıklamalar

## 🤝 Katkıda Bulunma

Pull request'ler kabul edilir! Önerileriniz için Issues açabilirsiniz.

## 📄 Lisans

MIT License - Özgürce kullanın, değiştirin, paylaşın.

## 🌟 Destekleyin

Faydalı bulduysanız ⭐ verin, arkadaşlarınızla paylaşın!

---

**Yapımcı:** Ahmet Çağıl
**Versiyon:** 1.0  
**Son Güncelleme:** Şubat 2026
