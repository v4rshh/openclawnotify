
"""
openclaw send notification on WhatsApp

Reads device data (mocked), checks alert thresholds,
and sends WhatsApp messages via Meta Cloud API.
Falls back to Gmail SMTP if WhatsApp delivery fails.
"""

import os, json, time, smtplib, logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from dotenv import load_dotenv

load_dotenv()  # Load .env file

# CONFIG  ← fill via .env (never hardcode keys here)
WHATSAPP_TOKEN    = os.getenv('WHATSAPP_TOKEN')      # <<< API KEY
PHONE_NUMBER_ID   = os.getenv('PHONE_NUMBER_ID')     # <<< PHONE ID
RECIPIENT_PHONE   = os.getenv('RECIPIENT_PHONE')     # <<< TARGET
GMAIL_USER        = os.getenv('GMAIL_USER')
GMAIL_APP_PASSWORD= os.getenv('GMAIL_APP_PASSWORD')
ALERT_EMAIL_TO    = os.getenv('ALERT_EMAIL_TO')
COOLDOWN_HOURS    = int(os.getenv('COOLDOWN_HOURS', '4'))

WA_API_URL = (f'https://graph.facebook.com/v19.0/'
              f'{PHONE_NUMBER_ID}/messages')

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s')
log = logging.getLogger(__name__)

# MOCK DATA  (replace with real DynamoDB fetch)
MOCK_DEVICES = [
    {"device_id": "FL-1023", "tank_level": 18,
     "sump_level": 12, "timestamp": "2026-06-08T10:30:00Z"},
    {"device_id": "FL-1024", "tank_level": 80,
     "sump_level": 45, "timestamp": "2026-06-08T10:30:00Z"},
    {"device_id": "FL-1025", "tank_level": 50,
     "sump_level": 5,  "timestamp": "2026-06-08T10:30:00Z"},
]

THRESHOLDS = {
    "tank_low":    25,   # % below → alert
    "tank_high":   75,   # % above → alert
    "sump_low":    10,   # % below → alert
}

# In-memory alert tracker: {device_id_alerttype: datetime}
last_alert_sent: dict = {}



# DYNAMODB FETCH  (swap mock when ready)
def fetch_device_data() -> list:
    """
    For production: uncomment boto3 block and remove MOCK_DEVICES.
    """
    # import boto3
    # table = boto3.resource("dynamodb").Table("device_data")
    # return table.scan()["Items"]
    log.info('Using mock device data (DynamoDB not connected)')
    return MOCK_DEVICES


# COOLDOWN CHECK

def can_send_alert(device_id: str, alert_type: str) -> bool:
    key = f'{device_id}_{alert_type}'
    last = last_alert_sent.get(key)
    if last is None:
        return True
    return datetime.utcnow() - last > timedelta(hours=COOLDOWN_HOURS)

def mark_alert_sent(device_id: str, alert_type: str):
    last_alert_sent[f'{device_id}_{alert_type}'] = datetime.utcnow()


 
# WHATSAPP SENDER
def send_whatsapp(message: str) -> bool:
    """Send a text message via Meta WhatsApp Cloud API."""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": RECIPIENT_PHONE,
        "type": "text",
        "text": {"body": message}
    }
    try:
        resp = requests.post(WA_API_URL, headers=headers,
                             json=payload, timeout=10)
        resp.raise_for_status()
        log.info(f'WhatsApp sent | id={resp.json().get("messages", [{}])[0].get("id")}')
        return True
    except Exception as e:
        log.error(f'WhatsApp failed: {e}')
        return False


# SMTP FALLBACK SENDER
def send_email(subject: str, body: str) -> bool:
    """SMTP fallback using Gmail App Password."""
    if not all([GMAIL_USER, GMAIL_APP_PASSWORD, ALERT_EMAIL_TO]):
        log.warning('SMTP not configured, skipping email fallback')
        return False
    try:
        msg = MIMEMultipart()
        msg["From"]    = GMAIL_USER
        msg["To"]      = ALERT_EMAIL_TO
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, ALERT_EMAIL_TO, msg.as_string())
        log.info(f'Email sent → {ALERT_EMAIL_TO}')
        return True
    except Exception as e:
        log.error(f'Email failed: {e}')
        return False


# ALERT DISPATCHER
def dispatch_alert(device_id: str, alert_type: str,
                   wa_msg: str, email_subject: str,
                   email_body: str):
    if not can_send_alert(device_id, alert_type):
        log.info(f'[{device_id}] {alert_type}: cooldown active, skipping')
        return
    log.info(f'[{device_id}] Dispatching alert: {alert_type}')
    ok = send_whatsapp(wa_msg)
    if not ok:
        send_email(email_subject, email_body)  # fallback
    mark_alert_sent(device_id, alert_type)


# THRESHOLD CHECKS
def check_device(device: dict):
    did   = device['device_id']
    tank  = device.get('tank_level', 100)
    sump  = device.get('sump_level', 100)
    ts    = device.get('timestamp', 'N/A')

    # 1. Low tank
    if tank < THRESHOLDS['tank_low']:
        wa  = (f'*ALERT [{did}]* — Low Tank Level\n'
               f'Tank: {tank}% (threshold: {THRESHOLDS["tank_low"]}%)\n'
               f'Please check water supply.\nTime: {ts}')
        sub = f'[{did}] Low Tank Level Alert'
        body = (f'Device: {did}\nTank Level: {tank}%\n'
                f'Threshold: {THRESHOLDS["tank_low"]}%\nTime: {ts}')
        dispatch_alert(did, 'tank_low', wa, sub, body)

    # 2. High tank
    elif tank > THRESHOLDS['tank_high']:
        wa  = (f'*ALERT [{did}]* — High Tank Level\n'
               f'Tank: {tank}% (threshold: {THRESHOLDS["tank_high"]}%)\n'
               f'Tank is nearly full.\nTime: {ts}')
        sub = f'[{did}] High Tank Level Alert'
        body = (f'Device: {did}\nTank Level: {tank}%\n'
                f'Threshold: {THRESHOLDS["tank_high"]}%\nTime: {ts}')
        dispatch_alert(did, 'tank_high', wa, sub, body)

    # 3. Low sump
    if sump < THRESHOLDS['sump_low']:
        wa  = (f'*ALERT [{did}]* — Low Sump Level\n'
               f'Sump: {sump}% (threshold: {THRESHOLDS["sump_low"]}%)\n'
               f'Water transfer may be affected.\nTime: {ts}')
        sub = f'[{did}] Low Sump Level Alert'
        body = (f'Device: {did}\nSump Level: {sump}%\n'
                f'Threshold: {THRESHOLDS["sump_low"]}%\nTime: {ts}')
        dispatch_alert(did, 'sump_low', wa, sub, body)


# MAIN LOOP
def run_service(poll_interval_seconds: int = 300):
    """
    Main polling loop.
    poll_interval_seconds: how often to check (default 5 min).
    """
    log.info('Notification service started')
    while True:
        devices = fetch_device_data()
        for device in devices:
            check_device(device)
        log.info(f'Cycle complete. Sleeping {poll_interval_seconds}s...')
        time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    run_service(poll_interval_seconds=300)  # check every 5 minutes
