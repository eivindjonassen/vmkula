/**
 * MatchCard component - Display match prediction card with Norwegian translations.
 *
 * Features:
 * - Display match info: teams, venue, kickoff time
 * - Show AI prediction with win probability bar
 * - Display predicted score
 * - Show reasoning (expandable)
 * - Color-coded confidence levels
 * - Handle TBD matchups gracefully
 */

"use client";

import { useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";
import {
	isBracketLabel,
	translateBracketLabel,
	translateTeamName,
} from "../lib/translationUtils";
import type { Match, MatchPrediction } from "../lib/types";

interface MatchCardProps {
	match: Match;
	prediction?: MatchPrediction;
}

export default function MatchCard({ match, prediction }: MatchCardProps) {
	const [isExpanded, setIsExpanded] = useState(false);
	const t = useTranslations("matchCard");
	const tCommon = useTranslations("common");
	const tBracket = useTranslations("bracketView");

	// Handle TBD matchups - use label if teams are not determined yet
	const isTBD =
		!match.homeTeamId ||
		!match.awayTeamId ||
		match.homeTeamName === "TBD" ||
		match.awayTeamName === "TBD";

	// Get raw team names/labels
	const rawHomeTeam =
		match.homeTeamName && match.homeTeamName !== "TBD"
			? match.homeTeamName
			: match.label.split(" vs ")[0];
	const rawAwayTeam =
		match.awayTeamName && match.awayTeamName !== "TBD"
			? match.awayTeamName
			: match.label.split(" vs ")[1] || "TBD";

	// Translate to Norwegian
	const homeTeam = isBracketLabel(rawHomeTeam)
		? translateBracketLabel(rawHomeTeam, (key) => tBracket(key))
		: translateTeamName(rawHomeTeam);
	const awayTeam = isBracketLabel(rawAwayTeam)
		? translateBracketLabel(rawAwayTeam, (key) => tBracket(key))
		: translateTeamName(rawAwayTeam);

	// Format kickoff time in Norwegian
	const kickoffDate = new Date(match.kickoff);
	const formattedDate = kickoffDate.toLocaleDateString("nb-NO", {
		day: "numeric",
		month: "long",
		year: "numeric",
	});
	const formattedTime = kickoffDate.toLocaleTimeString("nb-NO", {
		hour: "2-digit",
		minute: "2-digit",
		hour12: false,
	});

	// Confidence color coding (WCAG AA compliant contrast ratios)
	const getConfidenceColor = (confidence?: string) => {
		switch (confidence?.toLowerCase()) {
			case "high":
				return "bg-emerald-50 text-emerald-900 border-emerald-400";
			case "medium":
				return "bg-blue-50 text-blue-900 border-blue-400";
			case "low":
				return "bg-slate-50 text-slate-900 border-slate-400";
			default:
				return "bg-gray-50 text-gray-900 border-gray-400";
		}
	};

	const getConfidenceLabel = (confidence?: string) => {
		switch (confidence?.toLowerCase()) {
			case "high":
				return t("confidenceHigh");
			case "medium":
				return t("confidenceMedium");
			case "low":
				return t("confidenceLow");
			default:
				return confidence?.toUpperCase();
		}
	};

	const getConfidenceStars = (confidence?: string) => {
		switch (confidence?.toLowerCase()) {
			case "high":
				return "⭐⭐⭐";
			case "medium":
				return "⭐⭐";
			case "low":
				return "⭐";
			default:
				return "";
		}
	};

	// Truncate reasoning
	const [showFullReasoning, setShowFullReasoning] = useState(false);
	const reasoning = prediction?.reasoning || t("predictionPending");
	const truncatedReasoning =
		reasoning.length > 120 ? reasoning.substring(0, 120) + "..." : reasoning;
	const shouldShowReadMore = reasoning.length > 120;

	// Handle share functionality
	const handleShare = async () => {
		const shareText = `${homeTeam} vs ${awayTeam} - AI spår: ${prediction?.winner || "TBD"} (${prediction?.predictedHomeScore || 0}-${prediction?.predictedAwayScore || 0})`;

		if (navigator.share) {
			try {
				await navigator.share({
					title: "VM KULA 2026",
					text: shareText,
					url: window.location.href,
				});
			} catch {
				// User cancelled or error occurred
				console.log("Share cancelled or failed");
			}
		} else {
			// Fallback: copy to clipboard
			navigator.clipboard.writeText(shareText);
			alert("Kopiert til utklippstavle!");
		}
	};

	return (
		<div className="bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden hover:shadow-lg transition-all duration-300">
			{/* Compact Mobile-First View */}
			<div className="p-4">
				<div className="flex flex-col gap-3">
					{/* Match Number, Date & Time */}
					<div className="flex items-center gap-3 flex-wrap">
						<div className="inline-flex items-center gap-2 px-3 py-1 bg-slate-100 rounded-lg">
							<span className="text-xs font-bold text-slate-500 uppercase">
								Kamp
							</span>
							<span className="text-sm font-black text-slate-900">
								#{match.matchNumber}
							</span>
						</div>
						<div className="text-sm text-slate-600 font-medium">
							{formattedDate}
						</div>
						<div className="text-2xl font-bold text-slate-900">
							{formattedTime}
						</div>
					</div>

					{/* Teams & Share Button */}
					<div className="flex items-center gap-2">
						<div className="flex-1 min-w-0 space-y-1">
							<div className="flex items-center gap-2">
								<span className="text-2xl flex-shrink-0" aria-hidden="true">
									{match.homeTeamFlag || "🏴"}
								</span>
								<span className="font-semibold text-slate-900 truncate">
									{homeTeam}
								</span>
							</div>
							<div className="flex items-center gap-2">
								<span className="text-2xl flex-shrink-0" aria-hidden="true">
									{match.awayTeamFlag || "🏴"}
								</span>
								<span className="font-semibold text-slate-900 truncate">
									{awayTeam}
								</span>
							</div>
						</div>

						{/* Share Button */}
						<button
							onClick={(e) => {
								e.stopPropagation();
								handleShare();
							}}
							className="p-3 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-slate-100 rounded-full transition-colors focus:ring-4 focus:ring-emerald-300 focus:outline-none"
							aria-label="Del kamp"
							title="Del kamp"
						>
							<svg
								className="w-5 h-5 text-slate-600"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									strokeLinecap="round"
									strokeLinejoin="round"
									strokeWidth={2}
									d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
								/>
							</svg>
						</button>
					</div>

					{/* Venue Info */}
					<div className="flex items-center gap-2 text-sm text-slate-500">
						<svg
							className="w-4 h-4 text-red-500 flex-shrink-0"
							fill="currentColor"
							viewBox="0 0 20 20"
						>
							<path
								fillRule="evenodd"
								d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
								clipRule="evenodd"
							/>
						</svg>
						<span className="font-medium">{match.venue}</span>
					</div>

					{/* AI Prediction Summary - Expandable */}
					{prediction && !isTBD && (
						<button
							onClick={(e) => {
								e.stopPropagation();
								setIsExpanded(!isExpanded);
							}}
							className="w-full flex items-center justify-between gap-2 px-3 py-2 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors focus:ring-4 focus:ring-purple-300 focus:outline-none"
							aria-expanded={isExpanded}
							aria-label={isExpanded ? "Skjul AI-analyse" : "Vis AI-analyse"}
						>
							<div className="flex items-center gap-2 flex-1 min-w-0">
								<svg
									className="w-4 h-4 text-purple-600 flex-shrink-0"
									fill="currentColor"
									viewBox="0 0 20 20"
								>
									<path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z" />
								</svg>
								<span className="text-xs font-semibold text-purple-900 truncate">
									AI spår:{" "}
									<span className="font-bold">{prediction.winner}</span> (
									{prediction.predictedHomeScore}-
									{prediction.predictedAwayScore})
								</span>
							</div>
							<svg
								className={`w-5 h-5 text-purple-600 flex-shrink-0 transition-transform ${isExpanded ? "rotate-180" : ""}`}
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									strokeLinecap="round"
									strokeLinejoin="round"
									strokeWidth={2}
									d="M19 9l-7 7-7-7"
								/>
							</svg>
						</button>
					)}
				</div>
			</div>

			{/* Expanded Detail View - Only shown when AI prediction is clicked */}
			{isExpanded && prediction && !isTBD && (
				<div className="border-t border-purple-200 px-6 py-6 bg-gradient-to-br from-purple-50 to-white">
					{/* Winner */}
					<div className="mb-6">
						<div className="text-xs font-bold text-purple-700 uppercase tracking-wider mb-2 flex items-center gap-2">
							<span>🏆</span>
							<span>{t("predictedWinner")}</span>
						</div>
						<div className="font-black text-2xl text-slate-900">
							{prediction.winner}{" "}
							<span className="text-lg text-purple-600">
								({prediction.predictedHomeScore}-{prediction.predictedAwayScore}
								)
							</span>
						</div>
					</div>

					{/* Win Probability Bar */}
					<div className="mb-6">
						<div className="flex justify-between items-center mb-3">
							<span className="text-xs font-bold text-purple-700 uppercase tracking-wider flex items-center gap-2">
								<span>📊</span>
								<span>{t("winProbability")}</span>
							</span>
							<span className="text-sm font-black text-purple-600">
								{(prediction.winProbability * 100).toFixed(0)}%
							</span>
						</div>
						<div className="w-full bg-slate-200 rounded-full h-4 overflow-hidden shadow-inner">
							<div
								className="bg-gradient-to-r from-purple-500 to-purple-600 h-4 rounded-full transition-all duration-500 shadow-md"
								style={{ width: `${prediction.winProbability * 100}%` }}
							/>
						</div>
					</div>

					{/* Confidence Badge */}
					{prediction.confidence && (
						<div className="mb-6">
							<span
								className={`inline-flex items-center gap-2 px-4 py-2 text-sm font-bold rounded-xl border-2 ${getConfidenceColor(
									prediction.confidence,
								)}`}
							>
								<span>{getConfidenceStars(prediction.confidence)}</span>
								<span>
									{t("confidence")}: {getConfidenceLabel(prediction.confidence)}
								</span>
							</span>
						</div>
					)}

					{/* Reasoning */}
					<div>
						<div className="text-xs font-bold text-purple-700 uppercase tracking-wider mb-3 flex items-center gap-2">
							<span>🤖</span>
							<span>{t("aiAnalysis")}</span>
						</div>
						<div className="text-sm text-slate-700 leading-relaxed bg-white p-4 rounded-lg border border-purple-100">
							{showFullReasoning ? reasoning : truncatedReasoning}
						</div>
						{shouldShowReadMore && (
							<button
								onClick={(e) => {
									e.stopPropagation();
									setShowFullReasoning(!showFullReasoning);
								}}
								className="mt-4 w-full px-4 py-3 bg-white hover:bg-purple-100 text-purple-700 font-bold text-sm rounded-xl border-2 border-purple-200 transition-all duration-300 min-h-[44px] flex items-center justify-center gap-2 focus:ring-4 focus:ring-purple-300 focus:outline-none"
								aria-expanded={showFullReasoning}
								aria-label={
									showFullReasoning
										? "Skjul full AI-analyse"
										: "Vis full AI-analyse"
								}
							>
								{showFullReasoning ? (
									<>
										<span aria-hidden="true">▲</span>
										<span>{tCommon("showLess")}</span>
									</>
								) : (
									<>
										<span aria-hidden="true">▼</span>
										<span>{tCommon("readMore")}</span>
									</>
								)}
							</button>
						)}
					</div>
				</div>
			)}

			{/* TBD Notice - Always visible if TBD */}
			{isExpanded && isTBD && (
				<div className="border-t border-yellow-200 px-6 py-4 bg-gradient-to-br from-yellow-50 to-white">
					<div className="flex items-center gap-3 text-yellow-800">
						<svg
							className="w-6 h-6 flex-shrink-0"
							fill="currentColor"
							viewBox="0 0 20 20"
						>
							<path
								fillRule="evenodd"
								d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
								clipRule="evenodd"
							/>
						</svg>
						<span className="text-sm font-bold">{t("tbdNotice")}</span>
					</div>
				</div>
			)}
		</div>
	);
}
