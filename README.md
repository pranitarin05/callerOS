# Caller OS

Caller OS is an AI voice agent and CRM SaaS application. It manages leads, places outbound calls through ElevenLabs Conversational AI with Exotel telephony, runs browser voice sessions, captures transcripts/summaries/sentiment, answers from a private knowledge base, books appointments, and updates business insights.

> Inbound phone calls are not implemented. Calling is **outbound phone** plus **browser WebRTC voice**. Demo mode is a deterministic text simulation and is never presented as a real call.

## 📋 Current workflow

1. Create or select a lead.
2. Start a demo call, a real ElevenLabs + Exotel outbound call, or a browser voice session.
3. The ElevenLabs agent speaks with the prospect in Hindi, English or Hinglish.
4. The agent can call validated backend tools for lead details, CRM updates, knowledge search, follow-ups and appointments.
5. ElevenLabs sends a post-call webhook with transcript and analysis. Browser sessions finish through `/api/v1/voice/complete`.
6. Groq plus heuristic analysis derives qualification, sentiment, outcome and next action.
7. CRM records, transcripts, summaries, memory, appointments and follow-ups are persisted.
8. Calls page and dashboard show sentiment and business insights.

## 🛠️ Features

- Email/password sign-up and login with signed tokens
- Lead create, edit, search, delete and status management
- Dashboard from real database data
- Demo calling mode without telephony credentials
- Real outbound calling via the official ElevenLabs Exotel endpoint
- Browser WebRTC voice with live transcript
- Post-call transcript, summary, sentiment, qualification and outcome storage
- Sentiment visible on each call in the Calls page
- RAG knowledge base: txt/md/pdf upload, chunking, local multilingual embeddings, semantic search
- Rolling per-lead conversation memory with Hindi/English/Hinglish detection
- Internal appointment scheduling with business hours and conflict checks
- Post-call auto-follow-up fallback when an appointment is requested but not booked live
- Per-user agent script editor for first message and system prompt, sent as ElevenLabs per-call overrides
- Protected ElevenLabs server tools endpoint
- Groq key rotation with heuristic fallback
- Ownership checks, webhook signature verification, idempotency and server-only credentials

## 🏗️ Technology stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, shadcn/ui, Recharts |
| Backend | Python FastAPI, SQLAlchemy, Pydantic, Alembic |
| Database | SQLite locally; PostgreSQL/Supabase portable via SQLAlchemy |
| Auth | Server-side PBKDF2 password hashing + signed tokens |
| Voice | ElevenLabs Conversational AI, WebRTC browser sessions |
| Telephony | Exotel via the official ElevenLabs Exotel outbound-call API |
| AI analysis | Groq with key rotation; heuristic fallback |
| RAG | sentence-transformers multilingual embeddings; cosine search in Python |
| Scheduler | Internal appointment system with `tzdata` timezone support |

## 🔑 API endpoints

### Auth
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Leads
- `POST /api/v1/leads`
- `GET /api/v1/leads`
- `GET /api/v1/leads/{id}`
- `PATCH /api/v1/leads/{id}`
- `DELETE /api/v1/leads/{id}`
- `GET /api/v1/leads/{id}/memory`

### Calling
- `POST /api/calls/initiate`
- `POST /api/v1/calls/initiate`
- `POST /api/v1/calls/outbound`
- `GET /api/calls/config`
- `GET /api/v1/calls/config`
- `GET /api/v1/calls`
- `GET /api/v1/calls/{id}`
- `GET /api/v1/calls/{id}/insights`
- `POST /api/v1/calls/{id}/sync`

### Browser voice
- `GET /api/v1/voice/config`
- `POST /api/v1/voice/session`
- `POST /api/v1/voice/transcript`
- `POST /api/v1/voice/complete`

### Webhooks
- `POST /api/webhooks/elevenlabs`
- `POST /api/v1/webhooks/elevenlabs`
- `POST /api/webhooks/elevenlabs/tools` (protected agent server tools)

### Knowledge / RAG
- `POST /api/v1/knowledge/documents`
- `POST /api/v1/knowledge/documents/upload`
- `GET /api/v1/knowledge/documents`
- `DELETE /api/v1/knowledge/documents/{id}`
- `POST /api/v1/knowledge/search`

### Agent script
- `GET /api/v1/agent-config`
- `PUT /api/v1/agent-config`
- `DELETE /api/v1/agent-config`

### Appointments, follow-ups and insights
- `GET /api/v1/appointments/slots`
- `POST /api/v1/appointments`
- `GET /api/v1/appointments`
- `PATCH /api/v1/appointments/{id}`
- `POST /api/v1/followups`
- `GET /api/v1/followups`
- `GET /api/v1/analytics`
- `GET /api/v1/analytics/insights`

