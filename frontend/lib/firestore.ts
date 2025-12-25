/**
 * Firestore client for fetching tournament predictions.
 * 
 * Implements:
 * - Fetch predictions/latest document
 * - Detect stale data (>2 hours)
 * - Trigger backend refresh when stale
 */

import { initializeApp, getApps } from 'firebase/app'
import { getFirestore, doc, getDoc } from 'firebase/firestore'
import type { TournamentSnapshot } from './types'

// Firebase configuration
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
}

// Initialize Firebase (only once)
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0]
const db = getFirestore(app)

// Stale data threshold: 2 hours
const STALE_THRESHOLD_MS = 2 * 60 * 60 * 1000

/**
 * Fetch latest predictions from Firestore.
 * 
 * If data is stale (>2 hours old), triggers backend refresh.
 * 
 * @returns Tournament snapshot or null if not found
 */
export async function fetchLatestPredictions(): Promise<TournamentSnapshot | null> {
  try {
    // Fetch predictions/latest document
    const docRef = doc(db, 'predictions', 'latest')
    const docSnap = await getDoc(docRef)

    if (!docSnap.exists()) {
      return null
    }

    const data = docSnap.data() as TournamentSnapshot

    // Check if data is stale
    if (data.updatedAt) {
      const updatedAt = new Date(data.updatedAt)
      const now = new Date()
      const ageMs = now.getTime() - updatedAt.getTime()

      if (ageMs > STALE_THRESHOLD_MS) {
        // Trigger backend refresh (fire-and-forget)
        triggerBackendRefresh()
      }
    }

    return data
  } catch (error) {
    console.error('Error fetching predictions:', error)
    throw error
  }
}

/**
 * Trigger backend refresh via POST /api/update-predictions.
 * 
 * Fire-and-forget - does not wait for response.
 */
function triggerBackendRefresh(): void {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
  
  fetch(`${backendUrl}/api/update-predictions`, {
    method: 'POST',
  }).catch((error) => {
    console.warn('Failed to trigger backend refresh:', error)
  })
}
