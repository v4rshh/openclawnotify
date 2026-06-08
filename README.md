# Flostat WhatsApp Alert System

A professional, modularized alert service that polls water level reading sensors (mocked locally, integrated with AWS DynamoDB for production) and dispatches automated alert messages to a linked WhatsApp account using the OpenClaw gateway CLI.

---

## Folder Structure

```
whatsapp-alert-system/
│
├── src/
│   ├── main.py            # Service entry point and main polling loop
│   ├── alerts.py          # Threshold check conditions and alert routing logic
│   ├── dynamodb.py        # Data source operations (Mocked, scales to DynamoDB)
│   ├── openclaw_client.py # OpenClaw CLI invocation wrapper (via subprocess)
│   └── cooldown.py        # Alert frequency tracking and duplicate cooldown logic
│
├── tests/                 # Unit and integration test suites
│
├── .env                   # Local configuration file (contains phone targets & parameters)
├── requirements.txt       # Python library dependencies
└── README.md              # Setup and operations guide
```

---

## How it Works

### 1. Linking API (Authentication)
* **API Details**: This system does not use the official Meta Business API (which requires registered developers, billing, and template approvals). 
* **Protocol**: Instead, it integrates with **OpenClaw**, which uses the **Baileys WebSocket-based client library**. 
* **Mechanism**: When onboarding, you run a command that outputs a QR code simulating a WhatsApp Web session. Scanning this code pairs OpenClaw as a "Linked Device" on your personal phone. Session state credentials are cached locally under `~/.openclaw`.

### 2. Notification Trigger Workflow
1. **Fetch**: The polling loop in `src/main.py` wakes up periodically (configured by `poll_interval_seconds`) and calls `fetch_device_data()` in `src/dynamodb.py`.
2. **Evaluate**: It checks each device against thresholds defined in `src/alerts.py` (e.g. Tank Low < 25%, Tank High > 75%, Sump Low < 10%).
3. **De-duplicate**: If a threshold is crossed, it calls `can_send_alert()` in `src/cooldown.py` to check if the specific alert was already sent within the `COOLDOWN_HOURS` window (default 4 hours).
4. **Trigger**: If allowed, it runs a subprocess command:
   ```bash
   npx openclaw message send --channel whatsapp --target <phone_number> --message "<alert_text>"
   ```
5. **Deliver**: The local OpenClaw gateway routes the command payload over the established WebSocket connection to the WhatsApp servers, delivering a native message to the recipient.

---

## Setup & Execution

### Prerequisites
1. **Python 3.x**
2. **Node.js & npm** (included with Node.js)

### Installation
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure `.env` in the root folder:
   ```env
   # The recipient phone number (include country code, e.g. 91XXXXXXXXXX, no + or spaces)
   RECIPIENT_PHONE=91XXXXXXXXXX
   
   # Duplicate suppression period (hours)
   COOLDOWN_HOURS=4
   ```

3. Onboard your WhatsApp account into OpenClaw:
   ```bash
   npx openclaw channels add --channel whatsapp
   ```
   Scan the printed QR code with your WhatsApp app (**Settings -> Linked Devices -> Link a Device**).

4. Run the alert script:
   ```bash
   python src/main.py
   ```
