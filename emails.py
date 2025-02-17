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
import dns.resolver

dotenv.load_dotenv()
EMAIL = os.getenv("GMAIL")
EMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Email queue and worker thread
email_queue = queue.Queue()
stop_event = threading.Event()

def verify_email_domain(email):
    """Verify if the email domain exists and has valid MX records"""
    try:
        domain = email.split('@')[1]
        mx_records = dns.resolver.resolve(domain, 'MX')
        return True if mx_records else False
    except Exception as e:
        logger.warning(f"Domain verification failed for {email}: {e}")
        return False

def enqueue_email(msg):
    """Add an email to the sending queue and return status"""
    try:
        recipient = msg['To']
        
        # Verify domain before enqueueing
        if '@outlook' in recipient.lower() or '@hotmail' in recipient.lower() or '@live' in recipient.lower():
            if not verify_email_domain(recipient):
                logger.error(f"Invalid email domain for {recipient}")
                return False
        
        email_queue.put(msg)
        logger.info(f"Email to {recipient} added to queue")
        return True
    except Exception as e:
        logger.error(f"Failed to enqueue email: {e}")
        return False

def email_worker():
    """Worker thread that processes emails from the queue with rate limiting"""
    server = None
    retry_count = 0
    max_retries = 3
    
    while not stop_event.is_set() or not email_queue.empty():
        if server is None:
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(EMAIL, EMAIL_PASSWORD)
                # Set a longer timeout for Outlook domains
                server.timeout = 30
                logger.info("Email worker connected to SMTP server")
                retry_count = 0
            except Exception as e:
                logger.error(f"Failed to connect to SMTP server: {e}")
                time.sleep(30)
                continue

        try:
            message = email_queue.get(timeout=1)
            recipient = message['To']
            
            # Additional checks for Outlook domains
            if '@outlook' in recipient.lower() or '@hotmail' in recipient.lower() or '@live' in recipient.lower():
                # Add additional headers for better deliverability to Outlook
                message['X-Priority'] = '3'
                message['X-MSMail-Priority'] = 'Normal'
                message['Precedence'] = 'Bulk'
                message['X-Auto-Response-Suppress'] = 'OOF, AutoReply'

            # Set the message date
            message['Date'] = time.strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Try sending with retries for Outlook domains
            send_success = False
            for attempt in range(max_retries):
                try:
                    server.send_message(message)
                    send_success = True
                    break
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for {recipient}: {e}")
                    time.sleep(2 * (attempt + 1))  # Exponential backoff
                    
                    # Reconnect on failure
                    try:
                        if server:
                            server.quit()
                    except:
                        pass
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(EMAIL, EMAIL_PASSWORD)
                    server.timeout = 30

            if send_success:
                logger.info(f"Sent email to {recipient}")
                email_queue.task_done()
                time.sleep(1)  # Rate limiting
            else:
                logger.error(f"Failed to send email to {recipient} after {max_retries} attempts")
                email_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Error in email worker: {e}")
            try:
                if server:
                    server.quit()
            except:
                pass
            server = None

    # Cleanup
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

def send_otp(email: str) -> int:
    otp = generate_otp()
    body = f"""
    <html>
<head>
    <meta name="x-apple-disable-message-reformatting">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background-color: #1a0f2e;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 30px;
            background: linear-gradient(135deg, #1a0f2e 0%, #2d1b4e 100%);
            border: 2px solid #ff2e88;
            border-radius: 15px;
            box-shadow: 0 0 20px rgba(255, 46, 136, 0.3);
            position: relative;
            overflow: hidden;
        }}
        .container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent 48%, rgba(255, 46, 136, 0.1) 50%, transparent 52%);
            background-size: 20px 20px;
            z-index: 1;
        }}
        .content {{
            position: relative;
            z-index: 2;
        }}
        h1 {{
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-align: center;
            margin-bottom: 30px;
            font-size: 28px;
            text-shadow: 0 0 10px rgba(255, 46, 136, 0.5);
        }}
        p {{
            color: #ffffff;
            line-height: 1.6;
            margin-bottom: 20px;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
        }}
        .otp-container {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 46, 136, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin: 30px 0;
            text-align: center;
        }}
        .otp {{
            font-family: 'Courier New', monospace;
            font-size: 36px;
            letter-spacing: 8px;
            color: #ff2e88;
            margin: 0;
            text-shadow: 0 0 15px rgba(255, 46, 136, 0.7);
        }}
        .timer {{
            color: #ff2e88;
            font-size: 14px;
            margin-top: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .signature {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 46, 136, 0.3);
            color: #ff2e88;
            font-weight: bold;
            letter-spacing: 1px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            <h1>Verify Your Account</h1>
            <p>Hello {email},</p>
            <div class="otp-container">
                <h2 class="otp">{otp}</h2>
                <div class="timer">Valid for 10 minutes</div>
            </div>
            <p>Use the OTP above to complete your verification process. Do not share this code with anyone.</p>
            <div class="signature">
                <p>THREADS'25 TEAM<br>HACK • CREATE • DOMINATE</p>
            </div>
        </div>
    </div>
</body>
</html>
    """

    msg = MIMEMultipart('alternative')
    msg['From'] = f"Threads 25 <{EMAIL}>"  # Using a friendly name
    msg['To'] = email
    msg['Subject'] = "OTP Verification"
    msg['Message-ID'] = f"<{time.time()}.{os.getpid()}@gmail.com>"
    msg.attach(MIMEText(body, 'html'))
    
    return otp if enqueue_email(msg) else None

