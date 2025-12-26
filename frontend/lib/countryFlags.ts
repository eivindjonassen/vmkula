/**
 * Country name to flag emoji mapping for World Cup 2026 teams.
 * 
 * All 48 teams participating in the expanded World Cup.
 */

export const COUNTRY_FLAGS: Record<string, string> = {
  // UEFA (Europe) - 16 teams
  'Germany': '🇩🇪',
  'France': '🇫🇷',
  'Spain': '🇪🇸',
  'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  'Portugal': '🇵🇹',
  'Belgium': '🇧🇪',
  'Netherlands': '🇳🇱',
  'Croatia': '🇭🇷',
  'Denmark': '🇩🇰',
  'Switzerland': '🇨🇭',
  'Italy': '🇮🇹',
  'Poland': '🇵🇱',
  'Serbia': '🇷🇸',
  'Austria': '🇦🇹',
  'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
  'Ukraine': '🇺🇦',
  'Turkey': '🇹🇷',
  'Czech Republic': '🇨🇿',
  'Wales': '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
  'Sweden': '🇸🇪',
  'Norway': '🇳🇴',
  
  // CONMEBOL (South America) - 6 teams
  'Brazil': '🇧🇷',
  'Argentina': '🇦🇷',
  'Uruguay': '🇺🇾',
  'Colombia': '🇨🇴',
  'Ecuador': '🇪🇨',
  'Peru': '🇵🇪',
  'Chile': '🇨🇱',
  'Paraguay': '🇵🇾',
  'Venezuela': '🇻🇪',
  'Bolivia': '🇧🇴',
  
  // CONCACAF (North/Central America) - 8 teams (includes hosts)
  'Mexico': '🇲🇽',
  'United States': '🇺🇸',
  'USA': '🇺🇸',
  'Canada': '🇨🇦',
  'Costa Rica': '🇨🇷',
  'Jamaica': '🇯🇲',
  'Panama': '🇵🇦',
  'Honduras': '🇭🇳',
  'El Salvador': '🇸🇻',
  'Trinidad and Tobago': '🇹🇹',
  
  // CAF (Africa) - 9 teams
  'Senegal': '🇸🇳',
  'Morocco': '🇲🇦',
  'Tunisia': '🇹🇳',
  'Algeria': '🇩🇿',
  'Nigeria': '🇳🇬',
  'Cameroon': '🇨🇲',
  'Ghana': '🇬🇭',
  'Egypt': '🇪🇬',
  'South Africa': '🇿🇦',
  'Ivory Coast': '🇨🇮',
  'Mali': '🇲🇱',
  'Burkina Faso': '🇧🇫',
  
  // AFC (Asia) - 8 teams
  'Japan': '🇯🇵',
  'South Korea': '🇰🇷',
  'Korea Republic': '🇰🇷',
  'Iran': '🇮🇷',
  'Australia': '🇦🇺',
  'Saudi Arabia': '🇸🇦',
  'Qatar': '🇶🇦',
  'Iraq': '🇮🇶',
  'United Arab Emirates': '🇦🇪',
  'UAE': '🇦🇪',
  'China': '🇨🇳',
  'Uzbekistan': '🇺🇿',
  
  // OFC (Oceania) - 1 team
  'New Zealand': '🇳🇿',
  
  // Playoff winners / TBD
  'TBD': '🏴',
  
  // Historical teams (for reference)
  'Russia': '🇷🇺',
  'Iceland': '🇮🇸',
  'Haiti': '🇭🇹',
}

/**
 * Get flag emoji for a country name.
 * 
 * @param countryName Country name (e.g., 'Brazil', 'United States')
 * @returns Flag emoji or default flag if not found
 */
export function getCountryFlag(countryName?: string): string {
  if (!countryName) return '🏴'
  
  // Direct lookup
  const flag = COUNTRY_FLAGS[countryName]
  if (flag) return flag
  
  // Try case-insensitive lookup
  const lowerName = countryName.toLowerCase()
  for (const [key, value] of Object.entries(COUNTRY_FLAGS)) {
    if (key.toLowerCase() === lowerName) {
      return value
    }
  }
  
  // Default flag for unknown countries
  return '🏴'
}
