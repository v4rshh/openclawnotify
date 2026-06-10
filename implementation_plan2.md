# Modular Restructuring & OpenClaw Explanation Plan

We will restructure the single-file WhatsApp alert system into a clean, professional, modular layout matching the diagram you provided, and document the architectural details (linking API and notification trigger workflow).

## Architectural Explanations

### 1. The Linking API
- **How it works**: OpenClaw doesn't use the official Meta WhatsApp Business API (which requires developers.facebook.com access tokens, templates, and credit cards). Instead, it links to a personal WhatsApp account.
- **API implementation**: It uses the **Baileys** library (a WebSocket-based TypeScript library for the WhatsApp Web protocol). When you run `npx openclaw channels add --channel whatsapp`, the CLI runs a WebSocket connection that generates a QR code. When you scan it, your phone issues a session credential stored in OpenClaw's local profile state folder.

### 2. The Notification Trigger
- **Workflow**:
  1. The Python loop (`src/main.py`) polls data from DynamoDB (or mock data).
  2. If a device level crosses a threshold (`src/alerts.py`) and passes cooldown checks (`src/cooldown.py`), it triggers an alert.
  3. The alert calls the OpenClaw client wrapper (`src/openclaw_client.py`).
  4. The client executes `npx openclaw message send --channel whatsapp --target <phone> --message "<text>"` via Python's `subprocess` module.
  5. The OpenClaw CLI routes the payload to the running gateway session (which is connected to the WhatsApp servers via WebSockets), and delivers the message to the recipient's phone.

---

## Proposed Changes

We will create the modular folder structure under `c:\Users\varsh\Downloads\Flostat\flostat`:

### New Modular Directory Structure

```
c:\Users\varsh\Downloads\Flostat\flostat/
├── src/
│   ├── main.py            [NEW] - Main service entry point and loop.
│   ├── alerts.py          [NEW] - Threshold validation and dispatch logic.
│   ├── dynamodb.py        [NEW] - DynamoDB fetch (mocked for now).
│   ├── openclaw_client.py [NEW] - Subprocess CLI execution logic.
│   └── cooldown.py        [NEW] - Cooldown window enforcement.
├── tests/                 [NEW] - Directory for future tests.
├── .env                   [MODIFY] - Environment settings.
├── requirements.txt       [NEW] - Required pip libraries.
├── README.md              [NEW] - Documentation of setup, linking, and triggers.
└── notification_service.py [DELETE] - Removing the single-file script.
```

---

### [Component Name]

#### [main.py]
- Performs configuration loading and handles the polling loop that calls `fetch_device_data()` and `check_device()`.

#### [alerts.py]
- Contains threshold boundary definitions and the core `check_device` and `dispatch_alert` logic.

#### [dynamodb.py]
- Handles data collection interface (currently returning `MOCK_DEVICES`).

#### [openclaw_client.py]
- Wraps the `npx openclaw` command invocation.

#### [cooldown.py]
- Manages the deduplication and cooldown logic.

#### [requirements.txt]
- Specifies python-dotenv and boto3.

#### [README.md]
- Complete instruction manual for onboarding OpenClaw, connecting WhatsApp, configuring `.env`, and running the modular application.


---

## Verification Plan

### Automated / CLI Verification
1. Run python on individual modular files to confirm no syntax or import errors.
2. Run `python src/main.py` to confirm the service starts, polls successfully, triggers alerts, and logs command routing.
3. Check that the project structure is exactly as displayed in the image.
