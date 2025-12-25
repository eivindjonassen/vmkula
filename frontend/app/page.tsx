/**
 * Home page with tab navigation for World Cup 2026 predictions.
 * 
 * Features:
 * - Tab navigation: Groups | Matches | Bracket
 * - Fetch predictions on page load
 * - Display last updated timestamp
 * - Loading and error states
 * - Refresh predictions button
 */

'use client'

import { useState, useEffect } from 'react'
import { fetchLatestPredictions } from '../lib/firestore'
import type { TournamentSnapshot } from '../lib/types'
import GroupCard from '../components/GroupCard'
import MatchCard from '../components/MatchCard'
import BracketView from '../components/BracketView'

type Tab = 'groups' | 'matches' | 'bracket'

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>('groups')
  const [snapshot, setSnapshot] = useState<TournamentSnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  // Fetch predictions on mount
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

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      // Trigger backend update
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      await fetch(`${backendUrl}/api/update-predictions`, { method: 'POST' })
      
      // Wait 2 seconds for backend to complete
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // Reload predictions
      await loadPredictions()
    } catch (err) {
      setError('Failed to refresh predictions')
    } finally {
      setRefreshing(false)
    }
  }

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-center py-6 gap-4">
            {/* Logo */}
            <div className="flex items-center gap-4">
              <div className="bg-blue-600 p-3 rounded-2xl text-white shadow-lg">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-8 w-8"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-black tracking-tight text-slate-900">
                  VM KULA 2026
                </h1>
                <p className="text-xs text-blue-600 font-bold uppercase tracking-wider">
                  AI Predictions Enabled
                </p>
              </div>
            </div>

            {/* Tab Navigation */}
            <nav className="flex bg-slate-100 p-1.5 rounded-2xl border border-slate-200">
              {(['groups', 'matches', 'bracket'] as Tab[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition-all ${
                    activeTab === tab
                      ? 'bg-white text-blue-600 shadow-md'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  {tab === 'groups' ? 'Groups' : tab === 'matches' ? 'Matches' : 'Bracket'}
                </button>
              ))}
            </nav>
          </div>

          {/* Last Updated & Refresh */}
          {snapshot && (
            <div className="flex flex-col sm:flex-row justify-between items-center pb-4 gap-4 text-sm">
              <div className="text-slate-600">
                Last updated: <span className="font-semibold">{formatTimestamp(snapshot.updatedAt)}</span>
              </div>
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {refreshing ? 'Refreshing...' : 'Refresh Predictions'}
              </button>
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
            <p className="text-slate-600 font-medium">Loading predictions...</p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <div className="text-red-600 font-semibold mb-2">Error loading predictions</div>
            <p className="text-red-500 text-sm mb-4">{error}</p>
            <button
              onClick={loadPredictions}
              className="px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Content */}
        {snapshot && !loading && (
          <>
            {/* Groups Tab */}
            {activeTab === 'groups' && (
              <div className="space-y-8">
                {/* AI Summary */}
                <div className="bg-gradient-to-br from-white to-slate-50 rounded-3xl p-8 border border-slate-200 shadow-lg">
                  <h2 className="text-2xl font-bold mb-4 text-slate-900">Tournament Overview</h2>
                  <p className="text-slate-700 leading-relaxed mb-6">{snapshot.aiSummary}</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Favorites */}
                    <div className="bg-white p-6 rounded-2xl border border-blue-100">
                      <h4 className="text-xs font-bold text-blue-600 uppercase mb-3 tracking-wider">
                        Favorites
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {snapshot.favorites.map((team) => (
                          <span
                            key={team}
                            className="px-4 py-2 bg-blue-50 text-blue-700 rounded-xl font-semibold text-sm border border-blue-100"
                          >
                            {team}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Dark Horses */}
                    <div className="bg-white p-6 rounded-2xl border border-amber-100">
                      <h4 className="text-xs font-bold text-amber-600 uppercase mb-3 tracking-wider">
                        Dark Horses
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {snapshot.darkHorses.map((team) => (
                          <span
                            key={team}
                            className="px-4 py-2 bg-amber-50 text-amber-700 rounded-xl font-semibold text-sm border border-amber-100"
                          >
                            {team}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Group Standings */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {Object.entries(snapshot.groups).map(([letter, group]) => (
                    <GroupCard key={letter} group={group} />
                  ))}
                </div>
              </div>
            )}

            {/* Matches Tab */}
            {activeTab === 'matches' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-slate-900">All Matches</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {snapshot.bracket.map((match) => (
                    <MatchCard key={match.id} match={match} prediction={match.prediction} />
                  ))}
                </div>
              </div>
            )}

            {/* Bracket Tab */}
            {activeTab === 'bracket' && (
              <div className="space-y-8">
                <div className="text-center">
                  <h2 className="text-3xl font-bold text-slate-900 mb-2">Knockout Bracket</h2>
                  <p className="text-slate-600">Tournament progression from Round of 32 to Final</p>
                </div>
                <BracketView bracket={snapshot.bracket} />
                
                {/* AI Summary Below Bracket */}
                <div className="bg-gradient-to-br from-white to-slate-50 rounded-3xl p-8 border border-slate-200 shadow-lg">
                  <h3 className="text-xl font-bold mb-4 text-slate-900">AI Tournament Analysis</h3>
                  <p className="text-slate-700 leading-relaxed mb-6">{snapshot.aiSummary}</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-sm font-bold text-slate-600 mb-2">Favorites to Win</h4>
                      <ul className="space-y-1">
                        {snapshot.favorites.map((team) => (
                          <li key={team} className="text-slate-700 font-medium">• {team}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-600 mb-2">Dark Horses</h4>
                      <ul className="space-y-1">
                        {snapshot.darkHorses.map((team) => (
                          <li key={team} className="text-slate-700 font-medium">• {team}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-20 border-t border-slate-200 bg-white py-12 text-center">
        <div className="max-w-md mx-auto px-4">
          <p className="text-slate-900 font-bold text-2xl mb-2">VM KULA 2026</p>
          <p className="text-slate-500 text-sm mb-6">
            AI-powered World Cup predictions using Gemini AI
          </p>
          <p className="text-xs text-slate-400 uppercase tracking-wider">
            Unofficial Companion App
          </p>
        </div>
      </footer>
    </div>
  )
}
