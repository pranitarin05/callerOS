# AI CallerOS - Deployment & Calling Guide

## 1. Overview

Outbound calls are placed exclusively through the official ElevenLabs endpoint:

```
POST https://api.elevenlabs.io/v1/convai/exotel/outbound-call
xi-api-key: <ELEVENLABS_API_KEY>
```

Request fields used by the backend:

```json
{
  "agent_id": "<ELEVENLABS_AGENT_ID>",
  "agent_phone_number_id": "<ELEVENLABS_PHONE_NUMBER_ID>",
  "to_number": "+919876543210",
  "conversation_initiation_client_data": {
    "user_id": "<authenticated user id>",
    "source_info": { "source": "exotel" },
    "dynamic_variables": {
      "call_id": "<local call id>",
      "lead_id": "<local lead id>",
      "crm_user_id": "<authenticated user id>",
      "prospect_name": "<lead name>"
    }
  }
}
```

Exotel credentials are stored inside the imported phone number in ElevenLabs. The backend does not call Exotel directly and does not send Exotel credentials to the browser.

## 2. Environment variables

Keep these in `D:/voice automate/.env` (backend only):

```env
# Calling mode: demo or live
CALL_MODE=demo

# ElevenLabs
ELEVENLABS_API_KEY=
ELEVENLABS_AGENT_ID=
ELEVENLABS_PHONE_NUMBER_ID=
ELEVENLABS_AGENT_NAME=Student Project Demo Qualifier
ELEVENLABS_WEBHOOK_URL=
ELEVENLABS_WEBHOOK_SECRET=
ELEVENLABS_API_BASE_URL=https://api.elevenlabs.io

# Exotel credentials used when importing the number into ElevenLabs
EXOTEL_ACCOUNT_SID=
EXOTEL_API_KEY=
EXOTEL_API_TOKEN=
EXOTEL_PHONE_NUMBER=
EXOTEL_REGION=api.in.exotel.com

# Groq analysis with backup keys
GROQ_API_KEY=
GROQ_API_KEY_BACKUP_1=
GROQ_API_KEY_BACKUP_2=
GROQ_MODEL=llama-3.3-70b-versatile

# App
SECRET_KEY=change-this-secret
```

`.env` is gitignored. Never commit real values.

## 3. ElevenLabs + Exotel setup

1. In Exotel, enable the Voicebot applet and collect Account SID, API Key, API Token and the E.164 phone number.
2. In ElevenLabs → Phone Numbers → Import number → From Exotel:
   - Phone number in E.164 format, e.g. `+918048961234`
   - Account SID, API Key, API Token
   - Region: Mumbai (`api.in.exotel.com`) or Singapore (`api.exotel.com`)
   - Voicebot Applet ID
3. Copy the imported number's ID into `ELEVENLABS_PHONE_NUMBER_ID`.
4. Use the published agent `Student Project Demo Qualifier`; copy its ID into `ELEVENLABS_AGENT_ID`.
5. Do not change the agent prompt unless required; it already handles Hindi, English and Hinglish and lead grading.

## 4. Webhook configuration

1. In ElevenAgents settings → Post-call webhooks, create a webhook with:
   - URL: `https://<your-public-host>/api/webhooks/elevenlabs`
   - Auth type: HMAC
   - Events: `transcript`, `call_initiation_failure`
2. Copy the generated shared secret into `ELEVENLABS_WEBHOOK_SECRET`.
3. For local testing, expose the backend with a tunnel:

```bash
ngrok http 8000
```

Then set:

```env
ELEVENLABS_WEBHOOK_URL=https://<tunnel-host>/api/webhooks/elevenlabs
ELEVENLABS_WEBHOOK_SECRET=<secret-from-elevenlabs>
```

The backend verifies the `ElevenLabs-Signature` header using the official Python SDK. Without `ELEVENLABS_WEBHOOK_SECRET`, webhook delivery is rejected.

Supported webhook types handled:

- `post_call_transcription`: transcript, summary, metadata, analysis, qualification
- `call_initiation_failure`: busy, no-answer, failure reasons
- `post_call_audio`: acknowledged but not processed (no transcript data)

## 5. Run locally

Backend:

```bash
cd D:/voice automate
py -3.11 -m pip install -r requirements.txt
py -3.11 -m alembic upgrade head
py -3.11 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd D:/voice automate/frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## 6. Make a real outbound call

1. Log in or create an account.
2. Go to **Leads**, add a lead with an Indian mobile number (for example `9876543210`, normalized to `+919876543210`).
3. Select **Live call** on the Leads page, or use the home call console and choose **Live ElevenLabs + Exotel**.
4. Click **Call now** / **Live call**.
5. The backend returns `status: initiated` once ElevenLabs accepts the request. This does **not** mean the call was answered.
6. After the call ends, ElevenLabs sends `post_call_transcription` to the webhook. The CRM updates automatically with transcript, summary, sentiment, outcome and next action.
7. View results under **Calls** and **Dashboard**.

To check a call manually:

```bash
curl http://127.0.0.1:8000/api/v1/calls/<call_id>/insights
```

If the webhook was missed, force a provider sync:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/calls/<call_id>/sync
```

## 7. Testing

Automated tests use mocks and never place a real call:

```bash
py -3.11 -m unittest discover -s tests -v
npm run lint
npm run build
```

Manual live-call checklist:

- [ ] `GET /api/calls/config` shows `live_ready: true`
- [ ] Webhook URL is publicly reachable
- [ ] Webhook secret is configured
- [ ] Imported Exotel number is outbound-capable
- [ ] Lead has consent to be called

## 8. Database migrations

The migration `d0fd1ed2b278_replace_vapi_with_elevenlabs_exotel.py`:

- drops the obsolete `vapi_call_id` column and index
- adds `provider`, `conversation_id`, `exotel_call_sid`, `initiation_status`, `call_outcome`, `qualification_json`, `followup_required` and `error_message`
- preserves existing lead/call data

## 9. Remaining manual configuration

- Activate `ELEVENLABS_AGENT_ID` if still empty.
- Add `ELEVENLABS_WEBHOOK_SECRET` from the ElevenLabs webhook screen.
- Add `ELEVENLABS_WEBHOOK_URL` (public URL, not localhost).
- Confirm Exotel region matches your account cluster.
- Confirm the prospect has consented before calling.
