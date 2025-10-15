# Settings Tab - Product Redesign Specification

## Executive Summary

**Problem**: Users are confused by separate Config and Policy tabs. They don't understand what each setting does or how settings interact. There's no guidance on optimal configurations.

**Solution**: Merge Config + Policy into a unified "Settings" tab with AI-powered tooltips, smart recommendations, and preset profiles.

**Impact**: 
- ⬆️ User confidence in configuration
- ⬇️ Support questions about settings
- ⬆️ Adoption of advanced features
- ⬆️ Trading performance through optimal configs

## User Personas

### 1. Beginner Trader (60% of users)
**Needs**: 
- Simple, guided setup
- Preset profiles
- Clear explanations
- Safe defaults

**Pain Points**:
- Overwhelmed by technical terms
- Afraid of breaking something
- Doesn't know what's "good"

### 2. Intermediate Trader (30% of users)
**Needs**:
- Fine-tune specific settings
- Understand trade-offs
- See impact of changes
- Quick access to common tweaks

**Pain Points**:
- Two tabs is confusing
- No feedback on changes
- Trial and error is risky

### 3. Advanced Trader (10% of users)
**Needs**:
- Full control
- Deep customization
- JSON editing
- Performance metrics

**Pain Points**:
- UI gets in the way
- Wants direct access

## Product Requirements

### Must Have (MVP)
1. ✅ Merge Config + Policy into single "Settings" tab
2. ✅ AI tooltips explaining each setting
3. ✅ Smart recommendations based on config
4. ✅ Organized into logical sections
5. ✅ Preset profiles (Conservative, Balanced, Aggressive)
6. ✅ Visual impact indicators
7. ✅ Validation with clear errors
8. ✅ Save/Reset/Export capabilities

### Should Have (V2)
- Settings search
- Change history
- A/B testing different configs
- Performance comparison
- Import/export configs

### Could Have (Future)
- AI auto-optimization
- Community presets
- Settings marketplace

## Information Architecture

### New Structure: "Settings" Tab

```
Settings (Unified Tab)
├── 🎯 Quick Setup (Preset Profiles)
│   ├── Conservative
│   ├── Balanced (Recommended)
│   └── Aggressive
│
├── 📊 Universe & Data
│   ├── Active Universe Limit (1-600)
│   ├── Pinned Symbols
│   ├── Exchange Preferences
│   └── Data Freshness
│
├── ⚙️ Trading Strategy
│   ├── Entry Window (time range)
│   ├── Scoring Weights
│   │   ├── Trend
│   │   ├── Pullback
│   │   ├── VWAP
│   │   ├── Breakout
│   │   └── Volume
│   └── Signal Thresholds
│
├── 🎲 Risk Management
│   ├── Position Sizing
│   ├── Stop Loss Rules
│   ├── Take Profit Targets
│   └── Risk Limits
│
├── 🔧 Advanced Options
│   ├── Regime Caps
│   ├── Exclude Patterns
│   ├── Custom Filters
│   └── JSON Editor (for power users)
│
└── 💾 Actions
    ├── Save Configuration
    ├── Reset to Defaults
    ├── Export/Import
    └── View Change History
```

## AI Tooltip System

### Architecture

```typescript
interface AITooltip {
  setting: string;
  title: string;
  simpleExplanation: string;  // For beginners
  technicalDetails: string;    // For advanced users
  impact: 'low' | 'medium' | 'high';
  examples: {
    low: { value: any; outcome: string };
    medium: { value: any; outcome: string };
    high: { value: any; outcome: string };
  };
  recommendations: {
    conservative: any;
    balanced: any;
    aggressive: any;
  };
  relatedSettings: string[];  // Which settings this affects
}
```

### Example Tooltips

