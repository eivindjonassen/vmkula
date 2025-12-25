# Firebase MCP Server Setup Guide

This guide walks you through setting up the Firebase MCP server for the vmkula project.

---

## Prerequisites

- Firebase project created (or create one at [console.firebase.google.com](https://console.firebase.google.com))
- Node.js installed (for npx)
- OpenCode or Cursor IDE with MCP support

---

## Step 1: Download Service Account Key

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project (or create new project: "vmkula-2026")
3. Navigate to **Project Settings** (gear icon) → **Service Accounts**
4. Click **"Generate New Private Key"**
5. Save the JSON file to a secure location (e.g., `~/firebase-keys/vmkula-service-account.json`)

⚠️ **IMPORTANT**: Do NOT commit this file to git. It contains sensitive credentials.

---

## Step 2: Set Environment Variable

### macOS/Linux

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/firebase-keys/vmkula-service-account.json"
```

Then reload:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

### Windows

1. Open System Properties → Advanced → Environment Variables
2. Add new User Variable:
   - **Name**: `GOOGLE_APPLICATION_CREDENTIALS`
   - **Value**: `C:\firebase-keys\vmkula-service-account.json`

---

## Step 3: Create Local .env File

Create `.env` in project root (already in .gitignore):

```bash
# Firebase MCP Server
GOOGLE_APPLICATION_CREDENTIALS=/Users/yourusername/firebase-keys/vmkula-service-account.json

# API Keys (add when available)
API_FOOTBALL_KEY=your_key_here
GEMINI_API_KEY=your_key_here

# Firebase Project Config
NEXT_PUBLIC_FIREBASE_PROJECT_ID=vmkula-2026
NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=vmkula-2026.firebaseapp.com
```

---

## Step 4: Enable Firestore in Firebase Console

1. In Firebase Console, go to **Build** → **Firestore Database**
2. Click **"Create database"**
3. Choose **"Start in test mode"** (we'll add security rules later)
4. Select a location (e.g., `us-central1`)
5. Click **"Enable"**

---

## Step 5: Verify MCP Server Connection

The Firebase MCP server is already configured in `opencode.json`:

```json
{
  "mcpServers": {
    "firebase": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-firebase"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "${env:GOOGLE_APPLICATION_CREDENTIALS}"
      }
    }
  }
}
```

Restart OpenCode/Cursor to load the MCP server.

---

## Step 6: Test Firebase MCP Tools

In OpenCode, you can now use Firebase MCP tools:

### Query Firestore Collections
```
Can you query the predictions collection in Firestore?
```

### Get a Specific Document
```
Get the latest document from predictions/latest
```

### Write Test Data
```
Create a test document in predictions/test with some sample data
```

---

## Available MCP Tools

| Tool | Purpose | Example Use |
|------|---------|-------------|
| `firestore_query` | Query collections | Get all matches from a stage |
| `firestore_get` | Get specific document | Fetch predictions/latest |
| `firestore_set` | Write/overwrite document | Save prediction snapshot |
| `firestore_update` | Update document fields | Update timestamp only |
| `firestore_delete` | Delete document | Remove test data |

---

## Firestore Collections (Planned Schema)

### Main Collection: `predictions`
- **Document**: `latest`
- **Purpose**: Hot data for frontend (fast reads)
- **Contents**: Groups, bracket, AI summary

### Sub-collection: `matches/{match_id}/history`
- **Documents**: Timestamped prediction history
- **Purpose**: Cold data for analytics
- **Optimization**: Only written when prediction changes (diff check)

---

## Security Rules (Production)

Before deploying to production, update Firestore security rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Public read access
    match /predictions/{document=**} {
      allow read: if true;
      allow write: if false;  // Only Cloud Run service account can write
    }
    
    // History is also public (for analytics views)
    match /matches/{matchId}/history/{document=**} {
      allow read: if true;
      allow write: if false;  // Only Cloud Run service account can write
    }
  }
}
```

Deploy rules:
```bash
firebase deploy --only firestore:rules
```

---

## Troubleshooting

### Error: "GOOGLE_APPLICATION_CREDENTIALS not set"
- Verify environment variable is set: `echo $GOOGLE_APPLICATION_CREDENTIALS`
- Restart your terminal/IDE after setting the variable

### Error: "Permission denied"
- Check service account has "Cloud Datastore User" role
- Go to [IAM Console](https://console.cloud.google.com/iam-admin/iam)
- Find your service account, add role if missing

### Error: "Project not found"
- Verify project ID matches in service account JSON
- Check Firestore is enabled in Firebase Console

### MCP Server Not Loading
- Check `opencode.json` syntax is valid
- Restart OpenCode/Cursor completely
- Check terminal output for MCP server errors

---

## Cost Considerations

### Firestore Pricing (Free Tier)
- **Reads**: 50,000/day
- **Writes**: 20,000/day
- **Storage**: 1 GB

**Our Usage**:
- ~100 reads/hour (users viewing predictions)
- ~104 writes/day (daily prediction updates)
- ~1-2 MB storage (well within limits)

**Estimated Cost**: $0/month (stays within free tier)

---

## Next Steps

Once Firebase MCP is set up:

1. ✅ Test connection by querying Firestore
2. ✅ Create initial collections structure
3. ✅ Seed test data for frontend development
4. ✅ Configure security rules for production

---

**Last Updated**: 2025-12-25
