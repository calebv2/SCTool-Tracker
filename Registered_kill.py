# Registered_kill.py

from typing import Dict, Tuple, Any
from kill_event_formatter import RegisteredKillFormatter


def format_registered_kill(
    log_line: str,
    data: dict,
    registered_user: str,
    full_timestamp: str,
    last_game_mode: str,
    success: bool = True
) -> Tuple[str, Dict[str, Any]]:
    """
    Format a registered kill event using the new formatter system.
    
    Args:
        log_line: Original log line
        data: Kill data dictionary
        registered_user: Name of the registered user
        full_timestamp: Full timestamp string
        last_game_mode: Last known game mode
        success: Whether the kill was successful
        
    Returns:
        Tuple of (HTML readout, payload dictionary)
    """
    formatter = RegisteredKillFormatter()
    return formatter.format_event(
        log_line=log_line,
        data=data,
        registered_user=registered_user,
        full_timestamp=full_timestamp,
        last_game_mode=last_game_mode,
        success=success
    )