#### Universe Limit
```
Title: "Active Universe Limit"

Simple: "How many stocks to monitor simultaneously for trading opportunities"

Technical: "Maximum number of instruments subscribed to via KiteTicker WebSocket. 
Higher values = more opportunities but increased data processing and memory usage."

Impact: HIGH

Examples:
- Low (100): "Focus on top liquid stocks, fast performance"
- Medium (300): "Balanced coverage, recommended for most users"
- High (600): "Comprehensive scanning, higher resource usage"

Recommendations:
- Conservative: 100-150
- Balanced: 250-350 ⭐
- Aggressive: 500-600

Related: Pinned Symbols, Data Freshness, System Resources
```

#### Trend Weight
```
Title: "Trend Weight"

Simple: "How much importance to give to trend direction (EMA9 vs EMA21)"

Technical: "Scoring weight for trend factor in algorithm. Higher values favor 
strongly trending stocks. Calculated as normalized EMA9-EMA21 difference."

Impact: MEDIUM

Examples:
- Low (0.5): "Accept weaker trends, more opportunities"
- Medium (1.0): "Standard trend filtering"
- High (2.0): "Only strong trends, fewer but cleaner signals"

Recommendations:
- Conservative: 1.5 (favor strong trends)
- Balanced: 1.0 (standard) ⭐
- Aggressive: 0.7 (accept more signals)

Related: Pullback Weight, Scoring Algorithm
```

## Smart Recommendations Engine

### When to Show Recommendations

1. **On Setting Change**
   - User changes Universe Limit → Suggest adjusting Staleness threshold
   - User increases Trend Weight → Suggest decreasing Volume Weight
   - User sets tight Entry Window → Suggest wider Signal Thresholds

2. **On Profile Detection**
   - System detects "Aggressive" pattern → Suggest Aggressive preset
   - System detects "Day Trading" pattern → Suggest optimal entry window
   - System detects "Swing Trading" pattern → Suggest looser thresholds

3. **On Performance Issues**
   - High memory usage → Suggest reducing Universe Limit
   - Missing opportunities → Suggest expanding Entry Window
   - Too many false signals → Suggest tightening thresholds

### Recommendation Format

```typescript
interface Recommendation {
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
```

### Example Recommendations

```typescript
{
  type: 'suggestion',
  priority: 'medium',
  title: '💡 Optimize for Day Trading',
  description: 'Your entry window (11:00-15:10) is wide. For day trading, consider narrowing to peak hours.',
  action: {
    label: 'Apply Optimization',
    settings: {
      entry_window: { start: '10:00', end: '14:00' }
    }
  },
  reason: 'Peak liquidity hours have tighter spreads and better fills',
  impact: 'Expected improvement: 15-20% better entry prices'
}
```

```typescript
{
  type: 'warning',
  priority: 'high',
  title: '⚠️ Universe Limit Too High',
  description: 'With 600 stocks and trend weight 2.0, you may miss opportunities due to strict filtering.',
  action: {
    label: 'Balance Settings',
    settings: {
      universe_limit: 400,
      weights: { trend: 1.2 }
    }
  },
  reason: 'Wide universe needs relaxed filters to find signals',
  impact: 'Expected: 30-40% more trading opportunities'
}
```

## Preset Profiles

### Conservative Profile
**Target User**: Risk-averse, prefers quality over quantity

```json
{
  "name": "Conservative",
  "description": "Focus on high-quality setups with strong confirmation",
  "universe_limit": 150,
  "pinned": ["NSE:NIFTY50INDEX", "NSE:BANKNIFTY"],
  "weights": {
    "trend": 1.5,
    "pullback": 1.0,
    "vwap": 1.2,
    "breakout": 0.8,
    "volume": 1.3
  },
  "thresholds": {
    "min_volx": 1.8,
    "vwap_reversion_max_dev": 0.4,
    "atr_mult_sl": 1.5,
    "rr_target": 2.0
  },
  "entry_window": {
    "start": "10:30",
    "end": "14:00"
  }
}
```

### Balanced Profile (Recommended)
**Target User**: Most users, good risk/reward

