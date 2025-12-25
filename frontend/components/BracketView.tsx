/**
 * BracketView component - Display knockout bracket visualization.
 * 
 * Features:
 * - Group matches by stage (Round of 32, Round of 16, QF, SF, Final)
 * - Display bracket tree with visual progression
 * - Use MatchCard for individual matches
 * - Handle TBD matchups gracefully
 * - Responsive: horizontal scroll on mobile, full view on desktop
 */

import type { Match } from '../lib/types'
import MatchCard from './MatchCard'

interface BracketViewProps {
  bracket: Match[]
}

/**
 * Map stage IDs to stage names.
 * Based on tournament structure in worldcup2026.db
 */
const STAGE_NAMES: Record<number, string> = {
  2: 'Round of 32',
  3: 'Round of 16',
  4: 'Quarter-finals',
  5: 'Semi-finals',
  6: 'Third Place Playoff',
  7: 'Final',
}

/**
 * Stage display order (left to right in bracket)
 */
const STAGE_ORDER = [2, 3, 4, 5, 7] // Exclude Third Place Playoff from main bracket

export default function BracketView({ bracket }: BracketViewProps) {
  // Group matches by stage
  const matchesByStage = bracket.reduce((acc, match) => {
    const stageId = match.stageId
    if (!acc[stageId]) {
      acc[stageId] = []
    }
    acc[stageId].push(match)
    return acc
  }, {} as Record<number, Match[]>)

  // Get third place playoff separately
  const thirdPlaceMatch = matchesByStage[6]?.[0]

  return (
    <div className="w-full">
      {/* Main Bracket - Horizontal Scroll on Mobile */}
      <div className="overflow-x-auto pb-8">
        <div className="inline-flex gap-8 min-w-max px-4 py-6">
          {STAGE_ORDER.map((stageId) => {
            const matches = matchesByStage[stageId] || []
            const stageName = STAGE_NAMES[stageId] || `Stage ${stageId}`

            return (
              <div key={stageId} className="flex flex-col items-center">
                {/* Stage Header */}
                <div className="mb-6 text-center">
                  <h3 className="text-lg font-bold text-gray-800 mb-1">
                    {stageName}
                  </h3>
                  <div className="text-sm text-gray-500">
                    {matches.length} {matches.length === 1 ? 'match' : 'matches'}
                  </div>
                </div>

                {/* Matches */}
                <div className="flex flex-col gap-6 w-80">
                  {matches.map((match) => (
                    <MatchCard key={match.id} match={match} prediction={match.prediction} />
                  ))}
                  
                  {matches.length === 0 && (
                    <div className="text-center text-gray-400 py-8">
                      No matches scheduled
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Third Place Playoff - Separate Section */}
      {thirdPlaceMatch && (
        <div className="mt-8 border-t pt-8">
          <div className="max-w-md mx-auto">
            <div className="mb-4 text-center">
              <h3 className="text-lg font-bold text-gray-800 mb-1">
                Third Place Playoff
              </h3>
              <div className="text-sm text-gray-500">
                Determine 3rd place
              </div>
            </div>
            <MatchCard match={thirdPlaceMatch} prediction={thirdPlaceMatch.prediction} />
          </div>
        </div>
      )}

      {/* Mobile Scroll Hint */}
      <div className="lg:hidden mt-4 text-center text-sm text-gray-500">
        ← Scroll horizontally to view all stages →
      </div>

      {/* Legend */}
      <div className="mt-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h4 className="font-semibold text-gray-700 mb-3">Tournament Format</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-gray-600">
          <div className="flex items-start gap-2">
            <span className="font-semibold min-w-[140px]">Round of 32:</span>
            <span>Top 2 from each group + 8 best 3rd place teams</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-semibold min-w-[140px]">Round of 16:</span>
            <span>Winners from Round of 32</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-semibold min-w-[140px]">Quarter-finals:</span>
            <span>Winners from Round of 16</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-semibold min-w-[140px]">Semi-finals:</span>
            <span>Winners from Quarter-finals</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-semibold min-w-[140px]">Final:</span>
            <span>Winners from Semi-finals compete for championship</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-semibold min-w-[140px]">3rd Place:</span>
            <span>Losers from Semi-finals</span>
          </div>
        </div>
      </div>
    </div>
  )
}
