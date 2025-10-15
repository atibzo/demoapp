'use client';

import React, { useState } from 'react';

export interface AITooltipContent {
  setting: string;
  title: string;
  simpleExplanation: string;
  technicalDetails?: string;
  impact: 'low' | 'medium' | 'high';
  examples: {
    low?: { value: any; outcome: string };
    medium?: { value: any; outcome: string };
    high?: { value: any; outcome: string };
  };
  recommendations: {
    conservative?: any;
    balanced?: any;
    aggressive?: any;
  };
  relatedSettings?: string[];
}

interface AITooltipProps {
  content: AITooltipContent;
  children?: React.ReactNode;
}

export function AITooltip({ content, children }: AITooltipProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const impactColors = {
    low: 'text-green-700 bg-green-100',
    medium: 'text-amber-700 bg-amber-100',
    high: 'text-red-700 bg-red-100'
  };

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-blue-100 hover:bg-blue-200 text-blue-700 text-xs font-bold transition-all-smooth hover:scale-110"
        title="Learn more"
      >
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute left-0 top-full mt-2 w-96 max-w-[calc(100vw-2rem)] z-50 animate-fadeIn">
            <div className="rounded-xl border-2 border-blue-200 bg-white shadow-elevated p-4">
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <h4 className="text-sm font-bold text-slate-900">{content.title}</h4>
                <button 
                  onClick={() => setIsOpen(false)}
                  className="text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>

              {/* Simple Explanation */}
              <div className="mb-3">
                <div className="text-xs font-semibold text-slate-600 mb-1">📚 What is this?</div>
                <p className="text-sm text-slate-700 leading-relaxed">{content.simpleExplanation}</p>
              </div>

              {/* Impact Level */}
              <div className="mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-600">🎯 Impact:</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${impactColors[content.impact]}`}>
                    {content.impact.toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Examples */}
              {Object.keys(content.examples).length > 0 && (
                <div className="mb-3">
                  <div className="text-xs font-semibold text-slate-600 mb-2">📊 Examples:</div>
                  <div className="space-y-1.5">
                    {content.examples.low && (
                      <div className="text-xs bg-green-50 border border-green-200 rounded-lg p-2">
                        <span className="font-semibold text-green-900">Low ({JSON.stringify(content.examples.low.value)}):</span>
                        <span className="text-green-800 ml-1">{content.examples.low.outcome}</span>
                      </div>
                    )}
                    {content.examples.medium && (
                      <div className="text-xs bg-blue-50 border border-blue-200 rounded-lg p-2">
                        <span className="font-semibold text-blue-900">Medium ({JSON.stringify(content.examples.medium.value)}):</span>
                        <span className="text-blue-800 ml-1">{content.examples.medium.outcome}</span>
                      </div>
                    )}
                    {content.examples.high && (
                      <div className="text-xs bg-amber-50 border border-amber-200 rounded-lg p-2">
                        <span className="font-semibold text-amber-900">High ({JSON.stringify(content.examples.high.value)}):</span>
                        <span className="text-amber-800 ml-1">{content.examples.high.outcome}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {Object.keys(content.recommendations).length > 0 && (
                <div className="mb-3">
                  <div className="text-xs font-semibold text-slate-600 mb-2">💡 Recommendations:</div>
                  <div className="grid grid-cols-3 gap-2">
                    {content.recommendations.conservative !== undefined && (
                      <div className="text-center p-2 rounded-lg bg-green-50 border border-green-200">
                        <div className="text-xs font-semibold text-green-900">Conservative</div>
                        <div className="text-sm font-mono font-bold text-green-700">{JSON.stringify(content.recommendations.conservative)}</div>
                      </div>
                    )}
                    {content.recommendations.balanced !== undefined && (
                      <div className="text-center p-2 rounded-lg bg-blue-50 border border-blue-200">
                        <div className="text-xs font-semibold text-blue-900">Balanced ⭐</div>
                        <div className="text-sm font-mono font-bold text-blue-700">{JSON.stringify(content.recommendations.balanced)}</div>
                      </div>
                    )}
                    {content.recommendations.aggressive !== undefined && (
                      <div className="text-center p-2 rounded-lg bg-amber-50 border border-amber-200">
                        <div className="text-xs font-semibold text-amber-900">Aggressive</div>
                        <div className="text-sm font-mono font-bold text-amber-700">{JSON.stringify(content.recommendations.aggressive)}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Related Settings */}
              {content.relatedSettings && content.relatedSettings.length > 0 && (
                <div className="mb-3">
                  <div className="text-xs font-semibold text-slate-600 mb-1">🔗 Related Settings:</div>
                  <div className="flex flex-wrap gap-1">
                    {content.relatedSettings.map(setting => (
                      <span key={setting} className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                        {setting}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Technical Details Toggle */}
              {content.technicalDetails && (
                <div>
                  <button
                    onClick={() => setShowDetails(!showDetails)}
                    className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1"
                  >
                    <svg className={`w-3 h-3 transition-transform ${showDetails ? 'rotate-90' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                    {showDetails ? 'Hide' : 'Show'} Technical Details
                  </button>
                  {showDetails && (
                    <div className="mt-2 p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <p className="text-xs text-slate-700 leading-relaxed font-mono">{content.technicalDetails}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </>
      )}
      {children}
    </div>
  );
}

