from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import models, schemas

async def create_interaction(
    db: AsyncSession,
    interaction_data: schemas.InteractionCreate,
) -> models.Interaction:
    """Creates a new interaction record."""
    new_interaction = models.Interaction(**interaction_data.model_dump())
    db.add(new_interaction)
    await db.commit()
    await db.refresh(new_interaction)
    return new_interaction

async def get_interaction(db: AsyncSession, interaction_id: int) -> models.Interaction | None:
    """Retrieves an interaction by its ID."""
    result = await db.execute(
        select(models.Interaction).where(models.Interaction.id == interaction_id)
    )
    return result.scalar_one_or_none()

async def update_interaction(
    db: AsyncSession,
    interaction_id: int,
    update_data: dict # Allows partial updates
) -> models.Interaction | None:
    """Updates specific fields of an interaction record."""
    interaction = await get_interaction(db, interaction_id)
    if interaction:
        for key, value in update_data.items():
            setattr(interaction, key, value)
        await db.commit()
        await db.refresh(interaction)
    return interaction

async def create_code_snapshot(
    db: AsyncSession,
    snapshot_data: schemas.CodeSnapshotCreate,
) -> models.CodeSnapshot:
    """Creates a new code snapshot record, linked to an interaction."""
    # Ensure the interaction exists (optional, for data integrity)
    interaction = await get_interaction(db, snapshot_data.interaction_id)
    if not interaction:
        raise ValueError(f"Interaction with id {snapshot_data.interaction_id} not found.")

    new_snapshot = models.CodeSnapshot(**snapshot_data.model_dump())
    db.add(new_snapshot)
    await db.commit()
    await db.refresh(new_snapshot)
    return new_snapshot

async def get_code_snapshot(db: AsyncSession, snapshot_id: int) -> models.CodeSnapshot | None:
    """Retrieves a code snapshot by its ID."""
    result = await db.execute(
        select(models.CodeSnapshot).where(models.CodeSnapshot.id == snapshot_id)
    )
    return result.scalar_one_or_none()

async def get_last_interaction(db: AsyncSession, session_id: int) -> models.Interaction | None:
    """Retrieves the most recent interaction for a given session."""
    result = await db.execute(
        select(models.Interaction)
        .where(models.Interaction.session_id == session_id)
        .order_by(models.Interaction.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