```json
{
  "name": "Balanced",
  "description": "Well-rounded approach for consistent returns",
  "universe_limit": 300,
  "pinned": [],
  "weights": {
    "trend": 1.0,
    "pullback": 0.8,
    "vwap": 0.8,
    "breakout": 0.7,
    "volume": 0.6
  },
  "thresholds": {
    "min_volx": 1.4,
    "vwap_reversion_max_dev": 0.6,
    "atr_mult_sl": 1.2,
    "rr_target": 1.6
  },
  "entry_window": {
    "start": "11:00",
    "end": "15:10"
  }
}
```

### Aggressive Profile
**Target User**: Experienced traders, more signals

```json
{
  "name": "Aggressive",
  "description": "Maximum opportunities with active management",
  "universe_limit": 500,
  "pinned": [],
  "weights": {
    "trend": 0.7,
    "pullback": 0.6,
    "vwap": 0.5,
    "breakout": 1.0,
    "volume": 0.8
  },
  "thresholds": {
    "min_volx": 1.0,
    "vwap_reversion_max_dev": 0.8,
    "atr_mult_sl": 1.0,
    "rr_target": 1.2
  },
  "entry_window": {
    "start": "09:30",
    "end": "15:15"
  }
}
```

## UX Wireframes

### Main Settings View

```
┌─────────────────────────────────────────────────────────────┐
│ ⚙️ Settings                                    [Export] [?] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🎯 Quick Setup - Choose a preset to get started            │
│ ┌──────────┬──────────────┬──────────┐                    │
│ │Conservative│   Balanced   │ Aggressive│                   │
│ │  🛡️       │   ⭐ Rec     │   ⚡      │                   │
│ │ [Select]  │  [Select]    │ [Select]  │                   │
│ └──────────┴──────────────┴──────────┘                    │
│                                                             │
│ 📊 Universe & Data                                          │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ Active Universe Limit [ℹ️ AI Tooltip]               │   │
│ │ [300] [━━━━━━━━━━━━━━━━━━━━━━]  300/600 🟢      │   │
│ │                                                     │   │
│ │ 💡 Smart Recommendation:                            │   │
│ │ With 300 stocks, consider adjusting entry window   │   │
│ │ to 10:00-14:30 for optimal coverage                │   │
│ │ [Apply Optimization]                                │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
│ ⚙️ Trading Strategy                                         │
│ [Collapsed - Click to expand]                              │
│                                                             │
│ 🎲 Risk Management                                          │
│ [Collapsed - Click to expand]                              │
│                                                             │
│ [💾 Save All Changes]  [🔄 Reset to Defaults]              │
└─────────────────────────────────────────────────────────────┘
```

### AI Tooltip Component

```
┌─────────────────────────────────────────────────┐
│ Trend Weight                              [×]  │
├─────────────────────────────────────────────────┤
│                                                 │
│ 📚 What is this?                                │
│ Controls how much importance the algorithm     │
│ gives to trend direction (EMA crossover).      │
│                                                 │
│ 🎯 Impact: MEDIUM                               │
│ Affects: Number of signals, Trade quality      │
│                                                 │
│ 📊 Examples:                                    │
│ • Low (0.5): More signals, accept weak trends  │
│ • Medium (1.0): Balanced ⭐                     │
│ • High (2.0): Fewer signals, strong trends     │
│                                                 │
│ 💡 Recommendations:                             │
│ • Conservative: 1.5                             │
│ • Balanced: 1.0 ⭐                              │
│ • Aggressive: 0.7                               │
│                                                 │
│ 🔗 Related Settings:                            │
│ Pullback Weight, Volume Weight                 │
│                                                 │
│ [Show Technical Details]                        │
└─────────────────────────────────────────────────┘
```

### Smart Recommendation Card

