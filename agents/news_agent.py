from tavily import TavilyClient

from langchain_groq import ChatGroq

from core.state import StockAnalysisState

from core.config import config

from core . async_utils import run_sync_in_thread



# Initialization

tavily_client = TavilyClient ( api_key = config.TAVILY_API_KEY )

llm = ChatGroq ( api_key = config.GROQ_API_KEY , model_name = config.MODEL_NAME )



def  _fetch_news_sync ( ticker : str ) -> list:

    """
    Blocking the tavily call, wrapped seperately from sentiment scoring
    """

    results = tavily_client . search ( query = f" { ticker } stock news analysis today ", max_results = 5 )

    return results . get ( "results", [] )


async def news_agent_node ( state : StockAnalysisState ) -> dict :

    """
    News agent node.
    Reads : ticker
    Writes : news_headlines, sentiment_score
    """

    ticker = state [ 'ticker' ]

    print ( f" News agent : fetching news for { ticker } " )

    try :

        # Step 1 : Fetch news using Tavily from async code

        articles = await run_sync_in_thread ( _fetch_news_sync, ticker )


        if not articles :

            print ( f" No news articles found for { ticker } " )

            return { "news_headlines" : None , "sentiment_score" : None }
        
        headlines = []

        contents = []

        for article in articles :

            title = article . get ( "title", "" )

            content = article . get ( "content", "" )[ :200 ]

            if title :

                headlines . append ( title )

                contents . append ( f"{ title } : { content }" )

        print ( f" Found { len ( headlines ) } articles " )

        for h in headlines :

            print ( f" - { h } " )

        # Step 2 : Analyze sentiment using LLM

        # Join all headlines + snippets into one block of text

        news_text = "\n" . join ( contents )

        sentiment_prompt = f"""You are a financial news sentiment analyzer.

                Analyze the sentiment of these news headlines and snippets about {ticker} stock:

                {news_text}

                Instructions:
                    - Consider only financial/investment implications
                    - Positive news = earnings growth, new products, partnerships, price rises
                    - Negative news = lawsuits, revenue decline, recalls, executive departures
                    - Be objective, not emotional

                Respond with ONLY this format (nothing else):
                SENTIMENT_SCORE: [decimal between -1.0 and 1.0]
                SENTIMENT_LABEL: [VERY_NEGATIVE / NEGATIVE / NEUTRAL / POSITIVE / VERY_POSITIVE]
                SUMMARY: [one sentence summarizing overall news tone]"""

        # Call LLM
        # LLm invoke is also sync call under the hood so wrap the same way

        response = await llm . ainvoke ( sentiment_prompt )

        raw = response . content . strip ()

        print ( f" \n Sentiment LLM response : \n { raw } " )

        # Step 3 Parse the sentiment

        # Default values in case parsing fails
        sentiment_score = 0.0
        
        sentiment_label = "NEUTRAL"
        
        sentiment_summary = ""

        for line in raw.split("\n"):
            # Split response into lines and check each one

            if line.startswith("SENTIMENT_SCORE:"):

                score_str = line.split(":")[1].strip()
                # "SENTIMENT_SCORE: 0.65" → split → [" 0.65"] → strip → "0.65"

                sentiment_score = float(score_str)
                # float("0.65") = 0.65 as a number

            elif line.startswith("SENTIMENT_LABEL:"):

                sentiment_label = line.split(":")[1].strip()

            elif line.startswith("SUMMARY:"):
                
                sentiment_summary = line.split(":", 1)[1].strip()
                # split(":", 1) = split only on FIRST colon
                # Summary text might have colons in it

        print(f"✅ Sentiment: {sentiment_score} ({sentiment_label})")

        print(f"   Summary: {sentiment_summary}")

        # ── STEP 4: Return updated State fields ──────────────────

        return {
            "news_headlines": headlines,
            # List of headline strings e.g. ["Apple hits record...", ...]

            "sentiment_score": sentiment_score,
            # Single float e.g. 0.65

            "error": []
        }

    except Exception as e:
        print(f"❌ News Agent Error: {e}")

        return {
            "news_headlines": [],
            "sentiment_score": 0.0,
            "error": [f"News Agent failed: {str(e)}"]
        }
