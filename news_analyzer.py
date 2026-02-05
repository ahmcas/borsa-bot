# ============================================================
# news_analyzer.py — Haber Çekme & Sentiment Analizi
# ============================================================
# Bu modül:
# 1) Dünya haberlerini çeker
# 2) Her haberi sektörlerle ilişkilendirir
# 3) Pozitif/Negatif skor atar
# 4) Sektörel tahmin üretir
# ============================================================

import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict
import config

# Sektörler ve anahtar kelimeler eşleştirmesi
SECTOR_KEYWORDS = {
    "teknoloji": [
        "technology", "tech", "semiconductor", "AI", "artificial intelligence",
        "software", "cyber", "digital", "cloud", "chip", "gpu", "nvidia",
        "microsoft", "apple", "google", "teknoloji", "yapay zeka", "dijital"
    ],
    "enerji": [
        "oil", "energy", "petroleum", "crude", "OPEC", "natural gas",
        "renewable", "solar", "wind", "coal", "petrol", "enerji",
        "yenilenebilir", "güneş", "rüzgar"
    ],
    "finans": [
        "bank", "banking", "finance", "interest rate", "central bank",
        "Fed", "ECB", "inflation", "monetary", "credit", "banka",
        "faiz", "merkez bankası", "enflasyon", "finansal"
    ],
    "otomotiv": [
        "automotive", "car", "vehicle", "auto", "EV", "electric vehicle",
        "tesla", "ford", "otomotiv", "araba", "elektrikli araç"
    ],
    "sağlık": [
        "health", "pharma", "pharmaceutical", "FDA", "vaccine", "hospital",
        "medical", "biotech", "drug", "sağlık", "ilaç", "hastane"
    ],
    "telekom": [
        "telecom", "5G", "mobile", "network", "communication",
        "telekom", "5G", "mobil", "iletişim"
    ],
    "inşaat_gayrimenkul": [
        "real estate", "construction", "housing", "property", "mortgage",
        "gayrimenkul", "inşaat", "konut", "mortgage"
    ],
    "sigortalar": [
        "insurance", "sigorta", "claim", "policy", "reinsurance"
    ],
    "enerji_uluslararası": [
        "OPEC", "Brent", "WTI", "oil price", "fuel", "petro-dollar"
    ],
    "savunma": [
        "defense", "military", "NATO", "weapon", "defense spending",
        "savunma", "askeri", "NATO silah"
    ]
}

# Pozitif ve negatif kelimeler (Türkçe + İngilizce)
POSITIVE_WORDS = [
    "growth", "increase", "profit", "record", "surge", "rally", "boom",
    "strong", "bullish", "gain", "rise", "up", "positive", "good",
    "artış", "kazanç", "rekor", "güçlü", "yükseliş", "olumlu",
    "büyüme", "kar", "başarı", "mükemmel"
]

NEGATIVE_WORDS = [
    "decline", "drop", "fall", "loss", "crash", "recession", "bear",
    "weak", "risk", "crisis", "negative", "bad", "sanctions", "war",
    "düşüş", "kayıp", "kriz", "risk", "zayıf", "negatif",
    "yavaşlama", "tehlike", "zarar", "kaygı"
]

NEUTRAL_INTENSIFIERS = [
    "significant", "major", "critical", "important",
    "önemli", "kritik", "büyük"
]


def fetch_news(query: str, lang: str = "en", count: int = 20) -> list:
    """NewsAPI'den haber çeker."""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": lang,
        "sortBy": "publishedAt",
        "pageSize": count,
        "from": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        "apiKey": config.NEWS_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("articles", [])
    except requests.RequestException as e:
        print(f"[NewsAPI] Hata: {e}")
        return []


def calculate_sentiment(text: str) -> dict:
    """
    Bir metin için sentiment skoru hesaplar.
    Döndürür: {"score": float, "label": str}
    Score: -1.0 (çok negatif) ile +1.0 (çok pozitif) arası
    """
    if not text:
        return {"score": 0.0, "label": "neutral"}

    text_lower = text.lower()
    words = text_lower.split()

    positive_count = 0
    negative_count = 0

    for word in words:
        # Kelimelerin birini bile içerse say
        if any(pw in word for pw in POSITIVE_WORDS):
            positive_count += 1
        if any(nw in word for nw in NEGATIVE_WORDS):
            negative_count += 1

    # Yoğunlaştırıcı kelimeler varsa etkiyi 1.5x yap
    intensifier_found = any(
        any(intens in word for intens in NEUTRAL_INTENSIFIERS)
        for word in words
    )

    if intensifier_found:
        positive_count = int(positive_count * 1.5)
        negative_count = int(negative_count * 1.5)

    total = positive_count + negative_count
    if total == 0:
        return {"score": 0.0, "label": "neutral"}

    # -1 ile +1 arası normalize
    score = (positive_count - negative_count) / max(total, 1)
    score = max(-1.0, min(1.0, score))

    if score >= 0.2:
        label = "pozitif"
    elif score <= -0.2:
        label = "negatif"
    else:
        label = "tarafsız"

    return {"score": round(score, 3), "label": label}


