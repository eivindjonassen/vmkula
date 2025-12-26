# vmkula - World Cup 2026 AI Prediction Platform

AI-powered prediction platform for FIFA World Cup 2026, combining Python backend logic with Google Gemini AI magic.

## 🏆 Project Overview

**Mission**: Predict the 2026 FIFA World Cup using AI-driven analysis of team statistics, form, and xG data.

**Philosophy**: **"Logic in Python, Magic in AI"**
- **Python Backend**: Calculates group standings, third-place qualifiers, and knockout brackets using official FIFA rules
- **Gemini AI**: Generates match predictions based on team statistics, form strings, and xG (expected goals) data
- **Next.js Frontend**: Displays predictions with real-time updates via Firebase Firestore

## 🎯 Key Features

- **104 Match Predictions**: AI predictions for all group stage and knockout matches
- **Real-time Updates**: Firestore integration for instant frontend updates
- **Smart Caching**: 24-hour TTL on team statistics, diff-based prediction updates
- **xG-Based Analysis**: Expected goals data from API-Football for accurate predictions
- **FIFA Rules Engine**: Official tiebreaker sequence (GD → Goals → H2H → Fair Play → Seed)
- **Mobile-First UI**: Championship-grade design with WCAG AA accessibility
- **4 View Modes**: Favorites, Groups, Matches, Bracket (URL-synced navigation)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                       │
│  - React 19 + App Router                                        │
│  - Tailwind CSS 4 (Mobile-first responsive)                     │
│  - next-intl (Norwegian i18n)                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Firestore Real-time Listener
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                   Firebase Firestore                            │
│  - predictions/latest (Hot Data)                                │
│  - matches/{id}/history/{timestamp} (Cold Data)                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ REST API (POST /api/update-predictions)
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                   Backend (Python + FastAPI)                    │
│  - FIFA Engine (Group standings + knockout bracket)             │
│  - Data Aggregator (API-Football team stats + xG)               │
│  - AI Agent (Gemini 3.0 Pro predictions)                        │
│  - Firestore Publisher (Diff-based updates)                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                   ┌────────┴──────────┐
                   │                   │
        ┌──────────▼────────┐  ┌───────▼──────────┐
        │  API-Football v3  │  │  Google Gemini   │
        │  - Team stats     │  │  - 3.0 Pro       │
        │  - xG data        │  │  - JSON mode     │
        │  - Form strings   │  │  - Retry logic   │
        └───────────────────┘  └──────────────────┘
