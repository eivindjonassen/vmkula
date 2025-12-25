/**
 * GroupCard component - Display group standings table.
 * 
 * Features:
 * - Responsive Tailwind CSS design
 * - Highlight top 2 teams (green) - qualifiers
 * - Highlight 3rd place (yellow) - possible qualifier
 * - Display: Rank, Team, P, W, D, L, GF, GA, GD, Pts
 */

import type { Group } from '../lib/types'

interface GroupCardProps {
  group: Group
}

export default function GroupCard({ group }: GroupCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
        <h3 className="text-white font-bold text-xl">
          Group {group.letter}
        </h3>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Rank
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Team
              </th>
              <th className="px-2 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                P
              </th>
              <th className="px-2 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                W
              </th>
              <th className="px-2 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                D
              </th>
              <th className="px-2 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                L
              </th>
              <th className="px-2 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                GF
              </th>
              <th className="px-2 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                GA
              </th>
              <th className="px-2 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                GD
              </th>
              <th className="px-2 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Pts
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {group.teams.map((team, index) => {
              // Determine row styling based on rank
              const isQualifier = index < 2 // Top 2 qualify
              const isThirdPlace = index === 2 // 3rd place might qualify
              
              let rowClass = 'hover:bg-gray-50 transition-colors'
              if (isQualifier) {
                rowClass += ' bg-green-50'
              } else if (isThirdPlace) {
                rowClass += ' bg-yellow-50'
              }

              const goalDifference = team.goalsFor - team.goalsAgainst
              const gdDisplay = goalDifference > 0 ? `+${goalDifference}` : goalDifference.toString()

              return (
                <tr key={team.id} className={rowClass}>
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
                  <td className="px-2 py-3 text-center text-gray-700">
                    {team.goalsFor}
                  </td>
                  <td className="px-2 py-3 text-center text-gray-700">
                    {team.goalsAgainst}
                  </td>
                  <td className="px-2 py-3 text-center text-gray-700 font-medium">
                    {gdDisplay}
                  </td>
                  <td className="px-2 py-3 text-center font-bold text-blue-600">
                    {team.points}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Footer / Legend */}
      <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
        <div className="flex items-center space-x-6 text-xs text-gray-600">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-50 border border-green-200 rounded"></div>
            <span>Qualified</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-yellow-50 border border-yellow-200 rounded"></div>
            <span>Possible Qualifier</span>
          </div>
        </div>
      </div>
    </div>
  )
}
