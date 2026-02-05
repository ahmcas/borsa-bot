# ============================================================
# performance_tracker.py — Performans Takip Sistemi
# ============================================================
# Bu modül:
# 1) Her gün yapılan önerileri SQLite DB'ye kaydeder
# 2) 7, 14, 30 gün sonra gerçek sonuçları kontrol eder
# 3) Başarı oranını hesaplar ve raporlar
# 4) Hangi sinyallerin daha başarılı olduğunu analiz eder
# ============================================================

import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
import json
from typing import List, Dict
import pandas as pd


class PerformanceTracker:
    """
    Her önerinin performansını takip eder.
    """
    
    def __init__(self, db_path: str = "performance.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Veritabanı tablolarını oluştur."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Öneriler tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                ticker TEXT NOT NULL,
                entry_price REAL NOT NULL,
                technical_score REAL NOT NULL,
                final_score REAL NOT NULL,
                rating TEXT NOT NULL,
                sector TEXT,
                support_price REAL,
                resistance_price REAL,
                risk_pct REAL,
                reward_pct REAL,
                rr_ratio REAL,
                signals TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Performans sonuçları tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_id INTEGER NOT NULL,
                check_date TEXT NOT NULL,
                days_held INTEGER NOT NULL,
                exit_price REAL NOT NULL,
                return_pct REAL NOT NULL,
                hit_resistance BOOLEAN,
                hit_support BOOLEAN,
                max_price REAL,
                min_price REAL,
                volatility REAL,
                outcome TEXT,
                FOREIGN KEY (recommendation_id) REFERENCES recommendations(id)
            )
        """)
        
        # Genel istatistikler tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                total_recommendations INTEGER,
                successful_count INTEGER,
                failed_count INTEGER,
                neutral_count INTEGER,
                avg_return_pct REAL,
                win_rate REAL,
                best_sector TEXT,
                worst_sector TEXT,
                avg_holding_days REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Performans veritabanı hazır")
    
    def save_recommendation(self, rec: Dict) -> int:
        """
        Bir öneriyi veritabanına kaydet.
        Döndürür: recommendation_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO recommendations (
                date, ticker, entry_price, technical_score, final_score,
                rating, sector, support_price, resistance_price,
                risk_pct, reward_pct, rr_ratio, signals
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d"),
            rec.get("ticker"),
            rec.get("price"),
            rec.get("technical_score", 0),
            rec.get("final_score", 0),
            rec.get("rating"),
            rec.get("sector"),
            rec.get("support"),
            rec.get("resistance"),
            rec.get("risk_pct"),
            rec.get("reward_pct"),
            rec.get("risk_reward_ratio"),
            json.dumps(rec.get("signals", []))
        ))
        
        rec_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return rec_id
    
    def check_performance(self, days_to_check: List[int] = [7, 14, 30]):
        """
        Geçmiş önerilerin performansını kontrol et.
        days_to_check: [7, 14, 30] → 7, 14, 30 gün sonraki performansı
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        results = []
        
        for days in days_to_check:
            target_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            # O tarihteki önerileri al
            cursor.execute("""
                SELECT id, ticker, entry_price, support_price, resistance_price
                FROM recommendations
                WHERE date = ?
            """, (target_date,))
            
            recommendations = cursor.fetchall()
            
            for rec_id, ticker, entry_price, support, resistance in recommendations:
                # Bu öneri için performans daha önce hesaplandı mı?
                cursor.execute("""
                    SELECT id FROM performance_results
                    WHERE recommendation_id = ? AND days_held = ?
                """, (rec_id, days))
                
                if cursor.fetchone():
                    continue  # Zaten hesaplanmış
                
                # Gerçek performansı hesapla
                perf = self._calculate_actual_performance(
                    ticker, entry_price, target_date, days, support, resistance
                )
                
                if perf:
                    # Veritabanına kaydet
                    cursor.execute("""
                        INSERT INTO performance_results (
                            recommendation_id, check_date, days_held,
                            exit_price, return_pct, hit_resistance, hit_support,
                            max_price, min_price, volatility, outcome
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        rec_id,
                        datetime.now().strftime("%Y-%m-%d"),
                        days,
                        perf["exit_price"],
                        perf["return_pct"],
                        perf["hit_resistance"],
                        perf["hit_support"],
                        perf["max_price"],
                        perf["min_price"],
                        perf["volatility"],
                        perf["outcome"]
                    ))
                    
                    results.append({
                        "ticker": ticker,
                        "days": days,
                        "return": perf["return_pct"],
                        "outcome": perf["outcome"]
                    })
        
        conn.commit()
        conn.close()
        
        return results
    
    def _calculate_actual_performance(self, ticker: str, entry_price: float,
                                     start_date: str, days: int,
                                     support: float = None, resistance: float = None) -> Dict:
        """
        Gerçek piyasa performansını hesapla.
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = start + timedelta(days=days)
            
            # Hisse verisini çek
            df = yf.download(ticker, start=start, end=end, progress=False)
            
            if df.empty or len(df) < 2:
                return None
            
            # Fiyatları düzelt (multi-index varsa)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            exit_price = float(df["Close"].iloc[-1])
            max_price = float(df["High"].max())
            min_price = float(df["Low"].min())
            
            # Return hesapla
            return_pct = ((exit_price - entry_price) / entry_price) * 100
            
            # Volatilite
            volatility = float(df["Close"].pct_change().std() * 100)
            
            # Destek/Direnç test edildi mi?
            hit_resistance = max_price >= resistance if resistance else False
            hit_support = min_price <= support if support else False
            
            # Outcome belirle
            if return_pct >= 5:
                outcome = "SUCCESS"  # %5+ kazanç
            elif return_pct >= 0:
                outcome = "NEUTRAL"  # 0-5% arası
            else:
                outcome = "LOSS"     # Zarar
            
            return {
                "exit_price": round(exit_price, 2),
                "return_pct": round(return_pct, 2),
                "hit_resistance": hit_resistance,
                "hit_support": hit_support,
                "max_price": round(max_price, 2),
                "min_price": round(min_price, 2),
                "volatility": round(volatility, 2),
                "outcome": outcome
            }
        
        except Exception as e:
            print(f"❌ {ticker} performans hesaplama hatası: {e}")
            return None
    
    def generate_report(self, days: int = 30) -> Dict:
        """
        Son N günün performans raporunu üret.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Toplam öneri sayısı
        cursor.execute("""
            SELECT COUNT(*) FROM recommendations
            WHERE date >= ?
        """, (start_date,))
        total_recs = cursor.fetchone()[0]
        
        # Performans sonuçları (sadece 7 günlük)
        cursor.execute("""
            SELECT 
                pr.outcome,
                COUNT(*) as count,
                AVG(pr.return_pct) as avg_return
            FROM performance_results pr
            JOIN recommendations r ON pr.recommendation_id = r.id
            WHERE r.date >= ? AND pr.days_held = 7
            GROUP BY pr.outcome
        """, (start_date,))
        
        outcomes = cursor.fetchall()
        
        success_count = 0
        neutral_count = 0
        loss_count = 0
        avg_return = 0
        
        for outcome, count, avg_ret in outcomes:
            if outcome == "SUCCESS":
                success_count = count
            elif outcome == "NEUTRAL":
                neutral_count = count
            elif outcome == "LOSS":
                loss_count = count
        
        total_checked = success_count + neutral_count + loss_count
        win_rate = (success_count / total_checked * 100) if total_checked > 0 else 0
        
        # Ortalama getiri
        cursor.execute("""
            SELECT AVG(pr.return_pct)
            FROM performance_results pr
            JOIN recommendations r ON pr.recommendation_id = r.id
            WHERE r.date >= ? AND pr.days_held = 7
        """, (start_date,))
        
        avg_return_result = cursor.fetchone()[0]
        avg_return = avg_return_result if avg_return_result else 0
        
        # En iyi sektör
        cursor.execute("""
            SELECT 
                r.sector,
                AVG(pr.return_pct) as avg_return
            FROM performance_results pr
            JOIN recommendations r ON pr.recommendation_id = r.id
            WHERE r.date >= ? AND pr.days_held = 7
            GROUP BY r.sector
            ORDER BY avg_return DESC
            LIMIT 1
        """, (start_date,))
        
        best_sector_row = cursor.fetchone()
        best_sector = best_sector_row[0] if best_sector_row else "N/A"
        
        # En kötü sektör
        cursor.execute("""
            SELECT 
                r.sector,
                AVG(pr.return_pct) as avg_return
            FROM performance_results pr
            JOIN recommendations r ON pr.recommendation_id = r.id
            WHERE r.date >= ? AND pr.days_held = 7
            GROUP BY r.sector
            ORDER BY avg_return ASC
            LIMIT 1
        """, (start_date,))
        
        worst_sector_row = cursor.fetchone()
        worst_sector = worst_sector_row[0] if worst_sector_row else "N/A"
        
        conn.close()
        
        return {
            "period_days": days,
            "total_recommendations": total_recs,
            "total_checked": total_checked,
            "success_count": success_count,
            "neutral_count": neutral_count,
            "loss_count": loss_count,
            "win_rate": round(win_rate, 2),
            "avg_return_pct": round(avg_return, 2),
            "best_sector": best_sector,
            "worst_sector": worst_sector
        }
    
    def get_detailed_history(self, limit: int = 20) -> List[Dict]:
        """
        Detaylı geçmiş önerileri ve sonuçlarını getir.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                r.date,
                r.ticker,
                r.entry_price,
                r.rating,
                r.final_score,
                pr.days_held,
                pr.exit_price,
                pr.return_pct,
                pr.outcome
            FROM recommendations r
            LEFT JOIN performance_results pr ON r.id = pr.recommendation_id
            ORDER BY r.date DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "date": row[0],
                "ticker": row[1],
                "entry_price": row[2],
                "rating": row[3],
                "score": row[4],
                "days_held": row[5],
                "exit_price": row[6],
                "return_pct": row[7],
                "outcome": row[8]
            })
        
        return history


def generate_performance_email(report: Dict, history: List[Dict]) -> str:
    """
    Performans raporu için HTML email üretir.
    """
    
    win_rate_color = "#10b981" if report["win_rate"] >= 60 else "#f59e0b" if report["win_rate"] >= 45 else "#ef4444"
    avg_return_color = "#10b981" if report["avg_return_pct"] > 0 else "#ef4444"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f0f4f8; padding: 20px; }}
            .container {{ max-width: 700px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); padding: 30px; text-align: center; color: white; }}
            .stats {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; padding: 25px; }}
            .stat-box {{ background: #f8fafc; border: 2px solid #e2e8f0; border-radius: 10px; padding: 15px; text-align: center; }}
            .stat-label {{ color: #64748b; font-size: 12px; text-transform: uppercase; font-weight: 600; }}
            .stat-value {{ color: #1e293b; font-size: 28px; font-weight: 800; margin-top: 5px; }}
            .history {{ padding: 25px; }}
            .history-item {{ background: #f8fafc; border-left: 4px solid #cbd5e1; padding: 12px; margin-bottom: 10px; }}
            .success {{ border-left-color: #10b981; }}
            .neutral {{ border-left-color: #f59e0b; }}
            .loss {{ border-left-color: #ef4444; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Performans Raporu</h1>
                <p>Son {report['period_days']} Gün</p>
            </div>
            
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-label">Toplam Öneri</div>
                    <div class="stat-value">{report['total_recommendations']}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Başarı Oranı</div>
                    <div class="stat-value" style="color: {win_rate_color}">{report['win_rate']}%</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Ort. Getiri</div>
                    <div class="stat-value" style="color: {avg_return_color}">{report['avg_return_pct']:+.2f}%</div>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-label">Başarılı</div>
                    <div class="stat-value" style="color: #10b981">{report['success_count']}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Nötr</div>
                    <div class="stat-value" style="color: #f59e0b">{report['neutral_count']}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Zarar</div>
                    <div class="stat-value" style="color: #ef4444">{report['loss_count']}</div>
                </div>
            </div>
            
            <div style="padding: 25px; background: #f1f5f9;">
                <p style="margin: 0;"><strong>En İyi Sektör:</strong> {report['best_sector']}</p>
                <p style="margin: 5px 0 0 0;"><strong>En Kötü Sektör:</strong> {report['worst_sector']}</p>
            </div>
            
            <div class="history">
                <h3>Son Öneriler</h3>
    """
    
    for item in history[:10]:
        outcome_class = "success" if item["outcome"] == "SUCCESS" else "neutral" if item["outcome"] == "NEUTRAL" else "loss"
        outcome_text = "✅ Başarılı" if item["outcome"] == "SUCCESS" else "⚖️ Nötr" if item["outcome"] == "NEUTRAL" else "❌ Zarar"
        
        return_text = f"{item['return_pct']:+.2f}%" if item["return_pct"] else "Bekleniyor..."
        
        html += f"""
                <div class="history-item {outcome_class}">
                    <strong>{item['ticker']}</strong> - {item['date']} - {item['rating']}<br>
                    Giriş: {item['entry_price']} | Çıkış: {item['exit_price'] or 'N/A'} | Getiri: {return_text}<br>
                    Sonuç: {outcome_text}
                </div>
        """
    
    html += """
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


if __name__ == "__main__":
    # Test
    tracker = PerformanceTracker()
    
    # Örnek öneri kaydet
    sample_rec = {
        "ticker": "THYAO.IS",
        "price": 245.50,
        "technical_score": 72,
        "final_score": 68,
        "rating": "AL",
        "sector": "teknoloji",
        "support": 238,
        "resistance": 268,
        "risk_pct": 3.1,
        "reward_pct": 9.2,
        "risk_reward_ratio": 2.97,
        "signals": ["RSI 45", "MACD bullish"]
    }
    
    rec_id = tracker.save_recommendation(sample_rec)
    print(f"✅ Öneri kaydedildi: ID {rec_id}")
    
    # Performans kontrol et
    print("\n🔍 Geçmiş performanslar kontrol ediliyor...")
    results = tracker.check_performance([7, 14, 30])
    print(f"✅ {len(results)} sonuç hesaplandı")
    
    # Rapor üret
    print("\n📊 Performans raporu:")
    report = tracker.generate_report(30)
    for key, value in report.items():
        print(f"  {key}: {value}")
