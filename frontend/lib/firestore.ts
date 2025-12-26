/**
 * Firestore client for fetching tournament predictions.
 * 
 * Implements:
 * - Fetch predictions/latest document
 * - Detect stale data (>2 hours)
 * - Trigger backend refresh when stale
 * - Client-side caching with 5-minute TTL
 * - SWR (stale-while-revalidate) pattern
 * - Real-time Firestore listeners
 * - Network-first caching strategy
 * - Optimistic UI updates
 */

import { initializeApp, getApps } from 'firebase/app'
import { getFirestore, doc, getDoc, onSnapshot, Unsubscribe } from 'firebase/firestore'
import type { TournamentSnapshot } from './types'
import { getCountryFlag } from './countryFlags'

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

// Stale data threshold: 2 hours (backend refresh trigger)
const STALE_THRESHOLD_MS = 2 * 60 * 60 * 1000

// Client-side cache TTL: 5 minutes
const CACHE_TTL_MS = 5 * 60 * 1000

// Client-side cache for predictions
interface CacheEntry {
  data: TournamentSnapshot
  timestamp: number
}

let cache: CacheEntry | null = null

/**
 * Fetch latest predictions from Firestore with caching (SWR pattern).
 * 
 * Strategy:
 * 1. Check client-side cache (5-minute TTL)
 * 2. If cache fresh: return cached data (stale-while-revalidate)
 * 3. If cache stale: fetch from Firestore, update cache
 * 4. If data >2 hours old: trigger backend refresh (fire-and-forget)
 * 
 * @param opts Options for cache behavior
 * @returns Tournament snapshot or null if not found
 */
export async function fetchLatestPredictions(opts?: {
  /** Skip cache and force fresh fetch */
  forceRefresh?: boolean
  /** Return stale cache immediately and revalidate in background */
  staleWhileRevalidate?: boolean
}): Promise<TournamentSnapshot | null> {
  const { forceRefresh = false, staleWhileRevalidate = true } = opts || {}

  // Check cache first (unless forced refresh)
  if (!forceRefresh && cache) {
    const cacheAge = Date.now() - cache.timestamp

    if (cacheAge < CACHE_TTL_MS) {
      console.log(`✅ Cache HIT (age: ${Math.round(cacheAge / 1000)}s)`)
      
      // Fresh cache - return immediately
      if (!staleWhileRevalidate) {
        return cache.data
      }

      // SWR: return stale cache, revalidate in background
      revalidateCache()
      return cache.data
    }

    console.log(`⚠️ Cache STALE (age: ${Math.round(cacheAge / 1000)}s, TTL: ${CACHE_TTL_MS / 1000}s)`)
  } else {
    console.log('❌ Cache MISS')
  }

  // Fetch fresh data from Firestore
  return await fetchFromFirestore()
}

/**
 * Fetch data from Firestore and update cache.
 * 
 * @returns Tournament snapshot or null if not found
 */
