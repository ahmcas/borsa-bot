import os
import base64
from datetime import datetime
import config

# SendGrid kütüphanesi kontrolü
try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("! SendGrid kütüphanesi bulunamadı. Lütfen requirements.txt dosyanıza 'sendgrid' ekleyin.")

def generate_html_body(recommendations: dict, chart_paths: list) -> str:
    """
    [span_1](start_span)Sade, anlaşılır ve istenen tüm bilgilendirme mesajlarını içeren HTML mail gövdesi üretir.[span_1](end_span)
    """
    market_mood = recommendations.get("market_mood", "Belirsiz")
    recs = recommendations.get("recommendations", [])
    date_str = datetime.now().strftime("%d %B %Y %H:%M")

    # [span_2](start_span)CSS Tasarımı[span_2](end_span)
    css = """
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
        .container { max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #1a2e3e, #16213e); padding: 30px; text-align: center; color: #ffffff; }
        .info-box { background: #e7f3ff; border-left: 5px solid #2196F3; padding: 15px; margin: 20px; font-size: 14px; color: #0d47a1; line-height: 1.6; }
        .mood-bar { background: #1e293b; color: #00ff00; text-align: center; padding: 12px; font-weight: bold; font-size: 15px; }
        .section { padding: 25px; }
        .card { border: 1px solid #e2e8f0; border-radius: 10px; padding: 18px; margin-bottom: 20px; background: #fafafa; }
        .ticker { font-size: 24px; font-weight: 800; color: #1e293b; }
        .rating { display: inline-block; padding: 5px 12px; border-radius: 6px; font-weight: bold; font-size: 13px; margin-top: 8px; text-transform: uppercase; }
        .rating-strong { background: #d4edda; color: #155724; }
        .rating-buy { background: #cce5ff; color: #004085; }
        .rating-hold { background: #fff3cd; color: #856404; }
        .footer { background: #f8f9fa; padding: 25px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #eee; }
        .disclaimer { font-style: italic; font-size: 11px; margin-top: 10px; opacity: 0.8; }
    </style>
    """

    # [span_3](start_span)İSTEK: Puan Açıklaması ve Bilgilendirme Mesajı[span_3](end_span)
    explanation_box = """
    <div class="info-box">
        <strong>Puanlama Sistemi Açıklaması:</strong><br>
        Algoritmamız; hisselerin teknik göstergelerini, hacim artışlarını ve trend yönlerini analiz ederek 0 ile 100 arasında bir skor üretir.
        <br><br>
        <em>Bu sistem, algoritmayı hiç bilmeyen birinin bile anlayacağı şekilde, hisselerin teknik gücünü tek bir puanla özetleyen bir bilgilendirme mesajıdır.</em>
    </div>
    """

    header_html = f"""
    <div class="header">
        <h1 style="margin:0;">Borsa Analiz Raporu</h1>
        <p style="margin:8px 0 0 0; opacity:0.8;">{date_str} | Algoritmik Tarama Sistemi</p>
    </div>
    """

    mood_html = f'<div class="mood-bar">Piyasa Duygusu: {market_mood}</div>'

    # [span_4](start_span)[span_5](start_span)Önerilen Hisseler Bölümü[span_4](end_span)[span_5](end_span)
    rec_html = ""
    if recs:
        cards = ""
        for rec in recs:
            rating = rec.get("rating", "TUT")
            # [span_6](start_span)Rating'e göre renk sınıfı belirleme[span_6](end_span)
            r_class = "rating-strong" if "GÜÇLÜ" in rating else "rating-buy" if "AL" in rating else "rating-hold"
            
            cards += f"""
            <div class="card">
                <div class="ticker">#{rec.get('rank', '0')} {rec.get('ticker', 'N/A')}</div>
                <div class="rating {r_class}">{rating}</div>
                <div style="margin-top:15px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div style="color:#64748b; font-size:13px;"><b>Güncel Fiyat:</b><br><span style="color:#1e293b; font-size:16px;">{rec.get('price', '-')}</span></div>
                    <div style="color:#64748b; font-size:13px;"><b>Teknik Skor:</b><br><span style="color:#1e293b; font-size:16px;">{rec.get('score', 0)}/100</span></div>
                </div>
            </div>
            """
        rec_html = f'<div class="section"><h3 style="color:#1a2e3e; margin-bottom:20px;">Bugün Öne Çıkan Hisseler</h3>{cards}</div>'
    else:
        rec_html = """
        <div class="section">
            <div style="background:#fff3cd; color:#856404; padding:15px; border-radius:8px; text-align:center;">
                [span_7](start_span)Bugün kriterlere uygun yeterli alım sinyali bulunamadı. Piyasalar izlenmeye devam ediyor.[span_7](end_span)
            </div>
        </div>
        """

    # [span_8](start_span)İSTEK: Algoritma Bilgilendirme ve Sabit Footer[span_8](end_span)
    footer_html = """
    <div class="footer">
        <p><strong>Önemli Bilgilendirme:</strong> Bu rapor, hisseleri belirli teknik kriterlere göre rastgele seçen <strong>"Algoritmik Tarama"</strong> sistemi üzerine inşa edilmiştir.</p>
        [span_9](start_span)<p>Verilen bilgiler otomatik olarak üretilmiş olup yatırım tavsiyesi niteliği taşımaz.[span_9](end_span)</p>
        <div class="disclaimer">Borsa işlemleri ciddi risk taşır. [span_10](start_span)Geçmiş performans gelecek sonuçların garantisi değildir.[span_10](end_span)</div>
    </div>
    """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        {css}
    </head>
    <body>
        <div class="container">
            {header_html}
            {explanation_box}
            {mood_html}
            {rec_html}
            {footer_html}
        </div>
    </body>
    </html>
    """

def send_email(html_body: str, chart_paths: list = None, subject: str = None) -> bool:
    """
    [span_11](start_span)Email'i SendGrid API üzerinden güvenli bir şekilde gönderir.[span_11](end_span)
    """
    if not SENDGRID_AVAILABLE:
        print("X HATA: SendGrid kütüphanesi yüklü değil!")
        return False

    # [span_12](start_span)HATA ÇÖZÜMÜ: GitHub Secrets (os.environ) öncelikli, config ise yedek.[span_12](end_span)
    # Eğer config'de değişken yoksa hata vermemesi için getattr kullanıldı.
    api_key = os.environ.get("SENDGRID_API_KEY") or getattr(config, 'SENDGRID_API_KEY', None)
    sender_email = os.environ.get("MAIL_SENDER") or getattr(config, 'MAIL_SENDER', None)
    
    # İSTEK: Sabit alıcı adresi
    recipient_email = "ahm.cagil@hotmail.com"

    if not api_key:
        print("X HATA: SENDGRID_API_KEY bulunamadı! Lütfen GitHub Secrets veya config dosyanızı kontrol edin.")
        return False

    if subject is None:
        subject = f"Borsa Analiz Raporu - {datetime.now().strftime('%d.%m.%Y')}"

    try:
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        from_email = Email(sender_email)
        to_email = To(recipient_email)
        content = Content("text/html", html_body)
        
        mail = Mail(from_email, to_email, subject, content)

        # [span_13](start_span)Grafik Dosyalarını Ekleme (Attachment)[span_13](end_span)
        if chart_paths:
            for path in chart_paths:
                if os.path.exists(path):
                    with open(path, 'rb') as f:
                        data = f.read()
                        encoded_file = base64.b64encode(data).decode()
                        
                        attachment = Attachment(
                            FileContent(encoded_file),
                            FileName(os.path.basename(path)),
                            FileType('image/png'),
                            Disposition('attachment')
                        )
                        mail.add_attachment(attachment)
                        print(f"✔ Grafik eklendi: {os.path.basename(path)}")

        response = sg.client.mail.send.post(request_body=mail.get())
        
        if response.status_code in [200, 201, 202]:
            print(f"\n✔ Email başarıyla gönderildi!")
            print(f"📩 Alıcı: {recipient_email}")
            return True
        else:
            print(f"X SendGrid hata kodu: {response.status_code}")
            print(f"Detay: {response.body}")
            return False

    except Exception as e:
        print(f"X Email gönderim hatası oluştu: {e}")
        return False
