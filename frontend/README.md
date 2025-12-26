# World Cup 2026 Predictions Frontend

Next.js web application for displaying AI-powered World Cup 2026 predictions with real-time updates via Firebase.

## 🎨 Design Philosophy

**Modern Sports Stadium**: Dynamic pitch-to-podium energy with championship aesthetic.

- **Typography**: Montserrat ExtraBold for headers, Inter for body text
- **Color Palette**: Emerald Green (#10B981), Electric Yellow (#FBBF24), Midnight Blue (#0F172A)
- **UX Principles**: Mobile-first responsive, staggered animations, touch-optimized (44px+ tap targets)
- **Accessibility**: WCAG AA compliant with ARIA labels and keyboard navigation

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  Next.js 16 App Router (React 19)              │
│  - Server Components for SEO                    │
│  - Client Components for interactivity          │
└───────────────────┬─────────────────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
┌────────▼─────────┐  ┌────────▼──────────┐
│ Firebase SDK     │  │ Tailwind CSS 4    │
│ - Firestore      │  │ - PostCSS         │
│ - Real-time      │  │ - Mobile-first    │
└──────────────────┘  └───────────────────┘
```

### Key Features

- **Real-time Updates**: Firebase Firestore listeners for live prediction updates
- **Internationalization**: next-intl for Norwegian (nb-NO) translations
- **Smart Caching**: SWR pattern with 5-minute client-side TTL
- **Responsive Design**: Mobile-first (320px → 1440px+) with touch-optimized controls
- **Favorites System**: localStorage-based favorite teams tracking across tabs
- **4 View Modes**: Favorites, Groups, Matches, Bracket (URL-synced tabs)

## 🚀 Getting Started

### Prerequisites

- **Node.js**: 20.x or higher
- **npm**: 10.x or higher
- **Firebase Project**: Firestore enabled with predictions collection

### Local Development Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Set up environment variables**:
   
   Create `.env.local` file in `frontend/` directory:
   ```bash
   # Firebase Configuration
   NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key_here
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-firebase-project-id
   NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789012
   NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789012:web:abcdef123456
   
   # Backend API (for tournament refresh)
   NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
   ```

3. **Run development server**:
   ```bash
   npm run dev
   
   # Server starts at http://localhost:3000
   ```

4. **Run tests**:
   ```bash
   # Run all tests
   npm test
   
   # Run with UI
   npm run test:ui
   
   # Generate coverage report
   npm run test:coverage
   ```

5. **Build for production**:
   ```bash
   npm run build
   npm start
   ```

## 📁 Project Structure

```
frontend/
├── app/                      # Next.js App Router
│   ├── bracket/             # Knockout bracket view page
│   ├── groups/              # Group standings view page
│   ├── matches/             # All matches view page
│   ├── layout.tsx           # Root layout with i18n provider
│   ├── page.tsx             # Homepage (merged view with tabs)
│   └── globals.css          # Global Tailwind styles
├── components/              # Reusable React components
│   ├── BracketView.tsx      # Knockout tournament bracket
│   ├── ConnectionStatus.tsx # Firestore connection indicator
│   ├── ErrorBoundary.tsx    # Error handling component
│   ├── GroupCard.tsx        # Group standings table
│   ├── LoadingSpinner.tsx   # Loading state component
│   └── MatchCard.tsx        # Match fixture card
├── lib/                     # Utilities and data layer
│   ├── countryFlags.ts      # Country → emoji flag mapping
│   ├── favorites.ts         # localStorage favorite teams manager
│   ├── firestore.ts         # Firebase client and data fetching
│   ├── translationUtils.ts  # i18n helper functions
│   └── types.ts             # TypeScript type definitions
├── __tests__/               # Test files (Vitest)
│   ├── integration/         # Integration tests
│   ├── lib/                 # Library tests
│   └── *.test.tsx           # Component tests
└── public/                  # Static assets
```

## 🔧 Component Architecture

### Data Flow

```
Firestore (predictions/latest)
       ↓
lib/firestore.ts (fetchLatestPredictions)
       ↓
app/page.tsx (useEffect + useState)
       ↓
components/GroupCard, MatchCard, BracketView
```

### Key Components

**GroupCard** (`components/GroupCard.tsx`):
- Displays group standings table with team stats
- Shows predicted placement badges
- Star icon for adding favorite teams
- Responsive grid layout (1-column mobile, 2-column desktop)

**MatchCard** (`components/MatchCard.tsx`):
- Match fixture with team names, flags, venue, kickoff time
- AI prediction (winner, score, probability, reasoning)
- Confidence indicator (high/medium/low)
- Staggered animation on load

**BracketView** (`components/BracketView.tsx`):
- Knockout tournament tree visualization
- Rounds: Round of 32 → Round of 16 → Quarter → Semi → Final
- TBD handling for unresolved matchups
- Horizontal scroll on mobile

**ConnectionStatus** (`components/ConnectionStatus.tsx`):
- Fixed-position Firestore connection indicator
- Green = connected, Red = disconnected, Yellow = connecting
- Auto-hides after 3 seconds when connected

## 🌐 Internationalization (i18n)

**Framework**: next-intl

**Supported Locales**:
- Norwegian Bokmål (`nb-NO`) - Primary language

**Translation Files**: `messages/nb.json`

**Usage**:
```typescript
import { useTranslations } from 'next-intl'

function MyComponent() {
  const t = useTranslations('home')
  return <h1>{t('title')}</h1>
}
```

## 🎨 Tailwind CSS Configuration

**Version**: Tailwind CSS 4 (PostCSS-based)

**Custom Theme** (`tailwind.config.ts`):
- Extended color palette: emerald (primary), yellow (accent), slate (neutral)
- Custom animations: fadeIn, slideIn, pulse
- Responsive breakpoints: mobile-first (sm: 640px, md: 768px, lg: 1024px, xl: 1280px)

**Global Styles** (`app/globals.css`):
```css
@import "tailwindcss";

/* Championship-grade typography */
body {
  font-family: 'Inter', sans-serif;
  font-optical-sizing: auto;
}

h1, h2, h3 {
  font-family: 'Montserrat', sans-serif;
  font-weight: 800;
}
```

## 🔥 Firebase Integration

**SDK**: Firebase JS SDK 12.7.0

**Firestore Schema** (`lib/firestore.ts`):

**Main Document**: `predictions/latest`
```typescript
{
  groups: { [letter: string]: GroupStanding[] },
  matches: Match[],
  bracket: Match[],
  aiSummary: string,
  favorites: string[],
  darkHorses: string[],
  updatedAt: string
}
```

**Caching Strategy**:
- Client-side cache: 5-minute TTL
- Stale-while-revalidate: Return cached data immediately, revalidate in background
- Firestore real-time listener: Auto-update cache on document changes
- Stale data threshold: Trigger backend refresh if data >2 hours old

**Key Functions**:
- `fetchLatestPredictions()`: Fetch predictions with SWR caching
- `subscribeToLatestPredictions(callback)`: Real-time listener
- `prefetchPredictions()`: Pre-populate cache on app load
- `clearCache()`: Force fresh data fetch

## 🧪 Testing

**Framework**: Vitest 4 + React Testing Library

**Test Structure**:
- **Unit Tests**: `__tests__/*.test.tsx` for components
- **Integration Tests**: `__tests__/integration/*.test.tsx` for data flow
- **Library Tests**: `__tests__/lib/*.test.ts` for utilities

**Run Tests**:
```bash
# All tests
npm test

# Watch mode
npm test -- --watch

# UI mode (browser-based test runner)
npm run test:ui

# Coverage report (target: 80%+)
npm run test:coverage
```

**Coverage Configuration** (`.coveragerc`):
- Minimum: 80% (enforced in CI)
- Excluded: `*.config.ts`, `*.d.ts`, `__tests__/`

## 📦 Deployment (Firebase Hosting)

### Build and Deploy

```bash
# Build optimized production bundle
npm run build

# Preview production build locally
npm start

# Deploy to Firebase Hosting
firebase deploy --only hosting

# Deploy with custom message
firebase deploy --only hosting -m "Deploy v1.2.3"
```

### Firebase Hosting Configuration (`firebase.json`):

```json
{
  "hosting": {
    "public": "frontend/.next/out",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      { "source": "**", "destination": "/index.html" }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css)",
        "headers": [
          { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
        ]
      }
    ]
  }
}
```

### CI/CD (GitHub Actions)

See `.github/workflows/frontend-deploy.yml`:
- Trigger: Push to `main` branch (frontend/ changes only)
- Steps: Install deps → Run tests → Build → Deploy to Firebase Hosting
- Secrets: `FIREBASE_TOKEN` (CI token from `firebase login:ci`)

## 🛠️ Troubleshooting

### Common Errors

**1. "Firebase configuration missing"**
- **Cause**: `.env.local` not found or incomplete
- **Solution**: Copy `.env.example` to `.env.local` and fill in Firebase credentials
- **Verify**: Check `process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID` in browser console

**2. "predictions/latest document not found"**
- **Cause**: Backend hasn't published predictions yet
- **Solution**: Run `curl -X POST http://localhost:8000/api/update-predictions` to trigger backend
- **Verify**: Check Firestore console for `predictions/latest` document

**3. "Cache MISS" logged repeatedly**
- **Cause**: Client-side cache disabled or expired
- **Solution**: This is normal on first load. Subsequent loads should show "Cache HIT"
- **Debug**: Check `localStorage` for `vmkula_favorite_teams` (favorites only)

**4. "Connection status stuck on yellow"**
- **Cause**: Firestore real-time listener not connecting
- **Solution**: Check Firebase console → Firestore → Rules (must allow public read)
- **Firestore Rules**:
  ```
  rules_version = '2';
  service cloud.firestore {
    match /databases/{database}/documents {
      match /predictions/{document=**} {
        allow read: if true;
        allow write: if false;
      }
    }
  }
  ```

### Clear Local Cache

```bash
# Clear Next.js build cache
rm -rf frontend/.next

# Clear node_modules (full reinstall)
rm -rf frontend/node_modules
npm install

# Clear browser cache (in DevTools)
# Application tab → Storage → Clear site data
```

### View Logs

**Development**:
```bash
# Next.js dev server logs
npm run dev
# Check browser console (F12) for frontend logs
```

**Production (Firebase Hosting)**:
```bash
# View Hosting deployment history
firebase hosting:channel:list

# View recent deployment logs
firebase hosting:channel:open live
```

## 📊 Performance

### Lighthouse Scores (Target)

- **Performance**: 90+ (mobile), 95+ (desktop)
- **Accessibility**: 100 (WCAG AA compliant)
- **Best Practices**: 95+
- **SEO**: 100

### Optimization Strategies

- **Code Splitting**: Next.js automatic route-based splitting
- **Image Optimization**: Use `next/image` for all images (none currently - flags are emoji)
- **Font Loading**: Google Fonts with `font-display: swap`
- **Bundle Size**: Target <200KB gzipped initial bundle
- **Prefetching**: Prefetch predictions on app load (`prefetchPredictions()`)

## 🔗 Related Documentation

- **Backend API**: See `../backend/README.md` for API endpoints and data flow
- **Data Model**: See `../backend/docs/data-model.md` for Firestore schema details
- **Project Constitution**: See `../RULES.md` for code standards and architecture rules

## 📝 License

See `../LICENSE` for details.
