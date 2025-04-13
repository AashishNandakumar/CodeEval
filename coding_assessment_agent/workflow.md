# Coding Assessment Agent: End-to-End Workflow

This document outlines the typical flow of events and data within the backend application.

**Core Components:**

- **FastAPI:** Serves REST API endpoints and handles WebSocket connections.
- **PostgreSQL (via SQLAlchemy):** Stores persistent data like sessions, interactions, code snapshots, and final reports.
- **Redis:** Used for managing Langchain chat message history for each session (providing context memory).
- **ChromaDB (via Langchain):** Acts as a vector store for relevant context retrieval during AI interactions (though current implementation might be basic).
- **Langchain:** Orchestrates interactions with the LLM (OpenAI), manages prompts, context, and chains.
- **OpenAI:** The Large Language Model used for generating questions, evaluating responses, and creating reports.
- **WebSockets:** Enables real-time, bidirectional communication between the client (frontend) and the backend.

**Workflow Steps:**

1.  **Session Initiation:**

    - **Trigger:** The client (e.g., a web frontend) initiates a new assessment.
    - **Action:** Client sends a `POST` request to the `/sessions/` REST API endpoint.
    - **Backend Process:**
      - The request is routed to the `create_new_session` function in `app/routers/sessions.py`.
      - This function calls the `create_session` service in `app/services/session_service.py`.
      - `session_service` creates a new `Session` record in the PostgreSQL database with a unique ID and timestamps.
      - The newly created `session_id` is returned in the API response.

2.  **WebSocket Connection:**

    - **Trigger:** The client receives the `session_id` from the previous step.
    - **Action:** Client establishes a WebSocket connection to the backend endpoint: `ws://<host>:<port>/ws/session/{session_id}`.
    - **Backend Process:**
      - FastAPI routes the connection request to the `websocket_endpoint` function in `app/routers/websocket.py`.
      - This function accepts the connection and uses the `WebSocketManager` (`app/websocket_manager.py`) to register the active connection, associating it with the `session_id`.

3.  **Real-time Code Submission & Analysis:**

    - **Trigger:** The user types code in the frontend editor.
    - **Action:** The client periodically (or on significant changes) sends the current code snapshot via the established WebSocket connection using a JSON message: `{"message_type": "code_update", "code": "..."}`.
    - **Backend Process:**
      - The `websocket_endpoint` in `app/routers/websocket.py` receives the message.
      - It validates the message structure and type.
      - It calls `process_websocket_message` in `app/services/event_processor.py`, passing the message payload and database session.
      - `event_processor` calls `interaction_service.create_interaction` and `interaction_service.create_code_snapshot` to save the event and the code content to PostgreSQL.
      - `event_processor` retrieves the previous interaction for context.
      - `event_processor` calls `trigger_logic.should_trigger_interaction`. This function analyzes the code change (size of diff using `difflib`) and the time elapsed since the last interaction based on predefined rules (`MIN_CODE_CHANGE_LINES`, `MIN_TIME_BETWEEN_INTERACTIONS`).

4.  **AI Question Generation (Triggered):**

    - **Trigger:** `trigger_logic.should_trigger_interaction` returns `True`.
    - **Backend Process:**
      - `event_processor` calls `agent_orchestrator.request_question`.
      - `agent_orchestrator` prepares the context by calling `context_manager.prepare_context_for_question`. This involves:
        - Fetching the session's chat history from Redis (`RedisChatMessageHistory`).
        - Potentially performing a similarity search on ChromaDB using `vector_db_client` based on the code diff to find relevant documents or past interactions (this step might be simplified currently).
      - The prepared context (history, relevant docs, current code/diff) is passed to the Langchain `question_chain` (defined in `agent_orchestrator` using `prompts.question_generation_prompt` and the OpenAI LLM).
      - The LLM generates a relevant question based on the context and code changes.
      - `agent_orchestrator` saves this interaction (question text, interaction type `question_asked`) via `interaction_service`.
      - The AI's question is added to the session's chat history in Redis via `context_manager`.
      - `agent_orchestrator` uses the `WebSocketManager` to send the generated question back to the specific client. Message: `{"message_type": "question", "interaction_id": ..., "question": "..."}`.

5.  **User Response Submission:**

    - **Trigger:** The user receives the question on the frontend and submits their answer.
    - **Action:** The client sends the response via WebSocket. Message: `{"message_type": "response_submitted", "interaction_id": <id_of_question>, "response": "..."}`.
    - **Backend Process:**
      - `websocket_endpoint` receives and validates the message.
      - It calls `process_websocket_message` in `event_processor`.
      - `event_processor` saves the response interaction (type `response_received`) via `interaction_service`.
      - `event_processor` calls `agent_orchestrator.evaluate_response`.

6.  **AI Response Evaluation:**

    - **Trigger:** `agent_orchestrator.evaluate_response` is called.
    - **Backend Process:**
      - `agent_orchestrator` retrieves the original question using the `interaction_id` from the payload via `interaction_service`.
      - It identifies the relevant code context associated with that question (current logic finds the last snapshot _before_ the question).
      - The user's response is added to the chat history in Redis via `context_manager`.
      - `agent_orchestrator` prepares context for evaluation via `context_manager.prepare_context_for_evaluation` (history, question, response, code context, maybe ChromaDB search).
      - The context is passed to the Langchain `evaluation_chain` (using `prompts.evaluation_prompt` and the LLM).
      - The LLM generates an evaluation, expected in a JSON format containing evaluation text and a score.
      - `agent_orchestrator` parses the JSON response from the LLM.
      - The evaluation details (text, score) are added to the original question's `Interaction` record in PostgreSQL via `interaction_service`.
      - The AI's evaluation is added to the chat history in Redis via `context_manager`.
      - `agent_orchestrator` uses `WebSocketManager` to send the evaluation result back to the client. Message: `{"message_type": "evaluation_result", "interaction_id": ..., "evaluation": "...", "score": ...}`.

7.  **Session Completion & Report Generation:**

    - **Trigger:** Can be initiated by the client (e.g., clicking "Finish Assessment"). This could be a specific WebSocket message or a REST API call (e.g., `POST /sessions/{session_id}/generate-report`).
    - **Backend Process (assuming REST trigger):**
      - A dedicated endpoint in `app/routers/sessions.py` handles the request.
      - It calls `agent_orchestrator.generate_report`.
      - `agent_orchestrator` fetches the "final" code (e.g., the last saved `CodeSnapshot`).
      - It prepares context via `context_manager.prepare_context_for_report`, primarily getting the full chat history summary from Redis.
      - The context is passed to the Langchain `report_chain` (using `prompts.report_generation_prompt` and the LLM).
      - The LLM generates the final assessment report content.
      - `agent_orchestrator` calls `session_service.create_report` to save the report content to the `Report` table in PostgreSQL, linked to the session.
      - Optionally, the session can be marked as completed in the `Session` table.
      - Optionally, a notification `{"message_type": "report_ready", "session_id": ...}` can be sent via WebSocket.

8.  **Report Retrieval:**
    - **Trigger:** The client wants to view the generated report.
    - **Action:** Client sends a `GET` request to the `/sessions/{session_id}/report/` REST endpoint.
    - **Backend Process:**
      - The request is routed to `get_session_report` in `app/routers/sessions.py`.
      - This function calls `session_service.get_report`.
      - `session_service` queries PostgreSQL for the `Report` associated with the `session_id`.
      - The report content is returned in the API response.
