import smtplib
import qrcode
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import BytesIO
import base64
import dotenv
import os
from utils import generate_qr_code, generate_otp
import _thread

dotenv.load_dotenv()
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_email(subject, to, body, subtype='html'):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, subtype))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        server.sendmail(EMAIL, to, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(e)
        return False


def send_otp(email: str) -> int:
    otp = generate_otp()
    body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #fff;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                color: #333;
            }}
            p {{
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>OTP Verification</h1>
            <p>Hello {email},</p>
            <p>Use the following OTP to verify your account:</p>
            <h2>{otp}</h2>
            <p>This OTP is valid for 10 minutes.</p>
            <p>Thanks,<br>The Threads 25 Team</p>
        </div>
    </body>
    </html>
    """

    _thread.start_new_thread(send_email, ("OTP Verification", email, body))
    return otp


def send_id_mail(student_data, event_url):
    qr_code_data = generate_qr_code(event_url)
    body = f"""
    <html>
    <head>
        <style>
            .id-card {{
                width: 300px;
                padding: 20px;
                border: 2px solid #000;
                border-radius: 10px;
                text-align: center;
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
            }}
            .qr-code {{
                margin-top: 15px;
            }}
            .title {{
                font-size: 20px;
                font-weight: bold;
            }}
            .student-info {{
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="id-card">
            <div class="qr-code">
                <img src="data:image/png;base64,{qr_code_data}" alt="QR Code">
            </div>
            <h1 class="title">Your Event ID Card</h1>
            <div class="student-info">
                <p>Name: {student_data['name']}</p>
                <p>Email: {student_data['email']}</p>
                <p>Phone: {student_data['phone']}</p>
                <p>Roll No: {student_data['rollno']}</p>                
            </div>
        </div>
    </body>
    </html>
    """
    _thread.start_new_thread(send_email, ("Your Event ID Card", student_data['email'], body))
    return True