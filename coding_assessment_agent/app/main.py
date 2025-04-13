from fastapi import FastAPI
# Import routers later
from app.routers import sessions, websocket # Import the routers
import logging
import sys

# enable cors
from fastapi.middleware.cors import CORSMiddleware  


# Basic Logging Configuration
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level to DEBUG
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout) # Log to standard output
        # You might want to add logging.FileHandler("app.log") later
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Coding Assessment Agent Backend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
   logger.info("Root endpoint accessed") # Example log
   return {"message": "Assessment Agent Backend is running"}

# Include routers later:
app.include_router(sessions.router)
app.include_router(websocket.router)
