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
    print("! SendGrid yüklü değil, pip install sendgrid ile yükleyin")

def generate_html_body(recommendations: dict, chart_paths: list) -> str:
    """
    Sade ve anlaşılır HTML mail body üretir.
    """
    market_mood = recommendations.get("market_mood", "Belirsiz")
    recs = recommendations.get("recommendations", [])
    date_str = datetime.now().strftime("%d %B %Y %H:%M")

    # CSS Stilleri
    css = """
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f0f4f8; margin: 0; padding: 20px; }
        .container { max-width: 700px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #1a2e3e, #16213e); padding: 30px; text-align: center; color: #fff; }
        .header h1 { margin: 0 0 6px; font-size: 24px; }
        .info-box { background: #e0f2fe; padding: 15px; margin: 20px; border-left: 5px solid #0369a1; font-size: 14px; color: #0c4a6e; border-radius: 4px; }
        .mood-bar { background: #1e293b; padding: 14px; text-align: center; color: #2e8f0; font-weight: 600; }
        .section { padding: 22px 24px; }
        .card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 15px; margin-bottom: 20px; }
        .ticker-name { font-size: 20px; font-weight: 800; color: #1e293b; }
        .rating-box { display: inline-block; padding: 4px 12px; border-radius: 6px; font-weight: bold; margin-top: 5px; }
        .rating-strong-buy { background: #dcfce7; color: #166534; }
        .rating-buy { background: #dbeafe; color: #1e40af; }
        .rating-hold { background: #fef3c7; color: #92400e; }
        .footer { background: #f1f5f9; padding: 20px; text-align: center; font-size: 11px; color: #64748b; }
    </style>
    """

    # 1. Puan Açıklaması (İsteğiniz üzerine en başa eklendi)
    explanation_header = """
    <div class="info-box">
        <strong>Puanlama Sistemi Açıklaması:</strong><br>
        Bu rapor, teknik göstergeler, hacim verileri ve fiyat hareketlerini 0-100 arası bir puana dönüştürerek hisselerin kısa vadeli potansiyelini ölçer.
        <br><br>
        <em>Bilgilendirme: Bu sistem, algoritmayı hiç bilmeyenler için karmaşık verileri tek bir başarı skoruna indirgeyen "Algoritmik Tarama" modelidir.</em>
    </div>
    """

    header = f"""
    <div class="header">
        <h1>Borsa Analiz Raporu</h1>
        <p>{date_str} | Günlük Analiz</p>
    </div>
    """

    mood_html = f'<div class="mood-bar">Piyasa Duygusu: {market_mood}</div>'

    # Önerilen Hisseler Bölümü
    rec_section = ""
    if recs:
        cards = ""
        for rec in recs:
            rating_text = rec.get("rating", "TUT")
            rating_class = "rating-strong-buy" if "GÜÇLÜ" in rating_text else "rating-buy" if "AL" in rating_text else "rating-hold"
            
            cards += f"""
            <div class="card">
                <div class="ticker-name">#{rec.get('rank', '-')} {rec.get('ticker', 'N/A')}</div>
                <div class="rating-box {rating_class}">{rating_text}</div>
                <p><strong>Sektör:</strong> {rec.get('sector', 'Bilinmiyor')}</p>
                <p><strong>Fiyat:</strong> {rec.get('price', '0.00')} | <strong>Skor:</strong> {rec.get('score', 0)}/100</p>
            </div>
            """
        rec_section = f'<div class="section"><h3>Bugün Önerilen Hisseler ({len(recs)} Adet)</h3>{cards}</div>'
    else:
        rec_section = '<div class="section"><p>Bugün kriterlere uygun hisse bulunamadı.</p></div>'

    footer = """
    <div class="footer">
        <p><strong>Not:</strong> Bu rapor "Algoritmik Tarama" sistemiyle rastgele seçilen veriler üzerinden üretilmiştir.</p>
        <p>Yatırım tavsiyesi değildir. Borsa işlemleri risk içerir.</p>
    </div>
    """

    full_html = f"<html><head>{css}</head><body><div class='container'>{header}{explanation_header}{mood_html}{rec_section}{footer}</div></body></html>"
    return full_html

def send_email(html_body: str, chart_paths: list = None, subject: str = None) -> bool:
    if not SENDGRID_AVAILABLE:
        print("X SendGrid paketi yüklü değil!")
        return False

    if subject is None:
        subject = f"Borsa Analiz Raporu - {datetime.now().strftime('%d %m %Y')}"

    api_key = os.environ.get("SENDGRID_API_KEY", config.SENDGRID_API_KEY)
    # İsteğiniz üzerine alıcı adresi sabitlendi
    recipient_email = "ahm.cagil@hotmail.com" 
    sender_email = os.environ.get("MAIL_SENDER", config.MAIL_SENDER)

    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    from_email = Email(sender_email)
    to_email = To(recipient_email)
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content)

    # Grafik ekleme mantığı
    if chart_paths:
        for path in chart_paths:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    data = f.read()
                    encoded = base64.b64encode(data).decode()
                    attachment = Attachment(
                        FileContent(encoded),
                        FileName(os.path.basename(path)),
                        FileType('image/png'),
                        Disposition('attachment')
                    )
                    mail.add_attachment(attachment)

    try:
        response = sg.client.mail.send.post(request_body=mail.get())
        if response.status_code in [200, 201, 202]:
            print(f"✔ Email başarıyla {recipient_email} adresine gönderildi!")
            return True
        else:
            print(f"X SendGrid Hatası: {response.status_code}")
            return False
    except Exception as e:
        print(f"X Gönderim Hatası: {e}")
        return False
