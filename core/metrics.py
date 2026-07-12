import time

import json

from datetime import datetime, timezone

from memory . redis_client import redis_client



class AgentMetrics :

    """
    Tracks performance metrics for each agent run.
    Stores in Redis so metrics persist across requests
    and can be queried later for monitoring dashboards.
    """

    def __init__ ( self, request_id : str, ticker : str ) :

        self . request_id = request_id

        self . ticker = ticker

        self . start_time = time . time ()

        # Time . time () returns time as float ( unix timestamp )
        # eg : 1718546400.123

        self .agent_timings = {}
        #  Will store: {"price_agent": 0.34, "news_agent": 2.1, ...}

    
    def start_agent ( self, agent_name : str ) :

        """Call this whenever an agents starts"""

        self . agent_timing [ agent_name ] = { "start" : time . time() }


    def end_agent ( self, agent_name : str, success : bool = True, **extra_data ) :

        """Calls when agent finished runing"""

        if agent_name in self . agent_timings :

            start = self . agent_timings [ agent_name ][ "start" ]

            duration_ms = round ( ( time . time () - start ) * 1000, 2 )
            # * 1000 converts secs ti milsecs and , 2 is to keep 2 decimals

            self . agent_timings [ "agent_name" ] . update ( { "duration_ms" : duration_ms, "success" : success, **extra_data } )
            # Extra data = cache_hit = true, risk_lvl = high

    
    def save ( self, final_recommendation : str = None ) :

        """
        Saves the complete metrics record to Redis.
        Keeps last 100 request metrics for analysis.
        """

        total_duration_ms = round ( ( time . time () - self . start_time ) * 1000, 2 )

        metrics_record = {
            "request_id":          self.request_id,
            "ticker":              self.ticker,
            "timestamp":           datetime.now(timezone.utc).isoformat(),
            "total_duration_ms":   total_duration_ms,
            "agent_timings":       self.agent_timings,
            "final_recommendation": final_recommendation,
            "success": all(
                v.get("success", True)
                for v in self.agent_timings.values()
                if isinstance(v, dict) and "success" in v
            )
            # success = True only if all agents are succeeded
        }

        # sae this metrics for 24 hrs

        redis_client . set ( f"metrics : { self . request_id }", json . dumps ( metrics_record ), ex = 86400 )

        # Add to sorted set for "recent requests" list
        # Sorted sets in Redis let you keep N most recent items

        redis_client . zadd ( "metrics:recent", { self . request_id : time . time () } )
        # zadd = "sorted set add"
        # Key format: {"member": score}
        # Score = timestamp for time-based sorting

        # Keep only last 100 entries in the recent set
        redis_client . zremrangebyrank ( "metrics:recent", 0, -101 )
        # zremrangebyrank removes the items by their rank, 0 to -101 remove from 0 to 1100th from the end
        # To keep the mosst recent 100

        return metrics_record
    
def get_recent_metrics ( count : int = 10 ) -> list :

        """
        Returns the most recent N request metrics.
        Used by the /metrics endpoint in FastAPI.
        """

        # get the most recent req id from the sorted set

        recent_ids = redis_client . zrevrange ( "metrics:recent", 0, count - 1 )
        #  zrevrange = sorted set range in REVERSE order (newest first)
        # 0 to count-1 = first N items

        metrics = []

        for req_id in recent_ids :

            data = redis_client . get ( f"metrics : { req_id }" )

            if data :

                metrics . append ( json . loads ( data ) )

        return metrics