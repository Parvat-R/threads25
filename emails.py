import smtplib
import qrcode
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from io import BytesIO
import base64
import dotenv
import os
import time
from utils import generate_qr_code, generate_otp
import _thread
import logging
import threading
import queue

dotenv.load_dotenv()
EMAIL = os.getenv("GMAIL")
EMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
# EMAIL = os.getenv("SONATECH_MAIL")
# EMAIL_PASSWORD = os.getenv("SONATECH_PASSWORD")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Email queue and worker thread
email_queue = queue.Queue()
stop_event = threading.Event()

def email_worker():
    """Worker thread that processes emails from the queue with rate limiting"""
    server = None
    while not stop_event.is_set() or not email_queue.empty():
        # Try to establish connection if we don't have one
        if server is None:
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(EMAIL, EMAIL_PASSWORD)
                logger.info("Email worker connected to SMTP server")
            except Exception as e:
                logger.error(f"Failed to connect to SMTP server: {e}")
                time.sleep(30)  # Wait before trying again
                continue  # Skip to next iteration

        # Process emails from the queue
        try:
            message = email_queue.get(timeout=1)
            server.send_message(message)
            logger.info(f"Sent email to {message['To']}")
            email_queue.task_done()
            
            # Rate limiting - pause between emails
            time.sleep(1)  # Adjust based on Gmail's rate limits
            
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            # Close the broken connection
            try:
                if server:
                    server.quit()
            except:
                pass
            server = None  # Force reconnection on next iteration
            
            # Put the failed message back in the queue
            if 'message' in locals():
                email_queue.put(message)
                logger.info(f"Requeued email to {message['To']}")
                
    # Clean up
    if server:
        try:
            server.quit()
        except:
            pass
    logger.info("Email worker stopped")

# Start the email worker thread
worker_thread = threading.Thread(target=email_worker)
worker_thread.daemon = True
worker_thread.start()

def enqueue_email(msg):
    """Add an email to the sending queue"""
    email_queue.put(msg)
    return True

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

    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = email
    msg['Subject'] = "OTP Verification"
    msg.attach(MIMEText(body, 'html'))
    
    enqueue_email(msg)
    return otp

def send_id_mail(student_data, payment_data, event_url):
    qr_code_data = generate_qr_code(event_url)
    qr_code_binary = base64.b64decode(qr_code_data)
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = student_data['email']
    msg['Subject'] = "Your Event ID Card"
    
    # Attach the QR code image
    qr_image = MIMEImage(qr_code_binary)
    qr_image.add_header('Content-ID', '<qrcode>')
    qr_image.add_header('Content-Disposition', 'inline', filename='qrcode.png')
    msg.attach(qr_image)
    
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
                <img src="cid:qrcode" alt="QR Code">
            </div>
            <h1 class="title">Your Event ID Card</h1>
            <div class="student-info">
                <p>id: {event_url.split("/")[-1]}</p>
                <p>Name: {student_data['name']}</p>
                <p>Email: {student_data['email']}</p>
                <p>Phone: {student_data['phone']}</p>             
                <p>Events: {student_data['events']}</p>             
                <p>Paid: {payment_data['paid']}</p>             
                <p>Is Cash?: {payment_data['is_cash']}</p>             
            </div>
        </div>
    </body>
    </html>
    """
    
    html_part = MIMEText(body, 'html')
    msg.attach(html_part)
    
    enqueue_email(msg)
    return True

# Cleanup function to stop the worker thread
import atexit

def cleanup():
    stop_event.set()
    worker_thread.join(timeout=60)
    logger.info("Email system shutdown complete")

atexit.register(cleanup)