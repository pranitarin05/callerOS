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

# Browser WebRTC voice
ELEVENLABS_WEB_AGENT_ID=        # optional; defaults to ELEVENLABS_AGENT_ID
ELEVENLABS_TOOL_SECRET=         # random string; used by X-ElevenLabs-Tool-Secret
VOICE_SESSION_MAX_MINUTES=15

# RAG (local embeddings, no API key)
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDINGS_CACHE_DIR=./.cache/embeddings
RAG_CHUNK_SIZE=700
RAG_CHUNK_OVERLAP=120
RAG_TOP_K=5

# Appointment scheduler
BUSINESS_TIMEZONE=Asia/Kolkata
BUSINESS_HOURS_START=9
BUSINESS_HOURS_END=18
APPOINTMENT_SLOT_MINUTES=30
APPOINTMENT_WEEKDAYS=0,1,2,3,4

# Memory / languages
DEFAULT_LANGUAGE=auto
MEMORY_MAX_CHARS=4000
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

## 7b. Browser voice, agent tools, RAG and appointments

### Browser voice (WebRTC)
1. Make sure the ElevenLabs agent is enabled for the browser/WebRTC channel with language detection (Hindi / English / Hinglish) turned on. Language mirroring during the call is handled by the ElevenLabs agent; the backend detects and stores the language from the transcript afterwards.
2. `GET /api/v1/voice/config` must show `voice_ready: true`.
3. Open a lead and click **Talk to agent**. The backend requests a conversation token from ElevenLabs; the API key never reaches the browser. Live transcript lines are posted to `/api/v1/voice/transcript`, and `/api/v1/voice/complete` runs the same qualification/summary/memory pipeline as the webhook.

### Agent server tools
1. Set `ELEVENLABS_TOOL_SECRET` to a random string.
2. In the ElevenLabs agent, register server tools pointing at:
   `POST https://<your-public-host>/api/webhooks/elevenlabs/tools`
   with header `X-ElevenLabs-Tool-Secret: <ELEVENLABS_TOOL_SECRET>`.
3. Available tools: `get_lead_details`, `update_lead`, `search_knowledge`, `schedule_followup`, `book_appointment`, `get_available_slots`, `end_call`.
4. If the agent does not book during the call, post-call processing creates a follow-up to schedule the appointment (fallback).

### RAG
1. First run downloads the multilingual embedding model into `EMBEDDINGS_CACHE_DIR` (~470 MB).
2. Upload txt/md/pdf from the **Knowledge** page, or `POST /api/v1/knowledge/documents/upload`.
3. The agent's `search_knowledge` tool returns the top `RAG_TOP_K` chunks. Built-in FAQs are used when no documents are indexed.

### Appointments
1. Business hours/timezone come from `BUSINESS_TIMEZONE`, `BUSINESS_HOURS_START/END`, `APPOINTMENT_WEEKDAYS` and `APPOINTMENT_SLOT_MINUTES`.
2. View/book at **Appointments**. `tzdata` is included so timezone names work on Windows.

### Custom agent script
1. Open **Settings** to edit the first message and system prompt. These are saved per user and sent as `conversation_config_override` on outbound and browser calls.
2. Available placeholders: `{{prospect_name}}`, `{{language}}`, `{{lead_memory}}`, `{{call_id}}`, `{{lead_id}}`.
3. The override toggles for `first_message`, `language` and `prompt.prompt` are enabled on the ElevenLabs agent (`platform_settings.overrides.conversation_config_override`). If you recreate the agent, re-enable them.
4. Language: the agent's default language is Hindi with Hinglish mode enabled, and the `language_detection` system tool plus an English preset are configured. If a caller speaks Hindi, the agent responds in Hindi/Hinglish; if they speak English, the detection tool can switch to English. Setting `auto` in Settings keeps this behavior. Forcing `en` or `hi` overrides only the starting language.

## 8. Database migrations

- `d0fd1ed2b278_replace_vapi_with_elevenlabs_exotel.py` replaces Vapi with ElevenLabs + Exotel fields.
- `f1a2b3c4d5e6_add_rag_appointments_memory_voice.py` adds `knowledge_chunks`, `appointments`, `lead_memories`, plus `preferred_language`/`last_contact_at` on leads, `language`/`channel` on calls, and RAG status fields on knowledge documents.
- `f2b3c4d5e6f7_add_agent_script_overrides.py` adds `first_message` and `language` to `agent_configs`.
- Run `py -3.11 -m alembic upgrade head` before starting the app. SQLite uses batch ALTER; data is preserved.

## 8b. Why a call to another number fails with `exotel_connect_failed` / HTTP 403

If calls to your own number succeed but a friend's number fails with:

```
424: {'type': 'failed_dependency', 'code': 'upstream_service_error',
      'message': 'Exotel Connect API returned HTTP 403',
      'status': 'exotel_connect_failed'}
```

the credentials, region and agent are fine — Exotel is **denying that destination**. In an Exotel trial account, outbound calls are only allowed to verified/whitelisted numbers. Your own number works because it is verified; a friend's number is not.

Fixes (any one):
1. **Whitelist the number** in Exotel dashboard → Settings → Whitelist Numbers → add `+91...` → OTP verification (trial allows up to 10 numbers).
2. **Complete Exotel KYC / upgrade from trial** to call any number.
3. Confirm the account has balance and the number is not DND-blocked (check with Exotel Number Metadata API).

Also confirm `EXOTEL_REGION` in `.env` matches the dashboard cluster. This account is on **`api.exotel.com`**; the old value `api.in.exotel.com` returned 401 on direct API checks. ElevenLabs stores its own region for the imported number, so the 403 is not caused by this env value, but it should still be correct.

## 9. Remaining manual configuration

- Activate `ELEVENLABS_AGENT_ID` if still empty.
- Add `ELEVENLABS_WEBHOOK_SECRET` from the ElevenLabs webhook screen.
- Add `ELEVENLABS_WEBHOOK_URL` (public URL, not localhost).
- Confirm Exotel region matches your account cluster.
- Confirm the prospect has consented before calling.
