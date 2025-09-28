import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from language_manager import t

import weakref
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QFontMetrics

class OutlinedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.outline_color = QColor(0, 0, 0)
        self.text_color = QColor(255, 255, 255)
        self.outline_width = 1
        self.use_outline = True
        
    def set_outline_enabled(self, enabled):
        self.use_outline = enabled
        self.update()
        
    def set_outline_color(self, color):
        self.outline_color = QColor(color)
        self.update()
        
    def set_text_color(self, color):
        self.text_color = QColor(color)
        self.update()
        
    def paintEvent(self, event):
        if not self.use_outline:
            super().paintEvent(event)
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        text = self.text()
        if not text:
            return
            
        font = self.font()
        painter.setFont(font)
        
        rect = self.rect()
        
        painter.setPen(QPen(self.outline_color, self.outline_width))
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                painter.drawText(rect.adjusted(dx, dy, dx, dy), self.alignment(), text)

        painter.setPen(QPen(self.text_color, 0))
        painter.drawText(rect, self.alignment(), text)

class MultiColoredLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.text_segments = []
        self.outline_color = QColor(0, 0, 0)
        self.outline_width = 1
        self.use_outline = True
        
    def set_text_segments(self, segments):
        """Set text segments with individual colors: [(text, color)]"""
        self.text_segments = segments
        full_text = ''.join([segment[0] for segment in segments])
        self.setText(full_text)
        self.update()
        
    def set_outline_enabled(self, enabled):
        self.use_outline = enabled
        self.update()
        
    def set_outline_color(self, color):
        self.outline_color = QColor(color)
        self.update()
        
    def paintEvent(self, event):
        if not self.text_segments:
            super().paintEvent(event)
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        font = self.font()
        painter.setFont(font)
        
        fm = QFontMetrics(font)
        rect = self.rect()
        
        total_width = sum(fm.width(segment[0]) for segment in self.text_segments)
        start_x = (rect.width() - total_width) // 2
        y = rect.center().y() + fm.ascent() // 2
        
        current_x = start_x

        if self.use_outline:
            painter.setPen(QPen(self.outline_color, self.outline_width))
            temp_x = start_x
            for text, color in self.text_segments:
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        painter.drawText(temp_x + dx, y + dy, text)
                temp_x += fm.width(text)
        
        for text, color in self.text_segments:
            painter.setPen(QPen(QColor(color), 0))
            painter.drawText(current_x, y, text)
            current_x += fm.width(text)

class NotificationItem(QWidget):
    """Individual notification item with its own fade timer"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = MultiColoredLabel("")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self.start_fade)
        self.fade_animation = None
        self._opacity = 1.0
        
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
        
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)
        self.update()
        
    def start_fade(self):
        self.fade_timer.stop()
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(2000)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.finished.connect(self.deleteLater)
        self.fade_animation.start()
        
    def cleanup(self):
        if self.fade_timer:
            self.fade_timer.stop()
        if self.fade_animation:
            self.fade_animation.stop()

def create_simple_text_ui(self):
    self.setAttribute(Qt.WA_TranslucentBackground, True)
    self.setStyleSheet("background: transparent;")

    self.main_layout = QVBoxLayout()
    self.main_layout.setContentsMargins(0, 0, 0, 0)
    self.main_layout.setSpacing(5)
    self.main_layout.setAlignment(Qt.AlignTop)

    self.notification_container = QWidget()
    self.notification_container.setStyleSheet("background: transparent;")
    self.notification_layout = QVBoxLayout()
    self.notification_layout.setContentsMargins(0, 0, 0, 0)
    self.notification_layout.setSpacing(5)
    self.notification_container.setLayout(self.notification_layout)
    
    self.main_layout.addWidget(self.notification_container)
    self.setLayout(self.main_layout)
    
    self.active_notifications = []
    
    if not hasattr(self, 'countdown_timer') or not self.countdown_timer:
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_simple_countdown)
    
    self.countdown_seconds = 0
    self.is_example_mode = False
    self.example_notification = None

def add_notification(self, segments, notification_type='kill'):
    """Add a new notification to the stack"""
    notification = NotificationItem(self)
    notification.label.set_text_segments(segments)
    
    if hasattr(self, 'colors') and self.colors:
        notification.label.set_outline_enabled(True)
        notification.label.set_outline_color('black')
        
        text_color = self.colors['text_primary'].name()
        base_style = f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
                border: none;
                white-space: nowrap;
                color: {text_color};
            }}
        """
        notification.label.setStyleSheet(base_style)
    
    self.notification_layout.addWidget(notification)
    self.active_notifications.append(notification)
    
    if notification_type == 'example':
        notification.adjustSize()
        try:
            w = notification.sizeHint().width()
            notification.setFixedWidth(w)
            notification.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            notification.label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        except Exception:
            pass

    overlay_ref = weakref.ref(self)
    notification.destroyed.connect(lambda *args, nr=notification, orf=overlay_ref: remove_notification_ref(orf, nr))
    
    notification.fade_timer.start(8000)
    
    self.adjustSize()
    
    return notification

