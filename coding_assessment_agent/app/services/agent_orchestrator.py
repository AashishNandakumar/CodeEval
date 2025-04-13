import json
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from app import schemas, models
from app.database import get_llm
from app.prompts import question_generation_prompt, evaluation_prompt, report_generation_prompt
from app.services.context_manager import context_manager, ContextManager
from app.services import interaction_service, session_service
from app.websocket_manager import manager as websocket_manager # Import the singleton manager

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.llm: ChatOpenAI = get_llm()
        self.context_manager: ContextManager = context_manager
        # Langchain Expression Language (LCEL) chains
        self.question_chain = (
            RunnablePassthrough.assign(
                history=lambda x: x.get('history', 'No history yet.'),
                problem_statement=lambda x: x.get('problem_statement', '[Problem statement not provided]')
            )
            | question_generation_prompt
            | self.llm
            | StrOutputParser()
        )
        self.evaluation_chain = (
             RunnablePassthrough.assign(
                history=lambda x: x.get('history', 'No history yet.'),
                problem_statement=lambda x: x.get('problem_statement', '[Problem statement not provided]')
             )
            | evaluation_prompt
            | self.llm
            | StrOutputParser() # Output is expected JSON string
        )
        self.report_chain = (
            RunnablePassthrough.assign(
                full_history=lambda x: x.get('full_history', 'No history.'),
                problem_statement=lambda x: x.get('problem_statement', '[Problem statement not provided]')
            )
            | report_generation_prompt
            | self.llm
            | StrOutputParser()
        )

    async def request_question(self, session_id: int, current_code: str, previous_code: Optional[str], db: AsyncSession):
        """Generates a question based on code changes and sends it via WebSocket."""
        session_id_str = str(session_id)
        try:
            # Fetch the session to get the problem statement
            session = await session_service.get_session(db, session_id)
            if not session:
                logger.error(f"Session {session_id} not found for requesting question.")
                # Consider sending an error via WebSocket
                return
            problem_statement = session.problem_statement

            context = await self.context_manager.prepare_context_for_question(
                session_id=session_id_str,
                current_code=current_code,
                previous_code=previous_code,
                problem_statement=problem_statement # Pass it here
            )
            logger.debug(f"Prepared context for question generation (session {session_id}): {context}")

            question = await self.question_chain.ainvoke(context)
            logger.info(f"Generated question for session {session_id}: {question}")

            # Save the interaction record *before* sending, so we have an ID
            interaction_record = await interaction_service.create_interaction(
                db, schemas.InteractionCreate(
                    session_id=session_id,
                    interaction_type="question_asked",
                    data={"question": question}
                )
            )

            # Send question via WebSocket
            await websocket_manager.send_personal_message(session_id_str, {
                "message_type": "question",
                "interaction_id": interaction_record.id,
                "question": question
            })

            # Add AI question to history
            await self.context_manager.add_ai_message(session_id_str, question)

        except Exception as e:
            logger.error(f"Error requesting question for session {session_id}: {e}", exc_info=True)
            # Notify the user via WebSocket
            try:
                await websocket_manager.send_personal_message(session_id_str, {"error": f"Failed to generate question. Error: {str(e)}"})
            except Exception as ws_err:
                logger.error(f"Failed to send error message via WebSocket for session {session_id}: {ws_err}")

    async def evaluate_response(self, session_id: int, response_payload: schemas.ResponseSubmittedPayload, db: AsyncSession):
        """Evaluates a user's response, updates the interaction, and sends results via WebSocket."""
        session_id_str = str(session_id)
        try:
            # Fetch the session to get the problem statement
            session = await session_service.get_session(db, session_id)
            if not session:
                logger.error(f"Session {session_id} not found for evaluating response.")
                await websocket_manager.send_personal_message(session_id_str, {"error": f"Session {session_id} not found."})
                return
            problem_statement = session.problem_statement

            # Retrieve the original interaction (question) to get the question text and code context
            original_interaction = await interaction_service.get_interaction(db, response_payload.interaction_id)
            if not original_interaction or original_interaction.session_id != session_id:
                error_msg = f"Original interaction {response_payload.interaction_id} not found or mismatch for session {session_id}"
                logger.warning(error_msg)
                await websocket_manager.send_personal_message(session_id_str, {"error": error_msg})
                return

            question = original_interaction.data.get("question", "[Question not found]")
            # Find the code snapshot associated with the question interaction.
            # --- Current Simplification ---:
            # Assumes the most recent snapshot *before* the evaluation request is relevant.
            # This might be incorrect if multiple code updates happened before a response.
            # Future Improvement: Store the relevant snapshot_id with the question interaction.
            # Or, traverse interactions backward from the question to find the last snapshot.
            latest_snapshot_interaction = await db.execute(
                select(models.Interaction)
                .join(models.CodeSnapshot, models.Interaction.id == models.CodeSnapshot.interaction_id)
                .where(models.Interaction.session_id == session_id, models.Interaction.timestamp < original_interaction.timestamp)
                .options(joinedload(models.Interaction.code_snapshot))
                .order_by(models.Interaction.timestamp.desc())
                .limit(1)
            )
            relevant_interaction_with_snapshot = latest_snapshot_interaction.scalar_one_or_none()
            relevant_code = relevant_interaction_with_snapshot.code_snapshot.code_content if relevant_interaction_with_snapshot and relevant_interaction_with_snapshot.code_snapshot else "[Code context not available]"

            # Add user response to history *before* evaluation
            await self.context_manager.add_user_message(session_id_str, response_payload.response)

            context = await self.context_manager.prepare_context_for_evaluation(
                session_id=session_id_str,
                question=question,
                response=response_payload.response,
                relevant_code=relevant_code,
                problem_statement=problem_statement # Pass it here
            )
            logger.debug(f"Prepared context for evaluation (session {session_id}, interaction {response_payload.interaction_id}): {context}")

            evaluation_json_str = await self.evaluation_chain.ainvoke(context)
            logger.info(f"Generated evaluation for session {session_id}, interaction {response_payload.interaction_id}: {evaluation_json_str}")

            # Clean the LLM output: remove potential markdown fences and whitespace
            cleaned_json_str = evaluation_json_str.strip()
            if cleaned_json_str.startswith("```json"):
                cleaned_json_str = cleaned_json_str[7:] # Remove ```json
            if cleaned_json_str.startswith("```"):
                 cleaned_json_str = cleaned_json_str[3:] # Remove ```
            if cleaned_json_str.endswith("```"):
                cleaned_json_str = cleaned_json_str[:-3] # Remove ```
            cleaned_json_str = cleaned_json_str.strip() # Strip again just in case

            # Parse evaluation JSON
            try:
                evaluation_result = json.loads(cleaned_json_str) # Use the cleaned string
                # Validate expected keys
                if not all(k in evaluation_result for k in ["evaluation_text", "score"]):
                    raise ValueError("Evaluation JSON missing required keys ('evaluation_text', 'score')")
                evaluation_text = evaluation_result.get("evaluation_text", "Evaluation failed.")
                score = float(evaluation_result.get("score", 0.0)) # Ensure score is float
            except (json.JSONDecodeError, ValueError) as parse_error:
                logger.error(f"Failed to parse or validate evaluation JSON: {evaluation_json_str}. Cleaned string was: {cleaned_json_str}. Error: {parse_error}")
                evaluation_text = f"Failed to process evaluation result: {parse_error}"
                score = 0.0
                # Send error back to client
                await websocket_manager.send_personal_message(session_id_str, {
                    "error": "Failed to parse evaluation result from AI.",
                    "interaction_id": response_payload.interaction_id
                })
                # Optionally, still save the failed evaluation attempt?
                # return # Or continue to save the failed state

            # Update the interaction record with evaluation data
            updated_data = original_interaction.data.copy()
            updated_data['evaluation'] = {"text": evaluation_text, "score": score}
            await interaction_service.update_interaction(db, response_payload.interaction_id, {"data": updated_data})

            # Send evaluation result via WebSocket
            await websocket_manager.send_personal_message(session_id_str, {
                "message_type": "evaluation_result",
                "interaction_id": response_payload.interaction_id,
                "evaluation": evaluation_text,
                "score": score
            })

            # Add AI evaluation to history (maybe just the text part)
            await self.context_manager.add_ai_message(session_id_str, f"Evaluation: {evaluation_text} (Score: {score})")

        except Exception as e:
            logger.error(f"Error evaluating response for session {session_id}, interaction {response_payload.interaction_id}: {e}", exc_info=True)
            # Notify the user via WebSocket
            try:
                await websocket_manager.send_personal_message(session_id_str, {"error": f"Failed to evaluate response. Error: {str(e)}", "interaction_id": response_payload.interaction_id})
            except Exception as ws_err:
                 logger.error(f"Failed to send error message via WebSocket for session {session_id}: {ws_err}")

    async def generate_report(self, session_id: int, db: AsyncSession):
        """Generates a final report for the session and saves it."""
        session_id_str = str(session_id)
        try:
            # Fetch the session to get the problem statement
            session = await session_service.get_session(db, session_id)
            if not session:
                logger.error(f"Session {session_id} not found for generating report.")
                # Consider sending an error via WebSocket
                return
            problem_statement = session.problem_statement

            # --- Get Final Code State ---
            last_snapshot_interaction_result = await db.execute(
                 select(models.Interaction)
                 .join(models.CodeSnapshot, models.Interaction.id == models.CodeSnapshot.interaction_id)
                .where(models.Interaction.session_id == session_id)
                .options(joinedload(models.Interaction.code_snapshot))
                .order_by(models.Interaction.timestamp.desc())
                .limit(1)
            )
            last_snapshot_interaction = last_snapshot_interaction_result.scalar_one_or_none()
            final_code = last_snapshot_interaction.code_snapshot.code_content if last_snapshot_interaction and last_snapshot_interaction.code_snapshot else "[No final code snapshot found]"

            # --- Prepare Context (History + Problem Statement) ---
            context = await self.context_manager.prepare_context_for_report(
                session_id=session_id_str,
                final_code=final_code,
                problem_statement=problem_statement # Pass it here
            )
            logger.debug(f"Prepared context for report generation (session {session_id}): {context}")

            # --- Generate Report Content (LLM Call) ---
            report_content = await self.report_chain.ainvoke(context)
            logger.info(f"Generated report content for session {session_id}")

            # --- Calculate Average Score ---
            interactions_result = await db.execute(
                select(models.Interaction)
                .where(models.Interaction.session_id == session_id)
                .order_by(models.Interaction.timestamp.asc())
            )
            interactions = interactions_result.scalars().all()

            scores_list = []
            for interaction in interactions:
                if interaction.data and isinstance(interaction.data.get("evaluation"), dict):
                    score = interaction.data["evaluation"].get("score")
                    if score is not None:
                        try:
                            scores_list.append(float(score))
                        except (ValueError, TypeError):
                            logger.warning(f"Could not convert score '{score}' to float for interaction {interaction.id}")

            average_score = sum(scores_list) / len(scores_list) if scores_list else 0.0
            scores_dict = {
                "average_score": average_score,
                "individual_scores": scores_list
            }
            logger.info(f"Calculated scores for session {session_id}: {scores_dict}")

            # --- Save the Report ---
            report_schema = schemas.ReportCreate(
                session_id=session_id,
                report_content=report_content,
                scores=scores_dict # Use the calculated scores
            )
            await session_service.create_report(db, session_id, report_schema)
            logger.info(f"Report saved for session {session_id}")

            # Optionally mark session as ended if not already (redundant if triggered by end_session)
            # await session_service.end_session(db, session_id)

            # --- Notify User ---
            await websocket_manager.send_personal_message(session_id_str, {
                "message_type": "report_ready",
                "session_id": session_id
            })
            logger.info(f"Report ready notification sent for session {session_id}")

        except Exception as e:
            logger.error(f"Error generating report for session {session_id}: {e}", exc_info=True)
            # Notify user via WebSocket
            try:
                await websocket_manager.send_personal_message(session_id_str, {"error": f"Failed to generate report. Error: {str(e)}"})
            except Exception as ws_err:
                 logger.error(f"Failed to send error message via WebSocket for session {session_id}: {ws_err}")

# Singleton instance
agent_orchestrator = AgentOrchestrator()
