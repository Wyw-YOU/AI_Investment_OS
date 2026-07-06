# Prompt Templates Reference

Comprehensive prompt engineering patterns for multi-agent systems.

---

## Table of Contents

1. [Prompt Structure Principles](#1-prompt-structure-principles)
2. [Role Definition Patterns](#2-role-definition-patterns)
3. [Context Injection Patterns](#3-context-injection-patterns)
4. [Task Specification Patterns](#4-task-specification-patterns)
5. [Output Format Patterns](#5-output-format-patterns)
6. [Few-Shot Example Patterns](#6-few-shot-example-patterns)
7. [Domain-Specific Prompt Templates](#7-domain-specific-prompt-templates)
   - Investment Analysis
   - News Analysis
   - Risk Assessment
   - Report Generation
8. [Advanced Techniques](#8-advanced-techniques)

---

## 1. Prompt Structure Principles

### The CRAFT Framework

Every well-structured prompt should include:

- **C**ontext - Background information and current state
- **R**ole - Agent's expertise and perspective
- **A**ction - Specific task to perform
- **F**ormat - Expected output structure
- **T**one - Communication style and constraints

### Basic Template Structure

```markdown
[ROLE]
{role_definition}

[CONTEXT]
{relevant_data_and_background}

[TASK]
{clear_specific_instructions}

[OUTPUT FORMAT]
{exact_json_or_structured_format}

[EXAMPLES]
{input_output_pairs}

[CONSTRAINTS]
{limitations_and_requirements}

[TONE]
{communication_style}
```

---

## 2. Role Definition Patterns

### Pattern A: Expert Persona

Define a specific expert identity:

```markdown
[ROLE]
You are a Senior Financial Analyst with 20+ years of experience in equity research,
specializing in technology sector analysis at a top-tier investment bank.

Your expertise includes:
- Deep understanding of financial statements and accounting principles
- Mastery of valuation methodologies (DCF, comparable analysis, precedent transactions)
- Extensive experience with technology company business models
- Strong track record of accurate stock recommendations

Your analysis style is:
- Data-driven and evidence-based
- Balanced between quantitative metrics and qualitative insights
- Conservative in estimates, preferring to under-promise and over-deliver
- Clear about uncertainty and risk factors
```

### Pattern B: Team Role

Define agent as part of a team:

```markdown
[ROLE]
You are the Risk Assessment Specialist on a multi-agent investment research team.

Your role in the team:
- Receive analysis outputs from News, Financial, and Technical agents
- Identify and quantify investment risks
- Provide risk-adjusted recommendations
- Flag high-risk situations requiring human review

Your responsibilities:
- Synthesize risk signals from multiple sources
- Categorize risks by type (market, company, valuation, liquidity)
- Provide actionable risk mitigation strategies
- Assign risk scores with clear justification
```

### Pattern C: System Component

Define agent as system component:

```markdown
[ROLE]
You are the Data Validation Agent in an automated investment analysis pipeline.

Your function:
- Verify data quality and completeness from upstream sources
- Identify anomalies and inconsistencies
- Validate calculations and intermediate results
- Ensure output meets downstream requirements

You operate with:
- Strict validation rules and thresholds
- No bias toward any particular outcome
- Focus on data integrity over analysis
- Clear error reporting with actionable details
```

---

## 3. Context Injection Patterns

### Pattern A: Structured Context

```markdown
[CONTEXT]
## Stock Information
- Symbol: AAPL (Apple Inc.)
- Exchange: NASDAQ
- Sector: Technology
- Market Cap: $2.8T
- Current Price: $175.50

## Recent Market Data (Last 5 Days)
| Date | Open | High | Low | Close | Volume |
|------|------|------|-----|-------|--------|
| 2024-01-15 | 173.0 | 176.0 | 172.5 | 175.5 | 45.2M |
| 2024-01-14 | 172.0 | 174.0 | 171.0 | 173.0 | 38.1M |
| ... | ... | ... | ... | ... | ... |

## News Headlines (Last 24 Hours)
1. "Apple Reports Record Q4 Revenue of $89.5B" - Reuters (Positive)
2. "iPhone 15 Sales Exceed Expectations in China" - Bloomberg (Positive)
3. "Apple Vision Pro Launch Set for February 2" - TechCrunch (Neutral)

## Financial Highlights
- Revenue (TTM): $383.3B
- Net Income (TTM): $97.0B
- EPS (TTM): $6.13
- P/E Ratio: 28.6
- Dividend Yield: 0.55%
```

### Pattern B: Dynamic Context with Metadata

```markdown
[CONTEXT]
## Analysis Request
- User ID: user_12345
- Analysis Type: Deep Dive
- Time Horizon: 12 months
- Risk Tolerance: Moderate
- Portfolio Context: Already holding 5% AAPL position

## Available Data Sources
✓ Real-time price data (Alpha Vantage)
✓ News feed (last 7 days, 47 articles)
✓ Financial statements (Q4 2023)
✓ Technical indicators (daily, weekly, monthly)
○ Analyst consensus (pending update)
✗ Insider trading data (unavailable)

## Previous Analysis Summary (if available)
- Last analysis date: 2024-01-10
- Previous recommendation: BUY
- Previous confidence: 0.82
- Key changes since: Q4 earnings released
```

### Pattern C: Historical Context

```markdown
[CONTEXT]
## Historical Analysis Chain
This is a follow-up analysis. Previous findings:

### Analysis #3 (2024-01-10)
- Recommendation: BUY
- Price Target: $180
- Key Thesis: Strong iPhone cycle + Services growth
- Confidence: 0.82

### Analysis #2 (2023-12-15)
- Recommendation: HOLD
- Price Target: $170
- Key Thesis: Waiting for Q4 confirmation
- Confidence: 0.75

### Analysis #1 (2023-11-20)
- Recommendation: BUY
- Price Target: $175
- Key Thesis: Undervalued relative to peers
- Confidence: 0.78

## Current Task
Update the analysis incorporating Q4 earnings results and recent developments.
```

---

## 4. Task Specification Patterns

### Pattern A: Structured Task List

```markdown
[TASK]
Perform comprehensive technical analysis of AAPL stock. Address each point:

1. **Trend Analysis**
   - Identify primary trend (bullish/bearish/neutral)
   - Secondary trend direction
   - Trend strength (1-10 scale)

2. **Support & Resistance Levels**
   - Identify 3 key support levels with reasoning
   - Identify 3 key resistance levels with reasoning
   - Current price position relative to levels

3. **Momentum Indicators**
   - RSI (14-period): current value and interpretation
   - MACD: signal line crossover status
   - Stochastic: overbought/oversold status

4. **Volume Analysis**
   - Volume trend (increasing/decreasing/stable)
   - Volume confirmation of price moves
   - Unusual volume patterns

5. **Chart Patterns**
   - Identify any active patterns (triangles, channels, etc.)
   - Pattern completion probability
   - Expected price targets from patterns

6. **Trading Signal**
   - Overall signal: BUY/SELL/HOLD
   - Entry price suggestion
   - Stop loss level
   - Take profit target
   - Risk/reward ratio
```

### Pattern B: Question-Based Task

```markdown
[TASK]
Answer the following questions about AAPL based on the provided context:

1. What is the current trend, and how strong is it?
   - Consider multiple timeframes (daily, weekly, monthly)

2. Where are the key price levels?
   - Why are these levels significant?
   - How has price reacted at these levels historically?

3. What do momentum indicators tell us?
   - Are there any divergences between price and indicators?
   - What is the current momentum state?

4. Is volume confirming the price action?
   - What does volume tell us about conviction?
   - Are there any accumulation/distribution signals?

5. What is the overall technical outlook?
   - Synthesize all signals into a coherent view
   - What could invalidate this outlook?
```

### Pattern C: Decision Task

```markdown
[TASK]
Make an investment decision recommendation based on the analysis:

**Decision Required:** Should an investor with moderate risk tolerance
buy, hold, or sell AAPL stock at current levels?

**Consider:**
- Technical setup and timing
- Risk/reward profile
- Portfolio context (already 5% position)
- Market conditions

**Provide:**
1. Clear recommendation (BUY / HOLD / SELL)
2. Confidence level (0.0 - 1.0)
3. Key reasons (top 3)
4. Risk factors to monitor
5. Specific action items with price levels
```

---

## 5. Output Format Patterns

### Pattern A: Strict JSON Schema

```markdown
[OUTPUT FORMAT]
Respond with ONLY valid JSON matching this exact schema:

{
  "trend": {
    "primary": "bullish" | "bearish" | "neutral",
    "secondary": "bullish" | "bearish" | "neutral",
    "strength": 1-10
  },
  "support_levels": [
    {"price": 170.0, "strength": "strong", "reason": "50-day MA"},
    {"price": 165.0, "strength": "moderate", "reason": "Previous resistance"},
    {"price": 160.0, "strength": "weak", "reason": "Round number"}
  ],
  "resistance_levels": [
    {"price": 180.0, "strength": "strong", "reason": "All-time high"},
    {"price": 178.0, "strength": "moderate", "reason": "Fibonacci extension"},
    {"price": 176.5, "strength": "weak", "reason": "Recent high"}
  ],
  "indicators": {
    "rsi": {"value": 65, "signal": "neutral"},
    "macd": {"signal": "bullish_crossover", "histogram": 0.5},
    "stochastic": {"value": 75, "signal": "approaching_overbought"}
  },
  "volume": {
    "trend": "increasing",
    "relative_volume": 1.2,
    "interpretation": "Strong buying interest"
  },
  "patterns": [
    {"name": "ascending_triangle", "status": "forming", "target": 182.0}
  ],
  "signal": {
    "action": "BUY",
    "entry": 175.0,
    "stop_loss": 168.0,
    "take_profit": 185.0,
    "risk_reward": 2.33
  },
  "confidence": 0.78,
  "reasoning": "Summary of key factors"
}

IMPORTANT: Do not include any text before or after the JSON. Only output valid JSON.
```

### Pattern B: Markdown with Sections

```markdown
[OUTPUT FORMAT]
Respond in this exact markdown structure:

## Executive Summary
[2-3 sentence overview of findings]

## Trend Analysis
**Primary Trend:** [bullish/bearish/neutral]
**Secondary Trend:** [bullish/bearish/neutral]
**Strength:** [1-10]/10

**Reasoning:**
- [Key point 1]
- [Key point 2]

## Key Price Levels

### Support Levels
| Level | Strength | Reasoning |
|-------|----------|-----------|
| $170  | Strong   | 50-day MA |
| $165  | Moderate | Previous resistance |
| $160  | Weak     | Round number |

### Resistance Levels
| Level | Strength | Reasoning |
|-------|----------|-----------|
| $180  | Strong   | All-time high |
| $178  | Moderate | Fibonacci |
| $176.5| Weak     | Recent high |

## Technical Indicators
| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI (14)  | 65    | Neutral |
| MACD      | Bull crossover | Buy |
| Stochastic| 75    | Near overbought |

## Trading Recommendation
**Action:** BUY
**Entry:** $175.00
**Stop Loss:** $168.00 (-4%)
**Take Profit:** $185.00 (+5.7%)
**Risk/Reward:** 2.33

**Confidence:** 78%

## Risk Factors
- [ ] Near overbought on stochastic
- [ ] Approaching resistance at $178
- [ ] Market-wide volatility

## Citations
- Price data: Alpha Vantage
- News: Reuters, Bloomberg
- Indicators: TradingView
```

### Pattern C: Hybrid (JSON + Explanation)

```markdown
[OUTPUT FORMAT]
Provide your analysis in two parts:

### Part 1: Structured Data (JSON)
\```json
{
  "recommendation": "BUY",
  "confidence": 0.78,
  "entry_price": 175.0,
  "stop_loss": 168.0,
  "target_price": 185.0,
  "risk_reward": 2.33,
  "key_factors": ["strong_trend", "volume_confirmation", "bullish_indicators"]
}
\```

### Part 2: Detailed Reasoning
[Provide 3-5 paragraphs explaining your analysis, including:]
- How you arrived at this recommendation
- Key supporting evidence
- Risk factors considered
- Conditions that would change your view
- Comparison to previous analysis (if available)
```

---

## 6. Few-Shot Example Patterns

### Pattern A: Input-Output Pairs

```markdown
[EXAMPLES]
Here are examples of the expected analysis format:

**Example 1: Bullish Stock (MSFT)**
Input:
- Price: $375, RSI: 55, MACD: Bullish crossover, Volume: Above average
- News: Strong Azure growth, AI partnership announcements

Output:
{
  "recommendation": "BUY",
  "confidence": 0.85,
  "entry_price": 375.0,
  "stop_loss": 360.0,
  "target_price": 400.0,
  "key_factors": ["cloud_growth", "ai_tailwinds", "technical_breakout"],
  "reasoning": "Strong fundamentals combined with bullish technical setup..."
}

**Example 2: Bearish Stock (XYZ)**
Input:
- Price: $45, RSI: 72, MACD: Bearish divergence, Volume: Declining
- News: Earnings miss, guidance cut

Output:
{
  "recommendation": "SELL",
  "confidence": 0.80,
  "entry_price": 45.0,
  "stop_loss": 48.0,
  "target_price": 38.0,
  "key_factors": ["overbought", "negative_earnings", "weak_guidance"],
  "reasoning": "Technical weakness confirmed by fundamental deterioration..."
}
```

### Pattern B: Chain-of-Thought Example

```markdown
[EXAMPLES]
Here's how to think through the analysis step-by-step:

**Example Analysis Process:**

Step 1: Assess Trend
- Look at price relative to 50-day and 200-day moving averages
- MSFT: Price ($375) > 50MA ($360) > 200MA ($340) = Uptrend ✓
- Strength: Price 10% above 200MA = Strong uptrend

Step 2: Check Momentum
- RSI at 55 = Neutral (not overbought/oversold)
- MACD just crossed above signal line = Bullish momentum starting
- Stochastic at 45 = Room to run higher

Step 3: Verify with Volume
- Recent volume: 25M (above 20-day avg of 20M)
- Up days have higher volume than down days = Confirms uptrend

Step 4: Identify Key Levels
- Support: $360 (50-day MA), $350 (previous resistance turned support)
- Resistance: $380 (recent high), $400 (psychological level)

Step 5: Calculate Risk/Reward
- Entry: $375
- Stop: $360 (4% risk)
- Target: $400 (6.7% reward)
- R/R: 1.67

Step 6: Form Recommendation
- Trend: Bullish ✓
- Momentum: Bullish ✓
- Volume: Confirming ✓
- Risk/Reward: Acceptable ✓
- **Recommendation: BUY with 85% confidence**
```

### Pattern C: Contrastive Examples

```markdown
[EXAMPLES]
Compare good vs. poor analysis:

**GOOD Analysis (DO THIS):**
"The stock shows a strong uptrend with price above both 50-day ($360) and
200-day ($340) moving averages. RSI at 55 indicates room for upside without
being overbought. MACD bullish crossover on 1/15 with increasing volume
(25M vs 20M average) confirms momentum. Support at $360 (50-day MA) with
resistance at $380. BUY with 85% confidence based on aligned technical
indicators and strong volume confirmation."

**POOR Analysis (DON'T DO THIS):**
"Stock looks good. It's going up. Buy it. Maybe stop at $360ish. Target
around $400. Should be fine."

Why the good version is better:
- Specific price levels with reasoning
- References to actual indicator values
- Volume analysis supports conclusion
- Clear confidence level with justification
- Actionable entry/stop/target
```

---

## 7. Domain-Specific Prompt Templates

### Investment Analysis Prompt

```python
INVESTMENT_ANALYSIS_PROMPT = """
[ROLE]
You are a Senior Equity Research Analyst at a top investment bank with 20+ years
of experience covering {sector} sector. Your research is known for being thorough,
balanced, and actionable.

[CONTEXT]
## Stock Profile
- Company: {company_name} ({ticker})
- Sector: {sector}
- Market Cap: {market_cap}
- Current Price: {current_price}

## Financial Data
{financial_data}

## Market Data
{market_data}

## News Context
{news_summary}

## User Context
- Investment Horizon: {time_horizon}
- Risk Tolerance: {risk_tolerance}
- Current Position: {current_position}

[TASK]
Provide a comprehensive investment analysis addressing:

1. **Business Quality Assessment**
   - Competitive position and moat
   - Management quality
   - Growth drivers

2. **Financial Health**
   - Profitability metrics
   - Balance sheet strength
   - Cash flow analysis

3. **Valuation**
   - Current valuation vs peers
   - Fair value estimate
   - Margin of safety

4. **Risk Analysis**
   - Key risk factors
   - Scenario analysis (bull/base/bear)
   - Risk mitigation strategies

5. **Investment Recommendation**
   - Buy/Hold/Sell with conviction level
   - Price target with timeframe
   - Position sizing suggestion

[OUTPUT FORMAT]
{output_format}

[EXAMPLES]
{examples}

[CONSTRAINTS]
- Base analysis solely on provided data
- Cite specific numbers and sources
- Be explicit about uncertainty
- Avoid definitive predictions without evidence
- Consider multiple scenarios
"""

def create_investment_prompt(stock_data: dict, user_context: dict) -> str:
    return INVESTMENT_ANALYSIS_PROMPT.format(
        company_name=stock_data["name"],
        ticker=stock_data["ticker"],
        sector=stock_data["sector"],
        market_cap=stock_data["market_cap"],
        current_price=stock_data["price"],
        financial_data=format_financials(stock_data["financials"]),
        market_data=format_market_data(stock_data["market_data"]),
        news_summary=format_news(stock_data["news"]),
        time_horizon=user_context["time_horizon"],
        risk_tolerance=user_context["risk_tolerance"],
        current_position=user_context.get("position", "None"),
        output_format=OUTPUT_FORMAT_TEMPLATE,
        examples=EXAMPLES_TEMPLATE
    )
```

### News Analysis Prompt

```python
NEWS_ANALYSIS_PROMPT = """
[ROLE]
You are a Financial News Analyst specializing in sentiment analysis and
event impact assessment. You excel at extracting actionable insights from
news articles and identifying market-moving events.

[CONTEXT]
## Target Stock
- Ticker: {ticker}
- Company: {company_name}
- Sector: {sector}

## News Articles to Analyze
{news_articles}

## Historical Context
- Recent stock performance: {recent_performance}
- Sector trends: {sector_trends}

[TASK]
Analyze the provided news articles and extract:

1. **Sentiment Assessment**
   - Overall sentiment (bullish/bearish/neutral)
   - Sentiment strength (0-100)
   - Sentiment trend (improving/stable/deteriorating)

2. **Key Events Identified**
   - Material events affecting the company
   - Events affecting the sector/market
   - Timeline and sequencing of events

3. **Impact Analysis**
   - Short-term impact expectation
   - Long-term implications
   - Affected business segments

4. **Risk Factors**
   - Emerging risks from news
   - Regulatory/legal concerns
   - Competitive threats

5. **Source Quality**
   - Credibility assessment
   - Information completeness
   - Potential biases

[OUTPUT FORMAT]
{output_format}

[GUIDELINES]
- Distinguish between facts and opinions in news
- Consider source credibility and potential biases
- Look for consensus across multiple sources
- Identify what's priced in vs. new information
- Note any contradictions between sources
"""
```

### Risk Assessment Prompt

```python
RISK_ASSESSMENT_PROMPT = """
[ROLE]
You are a Risk Management Specialist responsible for identifying, quantifying,
and providing mitigation strategies for investment risks. Your assessment
must be comprehensive, balanced, and actionable.

[CONTEXT]
## Investment Under Review
- Stock: {ticker} ({company_name})
- Proposed Action: {proposed_action}
- Position Size: {position_size}
- Portfolio Context: {portfolio_context}

## Analysis Inputs
### From Financial Agent
{financial_analysis}

### From Technical Agent
{technical_analysis}

### From News Agent
{news_analysis}

## Market Context
- Current Market Regime: {market_regime}
- Sector Risk Level: {sector_risk}
- Macro Environment: {macro_context}

[TASK]
Provide comprehensive risk assessment:

1. **Overall Risk Rating**
   - Risk Level: Low / Medium / High / Very High
   - Risk Score: 0-100 (higher = riskier)
   - Confidence in assessment: 0-100%

2. **Risk Factor Analysis**
   Categorize and rate each risk factor:

   a) **Market/Systematic Risk**
      - Market volatility exposure
      - Correlation with market
      - Sector-specific risks

   b) **Company-Specific Risk**
      - Business model risks
      - Competitive position
      - Management risks
      - Financial leverage

   c) **Valuation Risk**
      - Current valuation vs intrinsic value
      - Expectations embedded in price
      - Margin of safety

   d) **Technical Risk**
      - Chart pattern risks
      - Support/resistance levels
      - Momentum risks

   e) **Liquidity Risk**
      - Trading volume
      - Bid-ask spread
      - Market cap considerations

3. **Scenario Analysis**
   - Best case (20% probability): {scenario}
   - Base case (60% probability): {scenario}
   - Worst case (20% probability): {scenario}

4. **Risk Mitigation Strategies**
   - Position sizing recommendations
   - Stop loss levels
   - Hedging suggestions
   - Monitoring triggers

5. **Early Warning Signals**
   - What to watch for
   - When to reconsider thesis
   - When to exit

[OUTPUT FORMAT]
{output_format}

[PRINCIPLES]
- Be conservative in risk estimates
- Consider tail risks (low probability, high impact)
- Quantify where possible, qualify where necessary
- Provide actionable mitigation strategies
- Flag when human judgment is needed
"""
```

### Report Generation Prompt

```python
REPORT_GENERATION_PROMPT = """
[ROLE]
You are a Senior Research Report Writer responsible for synthesizing multi-agent
analysis outputs into clear, professional, and actionable investment reports.
Your reports are read by portfolio managers and investment committees.

[CONTEXT]
## Stock Under Analysis
- Company: {company_name} ({ticker})
- Date: {analysis_date}
- Requested by: {requester}

## Agent Analysis Results

### News Analysis
{news_analysis}

### Financial Analysis
{financial_analysis}

### Technical Analysis
{technical_analysis}

### Risk Assessment
{risk_assessment}

## User Requirements
- Report Type: {report_type} (Full / Summary / Update)
- Audience: {audience} (Portfolio Manager / Retail Investor / Analyst)
- Focus Areas: {focus_areas}

[TASK]
Create a comprehensive investment report that:

1. **Executive Summary** (2-3 paragraphs)
   - Clear investment thesis
   - Recommendation with conviction level
   - Key catalysts and risks

2. **Company Overview**
   - Business description
   - Competitive position
   - Recent developments

3. **Detailed Analysis**

   a) **Financial Health**
      - Profitability trends
      - Balance sheet analysis
      - Cash flow assessment
      - Peer comparison

   b) **Technical Outlook**
      - Trend analysis
      - Key price levels
      - Trading signals
      - Chart patterns

   c) **News & Sentiment**
      - Recent news impact
      - Market sentiment
      - Analyst consensus

   d) **Risk Assessment**
      - Risk rating and score
      - Key risk factors
      - Mitigation strategies

4. **Valuation**
   - Methodology used
   - Fair value estimate
   - Peer comparison
   - Upside/downside scenarios

5. **Investment Recommendation**
   - Action: BUY / HOLD / SELL
   - Conviction: High / Medium / Low
   - Price Target: ${target} ({upside}% {direction})
   - Time Horizon: {horizon}
   - Position Sizing: {sizing}

6. **Risk-Reward Analysis**
   - Expected return
   - Downside risk
   - Risk/reward ratio

7. **Action Items & Monitoring**
   - Entry points
   - Stop loss levels
   - Key dates/events to monitor
   - Triggers for thesis revision

8. **Appendix**
   - Data sources
   - Methodology notes
   - Detailed calculations

[FORMAT REQUIREMENTS]
{format_requirements}

[TONE]
- Professional and objective
- Data-driven with clear citations
- Balanced view presenting both bull and bear cases
- Actionable with specific recommendations
- Transparent about uncertainty

[EXAMPLES]
{example_reports}
"""
```

---

## 8. Advanced Techniques

### Technique A: Self-Consistency Checking

```markdown
[TASK]
Perform your analysis, then verify it through self-consistency checks:

1. **Generate initial analysis**
   - Complete the full analysis as instructed

2. **Self-consistency verification**
   - Check: Do your conclusions align with the data?
   - Check: Are there contradictions in your reasoning?
   - Check: Did you consider alternative interpretations?
   - Check: Is your confidence level justified by evidence strength?

3. **Stress test your thesis**
   - What would need to be true for the opposite conclusion?
   - What are you most uncertain about?
   - What information would change your view?

4. **Final output**
   - Include self-consistency score (0-100)
   - Note any unresolved uncertainties
   - Adjust confidence if needed
```

### Technique B: Multi-Perspective Analysis

```markdown
[TASK]
Analyze this from multiple expert perspectives, then synthesize:

1. **Bull Case Analysis** (Role: Growth Investor)
   - Focus on upside potential
   - Emphasize positive catalysts
   - Argue FOR buying

2. **Bear Case Analysis** (Role: Short Seller)
   - Focus on risks and overvaluation
   - Emphasize negative catalysts
   - Argue AGAINST buying

3. **Neutral Analysis** (Role: Index Fund Manager)
   - Consider market-cap weighting
   - Focus on benchmark-relative value
   - Assess inclusion/exclusion criteria

4. **Synthesis**
   - Weight each perspective
   - Identify areas of agreement/disagreement
   - Form balanced conclusion
```

### Technique C: Confidence Calibration

```markdown
[TASK]
Provide your analysis with calibrated confidence:

For each claim or recommendation:
1. State your confidence level (0-100%)
2. Justify the confidence based on:
   - Quality of supporting evidence
   - Amount of data available
   - Historical accuracy of similar analyses
   - Degree of consensus among signals

3. Provide confidence intervals where appropriate:
   - Price target: $X (range: $Y to $Z)
   - Timeframe: N months (range: M to P months)

4. Flag low-confidence areas explicitly:
   - "Low confidence due to limited data"
   - "High uncertainty - monitoring required"
```

### Technique D: Reasoning Transparency

```markdown
[TASK]
Provide transparent reasoning chain:

For each conclusion, show your reasoning:

**Conclusion: [Statement]**
- **Evidence:** [Specific data points]
- **Reasoning:** [How evidence leads to conclusion]
- **Assumptions:** [What you're assuming]
- **Confidence:** [0-100%]
- **Alternative interpretations:** [Other ways to view this data]

This allows readers to:
- Follow your logic
- Identify where they might disagree
- Understand uncertainty sources
- Validate or challenge your thinking
```

---

## Summary

Effective prompt engineering for multi-agent systems requires:

1. **Clear structure** - Consistent format across agents
2. **Rich context** - All relevant information injected
3. **Specific tasks** - Clear, actionable instructions
4. **Defined outputs** - Exact format specifications
5. **Quality examples** - Demonstrate expected outputs
6. **Appropriate constraints** - Guide without over-constraining

Use these templates as starting points and adapt them to your specific domain and requirements.
