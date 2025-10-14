'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4">
          <div className="text-sm font-semibold text-red-800">Something went wrong</div>
          <div className="text-xs text-red-600 mt-1">
            {this.state.error?.message || 'An unexpected error occurred'}
          </div>
          <button 
            className="mt-2 rounded-lg bg-red-600 px-3 py-1 text-xs text-white hover:bg-red-700"
            onClick={() => this.setState({ hasError: false, error: undefined })}
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;