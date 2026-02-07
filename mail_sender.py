# ============================================================
# mail_sender.py — Email Gönderim Sistemi
# ============================================================
# Bu modül:
# 1) Analiz sonuçlarını HTML email'e formatlar
# 2) Her alınan grafik dosyasını mail'e ekler
# 3) Gmail SMTP üzerinden gönderir
# ============================================================

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
import os
import config


def generate_html_body(recommendations: dict, chart_paths: list) -> str:
    """
    Sade ve anlaşılır HTML mail body üretir.
    Herkes anlayabilecek şekilde düzenlenmiştir.
    """

    market_mood = recommendations.get("market_mood", "⚪ Belirsiz")
    recs = recommendations.get("recommendations", [])
    date_str = datetime.now().strftime("%d %B %Y, %H:%M")

    # --- CSS Styles ---
    css = """
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f0f4f8; margin: 0; padding: 20px; }
        .container { max-width: 700px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        .header { background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 28px 24px; text-align: center; }
        .header h1 { color: #fff; margin: 0 0 6px; font-size: 22px; font-weight: 700; }
        .header .subtitle { color: #94a3b8; font-size: 13px; margin: 0; }
        .mood-bar { background: #1e293b; padding: 14px 24px; text-align: center; }
        .mood-bar .mood-text { color: #e2e8f0; font-size: 15px; font-weight: 600; }
        .section { padding: 22px 24px; }
        .section-title { color: #1e293b; font-size: 16px; font-weight: 700; margin: 0 0 16px; padding-bottom: 8px; border-bottom: 2px solid #e2e8f0; }
        .card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 18px; margin-bottom: 16px; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .ticker-name { font-size: 20px; font-weight: 800; color: #1e293b; }
        .sector-badge { background: #e0e7ff; color: #4338ca; font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 20px; text-transform: uppercase; }
        .rating-box { text-align: center; padding: 8px 16px; border-radius: 8px; font-weight: 700; font-size: 15px; }
        .rating-strong-buy { background: #dcfce7; color: #16a34a; }
        .rating-buy { background: #dbeafe; color: #2563eb; }
        .rating-hold { background: #fef3c7; color: #d97706; }
        .info-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 14px; }
        .info-item { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; text-align: center; }
        .info-label { color: #64748b; font-size: 10px; text-transform: uppercase; font-weight: 600; margin-bottom: 4px; }
        .info-value { color: #1e293b; font-size: 15px; font-weight: 700; }
        .signals-list { list-style: none; padding: 0; margin: 0; }
        .signals-list li { padding: 5px 0; font-size: 12px; color: #475569; border-bottom: 1px solid #f1f5f9; }
        .signals-list li:last-child { border-bottom: none; }
        .signals-list li::before { content: "→ "; color: #6366f1; font-weight: 600; }
        .rr-box { display: flex; gap: 12px; margin-top: 12px; }
        .rr-item { flex: 1; text-align: center; padding: 8px; border-radius: 6px; }
        .rr-risk { background: #fef2f2; }
        .rr-reward { background: #f0fdf4; }
        .rr-label { font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 600; }
        .rr-value { font-size: 16px; font-weight: 800; }
        .rr-risk .rr-value { color: #dc2626; }
        .rr-reward .rr-value { color: #16a34a; }
        .chart-container { margin: 10px 0; text-align: center; }
        .chart-container img { max-width: 100%; border-radius: 8px; }
        .no-stocks { background: #fef3c7; border: 1px solid #fbbf24; border-radius: 10px; padding: 20px; text-align: center; }
        .no-stocks p { color: #92400e; font-weight: 600; margin: 0; }
        .footer { background: #f1f5f9; padding: 18px 24px; text-align: center; border-top: 1px solid #e2e8f0; }
        .footer p { color: #64748b; font-size: 11px; margin: 4px 0; }
        .disclaimer { color: #94a3b8; font-size: 10px; font-style: italic; margin-top: 8px !important; }
    </style>
    """

    # --- HEADER ---
    header = f"""
    <div class="header">
        <h1>📊 Borsa Analiz Raporu</h1>
        <p class="subtitle">{date_str} | Günlük Analiz</p>
    </div>
    """

    # --- MARKET MOOD ---
    mood = f"""
    <div class="mood-bar">
        <div class="mood-text">Piyasa Duygusu: {market_mood}</div>
    </div>
    """

    # --- RECOMMENDATIONS ---
    if recs:
        rec_title = f"""
        <div class="section">
            <div class="section-title">🎯 Bugün Önerilen Hisseler ({len(recs)} adet)</div>
        """

        cards = ""
        for i, rec in enumerate(recs):
            # Rating class
            rating_text = rec.get("rating", "")
            if "GÜÇLÜ" in rating_text:
                rating_class = "rating-strong-buy"
            elif "AL" in rating_text:
                rating_class = "rating-buy"
            else:
                rating_class = "rating-hold"

            # Signals
            signals_html = "<ul class='signals-list'>"
            for sig in rec.get("signals", [])[:5]:
                signals_html += f"<li>{sig}</li>"
            signals_html += "</ul>"

            # Risk/Reward
            rr_html = ""
            if rec.get("risk_pct") and rec.get("reward_pct"):
                rr_html = f"""
                <div class="rr-box">
                    <div class="rr-item rr-risk">
                        <div class="rr-label">Destek (Risk)</div>
                        <div class="rr-value">-{rec['risk_pct']}%</div>
                        <div style="font-size:11px; color:#64748b">Fib 0.382: {rec['support']}</div>
                    </div>
                    <div class="rr-item rr-reward">
                        <div class="rr-label">Direnç (Potansiyel)</div>
                        <div class="rr-value">+{rec['reward_pct']}%</div>
                        <div style="font-size:11px; color:#64748b">Fib 0.618: {rec['resistance']}</div>
                    </div>
                </div>
                """

            card = f"""
            <div class="card">
                <div class="card-header">
                    <div>
                        <div class="ticker-name">#{rec['rank']} {rec['ticker']}</div>
                        <span class="sector-badge">{rec['sector']}</span>
                    </div>
                    <div class="rating-box {rating_class}">{rec['rating']}</div>
                </div>

                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Fiyat</div>
                        <div class="info-value">{rec['price']}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Skor</div>
                        <div class="info-value">{rec['score']}/100</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Güven</div>
                        <div class="info-value">{rec['confidence']}</div>
                    </div>
                </div>

                {signals_html}
                {rr_html}
            </div>
            """
            cards += card

        rec_section = rec_title + cards + "</div>"
    else:
        rec_section = """
        <div class="section">
            <div class="no-stocks">
                <p>⚠️ Bugün yeterli alım sinyali bulunamadı.<br>
                Piyasaları izlemeye devam ediyoruz. Yarın tekrar kontrol edileceğiz.</p>
            </div>
        </div>
        """

    # --- CHARTS (inline as references) ---
    chart_note = ""
    if chart_paths:
        chart_note = f"""
        <div class="section">
            <div class="section-title">📈 Teknik Analiz Grafikler</div>
            <p style="color:#64748b; font-size:13px; margin:0;">
                Aşağıda önerilen hisselerin detaylı teknik analiz grafikler yer almaktadır.<br>
                Grafiklerde: Fiyat + Bollinger Band + Fibonacci + MACD + RSI gösterilmiştir.
            </p>
        </div>
        """

    # --- FOOTER ---
    footer = """
    <div class="footer">
        <p><strong>⚠️ Önemli Not:</strong></p>
        <p>Bu analiz sistemi otomatik olarak üretilmiştir ve yatırım tavsiyesi niteliği taşımaz.</p>
        <p>Kendi araştırmanızı yapın ve profesyonel bir finansal danışmana danışın.</p>
        <p class="disclaimer">
            Borsa işlemleri ciddi risk taşır. Geçmiş performans gelecek sonuçların garantisi değildir.
        </p>
    </div>
    """

    # Birleştir
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>{css}</head>
    <body>
        <div class="container">
            {header}
            {mood}
            {rec_section}
            {chart_note}
            {footer}
        </div>
    </body>
    </html>
    """

    return full_html


def send_email(html_body: str, chart_paths: list = None,
               subject: str = None) -> bool:
    """
    Email'i Gmail SMTP üzerinden gönderir.
    Grafikleri attachment olarak ekler.
    """
    if subject is None:
        subject = f"📊 Borsa Analiz Raporu - {datetime.now().strftime('%d %b %Y')}"

    try:
        # MIME message oluştur
        msg = MIMEMultipart("mixed")
        msg["From"] = config.MAIL_SENDER
        msg["To"] = config.MAIL_RECIPIENT
        msg["Subject"] = subject

        # HTML body ekle
        html_part = MIMEText(html_body, "html")
        msg.attach(html_part)

        # Grafikleri ekle
        if chart_paths:
            for chart_path in chart_paths:
                if os.path.exists(chart_path):
                    with open(chart_path, "rb") as img_file:
                        img_data = img_file.read()

                    # Image MIME
                    img_mime = MIMEImage(img_data, _subtype="png")
                    filename = os.path.basename(chart_path)
                    img_mime.add_header(
                        "Content-Disposition",
                        f"attachment; filename={filename}"
                    )
                    msg.attach(img_mime)
                    print(f"  📎 Grafik eklendi: {filename}")

        # SMTP bağlantı
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()  # Güvenli bağlantı
            server.ehlo()
            server.login(config.MAIL_SENDER, config.MAIL_PASSWORD)
            server.sendmail(config.MAIL_SENDER, config.MAIL_RECIPIENT, msg.as_string())

        print(f"\n✅ Email başarıyla gönderildi!")
        print(f"   📧 Alıcı: {config.MAIL_RECIPIENT}")
        print(f"   📌 Konu: {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Mail hata: Gmail kimlik doğrulama başarısız.")
        print("   → Gmail'de App Password oluşturduğunuzdan emin olun.")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP hata: {e}")
        return False
    except Exception as e:
        print(f"❌ Email gönderim genel hata: {e}")
        return False
