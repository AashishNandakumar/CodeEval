from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, models
from app.services import interaction_service, trigger_logic
from app.services.agent_orchestrator import agent_orchestrator # Import the singleton orchestrator
from app.websocket_manager import manager # Import the singleton manager
import logging

logger = logging.getLogger(__name__)

async def process_websocket_message(
    session_id_str: str, # From WebSocket path
    message_type: str,
    payload: schemas.CodeUpdatePayload | schemas.ResponseSubmittedPayload,
    db: AsyncSession,
    # agent_orchestrator: AgentOrchestrator # Pass orchestrator instance
):
    """Processes incoming messages from the WebSocket connection."""
    try:
        session_id = int(session_id_str) # Convert session_id from path param to int
    except ValueError:
        logger.error(f"Invalid session_id format received: {session_id_str}")
        await manager.send_personal_message(session_id_str, {"error": "Invalid session ID format"})
        return

    try: # Add top-level try-except for processing logic
        if message_type == "code_update":
            if not isinstance(payload, schemas.CodeUpdatePayload):
                 logger.error("Payload type mismatch for code_update") # Should not happen if routing is correct
                 return

            logger.info(f"Processing code_update for session {session_id}")
            current_code = payload.code

            # 1. Save the interaction and snapshot
            interaction_record = await interaction_service.create_interaction(
                db,
                schemas.InteractionCreate(
                    session_id=session_id,
                    interaction_type="code_snapshot",
                    data={"message": "Code update received"} # Store minimal data for now
                )
            )
            await interaction_service.create_code_snapshot(
                db,
                schemas.CodeSnapshotCreate(
                    interaction_id=interaction_record.id,
                    code_content=current_code
                )
            )

            # 2. Check trigger logic
            # Get the *previous* interaction that might have had a snapshot or represents the last prompt time
            # This logic might need refinement: should we look for the last 'code_snapshot' type or just the very last one?
            # Let's find the most recent interaction *before* the one we just created.
            last_interaction = await interaction_service.get_last_interaction(db, session_id)

            # Find the code content associated with the last_interaction (if it has a snapshot)
            previous_code_content = None
            if last_interaction and last_interaction.code_snapshot:
                 previous_code_content = last_interaction.code_snapshot.code_content

            should_prompt = await trigger_logic.should_trigger_interaction(
                current_code=current_code,
                last_interaction=last_interaction
            )

            if should_prompt:
                logger.info(f"Triggering interaction for session {session_id}")
                # 3. Call AgentOrchestrator (Phase 5)
                # Pass previous code content for diff calculation inside orchestrator
                await agent_orchestrator.request_question(
                    session_id=session_id,
                    current_code=current_code,
                    previous_code=previous_code_content,
                    db=db
                )
            else:
                logger.info(f"Interaction trigger condition not met for session {session_id}")
                # Optionally send an ack back?
                # await manager.send_personal_message(session_id_str, {"status": "code_update_processed"})

        elif message_type == "response_submitted":
            if not isinstance(payload, schemas.ResponseSubmittedPayload):
                 logger.error("Payload type mismatch for response_submitted")
                 return

            logger.info(f"Processing response_submitted for session {session_id}")
            response_payload: schemas.ResponseSubmittedPayload = payload # Type assertion

            # 1. Save the response interaction
            await interaction_service.create_interaction(
                db,
                schemas.InteractionCreate(
                    session_id=session_id,
                    interaction_type="response_received",
                    data={"response": response_payload.response, "original_interaction_id": response_payload.interaction_id}
                )
            )

            # 2. Call AgentOrchestrator for evaluation (Phase 5)
            await agent_orchestrator.evaluate_response(
                session_id=session_id,
                response_payload=response_payload,
                db=db
            )

        else:
            # This case should ideally be handled in the websocket router already
            logger.warning(f"process_websocket_message called with unknown message_type: {message_type}")
            await manager.send_personal_message(session_id_str, {"error": f"Internal error: Unknown message type '{message_type}' reached processor."})

    except Exception as e:
        logger.error(f"Unhandled exception during processing message for session {session_id_str}: {e}", exc_info=True)
        # Notify the client about the unexpected error
        try:
            await manager.send_personal_message(session_id_str, {
                "error": f"An unexpected internal error occurred while processing your '{message_type}' request. Please try again or contact support if the issue persists."
            })
        except Exception as ws_err:
            logger.error(f"Failed to send internal error notification via WebSocket for session {session_id_str}: {ws_err}") 