async function fetchFromFirestore(): Promise<TournamentSnapshot | null> {
  try {
    const startTime = Date.now()
    
    // Fetch predictions/latest document
    const docRef = doc(db, 'predictions', 'latest')
    const docSnap = await getDoc(docRef)

    const elapsed = Date.now() - startTime
    console.log(`🔥 Firestore fetch time: ${elapsed}ms`)

    if (!docSnap.exists()) {
      console.warn('⚠️ predictions/latest document not found')
      return null
    }

    const rawData = docSnap.data()
    
    console.log('🔥 Raw Firestore document:', rawData)
    console.log('📊 Matches in raw data:', rawData.matches ? rawData.matches.length : 'NO MATCHES FIELD')
    console.log('📊 Bracket in raw data:', rawData.bracket ? rawData.bracket.length : 'NO BRACKET FIELD')
    console.log('📊 Predictions in raw data:', rawData.predictions ? rawData.predictions.length : 'NO PREDICTIONS FIELD')

    // Create a map of predictions by match_id for easy lookup
    const predictionsMap = new Map()
    if (rawData.predictions) {
      rawData.predictions.forEach((pred: any) => {
        predictionsMap.set(pred.match_id, {
          winner: pred.winner,
          winProbability: pred.win_probability,
          predictedHomeScore: pred.predicted_home_score,
          predictedAwayScore: pred.predicted_away_score,
          reasoning: pred.reasoning,
          confidence: pred.confidence,
        })
      })
    }

    // Transform Firestore data to match frontend types
    const data: TournamentSnapshot = {
      groups: transformGroups(rawData.groups || {}),
      matches: transformMatches(rawData.matches || [], predictionsMap),
      bracket: transformMatches(rawData.bracket || [], predictionsMap),  // Transform bracket too!
      aiSummary: rawData.ai_summary || '',
      favorites: rawData.favorites || [],
      darkHorses: rawData.darkHorses || rawData.dark_horses || [],
      updatedAt: rawData.updated_at || rawData.updatedAt || new Date().toISOString(),
    }
    
    console.log('✅ Transformed tournament snapshot:', data)
    console.log('📊 Group matches in transformed data:', data.matches.length)
    console.log('📊 Knockout matches in transformed data:', data.bracket.length)

    // Update client-side cache
    cache = {
      data,
      timestamp: Date.now(),
    }
    console.log('💾 Cache updated')

    // Check if data is stale (>2 hours) → trigger backend refresh
    if (data.updatedAt) {
      const updatedAt = new Date(data.updatedAt)
      const now = new Date()
      const ageMs = now.getTime() - updatedAt.getTime()

      if (ageMs > STALE_THRESHOLD_MS) {
        console.warn(`⚠️ Data is stale (age: ${Math.round(ageMs / 1000 / 60)}min, threshold: ${STALE_THRESHOLD_MS / 1000 / 60}min)`)
        // Trigger backend refresh (fire-and-forget)
        triggerBackendRefresh()
      }
    }

    return data
  } catch (error) {
    console.error('❌ Error fetching predictions:', error)
    throw error
  }
}

/**
 * Revalidate cache in background (SWR pattern).
 * 
 * Fetches fresh data from Firestore without blocking.
 */
function revalidateCache(): void {
  console.log('🔄 Revalidating cache in background...')
  fetchFromFirestore().catch((error) => {
    console.error('❌ Background revalidation failed:', error)
  })
}

/**
 * Transform Firestore matches array to frontend format.
 * 
 * Converts snake_case to camelCase for match fields.
 * Adds country flags based on team names.
 * Merges predictions from predictions map.
 */
function transformMatches(firestoreMatches: any[], predictionsMap?: Map<number, any>): any[] {
  return firestoreMatches.map(match => {
    const prediction = predictionsMap?.get(match.id)
    
    return {
      id: match.id,
      matchNumber: match.match_number,
      homeTeamId: match.home_team_id,
      awayTeamId: match.away_team_id,
      homeTeamName: match.home_team_name,
      awayTeamName: match.away_team_name,
      homeTeamFlag: getCountryFlag(match.home_team_name),
      awayTeamFlag: getCountryFlag(match.away_team_name),
      venue: match.venue,
      stageId: match.stage_id,
      kickoff: match.kickoff,
      label: match.label,
      homeScore: match.home_score,
      awayScore: match.away_score,
      prediction: prediction || match.prediction,
      hasRealData: match.has_real_data,
    }
  })
}

/**
 * Transform Firestore groups structure to frontend format.
 * 
 * Firestore: { A: [team1, team2], B: [team3, team4] }
 * Frontend: { A: { letter: 'A', teams: [team1, team2] }, B: { letter: 'B', teams: [team3, team4] } }
 * Adds country flags based on team names.
 */
