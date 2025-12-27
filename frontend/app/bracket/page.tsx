/**
 * Bracket page - Display knockout bracket with winner path visualization.
 *
 * Features:
 * - Fetch predictions using fetchLatestPredictions()
 * - Display knockout bracket using BracketView component
 * - Show tournament progression
 * - Display AI summary and favorites below bracket
 * - Show dark horses section
 * - Zoom controls for mobile viewing
 */

"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import BracketView from "../../components/BracketView";
import { fetchLatestPredictions } from "../../lib/firestore";
import type { TournamentSnapshot } from "../../lib/types";

export default function BracketPage() {
	const [snapshot, setSnapshot] = useState<TournamentSnapshot | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [zoomLevel, setZoomLevel] = useState(100);

	const loadPredictions = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const data = await fetchLatestPredictions();
			setSnapshot(data);
		} catch (err) {
			setError(
				err instanceof Error ? err.message : "Failed to fetch predictions",
			);
		} finally {
			setLoading(false);
		}
	}, []);

	const handleZoomIn = useCallback(() => {
		setZoomLevel((prev) => Math.min(prev + 10, 150));
	}, []);

	const handleZoomOut = useCallback(() => {
		setZoomLevel((prev) => Math.max(prev - 10, 50));
	}, []);

	const handleResetZoom = useCallback(() => {
		setZoomLevel(100);
	}, []);

	useEffect(() => {
		loadPredictions();
	}, [loadPredictions]);

	// Keyboard shortcuts for zoom controls
	useEffect(() => {
		const handleKeyDown = (e: KeyboardEvent) => {
			if ((e.ctrlKey || e.metaKey) && e.key === "+") {
				e.preventDefault();
				handleZoomIn();
			}
			if ((e.ctrlKey || e.metaKey) && e.key === "-") {
				e.preventDefault();
				handleZoomOut();
			}
			if ((e.ctrlKey || e.metaKey) && e.key === "0") {
				e.preventDefault();
				handleResetZoom();
			}
		};
		window.addEventListener("keydown", handleKeyDown);
		return () => window.removeEventListener("keydown", handleKeyDown);
	}, [handleZoomIn, handleZoomOut, handleResetZoom]);

	// Find predicted winner (Final match winner)
	const getPredictedWinner = () => {
		if (!snapshot) return null;
		const finalMatch = snapshot.bracket.find((m) => m.stageId === 7); // Stage 7 = Final
		return finalMatch?.prediction?.winner || null;
	};

	const predictedWinner = getPredictedWinner();

	return (
		<div className="min-h-screen bg-slate-50">
			{/* Header */}
			<header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
					<div className="flex flex-col sm:flex-row justify-between items-center gap-4">
						<div>
							<h1 className="text-3xl font-black tracking-tight text-slate-900">
								Knockout Bracket
							</h1>
							<p className="text-sm text-slate-600 mt-1">
								Tournament progression from Round of 32 to Final
							</p>
						</div>
						<Link
							href="/"
							className="px-4 py-2 min-h-[44px] flex items-center bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-colors focus:ring-4 focus:ring-slate-300 focus:outline-none"
							aria-label="Tilbake til hjemmesiden"
						>
							← Back to Home
						</Link>
					</div>

					{/* Zoom Controls */}
					{snapshot && !loading && (
						<div className="mt-6 flex items-center justify-center gap-4 bg-slate-100 p-3 rounded-xl border border-slate-200">
							<span className="text-sm font-semibold text-slate-700">
								Zoom:
							</span>
							<button
								onClick={handleZoomOut}
								disabled={zoomLevel <= 50}
								className="px-4 py-2 min-w-[44px] min-h-[44px] flex items-center justify-center bg-white border border-slate-300 rounded-lg text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:ring-4 focus:ring-slate-300 focus:outline-none"
								aria-label="Zoom ut"
							>
								-
							</button>
							<span
								className="text-sm font-bold text-blue-600 w-12 text-center"
								aria-live="polite"
							>
								{zoomLevel}%
							</span>
							<button
								onClick={handleZoomIn}
								disabled={zoomLevel >= 150}
								className="px-4 py-2 min-w-[44px] min-h-[44px] flex items-center justify-center bg-white border border-slate-300 rounded-lg text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:ring-4 focus:ring-slate-300 focus:outline-none"
								aria-label="Zoom inn"
							>
								+
							</button>
							<button
								onClick={handleResetZoom}
								className="px-4 py-2 min-h-[44px] bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors focus:ring-4 focus:ring-blue-300 focus:outline-none"
								aria-label="Tilbakestill zoom"
							>
								Reset
							</button>
						</div>
					)}
				</div>
			</header>

			{/* Main Content */}
			<main className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-12">
				{/* Loading State - Skeleton Screens */}
				{loading && (
					<div className="space-y-8">
						{/* Predicted winner banner skeleton */}
						<div className="bg-slate-200 rounded-3xl p-8 animate-pulse">
							<div className="h-6 bg-slate-300 rounded w-48 mx-auto mb-4" />
							<div className="h-12 bg-slate-300 rounded w-64 mx-auto mb-2" />
							<div className="h-4 bg-slate-300 rounded w-96 mx-auto" />
						</div>

						{/* Bracket skeleton */}
						<div className="flex gap-8 overflow-hidden">
							{[1, 2, 3, 4, 5].map((i) => (
								<div key={i} className="flex flex-col gap-6 w-80 flex-shrink-0">
									<div className="h-8 bg-slate-200 rounded w-32 mx-auto animate-pulse" />
									{[1, 2].map((j) => (
										<div
											key={j}
											className="bg-white rounded-2xl border-2 border-slate-100 p-6 animate-pulse"
										>
											<div className="h-4 bg-slate-200 rounded mb-4" />
											<div className="h-20 bg-slate-100 rounded" />
										</div>
									))}
								</div>
							))}
						</div>
					</div>
				)}

				{/* Error State */}
				{error && !loading && (
					<div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
						<div className="text-red-600 font-semibold mb-2">
							Error loading bracket
						</div>
						<p className="text-red-500 text-sm mb-4">{error}</p>
						<button
							onClick={loadPredictions}
							className="px-4 py-2 min-h-[44px] bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors focus:ring-4 focus:ring-red-300 focus:outline-none"
							aria-label="Prøv å laste inn bracket på nytt"
						>
							Try Again
						</button>
					</div>
				)}

				{/* Bracket Visualization */}
				{snapshot && !loading && (
					<>
						{/* Predicted Winner Banner */}
						{predictedWinner && (
							<div className="mb-8 bg-gradient-to-r from-yellow-400 via-yellow-500 to-yellow-600 rounded-3xl p-8 text-center shadow-2xl border-4 border-yellow-300">
								<div className="text-sm font-bold text-yellow-900 uppercase tracking-wider mb-2">
									AI Predicted Champion
								</div>
								<div className="text-5xl font-black text-white mb-2">
									🏆 {predictedWinner} 🏆
								</div>
								<div className="text-yellow-100 text-sm font-semibold">
									Based on AI analysis of team statistics and tournament
									progression
								</div>
							</div>
						)}

						{/* Bracket with Zoom */}
						<div
							className="transition-transform duration-300 origin-top"
							style={{ transform: `scale(${zoomLevel / 100})` }}
						>
							<BracketView bracket={snapshot.bracket} />
						</div>

						{/* AI Analysis Section */}
						<div className="mt-16 space-y-8">
							{/* Tournament Summary */}
							<div className="bg-gradient-to-br from-white to-slate-50 rounded-3xl p-8 border border-slate-200 shadow-lg">
								<h2 className="text-2xl font-bold mb-4 text-slate-900">
									AI Tournament Analysis
								</h2>
								<p className="text-slate-700 text-lg leading-relaxed mb-6">
									{snapshot.aiSummary}
								</p>

								{/* Favorites & Dark Horses */}
								<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
									{/* Favorites */}
									<div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm">
										<div className="flex items-center gap-2 mb-4">
											<span className="text-3xl">⭐</span>
											<h3 className="text-lg font-bold text-blue-900">
												Tournament Favorites
											</h3>
										</div>
										<ul className="space-y-2">
											{snapshot.favorites.map((team, index) => (
												<li
													key={team}
													className="flex items-center gap-3 p-3 bg-blue-50 rounded-xl border border-blue-100"
												>
													<span className="text-sm font-bold text-blue-600 w-6">
														#{index + 1}
													</span>
													<span className="font-semibold text-slate-900">
														{team}
													</span>
												</li>
											))}
										</ul>
									</div>

									{/* Dark Horses */}
									<div className="bg-white p-6 rounded-2xl border border-amber-100 shadow-sm">
										<div className="flex items-center gap-2 mb-4">
											<span className="text-3xl">🐴</span>
											<h3 className="text-lg font-bold text-amber-900">
												Dark Horses
											</h3>
										</div>
										<ul className="space-y-2">
											{snapshot.darkHorses.map((team, index) => (
												<li
													key={team}
													className="flex items-center gap-3 p-3 bg-amber-50 rounded-xl border border-amber-100"
												>
													<span className="text-sm font-bold text-amber-600 w-6">
														#{index + 1}
													</span>
													<span className="font-semibold text-slate-900">
														{team}
													</span>
												</li>
											))}
										</ul>
									</div>
								</div>
							</div>

							{/* Prediction Methodology */}
							<div className="bg-blue-50 rounded-2xl p-6 border border-blue-200">
								<h3 className="text-lg font-bold text-blue-900 mb-3">
									How AI Predictions Work
								</h3>
								<div className="space-y-2 text-sm text-blue-800">
									<p>
										<strong>📊 Data Sources:</strong> Team statistics from
										API-Football including recent form, xG (expected goals),
										clean sheets, and head-to-head records
									</p>
									<p>
										<strong>🤖 AI Model:</strong> Google Gemini AI analyzes
										aggregated statistics to predict match outcomes with
										confidence levels
									</p>
									<p>
										<strong>⚖️ FIFA Rules:</strong> Standings calculated using
										official FIFA tiebreaker rules including Fair Play Points
									</p>
									<p>
										<strong>🔄 Updates:</strong> Predictions refresh daily
										during tournament to incorporate latest results
									</p>
								</div>
							</div>
						</div>
					</>
				)}
			</main>

			{/* Footer */}
			<footer className="mt-20 border-t border-slate-200 bg-white py-12 text-center">
				<div className="max-w-md mx-auto px-4">
					<p className="text-slate-900 font-bold text-2xl mb-2">VM KULA 2026</p>
					<p className="text-slate-500 text-sm mb-6">
						AI-powered World Cup predictions using Gemini AI
					</p>
					<p className="text-xs text-slate-400 uppercase tracking-wider">
						Unofficial Companion App
					</p>
				</div>
			</footer>
		</div>
	);
}
