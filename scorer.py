# ============================================================
# scorer.py — Master Scoring Engine
# ============================================================
# Bu modül:
# 1) Haber sentiment'i → Sektörsel skora çevirir
# 2) Teknik analizdeki her hisse skoru alır
# 3) İkisini birleştirip NIHAI skor hesaplar
# 4) En iyi 1-3 hisseyi seçer
# 5) Risk/reward analizi yapar
# ============================================================

import config
from collections import defaultdict


# Hisse → Sektör eşleştirmesi
TICKER_TO_SECTOR = {
    # Türk Borsa
    "THYAO.IS": "teknoloji",       # Havacılık → Tech/Transport
    "ASELS.IS": "savunma",         # Savunma
    "AKBANK.IS": "finans",         # Bankacılık
    "ISA.IS": "finans",            # Bankacılık
    "GARAN.IS": "finans",          # Bankacılık
    "AKSA.IS": "enerji",           # Enerji
    "TUPAS.IS": "enerji",          # Petrol
    "BLDYR.IS": "inşaat_gayrimenkul",
    "ENKA.IS": "inşaat_gayrimenkul",
    "SISE.IS": "teknoloji",        # Cam/Materyal
    "TOASY.IS": "inşaat_gayrimenkul",
    "FROTO.IS": "otomotiv",
    "OTKAR.IS": "otomotiv",
    "SAHOL.IS": "finans",          # Holding
    "DOAS.IS": "sigortalar",
    "EKGYO.IS": "inşaat_gayrimenkul",
    "TTKOM.IS": "telekom",
    "TCELL.IS": "telekom",

    # Global
    "AAPL": "teknoloji",
    "MSFT": "teknoloji",
    "NVDA": "teknoloji",
    "TSLA": "otomotiv",
    "AMZN": "teknoloji",
    "GOOGL": "teknoloji",
    "JPM": "finans",
    "XOM": "enerji",
    "NEE": "enerji",
    "UNH": "sağlık",
}


def map_sector_score_to_stock(ticker: str, sector_scores: dict) -> float:
    """
    Bir hissenin sektörünün haber sentiment skoru nedir?
    Döndürür: -1.0 ile +1.0 arası float
    """
    sector = TICKER_TO_SECTOR.get(ticker, "genel")
    score = sector_scores.get(sector, sector_scores.get("genel", 0.0))
    return score


def calculate_final_score(ticker: str, technical_score: float,
                          sector_scores: dict) -> dict:
    """
    Nihai skor hesaplar.

    Formül:
    final = (teknik * 0.40) + (sektör_haber * 0.20) + (temel * 0.30) + (momentum * 0.10)

    Ama "temel" analiz burada teknik analiz içindeki momentum'dan türetiliyor
    (temel analiz API'si için Alpha Vantage kullanılabilir ama ücretsiz tierde
    sınırlı, bu yüzden momentum'u temel proxy olarak kullanıyoruz)
    """

    # Teknik skor: 0-100 → 0-1 normalize
    tech_normalized = technical_score / 100.0

    # Sektörel haber skoru: -1 ile +1 → 0 ile 1 normalize
    sector_score = map_sector_score_to_stock(ticker, sector_scores)
    sector_normalized = (sector_score + 1.0) / 2.0  # -1,+1 → 0,1

    # Momentum bonus: Teknik skor yüksek olsa bile momentum negatif varsa penalize
    # (Bu zaten technical_score'da yansıtıldı ama burada ayrıca amplify ediyoruz)
    momentum_factor = 0.5  # default neutral

    # Ağırlıklı skor
    # Temel analiz proxy olarak teknik skor kullanılıyor (0.30 ağırlık)
    # Momentum ise 0.10 ile
    final_raw = (
        tech_normalized * config.WEIGHT_TECHNICAL / 100.0 +
        sector_normalized * config.WEIGHT_NEWS_SENTIMENT / 100.0 +
        tech_normalized * config.WEIGHT_FUNDAMENTAL / 100.0 +  # Proxy
        momentum_factor * config.WEIGHT_MOMENTUM / 100.0
    )

    # 0-100 arası normalize
    final_score = final_raw * 100.0
    final_score = max(0, min(100, final_score))

    # Rating ver
    if final_score >= 70:
        rating = "🔥 GÜÇLÜ AL"
        confidence = "Yüksek"
    elif final_score >= 58:
        rating = "📈 AL"
        confidence = "Orta-Yüksek"
    elif final_score >= 48:
        rating = "⚖️ İZLE"
        confidence = "Orta"
    elif final_score >= 38:
        rating = "📉 IVAR"
        confidence = "Orta-Düşük"
    else:
        rating = "🚫 SAT"
        confidence = "Düşük"

    return {
        "final_score": round(final_score, 1),
        "technical_score": technical_score,
        "sector_score": round(sector_score, 3),
        "rating": rating,
        "confidence": confidence,
        "sector": TICKER_TO_SECTOR.get(ticker, "genel")
    }


