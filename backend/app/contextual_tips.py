"""
Contextual Tips & Explanations Module
Provides AI-driven insights and explanations about trading data
"""
import os
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from .rl import redis_client

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4")


def _first_text_from_response(resp) -> str:
    """Extract text from OpenAI response"""
    txt = (getattr(resp, "output_text", None) or "").strip()
    if txt:
        return txt
    for attr in ("output", "content", "data"):
        part = getattr(resp, attr, None)
        if not part:
            continue
        try:
            if hasattr(part, "__iter__"):
                for p in part:
                    t = getattr(p, "text", None)
                    if t:
                        return (t or "").strip()
        except Exception:
            pass
    return ""


def explain_metric(metric_name: str, value: Any, context: Dict[str, Any]) -> str:
    """
    Explain what a specific metric means in the current context.
    
    Args:
        metric_name: Name of the metric (e.g., "RSI", "ATR", "confidence")
        value: Current value of the metric
        context: Additional context data
    
    Returns:
        Human-readable explanation of what the metric means
    """
    r = redis_client()
    cache_key = f"explain:v1:{metric_name}:{value}:{hash(json.dumps(context, sort_keys=True))}"
    cached = r.get(cache_key)
    if cached:
        return cached
    
    prompt = f"""Explain what the trading metric "{metric_name}" means in simple terms.

Current Value: {value}
Context: {json.dumps(context, indent=2)}

Provide a brief, educational explanation (2-3 sentences) that:
1. Defines what this metric measures
2. Explains what the current value indicates
3. Gives actionable insight for a trader

Keep it simple and practical."""

    try:
        resp = client.responses.create(
            model=MODEL,
            input=prompt,
            max_output_tokens=150,
            temperature=0.3,
        )
        text = _first_text_from_response(resp)
    except Exception:
        text = ""
    
    if text:
        r.setex(cache_key, 600, text)  # Cache for 10 minutes
    return text


def analyze_data_context(data: Dict[str, Any], data_type: str = "snapshot") -> Dict[str, Any]:
    """
    Analyze the overall context of trading data and provide insights.
    
    Args:
        data: Trading data (snapshot, bars, analysis, etc.)
        data_type: Type of data being analyzed
    
    Returns:
        Dictionary with insights, warnings, and tips
    """
    r = redis_client()
    cache_key = f"context:v1:{data_type}:{hash(json.dumps(data, sort_keys=True))}"
    cached = r.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass
    
    prompt = f"""Analyze this trading data and provide contextual insights.

Data Type: {data_type}
Data: {json.dumps(data, indent=2)}

Return a JSON object with:
{{
    "summary": "Brief overview of what this data shows",
    "key_insights": ["insight 1", "insight 2", "insight 3"],
    "warnings": ["warning 1", "warning 2"] (if any risks detected),
    "tips": ["actionable tip 1", "actionable tip 2"],
    "market_condition": "description of market condition",
    "confidence_level": "high|medium|low"
}}

Focus on practical, actionable insights for traders."""

    try:
        resp = client.responses.create(
            model=MODEL,
            input=prompt,
            response_format={"type": "json_object"},
            max_output_tokens=400,
            temperature=0.2,
        )
        txt = _first_text_from_response(resp)
        if txt:
            result = json.loads(txt)
            r.setex(cache_key, 300, json.dumps(result))  # Cache for 5 minutes
            return result
    except Exception:
        pass
    
    # Fallback response
    return {
        "summary": "Data analysis in progress",
        "key_insights": [],
        "warnings": [],
        "tips": [],
        "market_condition": "Unknown",
        "confidence_level": "low"
    }


def explain_decision(analysis: Dict[str, Any]) -> Dict[str, str]:
    """
    Explain why a particular trading decision was made.
    
    Args:
        analysis: Analysis result with decision, confidence, etc.
    
    Returns:
        Detailed explanation of the decision
    """
    r = redis_client()
    cache_key = f"decision:v1:{hash(json.dumps(analysis, sort_keys=True))}"
    cached = r.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass
    
    decision = analysis.get("decision", "WAIT")
    confidence = analysis.get("confidence", 0)
    
    prompt = f"""Explain this trading decision in clear, educational terms.

Analysis: {json.dumps(analysis, indent=2)}

Provide a JSON response with:
{{
    "why_this_decision": "Clear explanation of why {decision} was chosen",
    "confidence_explanation": "What the {confidence} confidence level means",
    "what_to_watch": "Key factors to monitor",
    "risk_factors": "Potential risks to be aware of",
    "next_steps": "What a trader should do next"
}}

Be educational and actionable."""

    try:
        resp = client.responses.create(
            model=MODEL,
            input=prompt,
            response_format={"type": "json_object"},
            max_output_tokens=350,
            temperature=0.2,
        )
        txt = _first_text_from_response(resp)
        if txt:
            result = json.loads(txt)
            r.setex(cache_key, 180, json.dumps(result))  # Cache for 3 minutes
            return result
    except Exception:
        pass
    
    return {
        "why_this_decision": "Analysis based on technical indicators",
        "confidence_explanation": "Confidence reflects signal strength",
        "what_to_watch": "Monitor price action and volume",
        "risk_factors": "Market volatility may affect outcomes",
        "next_steps": "Review and validate before acting"
    }


