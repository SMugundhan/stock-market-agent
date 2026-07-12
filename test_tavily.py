from tavily import TavilyClient

import os

from dotenv import load_dotenv

load_dotenv()

client = TavilyClient( api_key = os.getenv("TAVIL_API_KEY") )

results = client.search ( " Apple AAPL stock news today " )

for i in results [ "results" ][ :3 ]:

    print ( f" Title : { i [ 'title' ] } " )

    print ( f" Content : { i [ 'content' ][ :100 ] } " )

    print ( " --- " )