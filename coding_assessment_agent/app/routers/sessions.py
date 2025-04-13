from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, models
from app.database import get_db
from app.services import session_service
from app.services.agent_orchestrator import agent_orchestrator

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.SessionRead, status_code=201)
async def create_new_session(session_data: schemas.SessionCreate = Body(...), db: AsyncSession = Depends(get_db)):
    """Create a new assessment session, including the initial problem statement."""
    session = await session_service.create_session(db=db, problem_statement=session_data.problem_statement)
    # Manually construct the response model to include the problem statement and empty interactions list
    # This ensures the response matches the SessionRead schema correctly
    return schemas.SessionRead(
        id=session.id,
        start_time=session.start_time,
        end_time=session.end_time,
        problem_statement=session.problem_statement,
        report=None,
        interactions=[]
    )

@router.get("/{session_id}", response_model=schemas.SessionRead)
async def read_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """Get details of a specific session, including interactions and report if available."""
    session = await session_service.get_session(db=db, session_id=session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/{session_id}/end", response_model=schemas.SessionRead)
async def mark_session_ended(session_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a session as ended and trigger report generation."""
    session = await session_service.end_session(db=db, session_id=session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Trigger report generation after successfully ending the session
    try:
        await agent_orchestrator.generate_report(session_id=session_id, db=db)
    except Exception as e:
        # Log the error, but maybe don't fail the entire request?
        # Depending on requirements, you might want to handle this differently.
        # For now, we'll just log it and continue.
        # Consider adding proper logging here.
        print(f"Error during automatic report generation for session {session_id}: {e}") # Basic logging
        # Optionally: raise HTTPException(status_code=500, detail=f"Session ended, but failed to generate report: {e}")

    return session

@router.get("/{session_id}/report", response_model=schemas.ReportRead)
async def read_session_report(session_id: int, db: AsyncSession = Depends(get_db)):
    """Get the final report for a specific session."""
    # First check if the session exists
    session = await session_service.get_session(db=db, session_id=session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if the report exists (get_report already handles this implicitly)
    report = await session_service.get_report(db=db, session_id=session_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not generated yet or not found")
    return report

# Note: Report creation will likely be triggered internally by the AgentOrchestrator
# after the session ends or on demand, rather than via a direct POST endpoint.
# If a direct endpoint is needed later, it can be added here.
