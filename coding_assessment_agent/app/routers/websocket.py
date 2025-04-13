from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas
from app.websocket_manager import manager
from app.database import get_db
from app.services.event_processor import process_websocket_message
# Import AgentOrchestrator if needed directly here, or pass via dependency
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, db: AsyncSession = Depends(get_db)):
    await manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            logger.debug(f"Received message from {session_id}: {data}")

            # Basic validation / routing
            if "message_type" not in data:
                error_msg = "Invalid message format: Missing 'message_type' field."
                logger.warning(f"{error_msg} from {session_id}")
                await manager.send_personal_message(session_id, {"error": error_msg})
                continue

            message_type = data["message_type"]
            payload_obj = None # Initialize payload_obj

            try:
                session_id_int = int(session_id)
                if message_type == "code_update":
                    # Ensure 'code' key exists for code_update type
                    if "code" not in data:
                        raise ValueError("Missing 'code' field for code_update message.")
                    payload_obj = schemas.CodeUpdatePayload(**data, session_id=session_id_int)

                elif message_type == "response_submitted":
                    # Ensure required keys exist for response_submitted type
                    if "response" not in data or "interaction_id" not in data:
                        raise ValueError("Missing 'response' or 'interaction_id' field for response_submitted message.")
                    payload_obj = schemas.ResponseSubmittedPayload(**data, session_id=session_id_int)

                else:
                    error_msg = f"Received unknown message_type '{message_type}' from {session_id}"
                    logger.warning(error_msg)
                    await manager.send_personal_message(session_id, {"error": error_msg})
                    continue # Skip processing if message type is unknown

                # If payload was successfully parsed, process it
                if payload_obj:
                    await process_websocket_message(
                        session_id_str=session_id,
                        message_type=message_type,
                        payload=payload_obj,
                        db=db
                    )

            except (ValueError, TypeError, KeyError) as validation_error: # Catch Pydantic/validation errors
                error_msg = f"Invalid message payload for type '{message_type}': {validation_error}"
                logger.error(f"Error processing message from {session_id}: {error_msg}", exc_info=True)
                await manager.send_personal_message(session_id, {"error": error_msg})
            except Exception as e: # Catch unexpected processing errors
                error_msg = f"An unexpected error occurred processing your request: {str(e)}"
                logger.error(f"Unexpected error processing message from {session_id}: {e}", exc_info=True)
                await manager.send_personal_message(session_id, {"error": error_msg})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally for session: {session_id}")
    except Exception as e:
        error_msg = f"WebSocket connection error for session {session_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        # Note: We can't send a message if the socket is already closed/errored
    finally:
        manager.disconnect(session_id)
        logger.info(f"Cleaned up connection for session: {session_id}")
