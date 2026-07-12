from core.state import StockAnalysisState

def route_after_orchestrator ( state : StockAnalysisState ) -> str:

    """
    Called after Orchestrator runs.
    Decides: does the request need news + risk, or just price?
    """

    errors = state. get ( "error", [] )

    analysis_type = state. get ( "analysis_type", "full" )

    if errors:

        # Route to handler

        print ( " Routing -> error_handler ( errors detected ) " )

        return "error_handler"
    
    if analysis_type == "quick":

        # Skip straight to analyst -- no news or risk needed

        print ( " Routing -> price_agent ( quick_mode ) " )

        return "price_agent_quick"
    
    # default --- run full pipeline

    print ( " Routing ->  price_agent ( full mode ) " )

    return "price_agent"


def route_after_analyst ( state : StockAnalysisState ) -> str:
    
    """
        Called after Analyst Agent runs.
        Decides: is the analysis confident enough? Or retry?
    """

    confidence = state . get ( "confidence", 0.0 )

    errors = state . get ( "error", [] )

    retries = state . get ( "retry_count", 0 )

    # retry_count tracks how many time we have retired

    if errors and retries < 2:

        # Errors but haven't retried twice yet --- retry

        print ( f" Routing -> retry ( attempt { retries + 1 } ) " )

        return "retry_analyst"
    
    if confidence < 0.4 and retries < 1:

        # very low confidence on 1st try --- retry once

        print ( f" Routing -> retry ( low confidence : { confidence } ) " )

        return "retry_analyst"
    
    # Good enough ---> go to report

    print ( f" Routing -> report_agent ( confidence : { confidence } ) " )

    return "report_agent"
