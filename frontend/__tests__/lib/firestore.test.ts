import type { DocumentSnapshot } from "firebase/firestore";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fetchLatestPredictions } from "../../lib/firestore";

// Mock firebase/firestore
vi.mock("firebase/firestore", () => ({
	getFirestore: vi.fn(),
	doc: vi.fn(),
	getDoc: vi.fn(),
}));

// Helper to create mock document snapshots
function createMockDocSnapshot(
	exists: boolean,
	data?: Record<string, unknown>,
): Partial<DocumentSnapshot> {
	return {
		exists: () => exists,
		data: () => data,
	};
}

describe("firestore lib", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		vi.useFakeTimers();
	});

	it("fetches predictions/latest document", async () => {
		const { getDoc } = await import("firebase/firestore");
		const mockData = {
			updatedAt: new Date().toISOString(),
			groups: {},
			bracket: [],
		};
		vi.mocked(getDoc).mockResolvedValueOnce(
			createMockDocSnapshot(true, mockData) as DocumentSnapshot,
		);

		const result = await fetchLatestPredictions();
		// The function transforms data, so we check key properties instead
		expect(result).not.toBeNull();
		expect(result?.updatedAt).toEqual(mockData.updatedAt);
		expect(result?.groups).toEqual({});
		expect(result?.bracket).toEqual([]);
	});

	it("returns null when document doesn't exist", async () => {
		const { getDoc } = await import("firebase/firestore");
		vi.mocked(getDoc).mockResolvedValueOnce(
			createMockDocSnapshot(false) as DocumentSnapshot,
		);

		// Force refresh to skip cache
		const result = await fetchLatestPredictions({ forceRefresh: true });
		expect(result).toBeNull();
	});

	it("detects stale data and triggers refresh", async () => {
		const { getDoc } = await import("firebase/firestore");

		// Set current time
		const now = new Date("2026-06-25T12:00:00Z");
		vi.setSystemTime(now);

		// Stale data: 3 hours old (threshold is 2 hours)
		const staleTime = new Date("2026-06-25T09:00:00Z").toISOString();
		const mockData = {
			updatedAt: staleTime,
			groups: {},
		};

		vi.mocked(getDoc).mockResolvedValueOnce(
			createMockDocSnapshot(true, mockData) as DocumentSnapshot,
		);

		// Mock global fetch for backend refresh
		global.fetch = vi.fn().mockResolvedValueOnce({ ok: true });

		// Force refresh to skip cache and fetch from Firestore
		await fetchLatestPredictions({ forceRefresh: true });

		// Should have triggered refresh (uses /api/update-tournament endpoint)
		expect(global.fetch).toHaveBeenCalledWith(
			expect.stringContaining("/api/update-tournament"),
			expect.objectContaining({ method: "POST" }),
		);
	});

	it("does NOT trigger refresh when data is fresh", async () => {
		const { getDoc } = await import("firebase/firestore");

		const now = new Date("2026-06-25T12:00:00Z");
		vi.setSystemTime(now);

		// Fresh data: 1 hour old
		const freshTime = new Date("2026-06-25T11:00:00Z").toISOString();
		const mockData = {
			updatedAt: freshTime,
		};

		vi.mocked(getDoc).mockResolvedValueOnce(
			createMockDocSnapshot(true, mockData) as DocumentSnapshot,
		);

		global.fetch = vi.fn();

		await fetchLatestPredictions();

		expect(global.fetch).not.toHaveBeenCalled();
	});
});
