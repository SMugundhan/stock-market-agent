from langchain_groq import ChatGroq   # ChatGroq is LangChain's wrapper for Groq's API

from core.config import config

# initilaize the LLM

# Creating a Groq server using API key

llm = ChatGroq ( api_key = config.GROQ_API_KEY , model_name = config.MODEL_NAME )

# .Invoke () sends msgs to the LLMs and waits for the response
# It is like hitting a send on chat

response = llm.invoke ( "What are the top 3 factors to analyse before nuying a stock?" )

print ( response.content )

