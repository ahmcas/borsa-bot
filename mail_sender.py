# ============================================================
# mail_sender.py — Email Gönderim Sistemi (SendGrid)
# ============================================================
# Bu modül:
# 1) Analiz sonuçlarını HTML email'e formatlar
# 2) Her alınan grafik dosyasını mail'e ekler
# 3) SendGrid API üzerinden gönderir
# ============================================================

import os
from datetime import datetime
import base64
import config

# SendGrid import
try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("⚠️  SendGrid yüklü değil, pip install sendgrid ile yükleyin")


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
            {footer}
        </div>
    </body>
    </html>
    """

    return full_html


def send_email(html_body: str, chart_paths: list = None, subject: str = None) -> bool:
    """
    Email'i SendGrid API üzerinden gönderir.
    """
    if not SENDGRID_AVAILABLE:
        print("❌ SendGrid paketi yüklü değil!")
        return False
    
    if subject is None:
        subject = f"📊 Borsa Analiz Raporu - {datetime.now().strftime('%d %b %Y')}"
    
    # SendGrid API Key
    sendgrid_api_key = os.environ.get("SENDGRID_API_KEY", config.SENDGRID_API_KEY if hasattr(config, 'SENDGRID_API_KEY') else None)
    
    if not sendgrid_api_key:
        print("❌ SENDGRID_API_KEY bulunamadı!")
        return False
    
    try:
        # SendGrid client
        sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
        
        # Email oluştur
        from_email = Email(os.environ.get("MAIL_SENDER", config.MAIL_SENDER))
        to_email = To(os.environ.get("MAIL_RECIPIENT", config.MAIL_RECIPIENT))
        content = Content("text/html", html_body)
        
        mail = Mail(from_email, to_email, subject, content)
        
        # Grafikleri ekle
        if chart_paths:
            for chart_path in chart_paths:
                if os.path.exists(chart_path):
                    with open(chart_path, 'rb') as f:
                        data = f.read()
                    
                    encoded = base64.b64encode(data).decode()
                    filename = os.path.basename(chart_path)
                    
                    attachment = Attachment()
                    attachment.file_content = FileContent(encoded)
                    attachment.file_type = FileType('image/png')
                    attachment.file_name = FileName(filename)
                    attachment.disposition = Disposition('attachment')
                    
                    mail.add_attachment(attachment)
                    print(f"  📎 Grafik eklendi: {filename}")
        
        # Gönder
        response = sg.client.mail.send.post(request_body=mail.get())
        
        if response.status_code in [200, 201, 202]:
            print(f"\n✅ Email başarıyla gönderildi!")
            print(f"   📧 Alıcı: {to_email.email}")
            print(f"   📌 Konu: {subject}")
            return True
        else:
            print(f"❌ SendGrid hata kodu: {response.status_code}")
            print(f"   Body: {response.body}")
            return False
    
    except Exception as e:
        print(f"❌ Email gönderim hatası: {e}")
        import traceback
        traceback.print_exc()
        return False
