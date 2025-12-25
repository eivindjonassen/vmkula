import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fetchLatestPredictions } from '../../lib/firestore'

// Mock firebase/firestore
vi.mock('firebase/firestore', () => ({
  getFirestore: vi.fn(),
  doc: vi.fn(),
  getDoc: vi.fn(),
}))

describe('firestore lib', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  it('fetches predictions/latest document', async () => {
    const { getDoc } = await import('firebase/firestore')
    const mockData = {
      updatedAt: new Date().toISOString(),
      groups: {},
      bracket: [],
    }
    vi.mocked(getDoc).mockResolvedValueOnce({
      exists: () => true,
      data: () => mockData,
    } as any)

    const result = await fetchLatestPredictions()
    expect(result).toEqual(mockData)
  })

  it('returns null when document doesn\'t exist', async () => {
    const { getDoc } = await import('firebase/firestore')
    vi.mocked(getDoc).mockResolvedValueOnce({
      exists: () => false,
    } as any)

    const result = await fetchLatestPredictions()
    expect(result).toBeNull()
  })

  it('detects stale data and triggers refresh', async () => {
    const { getDoc } = await import('firebase/firestore')
    
    // Set current time
    const now = new Date('2026-06-25T12:00:00Z')
    vi.setSystemTime(now)
    
    // Stale data: 3 hours old (threshold is 2 hours)
    const staleTime = new Date('2026-06-25T09:00:00Z').toISOString()
    const mockData = {
      updatedAt: staleTime,
      groups: {},
    }
    
    vi.mocked(getDoc).mockResolvedValueOnce({
      exists: () => true,
      data: () => mockData,
    } as any)

    // Mock global fetch for backend refresh
    global.fetch = vi.fn().mockResolvedValueOnce({ ok: true })

    await fetchLatestPredictions()

    // Should have triggered refresh
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/update-predictions'),
      expect.objectContaining({ method: 'POST' })
    )
  })

  it('does NOT trigger refresh when data is fresh', async () => {
    const { getDoc } = await import('firebase/firestore')
    
    const now = new Date('2026-06-25T12:00:00Z')
    vi.setSystemTime(now)
    
    // Fresh data: 1 hour old
    const freshTime = new Date('2026-06-25T11:00:00Z').toISOString()
    const mockData = {
      updatedAt: freshTime,
    }
    
    vi.mocked(getDoc).mockResolvedValueOnce({
      exists: () => true,
      data: () => mockData,
    } as any)

    global.fetch = vi.fn()

    await fetchLatestPredictions()

    expect(global.fetch).not.toHaveBeenCalled()
  })
})
