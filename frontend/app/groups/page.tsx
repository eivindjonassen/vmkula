/**
 * Groups page - Display all 12 group standings with filtering.
 * 
 * Features:
 * - Fetch predictions using fetchLatestPredictions()
 * - Display all 12 groups in responsive grid
 * - Show top 8 third-place qualifiers
 * - Filter buttons to highlight specific groups
 * - Loading skeleton
 */

'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { fetchLatestPredictions } from '../../lib/firestore'
import type { TournamentSnapshot, Group } from '../../lib/types'
import GroupCard from '../../components/GroupCard'

export default function GroupsPage() {
  const [snapshot, setSnapshot] = useState<TournamentSnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null)

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

  // Get third-place teams sorted by qualification criteria
  const getThirdPlaceQualifiers = (): Array<{ group: string; team: any; points: number; gd: number }> => {
    if (!snapshot) return []

    const thirdPlaceTeams = Object.entries(snapshot.groups).map(([letter, group]) => {
      const thirdTeam = group.teams[2] // 3rd place team (0-indexed)
      if (!thirdTeam) return null
      return {
        group: letter,
        team: thirdTeam,
        points: thirdTeam.points,
        gd: thirdTeam.goalsFor - thirdTeam.goalsAgainst,
      }
    }).filter(Boolean) as Array<{ group: string; team: any; points: number; gd: number }>

    // Sort by points, then GD, then goals scored
    return thirdPlaceTeams.sort((a, b) => {
      if (a.points !== b.points) return b.points - a.points
      if (a.gd !== b.gd) return b.gd - a.gd
      return b.team.goalsFor - a.team.goalsFor
    }).slice(0, 8) // Top 8 qualify
  }

  const thirdPlaceQualifiers = getThirdPlaceQualifiers()

  // Filter groups based on selection
  const filteredGroups = snapshot
    ? Object.entries(snapshot.groups).filter(([letter]) => 
        selectedGroup ? letter === selectedGroup : true
      )
    : []

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <div>
              <h1 className="text-3xl font-black tracking-tight text-slate-900">Group Standings</h1>
              <p className="text-sm text-slate-600 mt-1">World Cup 2026 - All 12 Groups</p>
            </div>
            <Link
              href="/"
              className="px-4 py-2 min-h-[44px] flex items-center bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-colors focus:ring-4 focus:ring-slate-300 focus:outline-none"
              aria-label="Tilbake til hjemmesiden"
            >
              ← Back to Home
            </Link>
          </div>

          {/* Filter Buttons */}
          {snapshot && !loading && (
            <div className="mt-6 flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedGroup(null)}
                className={`px-4 py-2 min-h-[44px] rounded-lg text-sm font-semibold transition-colors focus:ring-4 focus:outline-none ${
                  selectedGroup === null
                    ? 'bg-blue-600 text-white focus:ring-blue-300'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200 focus:ring-slate-300'
                }`}
                aria-pressed={selectedGroup === null}
                aria-label="Vis alle grupper"
              >
                All Groups
              </button>
              {Object.keys(snapshot.groups).map((letter) => (
                <button
                  key={letter}
                  onClick={() => setSelectedGroup(letter)}
                  className={`px-4 py-2 min-h-[44px] rounded-lg text-sm font-semibold transition-colors focus:ring-4 focus:outline-none ${
                    selectedGroup === letter
                      ? 'bg-blue-600 text-white focus:ring-blue-300'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200 focus:ring-slate-300'
                  }`}
                  aria-pressed={selectedGroup === letter}
                  aria-label={`Vis gruppe ${letter}`}
                >
                  Group {letter}
                </button>
              ))}
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Loading State */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[...Array(12)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow-md border border-gray-200 p-6 animate-pulse">
                <div className="h-6 bg-slate-200 rounded mb-4"></div>
                <div className="space-y-3">
                  <div className="h-4 bg-slate-100 rounded"></div>
                  <div className="h-4 bg-slate-100 rounded"></div>
                  <div className="h-4 bg-slate-100 rounded"></div>
                  <div className="h-4 bg-slate-100 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <div className="text-red-600 font-semibold mb-2">Error loading groups</div>
            <p className="text-red-500 text-sm mb-4">{error}</p>
            <button
              onClick={loadPredictions}
              className="px-4 py-2 min-h-[44px] bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors focus:ring-4 focus:ring-red-300 focus:outline-none"
              aria-label="Prøv å laste inn grupper på nytt"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Groups Grid */}
        {snapshot && !loading && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
              {filteredGroups.map(([letter, group]) => (
                <GroupCard key={letter} group={group} />
              ))}
            </div>

            {/* Third-Place Qualifiers Section */}
            {selectedGroup === null && (
              <div className="mt-12 bg-gradient-to-br from-white to-amber-50 rounded-3xl p-8 border border-amber-200 shadow-lg">
                <h2 className="text-2xl font-bold mb-4 text-slate-900">
                  Top 8 Third-Place Qualifiers
                </h2>
                <p className="text-slate-600 mb-6">
                  Best 8 teams finishing 3rd in their groups advance to Round of 32
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {thirdPlaceQualifiers.map(({ group, team, points, gd }, index) => (
                    <div
                      key={`${group}-${team.id}`}
                      className="bg-white rounded-xl p-4 border border-amber-200 shadow-sm"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-amber-600 uppercase">
                          Group {group}
                        </span>
                        <span className="text-xs font-bold text-slate-500">
                          Rank #{index + 1}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 mb-3">
                        <span className="text-3xl">{team.flag}</span>
                        <span className="font-bold text-slate-900">{team.name}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <div className="text-slate-600">
                          <span className="font-semibold">Pts:</span> {points}
                        </div>
                        <div className="text-slate-600">
                          <span className="font-semibold">GD:</span> {gd > 0 ? '+' : ''}{gd}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Legend */}
                <div className="mt-6 p-4 bg-amber-100/50 rounded-xl border border-amber-200">
                  <h4 className="text-xs font-bold text-amber-800 uppercase mb-2">
                    Qualification Criteria
                  </h4>
                  <p className="text-sm text-amber-900">
                    Third-place teams ranked by: Points → Goal Difference → Goals Scored → Fair Play Points
                  </p>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-20 border-t border-slate-200 bg-white py-12 text-center">
        <p className="text-slate-500 text-sm">
          VM KULA 2026 - AI-powered World Cup predictions
        </p>
      </footer>
    </div>
  )
}
