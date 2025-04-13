from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base # Import Base from database.py
import datetime

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    problem_statement = Column(Text, nullable=False) # Added field for the initial question
    # Link to report (one-to-one)
    report = relationship("Report", back_populates="session", uselist=False)
    # Link to interactions (one-to-many)
    interactions = relationship("Interaction", back_populates="session")

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    interaction_type = Column(String) # e.g., 'code_snapshot', 'question_asked', 'response_received', 'evaluation'
    data = Column(JSON) # Flexible store for various data types (question, response, scores)

    # Link back to session (many-to-one)
    session = relationship("Session", back_populates="interactions")
    # Link to code snapshot (optional, one-to-one)
    code_snapshot = relationship("CodeSnapshot", back_populates="interaction", uselist=False)

class CodeSnapshot(Base):
    __tablename__ = "code_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    code_content = Column(Text)
    # Optionally store diff from previous snapshot
    # diff_content = Column(Text, nullable=True)

    # Link back to interaction (one-to-one)
    interaction = relationship("Interaction", back_populates="code_snapshot")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), unique=True) # Ensure one report per session
    generation_time = Column(DateTime(timezone=True), server_default=func.now())
    report_content = Column(Text) # The generated report text
    scores = Column(JSON, nullable=True) # Overall scores/metrics

    # Link back to session (one-to-one)
    session = relationship("Session", back_populates="report")
