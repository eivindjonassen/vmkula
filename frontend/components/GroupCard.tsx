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

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import type { Group } from '../lib/types'
import { translateTeamName } from '../lib/translationUtils'
import { isFavoriteTeam, toggleFavoriteTeam, getFavoriteTeams } from '../lib/favorites'

interface GroupCardProps {
  group: Group
}

export default function GroupCard({ group }: GroupCardProps) {
  const t = useTranslations('groupCard')
  const [favorites, setFavorites] = useState<string[]>(() => 
    typeof window !== 'undefined' ? getFavoriteTeams() : []
  )

  // Sync favorites when they change in other components
  useEffect(() => {
    const handleStorageChange = () => {
      setFavorites(getFavoriteTeams())
    }
    
    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])

  const handleToggleFavorite = (teamName: string) => {
    const updated = toggleFavoriteTeam(teamName)
    setFavorites(updated)
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg border-2 border-emerald-200 overflow-hidden hover:shadow-xl transition-shadow duration-300">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-500 to-emerald-600 px-6 py-4 shadow-lg">
        <div className="flex items-center justify-between">
          <h3 className="text-white font-bold text-xl flex items-center gap-2">
            <span>⚽</span>
            <span>{t('group')} {group.letter}</span>
          </h3>
          {/* Data Source Badge */}
          {group.teams.some(team => team.hasRealData) && (
            <span 
              className="inline-flex items-center gap-1 px-2 py-1 text-xs font-bold bg-green-900 bg-opacity-30 text-white border border-white border-opacity-30 rounded-full"
              title="Data hentet fra API-Football"
            >
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <span>Live Data</span>
            </span>
          )}
          {group.teams.every(team => team.hasRealData === false) && (
            <span 
              className="inline-flex items-center gap-1 px-2 py-1 text-xs font-bold bg-amber-900 bg-opacity-30 text-white border border-white border-opacity-30 rounded-full"
              title="Testdata - ikke fra API-Football"
            >
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span>Test Data</span>
            </span>
          )}
        </div>
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
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center space-x-2 flex-1 min-w-0">
                        <span className="text-2xl flex-shrink-0" aria-hidden="true">{team.flag}</span>
                        <span className="font-medium text-gray-900 truncate">
                          <span className="sr-only">Lag: </span>
                          {translateTeamName(team.name)}
                        </span>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleToggleFavorite(team.name)
                        }}
                        className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-emerald-100 rounded-full transition-colors focus:ring-4 focus:ring-emerald-300 focus:outline-none flex-shrink-0"
                        aria-label={favorites.includes(team.name) ? `Fjern ${team.name} fra favoritter` : `Legg til ${team.name} som favoritt`}
                        title={favorites.includes(team.name) ? 'Fjern fra favoritter' : 'Legg til favoritt'}
                      >
                        {favorites.includes(team.name) ? (
                          <svg className="w-5 h-5 text-yellow-500 fill-current" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5 text-slate-400 hover:text-yellow-500" fill="none" viewBox="0 0 20 20" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                          </svg>
                        )}
                      </button>
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
