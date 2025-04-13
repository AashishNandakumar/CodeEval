import difflib
import datetime
import logging # Add logging import
from typing import Optional
from app import models

# Configuration for trigger logic
MIN_TIME_BETWEEN_INTERACTIONS = datetime.timedelta(seconds=60) # Minimum time before asking again
MIN_CODE_CHANGE_LINES = 2 # Minimum number of lines changed to trigger based on diff

logger = logging.getLogger(__name__) # Get logger instance

def calculate_diff_lines(old_code: str, new_code: str) -> int:
    """Calculates the number of added/deleted lines between two code strings."""
    old_lines = old_code.splitlines()
    new_lines = new_code.splitlines()
    logger.debug(f"Calculating diff. Old lines count: {len(old_lines)}, New lines count: {len(new_lines)}")
    # logger.debug(f"Old lines for diff: {old_lines}") # Can be verbose
    # logger.debug(f"New lines for diff: {new_lines}") # Can be verbose

    diff_generator = difflib.unified_diff(old_lines, new_lines, lineterm='')
    diff = list(diff_generator) # Convert generator to list for inspection
    logger.debug(f"Raw diff output (length {len(diff)}): {diff}")

    change_count = 0
    for i, line in enumerate(diff):
        # Detailed check for each line
        is_add = line.startswith('+')
        is_remove = line.startswith('-')
        is_header = line.startswith('+++') or line.startswith('---')
        is_change = (is_add or is_remove) and not is_header

        logger.debug(f"  Diff line {i}: '{line}' | Add: {is_add} | Remove: {is_remove} | Header: {is_header} | Counted: {is_change}")

        if is_change:
            change_count += 1

    logger.debug(f"Final calculated change_count: {change_count}")
    return change_count

async def should_trigger_interaction(
    current_code: str,
    last_interaction: Optional[models.Interaction]
) -> bool:
    """Decides whether a new interaction (e.g., asking a question) should be triggered."""
    logger.debug("Evaluating trigger conditions...")
    logger.debug(f"Current code length: {len(current_code)}")
    now = datetime.datetime.now(datetime.timezone.utc)

    if last_interaction is None:
        logger.debug("No previous interaction found.")
        initial_diff = calculate_diff_lines("", current_code)
        logger.debug(f"Initial code change lines: {initial_diff}")
        if initial_diff >= MIN_CODE_CHANGE_LINES:
            logger.debug(f"Triggering: Initial change ({initial_diff}) meets threshold ({MIN_CODE_CHANGE_LINES}).")
            return True
        logger.debug(f"Not triggering: Initial change ({initial_diff}) below threshold ({MIN_CODE_CHANGE_LINES}).")
        return False

    logger.debug(f"Last interaction ID: {last_interaction.id}, Timestamp: {last_interaction.timestamp}")
    last_snapshot = last_interaction.code_snapshot # Assumes eager loaded

    # 1. Time-based trigger
    time_since_last = now - last_interaction.timestamp
    logger.debug(f"Time since last interaction: {time_since_last}, Required: {MIN_TIME_BETWEEN_INTERACTIONS}")
    if time_since_last >= MIN_TIME_BETWEEN_INTERACTIONS:
        logger.debug("Time threshold met.")
        if not last_snapshot:
            logger.warning(f"Last interaction {last_interaction.id} has no associated code snapshot for time check.")
            # Decide behavior: trigger anyway, or require snapshot? Assuming trigger if time met.
            logger.debug("Triggering: Time threshold met, even without snapshot to compare.")
            return True
        if last_snapshot.code_content != current_code:
            logger.debug("Code has changed since last snapshot.")
            logger.debug("Triggering: Time threshold met and code changed.")
            return True
        else:
            logger.debug("Code has NOT changed since last snapshot.")
    else:
        logger.debug("Time threshold NOT met.")

    # 2. Diff-based trigger (only if time threshold not met)
    if not last_snapshot:
        logger.warning(f"Last interaction {last_interaction.id} has no associated code snapshot for diff check. Cannot trigger based on diff.")
        logger.debug("Not triggering: No snapshot to calculate diff.")
        return False

    lines_changed = calculate_diff_lines(last_snapshot.code_content, current_code)
    logger.debug(f"Lines changed since last snapshot: {lines_changed}, Required: {MIN_CODE_CHANGE_LINES}")
    if lines_changed >= MIN_CODE_CHANGE_LINES:
        logger.debug(f"Triggering: Significant change ({lines_changed}) meets threshold ({MIN_CODE_CHANGE_LINES}).")
        return True

    logger.debug("Not triggering: No conditions met.")
    return False
