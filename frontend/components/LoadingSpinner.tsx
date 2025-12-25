/**
 * LoadingSpinner Component
 * 
 * Reusable loading indicator with skeleton placeholders
 * for different content types (cards, tables, text)
 */

'use client'

import { useTranslations } from 'next-intl'

type LoadingType = 'default' | 'card' | 'table' | 'bracket'

interface LoadingSpinnerProps {
  /** Type of content being loaded (affects skeleton structure) */
  type?: LoadingType
  /** Custom loading message */
  message?: string
  /** Show skeleton placeholders instead of spinner */
  skeleton?: boolean
}

export default function LoadingSpinner({
  type = 'default',
  message,
  skeleton = false,
}: LoadingSpinnerProps) {
  const t = useTranslations('common')

  // Default spinner (for general loading states)
  if (!skeleton || type === 'default') {
    return (
      <div className="flex flex-col items-center justify-center py-20 sm:py-32" role="status" aria-live="polite">
        <div className="relative">
          {/* Animated Soccer Ball Loader */}
          <div className="animate-spin rounded-full h-16 w-16 sm:h-20 sm:w-20 border-4 border-emerald-200 border-t-emerald-600 mb-6"></div>
          <div className="absolute inset-0 animate-ping rounded-full h-16 w-16 sm:h-20 sm:w-20 border-4 border-emerald-300/30"></div>
        </div>
        <p className="text-slate-800 font-bold text-base sm:text-lg">
          {message || t('loading')}
        </p>
        <p className="text-slate-600 text-xs sm:text-sm mt-2">
          {t('pleaseWait')}
        </p>
      </div>
    )
  }

  // Card skeleton (for GroupCard, MatchCard)
  if (type === 'card') {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6" role="status" aria-label={t('loading')}>
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="bg-white rounded-2xl p-6 border-2 border-slate-200 animate-pulse">
            {/* Header */}
            <div className="h-6 bg-slate-200 rounded-lg w-1/3 mb-4"></div>
            {/* Content rows */}
            {[1, 2, 3, 4].map((j) => (
              <div key={j} className="flex gap-4 mb-3">
                <div className="h-4 bg-slate-200 rounded w-8"></div>
                <div className="h-4 bg-slate-200 rounded flex-1"></div>
                <div className="h-4 bg-slate-200 rounded w-12"></div>
              </div>
            ))}
          </div>
        ))}
      </div>
    )
  }

  // Table skeleton (for group standings)
  if (type === 'table') {
    return (
      <div className="bg-white rounded-2xl p-6 border-2 border-slate-200 animate-pulse" role="status" aria-label={t('loading')}>
        {/* Table header */}
        <div className="flex gap-4 mb-4 pb-3 border-b border-slate-200">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-4 bg-slate-300 rounded flex-1"></div>
          ))}
        </div>
        {/* Table rows */}
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex gap-4 mb-3">
            <div className="h-4 bg-slate-200 rounded w-8"></div>
            <div className="h-4 bg-slate-200 rounded flex-1"></div>
            <div className="h-4 bg-slate-200 rounded w-12"></div>
            <div className="h-4 bg-slate-200 rounded w-12"></div>
            <div className="h-4 bg-slate-200 rounded w-12"></div>
          </div>
        ))}
      </div>
    )
  }

  // Bracket skeleton (for knockout bracket)
  if (type === 'bracket') {
    return (
      <div className="overflow-x-auto" role="status" aria-label={t('loading')}>
        <div className="min-w-max flex gap-8 p-6">
          {[1, 2, 3, 4].map((round) => (
            <div key={round} className="flex flex-col gap-4 min-w-[200px]">
              <div className="h-6 bg-slate-300 rounded w-32 mb-4 animate-pulse"></div>
              {Array.from({ length: Math.pow(2, 5 - round) }).map((_, i) => (
                <div key={i} className="bg-white rounded-xl p-4 border-2 border-slate-200 animate-pulse">
                  <div className="h-4 bg-slate-200 rounded w-3/4 mb-2"></div>
                  <div className="h-4 bg-slate-200 rounded w-2/3"></div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    )
  }

  return null
}
