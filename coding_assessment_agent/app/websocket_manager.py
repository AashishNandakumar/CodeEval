from fastapi import WebSocket
from typing import Dict, List
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Simple in-memory store. Replace with Redis/other for scalability.
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session: {session_id}")
        else:
            logger.warning(f"Attempted to disconnect non-existent WebSocket for session: {session_id}")

    async def send_personal_message(self, session_id: str, message: dict):
        websocket = self.active_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_json(message)
                logger.debug(f"Sent message to session {session_id}: {message}")
            except Exception as e:
                logger.error(f"Error sending message to session {session_id}: {e}")
                # Consider disconnecting if send fails repeatedly
                # self.disconnect(session_id)
        else:
            logger.warning(f"Attempted to send message to inactive session: {session_id}")

    async def broadcast(self, message: dict): # Optional: If broadcasting is needed
        message_json = json.dumps(message)
        # Use asyncio.gather for concurrent sends
        results = await asyncio.gather(
            *[conn.send_text(message_json) for conn in self.active_connections.values()],
            return_exceptions=True
        )
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error broadcasting message: {result}")

# Singleton instance
manager = WebSocketManager()
