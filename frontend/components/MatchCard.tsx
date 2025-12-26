/**
 * MatchCard component - Display match prediction card with Norwegian translations.
 * 
 * Features:
 * - Display match info: teams, venue, kickoff time
 * - Show AI prediction with win probability bar
 * - Display predicted score
 * - Show reasoning (expandable)
 * - Color-coded confidence levels
 * - Handle TBD matchups gracefully
 */

'use client'

import { useState, useEffect, useRef } from 'react'
import { useTranslations } from 'next-intl'
import type { Match, MatchPrediction } from '../lib/types'
import { translateBracketLabel, translateTeamName, isBracketLabel } from '../lib/translationUtils'

interface MatchCardProps {
  match: Match
  prediction?: MatchPrediction
}

export default function MatchCard({ match, prediction }: MatchCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const t = useTranslations('matchCard')
  const tCommon = useTranslations('common')
  const tBracket = useTranslations('bracketView')

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false)
      }
    }

    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showMenu])

  // Handle TBD matchups - use label if teams are not determined yet
  const isTBD = !match.homeTeamId || !match.awayTeamId || match.homeTeamName === 'TBD' || match.awayTeamName === 'TBD'
  
  // Get raw team names/labels
  const rawHomeTeam = (match.homeTeamName && match.homeTeamName !== 'TBD') 
    ? match.homeTeamName 
    : match.label.split(' vs ')[0]
  const rawAwayTeam = (match.awayTeamName && match.awayTeamName !== 'TBD') 
    ? match.awayTeamName 
    : match.label.split(' vs ')[1] || 'TBD'
  
  // Translate to Norwegian
  const homeTeam = isBracketLabel(rawHomeTeam) 
    ? translateBracketLabel(rawHomeTeam, (key) => tBracket(key))
    : translateTeamName(rawHomeTeam)
  const awayTeam = isBracketLabel(rawAwayTeam) 
    ? translateBracketLabel(rawAwayTeam, (key) => tBracket(key))
    : translateTeamName(rawAwayTeam)

  // Format kickoff time in Norwegian
  const kickoffDate = new Date(match.kickoff)
  const formattedDate = kickoffDate.toLocaleDateString('nb-NO', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
  const formattedTime = kickoffDate.toLocaleTimeString('nb-NO', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })

  // Confidence color coding (WCAG AA compliant contrast ratios)
  const getConfidenceColor = (confidence?: string) => {
    switch (confidence?.toLowerCase()) {
      case 'high':
        return 'bg-emerald-50 text-emerald-900 border-emerald-400'
      case 'medium':
        return 'bg-blue-50 text-blue-900 border-blue-400'
      case 'low':
        return 'bg-slate-50 text-slate-900 border-slate-400'
      default:
        return 'bg-gray-50 text-gray-900 border-gray-400'
    }
  }
  
  const getConfidenceLabel = (confidence?: string) => {
    switch (confidence?.toLowerCase()) {
      case 'high':
        return t('confidenceHigh')
      case 'medium':
        return t('confidenceMedium')
      case 'low':
        return t('confidenceLow')
      default:
        return confidence?.toUpperCase()
    }
  }
  
  const getConfidenceStars = (confidence?: string) => {
    switch (confidence?.toLowerCase()) {
      case 'high':
        return '⭐⭐⭐'
      case 'medium':
        return '⭐⭐'
      case 'low':
        return '⭐'
      default:
        return ''
    }
  }

  // Truncate reasoning
  const [showFullReasoning, setShowFullReasoning] = useState(false)
  const reasoning = prediction?.reasoning || t('predictionPending')
  const truncatedReasoning = reasoning.length > 120 
    ? reasoning.substring(0, 120) + '...' 
    : reasoning
  const shouldShowReadMore = reasoning.length > 120

  return (
    <div className="bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden hover:shadow-lg transition-all duration-300">
      {/* Compact Mobile-First View */}
      <div 
        className="p-4 cursor-pointer hover:bg-slate-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            setIsExpanded(!isExpanded)
          }
        }}
        aria-expanded={isExpanded}
        aria-label={`Kamp: ${homeTeam} mot ${awayTeam}, ${formattedTime}`}
      >
        <div className="flex flex-col gap-3">
          {/* Match Number, Date & Time */}
          <div className="flex items-center gap-3 flex-wrap">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-slate-100 rounded-lg">
              <span className="text-xs font-bold text-slate-500 uppercase">Kamp</span>
              <span className="text-sm font-black text-slate-900">#{match.matchNumber}</span>
            </div>
            <div className="text-sm text-slate-600 font-medium">{formattedDate}</div>
            <div className="text-2xl font-bold text-slate-900">{formattedTime}</div>
            {/* API-Football Data Badge */}
            {match.hasRealData && (
              <span 
                className="inline-flex items-center gap-1 px-2 py-1 text-xs font-bold bg-green-100 text-green-800 border border-green-300 rounded-full"
                title="Data hentet fra API-Football"
              >
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span>Live</span>
              </span>
            )}
            {/* Mock Data Badge */}
            {match.hasRealData === false && (
              <span 
                className="inline-flex items-center gap-1 px-2 py-1 text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300 rounded-full"
                title="Testdata - ikke fra API-Football"
              >
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <span>Test</span>
              </span>
            )}
          </div>

          {/* Teams & Menu */}
          <div className="flex items-center gap-2">
            <div className="flex-1 min-w-0 space-y-1">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <span className="text-2xl flex-shrink-0" aria-hidden="true">{match.homeTeamFlag || '🏴'}</span>
                  <span className="font-semibold text-slate-900 truncate">{homeTeam}</span>
                </div>
                {prediction && (
                  <span className="text-lg font-bold text-emerald-600 flex-shrink-0 min-w-[24px] text-right">
                    {prediction.predictedHomeScore}
                  </span>
                )}
              </div>
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <span className="text-2xl flex-shrink-0" aria-hidden="true">{match.awayTeamFlag || '🏴'}</span>
                  <span className="font-semibold text-slate-900 truncate">{awayTeam}</span>
                </div>
                {prediction && (
                  <span className="text-lg font-bold text-emerald-600 flex-shrink-0 min-w-[24px] text-right">
                    {prediction.predictedAwayScore}
                  </span>
                )}
              </div>
            </div>

            {/* Three-dot Menu */}
            <div className="flex-shrink-0 relative" ref={menuRef}>
            <button
              onClick={(e) => {
                e.stopPropagation()
                setShowMenu(!showMenu)
              }}
              className="p-3 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-slate-100 rounded-full transition-colors focus:ring-4 focus:ring-emerald-300 focus:outline-none"
              aria-label="Kampvalg meny"
              aria-expanded={showMenu}
              aria-haspopup="true"
            >
              <svg className="w-5 h-5 text-slate-600" fill="currentColor" viewBox="0 0 16 16">
                <circle cx="2" cy="8" r="2"/>
                <circle cx="8" cy="8" r="2"/>
                <circle cx="14" cy="8" r="2"/>
              </svg>
            </button>
            
            {/* Dropdown Menu */}
            {showMenu && (
              <div 
                className="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl shadow-xl border border-slate-200 z-50 overflow-hidden"
                role="menu"
                aria-orientation="vertical"
              >
                <button
                  className="w-full px-4 py-3 min-h-[44px] text-left text-sm hover:bg-slate-50 transition-colors flex items-center gap-2 focus:ring-2 focus:ring-inset focus:ring-emerald-300 focus:outline-none"
                  onClick={(e) => {
                    e.stopPropagation()
                    setShowMenu(false)
                    setIsExpanded(true)
                  }}
                  role="menuitem"
                >
                  <span aria-hidden="true">📊</span>
                  <span>Vis detaljer</span>
                </button>
                <button
                  className="w-full px-4 py-3 min-h-[44px] text-left text-sm hover:bg-slate-50 transition-colors flex items-center gap-2 focus:ring-2 focus:ring-inset focus:ring-emerald-300 focus:outline-none"
                  onClick={(e) => {
                    e.stopPropagation()
                    setShowMenu(false)
                    // Add share functionality
                  }}
                  role="menuitem"
                >
                  <span aria-hidden="true">📤</span>
                  <span>Del kamp</span>
                </button>
              </div>
            )}
            </div>
          </div>

          {/* Venue Info */}
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <svg className="w-4 h-4 text-red-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
            </svg>
            <span className="font-medium">{match.venue}</span>
          </div>
        </div>
      </div>

      {/* Expanded Detail View - Only shown when clicked */}
      {isExpanded && prediction && !isTBD && (
        <div className="border-t border-slate-200 px-6 py-6 bg-gradient-to-br from-emerald-50 to-white">
          {/* Close Button */}
          <div className="flex justify-end mb-4">
            <button
              onClick={(e) => {
                e.stopPropagation()
                setIsExpanded(false)
              }}
              className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-emerald-100 rounded-full transition-colors focus:ring-4 focus:ring-emerald-300 focus:outline-none"
              aria-label="Lukk kampdetaljer"
            >
              <svg className="w-5 h-5 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {/* Winner */}
          <div className="mb-6">
            <div className="text-xs font-bold text-emerald-700 uppercase tracking-wider mb-2 flex items-center gap-2">
              <span>🏆</span>
              <span>{t('predictedWinner')}</span>
            </div>
            <div className="font-black text-2xl text-slate-900">
              {prediction.winner}
            </div>
          </div>

          {/* Win Probability Bar */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-3">
              <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider flex items-center gap-2">
                <span>📊</span>
                <span>{t('winProbability')}</span>
              </span>
              <span className="text-sm font-black text-emerald-600">
                {(prediction.winProbability * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-4 overflow-hidden shadow-inner">
              <div
                className="bg-gradient-to-r from-emerald-500 to-emerald-600 h-4 rounded-full transition-all duration-500 shadow-md"
                style={{ width: `${prediction.winProbability * 100}%` }}
              />
            </div>
          </div>

          {/* Confidence Badge */}
          {prediction.confidence && (
            <div className="mb-6">
              <span
                className={`inline-flex items-center gap-2 px-4 py-2 text-sm font-bold rounded-xl border-2 ${getConfidenceColor(
                  prediction.confidence
                )}`}
              >
                <span>{getConfidenceStars(prediction.confidence)}</span>
                <span>{t('confidence')}: {getConfidenceLabel(prediction.confidence)}</span>
              </span>
            </div>
          )}

          {/* Reasoning */}
          <div>
            <div className="text-xs font-bold text-emerald-700 uppercase tracking-wider mb-3 flex items-center gap-2">
              <span>🤖</span>
              <span>{t('aiAnalysis')}</span>
            </div>
            <div className="text-sm text-slate-700 leading-relaxed">
              {showFullReasoning ? reasoning : truncatedReasoning}
            </div>
            {shouldShowReadMore && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setShowFullReasoning(!showFullReasoning)
                }}
                className="mt-4 w-full px-4 py-3 bg-white hover:bg-emerald-100 text-emerald-700 font-bold text-sm rounded-xl border-2 border-emerald-200 transition-all duration-300 min-h-[44px] flex items-center justify-center gap-2 focus:ring-4 focus:ring-emerald-300 focus:outline-none"
                aria-expanded={showFullReasoning}
                aria-label={showFullReasoning ? 'Skjul full AI-analyse' : 'Vis full AI-analyse'}
              >
                {showFullReasoning ? (
                  <>
                    <span aria-hidden="true">▲</span>
                    <span>{tCommon('showLess')}</span>
                  </>
                ) : (
                  <>
                    <span aria-hidden="true">▼</span>
                    <span>{tCommon('readMore')}</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      )}

      {/* TBD Notice - Always visible if TBD */}
      {isExpanded && isTBD && (
        <div className="border-t border-yellow-200 px-6 py-4 bg-gradient-to-br from-yellow-50 to-white">
          <div className="flex items-center gap-3 text-yellow-800">
            <svg
              className="w-6 h-6 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
            <span className="text-sm font-bold">
              {t('tbdNotice')}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