def send_id_mail(student_data, payment_data, event_url):
    print(event_url)
    qr_code_data = generate_qr_code(event_url)
    qr_code_binary = base64.b64decode(qr_code_data)
    
    msg = MIMEMultipart()
    msg['From'] = f"Threads 25 <{EMAIL}>"
    msg['To'] = student_data['email']
    msg['Subject'] = "Your Event ID Card"
    msg['Message-ID'] = f"<{time.time()}.{os.getpid()}@gmail.com>"
    
    # Attach the QR code image
    qr_image = MIMEImage(qr_code_binary)
    qr_image.add_header('Content-ID', '<qrcode>')
    qr_image.add_header('Content-Disposition', 'inline', filename='qrcode.png')
    msg.attach(qr_image)
    
    body = """
    <html>
<head>
    <meta name="x-apple-disable-message-reformatting">
    <style>
        .id-card {{
            max-width: 400px;
            margin: 20px auto;
            padding: 25px;
            background: linear-gradient(135deg, #1a0f2e 0%, #2d1b4e 100%);
            border: 2px solid #ff2e88;
            border-radius: 15px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            position: relative;
            overflow: hidden;
            box-shadow: 0 0 20px rgba(255, 46, 136, 0.3);
        }}

        .id-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent 48%, rgba(255, 46, 136, 0.1) 50%, transparent 52%);
            background-size: 20px 20px;
            z-index: 1;
        }}

        .header {{
            background: linear-gradient(135deg, #2d1b4e 0%, #1a0f2e 100%);
            margin: -25px -25px 20px -25px;
            padding: 20px;
            border-bottom: 2px solid #ff2e88;
            position: relative;
        }}

        .title {{
            font-size: 28px;
            font-weight: bold;
            margin: 0;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #ffffff;
            text-shadow: 0 0 10px rgba(255, 46, 136, 0.5);
        }}

        .qr-code {{
            text-align: center;
            margin: 20px 0;
            padding: 10px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            border: 1px solid rgba(255, 46, 136, 0.3);
        }}

        .qr-code img {{
            max-width: 150px;
            height: auto;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 12px;
            margin-top: 20px;
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid rgba(255, 46, 136, 0.3);
            position: relative;
            z-index: 2;
        }}

        .label {{
            font-weight: 600;
            color: #ff2e88;
            text-align: right;
            padding-right: 15px;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 1px;
        }}

        .value {{
            color: #ffffff;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
        }}

        .status {{
            margin-top: 20px;
            text-align: center;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 14px;
            letter-spacing: 2px;
            position: relative;
            z-index: 2;
        }}

        .status.paid {{
            background: rgba(39, 174, 96, 0.2);
            border: 1px solid #27ae60;
            color: #27ae60;
            text-shadow: 0 0 10px rgba(39, 174, 96, 0.5);
        }}

        .status.unpaid {{
            background: rgba(231, 76, 60, 0.2);
            border: 1px solid #e74c3c;
            color: #e74c3c;
            text-shadow: 0 0 10px rgba(231, 76, 60, 0.5);
        }}

        .id-number {{
            text-align: center;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #ff2e88;
            margin-top: 15px;
            padding: 8px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 5px;
            letter-spacing: 2px;
            border: 1px solid rgba(255, 46, 136, 0.3);
        }}
    </style>
</head>
<body>
    <div class="id-card">
        <div class="header">
            <h1 class="title">Threads'25 Pass</h1>
        </div>
        
        <div class="qr-code">
            <img src="cid:qrcode" alt="QR Code">
        </div>

        <div class="info-grid">
            <div class="label">Name:</div>
            <div class="value">{name}</div>
            
            <div class="label">Email:</div>
            <div class="value">{email}</div>
            
            <div class="label">Phone:</div>
            <div class="value">{phone}</div>
            
            <div class="label">Events:</div>
            <div class="value">{events}</div>
        </div>

        <div class="status {status_class}">
            {payment_status}
        </div>

        <div class="id-number">
            ID: {event_id}
        </div>
    </div>
</body>
</html>
    """.format(
        student_data=student_data,
        status_class="paid" if payment_data['paid'] else "unpaid",
        payment_status="Paid" if payment_data['paid'] else "Unpaid",
        event_id=event_url.split("/")[-1],
        name = student_data["name"],
        email = student_data["email"],
        phone = student_data["phone"],
        events = student_data["events"]
    )

    html_part = MIMEText(body, 'html')
    msg.attach(html_part)
    
    return enqueue_email(msg)

# Cleanup function to stop the worker thread
import atexit

def cleanup():
    stop_event.set()
    worker_thread.join(timeout=60)
    logger.info("Email system shutdown complete")

atexit.register(cleanup)