### Conversation helpers
- `POST /api/v1/conversations/simulate`
- `POST /api/v1/conversations/qualify`
- `POST /api/v1/conversations/knowledge-search`
- `POST /api/v1/conversations/followup`
- `POST /api/v1/conversations/end-call`
- `POST /api/v1/conversations/available-slots`
- `POST /api/v1/conversations/book-appointment`

## ⚙️ Environment variables

Secrets stay in `.env` (gitignored). Never commit real values. Placeholders below are examples.

```env
# App
PROJECT_NAME=Caller OS
API_V1_STR=/api/v1
CALL_MODE=live
SECRET_KEY=<random-secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=
LOCAL_DATABASE_URL=sqlite:///./calleros.db

# Supabase (optional)
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Groq analysis
GROQ_API_KEY=<groq-key>
GROQ_API_KEY_BACKUP_1=
GROQ_API_KEY_BACKUP_2=
GROQ_MODEL=llama-3.3-70b-versatile

# ElevenLabs
ELEVENLABS_API_KEY=<elevenlabs-key>
ELEVENLABS_AGENT_ID=<agent-id>
ELEVENLABS_PHONE_NUMBER_ID=<phone-number-id>
ELEVENLABS_WEB_AGENT_ID=          # optional; falls back to ELEVENLABS_AGENT_ID
ELEVENLABS_AGENT_NAME=Student Project Demo Qualifier
ELEVENLABS_API_BASE_URL=https://api.elevenlabs.io
ELEVENLABS_WEBHOOK_URL=https://<public-host>/api/webhooks/elevenlabs
ELEVENLABS_WEBHOOK_SECRET=<hmac-secret>
ELEVENLABS_TOOL_SECRET=<random-secret>
VOICE_SESSION_MAX_MINUTES=15

# Exotel
EXOTEL_ACCOUNT_SID=<account-sid>
EXOTEL_API_KEY=<api-key>
EXOTEL_API_TOKEN=<api-token>
EXOTEL_PHONE_NUMBER=<caller-id-number>
EXOTEL_REGION=api.exotel.com       # or api.in.exotel.com for Mumbai accounts

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

# Memory / language
DEFAULT_LANGUAGE=auto
MEMORY_MAX_CHARS=4000
```

The first RAG run downloads the multilingual embedding model into `EMBEDDINGS_CACHE_DIR` (~470 MB).

## 🔧 Running manually

Use `py -3.11`; plain `python` is Python 2.7 on this machine.

**1. Public webhook tunnel** (required for real phone calls):

```powershell
ngrok http 8000
```

Keep it running. If the ngrok URL changes, update `ELEVENLABS_WEBHOOK_URL` in `.env` and the ElevenLabs webhook.

**2. Backend:**

```powershell
cd D:\voice automate
py -3.11 -m pip install -r requirements.txt
py -3.11 -m alembic upgrade head
py -3.11 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**3. Frontend:**

```powershell
cd D:\voice automate\frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

Verify:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/calls/config | Select-Object live_ready,webhook_configured,exotel_region
```

After changing `.env`, restart the backend; uvicorn reload does not reload `.env`.

## 📞 Exotel trial note

On an Exotel trial account, outbound calls are only allowed to verified/whitelisted numbers. A non-whitelisted destination returns HTTP 403, surfaced as `424 ... exotel_connect_failed`. Whitelist the destination in Exotel → Settings → Whitelist Numbers, or complete KYC/upgrade to call any number. The current account uses the Singapore cluster `api.exotel.com`.

## ✅ Tests

```powershell
$env:PYTHONPATH = (Get-Location).Path
py -3.11 -m unittest discover -s tests -v

cd frontend
npm run lint
npx tsc --noEmit
```

## 🔒 Security

- Provider keys remain in backend environment variables only.
- No private keys are exposed through `NEXT_PUBLIC_*` variables.
- ElevenLabs webhooks are verified with `ELEVENLABS_WEBHOOK_SECRET` using the official SDK.
- Agent server tools are protected by `X-ElevenLabs-Tool-Secret`.
- Webhook processing is idempotent.
- Duplicate-call prevention, ownership checks, timeouts and safe error messages are implemented.
- Groq is used only for analysis, never for telephony.

## 📁 Repository structure

```text
app/
  api/v1/          auth, leads, calls, conversations, followups, knowledge,
                   agent_config, appointments, voice, analytics, webhooks
  core/            config, security, AI analysis, language detection
  services/        lead, calling, RAG, memory, appointment, agent-config services
  tools/           validated backend tools and conversation simulator
  models/          SQLAlchemy models
  schemas/         Pydantic schemas
frontend/          Next.js app
migrations/        Alembic migrations
tests/             mocked unit tests
DEPLOYMENT_GUIDE.md  provider setup, webhook setup, troubleshooting
```

## 📚 Documentation

See `DEPLOYMENT_GUIDE.md` for detailed ElevenLabs, Exotel, webhook, RAG and override setup.

---

**Caller OS** — AI Voice Agent + CRM SaaS, powered by ElevenLabs, Exotel, Groq and local multilingual embeddings.
