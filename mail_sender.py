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

def generate_html_body(recommendations: dict, chart_paths: list) -> str:
    """Sade, anlaşılır ve istenen açıklamaları içeren HTML mail gövdesi üretir."""
    market_mood = recommendations.get("market_mood", "Belirsiz")
    recs = recommendations.get("recommendations", [])
    date_str = datetime.now().strftime("%d %B %Y %H:%M")

    # CSS Tasarımı
    css = """
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
        .container { max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
        .header { background: #1a2e3e; padding: 25px; text-align: center; color: #ffffff; }
        .info-box { background: #e7f3ff; border-left: 4px solid #2196F3; padding: 15px; margin: 20px; font-size: 14px; color: #0d47a1; }
        .mood-bar { background: #333; color: #00ff00; text-align: center; padding: 10px; font-weight: bold; }
        .section { padding: 20px; }
        .card { border: 1px solid #eee; border-radius: 8px; padding: 15px; margin-bottom: 15px; background: #fafafa; }
        .ticker { font-size: 22px; font-weight: bold; color: #1a2e3e; }
        .rating { display: inline-block; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; margin-top: 5px; }
        .rating-strong { background: #d4edda; color: #155724; }
        .rating-buy { background: #cce5ff; color: #004085; }
        .rating-hold { background: #fff3cd; color: #856404; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; font-size: 11px; color: #6c757d; border-top: 1px solid #eee; }
    </style>
    """

    # 1. [span_0](start_span)[span_1](start_span)Puan Açıklaması (Mailin başında yer alacak)[span_0](end_span)[span_1](end_span)
    explanation_box = """
    <div class="info-box">
        <strong>Puan Açıklaması:</strong> Algoritma; teknik analiz, hacim ve trend verilerini harmanlayarak her hisseye 0-100 arası bir başarı skoru atar.
        <br><br>
        <em>Bu sistem, algoritmayı hiç bilmeyen birinin bile anlayacağı şekilde, hisselerin teknik gücünü tek bir puanla özetleyen bir bilgilendirme sistemidir.</em>
    </div>
    """

    header_html = f"""
    <div class="header">
        <h1 style="margin:0;">Borsa Analiz Raporu</h1>
        <p style="margin:5px 0 0 0; opacity:0.8;">{date_str} | Algoritmik Tarama</p>
    </div>
    """

    mood_html = f'<div class="mood-bar">Piyasa Duygusu: {market_mood}</div>'

    # Önerilen Hisseler
    rec_html = ""
    if recs:
        cards = ""
        for rec in recs:
            rating = rec.get("rating", "TUT")
            r_class = "rating-strong" if "GÜÇLÜ" in rating else "rating-buy" if "AL" in rating else "rating-hold"
            
            cards += f"""
            <div class="card">
                <div class="ticker">#{rec.get('rank', '0')} {rec.get('ticker', 'N/A')}</div>
                <div class="rating {r_class}">{rating}</div>
                <div style="margin-top:10px; color:#555;">
                    <b>Piyat:</b> {rec.get('price', '-')} | <b>Skor:</b> {rec.get('score', 0)}/100 | <b>Güven:</b> {rec.get('confidence', '-')}
                </div>
            </div>
            """
        rec_html = f'<div class="section"><h3 style="color:#1a2e3e;">Güncel Öneriler</h3>{cards}</div>'
    else:
        rec_html = '<div class="section"><p>Şu an kriterlere uygun hisse bulunamadı.</p></div>'

    # [span_2](start_span)Sabit footer ve Algoritmik Tarama Notu[span_2](end_span)
    footer_html = """
    <div class="footer">
        <p><strong>Sistem Notu:</strong> Bu rapor, hisseleri belirli kriterlere göre otomatik seçen "Algoritmik Tarama" sistemi üzerine inşa edilmiştir.</p>
        <p>Yatırım tavsiyesi değildir. Lütfen kendi risk analizinizi yapınız.</p>
    </div>
    """

    return f"<html><head>{css}</head><body><div class='container'>{header_html}{explanation_box}{mood_html}{rec_html}{footer_html}</div></body></html>"

def send_email(html_body: str, chart_paths: list = None, subject: str = None) -> bool:
    """SendGrid Secrets kullanarak mail gönderir."""
    if not SENDGRID_AVAILABLE:
        print("X HATA: sendgrid paketi yüklü değil!")
        return False

    # [span_3](start_span)Secrets'tan veya Config'den verileri çek[span_3](end_span)
    api_key = os.environ.get("SENDGRID_API_KEY") or config.SENDGRID_API_KEY
    sender_email = os.environ.get("MAIL_SENDER") or config.MAIL_SENDER
    # [span_4](start_span)Alıcı adresini isteğiniz üzerine sabitliyoruz[span_4](end_span)
    recipient_email = "ahm.cagil@hotmail.com"

    if not api_key:
        print("X HATA: SENDGRID_API_KEY bulunamadı!")
        return False

    if subject is None:
        subject = f"Borsa Analiz Raporu - {datetime.now().strftime('%d.%m.%Y')}"

    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    mail = Mail(
        from_email=Email(sender_email),
        to_emails=To(recipient_email),
        subject=subject,
        html_content=html_body
    )

    # [span_5](start_span)Grafikleri ekle[span_5](end_span)
    if chart_paths:
        for path in chart_paths:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    data = base64.b64encode(f.read()).decode()
                    attachment = Attachment(
                        FileContent(data),
                        FileName(os.path.basename(path)),
                        FileType('image/png'),
                        Disposition('attachment')
                    )
                    mail.add_attachment(attachment)

    try:
        response = sg.send(mail)
        if response.status_code in [200, 201, 202]:
            print(f"✔ Rapor başarıyla {recipient_email} adresine gönderildi!")
            return True
        else:
            print(f"X SendGrid Hatası! Kod: {response.status_code}")
            return False
    except Exception as e:
        print(f"X Gönderim sırasında hata oluştu: {e}")
        return False
