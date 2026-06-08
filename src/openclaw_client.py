import os
import subprocess
import logging

log = logging.getLogger(__name__)

def send_whatsapp(message: str) -> bool:
    """Send a text message via the OpenClaw CLI."""
    recipient_phone = os.getenv('RECIPIENT_PHONE')
    if not recipient_phone:
        log.error("RECIPIENT_PHONE not configured in environment")
        return False
    try:
        # Run the openclaw CLI send command via npx
        cmd = [
            "npx", "openclaw", "message", "send",
            "--channel", "whatsapp",
            "--target", recipient_phone,
            "--message", message
        ]
        log.info(f"Executing OpenClaw: {' '.join(cmd)}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        log.info(f"OpenClaw success: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"OpenClaw execution failed (exit code {e.returncode}):")
        log.error(f"Stdout: {e.stdout.strip()}")
        log.error(f"Stderr: {e.stderr.strip()}")
        return False
    except Exception as e:
        log.error(f"Failed to execute OpenClaw: {e}")
        return False
