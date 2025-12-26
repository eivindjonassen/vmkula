/**
 * Matches page - Display all 104 matches with filtering and search.
 * 
 * Features:
 * - Fetch predictions using fetchLatestPredictions()
 * - Display all matches using MatchCard component
 * - Stage filter (All, Group Stage, Round of 32, etc.)
 * - Date filter
 * - Search by team name
 * - Sort by kickoff time
 */

'use client'

import { useState, useEffect, useMemo } from 'react'
import { fetchLatestPredictions } from '../../lib/firestore'
import type { TournamentSnapshot, Match } from '../../lib/types'
import MatchCard from '../../components/MatchCard'

const STAGE_NAMES: Record<number, string> = {
  1: 'Group Stage',
  2: 'Round of 32',
  3: 'Round of 16',
  4: 'Quarter-finals',
  5: 'Semi-finals',
  6: 'Third Place Playoff',
  7: 'Final',
}

export default function MatchesPage() {
  const [snapshot, setSnapshot] = useState<TournamentSnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedStage, setSelectedStage] = useState<number | 'all'>('all')
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadPredictions()
  }, [])

  const loadPredictions = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchLatestPredictions()
      setSnapshot(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch predictions')
    } finally {
      setLoading(false)
    }
  }

  // Filter and sort matches
  const filteredMatches = useMemo(() => {
    if (!snapshot) return []

    // Use matches array which includes ALL 104 matches (group + knockout)
    let matches = snapshot.matches || []

    // Filter by stage
    if (selectedStage !== 'all') {
      matches = matches.filter((m) => m.stageId === selectedStage)
    }

    // Filter by search query (team names)
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      matches = matches.filter(
        (m) =>
          m.homeTeamName?.toLowerCase().includes(query) ||
          m.awayTeamName?.toLowerCase().includes(query) ||
          m.label.toLowerCase().includes(query)
      )
    }

    // Sort by kickoff time (ascending)
    matches.sort((a, b) => {
      const dateA = new Date(a.kickoff).getTime()
      const dateB = new Date(b.kickoff).getTime()
      return dateA - dateB
    })

    return matches
  }, [snapshot, selectedStage, searchQuery])

  // Group matches by date
  const matchesByDate = useMemo(() => {
    const groups: Record<string, Match[]> = {}
    filteredMatches.forEach((match) => {
      const date = new Date(match.kickoff).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
      if (!groups[date]) {
        groups[date] = []
      }
      groups[date].push(match)
    })
    return groups
  }, [filteredMatches])

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <div>
              <h1 className="text-3xl font-black tracking-tight text-slate-900">Match Schedule</h1>
              <p className="text-sm text-slate-600 mt-1">All 104 matches with AI predictions</p>
            </div>
            <a
              href="/"
              className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-colors"
            >
              ← Back to Home
            </a>
          </div>

          {/* Filters */}
          {snapshot && !loading && (
            <div className="mt-6 space-y-4">
              {/* Stage Filter */}
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedStage('all')}
                  className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
                    selectedStage === 'all'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  All Stages
                </button>
                {Object.entries(STAGE_NAMES).map(([id, name]) => (
                  <button
                    key={id}
                    onClick={() => setSelectedStage(Number(id))}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
                      selectedStage === Number(id)
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {name}
                  </button>
                ))}
              </div>

              {/* Search */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search by team name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-3 pl-12 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <svg
                  className="absolute left-4 top-3.5 h-5 w-5 text-slate-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-4 top-3.5 text-slate-400 hover:text-slate-600"
                  >
                    ✕
                  </button>
                )}
              </div>

              {/* Results Count */}
              <div className="text-sm text-slate-600">
                Showing <span className="font-semibold">{filteredMatches.length}</span> matches
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-slate-600 font-medium">Loading matches...</p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <div className="text-red-600 font-semibold mb-2">Error loading matches</div>
            <p className="text-red-500 text-sm mb-4">{error}</p>
            <button
              onClick={loadPredictions}
              className="px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Matches by Date */}
        {snapshot && !loading && (
          <div className="space-y-12">
            {Object.keys(matchesByDate).length === 0 ? (
              <div className="bg-white rounded-2xl p-12 text-center border border-slate-200">
                <p className="text-slate-500 font-medium">No matches found matching your filters</p>
              </div>
            ) : (
              Object.entries(matchesByDate).map(([date, matches]) => (
                <div key={date}>
                  {/* Date Header */}
                  <div className="sticky top-24 z-40 mb-6 flex justify-center">
                    <div className="bg-slate-900 text-white px-8 py-3 rounded-full shadow-lg border border-slate-700">
                      <span className="text-sm font-black uppercase tracking-wider">{date}</span>
                    </div>
                  </div>

                  {/* Matches Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {matches.map((match) => (
                      <MatchCard key={match.id} match={match} prediction={match.prediction} />
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-20 border-t border-slate-200 bg-white py-12 text-center">
        <p className="text-slate-500 text-sm">
          VM KULA 2026 - AI-powered World Cup predictions
        </p>
      </footer>
    </div>
  )
}
