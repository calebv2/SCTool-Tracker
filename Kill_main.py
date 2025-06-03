# Kill_main.py

"""
SCTool Killfeed
Version: 5.0
"""

import sys
import logging
import atexit
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

from Kill_form import main

if __name__ == "__main__":
    main()