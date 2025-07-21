# Kill_main.py

"""
SCTool Killfeed
"""

import sys
import logging
import atexit
import os
import json
from PyQt5.QtWidgets import QApplication
from responsive_ui import enable_high_dpi_support

enable_high_dpi_support()

def cleanup_hotkeys():
    """Cleanup global hotkeys on exit"""
    try:
        from Kill_form import app_instance
        if hasattr(app_instance, 'game_overlay') and app_instance.game_overlay:
            if hasattr(app_instance.game_overlay, 'hotkey_thread') and app_instance.game_overlay.hotkey_thread:
                app_instance.game_overlay.hotkey_thread.stop()
                app_instance.game_overlay.hotkey_thread.wait(1000)
    except:
        pass

atexit.register(cleanup_hotkeys)

def should_start_minimized():
    """Check if the app should start minimized (when starting with Windows and minimize to tray is enabled)"""
    try:
        from Kill_form import get_appdata_paths
        config_file, _, _ = get_appdata_paths()
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('start_with_system', False) and config.get('minimize_to_tray', False)
    except Exception as e:
        logging.error(f"Error checking if app should start minimized: {e}")
    
    return False

from Kill_form import main

if __name__ == "__main__":
    main(start_minimized=should_start_minimized())