# responsive_ui.py

import ctypes
from PyQt5.QtCore import Qt
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QFrame
from PyQt5.QtCore import QSize, QRect

def enable_high_dpi_support():
    """Enable High DPI scaling for the application"""
    try:
        
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
            
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except:
            pass
            
        logging.info("High DPI scaling enabled")
        return True
    except Exception as e:
        logging.error(f"Error enabling high DPI support: {e}")
        return False

class ScreenScaler:
    """Utility class to handle screen scaling for different resolutions"""
    
    @staticmethod
    def get_screen_info():
        """Get screen dimensions and calculate a scale factor"""
        screen = QApplication.primaryScreen()
        if not screen:
            return 1920, 1080, 1.0
            
        screen_size = screen.availableGeometry()
        width = screen_size.width()
        height = screen_size.height()
        
        base_width = 1920
        base_height = 1080
        width_scale = width / base_width
        height_scale = height / base_height
        
        scale_factor = min(width_scale, height_scale)
        
        if scale_factor < 0.7:
            scale_factor = 0.7
        
        logging.info(f"Screen dimensions: {width}x{height}, scale factor: {scale_factor}")
        return width, height, scale_factor
    
    @staticmethod
    def scale_size(size, scale_factor):
        """Scale a size value based on the screen scale factor"""
        return int(size * scale_factor)
    
    @staticmethod
    def scale_font_size(base_size, scale_factor):
        """Scale font size with a slightly gentler curve"""
        return int(base_size * (0.8 + 0.2 * scale_factor))

class ResponsiveUIHelper:
    """Helper class to manage responsive UI updates"""
    
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.scale_factor = getattr(parent_widget, 'scale_factor', 1.0)
        
    def scale_widget(self, widget, min_width=None, min_height=None):
        """Apply scale factors to a widget's minimum size"""
        if min_width is not None:
            scaled_min_width = ScreenScaler.scale_size(min_width, self.scale_factor)
            if min_height is not None:
                scaled_min_height = ScreenScaler.scale_size(min_height, self.scale_factor)
                widget.setMinimumSize(scaled_min_width, scaled_min_height)
            else:
                widget.setMinimumWidth(scaled_min_width)
        elif min_height is not None:
            scaled_min_height = ScreenScaler.scale_size(min_height, self.scale_factor)
            widget.setMinimumHeight(scaled_min_height)
            
    def scale_margins(self, layout, base_margin=10):
        """Scale layout margins based on screen resolution"""
        scaled_margin = ScreenScaler.scale_size(base_margin, self.scale_factor)
        layout.setContentsMargins(scaled_margin, scaled_margin, scaled_margin, scaled_margin)
        
    def scale_spacing(self, layout, base_spacing=10):
        """Scale layout spacing based on screen resolution"""
        scaled_spacing = ScreenScaler.scale_size(base_spacing, self.scale_factor)
        layout.setSpacing(scaled_spacing)

def make_popup_responsive(parent, popup_frame, base_width=300, base_height=100, scale_factor=1.0):
    """Position and size a popup frame responsively"""
    popup_width = ScreenScaler.scale_size(base_width, scale_factor)
    popup_height = ScreenScaler.scale_size(base_height, scale_factor)
    
    popup_frame.setGeometry(
        (parent.width() - popup_width) // 2,
        (parent.height() - popup_height) // 2,
        popup_width, popup_height
    )
    
    for child in popup_frame.findChildren(QWidget):
        font = child.font()
        current_size = font.pointSize()
        if current_size > 0:
            new_size = ScreenScaler.scale_font_size(current_size, scale_factor)
            font.setPointSize(new_size)
            child.setFont(font)