import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from language_manager import t

from PyQt5.QtWidgets import QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
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
        """Set text segments with individual colors: [(text, color), ...]"""
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

def create_simple_text_ui(self):
    self.setAttribute(Qt.WA_TranslucentBackground, True)
    self.setStyleSheet("background: transparent;")
    
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    
    self.simple_text_label = MultiColoredLabel("")
    self.simple_text_label.setAlignment(Qt.AlignCenter)
    self.simple_text_label.setWordWrap(False)
    apply_simple_text_theme(self)
    
    layout.addWidget(self.simple_text_label)
    self.setLayout(layout)
    
    if not hasattr(self, 'fade_timer') or not self.fade_timer:
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self.start_fade_animation)
    self.fade_animation = None
    
    if not hasattr(self, 'countdown_timer') or not self.countdown_timer:
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_simple_countdown)
    
    self.countdown_seconds = 0
    self.is_example_mode = False

def apply_simple_text_theme(self):
    """Apply theme-based styling to simple text overlay"""
    if hasattr(self, 'simple_text_label') and self.simple_text_label:
        try:
            theme_colors = self.colors if hasattr(self, 'colors') else None
            
            # Base style with theme-specific color
            if theme_colors:
                text_color = theme_colors['text_primary'].name()
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
            else:
                base_style = """
                    QLabel {
                        font-size: 18px;
                        font-weight: bold;
                        font-family: 'Consolas', monospace;
                        background: transparent;
                        border: none;
                        white-space: nowrap;
                        color: white;
                    }
                """
            
            self.simple_text_label.setStyleSheet(base_style)
            
            # Set outline based on theme
            if theme_colors:
                if hasattr(self, 'theme') and self.theme == 'default':
                    self.simple_text_label.set_outline_enabled(True)
                    self.simple_text_label.set_outline_color('black')
                elif hasattr(self, 'theme') and self.theme == 'dark':
                    self.simple_text_label.set_outline_enabled(True)
                    self.simple_text_label.set_outline_color('black')
                elif hasattr(self, 'theme') and self.theme == 'neon':
                    self.simple_text_label.set_outline_enabled(True)
                    self.simple_text_label.set_outline_color('black')
                else:
                    self.simple_text_label.set_outline_enabled(True)
                    self.simple_text_label.set_outline_color('black')
            else:
                self.simple_text_label.set_outline_enabled(True)
                self.simple_text_label.set_outline_color('black')
                
        except (RuntimeError, AttributeError):
            pass

def apply_simple_notification_theme(self, notification_type):
    """Apply theme-based styling for kill/death notifications"""
    if hasattr(self, 'simple_text_label') and self.simple_text_label:
        try:
            theme_colors = self.colors if hasattr(self, 'colors') else None
            
            # Base style with theme-specific color
            if theme_colors:
                text_color = theme_colors['text_primary'].name()
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
            else:
                base_style = """
                    QLabel {
                        font-size: 18px;
                        font-weight: bold;
                        font-family: 'Consolas', monospace;
                        background: transparent;
                        border: none;
                        white-space: nowrap;
                        color: white;
                    }
                """
            
            self.simple_text_label.setStyleSheet(base_style)
            
            # Set outline based on theme
            if theme_colors:
                if hasattr(self, 'theme') and self.theme == 'default':
                    self.simple_text_label.set_outline_enabled(True)
                    self.simple_text_label.set_outline_color('black')
                elif hasattr(self, 'theme') and self.theme == 'dark':
                    self.simple_text_label.set_outline_enabled(True)
                    self.simple_text_label.set_outline_color('black')
                elif hasattr(self, 'theme') and self.theme == 'neon':
                    self.simple_text_label.set_outline_enabled(True)
                    self.simple_text_label.set_outline_color('black')
                else:
                    self.simple_text_label.set_outline_enabled(True)
                    self.simple_text_label.set_outline_color('black')
            else:
                self.simple_text_label.set_outline_enabled(True)
                self.simple_text_label.set_outline_color('black')
                
        except (RuntimeError, AttributeError):
            pass

