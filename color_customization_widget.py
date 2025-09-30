# color_customization_widget.py

import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QFrame, QColorDialog, QGroupBox,
    QSizePolicy, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QPixmap, QPainter, QBrush

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from language_manager import t
from color_manager import color_manager

class SimpleColorDialog(QColorDialog):
    """Simplified color picker dialog with minimal interface"""
    
    def __init__(self, initial_color: QColor, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("Select Color"))
        self.setModal(True)
        
        self.setOption(QColorDialog.ShowAlphaChannel, False)
        self.setOption(QColorDialog.DontUseNativeDialog, True)
        self.setCurrentColor(initial_color)
        
        self.setStyleSheet("""
            QColorDialog {
                background: #2a2a2a;
                color: #ffffff;
            }
            
            QSpinBox, QLineEdit {
                max-height: 0px;
                max-width: 0px;
                min-height: 0px;
                min-width: 0px;
                border: none;
                background: transparent;
                color: transparent;
            }
            
            /* Make frames transparent */
            QFrame {
                background: transparent;
                border: none;
            }
            
            QPushButton {
                background: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 12px;
                min-height: 30px;
                min-width: 60px;
            }
            
            QPushButton:hover {
                background: #505050;
                border-color: #666666;
            }
            
            QPushButton[text="OK"], QPushButton[text="Apply"] {
                background: #00aa00;
                color: #ffffff;
                border: 1px solid #00cc00;
                font-weight: bold;
            }
            
            QPushButton[text="OK"]:hover, QPushButton[text="Apply"]:hover {
                background: #00cc00;
                border-color: #00dd00;
            }
            
            /* Style Cancel button */
            QPushButton[text="Cancel"] {
                background: #666666;
                color: #ffffff;
                border: 1px solid #777777;
            }
            
            QPushButton[text="Cancel"]:hover {
                background: #777777;
                border-color: #888888;
            }
        """)
        
        self.finished.connect(self._cleanup_interface)
    
    def showEvent(self, event):
        """Override to hide unwanted elements when dialog is shown"""
        super().showEvent(event)
        self._hide_unwanted_elements()
    
    def _hide_unwanted_elements(self):
        """Hide unwanted UI elements"""
        QTimer.singleShot(50, self._actually_hide_elements)
    
    def _actually_hide_elements(self):
        """Actually perform the hiding after dialog construction"""
        for widget_type in [self.findChildren(type_) for type_ in [QWidget]]:
            for child in widget_type:
                widget_class = child.__class__.__name__
                
                if widget_class in ['QSpinBox', 'QLineEdit']:
                    child.hide()
                    child.setMaximumSize(0, 0)
                    child.setMinimumSize(0, 0)
                
                if widget_class == 'QLabel':
                    text = child.text().lower() if hasattr(child, 'text') else ""
                    if any(word in text for word in ['hue', 'blue', 'red', 'green', 'sat', 'val', 'html', ':']):
                        child.hide()
                        child.setMaximumSize(0, 0)
                        child.setMinimumSize(0, 0)
                
                if widget_class == 'QPushButton':
                    text = child.text().lower() if hasattr(child, 'text') else ""
                    if text in ['ok', 'cancel', 'apply']:
                        child.setMinimumSize(60, 30)
                        child.show()
                    elif any(word in text for word in ['pick', 'screen', 'add', 'custom']):
                        child.hide()
                        child.setMaximumSize(0, 0)
                        child.setMinimumSize(0, 0)

                if widget_class == 'QFrame':
                    frame_children = child.findChildren(QWidget)
                    if len(frame_children) > 5:
                        child.hide()
                        child.setMaximumSize(0, 0)
                        child.setMinimumSize(0, 0)
                
                if hasattr(child, 'size') and child.size().width() < 50 and child.size().height() < 50:
                    parent = child.parent()
                    if parent and parent.geometry().y() > 200:
                        child.hide()
                        child.setMaximumSize(0, 0)
                        child.setMinimumSize(0, 0)
        
        self._hide_custom_color_section()
    
    def _hide_custom_color_section(self):
        """Specifically target and hide the custom colors section"""
        all_widgets = self.findChildren(QWidget)
        small_widgets = []
        
        for widget in all_widgets:
            if (hasattr(widget, 'size') and 
                widget.size().width() <= 30 and widget.size().height() <= 30 and
                widget.size().width() > 0 and widget.size().height() > 0):
                small_widgets.append(widget)

        if len(small_widgets) >= 8:
            for widget in small_widgets:
                widget.hide()
                widget.setMaximumSize(0, 0)
                widget.setMinimumSize(0, 0)
                if widget.parent():
                    parent = widget.parent()
                    parent.hide()
                    parent.setMaximumSize(0, 0)
    
    def _cleanup_interface(self):
        """Clean up any interface modifications"""
        pass

