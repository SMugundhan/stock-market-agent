import numpy as np  # For std deviation calculation

import yfinance as yf

from core. state import StockAnalysisState

from core . async_utils import run_sync_in_thread

def _calculate_risk_sync ( ticker : str ) -> dict :

    """
    All the numpy / yfinance risk math
    """
    # Step 1 fetch historical data

    stock = yf. Ticker ( ticker )

    hist = stock.history ( period = "6mo", interval = "1d" )

    if hist.empty :

        return { "volatality" : None, "risk_level" : "HIGH", "errors" : [ f"No historical data for { ticker }" ] }
        
    closes = hist [ "Close" ] # Series of value ( series, dataframe )

    # Step 2 Calculate volatality

    # Daily returns = % change from each day to the next day

    daily_returns = closes. pct_change(). dropna()

    # .pct_change() = (today - yesterday) / yesterday for each row
        
    # .dropna() = remove the first row which is NaN
        
    # (first row has no "yesterday" to compare to)

        
        
    #  Annualized volatility = daily std dev × sqrt(252)

    # Why 252? There are ~252 trading days in a year

    # Why sqrt(252)? Statistical scaling — variance scales linearly

    # with time, so std dev scales with sqrt of time

    volatility_daily = float(daily_returns.std())

    volatility_annual = round(volatility_daily * np.sqrt(252) * 100, 2)

    # Multiply by 100 to convert to percentage

    # e.g. 0.25 → 25% annual volatility

    print ( f" Annualized volatility : { volatility_annual }% " )


    # Step 3 Calculate the maximum drawdown

        
    # Cumulative product = running total of compound returns
        
    # (1 + r1) × (1 + r2) × ... gives you wealth growth factor

    cummulative = ( 1 + daily_returns ).cumprod ()

    #  e.g. if returns were +5%, -3%, +2%:
        
    # cumulative = [1.05, 1.0185, 1.0389]

        
    # Rolling maximum = highest cumulative value seen so far

    rolling_max = cummulative.cummax ()

    # At each point : " What was the peak up to this deal"

    # drawdown at each point = ( curr - peak ) / peak
        
    drawdown_series = ( cummulative - rolling_max ) / rolling_max

    # Neg values - how far below the peak are we?


    # max draw down = wors ( most neg ) value in the series

    max_drawdown = round ( float ( drawdown_series. min() ) * 100, 2 )

    # Multiply by 100 for percentage


    print ( f" Max DrawDown : { max_drawdown } % " )


    # Step 4 Calculate beta

    # beta = how this stock mpves relative to the S&P 500 market
    # We compare stock returns to SPY ( S&P 500 ETF ) returns

    spy = yf. Ticker ( "SPY" )

    # SPY = It tracks overall US market

    spy_hist = spy.history ( period = "6mo", interval = "1d" )

    spy_returns = spy_hist [ "Close" ]. pct_change ().dropna ()
    # Get same period S&P 500 returns to compare against

    # Align both return series by date
    # they might have slightly different lengths if data is missing

    min_length = min ( len ( daily_returns ), len( spy_returns ) )
        
    stock_ret = daily_returns. iloc [ -min_length: ].values
        
    market_ret = spy_returns. iloc [ -min_length:  ].values
        

    # Beta formuls = covariance ( stock, market ) / Variance ( market )
    # Covariance measures how two things move together
    # Variance measures how much market moves on it own
    covariance = np. cov ( stock_ret, market_ret )[0][1]
    # np. cov returns 2*2 matrix
    # [[var_stock, cov], [cov, var_market]]
    # [0][1] = the covariance element

    market_variance = np.var ( market_ret )
    # np.var = variance of market returns

    beta = round ( covariance / market_variance, 2 ) if market_variance != 0 else 1.0

    print ( f" BETA : { beta } " )


    # ── STEP 5: Calculate Risk Score (0-10) ───────────────────

    # Convert each metric to 0-10 sub-score

    # Volatility score: normalize against common ranges
    # <15% = low volatility | 15-30% = medium | >30% = high
    if volatility_annual < 15:
        vol_score = 2.0      # low risk
    elif volatility_annual < 25:
        vol_score = 5.0      # medium risk
    elif volatility_annual < 40:
        vol_score = 7.5      # high risk
    else:
            vol_score = 10.0     # very high risk

    # Drawdown score: normalize against common ranges
    # >-10% is mild | -10 to -25% is moderate | < -25% is severe
    if max_drawdown > -10:
        dd_score = 2.0       # mild drawdown
    elif max_drawdown > -20:
        dd_score = 5.0       # moderate
    elif max_drawdown > -35:
        dd_score = 7.5       # severe
    else:
        dd_score = 10.0      # extreme

    # Beta score
    if abs(beta) < 0.7:
        beta_score = 2.0     # defensive stock
    elif abs(beta) < 1.2:
        beta_score = 4.0     # market-like
    elif abs(beta) < 1.8:
        beta_score = 7.0     # aggressive
    else:
        beta_score = 10.0    # very aggressive

    # Weighted final score
    risk_score = round(
            (vol_score * 0.4) +    # 40% weight
            (dd_score  * 0.4) +    # 40% weight
            (beta_score * 0.2),    # 20% weight
            2
        )

    # Convert score to label
    if risk_score <= 3.5:
        risk_level = "LOW"
    elif risk_score <= 6.5:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    print(f"   ✅ Risk Score: {risk_score}/10 → {risk_level}")

    # ── STEP 6: Return updated State fields ───────────────────

    return {
            "volatility":   volatility_annual,
            # Annualized % volatility e.g. 23.4

            "risk_level":   risk_level,
            # "LOW" / "MEDIUM" / "HIGH"

            "error": []

            # Note: We could add max_drawdown and beta to State too
            # But keep it simple for now — risk_level is what
            # Analyst Agent needs to make its recommendation
        }


async def risk_agent_node ( state : StockAnalysisState ) -> dict:

    """
    Risk Agent Node.

    Reads:  state["ticker"]
    Does:   Calculates volatility, max drawdown, beta
            Combines into a 0-10 risk score
    Writes: volatility, risk_level, max_drawdown, beta, risk_score

    """

    ticker = state [ 'ticker' ]

    print ( f" Risk agent calculating risk for { ticker }.... " )

    try :

        # Calls the Sync function

        result = await run_sync_in_thread ( _calculate_risk_sync, ticker )

        return { **result, "error" : [] }
        
    except Exception as e:
        print(f"❌ Risk Agent Error: {e}")
        return {
            "volatility": None,
            "risk_level": "MEDIUM",
            "error": [f"Risk Agent failed: {str(e)}"]
        }


