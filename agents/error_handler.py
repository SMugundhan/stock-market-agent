from core.state import StockAnalysisState

from opentelemetry import trace
tracer = trace.get_tracer("stock-market-agent")

def error_handler_node ( state : StockAnalysisState ) -> dict:

    """
        Error Handler Node.
        Called when something goes wrong in the pipeline.
        Returns a graceful error response instead of crashing.
    """

    with tracer.start_as_current_span("Error_handler") as span:

        errors = state . get ( "error", [] )

        ticker = state . get ( "ticker", "UNKNOWN" )

        span.set_attribute("ticker", ticker)

        span.set_attribute("errors", errors)

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