```

### Data Flow

1. **Cloud Scheduler** triggers daily update (10:00 AM UTC)
2. **Backend** fetches team statistics from API-Football (with 24h caching)
3. **FIFA Engine** calculates group standings and resolves knockout bracket
4. **Gemini AI** generates predictions for all 104 matches
5. **Firestore Publisher** updates predictions/latest document (diff-based)
6. **Frontend** receives real-time updates via Firestore listener
7. **User** views predictions in mobile-optimized interface

## 📁 Monorepo Structure

```
vmkula/
├── backend/                 # Python FastAPI prediction engine
│   ├── src/                 # Source code
│   │   ├── ai_agent.py      # Gemini AI prediction service
│   │   ├── data_aggregator.py  # API-Football client
│   │   ├── fifa_engine.py   # FIFA rules engine
│   │   ├── firestore_manager.py  # Firestore client
│   │   ├── firestore_publisher.py  # Snapshot publisher
│   │   └── main.py          # FastAPI application
│   ├── tests/               # Test suite (pytest)
│   ├── Dockerfile           # Cloud Run container
│   ├── requirements.txt     # Production dependencies
│   └── README.md            # Backend documentation
├── frontend/                # Next.js web application
│   ├── app/                 # App Router pages
│   ├── components/          # React components
│   ├── lib/                 # Utilities (firestore, types, i18n)
│   ├── __tests__/           # Test suite (Vitest)
│   ├── package.json         # Dependencies
│   └── README.md            # Frontend documentation
├── specs/                   # Feature specifications (Bifrost)
│   └── vmkula-website/      # Website feature spec
├── .github/workflows/       # GitHub Actions CI/CD
│   ├── backend-deploy.yml   # Backend deployment
│   ├── backend-test.yml     # Backend tests
│   ├── frontend-deploy.yml  # Frontend deployment
│   └── frontend-test.yml    # Frontend tests
├── firebase.json            # Firebase configuration
├── firestore.rules          # Firestore security rules
├── RULES.md                 # Project constitution (code standards)
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.11+ (backend)
- **Node.js**: 20.x+ (frontend)
- **Firebase Project**: Firestore enabled
- **API Keys**:
  - [API-Football](https://www.api-football.com/) (team statistics)
  - [Google Gemini](https://ai.google.dev/) (AI predictions)

### Local Development

**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# Set up .env file (see backend/README.md)
# Run tests
pytest --cov=src

# Start server
uvicorn src.main:app --reload
# → http://localhost:8000
```

**Frontend**:
```bash
cd frontend
npm install

# Set up .env.local file (see frontend/README.md)
# Run tests
npm test

# Start dev server
npm run dev
# → http://localhost:3000
```

**Trigger Prediction Update**:
```bash
# Load tournament structure
curl -X POST http://localhost:8000/api/update-tournament

# Generate AI predictions (run after update-tournament)
curl -X POST http://localhost:8000/api/update-predictions
```

## 🌐 Deployment

### Production Environment

- **Backend**: Google Cloud Run (us-east4)
  - URL: `https://vmkula-backend-[hash].a.run.app`
  - Trigger: Cloud Scheduler (daily at 10:00 AM UTC)
  - See `backend/DEPLOYMENT.md` for details

- **Frontend**: Firebase Hosting
  - URL: `https://vmkula-website.web.app`
  - Trigger: GitHub Actions on push to `main`
  - See `.github/workflows/frontend-deploy.yml`

### Deployment Status

[![Backend Tests](https://github.com/yourusername/vmkula/actions/workflows/backend-test.yml/badge.svg)](https://github.com/yourusername/vmkula/actions/workflows/backend-test.yml)
[![Frontend Tests](https://github.com/yourusername/vmkula/actions/workflows/frontend-test.yml/badge.svg)](https://github.com/yourusername/vmkula/actions/workflows/frontend-test.yml)

## 📚 Documentation

- **Backend API**: [`backend/docs/api.md`](backend/docs/api.md) - REST API reference
- **Data Model**: [`backend/docs/data-model.md`](backend/docs/data-model.md) - Firestore schema and entities
- **Backend README**: [`backend/README.md`](backend/README.md) - Setup, testing, deployment
- **Frontend README**: [`frontend/README.md`](frontend/README.md) - Components, i18n, Firebase integration
- **Project Constitution**: [`RULES.md`](RULES.md) - Code standards, architecture rules, TDD workflow

## 🧩 Core Technologies

### Backend
- **Python 3.11**: Core language
- **FastAPI**: REST API framework
- **Firebase Admin SDK**: Firestore integration
- **Google Generative AI**: Gemini 3.0 Pro predictions
- **Requests**: API-Football HTTP client
- **Pytest**: Test framework

### Frontend
- **Next.js 16**: React framework (App Router)
- **React 19**: UI library
- **Tailwind CSS 4**: Utility-first styling
- **Firebase JS SDK**: Firestore real-time updates
- **next-intl**: Internationalization (Norwegian)
- **Vitest**: Test framework

### Infrastructure
- **Google Cloud Run**: Backend hosting (serverless containers)
- **Firebase Hosting**: Frontend hosting (CDN-backed static site)
- **Firestore**: NoSQL database (real-time sync)
- **Cloud Scheduler**: Cron jobs (daily prediction updates)
- **GitHub Actions**: CI/CD pipelines

## 🧪 Testing & Quality

### Test-Driven Development (TDD)

This project follows strict TDD methodology enforced by the Bifrost workflow:

**Test Coverage**:
- Backend: 80%+ required (enforced in CI)
- Frontend: 80%+ required (enforced in CI)

**Test Commands**:
```bash
# Backend tests
cd backend
pytest --cov=src --cov-report=html

# Frontend tests
cd frontend
npm run test:coverage

# Run all tests (from root)
./scripts/test-all.sh
```

**CI/CD Pipeline**:
- Tests run on every PR (backend + frontend)
- Deployment blocked if tests fail
- Coverage reports uploaded to Codecov

## 🤝 Contributing

This project uses the **Bifrost AI Spec Development Kit** for structured development.

### Workflow

1. **Create Specification**: Use `/spec` command to create feature spec
2. **Generate Plan**: Use `/plan` command for implementation plan
3. **Break Down Tasks**: Use `/tasks` command for granular task list
4. **Implement with TDD**: Write tests first, then implement
5. **Polish**: Use `/polish-*` commands (docs, refactor, security, etc.)

### Code Standards

See [`RULES.md`](RULES.md) for:
- Code style and conventions
- Component architecture
- Reusable component library
- i18n requirements (Norwegian)
- Testing standards
- Git workflow

### Commit Guidelines

```bash
# TDD workflow enforced (.bifrost/tdd-state.json)
git add .
git commit -m "Add group standings calculation with tiebreaker logic"
# → State machine: IDLE → TEST_FAILING → IMPLEMENTING → TEST_PASSING → COMMITTED
```

## 🔒 Security & Privacy

- **API Keys**: Never commit API keys (use `.env` files, Git-ignored)
- **Firestore Rules**: Public read (predictions), authenticated write only
- **CORS**: Restricted to production domain in Cloud Run deployment
- **IAM**: Cloud Run service account with minimal permissions
- **Secrets**: Stored in GitHub Secrets (CI/CD) and Cloud Secret Manager (production)

## 📊 Performance Metrics

### Backend
- **Prediction Pipeline**: ~2-3 minutes (104 matches, with caching)
- **API-Football Caching**: 24-hour TTL (minimize rate limits)
- **Gemini Retry Logic**: Max 1 retry (cost optimization)

### Frontend
- **Lighthouse Score**: 90+ (mobile), 95+ (desktop)
- **Bundle Size**: <200KB gzipped initial bundle
- **Firestore Cache**: 5-minute client-side TTL (SWR pattern)

## 🐛 Troubleshooting

### Backend Issues
- **API-Football Rate Limit**: Free tier limited to 100 requests/day - caching enabled
- **Gemini Timeout**: Retry triggered automatically (max 2 attempts)
- **Firestore Permission Denied**: Ensure service account has `Cloud Datastore User` role

### Frontend Issues
- **Firebase Config Missing**: Check `.env.local` for all `NEXT_PUBLIC_FIREBASE_*` variables
- **predictions/latest Not Found**: Run backend update first (`/api/update-predictions`)
- **Stale Data Warning**: Backend refresh triggered automatically if data >2 hours old

See individual READMEs for detailed troubleshooting:
- Backend: [`backend/README.md#troubleshooting`](backend/README.md#troubleshooting)
- Frontend: [`frontend/README.md#troubleshooting`](frontend/README.md#troubleshooting)

## 📄 License

MIT License - See [`LICENSE`](LICENSE) for details.

---

**Built with 🤖 AI + ⚡ Firebase + 🐍 Python + ⚛️ React**

*"Logic in Python, Magic in AI"*
