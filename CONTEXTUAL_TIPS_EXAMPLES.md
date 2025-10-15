# Contextual Tips - Usage Examples

This document provides practical examples of how to use the contextual tips system in your trading application.

## Example 1: Basic Contextual Tips Display

```tsx
import { ContextualTips } from '@/components/ContextualTips';

function TradingView() {
  const [analysisData, setAnalysisData] = useState(null);
  
  return (
    <div>
      <ContextualTips 
        contextType="analyst"
        data={analysisData}
        userLevel="intermediate"
      />
    </div>
  );
}
```

## Example 2: Explainable Metrics in a Dashboard

```tsx
import { ExplainableMetric } from '@/components/ContextualTips';

function MetricsDashboard({ data }) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <ExplainableMetric 
        label="RSI"
        value={data.rsi}
        metricName="RSI14"
        context={{ symbol: data.symbol, trend: data.trend }}
      />
      
      <ExplainableMetric 
        label="Confidence"
        value={`${(data.confidence * 100).toFixed(0)}%`}
        metricName="confidence"
        context={{ 
          decision: data.decision,
          signal_strength: data.signal_strength 
        }}
      />
      
      <ExplainableMetric 
        label="ATR"
        value={data.atr.toFixed(2)}
        metricName="ATR14"
        context={{ 
          volatility: data.volatility,
          price: data.price 
        }}
      />
    </div>
  );
}
```

## Example 3: Indicator Information in Chart Legend

```tsx
import { IndicatorInfo } from '@/components/ContextualTips';

function ChartLegend() {
  return (
    <div className="flex gap-4 text-sm">
      <div className="flex items-center gap-2">
        <div className="w-8 h-1 bg-blue-500"></div>
        <span>EMA 9</span>
        <IndicatorInfo indicator="EMA" simple={true} />
      </div>
      
      <div className="flex items-center gap-2">
        <div className="w-8 h-1 bg-purple-500"></div>
        <span>EMA 21</span>
      </div>
      
      <div className="flex items-center gap-2">
        <div className="w-8 h-1 bg-amber-500"></div>
        <span>VWAP</span>
        <IndicatorInfo indicator="VWAP" simple={true} />
      </div>
      
      <div className="flex items-center gap-2">
        <div className="w-8 h-1 bg-green-500"></div>
        <span>Volume</span>
        <IndicatorInfo indicator="Volume" simple={true} />
      </div>
    </div>
  );
}
```

## Example 4: Decision Explanation Button

```tsx
import { API } from '@/lib/api';

function DecisionCard({ analysis }) {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  
  async function explainDecision() {
    setLoading(true);
    try {
      const response = await fetch(`${API}/api/contextual/explain-decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(analysis),
      });
      
      if (response.ok) {
        const result = await response.json();
        setExplanation(result.data);
      }
    } finally {
      setLoading(false);
    }
  }
  
  return (
    <div className="rounded-lg border p-4">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-lg">{analysis.decision}</h3>
        <button 
          onClick={explainDecision}
          className="text-indigo-600 hover:text-indigo-800 text-sm"
          disabled={loading}
        >
          {loading ? 'Loading...' : 'Explain Why'}
        </button>
      </div>
      
      {explanation && (
        <div className="mt-4 space-y-2 text-sm">
          <div>
            <strong>Why {analysis.decision}:</strong>
            <p className="text-gray-700">{explanation.why_this_decision}</p>
          </div>
          <div>
            <strong>Confidence:</strong>
            <p className="text-gray-700">{explanation.confidence_explanation}</p>
          </div>
          <div>
            <strong>What to Watch:</strong>
            <p className="text-gray-700">{explanation.what_to_watch}</p>
          </div>
          <div>
            <strong>Risk Factors:</strong>
            <p className="text-gray-700">{explanation.risk_factors}</p>
          </div>
          <div>
            <strong>Next Steps:</strong>
            <p className="text-gray-700">{explanation.next_steps}</p>
          </div>
        </div>
      )}
    </div>
  );
}
```

## Example 5: Smart Q&A Feature

```tsx
import { API } from '@/lib/api';

