
export interface TeamStats {
  id: number;
  name: string;
  flag: string;
  played: number;
  won: number;
  draw: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  points: number;
  predictedPlacement?: string;
  predictedRank?: number;
}

export interface GroupData {
  id: string;
  name: string;
  teams: TeamStats[];
}

export interface Venue {
  id: number;
  city: string;
  country: string;
  stadium: string;
  region: string;
  airport: string;
}

export interface Stage {
  id: number;
  name: string;
  order: number;
}

export interface MatchPrediction {
  winnerId: number | 'draw' | null;
  winProbability: number;
  reasoning: string;
  predictedHomeScore: number;
  predictedAwayScore: number;
  predictedHomeTeamLabel?: string;
  predictedAwayTeamLabel?: string;
  predictedWinnerLabel?: string;
}

export interface Match {
  id: number;
  matchNumber: number;
  homeTeamId: number | null;
  awayTeamId: number | null;
  cityId: number;
  stageId: number;
  kickoff: string;
  label: string;
  homeScore?: number;
  awayScore?: number;
  prediction?: MatchPrediction;
}

export interface TeamPrediction {
  teamId: number;
  rank: number;
  note: string;
}

export interface GroupPrediction {
  groupId: string;
  predictions: TeamPrediction[];
}

export interface TournamentPathEntry {
  matchNumber: number;
  homeLabel: string;
  awayLabel: string;
  predictedHomeScore: number;
  predictedAwayScore: number;
  winnerLabel: string;
}

export interface AIAnalysis {
  summary: string;
  favorites: string[];
  darkHorses: string[];
  groupPredictions: GroupPrediction[];
  tournamentPath: TournamentPathEntry[];
}