def select_top_stocks(all_analysis: list, sector_scores: dict,
                      max_count: int = 3) -> list:
    """
    Tüm hisseleri skor alarak en iyi 1-3'ünü seçer.

    Seçim kriterleri:
    1) Nihai skor en yüksek olanlar
    2) Minimum skor threshold'u: 50 (altında olan hiçbiri seçilmez)
    3) Sektör çeşitlendirmesi: Aynı sektörden max 1 hisse
    4) Rating'i "AL" veya yukarısı olmalı
    """
    # Her hisse için nihai skor hesapla
    scored = []
    for stock in all_analysis:
        ticker = stock.get("ticker", "")
        tech_score = stock.get("score", 0)

        if tech_score == 0:
            continue

        final = calculate_final_score(ticker, tech_score, sector_scores)
        stock.update(final)
        scored.append(stock)

    # Final score'a göre sort
    scored.sort(key=lambda x: x.get("final_score", 0), reverse=True)

    # Sektör çeşitlendirmesi ile seç
    selected = []
    used_sectors = set()

    for stock in scored:
        if len(selected) >= max_count:
            break

        # Minimum threshold
        if stock.get("final_score", 0) < 50:
            continue

        # Rating kontrolü (sadece AL veya yukarısı)
        rating = stock.get("rating", "")
        if "AL" not in rating and "🔥" not in rating:
            continue

        # Sektör çeşitlendirmesi
        sector = stock.get("sector", "")
        if sector in used_sectors:
            continue  # Bu sektörden zaten seçtik

        selected.append(stock)
        used_sectors.add(sector)

    # Hiçbiri seçilmediyse en yüksek scored'u al (threshold düşür)
    if not selected and scored:
        best = scored[0]
        if best.get("final_score", 0) >= 40:
            selected.append(best)

    return selected


def generate_recommendation_text(selected: list, sector_scores: dict,
                                  news_summary: list = None) -> dict:
    """
    Son kullanıcı için okunabilir önerileri oluşturur.
    """
    recommendations = []

    for i, stock in enumerate(selected, 1):
        ticker = stock.get("ticker", "")
        price = stock.get("current_price", 0)
        score = stock.get("final_score", 0)
        rating = stock.get("rating", "")
        sector = stock.get("sector", "")
        signals = stock.get("signals", [])
        fib = stock.get("fibonacci", {})
        confidence = stock.get("confidence", "")

        # Fibonacci destek/direnç
        current = fib.get("current", price)
        support = fib.get("fib_0.382", 0)
        resistance = fib.get("fib_0.618", 0)

        # Risk/Reward hesapla
        if support > 0 and resistance > 0 and current > 0:
            risk = round((current - support) / current * 100, 1)
            reward = round((resistance - current) / current * 100, 1)
            rr_ratio = round(reward / risk, 2) if risk > 0 else 0
        else:
            risk = reward = rr_ratio = 0

        rec = {
            "rank": i,
            "ticker": ticker,
            "sector": sector,
            "price": price,
            "score": score,
            "rating": rating,
            "confidence": confidence,
            "signals": signals,
            "support": support,
            "resistance": resistance,
            "risk_pct": risk,
            "reward_pct": reward,
            "risk_reward_ratio": rr_ratio,
        }

        recommendations.append(rec)

    return {
        "recommendations": recommendations,
        "total_selected": len(selected),
        "market_mood": determine_market_mood(sector_scores),
        "analysis_date": None  # Sonra doldurulacak
    }


def determine_market_mood(sector_scores: dict) -> str:
    """Genel piyasa duygu analizi."""
    if not sector_scores:
        return "⚪ Belirsiz"

    avg_all = sum(sector_scores.values()) / len(sector_scores)

    if avg_all >= 0.3:
        return "🟢 Çok Olumlu - Piyasalar yukarı baskı altında"
    elif avg_all >= 0.1:
        return "🟢 Olumlu - Genel pozitif sinyaller var"
    elif avg_all >= -0.1:
        return "🟡 Karışık - Piyasa yönü belirsiz"
    elif avg_all >= -0.3:
        return "🔴 Olumsuz - Dikkatli olun"
    else:
        return "🔴 Çok Olumsuz - Yüksek risk dönem"
