'use client';

import React from 'react';

export interface Recommendation {
  id: string;
  type: 'optimization' | 'warning' | 'suggestion';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  action: {
    label: string;
    settings: Record<string, any>;
  };
  reason: string;
  impact: string;
}

interface SmartRecommendationsProps {
  currentSettings: any;
  onApplyRecommendation: (settings: Record<string, any>) => void;
  onDismiss: (id: string) => void;
}

export function SmartRecommendations({ currentSettings, onApplyRecommendation, onDismiss }: SmartRecommendationsProps) {
  const recommendations = generateRecommendations(currentSettings);
  
  if (recommendations.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      {recommendations.map(rec => (
        <RecommendationCard 
          key={rec.id}
          recommendation={rec}
          onApply={() => onApplyRecommendation(rec.action.settings)}
          onDismiss={() => onDismiss(rec.id)}
        />
      ))}
    </div>
  );
}

function RecommendationCard({ 
  recommendation, 
  onApply, 
  onDismiss 
}: { 
  recommendation: Recommendation; 
  onApply: () => void;
  onDismiss: () => void;
}) {
  const typeConfig = {
    optimization: {
      icon: '💡',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-900',
      buttonColor: 'bg-blue-600 hover:bg-blue-700'
    },
    warning: {
      icon: '⚠️',
      bgColor: 'bg-amber-50',
      borderColor: 'border-amber-200',
      textColor: 'text-amber-900',
      buttonColor: 'bg-amber-600 hover:bg-amber-700'
    },
    suggestion: {
      icon: '✨',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
      textColor: 'text-purple-900',
      buttonColor: 'bg-purple-600 hover:bg-purple-700'
    }
  };

  const config = typeConfig[recommendation.type];

  return (
    <div className={`rounded-xl border-2 ${config.borderColor} ${config.bgColor} p-4 animate-fadeIn`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{config.icon}</span>
          <h4 className={`text-sm font-bold ${config.textColor}`}>{recommendation.title}</h4>
        </div>
        <button 
          onClick={onDismiss}
          className="text-slate-400 hover:text-slate-600 transition-colors"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>

      <p className={`text-sm ${config.textColor} mb-3`}>{recommendation.description}</p>

      <div className="mb-3">
        <div className={`text-xs font-semibold ${config.textColor} mb-1`}>Why this matters:</div>
        <p className="text-xs text-slate-700">{recommendation.reason}</p>
      </div>

      <div className="mb-3">
        <div className={`text-xs font-semibold ${config.textColor} mb-1`}>Expected impact:</div>
        <p className="text-xs text-slate-700">{recommendation.impact}</p>
      </div>

      <div className="flex gap-2">
        <button
          onClick={onApply}
          className={`flex-1 rounded-lg ${config.buttonColor} text-white px-4 py-2 text-sm font-semibold transition-all-smooth hover-lift`}
        >
          {recommendation.action.label}
        </button>
        <button
          onClick={onDismiss}
          className="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 text-sm font-semibold hover:bg-slate-50 transition-colors"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}

// Recommendation generation logic
function generateRecommendations(settings: any): Recommendation[] {
  const recommendations: Recommendation[] = [];
  
  // Rule 1: High universe + tight entry window
  if (settings.universe_limit >= 500 && settings.entry_window) {
    const start = settings.entry_window.start || '11:00';
    const end = settings.entry_window.end || '15:10';
    const startMin = parseInt(start.split(':')[0]) * 60 + parseInt(start.split(':')[1]);
    const endMin = parseInt(end.split(':')[0]) * 60 + parseInt(end.split(':')[1]);
    const windowSize = endMin - startMin;
    
    if (windowSize < 180) { // Less than 3 hours
      recommendations.push({
        id: 'wide-universe-narrow-window',
        type: 'optimization',
        priority: 'medium',
        title: 'Optimize Universe vs Entry Window',
        description: `You're monitoring ${settings.universe_limit} stocks but only trading ${Math.floor(windowSize / 60)}h ${windowSize % 60}m per day. This limits opportunities.`,
        action: {
          label: 'Widen Entry Window',
          settings: {
            entry_window: { start: '10:00', end: '15:10' }
          }
        },
        reason: 'Wide universe needs wider trading window to capture signals from all stocks',
        impact: '📈 +35-45% more trading opportunities without adding more stocks'
      });
    }
  }

  // Rule 2: High trend weight + low volume weight
  if (settings.weights?.trend >= 1.5 && settings.weights?.volume < 0.6) {
    recommendations.push({
      id: 'balance-trend-volume',
      type: 'suggestion',
      priority: 'low',
      title: 'Balance Trend and Volume Weights',
      description: 'High trend weight (≥1.5) with low volume weight (<0.6) may miss volume-confirmed breakouts.',
      action: {
        label: 'Balance Weights',
        settings: {
          weights: {
            ...settings.weights,
            trend: 1.2,
            volume: 0.8
          }
        }
      },
      reason: 'Volume confirmation strengthens trend signals and reduces false breakouts',
      impact: '📊 15-20% reduction in false signals, better trade quality'
    });
  }

  // Rule 3: Aggressive R:R with conservative universe
  if (settings.thresholds?.rr_target >= 2.0 && settings.universe_limit < 200) {
    recommendations.push({
      id: 'rr-universe-mismatch',
      type: 'warning',
      priority: 'high',
      title: 'Risk:Reward vs Universe Size Mismatch',
      description: `High R:R target (${settings.thresholds.rr_target}) with only ${settings.universe_limit} stocks severely limits trade opportunities.`,
      action: {
        label: 'Expand Universe',
        settings: {
          universe_limit: 300
        }
      },
      reason: 'High R:R requirements need larger universe to find enough qualifying setups',
      impact: '📈 +60-80% more trade opportunities while maintaining quality'
    });
  }

  // Rule 4: All-day trading suggestion for beginners
  if (settings.entry_window?.start <= '09:30' && settings.entry_window?.end >= '15:00') {
    if (!settings.weights || settings.weights.trend === 1.0) { // Default weights = likely beginner
      recommendations.push({
        id: 'full-day-trading',
        type: 'suggestion',
        priority: 'medium',
        title: 'Consider Focused Trading Hours',
        description: 'Trading all day (9:30-15:00+) can be exhausting and spreads reduce quality. Peak hours often provide better opportunities.',
        action: {
          label: 'Use Peak Hours',
          settings: {
            entry_window: { start: '10:30', end: '14:30' }
          }
        },
        reason: 'Peak trading hours (10:30-14:30) have higher liquidity and tighter spreads',
        impact: '⚡ 20-25% better average entry prices, reduced monitoring time'
      });
    }
  }

  // Rule 5: Low universe with default settings
  if (settings.universe_limit < 150 && settings.weights?.trend === 1.0) {
    recommendations.push({
      id: 'conservative-defaults',
      type: 'optimization',
      priority: 'low',
      title: 'Conservative Setup Detected',
      description: 'You\'re using a small universe with default weights. This is very conservative.',
      action: {
        label: 'Use Balanced Preset',
        settings: {
          universe_limit: 300,
          weights: {
            trend: 1.0,
            pullback: 0.8,
            vwap: 0.8,
            breakout: 0.7,
            volume: 0.6
          }
        }
      },
      reason: 'Balanced preset provides better opportunity/quality ratio for most traders',
      impact: '📊 +50-70% more opportunities while maintaining good signal quality'
    });
  }

  // Rule 6: Very tight VWAP deviation
  if (settings.thresholds?.vwap_reversion_max_dev < 0.4) {
    recommendations.push({
      id: 'tight-vwap-deviation',
      type: 'warning',
      priority: 'medium',
      title: 'VWAP Deviation Too Tight',
      description: `VWAP deviation limit of ${settings.thresholds.vwap_reversion_max_dev} is very restrictive. May miss good setups.`,
      action: {
        label: 'Relax to 0.6',
        settings: {
          thresholds: {
            ...settings.thresholds,
            vwap_reversion_max_dev: 0.6
          }
        }
      },
      reason: 'Slight VWAP deviation is normal in trending markets and provides entry opportunities',
      impact: '📈 +30-40% more trade opportunities without compromising quality'
    });
  }

  // Rule 7: Low volume weight (dangerous for intraday)
  if (settings.weights?.volume < 0.4) {
    recommendations.push({
      id: 'low-volume-weight',
      type: 'warning',
      priority: 'high',
      title: '⚠️ Volume Weight Too Low for Intraday',
      description: `Volume weight of ${settings.weights.volume} is very low. Intraday trading NEEDS volume confirmation to avoid false breakouts and illiquid moves.`,
      action: {
        label: 'Increase Volume Weight',
        settings: {
          weights: {
            ...settings.weights,
            volume: 0.6
          }
        }
      },
      reason: 'Volume confirms price movements. Without it, you\'ll get trapped in low-liquidity moves with wide spreads',
      impact: '🛡️ 40-50% reduction in false breakouts and slippage costs'
    });
  }

  // Rule 8: High volume weight + tight volume threshold
  if (settings.weights?.volume >= 1.0 && settings.thresholds?.min_volx >= 1.8) {
    recommendations.push({
      id: 'double-volume-filter',
      type: 'optimization',
      priority: 'medium',
      title: 'Volume Double-Filtering Detected',
      description: `Both high volume weight (${settings.weights.volume}) and strict threshold (${settings.thresholds.min_volx}x) are active. This may be too restrictive.`,
      action: {
        label: 'Balance Volume Filters',
        settings: {
          weights: {
            ...settings.weights,
            volume: 0.7
          },
          thresholds: {
            ...settings.thresholds,
            min_volx: 1.4
          }
        }
      },
      reason: 'Use either scoring weight OR hard threshold for volume, not both aggressively',
      impact: '📈 +25-35% more opportunities while maintaining volume quality'
    });
  }

  // Rule 9: No volume filter (very risky)
  if (settings.thresholds?.min_volx <= 1.0) {
    recommendations.push({
      id: 'no-volume-filter',
      type: 'warning',
      priority: 'high',
      title: '🚨 No Volume Filter - High Risk!',
      description: `Minimum volume multiple of ${settings.thresholds.min_volx} means accepting normal/low volume. This is VERY risky for intraday - you\'ll get stuck in illiquid moves.`,
      action: {
        label: 'Add Volume Filter',
        settings: {
          thresholds: {
            ...settings.thresholds,
            min_volx: 1.4
          }
        }
      },
      reason: 'Low volume = wide spreads, poor fills, difficulty exiting positions',
      impact: '🛡️ 60-70% reduction in stuck trades and slippage costs'
    });
  }

  // Rule 10: Aggressive + low volume protection
  if (settings.universe_limit >= 400 && settings.thresholds?.min_volx < 1.3 && settings.weights?.volume < 0.5) {
    recommendations.push({
      id: 'aggressive-needs-volume',
      type: 'warning',
      priority: 'high',
      title: 'Aggressive Setup Needs Volume Protection',
      description: `With ${settings.universe_limit} stocks, low volume filter (${settings.thresholds.min_volx}x), and weak volume weight (${settings.weights.volume}), you\'re exposed to illiquid signals.`,
      action: {
        label: 'Add Volume Protection',
        settings: {
          thresholds: {
            ...settings.thresholds,
            min_volx: 1.4
          },
          weights: {
            ...settings.weights,
            volume: 0.6
          }
        }
      },
      reason: 'Large universe includes less liquid stocks - need strong volume filters',
      impact: '🛡️ 50-60% fewer illiquid trades, much better execution quality'
    });
  }

  // Rule 11: Volume weight vs breakout weight imbalance
  if (settings.weights?.breakout >= 1.0 && settings.weights?.volume < 0.5) {
    recommendations.push({
      id: 'breakout-without-volume',
      type: 'suggestion',
      priority: 'medium',
      title: 'Breakouts Need Volume Confirmation',
      description: `High breakout weight (${settings.weights.breakout}) but low volume weight (${settings.weights.volume}). Breakouts without volume often fail.`,
      action: {
        label: 'Add Volume to Breakouts',
        settings: {
          weights: {
            ...settings.weights,
            volume: 0.8
          }
        }
      },
      reason: 'Volume-confirmed breakouts have 2-3x better success rate than low-volume breakouts',
      impact: '📈 30-40% improvement in breakout trade success rate'
    });
  }

  // Sort by priority
  const priorityOrder = { high: 0, medium: 1, low: 2 };
  recommendations.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

  return recommendations.slice(0, 3); // Show max 3 recommendations
}
