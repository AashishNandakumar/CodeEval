from fastapi import FastAPI
# Import routers later
from app.routers import sessions, websocket # Import the routers
import logging
import sys

# Basic Logging Configuration
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout) # Log to standard output
        # You might want to add logging.FileHandler("app.log") later
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Coding Assessment Agent Backend")

@app.get("/")
async def root():
   logger.info("Root endpoint accessed") # Example log
   return {"message": "Assessment Agent Backend is running"}

# Include routers later:
app.include_router(sessions.router)
app.include_router(websocket.router)
