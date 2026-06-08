import logging
from src import cooldown
from src import openclaw_client

log = logging.getLogger(__name__)

# Alert threshold levels (%)
THRESHOLDS = {
    "tank_low": 25,    # % below -> alert
    "tank_high": 75,   # % above -> alert
    "sump_low": 10,    # % below -> alert
}

def dispatch_alert(device_id: str, alert_type: str, wa_msg: str):
    """Dispatch alert via OpenClaw if cooldown window has expired."""
    if not cooldown.can_send_alert(device_id, alert_type):
        log.info(f'[{device_id}] {alert_type}: Cooldown active, alert skipped')
        return

    log.info(f'[{device_id}] Dispatching alert: {alert_type}')
    success = openclaw_client.send_whatsapp(wa_msg)
    if success:
        cooldown.mark_alert_sent(device_id, alert_type)

def check_device(device: dict):
    """Check device tank and sump levels against thresholds and dispatch alerts."""
    did = device['device_id']
    tank = device.get('tank_level', 100)
    sump = device.get('sump_level', 100)
    ts = device.get('timestamp', 'N/A')

    # 1. Low tank check
    if tank < THRESHOLDS['tank_low']:
        wa = (f'*ALERT [{did}]* — Low Tank Level\n'
              f'Tank: {tank}% (threshold: {THRESHOLDS["tank_low"]}%)\n'
              f'Please check water supply.\nTime: {ts}')
        dispatch_alert(did, 'tank_low', wa)

    # 2. High tank check
    elif tank > THRESHOLDS['tank_high']:
        wa = (f'*ALERT [{did}]* — High Tank Level\n'
              f'Tank: {tank}% (threshold: {THRESHOLDS["tank_high"]}%)\n'
              f'Tank is nearly full.\nTime: {ts}')
        dispatch_alert(did, 'tank_high', wa)

    # 3. Low sump check
    if sump < THRESHOLDS['sump_low']:
        wa = (f'*ALERT [{did}]* — Low Sump Level\n'
              f'Sump: {sump}% (threshold: {THRESHOLDS["sump_low"]}%)\n'
              f'Water transfer may be affected.\nTime: {ts}')
        dispatch_alert(did, 'sump_low', wa)
