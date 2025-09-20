# Death_kill.py

from kill_event_formatter import DeathEventFormatter


def format_death_kill(log_line: str, data: dict, registered_user: str, timestamp: str, last_game_mode: str) -> str:
    """
    Format a death event using the new formatter system.
    
    Args:
        log_line: Original log line
        data: Death data dictionary
        registered_user: Name of the registered user
        timestamp: Event timestamp
        last_game_mode: Last known game mode
        
    Returns:
        HTML readout string
    """
    formatter = DeathEventFormatter()
    return formatter.format_event(
        log_line=log_line,
        data=data,
        registered_user=registered_user,
        timestamp=timestamp,
        last_game_mode=last_game_mode
    )