function transformGroups(firestoreGroups: Record<string, any[]>): Record<string, any> {
  const transformed: Record<string, any> = {}
  
  for (const [letter, teams] of Object.entries(firestoreGroups)) {
    transformed[letter] = {
      letter,
      teams: teams.map(team => {
        const teamName = team.team_name || team.name || ''
        return {
          id: team.team_id || 0,
          name: teamName,
          flag: team.flag || getCountryFlag(teamName),
          played: team.played || 0,
          won: team.won || 0,
          draw: team.draw || 0,
          lost: team.lost || 0,
          goalsFor: team.goals_for || 0,
          goalsAgainst: team.goals_against || 0,
          points: team.points || 0,
          rank: team.rank,
          predictedPlacement: team.predicted_placement,
          predictedRank: team.predicted_rank,
        }
      }),
    }
  }
  
  return transformed
}

/**
 * Subscribe to real-time updates for predictions/latest document.
 * 
 * Automatically updates cache when Firestore document changes.
 * 
 * @param callback Callback fired when data updates
 * @returns Unsubscribe function to stop listening
 */
export function subscribeToLatestPredictions(
  callback: (data: TournamentSnapshot | null) => void
): Unsubscribe {
  const docRef = doc(db, 'predictions', 'latest')

  console.log('📡 Subscribing to real-time updates...')

  return onSnapshot(
    docRef,
    (docSnap) => {
      if (!docSnap.exists()) {
        console.warn('⚠️ predictions/latest document not found (real-time)')
        callback(null)
        return
      }

      const rawData = docSnap.data()
      console.log('🔔 Real-time update received')

      // Create predictions map
      const predictionsMap = new Map()
      if (rawData.predictions) {
        rawData.predictions.forEach((pred: any) => {
          predictionsMap.set(pred.match_id, {
            winner: pred.winner,
            winProbability: pred.win_probability,
            predictedHomeScore: pred.predicted_home_score,
            predictedAwayScore: pred.predicted_away_score,
            reasoning: pred.reasoning,
            confidence: pred.confidence,
          })
        })
      }

      // Transform data
      const data: TournamentSnapshot = {
        groups: transformGroups(rawData.groups || {}),
        matches: transformMatches(rawData.matches || [], predictionsMap),
        bracket: transformMatches(rawData.bracket || [], predictionsMap),  // Transform bracket too!
        aiSummary: rawData.ai_summary || '',
        favorites: rawData.favorites || [],
        darkHorses: rawData.darkHorses || rawData.dark_horses || [],
        updatedAt: rawData.updated_at || rawData.updatedAt || new Date().toISOString(),
      }

      // Update cache
      cache = {
        data,
        timestamp: Date.now(),
      }
      console.log('💾 Cache updated from real-time listener')

      // Notify callback
      callback(data)
    },
    (error) => {
      console.error('❌ Real-time listener error:', error)
    }
  )
}

/**
 * Prefetch predictions on app load.
 * 
 * Pre-populates cache before user requests data.
 * Call this in layout.tsx or root component useEffect.
 * 
 * @returns Promise that resolves when prefetch completes
 */
export async function prefetchPredictions(): Promise<void> {
  console.log('⚡ Prefetching predictions...')
  try {
    await fetchFromFirestore()
    console.log('✅ Prefetch complete')
  } catch (error) {
    console.error('❌ Prefetch failed:', error)
  }
}

/**
 * Clear client-side cache.
 * 
 * Useful for testing or forcing fresh data.
 */
export function clearCache(): void {
  cache = null
  console.log('🗑️ Cache cleared')
}

/**
 * Trigger backend refresh via POST /api/update-tournament.
 * 
 * Fire-and-forget - does not wait for response.
 */
function triggerBackendRefresh(): void {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
  
  console.log('🔄 Triggering backend refresh...')
  fetch(`${backendUrl}/api/update-tournament`, {
    method: 'POST',
  }).catch((error) => {
    console.warn('❌ Failed to trigger backend refresh:', error)
  })
}
