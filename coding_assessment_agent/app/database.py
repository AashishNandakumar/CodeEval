from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import redis.asyncio as redis
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.chat_message_histories import RedisChatMessageHistory
from app.config import settings

# SQLAlchemy Async Engine
async_engine = create_async_engine(settings.database_url, echo=True) # echo=True for debugging
AsyncSessionFactory = sessionmaker(
   bind=async_engine, class_=AsyncSession, expire_on_commit=False
)

# Base for SQLAlchemy models (will be imported in models.py)
Base = declarative_base()

# Redis Async Connection Pool
redis_pool = redis.ConnectionPool.from_url(settings.redis_url, decode_responses=True)

# --- LLM Initialization ---
llm = ChatOpenAI(openai_api_key=settings.openai_api_key, model_name="gpt-4o") # Or specify another model

# --- Chat History Factory ---
def get_redis_chat_history(session_id: str) -> RedisChatMessageHistory:
    # Constructs a unique Redis key for each session's chat history
    return RedisChatMessageHistory(session_id=f"chat_history:{session_id}", url=settings.redis_url)

# ChromaDB Client & Langchain Vector Store
embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
vector_store = Chroma(
   persist_directory=settings.chroma_persist_directory,
   embedding_function=embeddings
)

async def get_db() -> AsyncSession:
   async with AsyncSessionFactory() as session:
       yield session

async def get_redis():
   # Ensure the connection is established from the pool
   return redis.Redis(connection_pool=redis_pool)

def get_vector_store():
   # Chroma client might need initialization checks in a real app
   return vector_store

# --- Function to get LLM instance ---
def get_llm():
    return llm
