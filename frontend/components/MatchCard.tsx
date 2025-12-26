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

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import type { Match, MatchPrediction } from '../lib/types'
import { translateBracketLabel, translateTeamName, isBracketLabel } from '../lib/translationUtils'

interface MatchCardProps {
  match: Match
  prediction?: MatchPrediction
}

export default function MatchCard({ match, prediction }: MatchCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const t = useTranslations('matchCard')
  const tCommon = useTranslations('common')
  const tBracket = useTranslations('bracketView')

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
    month: 'short',
    year: 'numeric',
  })
  const formattedTime = kickoffDate.toLocaleTimeString('nb-NO', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })

  // Confidence color coding (updated to match design system)
  const getConfidenceColor = (confidence?: string) => {
    switch (confidence?.toLowerCase()) {
      case 'high':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300'
      case 'medium':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'low':
        return 'bg-slate-100 text-slate-700 border-slate-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
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
  const reasoning = prediction?.reasoning || t('predictionPending')
  const truncatedReasoning = reasoning.length > 120 
    ? reasoning.substring(0, 120) + '...' 
    : reasoning
  const shouldShowReadMore = reasoning.length > 120

  return (
    <div className="bg-white rounded-2xl shadow-lg border-2 border-emerald-200 overflow-hidden hover:shadow-xl transition-all duration-300">
      {/* Header: Match Info */}
      <div className="bg-gradient-to-r from-emerald-600 to-emerald-700 px-6 py-4 shadow-lg">
        <div className="flex justify-between items-start text-white">
          <div>
            <div className="text-xs font-bold opacity-90 uppercase tracking-wider">{t('match')} #{match.matchNumber}</div>
            <div className="text-lg font-bold mt-1 flex items-center gap-2">
              <span>📍</span>
              <span>{match.venue}</span>
            </div>
          </div>
          <div className="text-right text-sm opacity-90">
            <div className="font-semibold">{formattedDate}</div>
            <div className="font-bold">{formattedTime}</div>
          </div>
        </div>
      </div>

      {/* Teams */}
      <div className="px-6 py-4">
        <div className="grid grid-cols-3 gap-4 items-center">
          {/* Home Team */}
          <div className="text-center">
            <div className="font-bold text-lg text-gray-900">{homeTeam}</div>
            {prediction && (
              <div className="text-3xl font-black text-emerald-600 mt-2">
                {prediction.predictedHomeScore}
              </div>
            )}
          </div>

          {/* VS */}
          <div className="text-center text-slate-600 font-bold text-sm">
            {t('vs')}
          </div>

          {/* Away Team */}
          <div className="text-center">
            <div className="font-bold text-lg text-gray-900">{awayTeam}</div>
            {prediction && (
              <div className="text-3xl font-black text-emerald-600 mt-2">
                {prediction.predictedAwayScore}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Prediction */}
      {prediction && !isTBD && (
        <div className="border-t-2 border-emerald-200 px-6 py-6 bg-gradient-to-br from-emerald-50 to-white">
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
              {isExpanded ? reasoning : truncatedReasoning}
            </div>
            {shouldShowReadMore && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="mt-4 w-full px-4 py-3 bg-white hover:bg-emerald-100 text-emerald-700 font-bold text-sm rounded-xl border-2 border-emerald-200 transition-all duration-300 min-h-[44px] flex items-center justify-center gap-2 focus:ring-4 focus:ring-emerald-300 focus:outline-none"
                aria-expanded={isExpanded}
                aria-label={isExpanded ? 'Skjul AI-analyse' : 'Vis full AI-analyse'}
              >
                {isExpanded ? (
                  <>
                    <span>▲</span>
                    <span>{tCommon('showLess')}</span>
                  </>
                ) : (
                  <>
                    <span>▼</span>
                    <span>{tCommon('readMore')}</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      )}

      {/* TBD Notice */}
      {isTBD && (
        <div className="border-t-2 border-yellow-200 px-6 py-4 bg-gradient-to-br from-yellow-50 to-white">
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