function SmartAssistant({ currentData }) {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  
  async function askQuestion() {
    if (!question.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API}/api/contextual/smart-explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: question,
          context: currentData
        }),
      });
      
      if (response.ok) {
        const result = await response.json();
        setAnswer(result.data.answer);
      }
    } finally {
      setLoading(false);
    }
  }
  
  return (
    <div className="rounded-lg border p-4 bg-white">
      <h3 className="font-bold mb-3">Ask AI Assistant</h3>
      <div className="flex gap-2">
        <input 
          type="text"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && askQuestion()}
          placeholder="Ask about the data..."
          className="flex-1 border rounded px-3 py-2 text-sm"
        />
        <button 
          onClick={askQuestion}
          disabled={loading}
          className="px-4 py-2 bg-indigo-600 text-white rounded text-sm"
        >
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </div>
      
      {answer && (
        <div className="mt-3 p-3 bg-indigo-50 border border-indigo-200 rounded text-sm">
          <strong>Answer:</strong>
          <p className="mt-1 text-gray-700">{answer}</p>
        </div>
      )}
      
      <div className="mt-3 text-xs text-gray-500">
        <strong>Example questions:</strong>
        <ul className="mt-1 space-y-1">
          <li>• What does this RSI value mean?</li>
          <li>• Is this good volume?</li>
          <li>• Should I be concerned about the ATR?</li>
          <li>• What's the significance of this EMA crossover?</li>
        </ul>
      </div>
    </div>
  );
}
```

## Example 6: Context Analysis Panel

```tsx
import { API } from '@/lib/api';

function ContextAnalysisPanel({ snapshotData }) {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    loadInsights();
  }, [snapshotData]);
  
  async function loadInsights() {
    if (!snapshotData) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API}/api/contextual/analyze-context`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: snapshotData,
          data_type: 'snapshot'
        }),
      });
      
      if (response.ok) {
        const result = await response.json();
        setInsights(result.data);
      }
    } finally {
      setLoading(false);
    }
  }
  
  if (loading) return <div>Analyzing...</div>;
  if (!insights) return null;
  
  return (
    <div className="rounded-lg border p-4 bg-white space-y-3">
      <div>
        <h3 className="font-bold text-sm text-gray-500 uppercase">Summary</h3>
        <p className="text-sm mt-1">{insights.summary}</p>
      </div>
      
      <div>
        <h3 className="font-bold text-sm text-gray-500 uppercase">Key Insights</h3>
        <ul className="text-sm mt-1 space-y-1">
          {insights.key_insights.map((insight, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-blue-500">•</span>
              <span>{insight}</span>
            </li>
          ))}
        </ul>
      </div>
      
      {insights.warnings.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded p-3">
          <h3 className="font-bold text-sm text-amber-800">⚠️ Warnings</h3>
          <ul className="text-sm mt-1 space-y-1">
            {insights.warnings.map((warning, i) => (
              <li key={i} className="text-amber-700">{warning}</li>
            ))}
          </ul>
        </div>
      )}
      
      {insights.tips.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded p-3">
          <h3 className="font-bold text-sm text-blue-800">💡 Tips</h3>
          <ul className="text-sm mt-1 space-y-1">
            {insights.tips.map((tip, i) => (
              <li key={i} className="text-blue-700">{tip}</li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Market Condition: <strong>{insights.market_condition}</strong></span>
        <span>Confidence: <strong className="uppercase">{insights.confidence_level}</strong></span>
      </div>
    </div>
  );
}
```

## Example 7: Tooltip Usage

```tsx
import { Tooltip } from '@/components/ContextualTips';

function MetricCard() {
  return (
    <div className="p-4 border rounded">
      <Tooltip content="Risk-to-Reward ratio shows potential profit vs potential loss. Higher is better.">
        <div className="text-sm text-gray-600 cursor-help">
          R:R Ratio
        </div>
      </Tooltip>
      <div className="text-2xl font-bold mt-1">1:2.5</div>
    </div>
  );
}
```

## Example 8: Progressive Disclosure

