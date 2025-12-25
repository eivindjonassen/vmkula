/**
 * BracketView component - Display knockout bracket visualization with Norwegian translations.
 * 
 * Features:
 * - Group matches by stage (Round of 32, Round of 16, QF, SF, Final)
 * - Display bracket tree with visual progression
 * - Use MatchCard for individual matches
 * - Handle TBD matchups gracefully
 * - Responsive: horizontal scroll on mobile, full view on desktop
 */

'use client'

import { useTranslations } from 'next-intl'
import type { Match } from '../lib/types'
import MatchCard from './MatchCard'

interface BracketViewProps {
  bracket: Match[]
}

/**
 * Stage display order (left to right in bracket)
 */
const STAGE_ORDER = [2, 3, 4, 5, 7] // Exclude Third Place Playoff from main bracket

export default function BracketView({ bracket }: BracketViewProps) {
  const t = useTranslations('bracketView')
  
  /**
   * Map stage IDs to translated stage names
   */
  const getStageNames = (): Record<number, string> => ({
    2: t('roundOf32'),
    3: t('roundOf16'),
    4: t('quarterFinals'),
    5: t('semiFinals'),
    6: t('thirdPlacePlayoff'),
    7: t('final'),
  })
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
  const STAGE_NAMES = getStageNames()

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
                  <h3 className="text-lg font-bold text-emerald-800 mb-1">
                    {stageName}
                  </h3>
                  <div className="text-sm text-slate-600">
                    {matches.length} {matches.length === 1 ? t('match') : t('matches')}
                  </div>
                </div>

                {/* Matches */}
                <div className="flex flex-col gap-6 w-80">
                  {matches.map((match) => (
                    <MatchCard key={match.id} match={match} prediction={match.prediction} />
                  ))}
                  
                  {matches.length === 0 && (
                    <div className="text-center text-slate-400 py-8">
                      {t('noMatchesScheduled')}
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
        <div className="mt-8 border-t-2 border-emerald-200 pt-8">
          <div className="max-w-md mx-auto">
            <div className="mb-4 text-center">
              <h3 className="text-lg font-bold text-emerald-800 mb-1 flex items-center justify-center gap-2">
                <span>🥉</span>
                <span>{t('thirdPlacePlayoff')}</span>
              </h3>
              <div className="text-sm text-slate-600">
                {t('determine3rdPlace')}
              </div>
            </div>
            <MatchCard match={thirdPlaceMatch} prediction={thirdPlaceMatch.prediction} />
          </div>
        </div>
      )}

      {/* Mobile Scroll Hint */}
      <div className="lg:hidden mt-4 text-center text-sm text-slate-500">
        {t('scrollHint')}
      </div>

      {/* Legend */}
      <div className="mt-8 p-6 bg-gradient-to-br from-emerald-50 to-white rounded-2xl border-2 border-emerald-200">
        <h4 className="font-bold text-emerald-800 mb-4 text-lg flex items-center gap-2">
          <span>📋</span>
          <span>{t('tournamentFormat')}</span>
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-slate-700">
          <div className="flex items-start gap-3 bg-white p-3 rounded-lg border border-emerald-200">
            <span className="font-bold text-emerald-700 min-w-[140px]">{t('roundOf32')}:</span>
            <span>{t('formatRoundOf32')}</span>
          </div>
          <div className="flex items-start gap-3 bg-white p-3 rounded-lg border border-emerald-200">
            <span className="font-bold text-emerald-700 min-w-[140px]">{t('roundOf16')}:</span>
            <span>{t('formatRoundOf16')}</span>
          </div>
          <div className="flex items-start gap-3 bg-white p-3 rounded-lg border border-emerald-200">
            <span className="font-bold text-emerald-700 min-w-[140px]">{t('quarterFinals')}:</span>
            <span>{t('formatQuarterFinals')}</span>
          </div>
          <div className="flex items-start gap-3 bg-white p-3 rounded-lg border border-emerald-200">
            <span className="font-bold text-emerald-700 min-w-[140px]">{t('semiFinals')}:</span>
            <span>{t('formatSemiFinals')}</span>
          </div>
          <div className="flex items-start gap-3 bg-white p-3 rounded-lg border border-emerald-200">
            <span className="font-bold text-emerald-700 min-w-[140px]">{t('final')}:</span>
            <span>{t('formatFinal')}</span>
          </div>
          <div className="flex items-start gap-3 bg-white p-3 rounded-lg border border-emerald-200">
            <span className="font-bold text-emerald-700 min-w-[140px]">3. plass:</span>
            <span>{t('format3rdPlace')}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
