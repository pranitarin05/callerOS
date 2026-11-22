# AI CallerOS

AI CallerOS is an AI-powered Voice Agent + CRM SaaS application that helps businesses manage leads, automate outbound calling, qualify prospects, summarize conversations, and schedule follow-ups.

## 🚀 Live Demo

The application is deployed and ready for use. Visit the repository for full access.

## 📋 Project Overview

AI CallerOS automates the entire lead qualification workflow:
1. Create a lead
2. Initiate an AI-powered call
3. Have a natural conversation
4. Extract lead requirements and interest
5. Update the CRM using backend tools
6. Store transcript, summary and call outcome
7. Schedule a follow-up

## 🏗️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16, TypeScript, Tailwind CSS, shadcn/ui, Recharts |
| **Backend** | Python FastAPI, SQLAlchemy, Pydantic, Alembic |
| **Database** | Supabase PostgreSQL (9 tables via Alembic migrations) |
| **Authentication** | Supabase Auth (Google OAuth + email magic link) |
| **AI** | Groq API for LLM, structured outputs for qualification |
| **Voice** | Vapi integration for real and demo modes |

## 📦 Milestones Implemented (9/9)

| Milestone | Focus | Status |
|-----------|-------|--------|
| 1 | Project setup, configuration, database and authentication | ✅ Complete |
| 2 | Lead management APIs and CRM frontend | ✅ Complete |
| 3 | Dashboard and lead details | ✅ Complete |
| 4 | AI conversation simulator and qualification | ✅ Complete |
| 5 | Backend tools and CRM updates | ✅ Complete |
| 6 | Vapi outbound calling and webhook integration | ✅ Complete |
| 7 | Call transcripts, summaries, sentiment and outcomes | ✅ Complete |
| 8 | Follow-up scheduling | ✅ Complete |
| 9 | Tests, Docker and deployment documentation | ✅ Complete |

## 🛠️ Features

### P0 - Required Features
- ✅ User registration and login (Supabase Auth - Google OAuth + email magic link)
- ✅ CRM dashboard with business metrics and Recharts charts
- ✅ Create, view, edit and search leads
- ✅ Lead status management
- ✅ AI conversation simulator (demo mode, no telephony credentials needed)
- ✅ AI lead qualification (structured outputs matching the spec)
- ✅ Backend tool execution (5 validated functions with ownership enforcement)
- ✅ Vapi outbound call integration (live mode + demo mode)
- ✅ Vapi webhook handling with HMAC-SHA256 signature verification
- ✅ Call history and persistence in PostgreSQL
- ✅ Transcript and summary storage
- ✅ Sentiment and call outcome extraction
- ✅ Follow-up creation and management

### P1 - After Core Workflow Works
- ✅ Knowledge base and document upload (keyword-based search)
- ✅ Advanced call analytics (dashboard metrics from database)
- ✅ Configurable agent instructions (agent_configs table)
- ✅ Human handoff concepts (through backend tools)

### P2 - Future Enhancements
- Multi-tenant organizations
- Role-based permissions
- Multiple voice agents
- Campaign management
- Advanced reporting
- Automated scheduled calling

## 🔑 API Endpoints

### Leads API
- `GET/POST /api/v1/leads` - Create and list leads
- `GET/PATCH /api/v1/leads/{id}` - View and update single lead

### Analytics
- `GET /api/v1/analytics/dashboard` - Dashboard metrics from database

### Conversations
- `POST /api/v1/conversations/simulate` - AI conversation simulator
- `POST /api/v1/conversations/qualify` - AI lead qualification
- `POST /api/v1/conversations/knowledge-search` - Knowledge base search
- `POST /api/v1/conversations/followup` - Schedule follow-up
- `POST /api/v1/conversations/end-call` - Complete call and update CRM

### Vapi
- `POST /api/v1/vapi/outbound-call` - Initiate Vapi outbound call
- `POST /api/v1/vapi/webhook` - Vapi call event webhook
- `POST /api/v1/vapi/authenticate` - Vapi assistant authentication

## 🔧 Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- Supabase account
- Vapi account (for live mode)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cd app
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The application will be available at:
- Frontend: `http://localhost:3000`
- Backend: `http://127.0.0.1:8000`

### Environment Variables (.env)
Create a `.env` file with:
```env
# Groq AI API
GROQ_API_KEY=your_groq_key

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Vapi Configuration (for live mode)
VAPI_ASSISTANT_ID=your_assistant_id
VAPI_PUBLIC_KEY=your_public_key
VAPI_SECRET_KEY=your_secret_key  # Keep this secret!

# Application Settings
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Backend Configuration
API_V1_STR=/api/v1
PROJECT_NAME=AI CallerOS
```

### Docker Deployment
```bash
docker-compose up --build
# Or build individually:
docker build -t calleros/backend ./backend
docker build -t calleros/frontend ./frontend
docker-compose up
```

## 🔒 Security

- LLM never directly executes SQL or bypasses backend authorization
- Webhook processing is idempotent
- Record ownership enforced on all operations
- Input validation on all endpoints and tools
- Environment-based configuration (no hardcoded secrets)
- Demo mode works without Vapi credentials; live mode when keys provided
- Never presents a simulated call as a real phone call

## 📁 Repository Structure

```
AI CallerOS/
├── .env                    # Placeholder keys only (excluded from git)
├── .env.txt                # Placeholder only (excluded from git)
├── DEPLOYMENT_GUIDE.md     # Deployment instructions
├── Dockerfile              # Backend Dockerfile
├── docker-compose.yml      # Full stack deployment
├── alembic.ini            # Database migration config
├── requirements.txt        # Python dependencies (34 pkgs)
├── plan.txt               # Full requirements document
├── app/                    # Backend (FastAPI + SQLAlchemy)
│   ├── main.py            # FastAPI application
│   ├── core/              # Configuration and settings
│   ├── models/            # 9 SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── tools/             # 5+ validated backend tools
│   ├── services/          # Business logic layer
│   └── api/v1/            # API route handlers
├── frontend/               # Next.js 16 frontend
│   ├── app/               # App Router + pages
│   ├── components/        # shadcn/ui components
│   ├── package.json       # npm dependencies
│   └── tailwind.config.js # CSS configuration
├── migrations/             # Alembic migration scripts (9 tables)
├── .gitignore             # Excludes .env* files
└── README.md              # This file
```

## 🚀 Deployment

### Vercel (Frontend)
```bash
vercel --prod
```

### Render + Supabase (Backend + Database)
```bash
# Set environment variables in Render dashboard
# Deploy Docker container or use Supabase directly
```

### Full Stack (Docker Compose)
```bash
docker-compose up --build
```

### Supabase Setup
1. Create project at [supabase.com](https://supabase.com)
2. Run migrations: `alembic upgrade head`
3. Enable Google OAuth authentication
4. Configure redirect URL: `http://localhost:8000/auth/callback`

## 📞 Contact & Support

For issues or questions:
- Check the [Supabase documentation](https://supabase.com/docs)
- Check the [Vapi documentation](https://vapi.ai/docs)
- Check the [FastAPI documentation](https://fastapi.tiangolo.com)
- Check the [Next.js documentation](https://nextjs.org/docs)

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**AI CallerOS** - AI Voice Agent + CRM SaaS Application

Built with ❤️ using FastAPI, Next.js, Supabase, and Groq API