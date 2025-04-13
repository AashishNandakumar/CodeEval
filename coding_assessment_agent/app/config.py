from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
   database_url: str
   redis_url: str
   openai_api_key: str
   chroma_persist_directory: str = "./chroma_db_store"
   # Add other settings as needed

   class Config:
       env_file = ".env"
       extra = "ignore" # Ignore extra fields not defined in the model

settings = Settings()
