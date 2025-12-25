# Configuration Summary

## Environment Configuration
- **Single .env file**: All configuration in project root `.env` (not committed)
- **Documentation**: See `ENV_SETUP.md` for complete setup instructions
- **Firebase Project**: vmkula

## Key Configuration Points

### 1. Backend (Python)
- **Config Loading**: `backend/src/config.py` validates required env vars on startup
- **Firestore**: Uses `FIRESTORE_PROJECT_ID=vmkula` and service account from `GOOGLE_APPLICATION_CREDENTIALS`
- **API Keys**: API-Football and Gemini API keys required

### 2. Frontend (Next.js)
- **Firebase SDK**: Configured for vmkula project via `NEXT_PUBLIC_FIREBASE_*` variables
- **Build**: Static export for Firebase Hosting (`next.config.ts` has `output: 'export'`)

### 3. Security
- ✅ `.env` in `.gitignore` - never committed
- ✅ `SA/` directory for service account keys - never committed
- ✅ `NEXT_PUBLIC_*` variables are safe (public by design)

## Quick Setup

1. Copy `.env` template from `ENV_SETUP.md`
2. Download Firebase service account key → save to `SA/`
3. Get Firebase web config from console → add `NEXT_PUBLIC_*` vars
4. Add API keys for API-Football and Gemini
5. Run `cd backend && python -c "from src.config import config; print('✅ Config valid')"` to test

## Firebase Project Details
- **Project ID**: vmkula
- **Backend**: Firestore with service account auth
- **Frontend**: Firebase client SDK (public web app config)
- **Deployment**: Firebase Hosting (frontend), Cloud Run (backend)
