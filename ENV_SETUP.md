# Environment Configuration

This project uses a `.env` file in the project root for all environment variables.

## Firebase Project: vmkula

The project is configured to use the **vmkula** Firebase project.

## Required Environment Variables

Copy the following template to your `.env` file and fill in your actual values:

```bash
# ========================================
# Firebase MCP Server Configuration
# ========================================
# Download service account key from Firebase Console:
# Project Settings > Service Accounts > Generate New Private Key
# Save to SA/ directory (already in .gitignore)
GOOGLE_APPLICATION_CREDENTIALS=SA/vmkula-firebase-adminsdk-fbsvc-XXXXX.json

# ========================================
# Required API Keys
# ========================================
# API-Football v3 API Key (https://www.api-football.com/)
# Free tier: 100 requests/day
API_FOOTBALL_KEY=your_api_football_key_here

# Google Gemini API Key (https://ai.google.dev/)
GEMINI_API_KEY=your_gemini_api_key_here

# ========================================
# Firebase Configuration (vmkula project)
# ========================================
# Backend - Firestore server-side SDK
FIRESTORE_PROJECT_ID=vmkula

# Frontend - Firebase client SDK (public variables)
NEXT_PUBLIC_FIREBASE_PROJECT_ID=vmkula
NEXT_PUBLIC_FIREBASE_API_KEY=your-firebase-web-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=vmkula.firebaseapp.com
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=vmkula.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id

# ========================================
# Optional Configuration (defaults shown)
# ========================================
# Cache time-to-live in hours
CACHE_TTL_HOURS=24

# Cache directory path
CACHE_DIR=cache

# API-Football request delay in seconds (avoid rate limiting)
API_FOOTBALL_DELAY_SECONDS=0.5

# Maximum retry attempts for API calls
MAX_RETRIES=3

# Debug mode (verbose logging)
DEBUG=false
```

## Getting Firebase Configuration Values

### 1. Backend (Service Account)
- Go to Firebase Console → Project Settings → Service Accounts
- Click "Generate New Private Key"
- Save JSON file to `SA/` directory
- Update `GOOGLE_APPLICATION_CREDENTIALS` path in `.env`

### 2. Frontend (Web SDK Config)
- Go to Firebase Console → Project Settings → General
- Scroll to "Your apps" section
- Click on your web app or create one
- Copy the config values to `.env` with `NEXT_PUBLIC_` prefix

## Security Notes

- ✅ `.env` is already in `.gitignore` - NEVER commit it to git
- ✅ `SA/` directory (service account keys) is in `.gitignore`
- ✅ `NEXT_PUBLIC_*` variables are safe to expose in frontend (they're public)
- ❌ DO NOT commit API keys or service account keys
