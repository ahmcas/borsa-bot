import os
import base64
from datetime import datetime
import config

try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

def generate_html_body(recommendations: dict, chart_paths: list) -> str:
    recs = recommendations.get("recommendations", [])
    date_str = datetime.now().strftime("%d %B %Y %H:%M")

    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="background: #1a2e3e; color: white; padding: 25px; text-align: center;">
            <h1 style="margin: 0;">Borsa Analiz Raporu</h1>
            <p style="margin: 5px 0;">{date_str} | Algoritmik Tarama</p>
        </div>
        
        <div style="background: #e7f3ff; border-left: 5px solid #2196F3; padding: 15px; margin: 20px;">
            <strong>Puan Açıklaması:</strong> Bu puan, hissenin teknik gücünü 0-100 arasında özetler. 
            Algoritmayı bilmeyen birinin bile hissenin durumunu tek bakışta anlamasını sağlayan bir göstergedir.
        </div>

        <div style="padding: 0 20px;">
    """
    
    if recs:
        for rec in recs:
            body += f"""
            <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 8px;">
                <b style="font-size: 18px;">#{rec.get('rank')} {rec.get('ticker')}</b><br>
                Sinyal: {rec.get('rating')} | Skor: {rec.get('score')}/100<br>
                Fiyat: {rec.get('price')}
            </div>
            """
    else:
        body += "<p>Bugün uygun hisse bulunamadı.</p>"

    body += """
        </div>
        <div style="background: #f8f9fa; padding: 20px; text-align: center; font-size: 11px; color: #666;">
            <p>Bu rapor <b>Algoritmik Tarama</b> sistemi tarafından otomatik üretilmiştir.</p>
            <p>Yatırım tavsiyesi değildir.</p>
        </div>
    </body>
    </html>
    """
    return body

def send_email(html_body: str, chart_paths: list = None, subject: str = None) -> bool:
    api_key = os.environ.get("SENDGRID_API_KEY") or config.SENDGRID_API_KEY
    if not api_key:
        print("X SENDGRID_API_KEY bulunamadı!")
        return False

    sg = sendgrid.SendGridAPIClient(api_key=api_key)
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
                    print(f"Grafik eklendi: {os.path.basename(path)}")

    try:
        response = sg.send(mail)
        if response.status_code in [200, 201, 202]:
            print(f"Email başarıyla gönderildi! Alıcı: {to_addr}")
            return True
        else:
            print(f"X SendGrid hata kodu: {response.status_code}")
            return False
    except Exception as e:
        print(f"X Gönderim hatası: {e}")
        return False
