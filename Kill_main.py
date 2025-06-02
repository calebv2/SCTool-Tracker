# Kill_main.py

"""
SCTool Killfeed
Version: 4.9
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from responsive_ui import enable_high_dpi_support

enable_high_dpi_support()

from Kill_form import main

if __name__ == "__main__":
    main()