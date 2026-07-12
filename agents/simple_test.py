from langchain_groq import ChatGroq   # ChatGroq is LangChain's wrapper for Groq's API

from core.config import Config

# initilaize the LLM

# Creating a Groq server using API key

llm = ChatGroq ( api_key = Config.GROQ_API_KEY , model_name = Config.MODEL_NAME )

# .Invoke () sends msgs to the LLMs and waits for the response
# It is like hitting a send on chat

response = llm.invoke ( "What are the top 3 factors to analyse before nuying a stock?" )

print ( response.content )

