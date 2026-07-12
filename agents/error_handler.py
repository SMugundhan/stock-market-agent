from core.state import StockAnalysisState

def error_handler_node ( state : StockAnalysisState ) -> dict:

    """
        Error Handler Node.
        Called when something goes wrong in the pipeline.
        Returns a graceful error response instead of crashing.
    """

    errors = state . get ( "error", [] )

    ticker = state . get ( "ticker", "UNKNOWN" )

    print ( f" Error Handler : { errors } " )

    # Create a error report

    error_report = f"""
                        Analysis for {ticker} encountered issues:

                        Errors: {', '.join(errors)}

                        Partial data available:
                            - Price: {state.get('current_price', 'unavailable')}
                            - Recommendation: Unable to complete due to errors

                        Please retry or check the ticker symbol.
                    """.strip()
    
    return { "final_report" : error_report, "recommendation" : "UNAVAILABLE", "confidence" : 0.0 }
