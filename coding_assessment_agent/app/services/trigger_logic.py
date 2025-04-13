import difflib
import datetime
from typing import Optional
from app import models

# Configuration for trigger logic
MIN_TIME_BETWEEN_INTERACTIONS = datetime.timedelta(seconds=60) # Minimum time before asking again
MIN_CODE_CHANGE_LINES = 5 # Minimum number of lines changed to trigger based on diff

def calculate_diff_lines(old_code: str, new_code: str) -> int:
    """Calculates the number of added/deleted lines between two code strings."""
    diff = difflib.unified_diff(old_code.splitlines(), new_code.splitlines(), lineterm='')
    # Count lines starting with '+' or '-' but not '+++' or '---'
    change_count = sum(1 for line in diff if (line.startswith('+') or line.startswith('-')) and not (line.startswith('+++') or line.startswith('---')))
    return change_count

async def should_trigger_interaction(
    current_code: str,
    last_interaction: Optional[models.Interaction]
) -> bool:
    """Decides whether a new interaction (e.g., asking a question) should be triggered."""
    now = datetime.datetime.now(datetime.timezone.utc)

    if last_interaction is None:
        # Trigger if first code block has enough lines changed (compared to empty)
        if calculate_diff_lines("", current_code) >= MIN_CODE_CHANGE_LINES:
             return True # Trigger on first substantial code input
        return False

    # 1. Time-based trigger
    # Ensure timestamp comparison is timezone-aware if necessary (models.py uses timezone=True)
    time_since_last = now - last_interaction.timestamp
    if time_since_last >= MIN_TIME_BETWEEN_INTERACTIONS:
        # Check if there was *any* change since the last interaction's snapshot
        # Note: last_interaction might not have a snapshot (e.g., if it was a 'response_received' interaction)
        # We need the snapshot from the *previous* code submission interaction.
        # This logic might need refinement depending on how snapshots are associated.
        # Assuming last_interaction *does* have the relevant snapshot for now.
        last_snapshot = last_interaction.code_snapshot
        if last_snapshot and last_snapshot.code_content != current_code:
             return True # Trigger if enough time passed and code changed since last snapshot

    # 2. Diff-based trigger (only if time threshold not met)
    # Same assumption as above regarding last_interaction and its snapshot
    last_snapshot = last_interaction.code_snapshot
    if last_snapshot:
        lines_changed = calculate_diff_lines(last_snapshot.code_content, current_code)
        if lines_changed >= MIN_CODE_CHANGE_LINES:
            return True # Trigger if significant change occurred, regardless of time

    return False
