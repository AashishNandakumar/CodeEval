from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app import models, schemas
import datetime

async def create_session(db: AsyncSession) -> models.Session:
    """Creates a new session in the database."""
    new_session = models.Session()
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session

async def get_session(db: AsyncSession, session_id: int) -> models.Session | None:
    """Retrieves a session by its ID, optionally loading related interactions and report."""
    result = await db.execute(
        select(models.Session)
        .where(models.Session.id == session_id)
        .options(
            selectinload(models.Session.interactions).selectinload(models.Interaction.code_snapshot),
            selectinload(models.Session.report)
        )
    )
    return result.scalar_one_or_none()

async def end_session(db: AsyncSession, session_id: int) -> models.Session | None:
    """Marks a session as ended by setting the end_time."""
    session = await get_session(db, session_id) # Use get_session to potentially pre-load data if needed later
    if session:
        session.end_time = datetime.datetime.now(datetime.timezone.utc)
        await db.commit()
        await db.refresh(session)
    return session

async def create_report(db: AsyncSession, session_id: int, report_data: schemas.ReportCreate) -> models.Report:
    """Creates a final report for a given session."""
    # Ensure the session exists first (optional, depends on requirements)
    session = await get_session(db, session_id)
    if not session:
        raise ValueError(f"Session with id {session_id} not found.")
    if session.report:
        raise ValueError(f"Report for session {session_id} already exists.")

    new_report = models.Report(
        session_id=session_id,
        report_content=report_data.report_content,
        scores=report_data.scores
    )
    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)
    return new_report

async def get_report(db: AsyncSession, session_id: int) -> models.Report | None:
    """Retrieves the report associated with a session ID."""
    result = await db.execute(
        select(models.Report).where(models.Report.session_id == session_id)
    )
    return result.scalar_one_or_none()
