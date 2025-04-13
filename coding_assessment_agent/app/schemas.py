from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import datetime

# Base Pydantic model configuration
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True # Renamed from orm_mode in Pydantic v2

# --- CodeSnapshot Schemas ---
class CodeSnapshotBase(BaseSchema):
    code_content: str
    # diff_content: Optional[str] = None

class CodeSnapshotCreate(CodeSnapshotBase):
    interaction_id: int

class CodeSnapshotRead(CodeSnapshotBase):
    id: int
    interaction_id: int
    timestamp: datetime.datetime

# --- Interaction Schemas ---
class InteractionBase(BaseSchema):
    interaction_type: str
    data: Dict[str, Any]

class InteractionCreate(InteractionBase):
    session_id: int

class InteractionRead(InteractionBase):
    id: int
    session_id: int
    timestamp: datetime.datetime
    code_snapshot: Optional[CodeSnapshotRead] = None # Include related snapshot if available

# --- Report Schemas ---
class ReportBase(BaseSchema):
    report_content: str
    scores: Optional[Dict[str, Any]] = None

class ReportCreate(ReportBase):
    session_id: int

class ReportRead(ReportBase):
    id: int
    session_id: int
    generation_time: datetime.datetime

# --- Session Schemas ---
class SessionBase(BaseSchema):
    pass # No specific fields in base session for now

class SessionCreate(SessionBase):
    pass # No input needed to create a session initially

class SessionRead(SessionBase):
    id: int
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime] = None
    report: Optional[ReportRead] = None
    interactions: List[InteractionRead] = []

# --- WebSocket Payload Schemas ---
class CodeUpdatePayload(BaseModel):
    session_id: str # Using string here as it comes from WebSocket path param
    code: str
    # potentially add file path, cursor position etc.

class ResponseSubmittedPayload(BaseModel):
    session_id: str
    interaction_id: int # ID of the interaction (question) being responded to
    response: str

# --- API Response Schemas ---
class QuestionResponse(BaseModel):
    interaction_id: int
    question: str
