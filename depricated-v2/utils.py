import smtplib
import qrcode
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import BytesIO
import base64

def generate_qr_code(link):
    qr = qrcode.make(link)
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def send_id_mail(student_data, event_url):
    msg = MIMEMultipart()
    msg['From'] = 'your_email@example.com'
    msg['To'] = student_data['email']
    msg['Subject'] = 'Your Event ID Card'
    
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
            <div class="title">Welcome to the Event</div>
            <div class="student-info">
                <p><strong>Name:</strong> {student_data['name']}</p>
                <p><strong>Roll No:</strong> {student_data['rollno']}</p>
                <p><strong>Email:</strong> {student_data['email']}</p>
            </div>
            <div class="qr-code">
                <img src="data:image/png;base64,{qr_code_data}" alt="QR Code">
            </div>
            <p>Scan the QR code to access event details</p>
        </div>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(body, 'html'))
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('your_email@example.com', 'your_password')
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()
    
    print("ID mail sent successfully!")
