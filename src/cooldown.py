import os
from datetime import datetime, timedelta, timezone

COOLDOWN_HOURS = int(os.getenv('COOLDOWN_HOURS', '4'))

# In-memory alert tracker: {device_id_alerttype: datetime}
last_alert_sent = {}

def can_send_alert(device_id: str, alert_type: str) -> bool:
    """Check if the cooldown period has expired for the given device and alert type."""
    key = f"{device_id}_{alert_type}"
    last = last_alert_sent.get(key)
    if last is None:
        return True
    return datetime.now(timezone.utc) - last > timedelta(hours=COOLDOWN_HOURS)

def mark_alert_sent(device_id: str, alert_type: str):
    """Record the timestamp of a sent alert."""
    key = f"{device_id}_{alert_type}"
    last_alert_sent[key] = datetime.now(timezone.utc)
