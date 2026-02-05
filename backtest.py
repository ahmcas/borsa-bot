#!/usr/bin/env python3
# ============================================================
# backtest.py — Geçmişe Dönük Test (Backtesting)
# ============================================================
# Sistemi geçmiş verilerde test ederek gerçek başarı oranını hesaplar.
#
# Kullanım:
#   python backtest.py --start 2024-01-01 --end 2025-01-01
#   python backtest.py --days 90
# ============================================================

import argparse
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import sys
import os

# Module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from technical_analyzer import download_stock_data, score_technical
from scorer import calculate_final_score


def backtest_single_day(test_date: str, tickers: list) -> dict:
    """
    Tek bir gün için backtest yap.
    O günkü sinyallere göre öneri üretir, 7 gün sonraki performansı hesaplar.
    """
    
    print(f"\n📅 Test Tarihi: {test_date}")
    
    # O tarihteki analizi yap (200 gün öncesinden itibaren veri al)
    start = datetime.strptime(test_date, "%Y-%m-%d") - timedelta(days=200)
    end = datetime.strptime(test_date, "%Y-%m-%d")
    
    recommendations = []
    
    for ticker in tickers:
        try:
            # Veriyi çek
            df = yf.download(
                ticker,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True
            )
            
            if df.empty or len(df) < 60:
                continue
            
            # Column flatten
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Teknik analiz
            analysis = score_technical(df)
            
            if analysis["score"] == 0:
                continue
            
            # Skor hesapla (haber analizi olmadan, sadece teknik)
            # Basitleştirilmiş skor: teknik * 0.7 + momentum * 0.3
            final_score = analysis["score"] * 0.7 + 50 * 0.3
            
            if final_score >= 55:  # Alım sinyali threshold
                recommendations.append({
                    "ticker": ticker,
                    "date": test_date,
                    "entry_price": analysis["current_price"],
                    "score": round(final_score, 1),
                    "rsi": analysis["rsi"],
                    "support": analysis["fibonacci"].get("fib_0.382", 0),
                    "resistance": analysis["fibonacci"].get("fib_0.618", 0)
                })
        
        except Exception as e:
            continue
    
    # En iyi 3'ü seç
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    top_recs = recommendations[:3]
    
    print(f"  📊 {len(recommendations)} hisse sinyal verdi, {len(top_recs)} seçildi")
    
    # 7 gün sonraki performansı hesapla
    results = []
    
    for rec in top_recs:
        ticker = rec["ticker"]
        entry = rec["entry_price"]
        
        # 7 gün sonraki fiyatı al
        future_start = datetime.strptime(test_date, "%Y-%m-%d") + timedelta(days=1)
        future_end = future_start + timedelta(days=10)  # 7 iş günü için 10 takvim günü
        
        try:
            future_df = yf.download(
                ticker,
                start=future_start.strftime("%Y-%m-%d"),
                end=future_end.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True
            )
            
            if future_df.empty or len(future_df) < 5:
                continue
            
            if isinstance(future_df.columns, pd.MultiIndex):
                future_df.columns = future_df.columns.get_level_values(0)
            
            # 7. günün (veya mevcut son günün) fiyatı
            exit_price = float(future_df["Close"].iloc[min(6, len(future_df)-1)])
            
            # Return hesapla
            return_pct = ((exit_price - entry) / entry) * 100
            
            # Outcome
            if return_pct >= 5:
                outcome = "SUCCESS"
            elif return_pct >= 0:
                outcome = "NEUTRAL"
            else:
                outcome = "LOSS"
            
            results.append({
                "ticker": ticker,
                "entry": entry,
                "exit": exit_price,
                "return": return_pct,
                "outcome": outcome,
                "score": rec["score"]
            })
            
            # Sonuç göster
            emoji = "✅" if outcome == "SUCCESS" else "⚖️" if outcome == "NEUTRAL" else "❌"
            print(f"  {emoji} {ticker:12s} → {return_pct:+6.2f}% (Skor: {rec['score']:.0f})")
        
        except Exception as e:
            continue
    
    return results