def remove_notification(self, notification):
    """Remove notification from tracking list"""
    try:
        if notification in self.active_notifications:
            self.active_notifications.remove(notification)
        try:
            self.adjustSize()
        except RuntimeError:
            pass
    except Exception:
        pass

def remove_notification_ref(overlay_ref, notification):
    """Safe wrapper that resolves a weakref to the overlay and calls
    remove_notification if the overlay is still alive."""
    overlay = overlay_ref()
    if overlay is None:
        return
    try:
        remove_notification(overlay, notification)
    except RuntimeError:
        pass

def show_simple_kill_notification(self, victim, weapon=None):
    try:
        player_name = t('You')
        if hasattr(self, 'parent_tracker') and self.parent_tracker:
            if hasattr(self.parent_tracker, 'local_user_name') and self.parent_tracker.local_user_name:
                player_name = self.parent_tracker.local_user_name
        
        if self.is_example_mode:
            clear_example_mode(self)
        
        if hasattr(self, 'colors') and self.colors:
            if hasattr(self, 'theme') and self.theme == 'dark':
                segments = [
                    (player_name, '#808080'),
                    (t(' killed '), '#808080'),
                    (victim, '#808080')
                ]
            else:
                kill_color = self.colors['kill_color'].name()
                death_color = self.colors['death_color'].name()
                text_color = self.colors['text_primary'].name()
                
                segments = [
                    (player_name, kill_color),
                    (t(' killed '), text_color),
                    (victim, death_color)
                ]
        else:
            if hasattr(self, 'theme') and self.theme == 'default':
                segments = [
                    (player_name, '#00ff00'),
                    (t(' killed '), 'white'),
                    (victim, '#ff0000')
                ]
            elif hasattr(self, 'theme') and self.theme == 'neon':
                segments = [
                    (player_name, '#00ff7f'),
                    (t(' killed '), '#00ffff'),
                    (victim, '#ff1493')
                ]
            elif hasattr(self, 'theme') and self.theme == 'dark':
                segments = [
                    (player_name, '#808080'),
                    (t(' killed '), '#808080'),
                    (victim, '#808080')
                ]
            else:
                segments = [
                    (player_name, 'white'),
                    (t(' killed '), 'white'),
                    (victim, 'white')
                ]
        
        add_notification(self, segments, 'kill')
        self.setWindowOpacity(1.0)
        
    except RuntimeError:
        return

def show_simple_death_notification(self, attacker, weapon=None):
    try:
        player_name = t('You')
        if hasattr(self, 'parent_tracker') and self.parent_tracker:
            if hasattr(self.parent_tracker, 'local_user_name') and self.parent_tracker.local_user_name:
                player_name = self.parent_tracker.local_user_name
        
        if self.is_example_mode:
            clear_example_mode(self)
        
        if hasattr(self, 'colors') and self.colors:
            if hasattr(self, 'theme') and self.theme == 'dark':
                segments = [
                    (attacker, '#808080'),
                    (t(' killed '), '#808080'),
                    (player_name, '#808080')
                ]
            else:
                kill_color = self.colors['kill_color'].name()
                death_color = self.colors['death_color'].name()
                text_color = self.colors['text_primary'].name()
                
                segments = [
                    (attacker, death_color),
                    (t(' killed '), text_color),
                    (player_name, kill_color)
                ]
        else:
            if hasattr(self, 'theme') and self.theme == 'default':
                segments = [
                    (attacker, '#ff0000'),
                    (t(' killed '), 'white'),
                    (player_name, '#00ff00')
                ]
            elif hasattr(self, 'theme') and self.theme == 'neon':
                segments = [
                    (attacker, '#ff1493'),
                    (t(' killed '), '#00ffff'),
                    (player_name, '#00ff7f')
                ]
            elif hasattr(self, 'theme') and self.theme == 'dark':
                segments = [
                    (attacker, '#808080'),
                    (t(' killed '), '#808080'),
                    (player_name, '#808080')
                ]
            else:
                segments = [
                    (attacker, 'white'),
                    (t(' killed '), 'white'),
                    (player_name, 'white')
                ]
        
        add_notification(self, segments, 'death')
        self.setWindowOpacity(1.0)
        
    except RuntimeError:
        return

def clear_example_mode(self):
    """Clear example notification if active"""
    self.is_example_mode = False
    if self.example_notification:
        self.example_notification.cleanup()
        self.example_notification.deleteLater()
        self.example_notification = None
    if hasattr(self, 'countdown_timer'):
        self.countdown_timer.stop()