def adjust_simple_text_size(self):
    if hasattr(self, 'simple_text_label') and self.simple_text_label:
        try:
            self.simple_text_label.adjustSize()
            self.adjustSize()
            self.resize(self.simple_text_label.sizeHint())
        except RuntimeError:
            pass

def update_simple_countdown(self):
    try:
        if not hasattr(self, 'simple_text_label') or not self.simple_text_label:
            if hasattr(self, 'countdown_timer') and self.countdown_timer:
                try:
                    self.countdown_timer.stop()
                except RuntimeError:
                    pass
            return
            
        if not hasattr(self, 'is_example_mode') or not self.is_example_mode:
            if hasattr(self, 'countdown_timer') and self.countdown_timer:
                try:
                    self.countdown_timer.stop()
                except RuntimeError:
                    pass
            return
            
        if not hasattr(self, 'countdown_seconds'):
            return
            
        if self.countdown_seconds > 0:
            self.countdown_seconds -= 1
            
            # Use theme colors if available
            if hasattr(self, 'colors') and self.colors:
                kill_color = self.colors['kill_color'].name()
                death_color = self.colors['death_color'].name()
                text_color = self.colors['text_primary'].name()
                
                segments = [
                    (t('player'), kill_color),
                    (t(' killed '), text_color),
                    (t('player'), death_color),
                    (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', text_color)
                ]
                self.simple_text_label.set_text_segments(segments)
            else:
                # Fallback to theme-specific hardcoded colors
                if hasattr(self, 'theme') and self.theme == 'default':
                    segments = [
                        (t('player'), '#00ff00'),
                        (t(' killed '), 'white'),
                        (t('player'), '#ff0000'),
                        (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', 'white')
                    ]
                    self.simple_text_label.set_text_segments(segments)
                elif hasattr(self, 'theme') and self.theme == 'neon':
                    segments = [
                        (t('player'), '#00ff7f'),
                        (t(' killed '), '#00ffff'),
                        (t('player'), '#ff1493'),
                        (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', '#00ffff')
                    ]
                    self.simple_text_label.set_text_segments(segments)
                else:
                    text = f"{t('player')}{t(' killed ')}{t('player')} {t('(EXAMPLE)')} {self.countdown_seconds}s"
                    self.simple_text_label.setText(text)
            
            adjust_simple_text_size(self)
        else:
            if hasattr(self, 'countdown_timer') and self.countdown_timer:
                try:
                    self.countdown_timer.stop()
                except RuntimeError:
                    pass
            self.start_fade_animation()
    except (RuntimeError, AttributeError):
        if hasattr(self, 'countdown_timer') and self.countdown_timer:
            try:
                self.countdown_timer.stop()
            except RuntimeError:
                pass
        return

def show_simple_kill_notification(self, victim, weapon=None):
    if hasattr(self, 'simple_text_label') and self.simple_text_label:
        try:
            player_name = t('You')
            if hasattr(self, 'parent_tracker') and self.parent_tracker:
                if hasattr(self.parent_tracker, 'local_user_name') and self.parent_tracker.local_user_name:
                    player_name = self.parent_tracker.local_user_name
            
            if hasattr(self, 'colors') and self.colors:
                kill_color = self.colors['kill_color'].name()
                death_color = self.colors['death_color'].name()
                text_color = self.colors['text_primary'].name()
                
                segments = [
                    (player_name, kill_color),
                    (t(' killed '), text_color),
                    (victim, death_color)
                ]
                self.simple_text_label.set_text_segments(segments)
            else:
                if hasattr(self, 'theme') and self.theme == 'default':
                    segments = [
                        (player_name, '#00ff00'),
                        (t(' killed '), 'white'),
                        (victim, '#ff0000')
                    ]
                    self.simple_text_label.set_text_segments(segments)
                elif hasattr(self, 'theme') and self.theme == 'neon':
                    segments = [
                        (player_name, '#00ff7f'),
                        (t(' killed '), '#00ffff'),
                        (victim, '#ff1493')
                    ]
                    self.simple_text_label.set_text_segments(segments)
                else:
                    text = f"{player_name}{t(' killed ')}{victim}"
                    self.simple_text_label.setText(text)
            
            apply_simple_notification_theme(self, 'kill')
            self.is_example_mode = False
            if hasattr(self, 'countdown_timer'):
                self.countdown_timer.stop()
            adjust_simple_text_size(self)
            self.setWindowOpacity(1.0)
            self.fade_timer.start(8000)
        except RuntimeError:
            return

def show_simple_death_notification(self, attacker, weapon=None):
    if hasattr(self, 'simple_text_label') and self.simple_text_label:
        try:
            player_name = t('You')
            if hasattr(self, 'parent_tracker') and self.parent_tracker:
                if hasattr(self.parent_tracker, 'local_user_name') and self.parent_tracker.local_user_name:
                    player_name = self.parent_tracker.local_user_name
            
            if hasattr(self, 'colors') and self.colors:
                kill_color = self.colors['kill_color'].name()
                death_color = self.colors['death_color'].name()
                text_color = self.colors['text_primary'].name()
                
                segments = [
                    (attacker, death_color),
                    (t(' killed '), text_color),
                    (player_name, kill_color)
                ]
                self.simple_text_label.set_text_segments(segments)
            else:
                if hasattr(self, 'theme') and self.theme == 'default':
                    segments = [
                        (attacker, '#ff0000'),
                        (t(' killed '), 'white'),
                        (player_name, '#00ff00')
                    ]
                    self.simple_text_label.set_text_segments(segments)
                elif hasattr(self, 'theme') and self.theme == 'neon':
                    segments = [
                        (attacker, '#ff1493'),
                        (t(' killed '), '#00ffff'),
                        (player_name, '#00ff7f')
                    ]
                    self.simple_text_label.set_text_segments(segments)
                else:
                    text = f"{attacker}{t(' killed ')}{player_name}"
                    self.simple_text_label.setText(text)
            
            apply_simple_notification_theme(self, 'death')
            self.is_example_mode = False
            if hasattr(self, 'countdown_timer'):
                self.countdown_timer.stop()
            adjust_simple_text_size(self)
            self.setWindowOpacity(1.0)
            self.fade_timer.start(8000)
        except RuntimeError:
            return

def start_fade_animation(self):
    try:
        if hasattr(self, 'fade_timer') and self.fade_timer:
            try:
                self.fade_timer.stop()
            except RuntimeError:
                pass
                
        if hasattr(self, 'countdown_timer') and self.countdown_timer:
            try:
                self.countdown_timer.stop()
            except RuntimeError:
                pass
        
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(2000)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.finished.connect(self.hide_simple_notification)
        self.fade_animation.start()
    except RuntimeError:
        pass

def hide_simple_notification(self):
    if hasattr(self, 'simple_text_label'):
        self.simple_text_label.setText("")
    self.setWindowOpacity(0.0)

def show_simple_notification(self):
    if hasattr(self, 'simple_text_label') and self.simple_text_label.text():
        current_text = self.simple_text_label.text()
        if "(EXAMPLE)" in current_text:
            show_simple_sample_notification(self)
        else:
            self.setWindowOpacity(1.0)
            if hasattr(self, 'fade_animation') and self.fade_animation:
                try:
                    self.fade_animation.stop()
                except RuntimeError:
                    pass
            if hasattr(self, 'countdown_timer') and self.countdown_timer:
                try:
                    self.countdown_timer.stop()
                except RuntimeError:
                    pass
            self.is_example_mode = False
            if hasattr(self, 'fade_timer') and self.fade_timer:
                try:
                    self.fade_timer.start(8000)
                except RuntimeError:
                    pass
    else:
        show_simple_sample_notification(self)

def show_simple_sample_notification(self):
    if hasattr(self, 'simple_text_label') and self.simple_text_label:
        try:
            self.is_example_mode = True
            self.countdown_seconds = 30
            
            if hasattr(self, 'colors') and self.colors:
                kill_color = self.colors['kill_color'].name()
                death_color = self.colors['death_color'].name()
                text_color = self.colors['text_primary'].name()
                
                segments = [
                    (t('player'), kill_color),
                    (t(' killed '), text_color),
                    (t('player'), death_color),
                    (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', text_color)
                ]
                self.simple_text_label.set_text_segments(segments)
            else:
                if hasattr(self, 'theme') and self.theme == 'default':
                    segments = [
                        (t('player'), '#00ff00'),
                        (t(' killed '), 'white'),
                        (t('player'), '#ff0000'),
                        (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', 'white')
                    ]
                    self.simple_text_label.set_text_segments(segments)
                elif hasattr(self, 'theme') and self.theme == 'neon':
                    segments = [
                        (t('player'), '#00ff7f'),
                        (t(' killed '), '#00ffff'),
                        (t('player'), '#ff1493'),
                        (f' {t("(EXAMPLE)")} {self.countdown_seconds}s', '#00ffff')
                    ]
                    self.simple_text_label.set_text_segments(segments)
                else:
                    text = f"{t('player')}{t(' killed ')}{t('player')} {t('(EXAMPLE)')} {self.countdown_seconds}s"
                    self.simple_text_label.setText(text)
            
            apply_simple_notification_theme(self, 'kill')
            adjust_simple_text_size(self)
            self.setWindowOpacity(1.0)
            if hasattr(self, 'fade_timer') and self.fade_timer:
                try:
                    if self.fade_timer.isActive():
                        self.fade_timer.stop()
                except RuntimeError:
                    pass
            if hasattr(self, 'countdown_timer') and self.countdown_timer:
                try:
                    self.countdown_timer.start(1000)
                except RuntimeError:
                    pass
        except RuntimeError:
            return

def clear_simple_container(self):
    try:
        if hasattr(self, 'countdown_timer') and self.countdown_timer:
            try:
                if self.countdown_timer and self.countdown_timer.isActive():
                    self.countdown_timer.stop()
            except RuntimeError:
                pass
                
        if hasattr(self, 'fade_timer') and self.fade_timer:
            try:
                if self.fade_timer.isActive():
                    self.fade_timer.stop()
            except RuntimeError:
                pass
                
        if hasattr(self, 'fade_animation') and self.fade_animation:
            try:
                self.fade_animation.stop()
            except RuntimeError:
                pass
                
        if hasattr(self, 'simple_text_label') and self.simple_text_label:
            try:
                self.simple_text_label.setText("")
            except RuntimeError:
                pass
                
        self.is_example_mode = False
        self.setWindowOpacity(0.0)
    except (RuntimeError, AttributeError):
        pass

def cleanup_simple_timers(self):
    """Cleanup all timers to prevent errors when overlay is destroyed"""
    try:
        if hasattr(self, 'countdown_timer') and self.countdown_timer:
            try:
                self.countdown_timer.stop()
                self.countdown_timer.disconnect()
                self.countdown_timer.deleteLater()
            except RuntimeError:
                pass
            self.countdown_timer = None
            
        if hasattr(self, 'fade_timer') and self.fade_timer:
            try:
                self.fade_timer.stop()
            except RuntimeError:
                pass
                
        if hasattr(self, 'fade_animation') and self.fade_animation:
            try:
                self.fade_animation.stop()
            except RuntimeError:
                pass
            self.fade_animation = None
            
        self.is_example_mode = False
    except (RuntimeError, AttributeError):
        pass