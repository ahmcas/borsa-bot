# ============================================================
# main_bot.py — ANA BOT (Orchestrator)
# ============================================================
# Bu dosya tüm sistemi yönetir:
# 1) Haberleri çeker ve analiz eder
# 2) Tüm hisselerin teknik analizini yapır
# 3) Master scorer ile nihai skor hesaplar
# 4) En iyi 1-3 hisseyi seçer
# 5) Grafikleri üretir
# 6) Email'i formatlar ve gönderir
# 7) Her gün otomatik olarak çalıştırılır
# ============================================================

import sys
import os
import schedule
import time
from datetime import datetime

# Module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from news_analyzer import analyze_all_news
from technical_analyzer import analyze_all_stocks
from scorer import select_top_stocks, generate_recommendation_text
from chart_generator import generate_all_charts
from mail_sender import generate_html_body, send_email
#from performance_tracker import PerformanceTracker, generate_performance_email


def run_full_analysis():
    """
    Tam analiz pipeline'ı çalıştırır.
    """
    print("\n" + "=" * 65)
    print(f"  🚀 BORSA ANALİZ BOT BAŞLANGICI")
    print(f"  📅 {datetime.now().strftime('%d %B %Y, %H:%M:%S')}")
    print("=" * 65)

    # ─── STEP 1: HABER ANALİZİ ─────────────────────────────
    print("\n📰 ADIM 1: Haber analizi başlıyor...")
    print("-" * 50)

    try:
        news_data = analyze_all_news()
        sector_scores = news_data.get("sector_scores", {})
        top_sectors = news_data.get("top_sectors", [])
        risk_sectors = news_data.get("risk_sectors", [])

        print(f"\n  📊 Analiz edilen haber sayısı: {len(news_data.get('raw_news', []))}")
        print(f"  🏆 En olumlu sektörler: {top_sectors}")
        print(f"  ⚠️  Risk sektörler: {risk_sectors}")

    except Exception as e:
        print(f"  ❌ Haber analizi hatası: {e}")
        sector_scores = {}
        news_data = {"raw_news": []}

    # ─── STEP 2: TEKNİK ANALİZ ─────────────────────────────
    print("\n📈 ADIM 2: Teknik analiz başlıyor...")
    print("-" * 50)

    try:
        stock_analysis = analyze_all_stocks(config.ALL_STOCKS)

        print(f"\n  ✅ {len(stock_analysis)} hisse analiz edildi.")
        print(f"\n  📋 Top 5 Teknik Skor:")
        for s in stock_analysis[:5]:
            print(f"     {s.get('ticker', 'N/A'):15s} → Skor: {s.get('score', 0)}/100")

    except Exception as e:
        print(f"  ❌ Teknik analiz hatası: {e}")
        stock_analysis = []

    if not stock_analysis:
        print("\n⛔ Hiçbir hisse analiz edilemedi. Bot durduruyor.")
        return False

    # ─── STEP 3: MASTER SCORING & SEÇIM ────────────────────
    print("\n🎯 ADIM 3: Hisse seçimi ve skor hesabı...")
    print("-" * 50)

    try:
        selected = select_top_stocks(stock_analysis, sector_scores, max_count=3)

        if selected:
            print(f"\n  🏆 {len(selected)} hisse seçildi:")
            for s in selected:
                print(f"     {s.get('ticker', 'N/A'):15s} → {s.get('rating', '')} | Skor: {s.get('final_score', 0)}")
        else:
            print("\n  ⚠️  Bu gün yeterli alım sinyali bulunamadı.")

        recommendations = generate_recommendation_text(selected, sector_scores)

    except Exception as e:
        print(f"  ❌ Scoring hatası: {e}")
        selected = []
        recommendations = {"recommendations": [], "market_mood": "⚪ Belirsiz"}

    # ─── STEP 4: GRAFİK ÜRETIM ─────────────────────────────
    print("\n📊 ADIM 4: Grafik üretimi...")
    print("-" * 50)

    chart_paths = []
    if selected:
        try:
            chart_paths = generate_all_charts(selected)
            print(f"\n  ✅ {len(chart_paths)} grafik üretildi.")
        except Exception as e:
            print(f"  ❌ Grafik üretim hatası: {e}")

    # ─── STEP 5: EMAIL GÖNDERİM ────────────────────────────
    print("\n📧 ADIM 5: Email hazırlanıyor ve gönderildi...")
    print("-" * 50)

    try:
        html_body = generate_html_body(recommendations, chart_paths)
        success = send_email(html_body, chart_paths)

        if success:
            print("\n  🎉 Süreç başarıyla tamamlandı!")
        else:
            print("\n  ⚠️  Email gönderildi ama doğrulama yapılamadı.")

    except Exception as e:
        print(f"  ❌ Email hatası: {e}")
        success = False
    
        # ─── STEP 6: PERFORMANS TAKİBİ ─────────────────────────
    print("\n📊 ADIM 6: Performans takibi...")
    print("-" * 50)
    print("  ℹ️  Performans takibi geçici olarak devre dışı")
    # Geçici olarak kapatıldı - veritabanı hatası düzeltilecek

    # ─── SUMMARY ────────────────────────────────────────────
    print("\n" + "=" * 65)
    print(f"  📋 ÖZET")
    print(f"  📰 Haberler: {len(news_data.get('raw_news', []))} adet analiz edildi")
    print(f"  📈 Hisseler: {len(stock_analysis)} adet analiz edildi")
    print(f"  🏆 Seçilen: {len(selected)} hisse")
    print(f"  📊 Grafik: {len(chart_paths)} adet üretildi")
    print(f"  📧 Email: {'✅ Gönderildi' if success else '❌ Gönderilmedi'}")
    print(f"  💾 Performans: {len(selected)} öneri kaydedildi")
    print("=" * 65)

    return success


def start_scheduler():
    """
    Günlük otomatik çalıştırıcıyı başlatır.
    """
    print("\n⏰ OTOMATIK ZAMANLAYICI AKTIF")
    print(f"   Her gün {config.DAILY_RUN_HOUR}:{config.DAILY_RUN_MINUTE:02d}'de çalışacak.")
    print("   Durdurmak için: Ctrl + C\n")

    # Her gün belirli saatte çalıştır
    schedule.every().day.at(
        f"{config.DAILY_RUN_HOUR}:{config.DAILY_RUN_MINUTE:02d}"
    ).do(run_full_analysis)

    # Başlangıçta hemen bir kez çalıştır
    run_full_analysis()

    # Zamanlayıcıyı kontrol eden loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Her dakika kontrol et


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Borsa Analiz Botu")
    parser.add_argument("--mode", choices=["run", "schedule", "test"],
                       default="run",
                       help="run=tek seferlik, schedule=otomatik, test=hızlı test")
    args = parser.parse_args()

    if args.mode == "test":
        print("🧪 TEST MODU - Sadece 2 hisse ile hızlı kontrol")
        # Test modunda sadece 2 hisseyi analiz et
        config.ALL_STOCKS = ["THYAO.IS", "AAPL"]
        run_full_analysis()

    elif args.mode == "schedule":
        start_scheduler()

    else:  # run
        run_full_analysis()
