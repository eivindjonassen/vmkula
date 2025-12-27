/**
 * ConnectionStatus Component
 *
 * Displays real-time connection status indicator
 * Shows offline/online state with smooth animations
 */

"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

export default function ConnectionStatus() {
	const t = useTranslations("common");
	const [isOnline, setIsOnline] = useState(() =>
		typeof window !== "undefined" ? navigator.onLine : true,
	);
	const [showOffline, setShowOffline] = useState(false);

	useEffect(() => {
		// Sync with current online status if it changed during mount
		if (navigator.onLine !== isOnline) {
			setIsOnline(navigator.onLine);
		}

		// Event handlers
		const handleOnline = () => {
			setIsOnline(true);
			setShowOffline(false);
		};

		const handleOffline = () => {
			setIsOnline(false);
			setShowOffline(true);
		};

		// Listen for online/offline events
		window.addEventListener("online", handleOnline);
		window.addEventListener("offline", handleOffline);

		return () => {
			window.removeEventListener("online", handleOnline);
			window.removeEventListener("offline", handleOffline);
		};
	}, []);

	// Only show indicator when offline or briefly when coming back online
	if (!showOffline && isOnline) {
		return null;
	}

	return (
		<div
			className={`fixed top-20 right-4 z-50 transition-all duration-500 ${
				isOnline ? "translate-y-0 opacity-100" : "translate-y-0 opacity-100"
			}`}
			role="status"
			aria-live="polite"
		>
			<div
				className={`flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg backdrop-blur-md transition-colors ${
					isOnline
						? "bg-emerald-500/90 text-white"
						: "bg-red-500/90 text-white animate-pulse"
				}`}
			>
				{/* Status Icon */}
				{isOnline ? (
					<svg
						xmlns="http://www.w3.org/2000/svg"
						className="h-5 w-5"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							strokeLinecap="round"
							strokeLinejoin="round"
							strokeWidth={2}
							d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
				) : (
					<svg
						xmlns="http://www.w3.org/2000/svg"
						className="h-5 w-5"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							strokeLinecap="round"
							strokeLinejoin="round"
							strokeWidth={2}
							d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414"
						/>
					</svg>
				)}

				{/* Status Text */}
				<span className="text-sm font-bold">
					{isOnline ? t("backOnline") : t("offline")}
				</span>
			</div>
		</div>
	);
}