```tsx
function TradingMetrics({ data }) {
  return (
    <div className="space-y-2">
      {/* Simple metric */}
      <div className="flex items-center justify-between">
        <span>Price</span>
        <span className="font-bold">₹{data.price}</span>
      </div>
      
      {/* Explainable metric with info */}
      <ExplainableMetric 
        label="RSI"
        value={data.rsi}
        metricName="RSI14"
        context={{ price: data.price, trend: data.trend }}
      />
      
      {/* Indicator with learn more */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span>Bollinger Bands</span>
          <IndicatorInfo indicator="Bollinger Bands" simple={true} />
        </div>
        <span className="font-mono text-sm">
          {data.bb_lower.toFixed(2)} - {data.bb_upper.toFixed(2)}
        </span>
      </div>
    </div>
  );
}
```

## API Usage Patterns

### Pattern 1: On-Demand Explanation

```javascript
// Load explanation only when user clicks
async function explainOnClick(metric, value, context) {
  const response = await fetch(`${API}/api/contextual/explain-metric`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ metric_name: metric, value, context }),
  });
  
  if (response.ok) {
    const result = await response.json();
    return result.data.explanation;
  }
}
```

### Pattern 2: Batch Loading with Cache

```javascript
// Load multiple explanations, cache handles duplicates
async function loadAllExplanations(metrics) {
  const promises = metrics.map(m => 
    fetch(`${API}/api/contextual/explain-metric`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        metric_name: m.name,
        value: m.value,
        context: m.context
      }),
    })
  );
  
  const results = await Promise.all(promises);
  return Promise.all(results.map(r => r.json()));
}
```

### Pattern 3: Real-time Context Updates

```javascript
// Update contextual tips as data changes
useEffect(() => {
  const updateTips = async () => {
    const response = await fetch(`${API}/api/contextual/tips`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        context_type: 'analyst',
        data: currentSnapshot,
        user_level: userPreferences.level
      }),
    });
    
    if (response.ok) {
      const result = await response.json();
      setTips(result.data.tips);
    }
  };
  
  updateTips();
}, [currentSnapshot, userPreferences.level]);
```

## Best Practices

### 1. **Progressive Enhancement**
Start with basic metrics, add explanations progressively:
```tsx
// Basic
<div>RSI: {rsi}</div>

// Enhanced
<ExplainableMetric label="RSI" value={rsi} metricName="RSI14" />

// Full context
<ExplainableMetric 
  label="RSI" 
  value={rsi} 
  metricName="RSI14"
  context={{ symbol, trend, price, volume }}
/>
```

### 2. **User-Centric Design**
Adapt to user level:
```tsx
const userLevel = userPreferences.experience || 'intermediate';

<ContextualTips 
  contextType="analyst"
  data={analysisData}
  userLevel={userLevel}
/>
```

### 3. **Performance Optimization**
Use caching effectively:
```javascript
// Cache key includes all relevant context
// Same query = instant response from cache
const cacheKey = `${metric}:${value}:${JSON.stringify(context)}`;
```

### 4. **Error Handling**
Always provide fallbacks:
```tsx
try {
  const explanation = await loadExplanation();
  setExplanation(explanation);
} catch (error) {
  setExplanation('Unable to load explanation. Please try again.');
  console.error(error);
}
```

### 5. **Accessibility**
Make explanations accessible:
```tsx
<button
  onClick={loadExplanation}
  aria-label="Explain this metric"
  title="Click to learn more about RSI"
>
  <InfoIcon />
</button>
```

## Common Use Cases

1. **Learning Mode**: Show all indicator info by default
2. **Quick Reference**: Tooltips on hover
3. **Deep Dive**: Full explanations on click
4. **Contextual Help**: AI assistant for questions
5. **Decision Support**: Explain why decisions were made
6. **Risk Awareness**: Highlight warnings automatically
7. **Performance Review**: Analyze historical decisions

## Tips for Implementation

- Start with `IndicatorInfo` for quick wins
- Add `ContextualTips` to main views
- Use `ExplainableMetric` for complex metrics
- Implement smart Q&A for power users
- Monitor cache hit rates
- Adjust rate limits based on usage
- Collect feedback on explanation quality
