from langchain_groq import ChatGroq   # ChatGroq is LangChain's wrapper for Groq's API

from core.state import StockAnalysisState #import our shared state definition

from core.config import config

# initilaize the LLM

llm = ChatGroq ( api_key = config.GROQ_API_KEY , model_name = config.MODEL_NAME )

async def analyst_agent_node ( state: StockAnalysisState ) -> dict :

    """
    Analyst agent node.
    Reads : current_price, price_change_pct, rsi, news_headlines, sentiment_score, volatility, risk_level
    Writes : recommendation, confidence, reasoning
    """

    print ( f" Analyst agent : Analyzing { state [ 'ticker' ] } ... " )

    retry_count = state . get ( "retry_count", 0 )
    
    # Step 1 Build the promt using real data from state

    prompt = f"""You are a senior stock market analyst.

            Analyze this real-time data and give a recommendation:

            Stock:            {state['ticker']}
            Current Price:    ${state.get('current_price', 'N/A')}
            Price Change:     {state.get('price_change_pct', 'N/A')}%
            RSI:              {state.get('rsi', 'N/A')}
            Sentiment Score:  {state.get('sentiment_score', 'N/A')}
                                (-1.0 = very negative, 0 = neutral, +1.0 = very positive)
            Sentiment:       {state.get('sentiment_score', 'N/A')} (-1 to +1)
            Volatility:      {state.get('volatility', 'N/A')}%
            Risk Level:      {state.get('risk_level', 'N/A')}

            Recent Headlines: {chr(10).join(f"- {h}" for h in state.get('news_headlines', [])[:3])}

            Analysis Framework:
                                - RSI above 70 = overbought (potential sell signal)
                                - RSI below 30 = oversold (potential buy signal)
                                - High positive sentiment + rising price = bullish signal
                                - Negative sentiment + falling price = bearish signal

            Respond in EXACTLY this format:
            RECOMMENDATION: [BUY/HOLD/SELL]
            CONFIDENCE: [0.0 to 1.0]
            REASONING: [2-3 sentences using price, RSI, AND sentiment data]"""

        # chr(10) = newline character "\n"

        # We use chr(10) inside f-string because you can't use \n directly in f-string expressions

        # f"- {h}" for h in list = creates "- headline" for each headline

        # [:3] = only use first 3 headlines to keep prompt concise

    # Note : We specify exact output format

    # This is called prompt engineering

    try :

        # Step 2 : Call the LLM

        response = await llm . ainvoke ( prompt )

        raw_text = response.content

        print ( f" RAW LLM Response : \n {raw_text} " ) 

        # Step 3 : Parse the response to extract recommendation, confidence and reasoning

        lines = raw_text . strip ( ) . split ( "\n" ) # split response into lines

        recommendation = "HOLD" # default to HOLD if not found

        confidence = 0.5

        reasoning = raw_text # default to raw text if parsing fails

        for line in lines:

            if line.startswith ( "RECOMMENDATION" ) :

                recommendation = line . split ( ":" ) [ 1 ] . strip ( )

            elif line.startswith ( "CONFIDENCE" ) :

                confidence = float ( line . split ( ":" ) [ 1 ] . strip ( ) )

            elif line.startswith ( "REASONING" ) :

                reasoning = line . split ( ":" ) [ 1 ] . strip ( )

        print ( f" Analyst Agent : Recommendation = { recommendation } , Confidence = { confidence } , Reasoning = { reasoning } " )

        # Step 4 : Write the results back to the state

        return { "recommendation" : recommendation , "confidence" : confidence , "reasoning" : reasoning, "error" : [] }
    

    except Exception as e :

        print ( f" Analyst Agent Error : { e } " )

        return { "recommendation" : "HOLD" , "confidence" : 0.5 , "reasoning" : f"Error occurred : { str ( e ) } ", "error" : [ str ( e ) ], "retry_count" : retry_count + 1 }