def classify_sector(text: str) -> list:
    """
    Bir metin için ilgili sektörleri bulur.
    Döndürür: ilgili sektörler listesi
    """
    text_lower = text.lower()
    matched_sectors = []

    for sector, keywords in SECTOR_KEYWORDS.items():
        match_count = sum(1 for kw in keywords if kw.lower() in text_lower)
        if match_count >= 2:  # En az 2 anahtar kelime eşleşmeli
            matched_sectors.append((sector, match_count))

    # Match sayısına göre sort
    matched_sectors.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in matched_sectors[:3]]  # Max 3 sektör


def analyze_all_news() -> dict:
    """
    Ana analiz fonksiyonu.
    Tüm haberler çekilir, sektörlerine atanır, sentiment hesaplanır.
    Döndürür:
    {
        "sector_scores": {sektör: ortalama_score},
        "raw_news": [haberlerin detayları],
        "top_sectors": [en olumlu sektörler],
        "risk_sectors": [en riskli sektörler]
    }
    """
    # Çeşitli sorguyla haberler çek
    search_queries = [
        "global stock market economy 2025",
        "Turkey economy BIST stock market",
        "OPEC oil prices energy market",
        "technology stocks AI semiconductor",
        "Federal Reserve interest rate decision",
        "Turkey central bank interest rate",
        "NATO defense spending Europe",
        "global recession risk inflation",
        "Türkiye ekonomi borsa",
        "dünya piyasaları hisse"
    ]

    all_articles = []
    for query in search_queries:
        lang = "tr" if "Türkiye" in query or "borsa" in query else "en"
        articles = fetch_news(query, lang=lang, count=10)
        all_articles.extend(articles)

    # Sektörel skor hesaplama
    sector_scores = defaultdict(list)

    analyzed_news = []
    for article in all_articles:
        title = article.get("title", "")
        description = article.get("description", "")
        full_text = f"{title} {description}"

        # Sentiment hesapla
        sentiment = calculate_sentiment(full_text)

        # Sektörü bul
        sectors = classify_sector(full_text)

        # Eğer sektör bulunamadıysa "genel" ekle
        if not sectors:
            sectors = ["genel"]

        # Sektöre skoru ekle
        for sector in sectors:
            sector_scores[sector].append(sentiment["score"])

        analyzed_news.append({
            "title": title[:100],
            "sentiment": sentiment,
            "sectors": sectors,
            "source": article.get("source", {}).get("name", "bilinmiyor"),
            "url": article.get("url", "")
        })

    # Sektörel ortalama skor hesapla
    avg_sector_scores = {}
    for sector, scores in sector_scores.items():
        avg = sum(scores) / len(scores) if scores else 0
        avg_sector_scores[sector] = round(avg, 3)

    # En olumlu ve en riskli sektörler
    sorted_sectors = sorted(avg_sector_scores.items(), key=lambda x: x[1], reverse=True)
    top_sectors = [s for s in sorted_sectors if s[1] > 0][:3]
    risk_sectors = [s for s in sorted_sectors if s[1] < 0][:3]

    return {
        "sector_scores": avg_sector_scores,
        "raw_news": analyzed_news,
        "top_sectors": top_sectors,
        "risk_sectors": risk_sectors,
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M")
    }


if __name__ == "__main__":
    # Test çalıştırma
    print("📰 Haber analizi başlıyor...")
    result = analyze_all_news()

    print("\n📊 Sektörel Sonuçlar:")
    for sector, score in sorted(result["sector_scores"].items(), key=lambda x: x[1], reverse=True):
        emoji = "🟢" if score > 0 else "🔴" if score < 0 else "⚪"
        print(f"  {emoji} {sector:25s} → {score:+.3f}")

    print(f"\n🏆 En Olumlu Sektörler: {result['top_sectors']}")
    print(f"⚠️  Risk Taşıyan Sektörler: {result['risk_sectors']}")
