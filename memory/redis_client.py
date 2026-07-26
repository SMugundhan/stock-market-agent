import redis

import json

from core.config import config

# Creating a redis connection
redis_client = redis. from_url ( config. REDIS_URL,
                                decode_responses = True ,
                                socket_timeout=5,            # give up waiting on a stuck command after 5s
                                socket_connect_timeout=5,    # give up trying to connect after 5s
                                retry_on_timeout=True,       # retry once automatically if a command times out
                                health_check_interval=30     # proactively pings the connection every 30s to keep it alive / detect drops early
                                ) # decode_response returns strings instead of bytes
# Eg: AAPL -> b'AAPL' bytes


def test_connection ():

    """ Quick test to verify Redis is reachable """

    try :

        redis_client. ping()

        print ( " Reddis connected successfully " )

        return True
    
    except redis.ConnectionError:

        print ( " Reddis connection failed " )

        return False