// Export tooltip content database
export const TOOLTIP_CONTENT: Record<string, AITooltipContent> = {
  universe_limit: {
    setting: 'universe_limit',
    title: 'Active Universe Limit',
    simpleExplanation: 'How many stocks to monitor simultaneously for trading opportunities. More stocks = more opportunities but higher resource usage.',
    technicalDetails: 'Maximum number of instruments subscribed via KiteTicker WebSocket. Each subscription consumes memory for storing snapshots and CPU for processing ticks. Optimal range depends on system resources and trading style.',
    impact: 'high',
    examples: {
      low: { value: 100, outcome: 'Focus on top liquid stocks, fast performance, conservative' },
      medium: { value: 300, outcome: 'Balanced coverage, recommended for most traders' },
      high: { value: 600, outcome: 'Comprehensive scanning, higher resource usage' }
    },
    recommendations: {
      conservative: 150,
      balanced: 300,
      aggressive: 500
    },
    relatedSettings: ['Pinned Symbols', 'Data Freshness', 'System Resources']
  },
  
  trend_weight: {
    setting: 'trend_weight',
    title: 'Trend Weight',
    simpleExplanation: 'How much importance to give to trend direction (EMA9 vs EMA21). Higher values favor strongly trending stocks.',
    technicalDetails: 'Scoring weight for trend factor calculated as normalized EMA9-EMA21 difference divided by ATR. Values >1.0 increase trend importance, <1.0 decrease it.',
    impact: 'medium',
    examples: {
      low: { value: 0.5, outcome: 'Accept weaker trends, more opportunities, higher risk' },
      medium: { value: 1.0, outcome: 'Standard trend filtering, balanced' },
      high: { value: 2.0, outcome: 'Only strong trends, fewer but cleaner signals' }
    },
    recommendations: {
      conservative: 1.5,
      balanced: 1.0,
      aggressive: 0.7
    },
    relatedSettings: ['Pullback Weight', 'VWAP Weight', 'Scoring Algorithm']
  },

  entry_window: {
    setting: 'entry_window',
    title: 'Entry Time Window',
    simpleExplanation: 'Time range during market hours when trades can be initiated. Narrower windows focus on specific market conditions.',
    technicalDetails: 'Defines active trading hours for signal generation. Signals outside this window are blocked. Affects opportunity count and risk exposure.',
    impact: 'high',
    examples: {
      low: { value: '13:00-14:30', outcome: 'Late day only, fewer opportunities, lower risk' },
      medium: { value: '11:00-15:10', outcome: 'Standard window, balanced' },
      high: { value: '09:30-15:15', outcome: 'Full day trading, maximum opportunities' }
    },
    recommendations: {
      conservative: { start: '11:00', end: '14:00' },
      balanced: { start: '11:00', end: '15:10' },
      aggressive: { start: '10:00', end: '15:15' }
    },
    relatedSettings: ['Signal Freshness', 'Universe Limit']
  },

  min_volx: {
    setting: 'min_volx',
    title: 'Minimum Volume Multiple',
    simpleExplanation: 'Required volume increase vs median. Higher values mean more active trading. 1.4 = 40% above normal volume.',
    technicalDetails: 'Compares current 1-minute volume to median 1-minute volume. Used as volume filter in scoring. Higher thresholds reduce false signals but miss some opportunities.',
    impact: 'medium',
    examples: {
      low: { value: 1.0, outcome: 'Accept normal volume, more signals' },
      medium: { value: 1.4, outcome: 'Require 40% volume spike, balanced' },
      high: { value: 2.0, outcome: 'Require 2x volume, fewer but stronger signals' }
    },
    recommendations: {
      conservative: 1.8,
      balanced: 1.4,
      aggressive: 1.0
    },
    relatedSettings: ['Volume Weight', 'Breakout Detection']
  },

  rr_target: {
    setting: 'rr_target',
    title: 'Risk:Reward Target',
    simpleExplanation: 'Minimum required reward vs risk ratio. 2.0 means profit target must be 2x larger than stop loss.',
    technicalDetails: 'Calculated as (TP2 - Entry) / (Entry - Stop). Used to filter low R:R setups. Higher values reduce trade frequency but improve win quality.',
    impact: 'high',
    examples: {
      low: { value: 1.2, outcome: 'Accept lower R:R, more trades' },
      medium: { value: 1.6, outcome: 'Standard risk management' },
      high: { value: 2.5, outcome: 'Only excellent R:R, fewer trades' }
    },
    recommendations: {
      conservative: 2.0,
      balanced: 1.6,
      aggressive: 1.2
    },
    relatedSettings: ['Stop Loss Multiplier', 'Take Profit Targets']
  },

  // ===== VOLUME CONFIGURATION =====
  
  volume_weight: {
    setting: 'volume_weight',
    title: 'Volume Weight (Scoring)',
    simpleExplanation: 'How much importance to give to volume in the scoring algorithm. Volume confirms price movements and indicates institutional participation.',
    technicalDetails: 'Scoring weight for volume factor. Calculated as current 1-min volume vs median volume, capped at 1.2x. Higher weights favor high-volume breakouts and ignore low-volume noise.',
    impact: 'high',
    examples: {
      low: { value: 0.3, outcome: 'Volume less important, more signals (including low-volume)' },
      medium: { value: 0.6, outcome: 'Balanced approach, filters some low-volume setups' },
      high: { value: 1.2, outcome: 'Only high-volume confirmations, institutional-grade signals' }
    },
    recommendations: {
      conservative: 1.0,
      balanced: 0.6,
      aggressive: 0.4
    },
    relatedSettings: ['Min Volume Multiple', 'Breakout Weight', 'Trend Weight']
  },

  min_volume_multiple: {
    setting: 'min_volume_multiple',
    title: 'Minimum Volume Multiple (VolX)',
    simpleExplanation: 'Required volume spike vs normal. 1.4 means current volume must be 40% higher than median. Filters out low-liquidity moves.',
    technicalDetails: 'Threshold for volume filter. Compares current 1-minute bar volume to rolling median 1-minute volume. Acts as hard cutoff - signals below this are rejected regardless of other factors. Critical for avoiding illiquid stocks.',
    impact: 'high',
    examples: {
      low: { value: 1.0, outcome: 'No volume filter, accept all volume levels (risky!)' },
      medium: { value: 1.4, outcome: 'Require 40% volume spike, standard filtering' },
      high: { value: 2.0, outcome: 'Require 100% volume spike (2x), very selective' }
    },
    recommendations: {
      conservative: 1.8,
      balanced: 1.4,
      aggressive: 1.1
    },
    relatedSettings: ['Volume Weight', 'Liquidity Filters', 'Universe Size']
  },

  volume_confirmation: {
    setting: 'volume_confirmation',
    title: 'Volume Confirmation Strategy',
    simpleExplanation: 'How to use volume in trade decisions. Volume should confirm price movements - high volume on breakouts good, high volume on pullbacks questionable.',
    technicalDetails: 'Strategy for incorporating volume into signal generation. Options: (1) Volume-weighted scoring, (2) Hard threshold filter, (3) Dynamic adjustment based on stock characteristics.',
    impact: 'medium',
    examples: {
      low: { value: 'none', outcome: 'Ignore volume completely (not recommended for intraday)' },
      medium: { value: 'filter', outcome: 'Use as threshold filter (standard approach)' },
      high: { value: 'weighted', outcome: 'Full integration in scoring (sophisticated)' }
    },
    recommendations: {
      conservative: 'weighted',
      balanced: 'filter',
      aggressive: 'filter'
    },
    relatedSettings: ['Min Volume Multiple', 'Volume Weight']
  },

  institutional_volume: {
    setting: 'institutional_volume',
    title: 'Institutional Volume Detection',
    simpleExplanation: 'Detect when big players (institutions, funds) are active. They move markets with large orders. Following institutional money improves success.',
    technicalDetails: 'Identifies unusually large volume spikes (>3x median) combined with tight spreads, indicating institutional participation. These moves tend to persist as institutions accumulate/distribute positions.',
    impact: 'medium',
    examples: {
      low: { value: 2.0, outcome: '2x spike = institutional, more signals' },
      medium: { value: 3.0, outcome: '3x spike = institutional, standard threshold' },
      high: { value: 4.0, outcome: '4x spike = institutional, very selective' }
    },
    recommendations: {
      conservative: 3.5,
      balanced: 3.0,
      aggressive: 2.5
    },
    relatedSettings: ['Min Volume Multiple', 'Volume Weight']
  }
};
