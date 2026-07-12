import redis

import json

from core.config import Config

# Creating a redis connection
redis_client = redis. from_url ( Config. REDIS_URL, decode_responses = True ) # decode_response returns strings instead of bytes
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
