import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from language_manager import t

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QApplication
)
from PyQt5.QtCore import (
    QTimer, QPropertyAnimation, Qt, QEasingCurve
)
from PyQt5.QtGui import (
    QPixmap, QPainter, QBrush, QPen, QColor
)
faded_timers = []
faded_animations = []

def create_faded_ui(self):
    """Create faded overlay UI with notification system"""
    layout = QVBoxLayout()
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(5)

    self.faded_container = QWidget()
    self.faded_container.setStyleSheet("background: transparent;")
    self.faded_container.setLayout(QVBoxLayout())
    self.faded_container.layout().setContentsMargins(0, 0, 0, 0)
    self.faded_container.layout().setSpacing(5)
    
    layout.addWidget(self.faded_container)
    self.setLayout(layout)

def show_death_notification(self, message, player_name=""):
    """Show death notification with fading effect"""
    show_faded_notification(self, message, is_death=True, player_name=player_name)

def show_kill_notification(self, message, player_name=""):
    """Show kill notification with fading effect"""
    show_faded_notification(self, message, is_death=False, player_name=player_name)

def show_faded_notification(self, message, is_death=False, player_name="", duration=5000):
    """Show a notification with fading animation"""
    if not hasattr(self, 'faded_container'):
        return
    
    notification = QWidget()
    notification_layout = QHBoxLayout()
    notification_layout.setContentsMargins(10, 8, 10, 8)
    notification_layout.setSpacing(10)
    
    image_label = QLabel()
    image_label.setFixedSize(80, 80)
    image_label.setStyleSheet("""
        QLabel {
            background-color: #2a2a2a;
            border: 2px solid #555;
            border-radius: 40px;
            color: white;
            font-size: 10px;
            font-weight: bold;
        }
    """)
    image_label.setAlignment(Qt.AlignCenter)
    image_label.setText("IMG")
    
    message_label = QLabel(message)
    message_label.setStyleSheet(f"""
        QLabel {{
            color: {'#ff4444' if is_death else '#44ff44'};
            font-size: 14px;
            font-weight: bold;
            background: transparent;
        }}
    """)
    message_label.setWordWrap(True)
    
    notification_layout.addWidget(image_label)
    notification_layout.addWidget(message_label, 1)
    
    notification.setLayout(notification_layout)
    notification.setStyleSheet("""
        QWidget {
            background-color: rgba(0, 0, 0, 180);
            border: 1px solid #555;
            border-radius: 5px;
        }
    """)
    
    self.faded_container.layout().addWidget(notification)
    
    fade_notification(self, notification, duration)

def show_faded_positioning_helper(self):
    """Show positioning helper for faded overlay"""
    if not hasattr(self, 'faded_container'):
        return
    
    helper = QLabel("Faded Overlay Position Helper")
    helper.setStyleSheet("""
        QLabel {
            background-color: rgba(255, 255, 0, 100);
            color: black;
            font-size: 16px;
            font-weight: bold;
            padding: 20px;
            border: 2px dashed yellow;
        }
    """)
    helper.setAlignment(Qt.AlignCenter)
    
    self.faded_container.layout().addWidget(helper)
    
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(lambda: hide_positioning_helper(self))
    timer.start(3000)
    faded_timers.append(timer)

def hide_positioning_helper(self):
    """Hide positioning helper"""
    if hasattr(self, 'faded_container'):
        layout = self.faded_container.layout()
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QLabel) and "Helper" in widget.text():
                    widget.deleteLater()
                    break

def stop_all_faded_animations(self):
    """Stop all active faded animations"""
    global faded_animations, faded_timers
    
    for animation in faded_animations:
        if animation:
            animation.stop()
    faded_animations.clear()
    
    for timer in faded_timers:
        if timer:
            timer.stop()
    faded_timers.clear()

def fade_notification(self, notification, duration=5000):
    """Apply fade animation to notification"""
    global faded_animations, faded_timers
    
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(lambda: hide_faded_notification(self, notification))
    timer.start(duration)
    faded_timers.append(timer)

def hide_faded_notification(self, notification):
    """Hide and remove a notification"""
    if notification and notification.parent():
        notification.deleteLater()

def update_countdown(self, remaining_seconds):
    """Update countdown display"""
    pass

def clear_faded_container(self):
    """Clear all notifications from faded container"""
    if hasattr(self, 'faded_container'):
        layout = self.faded_container.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

def cleanup_faded_timers():
    """Clean up all faded timers and animations"""
    global faded_animations, faded_timers
    
    for animation in faded_animations:
        if animation:
            animation.stop()
    faded_animations.clear()
    
    for timer in faded_timers:
        if timer:
            timer.stop()
    faded_timers.clear() 