# Coding Assessment Agent Backend

This project provides the backend infrastructure for a real-time coding assessment agent. It uses FastAPI for the web framework, PostgreSQL for the relational database, Redis for caching and message queues (like chat history), ChromaDB as a vector store for similarity searches, and Langchain with OpenAI for AI-driven interactions.

## Features

- Real-time code analysis via WebSockets.
- AI-powered question generation based on code changes.
- AI-powered evaluation of user responses.
- Session management and interaction tracking.
- Generation of final assessment reports.

## Project Structure

```
coding_assessment_agent/
├── app/                  # Core application code
│   ├── __init__.py
│   ├── main.py           # FastAPI app instance & basic logging
│   ├── config.py         # Environment variables & settings
│   ├── database.py       # DB session management (SQLAlchemy, Redis, Chroma)
│   ├── models.py         # SQLAlchemy ORM models
│   ├── schemas.py        # Pydantic validation models
│   ├── prompts.py        # Langchain prompt templates
│   ├── routers/          # API endpoints
│   │   ├── sessions.py     # REST endpoints for sessions/reports
│   │   └── websocket.py    # WebSocket endpoint
│   ├── services/         # Business logic
│   │   ├── session_service.py
│   │   ├── interaction_service.py
│   │   ├── trigger_logic.py
│   │   ├── context_manager.py
│   │   ├── agent_orchestrator.py
│   │   ├── vector_db_client.py
│   │   └── event_processor.py # Handles incoming WebSocket messages
│   └── websocket_manager.py # Manages active WebSocket connections
├── tests/                # Pytest tests (basic structure)
├── alembic/              # Alembic migration scripts
├── chroma_db_store/      # Default local directory for ChromaDB persistence
├── .env.example          # Example environment variables file
├── .gitignore
├── requirements.txt      # Python dependencies
├── alembic.ini           # Alembic configuration
└── README.md             # This file
```

## Setup

1.  **Clone the repository:**

    ```bash
    git clone <your-repo-url>
    cd coding_assessment_agent
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up databases:**

    - Ensure you have **PostgreSQL** running and accessible. Create a database and user/password.
    - Ensure you have **Redis** running and accessible.

5.  **Configure environment variables:**

    - Copy `.env.example` to `.env` (if `.env.example` exists) or create a new `.env` file.
    - Update the following variables in `.env`:
      - `DATABASE_URL`: Your PostgreSQL connection string (e.g., `postgresql+asyncpg://user:password@host:port/dbname`).
      - `REDIS_URL`: Your Redis connection string (e.g., `redis://localhost:6379/0`).
      - `OPENAI_API_KEY`: Your OpenAI API key.
      - `CHROMA_PERSIST_DIRECTORY`: Path where ChromaDB should store its data locally (defaults to `./chroma_db_store`).

6.  **Apply database migrations:**
    - Make sure your `DATABASE_URL` in `.env` is correct and the database server is running.
    - Run:
      ```bash
      alembic upgrade head
      ```
    - (If making model changes later, generate new migrations with `alembic revision --autogenerate -m "Your migration message"`)

## Running the Application

1.  **Start the FastAPI server:**

    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

    - `--reload`: Enables auto-reloading on code changes (for development).
    - `--host 0.0.0.0`: Makes the server accessible on your network.
    - `--port 8000`: Specifies the port (default is 8000).

2.  The API will be available at `http://localhost:8000`.
3.  Interactive API documentation (Swagger UI) is available at `http://localhost:8000/docs`.
4.  The WebSocket endpoint is at `ws://localhost:8000/ws/session/{session_id}`.

## Running Tests

- (Ensure test database is configured if necessary)
- Run tests using pytest:
  ```bash
  pytest
  ```
  _(Note: Comprehensive tests are not yet fully implemented)_

## API Endpoints

- `GET /`: Basic health check endpoint.
- `POST /sessions/`: Creates a new assessment session.
- `GET /sessions/{session_id}/report/`: Retrieves the final report for a session (if generated).
- `WS /ws/session/{session_id}`: WebSocket connection for real-time interaction.
  - **Client -> Server Messages:**
    - `{"message_type": "code_update", "code": "..."}`
    - `{"message_type": "response_submitted", "interaction_id": ..., "response": "..."}`
  - **Server -> Client Messages:**
    - `{"message_type": "question", "interaction_id": ..., "question": "..."}`
    - `{"message_type": "evaluation_result", "interaction_id": ..., "evaluation": "...", "score": ...}`
    - `{"message_type": "report_ready", "session_id": ...}`
    - `{"error": "..."}`

## Deployment Considerations

- Use a production-grade ASGI server like Uvicorn with Gunicorn workers.
- Use managed services for PostgreSQL and Redis in production.
- Consider a managed Vector Database instead of local ChromaDB persistence for scalability and reliability.
- Configure proper logging (e.g., sending logs to a centralized service).
- Set up HTTPS using a reverse proxy like Nginx or Traefik.
- Implement robust security measures (authentication, authorization, rate limiting).
- Containerize the application using Docker (see `Dockerfile`).
