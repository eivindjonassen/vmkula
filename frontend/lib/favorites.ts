/**
 * Favorite teams management using localStorage.
 * 
 * Features:
 * - Add/remove favorite teams
 * - Get all favorite teams
 * - Check if team is favorited
 * - Persist across sessions
 */

const FAVORITES_KEY = 'vmkula_favorite_teams'

/**
 * Get all favorite teams from localStorage.
 * 
 * @returns Array of team names
 */
export function getFavoriteTeams(): string[] {
  if (typeof window === 'undefined') return []
  
  try {
    const stored = localStorage.getItem(FAVORITES_KEY)
    if (!stored) return []
    
    const favorites = JSON.parse(stored)
    return Array.isArray(favorites) ? favorites : []
  } catch (error) {
    console.error('Error reading favorite teams:', error)
    return []
  }
}

/**
 * Dispatch custom event to notify components of favorites change.
 */
function notifyFavoritesChanged(): void {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('favoritesUpdated'))
  }
}

/**
 * Add a team to favorites.
 * 
 * @param teamName Team name to add
 * @returns Updated favorites array
 */
export function addFavoriteTeam(teamName: string): string[] {
  const favorites = getFavoriteTeams()
  
  // Don't add duplicates
  if (favorites.includes(teamName)) {
    return favorites
  }
  
  const updated = [...favorites, teamName]
  
  try {
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(updated))
    notifyFavoritesChanged()
  } catch (error) {
    console.error('Error saving favorite team:', error)
  }
  
  return updated
}

/**
 * Remove a team from favorites.
 * 
 * @param teamName Team name to remove
 * @returns Updated favorites array
 */
export function removeFavoriteTeam(teamName: string): string[] {
  const favorites = getFavoriteTeams()
  const updated = favorites.filter(name => name !== teamName)
  
  try {
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(updated))
    notifyFavoritesChanged()
  } catch (error) {
    console.error('Error removing favorite team:', error)
  }
  
  return updated
}

/**
 * Toggle favorite status for a team.
 * 
 * @param teamName Team name to toggle
 * @returns Updated favorites array
 */
export function toggleFavoriteTeam(teamName: string): string[] {
  const favorites = getFavoriteTeams()
  
  if (favorites.includes(teamName)) {
    return removeFavoriteTeam(teamName)
  } else {
    return addFavoriteTeam(teamName)
  }
}

/**
 * Check if a team is in favorites.
 * 
 * @param teamName Team name to check
 * @returns True if team is favorited
 */
export function isFavoriteTeam(teamName: string): boolean {
  const favorites = getFavoriteTeams()
  return favorites.includes(teamName)
}

/**
 * Clear all favorite teams.
 */
export function clearFavoriteTeams(): void {
  try {
    localStorage.removeItem(FAVORITES_KEY)
    notifyFavoritesChanged()
  } catch (error) {
    console.error('Error clearing favorite teams:', error)
  }
}
