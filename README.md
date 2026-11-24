# AI CallerOS

AI CallerOS is an AI-powered Voice Agent + CRM SaaS application that manages leads, places real outbound calls through ElevenLabs Conversational AI with Exotel telephony, captures transcripts/summaries/sentiment, and schedules follow-ups.



## 📋 Project overview

1. Create or select a lead.
2. Start a demo call or a real ElevenLabs + Exotel outbound call.
3. The published ElevenLabs agent speaks with the prospect in Hindi, English or Hinglish.
4. ElevenLabs sends a post-call webhook with transcript and analysis.
5. Groq plus heuristic analysis derives qualification, sentiment, outcome and next action.
6. CRM records, transcripts, summaries and follow-ups are persisted.

## 🏗️ Technology stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, shadcn/ui, Recharts |
| Backend | Python FastAPI, SQLAlchemy, Pydantic, Alembic |
| Database | SQLite locally / Supabase PostgreSQL portable via SQLAlchemy |
| Auth | Server-side PBKDF2 password hashing + signed tokens |
| Voice | ElevenLabs Conversational AI |
| Telephony | Exotel via the official ElevenLabs Exotel outbound-call API |
| AI analysis | Groq with key rotation; heuristic fallback |

## ✅ Milestones

| Milestone | Focus | Status |
|-----------|-------|--------|
| 1 | Project setup, configuration, database and authentication | ✅ |
| 2 | Lead management APIs and CRM frontend | ✅ |
| 3 | Dashboard and lead details | ✅ |
| 4 | AI conversation simulator and qualification | ✅ |
| 5 | Backend tools and CRM updates | ✅ |
| 6 | ElevenLabs + Exotel outbound calling and webhook integration | ✅ |
| 7 | Call transcripts, summaries, sentiment and outcomes | ✅ |
| 8 | Follow-up scheduling | ✅ |
| 9 | Tests, Docker and deployment documentation | ✅ |

## 🛠️ Features

- User sign-up and login with email/password
- Lead create, edit, search, delete and status management
- Dashboard metrics from the database
- Demo calling mode with no telephony credentials
- Real outbound calling via ElevenLabs Exotel endpoint
- Manual call target entry or existing lead selection
- Call history with provider IDs
- Webhook-driven transcript, summary, sentiment and qualification
- Follow-up scheduling
- Groq key rotation with safe fallback
- Ownership checks and server-only credentials

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

### Calling
- `POST /api/calls/initiate`
- `POST /api/v1/calls/initiate`
- `POST /api/v1/calls/outbound` (compatibility alias)
- `GET /api/calls/config`
- `GET /api/v1/calls/config`
- `GET /api/v1/calls`
- `GET /api/v1/calls/{id}`
- `GET /api/v1/calls/{id}/insights`
- `POST /api/v1/calls/{id}/sync`

### Webhooks
- `POST /api/webhooks/elevenlabs`
- `POST /api/v1/webhooks/elevenlabs`

## 🔧 Running locally

### Backend

```bash
py -3.11 -m pip install -r requirements.txt
py -3.11 -m alembic upgrade head
py -3.11 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 🔒 Security

- Credentials are read from backend environment variables only.
- No provider keys are exposed through `NEXT_PUBLIC_*` variables.
- ElevenLabs webhooks are verified with `ELEVENLABS_WEBHOOK_SECRET` using the official SDK.
- Webhook processing is idempotent.
- Duplicate call prevention, consent/opt-out checks, timeouts and safe error messages are implemented.
- Groq is used only for analysis, never for telephony.

## 📁 Repository structure

```
app/
  api/v1/auth, leads, calls, conversations, followups, analytics, webhooks
  core/        config, security, Groq client
  services/    lead_service, calling_service
  tools/       backend tools, transcript helpers
  models/      SQLAlchemy models
  schemas/     Pydantic schemas
frontend/      Next.js app
frontend design/  Obsidian Executive design reference
migrations/    Alembic migrations
tests/         mocked tests
```

## 📚 Documentation

See `DEPLOYMENT_GUIDE.md` for webhook setup, real-call steps and manual configuration.

---

**AI CallerOS** — AI Voice Agent + CRM SaaS, powered by ElevenLabs, Exotel and Groq.