class ColorPreviewWidget(QWidget):
    """Widget to show color preview with RGB values"""
    
    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(60, 40)
        self.setToolTip(f"RGB: {color.red()}, {color.green()}, {color.blue()}\nAlpha: {color.alpha()}")
    
    def set_color(self, color: QColor):
        """Update the color and refresh display"""
        self.color = color
        self.setToolTip(f"RGB: {color.red()}, {color.green()}, {color.blue()}\nAlpha: {color.alpha()}")
        self.update()
    
    def paintEvent(self, event):
        """Paint the color preview"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), Qt.white)

        square_size = 8
        for x in range(0, self.width(), square_size):
            for y in range(0, self.height(), square_size):
                if (x // square_size + y // square_size) % 2:
                    painter.fillRect(x, y, square_size, square_size, QColor(220, 220, 220))

        painter.fillRect(self.rect(), self.color)

        painter.setPen(QColor(100, 100, 100))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

class ColorCustomizationWidget(QWidget):
    """Widget for customizing overlay colors"""
    
    colors_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color_buttons = {}
        self.color_previews = {}
        self.setup_ui()
        self.load_colors()
    
    def setup_ui(self):
        """Setup the color customization UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 15, 15, 15)

        header = QLabel(t("CUSTOM COLOR MODE"))
        header.setStyleSheet("""
            QLabel {
                color: #f0f0f0;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(header)

        desc = QLabel(t("Customize every color element in the overlay system. Click 'Change Color' to open a simplified color picker. Not every item may be visible in all overlays, but all colors will be saved. Changes are applied immediately and saved automatically."))
        desc.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 13px;
                background: transparent;
                border: none;
                margin-bottom: 15px;
            }
        """)
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        self.create_color_group(main_layout)
    
    def create_color_group(self, parent_layout):
        """Create the main color customization group"""
        group = QGroupBox(t("Color Customization"))
        group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #444444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background: #2a2a2a;
            }
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 20, 15, 15)

        display_names = color_manager.get_color_display_names()
        
        row = 0
        for color_name, display_name in display_names.items():
            color = color_manager.get_color(color_name)
            preview = ColorPreviewWidget(color)
            self.color_previews[color_name] = preview

            label = QLabel(display_name)
            label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 13px;
                    background: transparent;
                    border: none;
                }
            """)

            button = QPushButton(t("Change Color"))
            button.setFixedSize(100, 30)
            button.setStyleSheet("""
                QPushButton {
                    background: #404040;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background: #505050;
                    border-color: #666666;
                }
                QPushButton:pressed {
                    background: #353535;
                }
            """)
            button.clicked.connect(lambda checked, name=color_name: self.change_color(name))
            self.color_buttons[color_name] = button

            layout.addWidget(preview, row, 0)
            layout.addWidget(label, row, 1)
            layout.addWidget(button, row, 2)
            
            row += 1
        
        parent_layout.addWidget(group)

    def change_color(self, color_name: str):
        """Open simplified color picker for a specific color"""
        current_color = color_manager.get_color(color_name)
        
        color_dialog = SimpleColorDialog(current_color, self)
        
        if color_dialog.exec_() == QColorDialog.Accepted:
            new_color = color_dialog.currentColor()
            new_color.setAlpha(255)
            color_manager.set_color(color_name, new_color)
            self.color_previews[color_name].set_color(new_color)
            self.colors_changed.emit()

    def load_colors(self):
        """Load current colors into preview widgets"""
        for color_name, preview in self.color_previews.items():
            color = color_manager.get_color(color_name)
            preview.set_color(color)