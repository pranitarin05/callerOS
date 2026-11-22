# AI CallerOS - Deployment Guide

## Overview
AI CallerOS is a full-stack AI Voice Agent + CRM SaaS application built with:
- **Frontend**: Next.js 16, TypeScript, Tailwind CSS, shadcn/ui, Recharts
- **Backend**: Python FastAPI, SQLAlchemy, Pydantic, Alembic
- **Database**: Supabase PostgreSQL
- **Authentication**: Supabase Auth (Google OAuth + email magic link)
- **AI**: Groq API for LLM, structured outputs for qualification
- **Voice**: Vapi integration for outbound calling

## Prerequisites

### 1. Environment Variables
Create a `.env` file in the root directory with the following variables:

```env
# Groq AI API
GROQ_API_KEY=gsk_placeholder_groq_key_for_development_only

# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Vapi Configuration (for live mode)
VAPI_ASSISTANT_ID=your_vapi_assistant_id
VAPI_PUBLIC_KEY=your_vapi_public_key
VAPI_SECRET_KEY=your_vapi_secret_key  # Keep this secret!

# Application Settings
SECRET_KEY=calleros-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Backend Configuration
API_V1_STR=/api/v1
PROJECT_NAME=AI CallerOS
```

### 2. Database Setup - Supabase

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Get your project URL and anon/service role keys
3. Run the Alembic migrations to set up the 9 database tables:
   ```bash
   cd backend
   alembic upgrade head
   ```
2. Enable Supabase Auth:
   - Go to Supabase Dashboard > Authentication > Providers
   - Enable Google OAuth
   - Configure the redirect URL: `http://localhost:8000/auth/callback`

### 3. Vapi Configuration (for live mode)

1. Create a Vapi account at [vapi.ai](https://vapi.ai)
2. Create an assistant with your desired configuration
3. Get your:
   - Assistant ID
   - Public Key (can be exposed to frontend)
   - Secret Key (keep secret - backend only!)
4. Set the VAPI_SECRET_KEY in your .env file
5. The webhook URL will be: `https://your-domain.com/api/v1/vapi/webhook`

## Development Setup

### 1. Backend

```bash
cd D:/voice\ automate

# Install dependencies
pip install -r requirements.txt

# Run migrations
cd app
alembic upgrade head

# Start the server
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The backend will be available at `http://127.0.0.1:8000`

### 2. Frontend

```bash
cd D:/voice\ automate/frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 3. Full Stack (with Docker)

```bash
# Using Docker Compose
docker-compose up --build

# Or build and run individually:
docker build -t calleros/backend ./backend
docker build -t calleros/frontend ./frontend
docker-compose up
```

## API Endpoints

### Leads API
- `GET /api/v1/leads` - List leads with filtering and pagination
- `POST /api/v1/leads` - Create a new lead
- `GET /api/v1/leads/{id}` - Get a single lead by ID
- `PATCH /api/v1/leads/{id}` - Update a lead

### Analytics API
- `GET /api/v1/analytics/dashboard` - Get dashboard metrics

### Conversations API
- `POST /api/v1/conversations/simulate` - Run AI conversation simulator (demo mode)
- `POST /api/v1/conversations/qualify` - AI lead qualification
- `POST /api/v1/conversations/knowledge-search` - Search knowledge base
- `POST /api/v1/conversations/followup` - Schedule follow-up
- `POST /api/v1/conversations/end-call` - Complete call and update CRM

### Vapi API
- `POST /api/v1/vapi/outbound-call` - Initiate Vapi outbound call
- `POST /api/v1/vapi/webhook` - Vapi call event webhook
- `POST /api/v1/vapi/authenticate` - Vapi assistant authentication

## Docker Deployment

### Build and Run

```bash
# Using Docker Compose (recommended)
docker-compose up --build

# Or build and run individually
docker build -t calleros/backend ./backend
docker build -t calleros/frontend ./frontend
docker-compose up
```

### Environment Variables in Docker

Set environment variables when running containers:

```bash
docker run -d \
  -p 8000:8000 \
  -p 3000:3000 \
  -e GROQ_API_KEY=your_groq_key \
  -e SUPABASE_URL=your_supabase_url \
  -e SUPABASE_ANON_KEY=your_supabase_anon_key \
  -e SUPABASE_SERVICE_ROLE_KEY=your_service_role_key \
  -e VAPI_ASSISTANT_ID=your_assistant_id \
  -e VAPI_PUBLIC_KEY=your_public_key \
  -e VAPI_SECRET_KEY=your_secret_key \
  -e SECRET_KEY=calleros-super-secret-key-change-in-production \
  calleros/backend
```

## Production Checklist

### 1. Security
- [ ] Keep VAPI_SECRET_KEY secret - never expose in frontend
- [ ] Use Supabase production URLs and keys
- [ ] Set a strong SECRET_KEY
- [ ] Enable HTTPS for production deployment
- [ ] Configure CORS properly for your domain

### 2. Database
- [ ] Run Alembic migrations: `alembic upgrade head`
- [ ] Set up regular backups of Supabase PostgreSQL
- [ ] Configure connection pooling for high traffic

### 3. Vapi Configuration
- [ ] Set up Vapi assistant with proper call handling
- [ ] Configure webhook endpoints for call events
- [ ] Test call flow in demo mode before going live
- [ ] Set up call recording and storage if needed

### 4. Monitoring
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Log FastAPI requests and responses
- [ ] Monitor Supabase database performance
- [ ] Track Vapi call metrics and duration

### 5. Scaling
- [ ] Configure connection pooling for PostgreSQL
- [ ] Set up Redis caching for frequently accessed data
- [ ] Implement rate limiting for API endpoints
- [ ] Configure CDN for static frontend assets

## Development Workflow

### 1. Local Development
```bash
# Terminal 1 - Backend
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend  
cd frontend && npm run dev
```

### 2. Testing
```bash
# Run tests (when Python 3 available)
python -m pytest tests/

# Manual testing
# - Register/login via Supabase Auth
# - Create and manage leads
# - Run demo conversations
# - Test Vapi integration in demo mode
```

### 3. Deployment
```bash
# Push to GitHub
git add .
git commit -m "Milestone 9: Tests, Docker and deployment docs"
git push

# Deploy to Vercel (frontend)
vercel --prod

# Deploy to Render or Supabase (backend)
# Or use Docker Compose for full stack deployment
```

## File Structure

```
D:/voice automate/
├── Dockerfile              # Root-level Dockerfile
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── alembic.ini           # Database migration config
├── migrations/           # Alembic migration scripts
├── app/                  # Backend (FastAPI + SQLAlchemy)
│   ├── main.py           # FastAPI application
│   ├── core/             # Configuration and settings
│   ├── models/           # SQLAlchemy models (9 tables)
│   ├── schemas/          # Pydantic schemas
│   ├── tools/            # 9 validated backend tools
│   ├── services/         # Business logic layer
│   └── api/v1/           # API route handlers
├── frontend/             # Frontend (Next.js 16)
│   ├── app/              # Next.js App Router
│   ├── components/       # shadcn/ui components
│   ├── package.json      # npm dependencies
│   └── tailwind.config.js # Tailwind CSS configuration
├── test_milestone9.py    # Test suite
└── plan.txt              # Full requirements document
```

## Support

For issues or questions:
- Check the [Supabase documentation](https://supabase.com/docs)
- Check the [Vapi documentation](https://vapi.ai/docs)
- Check the [FastAPI documentation](https://fastapi.tiangolo.com)
- Check the [Next.js documentation](https://nextjs.org/docs)

## Version
AI CallerOS - Milestone 9 Complete