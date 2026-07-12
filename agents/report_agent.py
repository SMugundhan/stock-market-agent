import json

from datetime import datetime

from langchain_groq import ChatGroq

from core.state import StockAnalysisState

from core.config import Config

llm = ChatGroq ( api_key = Config. GROQ_API_KEY, model_name = Config. MODEL_NAME )

def  report_agent_node ( state : StockAnalysisState ) -> dict:

    """
    Report Agent Node — the final step.

    Reads:  Everything in state (all agents have written their data)
    Does:   Compiles structured JSON report
            Generates executive summary via LLM
            Adds metadata (date, disclaimer)
    Writes: final_report (JSON string)
    """

    ticker = state. get ( "ticker", "UNKNOWN" )

    print ( f" Report agent : compiling report for { ticker } " )

    try :

        # Step 1 Generate executive summary

        # WE have already have the recommendation from analyst agent
        # Now we aks LLM to write a professional paragraph
        # Summarizing everything

        summary_report =  f"""You are a professional financial report writer.

Write a concise 3-sentence executive summary for this stock analysis:

Stock:          {ticker}
Price:          ${state.get('current_price', 'N/A')}
Change:         {state.get('price_change_pct', 'N/A')}%
RSI:            {state.get('rsi', 'N/A')}
Sentiment:      {state.get('sentiment_score', 'N/A')} (-1 to +1)
Volatility:     {state.get('volatility', 'N/A')}%
Risk Level:     {state.get('risk_level', 'N/A')}
Recommendation: {state.get('recommendation', 'N/A')}
Confidence:     {state.get('confidence', 'N/A')}
Reasoning:      {state.get('reasoning', 'N/A')}

Requirements:
- Professional financial language
- Mention the key data points that drove the recommendation
- End with the final recommendation and confidence level
- Max 3 sentences, no bullet points"""
        
        summary_response = llm. invoke ( summary_report )

        executive_summary = summary_response. content. strip()

        print ( " Executive summary generated " )

        # Step 2 Extract keys

        # Determine what the key factors were in the recommendatiom
        # We derive this programmatically from the state data

        key_factors = []

        # Price momentum factor

        price_change = state. get ( "price_change_pct", 0 ) or 0

        if price_change > 1.5:

            key_factors.append ( f" Strong upward momentum ( + { price_change }% ) " )

        elif price_change < -1.5:

            key_factors.append ( f" Downward pressure ( { price_change }% ) " )

        else:

            key_factors.append ( f" Price stable ( { price_change }% ) " )


        # RSI factor
        rsi = state.get("rsi", 50) or 50
        
        if rsi > 70:
        
            key_factors.append(f"Overbought signal (RSI: {rsi})")
        
        elif rsi < 30:
        
            key_factors.append(f"Oversold signal (RSI: {rsi})")
        
        else:
        
            key_factors.append(f"RSI in neutral zone ({rsi})")

        # Sentiment factor
        sentiment = state.get("sentiment_score", 0) or 0

        if sentiment > 0.5:

            key_factors.append(f"Strong positive news sentiment ({sentiment})")
        
        elif sentiment < -0.3:
        
            key_factors.append(f"Negative news sentiment ({sentiment})")
        
        else:
        
            key_factors.append(f"Neutral market sentiment ({sentiment})")

        # Risk factor
        risk_level = state.get("risk_level", "MEDIUM") or "MEDIUM"
        
        volatility = state.get("volatility", 0) or 0
        
        key_factors.append(f"{risk_level} risk profile (volatility: {volatility}%)")

        # ── STEP 3: Build Structured Report Dict ──────────────

        report_dict = {
            # ── HEADER ──────────────────────────────
            "ticker":       ticker,
            
            "company_name": ticker,
            # In production: fetch from yfinance info["longName"]
            
            "report_date":  datetime.now().strftime("%Y-%m-%d %H:%M"),
            # strftime formats datetime → "2026-06-16 14:30"
            
            "analysis_type": state.get("analysis_type", "full"),

            # ── MARKET DATA ─────────────────────────
            "market_data": {
                "current_price":    state.get("current_price"),
                "price_change_pct": state.get("price_change_pct"),
                "rsi":              state.get("rsi"),
            },

            # ── SENTIMENT ───────────────────────────
            "sentiment": {
                "score":     state.get("sentiment_score"),
                "headlines": state.get("news_headlines", [])[:3],
                # [:3] = only include top 3 headlines in report
            },

            # ── RISK METRICS ────────────────────────
            "risk": {
                "volatility_annual": state.get("volatility"),
                "risk_level":        state.get("risk_level"),
            },

            # ── VERDICT ─────────────────────────────
            "verdict": {
                "recommendation": state.get("recommendation"),
                "confidence":     state.get("confidence"),
                "reasoning":      state.get("reasoning"),
                "key_factors":    key_factors,
            },

            # ── NARRATIVE ───────────────────────────
            "executive_summary": executive_summary,

            # ── METADATA ────────────────────────────
            "disclaimer": (
                "This report is generated by an AI system for "
                "educational purposes only. It does not constitute "
                "financial advice. Always consult a qualified financial "
                "advisor before making investment decisions."
            ),
            "generated_by": "Multi-Agent Stock Analysis System v1.0",
            "error": state.get("error", [])
        }

        # ── STEP 4: Convert dict to JSON string ───────────────
        # json.dumps() converts Python dict → JSON string
        # indent=2 makes it human-readable with 2-space indentation
        # ensure_ascii=False allows non-ASCII characters
        final_report_json = json.dumps(report_dict, indent=2, ensure_ascii=False)

        print(f"✅ Report compiled successfully")
        
        print(f"   Recommendation: {report_dict['verdict']['recommendation']}")
        
        print(f"   Confidence:     {report_dict['verdict']['confidence']}")

        return {
            "final_report": final_report_json
            # Stored as JSON string in state
            # API layer will parse and return it
        }

    except Exception as e:
        
        print(f" Report Agent Error: {e}")

        # Even if report fails — return a minimal report
        # Never return None or crash the pipeline
        fallback_report = json.dumps({
            "ticker":       ticker,
            "report_date":  datetime.now().strftime("%Y-%m-%d %H:%M"),
            "verdict": {
                "recommendation": state.get("recommendation", "UNAVAILABLE"),
                "confidence":     state.get("confidence", 0.0),
            },
            "error": f"Report generation failed: {str(e)}",
            "disclaimer": "This report is for educational purposes only."
        }, indent=2)

        return {"final_report": fallback_report}