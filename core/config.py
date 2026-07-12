import os # os module lets python talk to ur operating system, like reading env variables

from dotenv import load_dotenv # this loads env variables from a .env file into the environment

load_dotenv() # call the function to load the env variables

def get_version ( ) -> str :

    try :

        with open ( "VERSION", "r" ) as f :

            return f.read().strip()
        
    except FileNotFoundError :

        return os . getenv ( "APP_VERSION", "0.1.0" )


class Config:

    # os.getenv() is used to get the value of an environment variable, if it doesn't exist it returns None
    GROQ_API_KEY = os.getenv("GROQ_API_KEY") # get the GROQ_API_KEY from env variables

    TAVILY_API_KEY = os.getenv("TAVIL_API_KEY") # get the TAVIL_API_KEY from env variables

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379") # get the REDIS_URL from env variables

    MODEL_NAME = "openai/gpt-oss-120b" # this is the name of the model we want to use, in this case it's a smaller version of the llma-3.1 model, which is optimized for faster inference and lower resource usage, making it suitable for applications that require quick responses and have limited computational resources.

    MAX_TOKENS = 1024 # this is the maximum number of tokens that the model will generate in response to a prompt, setting a limit on the length of the generated output to prevent excessively long responses and manage resource usage effectively.

    APP_VERSION = "1.0.0"

config = Config() # create an instance of the Config class to access the configuration settings throughout the application