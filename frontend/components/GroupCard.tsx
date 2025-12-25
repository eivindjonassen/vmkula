/**
 * GroupCard component - Display group standings table.
 * 
 * Features:
 * - Responsive Tailwind CSS design with Norwegian translations
 * - Highlight top 2 teams (green) - qualifiers
 * - Highlight 3rd place (yellow) - possible qualifier
 * - Display: Rank, Team, P, W, D, L, GF, GA, GD, Pts
 */

'use client'

import { useTranslations } from 'next-intl'
import type { Group } from '../lib/types'

interface GroupCardProps {
  group: Group
}

export default function GroupCard({ group }: GroupCardProps) {
  const t = useTranslations('groupCard')
  return (
    <div className="bg-white rounded-2xl shadow-lg border-2 border-emerald-200 overflow-hidden hover:shadow-xl transition-shadow duration-300">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-500 to-emerald-600 px-6 py-4 shadow-lg">
        <h3 className="text-white font-bold text-xl flex items-center gap-2">
          <span>⚽</span>
          <span>{t('group')} {group.letter}</span>
        </h3>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-emerald-50 border-b border-emerald-200">
              <th className="px-4 py-3 text-left text-xs font-bold text-emerald-800 uppercase tracking-wider" title={t('rank')}>
                #
              </th>
              <th className="px-4 py-3 text-left text-xs font-bold text-emerald-800 uppercase tracking-wider">
                {t('team')}
              </th>
              <th className="px-2 py-3 text-center text-xs font-bold text-emerald-800 uppercase tracking-wider" title={t('playedFull')}>
                {t('played')}
              </th>
              <th className="px-2 py-3 text-center text-xs font-bold text-emerald-800 uppercase tracking-wider" title={t('wonFull')}>
                {t('won')}
              </th>
              <th className="px-2 py-3 text-center text-xs font-bold text-emerald-800 uppercase tracking-wider" title={t('drawFull')}>
                {t('draw')}
              </th>
              <th className="px-2 py-3 text-center text-xs font-bold text-emerald-800 uppercase tracking-wider" title={t('lostFull')}>
                {t('lost')}
              </th>
              <th className="hidden sm:table-cell px-2 py-3 text-center text-xs font-bold text-emerald-800 uppercase tracking-wider" title={t('goalsForFull')}>
                {t('goalsFor')}
              </th>
              <th className="hidden sm:table-cell px-2 py-3 text-center text-xs font-bold text-emerald-800 uppercase tracking-wider" title={t('goalsAgainstFull')}>
                {t('goalsAgainst')}
              </th>
              <th className="px-2 py-3 text-center text-xs font-bold text-emerald-800 uppercase tracking-wider" title={t('goalDifferenceFull')}>
                {t('goalDifference')}
              </th>
              <th className="px-2 py-3 text-center text-xs font-bold text-emerald-800 uppercase tracking-wider" title={t('pointsFull')}>
                {t('points')}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {group.teams.map((team, index) => {
              // Determine row styling based on rank
              const isQualifier = index < 2 // Top 2 qualify
              const isThirdPlace = index === 2 // 3rd place might qualify
              
              let rowClass = 'hover:bg-emerald-50 transition-all duration-200'
              if (isQualifier) {
                rowClass += ' bg-emerald-50 border-l-4 border-l-emerald-500'
              } else if (isThirdPlace) {
                rowClass += ' bg-yellow-50 border-l-4 border-l-yellow-500'
              }

              const goalDifference = team.goalsFor - team.goalsAgainst
              const gdDisplay = goalDifference > 0 ? `+${goalDifference}` : goalDifference.toString()

              return (
                <tr key={`${group.letter}-${team.name}-${index}`} className={rowClass}>
                  {/* Rank */}
                  <td className="px-4 py-3 text-center font-medium text-gray-900">
                    {index + 1}
                  </td>

                  {/* Team */}
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl">{team.flag}</span>
                      <span className="font-medium text-gray-900">{team.name}</span>
                    </div>
                  </td>

                  {/* Stats */}
                  <td className="px-2 py-3 text-center text-gray-700 font-medium">
                    {team.played}
                  </td>
                  <td className="px-2 py-3 text-center text-gray-700">
                    {team.won}
                  </td>
                  <td className="px-2 py-3 text-center text-gray-700">
                    {team.draw}
                  </td>
                  <td className="px-2 py-3 text-center text-gray-700">
                    {team.lost}
                  </td>
                  <td className="hidden sm:table-cell px-2 py-3 text-center text-gray-700">
                    {team.goalsFor}
                  </td>
                  <td className="hidden sm:table-cell px-2 py-3 text-center text-gray-700">
                    {team.goalsAgainst}
                  </td>
                  <td className="px-2 py-3 text-center text-gray-700 font-medium">
                    {gdDisplay}
                  </td>
                  <td className="px-2 py-3 text-center">
                    <div className="inline-flex items-center justify-center bg-emerald-100 border-2 border-emerald-300 rounded-lg px-3 py-1">
                      <span className="font-black text-emerald-700 text-base">{team.points}</span>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Footer / Legend */}
      <div className="bg-emerald-50 px-6 py-3 border-t-2 border-emerald-200">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 text-xs">
          <div className="flex items-center gap-2 bg-white border-2 border-emerald-300 rounded-lg px-3 py-1.5">
            <div className="w-4 h-4 bg-emerald-100 border-2 border-emerald-400 rounded"></div>
            <span className="font-bold text-emerald-800">{t('qualified')}</span>
          </div>
          <div className="flex items-center gap-2 bg-white border-2 border-yellow-300 rounded-lg px-3 py-1.5">
            <div className="w-4 h-4 bg-yellow-100 border-2 border-yellow-400 rounded"></div>
            <span className="font-bold text-yellow-800">{t('possibleQualifier')}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
