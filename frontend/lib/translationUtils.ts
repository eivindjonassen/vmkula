/**
 * Translation utilities for team names and bracket labels.
 * 
 * Handles translation for:
 * - Bracket structure labels (e.g., "Winner A" → "Vinner A")
 * - Team names (future: will map API-Football names to Norwegian)
 * - TBD placeholders
 * 
 * This centralizes all translation logic for when we switch to API-Football.
 */

interface TranslationFunction {
  (key: string): string
}

/**
 * Translate bracket label from English to Norwegian.
 * 
 * Examples:
 * - "Winner A" → "Vinner A"
 * - "Runner-up B" → "Toer B"
 * - "3rd Place C/D/E" → "3. plass C/D/E"
 * - "TBD" → "Avgjøres senere"
 * - "Mexico" → "Mexico" (team names stay as-is for now)
 * 
 * @param label - English label from backend
 * @param t - Translation function from next-intl
 * @returns Norwegian translated label
 */
export function translateBracketLabel(label: string, t: TranslationFunction): string {
  // Handle TBD
  if (label === 'TBD') {
    return t('tbd')
  }

  // Handle "Winner X" pattern
  if (label.startsWith('Winner ')) {
    const group = label.replace('Winner ', '')
    return `${t('winner')} ${group}`
  }

  // Handle "Runner-up X" pattern
  if (label.startsWith('Runner-up ')) {
    const group = label.replace('Runner-up ', '')
    return `${t('runnerUp')} ${group}`
  }

  // Handle "3rd Place X/Y/Z" pattern
  if (label.startsWith('3rd Place ')) {
    const groups = label.replace('3rd Place ', '')
    return `${t('thirdPlace')} ${groups}`
  }

  // Team names - return as-is for now
  // TODO: When switching to API-Football, add team name mapping here
  return label
}

/**
 * Translate match label (full "X vs Y" format).
 * 
 * Examples:
 * - "Winner A vs Runner-up B" → "Vinner A vs Toer B"
 * - "Mexico vs Poland" → "Mexico vs Polen"
 * - "TBD vs TBD" → "Avgjøres senere vs Avgjøres senere"
 * 
 * @param label - Full match label
 * @param t - Translation function from next-intl
 * @returns Norwegian translated label
 */
export function translateMatchLabel(label: string, t: TranslationFunction): string {
  if (!label.includes(' vs ')) {
    return translateBracketLabel(label, t)
  }

  const [home, away] = label.split(' vs ')
  const translatedHome = translateBracketLabel(home.trim(), t)
  const translatedAway = translateBracketLabel(away.trim(), t)
  
  return `${translatedHome} vs ${translatedAway}`
}

/**
 * Translate team name from English to Norwegian.
 * 
 * Currently returns team names as-is since they're proper nouns.
 * Will be extended when switching to API-Football to handle:
 * - Country name variations (e.g., "South Korea" → "Sør-Korea")
 * - Placeholder teams (e.g., "UEFA Playoff Winner" → "UEFA Playoff-vinner")
 * 
 * @param teamName - Team name from backend or API-Football
 * @returns Norwegian team name
 */
export function translateTeamName(teamName: string): string {
  // Team name mapping for special cases
  const teamNameMap: Record<string, string> = {
    // Placeholder teams
    'Winner UEFA Playoff A': 'Vinner UEFA Playoff A',
    'Winner UEFA Playoff B': 'Vinner UEFA Playoff B',
    'Winner UEFA Playoff C': 'Vinner UEFA Playoff C',
    'Winner UEFA Playoff D': 'Vinner UEFA Playoff D',
    'Winner AFC Playoff': 'Vinner AFC Playoff',
    'Winner CONMEBOL Playoff': 'Vinner CONMEBOL Playoff',
    
    // Country names (if API-Football uses different names)
    // Add mappings as needed when switching to API-Football
    // 'South Korea': 'Sør-Korea',
    // 'United States': 'USA',
    // etc.
  }

  return teamNameMap[teamName] || teamName
}

/**
 * Check if a label is a bracket structure label (not a team name).
 * 
 * @param label - Label to check
 * @returns True if it's a bracket label (Winner/Runner-up/3rd Place/TBD)
 */
export function isBracketLabel(label: string): boolean {
  return (
    label === 'TBD' ||
    label.startsWith('Winner ') ||
    label.startsWith('Runner-up ') ||
    label.startsWith('3rd Place ')
  )
}
