import difflib
from typing import Dict, Any, List, Optional
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from app.services.vector_db_client import vector_db_client # Import the singleton client
from app.database import get_redis_chat_history
import logging

logger = logging.getLogger(__name__)

# Configuration for context management
MAX_HISTORY_MESSAGES = 10 # Limit the number of recent messages fetched
MAX_SIMILARITY_RESULTS = 3 # Limit the number of documents from vector search

class ContextManager:

    def _format_history(self, history: List[BaseMessage]) -> str:
        """Formats Langchain message history into a simple string."""
        if not history:
            return "No history yet."
        formatted = []
        for msg in history[-MAX_HISTORY_MESSAGES:]: # Get only the most recent messages
            role = "User" if isinstance(msg, HumanMessage) else "AI" if isinstance(msg, AIMessage) else "System"
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)

    def _calculate_diff(self, old_code: Optional[str], new_code: str) -> str:
        """Calculates unified diff between old and new code."""
        if old_code is None:
            old_code = ""
        diff = difflib.unified_diff(
            old_code.splitlines(keepends=True),
            new_code.splitlines(keepends=True),
            fromfile="previous_code",
            tofile="current_code",
            lineterm='\n'
        )
        return '\n'.join(diff)

    async def prepare_context_for_question(
        self, session_id: str, current_code: str, previous_code: Optional[str], problem_statement: str
    ) -> Dict[str, Any]:
        """Prepares context for the question generation prompt."""
        history_manager = get_redis_chat_history(session_id)
        chat_history_messages = await history_manager.aget_messages()
        formatted_history = self._format_history(chat_history_messages)

        diff = self._calculate_diff(previous_code, current_code)

        # Potential: Add similarity search based on diff or code snippet
        # relevant_docs = await vector_db_client.similarity_search(query=diff, k=1, filter_metadata={...})

        context = {
            "problem_statement": problem_statement,
            "code": current_code,
            "diff": diff if diff else "No changes detected or first submission.",
            "history": formatted_history,
            # "relevant_docs": relevant_docs # Add if similarity search is used
        }
        return context

    async def prepare_context_for_evaluation(
        self, session_id: str, question: str, response: str, relevant_code: str, problem_statement: str
    ) -> Dict[str, Any]:
        """Prepares context for the evaluation prompt."""
        history_manager = get_redis_chat_history(session_id)
        # Get history *before* the current question/response pair if possible
        # This might require more sophisticated history management
        chat_history_messages = await history_manager.aget_messages()
        formatted_history = self._format_history(chat_history_messages)

        # Potential: Add similarity search based on question/response
        # relevant_docs = await vector_db_client.similarity_search(query=f"{question}\n{response}", k=2)

        context = {
            "problem_statement": problem_statement,
            "code": relevant_code,
            "history": formatted_history,
            "question": question,
            "response": response,
            # "relevant_docs": relevant_docs
        }
        return context

    async def prepare_context_for_report(
        self, session_id: str, final_code: str, problem_statement: str
    ) -> Dict[str, Any]:
        """Prepares context for the final report generation prompt."""
        history_manager = get_redis_chat_history(session_id)
        # Get the full history for the report
        full_history_messages = await history_manager.aget_messages()
        # Format history including all details (maybe custom formatting needed)
        formatted_full_history = self._format_history(full_history_messages) # Use basic for now

        context = {
            "problem_statement": problem_statement,
            "final_code": final_code,
            "full_history": formatted_full_history,
        }
        return context

    async def add_user_message(self, session_id: str, message: str):
        """Adds a user message to the chat history."""
        history_manager = get_redis_chat_history(session_id)
        history_manager.add_user_message(message)
        logger.debug(f"Added user message for session {session_id}")

    async def add_ai_message(self, session_id: str, message: str):
        """Adds an AI message to the chat history."""
        history_manager = get_redis_chat_history(session_id)
        history_manager.add_ai_message(message)
        logger.debug(f"Added AI message for session {session_id}")

    async def get_full_history_summary(self, session_id: str) -> str:
        # Implementation of get_full_history_summary method
        pass

# Singleton instance or inject via dependency
context_manager = ContextManager()
