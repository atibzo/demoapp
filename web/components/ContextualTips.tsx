'use client';

import React, { useState, useEffect } from 'react';
import { API } from '@/lib/api';

interface Tip {
  title: string;
  description: string;
  type: 'info' | 'warning' | 'tip' | 'insight';
  priority: 'high' | 'medium' | 'low';
}

interface ContextualTipsProps {
  contextType: string;
  data: any;
  userLevel?: 'beginner' | 'intermediate' | 'advanced';
  className?: string;
}

export function ContextualTips({ contextType, data, userLevel = 'intermediate', className = '' }: ContextualTipsProps) {
  const [tips, setTips] = useState<Tip[]>([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    loadTips();
  }, [contextType, data, userLevel]);

  async function loadTips() {
    if (!data || Object.keys(data).length === 0) return;
    
    try {
      setLoading(true);
      const response = await fetch(`${API}/api/contextual/tips`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context_type: contextType, data, user_level: userLevel }),
      });
      
      if (response.ok) {
        const result = await response.json();
        setTips(result.data?.tips || []);
      }
    } catch (error) {
      console.error('Failed to load contextual tips:', error);
    } finally {
      setLoading(false);
    }
  }

  if (!tips.length && !loading) return null;

  const getIconForType = (type: string) => {
    switch (type) {
      case 'warning':
        return (
          <svg className="w-5 h-5 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'insight':
        return (
          <svg className="w-5 h-5 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
            <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
          </svg>
        );
      case 'tip':
        return (
          <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5 text-slate-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const getBgColorForType = (type: string) => {
    switch (type) {
      case 'warning': return 'bg-amber-50 border-amber-200';
      case 'insight': return 'bg-purple-50 border-purple-200';
      case 'tip': return 'bg-blue-50 border-blue-200';
      default: return 'bg-slate-50 border-slate-200';
    }
  };

  return (
    <div className={`rounded-2xl border border-slate-200 bg-white shadow-card overflow-hidden ${className}`}>
      <div 
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
          <span className="font-semibold text-slate-800">AI Tips & Insights</span>
          {loading && (
            <svg className="animate-spin w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
        </div>
        <svg 
          className={`w-5 h-5 text-slate-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
      
      {expanded && (
        <div className="p-4 pt-0 space-y-2">
          {tips.map((tip, idx) => (
            <div 
              key={idx} 
              className={`rounded-xl border p-3 ${getBgColorForType(tip.type)} animate-fadeIn`}
              style={{ animationDelay: `${idx * 50}ms` }}
            >
              <div className="flex items-start gap-2">
                {getIconForType(tip.type)}
                <div className="flex-1">
                  <div className="font-semibold text-sm text-slate-800">{tip.title}</div>
                  <div className="text-xs text-slate-600 mt-1">{tip.description}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


interface TooltipProps {
  content: string;
  children: React.ReactNode;
  className?: string;
}

export function Tooltip({ content, children, className = '' }: TooltipProps) {
  const [visible, setVisible] = useState(false);

  if (!content) return <>{children}</>;

  return (
    <div className={`relative inline-block ${className}`}>
      <div
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
        className="cursor-help"
      >
        {children}
      </div>
      {visible && (
        <div className="absolute z-50 bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-slate-900 text-white text-xs rounded-lg shadow-lg max-w-xs animate-fadeIn">
          {content}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
            <div className="border-8 border-transparent border-t-slate-900"></div>
          </div>
        </div>
      )}
    </div>
  );
}


interface ExplainableMetricProps {
  label: string;
  value: any;
  metricName: string;
  context?: any;
  className?: string;
}

export function ExplainableMetric({ label, value, metricName, context = {}, className = '' }: ExplainableMetricProps) {
  const [explanation, setExplanation] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);

  async function loadExplanation() {
    if (explanation || loading) {
      setShowExplanation(!showExplanation);
      return;
    }
    
    try {
      setLoading(true);
      const response = await fetch(`${API}/api/contextual/explain-metric`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metric_name: metricName, value, context }),
      });
      
      if (response.ok) {
        const result = await response.json();
        setExplanation(result.data?.explanation || 'No explanation available');
        setShowExplanation(true);
      }
    } catch (error) {
      console.error('Failed to load explanation:', error);
      setExplanation('Unable to load explanation');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={`${className}`}>
      <div className="flex items-center gap-2">
        <span className="text-slate-600 text-sm">{label}:</span>
        <span className="font-semibold text-slate-900">{value}</span>
        <button
          onClick={loadExplanation}
          className="text-indigo-500 hover:text-indigo-700 transition-colors"
          title="Explain this metric"
        >
          {loading ? (
            <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
          )}
        </button>
      </div>
      {showExplanation && explanation && (
        <div className="mt-2 p-3 bg-indigo-50 border border-indigo-200 rounded-lg text-xs text-slate-700 animate-fadeIn">
          {explanation}
        </div>
      )}
    </div>
  );
}


interface IndicatorInfoProps {
  indicator: string;
  simple?: boolean;
}

export function IndicatorInfo({ indicator, simple = false }: IndicatorInfoProps) {
  const [explanation, setExplanation] = useState<string>('');
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState(false);

  async function loadExplanation() {
    if (explanation) {
      setVisible(!visible);
      return;
    }
    
    try {
      setLoading(true);
      const response = await fetch(
        `${API}/api/contextual/explain-indicator?indicator=${encodeURIComponent(indicator)}&simple=${simple}`
      );
      
      if (response.ok) {
        const result = await response.json();
        setExplanation(result.data?.explanation || 'No explanation available');
        setVisible(true);
      }
    } catch (error) {
      console.error('Failed to load indicator explanation:', error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={loadExplanation}
      className="inline-flex items-center gap-1 text-slate-500 hover:text-indigo-600 transition-colors text-xs"
      title={`Learn about ${indicator}`}
    >
      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
      </svg>
      {loading && (
        <svg className="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
      )}
      {visible && explanation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 animate-fadeIn" onClick={() => setVisible(false)}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-md mx-4 p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-lg text-slate-900">{indicator}</h3>
              <button onClick={() => setVisible(false)} className="text-slate-400 hover:text-slate-600">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
            <div className="text-sm text-slate-700 leading-relaxed">
              {explanation}
            </div>
          </div>
        </div>
      )}
    </button>
  );
}
