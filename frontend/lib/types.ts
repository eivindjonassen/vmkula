/**
 * Type definitions for vmkula-website frontend.
 *
 * Ported from poc/types.ts with additions for tournament predictions.
 */

/**
 * Team statistics and standing information.
 */
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
	rank?: number;
	predictedPlacement?: string;
	predictedRank?: number; // AI predicted final rank (1-4) based on match predictions
	hasRealData?: boolean; // True if data from API-Football, false if mock/placeholder
}

/**
 * Group data with team standings.
 */
export interface Group {
	letter: string;
	teams: TeamStats[];
}

/**
 * Match prediction from AI.
 */
export interface MatchPrediction {
	winner: string;
	winProbability: number;
	predictedHomeScore: number;
	predictedAwayScore: number;
	reasoning: string;
	confidence?: string;
}

/**
 * Match information.
 */
export interface Match {
	id: number;
	matchNumber: number;
	homeTeamId: number | null;
	awayTeamId: number | null;
	homeTeamName?: string;
	awayTeamName?: string;
	homeTeamFlag?: string;
	awayTeamFlag?: string;
	venue: string;
	stageId: number;
	kickoff: string;
	label: string;
	homeScore?: number;
	awayScore?: number;
	prediction?: MatchPrediction;
	hasRealData?: boolean; // True if team data from API-Football, false if mock/placeholder
}

/**
 * Tournament snapshot from Firestore.
 */
export interface TournamentSnapshot {
	groups: Record<string, Group>;
	matches: Match[]; // Group stage matches
	bracket: Match[]; // Knockout matches
	aiSummary: string;
	favorites: string[];
	darkHorses: string[];
	updatedAt: string;
}
