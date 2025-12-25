/**
 * MatchCard component - Display match prediction card.
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
import type { Match, MatchPrediction } from '../lib/types'

interface MatchCardProps {
  match: Match
  prediction?: MatchPrediction
}

export default function MatchCard({ match, prediction }: MatchCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  // Handle TBD matchups
  const isTBD = !match.homeTeamId || !match.awayTeamId
  const homeTeam = match.homeTeamName || match.label.split(' vs ')[0]
  const awayTeam = match.awayTeamName || match.label.split(' vs ')[1] || 'TBD'

  // Format kickoff time
  const kickoffDate = new Date(match.kickoff)
  const formattedDate = kickoffDate.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
  const formattedTime = kickoffDate.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })

  // Confidence color coding
  const getConfidenceColor = (confidence?: string) => {
    switch (confidence?.toLowerCase()) {
      case 'high':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'low':
        return 'bg-red-100 text-red-800 border-red-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  // Truncate reasoning
  const reasoning = prediction?.reasoning || 'Prediction pending...'
  const truncatedReasoning = reasoning.length > 120 
    ? reasoning.substring(0, 120) + '...' 
    : reasoning
  const shouldShowReadMore = reasoning.length > 120

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow">
      {/* Header: Match Info */}
      <div className="bg-gradient-to-r from-slate-700 to-slate-800 px-6 py-4">
        <div className="flex justify-between items-start text-white">
          <div>
            <div className="text-sm opacity-90">Match #{match.matchNumber}</div>
            <div className="text-lg font-semibold mt-1">{match.venue}</div>
          </div>
          <div className="text-right text-sm opacity-90">
            <div>{formattedDate}</div>
            <div>{formattedTime}</div>
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
              <div className="text-3xl font-bold text-blue-600 mt-2">
                {prediction.predictedHomeScore}
              </div>
            )}
          </div>

          {/* VS */}
          <div className="text-center text-gray-400 font-semibold text-sm">
            VS
          </div>

          {/* Away Team */}
          <div className="text-center">
            <div className="font-bold text-lg text-gray-900">{awayTeam}</div>
            {prediction && (
              <div className="text-3xl font-bold text-blue-600 mt-2">
                {prediction.predictedAwayScore}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Prediction */}
      {prediction && !isTBD && (
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
          {/* Winner */}
          <div className="mb-3">
            <div className="text-sm font-semibold text-gray-600 mb-1">
              Predicted Winner
            </div>
            <div className="font-bold text-xl text-gray-900">
              {prediction.winner}
            </div>
          </div>

          {/* Win Probability Bar */}
          <div className="mb-3">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-semibold text-gray-600">
                Win Probability
              </span>
              <span className="text-sm font-bold text-blue-600">
                {(prediction.winProbability * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all"
                style={{ width: `${prediction.winProbability * 100}%` }}
              />
            </div>
          </div>

          {/* Confidence Badge */}
          {prediction.confidence && (
            <div className="mb-3">
              <span
                className={`inline-block px-3 py-1 text-xs font-semibold rounded-full border ${getConfidenceColor(
                  prediction.confidence
                )}`}
              >
                Confidence: {prediction.confidence.toUpperCase()}
              </span>
            </div>
          )}

          {/* Reasoning */}
          <div>
            <div className="text-sm font-semibold text-gray-600 mb-1">
              AI Analysis
            </div>
            <div className="text-sm text-gray-700 leading-relaxed">
              {isExpanded ? reasoning : truncatedReasoning}
            </div>
            {shouldShowReadMore && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="mt-2 text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
              >
                {isExpanded ? 'Show less' : 'Read more'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* TBD Notice */}
      {isTBD && (
        <div className="border-t border-gray-200 px-6 py-4 bg-amber-50">
          <div className="flex items-center space-x-2 text-amber-800">
            <svg
              className="w-5 h-5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
            <span className="text-sm font-medium">
              Teams to be determined after group stage
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
