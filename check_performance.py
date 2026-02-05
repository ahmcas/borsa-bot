#!/usr/bin/env python3
# ============================================================
# check_performance.py — Manuel Performans Kontrolü
# ============================================================
# Bu scripti istediğiniz zaman çalıştırarak performansı kontrol edebilirsiniz.
# 
# Kullanım:
#   python check_performance.py --days 30
#   python check_performance.py --report
#   python check_performance.py --history
# ============================================================

import argparse
from performance_tracker import PerformanceTracker, generate_performance_email
from mail_sender import send_email
from datetime import datetime
import sys


def print_report(report: dict):
    """Raporu terminalde güzel formatta göster."""
    print("\n" + "=" * 60)
    print(f"  📊 PERFORMANS RAPORU - Son {report['period_days']} Gün")
    print("=" * 60)
    
    print(f"\n  📈 GENEL İSTATİSTİKLER:")
    print(f"     Toplam Öneri      : {report['total_recommendations']}")
    print(f"     Kontrol Edilen    : {report['total_checked']}")
    print(f"     Başarılı          : {report['success_count']} ✅")
    print(f"     Nötr              : {report['neutral_count']} ⚖️")
    print(f"     Zarar             : {report['loss_count']} ❌")
    
    # Win rate renklendirme
    win_rate = report['win_rate']
    if win_rate >= 60:
        wr_emoji = "🔥"
        wr_label = "MÜKEMMEL"
    elif win_rate >= 50:
        wr_emoji = "✅"
        wr_label = "İYİ"
    elif win_rate >= 40:
        wr_emoji = "⚠️"
        wr_label = "ORTA"
    else:
        wr_emoji = "❌"
        wr_label = "DÜŞÜK"
    
    print(f"\n  🎯 BAŞARI ORANI:")
    print(f"     {win_rate}% {wr_emoji} ({wr_label})")
    
    # Ortalama getiri
    avg_ret = report['avg_return_pct']
    ret_emoji = "📈" if avg_ret > 0 else "📉"
    print(f"\n  💰 ORTALAMA GETİRİ:")
    print(f"     {avg_ret:+.2f}% {ret_emoji}")
    
    print(f"\n  🏆 SEKTÖR ANALİZİ:")
    print(f"     En İyi Sektör     : {report['best_sector']}")
    print(f"     En Kötü Sektör    : {report['worst_sector']}")
    
    print("\n" + "=" * 60)


def print_history(history: list):
    """Geçmiş önerileri tablo formatında göster."""
    print("\n" + "=" * 100)
    print(f"  📜 ÖNERİ GEÇMİŞİ (Son {len(history)} Öneri)")
    print("=" * 100)
    
    # Header
    print(f"\n  {'Tarih':<12} {'Ticker':<12} {'Giriş':<10} {'Rating':<15} {'Skor':<6} {'Gün':<5} {'Çıkış':<10} {'Getiri':<10} {'Sonuç':<10}")
    print("  " + "-" * 95)
    
    for item in history:
        date = item['date']
        ticker = item['ticker']
        entry = f"{item['entry_price']:.2f}" if item['entry_price'] else "N/A"
        rating = item['rating'][:12]
        score = f"{item['score']:.0f}" if item['score'] else "N/A"
        days = str(item['days_held']) if item['days_held'] else "-"
        exit_p = f"{item['exit_price']:.2f}" if item['exit_price'] else "Bekl..."
        ret = f"{item['return_pct']:+.2f}%" if item['return_pct'] is not None else "..."
        
        # Outcome emoji
        outcome = item['outcome']
        if outcome == "SUCCESS":
            outcome_str = "✅ Başarılı"
        elif outcome == "NEUTRAL":
            outcome_str = "⚖️  Nötr"
        elif outcome == "LOSS":
            outcome_str = "❌ Zarar"
        else:
            outcome_str = "⏳ Bekliyor"
        
        print(f"  {date:<12} {ticker:<12} {entry:<10} {rating:<15} {score:<6} {days:<5} {exit_p:<10} {ret:<10} {outcome_str}")
    
    print("\n" + "=" * 100)


def main():
    parser = argparse.ArgumentParser(description="Borsa Bot Performans Kontrolü")
    parser.add_argument("--days", type=int, default=30, help="Rapor için gün sayısı (default: 30)")
    parser.add_argument("--report", action="store_true", help="Performans raporunu göster")
    parser.add_argument("--history", action="store_true", help="Öneri geçmişini göster")
    parser.add_argument("--check", action="store_true", help="Geçmiş önerilerin performansını hesapla")
    parser.add_argument("--email", action="store_true", help="Raporu email olarak gönder")
    parser.add_argument("--limit", type=int, default=20, help="Geçmişte gösterilecek öneri sayısı")
    
    args = parser.parse_args()
    
    tracker = PerformanceTracker()
    
    # Performans hesaplama
    if args.check:
        print("🔍 Geçmiş önerilerin performansı hesaplanıyor...")
        results = tracker.check_performance([7, 14, 30])
        print(f"✅ {len(results)} yeni performans sonucu hesaplandı\n")
        
        for res in results[:10]:
            print(f"  {res['ticker']:12s} ({res['days']:2d} gün) → {res['return']:+6.2f}% ({res['outcome']})")
    
    # Rapor göster
    if args.report or (not args.history and not args.check):
        report = tracker.generate_report(args.days)
        print_report(report)
        
        # Email gönder
        if args.email:
            print("\n📧 Rapor email olarak gönderiliyor...")
            history = tracker.get_detailed_history(args.limit)
            html = generate_performance_email(report, history)
            success = send_email(
                html,
                subject=f"📊 Performans Raporu - {datetime.now().strftime('%d %b %Y')}"
            )
            if success:
                print("✅ Email gönderildi!")
            else:
                print("❌ Email gönderilemedi")
    
    # Geçmiş göster
    if args.history:
        history = tracker.get_detailed_history(args.limit)
        print_history(history)


if __name__ == "__main__":
    main()
