import os
import base64
from datetime import datetime
import config
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition

def generate_html_body(recommendations: dict, chart_paths: list) -> str:
    recs = recommendations.get("recommendations", [])
    date_str = datetime.now().strftime("%d %B %Y %H:%M")

    # Mail Tasarımı ve Puan Açıklaması
    body = f"""
    <html>
    <body style="font-family: Arial; color: #333;">
        <div style="background: #1a2e3e; color: white; padding: 20px; text-align: center;">
            <h2>Borsa Analiz Raporu</h2>
            <p>{date_str}</p>
        </div>
        
        <div style="background: #e7f3ff; border-left: 5px solid #2196F3; padding: 15px; margin: 20px 0;">
            <strong>Puanlama Sistemi:</strong> Bu sistem, teknik verileri 0-100 arası bir skora indirger. 
            Algoritmayı bilmeyenler için karmaşık verileri tek bir başarı puanıyla özetleyen bir bilgilendirmedir.
        </div>

        <h3>Öne Çıkan Hisseler</h3>
    """
    for rec in recs:
        body += f"""
        <div style="border: 1px solid #ddd; padding: 10px; margin-bottom: 10px;">
            <b style="font-size: 18px;">#{rec.get('rank')} {rec.get('ticker')}</b><br>
            Puan: {rec.get('score')}/100 | Sinyal: {rec.get('rating')}<br>
            Fiyat: {rec.get('price')}
        </div>
        """
    
    body += """
        <div style="margin-top: 30px; font-size: 12px; color: #666; text-align: center;">
            <p><strong>Not:</strong> Bu rapor "Algoritmik Tarama" sistemiyle otomatik üretilmiştir.</p>
            <p>Yatırım tavsiyesi değildir.</p>
        </div>
    </body>
    </html>
    """
    return body

def send_email(html_body: str, chart_paths: list = None, subject: str = None) -> bool:
    api_key = os.environ.get("SENDGRID_API_KEY") or config.SENDGRID_API_KEY
    if not api_key: return False

    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    mail = Mail(
        from_email=Email(config.MAIL_SENDER),
        to_emails=To(config.MAIL_RECIPIENT),
        subject=subject or f"Analiz Raporu - {datetime.now().strftime('%d.%m.%Y')}",
        html_content=Content("text/html", html_body)
    )

    if chart_paths:
        for path in chart_paths:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    data = base64.b64encode(f.read()).decode()
                    mail.add_attachment(Attachment(FileContent(data), FileName(os.path.basename(path)), FileType('image/png'), Disposition('attachment')))

    try:
        response = sg.send(mail)
        return response.status_code in [200, 201, 202]
    except Exception as e:
        print(f"Hata: {e}")
        return False
