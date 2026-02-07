import os
import base64
from datetime import datetime
import config
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition

def generate_html_body(recommendations: dict, chart_paths: list) -> str:
    recs = recommendations.get("recommendations", [])
    date_str = datetime.now().strftime("%d %B %Y %H:%M")

    # Puan açıklaması mailin başında yer alıyor
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="background: #1a2e3e; color: white; padding: 25px; text-align: center;">
            <h1 style="margin: 0;">Borsa Analiz Raporu</h1>
            <p style="margin: 5px 0;">{date_str} | Algoritmik Tarama</p>
        </div>
        
        <div style="background: #e7f3ff; border-left: 5px solid #2196F3; padding: 15px; margin: 20px;">
            <strong>Puan Açıklaması:</strong> Bu sistem, teknik verileri 0-100 arası bir skora dönüştürür. 
            Algoritmayı bilmeyen birinin bile hissenin gücünü tek bir puanla anlamasını sağlayan bir özet bilgilendirmedir.
        </div>

        <div style="padding: 0 20px;">
            <h3>Seçilen Hisseler</h3>
    """
    
    if recs:
        for rec in recs:
            body += f"""
            <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin-bottom: 15px; background: #fafafa;">
                <b style="font-size: 20px; color: #1a2e3e;">#{rec.get('rank')} {rec.get('ticker')}</b><br>
                <span style="background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">{rec.get('rating')}</span>
                <p style="margin: 10px 0 0 0;">Fiyat: <b>{rec.get('price')}</b> | Teknik Skor: <b>{rec.get('score')}/100</b></p>
            </div>
            """
    else:
        body += "<p>Uygun hisse bulunamadı.</p>"

    body += """
        </div>
        <div style="background: #f1f5f9; padding: 20px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0;">
            <p><strong>Sistem Bilgisi:</strong> Bu rapor, hisseleri otomatik seçen "Algoritmik Tarama" sistemi üzerine inşa edilmiştir.</p>
            <p>Yatırım tavsiyesi değildir. Borsa işlemleri risk taşır.</p>
        </div>
    </body>
    </html>
    """
    return body

def send_email(html_body: str, chart_paths: list = None, subject: str = None) -> bool:
    # Secrets'tan anahtarı çek
    api_key = os.environ.get("SENDGRID_API_KEY") or config.SENDGRID_API_KEY
    if not api_key:
        print("X SENDGRID_API_KEY bulunamadı!")
        return False

    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    
    # Secrets isimlerini kullanarak gönderici ve alıcıyı ayarla
    from_addr = os.environ.get("MAIL_SENDER") or config.MAIL_SENDER
    to_addr = os.environ.get("MAIL_RECIPIENT") or config.MAIL_RECIPIENT

    mail = Mail(
        from_email=Email(from_addr),
        to_emails=To(to_addr),
        subject=subject or f"Analiz Raporu - {datetime.now().strftime('%d.%m.%Y')}",
        html_content=Content("text/html", html_body)
    )

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
                    [span_2](start_span)print(f"Grafik eklendi: {os.path.basename(path)}")[span_2](end_span)

    try:
        response = sg.send(mail)
        [span_3](start_span)if response.status_code in [200, 201, 202]:[span_3](end_span)
            [span_4](start_span)print(f"Email başarıyla gönderildi! Alıcı: {to_addr}")[span_4](end_span)
            return True
        else:
            [span_5](start_span)print(f"SendGrid hata kodu: {response.status_code}")[span_5](end_span)
            return False
    except Exception as e:
        [span_6](start_span)print(f"Gönderim hatası: {e}")[span_6](end_span)
        return False
