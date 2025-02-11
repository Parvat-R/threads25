from io import BytesIO
import base64
import qrcode
import random

def generate_qr_code(link):
    qr = qrcode.make(link)
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def generate_otp():
    return random.randint(100000, 999999)