def get_contextual_tips(
    context_type: str,
    data: Dict[str, Any],
    user_level: str = "intermediate"
) -> List[Dict[str, str]]:
    """
    Get contextual tips based on the current view/data.
    
    Args:
        context_type: Type of context (e.g., "analyst", "chart", "decision")
        data: Current data being viewed
        user_level: User expertise level (beginner, intermediate, advanced)
    
    Returns:
        List of contextual tips with titles and descriptions
    """
    r = redis_client()
    cache_key = f"tips:v1:{context_type}:{user_level}:{hash(json.dumps(data, sort_keys=True))}"
    cached = r.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass
    
    prompt = f"""Generate helpful contextual tips for a {user_level} trader.

Context: {context_type}
Current Data: {json.dumps(data, indent=2)}

Return a JSON array of 3-5 tips, each with:
{{
    "title": "Tip title",
    "description": "Brief, actionable description",
    "type": "info|warning|tip|insight",
    "priority": "high|medium|low"
}}

Make tips specific to the current data and context."""

    try:
        resp = client.responses.create(
            model=MODEL,
            input=prompt,
            response_format={"type": "json_object"},
            max_output_tokens=400,
            temperature=0.4,
        )
        txt = _first_text_from_response(resp)
        if txt:
            result = json.loads(txt)
            tips = result.get("tips", [])
            r.setex(cache_key, 300, json.dumps(tips))
            return tips
    except Exception:
        pass
    
    # Fallback tips
    return [
        {
            "title": "Check the Data",
            "description": "Review all indicators before making decisions",
            "type": "tip",
            "priority": "high"
        }
    ]


def explain_indicator(
    indicator_name: str,
    values: Dict[str, Any],
    simple: bool = False
) -> str:
    """
    Explain what a technical indicator shows.
    
    Args:
        indicator_name: Name of indicator (e.g., "EMA", "RSI", "VWAP")
        values: Current values and context
        simple: If True, provide simpler explanation for beginners
    
    Returns:
        Explanation of the indicator
    """
    # Static explanations for common indicators (fast, no API call)
    explanations = {
        "EMA": {
            "simple": "Exponential Moving Average (EMA) smooths price data to identify trends. Higher values mean uptrend, lower means downtrend.",
            "detailed": "EMA gives more weight to recent prices. EMA 9 crossing above EMA 21 suggests bullish momentum. The distance between them indicates trend strength."
        },
        "RSI": {
            "simple": "RSI measures if a stock is overbought (>70) or oversold (<30). Values 30-70 are neutral.",
            "detailed": "RSI (Relative Strength Index) ranges 0-100. Above 70 suggests overbought (may reverse down), below 30 suggests oversold (may reverse up). Use with other indicators."
        },
        "VWAP": {
            "simple": "VWAP is the average price weighted by volume. Price above VWAP is bullish, below is bearish.",
            "detailed": "Volume-Weighted Average Price (VWAP) shows the true average price considering volume. Institutional traders use it. Price above VWAP with volume confirms bullish sentiment."
        },
        "ATR": {
            "simple": "ATR measures volatility. Higher ATR means bigger price swings, use wider stops.",
            "detailed": "Average True Range (ATR) measures market volatility. Use it to set stop-loss distances - multiply ATR by 1.5-2x for stops. Higher ATR needs larger position sizing adjustments."
        },
        "Bollinger Bands": {
            "simple": "Bands show volatility. Price near upper band is high, near lower is low. Squeeze means breakout coming.",
            "detailed": "Bollinger Bands use standard deviation. Price near bands suggests overbought/oversold. Band squeeze (narrow bands) precedes volatility expansion. Use with volume."
        },
        "Volume": {
            "simple": "Volume shows how many shares traded. High volume confirms trends, low volume suggests weak moves.",
            "detailed": "Volume is crucial for confirmation. Rising price + rising volume = strong trend. Breakouts need 1.5-2x average volume. Low volume rallies often fail."
        }
    }
    
    # Return static explanation if available
    if indicator_name in explanations:
        key = "simple" if simple else "detailed"
        base = explanations[indicator_name][key]
        
        # Add current values context if provided
        if values:
            current = values.get("current", "")
            if current:
                base += f" Current: {current}."
        
        return base
    
    # Otherwise use AI
    r = redis_client()
    cache_key = f"indicator:v1:{indicator_name}:{simple}:{hash(json.dumps(values, sort_keys=True))}"
    cached = r.get(cache_key)
    if cached:
        return cached
    
    level = "simple, beginner-friendly" if simple else "detailed, technical"
    prompt = f"""Explain the {indicator_name} indicator in {level} terms.

Current Values: {json.dumps(values, indent=2)}

Provide a 2-3 sentence explanation that:
1. Defines what it measures
2. Explains the current values
3. Gives trading insight

Keep it practical and educational."""

    try:
        resp = client.responses.create(
            model=MODEL,
            input=prompt,
            max_output_tokens=120,
            temperature=0.2,
        )
        text = _first_text_from_response(resp)
        if text:
            r.setex(cache_key, 1800, text)  # Cache for 30 minutes
            return text
    except Exception:
        pass
    
    return f"{indicator_name} is a technical indicator used in trading analysis."


def smart_explanation(query: str, context: Dict[str, Any]) -> str:
    """
    Answer any question about the data using AI.
    
    Args:
        query: User's question
        context: Current data/context
    
    Returns:
        AI-generated answer
    """
    r = redis_client()
    cache_key = f"smart:v1:{query}:{hash(json.dumps(context, sort_keys=True))}"
    cached = r.get(cache_key)
    if cached:
        return cached
    
    prompt = f"""Answer this question about trading data clearly and concisely.

Question: {query}
Context/Data: {json.dumps(context, indent=2)}

Provide a clear, educational answer in 2-4 sentences. Be specific to the data shown."""

    try:
        resp = client.responses.create(
            model=MODEL,
            input=prompt,
            max_output_tokens=200,
            temperature=0.3,
        )
        text = _first_text_from_response(resp)
        if text:
            r.setex(cache_key, 600, text)
            return text
    except Exception:
        pass
    
    return "Unable to generate explanation at this time."