```
┌─────────────────────────────────────────────────┐
│ 💡 Smart Recommendation                   [×]  │
├─────────────────────────────────────────────────┤
│ Optimize for Your Trading Style                │
│                                                 │
│ We detected you're using:                      │
│ • Wide universe (600 stocks)                   │
│ • High trend weight (1.8)                      │
│ • Tight entry window (11:00-13:00)             │
│                                                 │
│ ⚠️ This combination may cause:                  │
│ • Missed opportunities (strict filtering)      │
│ • Uneven signal distribution                   │
│                                                 │
│ 💊 Suggested Fix:                               │
│ Expand entry window to 10:00-14:30             │
│ OR reduce trend weight to 1.2                  │
│                                                 │
│ Expected Impact:                                │
│ 📈 +35% more trading opportunities              │
│ ⏱️ Better signal timing                         │
│                                                 │
│ [Apply Suggestion] [Dismiss] [Learn More]      │
└─────────────────────────────────────────────────┘
```

## Technical Implementation Plan

### Phase 1: Component Architecture (Week 1)
1. Create AITooltip component
2. Create RecommendationEngine
3. Create PresetProfileSelector
4. Create unified Settings layout

### Phase 2: Data & Logic (Week 2)
1. Define all tooltip content
2. Build recommendation rules
3. Implement preset profiles
4. Add validation logic

### Phase 3: Integration (Week 3)
1. Merge Config + Policy tabs
2. Wire up all components
3. Add save/load functionality
4. Implement export/import

### Phase 4: Polish & Testing (Week 4)
1. User testing with all personas
2. Performance optimization
3. Documentation
4. Launch

## Success Metrics

### Key Performance Indicators (KPIs)

1. **User Engagement**
   - Settings page views: Target +200%
   - Time on settings page: Target 3-5 minutes (vs 30 seconds)
   - Settings changes per session: Target 5-8 (vs 1-2)

2. **User Confidence**
   - % using presets: Target 70% (beginners)
   - % customizing after preset: Target 40% (growth)
   - % using advanced options: Target 15% (power users)

3. **Support Impact**
   - Settings-related support tickets: Target -60%
   - "How do I configure" questions: Target -80%
   - User satisfaction score: Target 4.5/5

4. **Trading Performance**
   - % of users with optimal configs: Target 75%
   - Avg signals per user: Target +30%
   - User-reported profitability: Target +25%

## Rollout Plan

### Phase 1: Beta (Week 5)
- Release to 10% of users
- Collect feedback
- Monitor metrics
- Iterate quickly

### Phase 2: Gradual Rollout (Week 6-7)
- 25% → 50% → 75% → 100%
- Monitor performance at each stage
- Roll back if issues

### Phase 3: Education (Week 8)
- Tutorial videos
- Blog posts
- Webinars
- In-app tour

## Risks & Mitigation

### Risk 1: User Confusion During Transition
**Mitigation**: 
- Keep old tabs hidden but accessible via flag
- Show migration guide on first visit
- Preserve all existing configs

### Risk 2: Performance Issues with AI Tooltips
**Mitigation**:
- Lazy load tooltip content
- Cache recommendations
- Optimize rendering

### Risk 3: Overwhelming Advanced Users
**Mitigation**:
- Add "Simple/Advanced" mode toggle
- Keep JSON editor for power users
- Allow disabling recommendations

## Future Enhancements

### V2 (3 months)
- Settings search
- Change history with rollback
- A/B testing framework
- Performance dashboard

### V3 (6 months)
- AI auto-optimization
- Community presets
- Machine learning recommendations
- Integration with backtesting

### V4 (12 months)
- Settings marketplace
- Custom strategy builder
- Visual strategy designer
- Multi-account configs

## Conclusion

This redesign transforms settings from a confusing, technical configuration into an intelligent, guided experience that:
- ✅ Reduces cognitive load
- ✅ Increases user confidence
- ✅ Improves trading performance
- ✅ Scales from beginner to advanced

**Next Steps**: Approve spec → Start Phase 1 implementation

---

**Product Manager**: [Your Name]  
**Date**: 2025-10-15  
**Status**: Ready for Engineering Review