def run_backtest(start_date: str, end_date: str, tickers: list = None) -> dict:
    """
    Belirli bir tarih aralığında backtest yap.
    """
    if tickers is None:
        tickers = config.ALL_STOCKS
    
    print("\n" + "=" * 70)
    print(f"  🔬 BACKTEST BAŞLATILIYOR")
    print(f"  📅 Tarih Aralığı: {start_date} → {end_date}")
    print(f"  📊 Hisse Sayısı: {len(tickers)}")
    print("=" * 70)
    
    # Tarih listesi oluştur (hafta içi günler)
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    test_dates = []
    current = start
    
    while current <= end:
        # Sadece hafta içi (Pzt-Cuma)
        if current.weekday() < 5:
            test_dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    print(f"\n  🗓️  Test edilecek gün sayısı: {len(test_dates)}")
    print(f"  ⏱️  Tahmini süre: {len(test_dates) * 2} dakika")
    print("\n" + "-" * 70)
    
    all_results = []
    
    for i, test_date in enumerate(test_dates, 1):
        print(f"\n[{i}/{len(test_dates)}]", end=" ")
        
        results = backtest_single_day(test_date, tickers)
        all_results.extend(results)
    
    # Sonuçları analiz et
    print("\n\n" + "=" * 70)
    print("  📊 BACKTEST SONUÇLARI")
    print("=" * 70)
    
    if not all_results:
        print("\n  ⚠️  Hiç sonuç bulunamadı!")
        return {}
    
    total = len(all_results)
    success = len([r for r in all_results if r["outcome"] == "SUCCESS"])
    neutral = len([r for r in all_results if r["outcome"] == "NEUTRAL"])
    loss = len([r for r in all_results if r["outcome"] == "LOSS"])
    
    win_rate = (success / total * 100) if total > 0 else 0
    
    avg_return = sum([r["return"] for r in all_results]) / total if total > 0 else 0
    avg_success_return = sum([r["return"] for r in all_results if r["outcome"] == "SUCCESS"]) / success if success > 0 else 0
    avg_loss_return = sum([r["return"] for r in all_results if r["outcome"] == "LOSS"]) / loss if loss > 0 else 0
    
    print(f"\n  📈 GENEL İSTATİSTİKLER:")
    print(f"     Toplam İşlem       : {total}")
    print(f"     Başarılı (>=%5)    : {success} ({success/total*100:.1f}%)")
    print(f"     Nötr (0-5%)        : {neutral} ({neutral/total*100:.1f}%)")
    print(f"     Zarar (<0%)        : {loss} ({loss/total*100:.1f}%)")
    
    # Win rate değerlendirmesi
    if win_rate >= 60:
        wr_label = "🔥 MÜKEMMEL"
    elif win_rate >= 50:
        wr_label = "✅ İYİ"
    elif win_rate >= 40:
        wr_label = "⚠️ ORTA"
    else:
        wr_label = "❌ DÜŞÜK"
    
    print(f"\n  🎯 BAŞARI ORANI: {win_rate:.2f}% {wr_label}")
    
    print(f"\n  💰 GETİRİ ANALİZİ:")
    print(f"     Ortalama Getiri    : {avg_return:+.2f}%")
    print(f"     Başarılı Ort.      : {avg_success_return:+.2f}%")
    print(f"     Zararlı Ort.       : {avg_loss_return:+.2f}%")
    
    # Risk/Reward
    if abs(avg_loss_return) > 0:
        rr_ratio = abs(avg_success_return / avg_loss_return)
        print(f"     Risk/Reward Ratio  : {rr_ratio:.2f}")
    
    # En iyi ve en kötü performanslar
    best = max(all_results, key=lambda x: x["return"])
    worst = min(all_results, key=lambda x: x["return"])
    
    print(f"\n  🏆 EN İYİ İŞLEM:")
    print(f"     {best['ticker']:12s} → {best['return']:+.2f}% (Skor: {best['score']:.0f})")
    
    print(f"\n  📉 EN KÖTÜ İŞLEM:")
    print(f"     {worst['ticker']:12s} → {worst['return']:+.2f}% (Skor: {worst['score']:.0f})")
    
    # Hisse bazlı analiz
    ticker_stats = {}
    for r in all_results:
        ticker = r["ticker"]
        if ticker not in ticker_stats:
            ticker_stats[ticker] = {"total": 0, "success": 0, "returns": []}
        
        ticker_stats[ticker]["total"] += 1
        if r["outcome"] == "SUCCESS":
            ticker_stats[ticker]["success"] += 1
        ticker_stats[ticker]["returns"].append(r["return"])
    
    print(f"\n  📊 HİSSE BAZLI ANALİZ (Top 10):")
    print(f"     {'Ticker':<12} {'İşlem':<8} {'Başarı %':<12} {'Ort. Getiri':<12}")
    print("     " + "-" * 50)
    
    # Başarı oranına göre sırala
    sorted_tickers = sorted(
        ticker_stats.items(),
        key=lambda x: x[1]["success"] / x[1]["total"] if x[1]["total"] > 0 else 0,
        reverse=True
    )
    
    for ticker, stats in sorted_tickers[:10]:
        total = stats["total"]
        success = stats["success"]
        success_rate = (success / total * 100) if total > 0 else 0
        avg_ret = sum(stats["returns"]) / len(stats["returns"]) if stats["returns"] else 0
        
        print(f"     {ticker:<12} {total:<8} {success_rate:>6.1f}%     {avg_ret:>+7.2f}%")
    
    print("\n" + "=" * 70)
    
    return {
        "total": total,
        "success": success,
        "neutral": neutral,
        "loss": loss,
        "win_rate": win_rate,
        "avg_return": avg_return,
        "all_results": all_results
    }


def main():
    parser = argparse.ArgumentParser(description="Borsa Bot Backtesting")
    parser.add_argument("--start", type=str, help="Başlangıç tarihi (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="Bitiş tarihi (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, help="Bugünden geriye kaç gün test edilsin")
    parser.add_argument("--tickers", type=str, nargs="+", help="Test edilecek hisseler (boş ise tümü)")
    
    args = parser.parse_args()
    
    # Tarihleri belirle
    if args.days:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
    elif args.start and args.end:
        start_str = args.start
        end_str = args.end
    else:
        # Default: son 30 gün
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
    
    # Ticker listesi
    tickers = args.tickers if args.tickers else config.ALL_STOCKS
    
    # Backtest çalıştır
    results = run_backtest(start_str, end_str, tickers)
    
    print(f"\n✅ Backtest tamamlandı!")


if __name__ == "__main__":
    main()