def show_simple_sample_notification(self):
    try:
        clear_simple_container(self)
        
        self.is_example_mode = True
        self.countdown_seconds = 30
        
        if hasattr(self, 'colors') and self.colors:
            if hasattr(self, 'theme') and self.theme == 'dark':
                segments = [
                    (t('player'), '#808080'),
                    (t(' killed '), '#808080'),
                    (t('player'), '#808080'),
                    (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', '#808080')
                ]
            else:
                kill_color = self.colors['kill_color'].name()
                death_color = self.colors['death_color'].name()
                text_color = self.colors['text_primary'].name()
                
                segments = [
                    (t('player'), kill_color),
                    (t(' killed '), text_color),
                    (t('player'), death_color),
                    (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', text_color)
                ]
        else:
            if hasattr(self, 'theme') and self.theme == 'default':
                segments = [
                    (t('player'), '#00ff00'),
                    (t(' killed '), 'white'),
                    (t('player'), '#ff0000'),
                    (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', 'white')
                ]
            elif hasattr(self, 'theme') and self.theme == 'neon':
                segments = [
                    (t('player'), '#00ff7f'),
                    (t(' killed '), '#00ffff'),
                    (t('player'), '#ff1493'),
                    (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', '#00ffff')
                ]
            elif hasattr(self, 'theme') and self.theme == 'dark':
                segments = [
                    (t('player'), '#808080'),
                    (t(' killed '), '#808080'),
                    (t('player'), '#808080'),
                    (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', '#808080')
                ]
            else:
                segments = [
                    (t('player'), 'white'),
                    (t(' killed '), 'white'),
                    (t('player'), 'white'),
                    (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', 'white')
                ]
        
        self.example_notification = add_notification(self, segments, 'example')
        self.example_notification.fade_timer.stop()
        
        self.setWindowOpacity(1.0)
        if hasattr(self, 'countdown_timer'):
            self.countdown_timer.start(1000)
            
    except RuntimeError:
        return

def update_simple_countdown(self):
    try:
        if not self.is_example_mode or not self.example_notification:
            if hasattr(self, 'countdown_timer'):
                self.countdown_timer.stop()
            return
            
        if self.countdown_seconds > 0:
            self.countdown_seconds -= 1
            
            if hasattr(self, 'colors') and self.colors:
                if hasattr(self, 'theme') and self.theme == 'dark':
                    segments = [
                        (t('player'), '#808080'),
                        (t(' killed '), '#808080'),
                        (t('player'), '#808080'),
                        (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', '#808080')
                    ]
                else:
                    kill_color = self.colors['kill_color'].name()
                    death_color = self.colors['death_color'].name()
                    text_color = self.colors['text_primary'].name()
                    
                    segments = [
                        (t('player'), kill_color),
                        (t(' killed '), text_color),
                        (t('player'), death_color),
                        (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', text_color)
                    ]
            else:
                if hasattr(self, 'theme') and self.theme == 'default':
                    segments = [
                        (t('player'), '#00ff00'),
                        (t(' killed '), 'white'),
                        (t('player'), '#ff0000'),
                        (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', 'white')
                    ]
                elif hasattr(self, 'theme') and self.theme == 'neon':
                    segments = [
                        (t('player'), '#00ff7f'),
                        (t(' killed '), '#00ffff'),
                        (t('player'), '#ff1493'),
                        (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', '#00ffff')
                    ]
                elif hasattr(self, 'theme') and self.theme == 'dark':
                    segments = [
                        (t('player'), '#808080'),
                        (t(' killed '), '#808080'),
                        (t('player'), '#808080'),
                        (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', '#808080')
                    ]
                else:
                    segments = [
                        (t('player'), 'white'),
                        (t(' killed '), 'white'),
                        (t('player'), 'white'),
                        (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', 'white')
                    ]
            
            self.example_notification.label.set_text_segments(segments)
            
        else:
            if hasattr(self, 'countdown_timer'):
                self.countdown_timer.stop()
            if self.example_notification:
                self.example_notification.start_fade()
            self.is_example_mode = False
            self.example_notification = None
            
    except (RuntimeError, AttributeError):
        if hasattr(self, 'countdown_timer'):
            self.countdown_timer.stop()

def clear_simple_container(self):
    """Clear all notifications"""
    try:
        if hasattr(self, 'countdown_timer') and self.countdown_timer:
            self.countdown_timer.stop()
        
        for notification in self.active_notifications[:]:
            notification.cleanup()
            notification.deleteLater()
        
        self.active_notifications.clear()
        self.is_example_mode = False
        self.example_notification = None
        self.setWindowOpacity(0.0)
        
    except (RuntimeError, AttributeError):
        pass

def cleanup_simple_timers(self):
    """Cleanup all timers and notifications"""
    try:
        clear_simple_container(self)
        
        if hasattr(self, 'countdown_timer') and self.countdown_timer:
            self.countdown_timer.stop()
            self.countdown_timer.disconnect()
            self.countdown_timer.deleteLater()
            self.countdown_timer = None
            
    except (RuntimeError, AttributeError):
        pass

def apply_simple_text_theme(self):
    """Compatibility stub - theming now handled in add_notification"""
    pass

def apply_simple_notification_theme(self, notification_type):
    """Compatibility stub - theming now handled in add_notification"""
    pass

def adjust_simple_text_size(self):
    """Adjust window size to fit content"""
    self.adjustSize()

def start_fade_animation(self):
    """Compatibility stub - fade now handled per notification"""
    pass

def hide_simple_notification(self):
    """Hide all notifications"""
    clear_simple_container(self)

def show_simple_notification(self):
    """Show sample notification"""
    show_simple_sample_notification(self)