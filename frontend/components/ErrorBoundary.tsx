/**
 * ErrorBoundary Component
 * 
 * React Error Boundary for catching and displaying React errors gracefully
 * Provides fallback UI and error reporting capabilities
 */

'use client'

import React, { Component, ReactNode } from 'react'

interface ErrorBoundaryProps {
  /** Child components to render */
  children: ReactNode
  /** Custom fallback UI (optional) */
  fallback?: ReactNode
  /** Callback fired when an error occurs */
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
}

/**
 * ErrorBoundary Component
 * 
 * Usage:
 * ```tsx
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 */
export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to console (in production, send to error tracking service)
    console.error('ErrorBoundary caught an error:', error, errorInfo)

    this.setState({
      error,
      errorInfo,
    })

    // Call optional error callback
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default fallback UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 p-4">
          <div className="max-w-2xl w-full bg-white rounded-2xl sm:rounded-3xl p-8 sm:p-12 border-2 border-red-300 shadow-2xl">
            {/* Error Icon */}
            <div className="flex justify-center mb-6">
              <div className="bg-gradient-to-br from-red-500 to-red-600 p-4 rounded-full">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-12 w-12 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
            </div>

            {/* Error Message */}
            <h1 className="text-2xl sm:text-3xl font-black text-red-800 text-center mb-4">
              Oops! Something went wrong
            </h1>
            <p className="text-slate-700 text-center mb-8">
              We encountered an unexpected error while rendering this page. Don&apos;t worry, our team has been notified.
            </p>

            {/* Error Details (Development Mode) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="bg-red-50 border-2 border-red-200 rounded-xl p-4 mb-6 overflow-auto">
                <h2 className="text-sm font-bold text-red-800 mb-2">Error Details (Development Only)</h2>
                <pre className="text-xs text-red-700 whitespace-pre-wrap font-mono">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={this.handleReset}
                className="px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-xl font-bold hover:from-red-600 hover:to-red-700 transition-all duration-300 shadow-lg hover:scale-105 transform"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-6 py-3 bg-gradient-to-r from-slate-500 to-slate-600 text-white rounded-xl font-bold hover:from-slate-600 hover:to-slate-700 transition-all duration-300 shadow-lg hover:scale-105 transform"
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
