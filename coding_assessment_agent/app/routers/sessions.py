from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, models
from app.database import get_db
from app.services import session_service

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.SessionRead, status_code=201)
async def create_new_session(db: AsyncSession = Depends(get_db)):
    """Create a new assessment session."""
    session = await session_service.create_session(db=db)
    # Manually construct the response model to include empty interactions list
    # This ensures the response matches the SessionRead schema correctly
    return schemas.SessionRead(
        id=session.id,
        start_time=session.start_time,
        end_time=session.end_time,
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
    """Mark a session as ended."""
    session = await session_service.end_session(db=db, session_id=session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
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
