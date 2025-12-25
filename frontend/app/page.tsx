/**
 * Design: VM KULA 2026 Homepage
 * 
 * Aesthetic Direction: Modern Sports Stadium - Dynamic pitch-to-podium energy
 * Typography: Montserrat ExtraBold for headers, Inter for body (championship aesthetic)
 * Color Palette: Emerald Green (#10B981), Electric Yellow (#FBBF24), Midnight Blue (#0F172A)
 * Key Features: Mobile-first responsive, staggered animations, touch-optimized
 * 
 * Accessibility: WCAG AA compliant
 * Responsive: Mobile-first (320px → 1440px+)
 */

'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { fetchLatestPredictions } from '../lib/firestore'
import type { TournamentSnapshot } from '../lib/types'
import GroupCard from '../components/GroupCard'
import MatchCard from '../components/MatchCard'
import BracketView from '../components/BracketView'
import LoadingSpinner from '../components/LoadingSpinner'
import ConnectionStatus from '../components/ConnectionStatus'

type Tab = 'groups' | 'matches' | 'bracket'

export default function Home() {
  const t = useTranslations('home')
  const tNav = useTranslations('navigation')
  const tCommon = useTranslations('common')
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
      // Trigger backend tournament update (fast - no AI predictions)
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      await fetch(`${backendUrl}/api/update-tournament`, { method: 'POST' })
      
      // Wait 1 second for backend to complete
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Reload tournament data
      await loadPredictions()
    } catch (err) {
      setError('Failed to refresh tournament data')
    } finally {
      setRefreshing(false)
    }
  }

  // Format timestamp in Norwegian
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString('nb-NO', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50">
      {/* Connection Status Indicator */}
      <ConnectionStatus />

      {/* Animated Background Pattern - Stadium Lights Effect */}
      <div className="fixed inset-0 opacity-5 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-400 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-yellow-300 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
      </div>

      {/* Header - Mobile First */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-white/95 border-b border-emerald-200 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Logo & Title - Stacked on Mobile */}
          <div className="flex flex-col items-center py-4 sm:py-6 gap-3 sm:gap-4">
            <div className="flex items-center gap-3 sm:gap-4">
              {/* Animated Soccer Ball Icon */}
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-br from-emerald-400 to-emerald-500 rounded-2xl blur-md opacity-75 group-hover:opacity-100 transition-opacity"></div>
                <div className="relative bg-gradient-to-br from-emerald-500 to-emerald-600 p-2.5 sm:p-3 rounded-2xl shadow-xl transform group-hover:scale-110 transition-transform">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-6 w-6 sm:h-8 sm:w-8 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2.5}
                      d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
              </div>
              <div className="text-center sm:text-left">
                <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black tracking-tight bg-gradient-to-r from-emerald-600 via-emerald-700 to-emerald-600 bg-clip-text text-transparent">
                  {tCommon('appName')}
                </h1>
                <p className="text-[10px] sm:text-xs text-emerald-600 font-bold uppercase tracking-widest flex items-center justify-center sm:justify-start gap-1.5">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
                  {tCommon('aiPredictionsEnabled')}
                </p>
              </div>
            </div>

            {/* Tab Navigation - Mobile Optimized (Touch Friendly) */}
            <nav className="w-full sm:w-auto flex bg-slate-100 p-1 rounded-2xl border border-slate-200 shadow-md">
              {(['groups', 'matches', 'bracket'] as Tab[]).map((tab, index) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`flex-1 sm:flex-none px-4 sm:px-6 py-3 sm:py-2.5 rounded-xl text-xs sm:text-[11px] font-bold uppercase tracking-wider transition-all duration-300 min-h-[44px] sm:min-h-0 ${
                    activeTab === tab
                      ? 'bg-gradient-to-br from-emerald-500 to-emerald-600 text-white shadow-lg shadow-emerald-500/30'
                      : 'text-slate-600 hover:text-emerald-600 hover:bg-white'
                  }`}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  {tab === 'groups' ? `⚽ ${tNav('groups')}` : tab === 'matches' ? `📊 ${tNav('matches')}` : `🏆 ${tNav('bracket')}`}
                </button>
              ))}
            </nav>
          </div>

          {/* Last Updated & Refresh - Mobile Optimized */}
          {snapshot && (
            <div className="flex flex-col sm:flex-row justify-between items-center pb-3 sm:pb-4 gap-3 text-xs sm:text-sm">
              <div className="text-slate-700 text-center sm:text-left">
                ⏱️ {tCommon('lastUpdated')}: <span className="font-bold text-emerald-700">{formatTimestamp(snapshot.updatedAt)}</span>
              </div>
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="w-full sm:w-auto px-6 py-3 sm:py-2 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white rounded-xl font-bold hover:from-emerald-600 hover:to-emerald-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-emerald-500/30 hover:scale-105 transform min-h-[44px] sm:min-h-0"
              >
                {refreshing ? `🔄 ${tCommon('refreshing')}...` : `🔄 ${t('refreshTournament')}`}
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-12">
        {/* Loading State - Using LoadingSpinner Component */}
        {loading && (
          <LoadingSpinner message={t('loadingPredictions')} />
        )}

        {/* Error State - Enhanced with Better UX */}
        {error && !loading && (
          <div className="bg-red-50 border-2 border-red-300 rounded-2xl p-6 sm:p-8 text-center shadow-xl">
            <div className="text-6xl mb-4">⚠️</div>
            <div className="text-red-800 font-bold text-lg sm:text-xl mb-2">{t('errorLoading')}</div>
            <p className="text-red-700 text-sm sm:text-base mb-6">{error}</p>
            <button
              onClick={loadPredictions}
              className="px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-xl font-bold hover:from-red-600 hover:to-red-700 transition-all duration-300 shadow-lg hover:scale-105 transform min-h-[44px]"
            >
              {tCommon('tryAgain')}
            </button>
          </div>
        )}

        {/* Content */}
        {snapshot && !loading && (
          <>
            {/* Groups Tab */}
            {activeTab === 'groups' && (
              <div className="space-y-6 sm:space-y-8 animate-fadeIn">
                {/* AI Summary - Enhanced Visual Design */}
                <div className="relative overflow-hidden bg-white rounded-2xl sm:rounded-3xl p-6 sm:p-8 border-2 border-emerald-200 shadow-xl">
                  {/* Decorative Elements */}
                  <div className="absolute top-0 right-0 w-40 h-40 bg-emerald-100 rounded-full blur-3xl"></div>
                  <div className="absolute bottom-0 left-0 w-40 h-40 bg-yellow-100 rounded-full blur-3xl"></div>
                  
                  <div className="relative z-10">
                    <div className="flex items-center gap-3 mb-4">
                      <span className="text-3xl sm:text-4xl">🏆</span>
                      <h2 className="text-xl sm:text-2xl lg:text-3xl font-black text-emerald-800">
                        {t('tournamentOverview')}
                      </h2>
                    </div>
                    <p className="text-slate-700 leading-relaxed text-sm sm:text-base mb-6 sm:mb-8">{snapshot.aiSummary}</p>
                    
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                      {/* Favorites */}
                      <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 p-4 sm:p-6 rounded-xl sm:rounded-2xl border-2 border-emerald-300 hover:border-emerald-400 transition-all duration-300 hover:scale-105 hover:shadow-lg">
                        <h4 className="text-xs sm:text-sm font-bold text-emerald-800 uppercase mb-3 tracking-wider flex items-center gap-2">
                          <span>⭐</span> {t('favorites')}
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {snapshot.favorites.map((team, index) => (
                            <span
                              key={team}
                              className="px-3 sm:px-4 py-2 bg-white text-emerald-700 rounded-lg sm:rounded-xl font-bold text-xs sm:text-sm border border-emerald-300 hover:bg-emerald-50 transition-colors shadow-sm"
                              style={{ animationDelay: `${index * 100}ms` }}
                            >
                              {team}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Dark Horses */}
                      <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 p-4 sm:p-6 rounded-xl sm:rounded-2xl border-2 border-yellow-300 hover:border-yellow-400 transition-all duration-300 hover:scale-105 hover:shadow-lg">
                        <h4 className="text-xs sm:text-sm font-bold text-yellow-800 uppercase mb-3 tracking-wider flex items-center gap-2">
                          <span>🐴</span> {t('darkHorses')}
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {snapshot.darkHorses.map((team, index) => (
                            <span
                              key={team}
                              className="px-3 sm:px-4 py-2 bg-white text-yellow-700 rounded-lg sm:rounded-xl font-bold text-xs sm:text-sm border border-yellow-300 hover:bg-yellow-50 transition-colors shadow-sm"
                              style={{ animationDelay: `${index * 100}ms` }}
                            >
                              {team}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Group Standings - Responsive Grid */}
                <div>
                  <h3 className="text-lg sm:text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                    <span>⚽</span> {t('groupStandings')}
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                    {Object.entries(snapshot.groups)
                      .sort(([a], [b]) => a.localeCompare(b))
                      .map(([letter, group], index) => (
                        <div key={letter} className="animate-slideIn" style={{ animationDelay: `${index * 50}ms` }}>
                          <GroupCard group={group} />
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            )}

            {/* Matches Tab */}
            {activeTab === 'matches' && (
              <div className="space-y-6 animate-fadeIn">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                  <h2 className="text-xl sm:text-2xl lg:text-3xl font-black text-emerald-800 flex items-center gap-2">
                    <span>📊</span> {t('groupStageMatches')}
                  </h2>
                  <div className="text-xs sm:text-sm text-emerald-700 bg-emerald-50 px-4 py-2 rounded-full border-2 border-emerald-200">
                    <span className="font-bold text-emerald-800">{snapshot.matches.length}</span> {t('matchesLoaded')}
                  </div>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                  {snapshot.matches.map((match, index) => (
                    <div key={match.id} className="animate-slideIn" style={{ animationDelay: `${index * 30}ms` }}>
                      <MatchCard match={match} prediction={match.prediction} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Bracket Tab */}
            {activeTab === 'bracket' && (
              <div className="space-y-6 sm:space-y-8 animate-fadeIn">
                <div className="text-center">
                  <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black text-emerald-800 mb-2 flex items-center justify-center gap-3">
                    <span>🏆</span> {tNav('bracket')}
                  </h2>
                  <p className="text-slate-700 text-sm sm:text-base">{t('tournamentProgression')}</p>
                </div>
                <BracketView bracket={snapshot.bracket} />
                
                {/* AI Summary Below Bracket */}
                <div className="relative overflow-hidden bg-white rounded-2xl sm:rounded-3xl p-6 sm:p-8 border-2 border-emerald-200 shadow-xl">
                  {/* Decorative Elements */}
                  <div className="absolute top-0 right-0 w-40 h-40 bg-emerald-100 rounded-full blur-3xl"></div>
                  <div className="absolute bottom-0 left-0 w-40 h-40 bg-yellow-100 rounded-full blur-3xl"></div>
                  
                  <div className="relative z-10">
                    <h3 className="text-lg sm:text-xl lg:text-2xl font-black text-emerald-800 mb-4 flex items-center gap-2">
                      <span>🤖</span> {t('aiTournamentAnalysis')}
                    </h3>
                    <p className="text-slate-700 leading-relaxed text-sm sm:text-base mb-6">{snapshot.aiSummary}</p>
                    
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                      <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 p-4 sm:p-6 rounded-xl border-2 border-emerald-300">
                        <h4 className="text-xs sm:text-sm font-bold text-emerald-800 uppercase mb-3 tracking-wider flex items-center gap-2">
                          <span>⭐</span> {t('favoritesToWin')}
                        </h4>
                        <ul className="space-y-2">
                          {snapshot.favorites.map((team) => (
                            <li key={team} className="text-slate-800 font-semibold text-sm sm:text-base flex items-center gap-2">
                              <span className="text-emerald-600">•</span> {team}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 p-4 sm:p-6 rounded-xl border-2 border-yellow-300">
                        <h4 className="text-xs sm:text-sm font-bold text-yellow-800 uppercase mb-3 tracking-wider flex items-center gap-2">
                          <span>🐴</span> {t('darkHorses')}
                        </h4>
                        <ul className="space-y-2">
                          {snapshot.darkHorses.map((team) => (
                            <li key={team} className="text-slate-800 font-semibold text-sm sm:text-base flex items-center gap-2">
                              <span className="text-yellow-600">•</span> {team}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Footer - Mobile Optimized */}
      <footer className="relative mt-12 sm:mt-20 border-t-2 border-emerald-200 bg-gradient-to-br from-emerald-50 to-white py-8 sm:py-12 text-center overflow-hidden">
        {/* Decorative Background */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-64 bg-emerald-200 rounded-full blur-3xl"></div>
        </div>
        
        <div className="relative z-10 max-w-md mx-auto px-4">
          <div className="flex items-center justify-center gap-3 mb-3">
            <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 p-2 rounded-xl shadow-md">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2.5}
                  d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <p className="text-xl sm:text-2xl font-black text-emerald-800">
              {tCommon('appName')}
            </p>
          </div>
          <p className="text-slate-700 text-xs sm:text-sm mb-4 sm:mb-6">
            {t('footerTagline')}
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-2 text-[10px] sm:text-xs text-slate-600 uppercase tracking-widest">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
              {t('unofficialApp')}
            </span>
            <span className="hidden sm:inline text-slate-400">•</span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
              {t('madeWithLove')}
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}
