# route.py

import os
import sys
import json
import re
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to sys.path to import kill_parser
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from kill_parser import KillParser
from language_manager import t

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QApplication
)
from PyQt5.QtCore import (
    Qt, QTimer, QPoint, pyqtSlot
)
from PyQt5.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient, 
    QRadialGradient
)

from .form import GlobalHotkeyThread
from .minimal_overlay import create_minimal_ui
from .compact_overlay import create_compact_ui
from .detailed_overlay import create_detailed_ui
from .horizontal_overlay import create_horizontal_ui
from .faded_overlay import (
    create_faded_ui, show_death_notification, show_kill_notification,
    show_faded_notification, show_faded_positioning_helper,
    stop_all_faded_animations, fade_notification, hide_faded_notification,
    hide_positioning_helper, update_countdown, clear_faded_container
)

class GameOverlay(QWidget):
    """Overlay for Star Citizen"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_tracker = parent
        self.is_dragging = False
        self.drag_position = QPoint()
        self.resize_mode = False
        self.config_file = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "SCTool_Tracker", "overlay_config.json")
        self.config = self.load_config()
        
        self.create_faded_ui = lambda: create_faded_ui(self)
        self.show_death_notification = lambda attacker, weapon, zone, game_mode="Unknown": show_death_notification(self, attacker, weapon, zone, game_mode)
        self.show_kill_notification = lambda victim, weapon, zone, game_mode="Unknown": show_kill_notification(self, victim, weapon, zone, game_mode)
        self.show_faded_notification = lambda: show_faded_notification(self)
        self.show_faded_positioning_helper = lambda: show_faded_positioning_helper(self)
        self.stop_all_faded_animations = lambda: stop_all_faded_animations(self)
        self.fade_notification = lambda: fade_notification(self)
        self.hide_faded_notification = lambda: hide_faded_notification(self)
        self.hide_positioning_helper = lambda: hide_positioning_helper(self)
        self.update_countdown = lambda: update_countdown(self)
        self.clear_faded_container = lambda: clear_faded_container(self)

        self.create_minimal_ui = lambda: create_minimal_ui(self)
        self.create_compact_ui = lambda: create_compact_ui(self)
        self.create_detailed_ui = lambda: create_detailed_ui(self)
        self.create_horizontal_ui = lambda: create_horizontal_ui(self)
        
        self.hotkey_enabled = self.config.get('hotkey_enabled', True)
        self.hotkey_combination = self.config.get('hotkey_combination', 'ctrl+`')
        self.hotkey_thread = None
        self.setup_global_hotkey()

        self.live_update_timer = QTimer()
        self.live_update_timer.timeout.connect(self.update_live_data)
        self.live_update_timer.start(1000)

        self.is_enabled = self.config.get('enabled', False)
        self.is_visible = False
        self.display_mode = self.config.get('display_mode', 'compact')
        self.opacity_level = self.config.get('opacity', 0.9)
        self.show_animations = self.config.get('animations', True)
        self.is_locked = self.config.get('locked', False)
        
        self.kills = 0
        self.deaths = 0
        self.session_time = "00:00"
        self.ship = "Unknown"
        self.game_mode = "Unknown"
        self.last_kill_info = None
        self.last_death_info = None
        self.kill_streak = 0
        self.best_kill_streak = 0
        self.session_start = datetime.now()
        self.theme = self.config.get('theme', 'default')
        self.colors = self.get_theme_colors()
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animations)
        self.pulse_alpha = 0
        self.pulse_direction = 1
        
        self.setup_overlay()
        self.create_ui()
        self.load_position()

        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_config)
        self.save_timer.start(5000)
        
        if self.is_enabled:
            self.show_overlay()
        
    def set_enabled(self, enabled: bool):
        """Set overlay enabled state and save to config"""
        self.is_enabled = enabled
        self.config['enabled'] = enabled
        if enabled:
            self.show_overlay()
        else:
            self.hide_overlay()

    def setup_global_hotkey(self):
        """Setup global hotkey for toggling overlay"""
        if not self.hotkey_enabled or not sys.platform.startswith('win'):
            if not sys.platform.startswith('win'):
                print("Global hotkeys are only supported on Windows")
            return
        
        try:
            if self.hotkey_thread and self.hotkey_thread.isRunning():
                self.hotkey_thread.stop()
                self.hotkey_thread.wait(1000)
            
            print(f"Setting up hotkey: {self.hotkey_combination}")
            self.hotkey_thread = GlobalHotkeyThread(self.hotkey_combination)
            self.hotkey_thread.hotkey_pressed.connect(self.toggle_overlay_visibility)
            self.hotkey_thread.start()
            
            QTimer.singleShot(500, lambda: self.check_hotkey_status())
            
        except Exception as e:
            print(f"Failed to setup global hotkey: {e}")
            traceback.print_exc()
    
    def check_hotkey_status(self):
        """Check if hotkey was successfully registered"""
        if self.hotkey_thread and self.hotkey_thread.isRunning():
            print(f"Hotkey thread is running for: {self.hotkey_combination}")
        else:
            print(f"Warning: Hotkey thread may not have started properly")

    @pyqtSlot()
    def toggle_overlay_visibility(self):
        """Toggle overlay visibility when hotkey is pressed"""
        if self.display_mode == 'faded':
            return
        
        if self.is_visible:
            self.hide_overlay()
        else:
            self.show_overlay()
    
    def show_hotkey_notification(self, title: str, message: str):
        """Show a temporary notification when hotkey is used"""
        notification = QWidget()
        notification.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.BypassWindowManagerHint
        )
        notification.setAttribute(Qt.WA_TranslucentBackground, True)
        
        layout = QVBoxLayout(notification)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['accent'].name()};
                font-size: 18px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        title_label.setAlignment(Qt.AlignCenter)
        
        message_label = QLabel(message)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        message_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(message_label)

        notification.setStyleSheet(f"""
            QWidget {{
                background: {self.colors['background'].name()};
                border: 2px solid {self.colors['accent'].name()};
                border-radius: 8px;
            }}
        """)
        
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        notification.adjustSize()
        notification.move(
            screen.width() // 2 - notification.width() // 2,
            screen.height() // 2 - notification.height() // 2
        )
        
        notification.show()
        
        QTimer.singleShot(2000, notification.deleteLater)
    
    def set_hotkey_combination(self, combination: str):
        """Set new hotkey combination"""
        self.hotkey_combination = combination
        self.config['hotkey_combination'] = combination
        self.setup_global_hotkey()
    
    def set_hotkey_enabled(self, enabled: bool):
        """Enable/disable global hotkey"""
        self.hotkey_enabled = enabled
        self.config['hotkey_enabled'] = enabled
        
        if enabled:
            self.setup_global_hotkey()
        else:
            if self.hotkey_thread and self.hotkey_thread.isRunning():
                self.hotkey_thread.stop()
                self.hotkey_thread.wait(1000)

    def load_config(self) -> Dict[str, Any]:
        """Load overlay configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading overlay config: {e}")
        return {
            'position': {'x': 50, 'y': 50},
            'size': {'width': 300, 'height': 200},
            'opacity': 0.9,
            'display_mode': 'compact',
            'theme': 'default',
            'animations': True,
            'show_latest_kill': True,
            'show_session_stats': True,
            'auto_hide_delay': 0,
            'font_size': 12,
            'locked': False,
            'enabled': False,
            'hotkey_enabled': True,
            'hotkey_combination': 'ctrl+`'
        }
    
    def save_config(self):
        """Save overlay configuration to file"""
        try:
            self.config['position'] = {'x': self.x(), 'y': self.y()}
            self.config['size'] = {'width': self.width(), 'height': self.height()}
            self.config['opacity'] = self.opacity_level
            self.config['display_mode'] = self.display_mode
            self.config['enabled'] = self.is_enabled
            self.config['theme'] = self.theme
            self.config['animations'] = self.show_animations
            self.config['locked'] = self.is_locked
            self.config['hotkey_enabled'] = self.hotkey_enabled
            self.config['hotkey_combination'] = self.hotkey_combination

            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving overlay config: {e}")
    
    def get_theme_colors(self) -> Dict[str, QColor]:
        """Get colors for the current theme"""
        themes = {
            'default': {
                'background': QColor(0, 0, 0, 180),
                'border': QColor(0, 255, 65, 200),
                'text_primary': QColor(255, 255, 255, 255),
                'text_secondary': QColor(200, 200, 200, 255),
                'accent': QColor(0, 255, 65, 255),
                'kill_color': QColor(102, 255, 102, 255),
                'death_color': QColor(240, 71, 71, 255),
                'info_color': QColor(0, 204, 255, 255)
            },
            'dark': {
                'background': QColor(15, 15, 15, 200),
                'border': QColor(60, 60, 60, 200),
                'text_primary': QColor(255, 255, 255, 255),
                'text_secondary': QColor(180, 180, 180, 255),
                'accent': QColor(255, 140, 0, 255),
                'kill_color': QColor(76, 175, 80, 255),
                'death_color': QColor(244, 67, 54, 255),
                'info_color': QColor(33, 150, 243, 255)
            },
            'neon': {
                'background': QColor(5, 5, 5, 190),
                'border': QColor(0, 255, 255, 220),
                'text_primary': QColor(0, 255, 255, 255),
                'text_secondary': QColor(0, 200, 200, 255),
                'accent': QColor(255, 0, 255, 255),
                'kill_color': QColor(0, 255, 127, 255),
                'death_color': QColor(255, 20, 147, 255),
                'info_color': QColor(0, 191, 255, 255)
            }
        }
        return themes.get(self.theme, themes['default'])
    
    def setup_overlay(self):
        """Setup overlay window properties"""
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.BypassWindowManagerHint |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        
        size = self.config.get('size', {'width': 300, 'height': 200})
        self.setMinimumSize(150, 80)
        self.setMaximumSize(500, 800)
        self.resize(size['width'], size['height'])    
        self.setWindowOpacity(self.opacity_level)
        
        if self.is_locked:
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.SizeAllCursor)
    
    def setParent(self, parent):
        """Override setParent to maintain independence"""
        self.parent_tracker = parent
        super().setParent(None)
    
    def closeEvent(self, event):
        """Handle close event - cleanup hotkey thread"""
        if self.hotkey_thread and self.hotkey_thread.isRunning():
            self.hotkey_thread.stop()
            self.hotkey_thread.wait(1000)
        
        self.hide_overlay()
        event.ignore()

    def load_position(self):
        """Load position from config"""
        pos = self.config.get('position', {'x': 50, 'y': 50})
        self.move(pos['x'], pos['y'])

    def create_ui(self):
        """Create overlay UI elements based on display mode"""
        if self.layout():
            QWidget().setLayout(self.layout())
        
        if self.display_mode == 'minimal':
            self.create_minimal_ui()
        elif self.display_mode == 'detailed':
            self.create_detailed_ui()
        elif self.display_mode == 'horizontal':
            self.create_horizontal_ui()
        elif self.display_mode == 'faded':
            self.create_faded_ui()
        else:
            self.create_compact_ui()
        
        self.adjust_size_to_content()

    def paintEvent(self, event):
        """Draw overlay background with enhanced visuals and animations"""
        if self.display_mode == 'faded' and (not hasattr(self, 'faded_container') or not self.faded_container.isVisible()):
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(2, 2, -2, -2)

        if self.display_mode == 'faded':
            gradient = QRadialGradient(rect.center(), max(rect.width(), rect.height()) / 2)
            bg_color = QColor(self.colors['background'])
            bg_color.setAlpha(int(bg_color.alpha() * self.opacity_level * 0.95))
            
            gradient.setColorAt(0.0, bg_color)
            darker_bg = QColor(bg_color)
            darker_bg.setRgb(
                max(0, bg_color.red() - 30),
                max(0, bg_color.green() - 30),
                max(0, bg_color.blue() - 30),
                int(bg_color.alpha() * 0.8)
            )
            gradient.setColorAt(1.0, darker_bg)
            
            painter.setBrush(QBrush(gradient))

            border_color = QColor(self.colors['accent'])
            border_color.setAlpha(int(border_color.alpha() * self.opacity_level))
            painter.setPen(QPen(border_color, 3))
            painter.drawRoundedRect(rect, 12, 12)

            glow_color = QColor(self.colors['accent'])
            glow_color.setAlpha(int(glow_color.alpha() * 0.3 * self.opacity_level))
            painter.setPen(QPen(glow_color, 6))
            painter.drawRoundedRect(rect.adjusted(-2, -2, 2, 2), 14, 14)
        else:
            gradient = QLinearGradient(0, 0, 0, rect.height())
            bg_color = QColor(self.colors['background'])
            bg_color.setAlpha(int(bg_color.alpha() * self.opacity_level))
            
            gradient.setColorAt(0.0, bg_color)
            darker_bg = QColor(bg_color)
            darker_bg.setRgb(
                max(0, bg_color.red() - 20),
                max(0, bg_color.green() - 20),
                max(0, bg_color.blue() - 20),
                bg_color.alpha()
            )
            gradient.setColorAt(1.0, darker_bg)
            
            painter.setBrush(QBrush(gradient))

            border_color = QColor(self.colors['border'])
            border_width = 2
            if self.show_animations and self.animation_timer.isActive():
                border_width = int(2 + 2 * self.pulse_alpha)
            else:
                border_width = 2
            
            painter.setPen(QPen(border_color, border_width))
            painter.drawRoundedRect(rect, 8, 8)

            if hasattr(self, 'kill_glow_alpha') and self.kill_glow_alpha > 0:
                glow_color = QColor(self.colors['kill_color'])
                glow_color.setAlpha(int(255 * self.kill_glow_alpha * 0.3))
                painter.setPen(QPen(glow_color, 4))
                painter.drawRoundedRect(rect.adjusted(-1, -1, 1, 1), 9, 9)

            if hasattr(self, 'death_glow_alpha') and self.death_glow_alpha > 0:
                glow_color = QColor(self.colors['death_color'])
                glow_color.setAlpha(int(255 * self.death_glow_alpha * 0.3))
                painter.setPen(QPen(glow_color, 4))
                painter.drawRoundedRect(rect.adjusted(-1, -1, 1, 1), 9, 9)

    def update_translations(self):
        """Update all translatable text in the overlay when language changes"""
        try:
            self.create_ui()
            self.update_display()
        except Exception as e:
            print(f"Error updating overlay translations: {e}")

    def cycle_display_mode(self):
        """Cycle through display modes"""
        modes = ['minimal', 'compact', 'detailed', 'horizontal', 'faded']
        current_index = modes.index(self.display_mode)
        next_index = (current_index + 1) % len(modes)
        self.display_mode = modes[next_index]
        self.config['display_mode'] = self.display_mode
        self.create_ui()
        self.update_display()
        self.adjust_size_to_content()
        self.show_mode_change_indicator()

        if self.display_mode == 'faded':
            self.show_faded_positioning_helper()
    
    def show_mode_change_indicator(self):
        """Show visual indicator when mode changes"""
        pass
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton and not self.is_locked:
            if self.display_mode == 'faded' and hasattr(self, 'faded_container') and self.faded_container.isVisible():
                pass
            
            self.is_dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle dragging"""
        if self.is_dragging and event.buttons() == Qt.LeftButton and not self.is_locked:
            new_pos = event.globalPos() - self.drag_position
            self.move(new_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self.is_dragging = False
        event.accept()
    
    def wheelEvent(self, event):
        """Handle mouse wheel for opacity adjustment"""
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y() / 120
            new_opacity = max(0.3, min(1.0, self.opacity_level + delta * 0.1))
            self.set_opacity(new_opacity)
            event.accept()
    
    def set_opacity(self, opacity: float):
        """Set overlay opacity"""
        self.opacity_level = opacity
        self.config['opacity'] = opacity
        self.setWindowOpacity(opacity)
        self.update()
    
    def set_theme(self, theme: str):
        """Change overlay theme"""
        self.theme = theme
        self.config['theme'] = theme
        self.colors = self.get_theme_colors()
        self.create_ui()
        self.update_display()
    
    def toggle_animations(self, enabled: bool):
        """Toggle animations with immediate visual feedback"""
        self.show_animations = enabled
        self.config['animations'] = enabled
        
        if enabled:
            if not hasattr(self, 'kill_glow_alpha'):
                self.kill_glow_alpha = 0
            if not hasattr(self, 'death_glow_alpha'):
                self.death_glow_alpha = 0
            
            self.animation_timer.start(50)
            
            self.pulse_alpha = 0
            self.pulse_direction = 1
        else:
            self.animation_timer.stop()
            self.pulse_alpha = 0
            if hasattr(self, 'kill_glow_alpha'):
                self.kill_glow_alpha = 0
            if hasattr(self, 'death_glow_alpha'):
                self.death_glow_alpha = 0
            self.update()
    
    def set_locked(self, locked: bool):
        """Set overlay lock state"""
        self.is_locked = locked
        self.config['locked'] = locked
        if locked:
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.SizeAllCursor)
    
    def update_animations(self):
        """Update animation states"""
        if not self.show_animations:
            return
        
        self.pulse_alpha += self.pulse_direction * 0.08
        if self.pulse_alpha >= 1.0:
            self.pulse_alpha = 1.0
            self.pulse_direction = -1
        elif self.pulse_alpha <= 0.0:
            self.pulse_alpha = 0.0
            self.pulse_direction = 1

        if hasattr(self, 'kill_glow_alpha'):
            self.kill_glow_alpha = max(0, self.kill_glow_alpha - 0.02)
        if hasattr(self, 'death_glow_alpha'):
            self.death_glow_alpha = max(0, self.death_glow_alpha - 0.02)
        
        self.update()
    
    def trigger_kill_animation(self):
        """Trigger animation effects for a kill"""
        if not self.show_animations:
            return
        
        self.kill_glow_alpha = 1.0
        
        if not self.animation_timer.isActive():
            self.animation_timer.start(50)

        QTimer.singleShot(3000, self.check_stop_animations)

    def trigger_death_animation(self):
        """Trigger animation effects for a death"""
        if not self.show_animations:
            return
        
        self.death_glow_alpha = 1.0
        
        if not self.animation_timer.isActive():
            self.animation_timer.start(50)
        
        QTimer.singleShot(3000, self.check_stop_animations)

    def check_stop_animations(self):
        """Stop animations if no active glows"""
        kill_glow = getattr(self, 'kill_glow_alpha', 0)
        death_glow = getattr(self, 'death_glow_alpha', 0)
        
        if kill_glow <= 0 and death_glow <= 0 and not self.show_animations:
            self.animation_timer.stop()

    def update_live_data(self):
        """Update live data like session time, ship info, etc."""
        if not self.is_visible or not self.parent_tracker:
            return

        if hasattr(self.parent_tracker, 'session_time_display'):
            session_time_text = self.parent_tracker.session_time_display.text()
            if session_time_text != self.session_time:
                self.session_time = session_time_text
                self.update_session_time_display()

        if hasattr(self.parent_tracker, 'ship_combo'):
            current_ship = self.parent_tracker.ship_combo.currentText() or "Unknown"
            if current_ship != self.ship:
                self.ship = current_ship
                self.update_ship_display()        
        if hasattr(self.parent_tracker, 'game_mode_display'):
            mode_text = self.parent_tracker.game_mode_display.text()
            if mode_text.startswith('Mode: '):
                new_mode = mode_text[6:]
                if new_mode != self.game_mode:
                    self.game_mode = new_mode
                    self.update_game_mode_display()

    def update_session_time_display(self):
        """Update only session time labels without full UI refresh"""
        if self.display_mode == 'compact':
            if hasattr(self, 'session_label_c'):
                self.session_label_c.setText(t("Session") + f": {self.session_time}")
                
        elif self.display_mode == 'detailed':
            if hasattr(self, 'session_time_label'):
                self.session_time_label.setText(t("Session") + f": {self.session_time}")
                
        elif self.display_mode == 'horizontal':
            if hasattr(self, 'session_time_label_h'):
                self.session_time_label_h.setText(t("Session") + f": {self.session_time}")
         
    def update_ship_display(self):
        """Update only ship labels without full UI refresh"""
        if self.display_mode == 'compact':
            if hasattr(self, 'ship_label_c'):
                self.ship_label_c.setText(t("Ship") + f": {self.ship}")
                
        elif self.display_mode == 'detailed':
            if hasattr(self, 'ship_label'):
                self.ship_label.setText(t("Ship") + f": {self.ship}")
                
        elif self.display_mode == 'horizontal':
            if hasattr(self, 'ship_label_h'):
                self.ship_label_h.setText(t("Ship") + f": {self.ship}")

    def update_game_mode_display(self):
        """Update only game mode labels without full UI refresh"""
        if self.display_mode == 'compact':
            if hasattr(self, 'game_mode_label_c'):
                self.game_mode_label_c.setText(t("Mode") + f": {self.game_mode}")
                
        elif self.display_mode == 'detailed':
            if hasattr(self, 'game_mode_label'):
                self.game_mode_label.setText(t("Mode") + f": {self.game_mode}")
                
        elif self.display_mode == 'horizontal':
            if hasattr(self, 'game_mode_label_h'):
                self.game_mode_label_h.setText(t("Mode") + f": {self.game_mode}")
                
        elif self.display_mode == 'minimal':
            if hasattr(self, 'game_mode_label_m'):
                mode_text = t("Mode")
                self.game_mode_label_m.setText(f"{mode_text}: {self.game_mode}")

    def hide_overlay(self):
        """Hide the overlay"""
        self.is_visible = False
        self.hide()
        self.animation_timer.stop()
        if hasattr(self, 'live_update_timer'):
            self.live_update_timer.stop()
        if hasattr(self, 'fade_timer'):
            self.fade_timer.stop()
        if hasattr(self, 'fade_animation'):
            self.fade_animation.stop()

    def show_overlay(self):
        """Show the overlay"""
        self.is_visible = True
        
        if self.display_mode == 'faded':
            return
        
        self.show()
        if self.show_animations:
            self.animation_timer.start(50)
        if hasattr(self, 'live_update_timer'):
            self.live_update_timer.start(1000)
    
    def update_stats(self, kills: int, deaths: int, session_time: str = "00:00", 
        ship: str = "Unknown", game_mode: str = "Unknown", 
        kill_streak: int = 0, latest_kill: Optional[Dict] = None,
        latest_death: Optional[Dict] = None):
        """Update overlay with new stats and trigger animations"""
        prev_kills = self.kills
        prev_deaths = self.deaths
        
        if latest_kill:
            self.last_kill_info = latest_kill
            
        if latest_death:
            self.last_death_info = latest_death
            
        if kills > prev_kills:
            self.trigger_kill_animation()
            self.kill_streak = kill_streak
            if self.kill_streak > self.best_kill_streak:
                self.best_kill_streak = self.kill_streak
        elif deaths > prev_deaths:
            self.trigger_death_animation()
            self.kill_streak = 0
        
        self.kills = kills
        self.deaths = deaths
        self.session_time = session_time
        self.ship = ship
        self.game_mode = game_mode
        
        self.update_display()

    def update_display(self):
        """Update the display based on current mode and data"""        
        if not hasattr(self, 'layout') or not self.layout():
            return
        
        if self.deaths > 0:
            kd_ratio = f"{self.kills / self.deaths:.2f}"        
        else:
            kd_ratio = str(self.kills) if self.kills > 0 else "--"
        
        if self.display_mode == 'minimal':
            if hasattr(self, 'kills_count'):
                self.kills_count.setText(str(self.kills))
            if hasattr(self, 'deaths_count'):
                self.deaths_count.setText(str(self.deaths))
            if hasattr(self, 'game_mode_label_m'):
                mode_text = t('Mode')
                self.game_mode_label_m.setText(f"{mode_text}: {self.game_mode}")
                
        elif self.display_mode == 'compact':
            if hasattr(self, 'kills_value_c'):
                self.kills_value_c.setText(str(self.kills))
            if hasattr(self, 'deaths_value_c'):
                self.deaths_value_c.setText(str(self.deaths))
            if hasattr(self, 'kd_value_c'):
                self.kd_value_c.setText(kd_ratio)
            if hasattr(self, 'session_label_c'):
                self.session_label_c.setText(t("Session") + f": {self.session_time}")
            if hasattr(self, 'game_mode_label_c'):
                self.game_mode_label_c.setText(t("Mode") + f": {self.game_mode}")
            if hasattr(self, 'ship_label_c'):
                self.ship_label_c.setText(t("Ship") + f": {self.ship}")
                
        elif self.display_mode == 'detailed':
            if hasattr(self, 'kills_value'):
                self.kills_value.setText(str(self.kills))
            if hasattr(self, 'deaths_value'):
                self.deaths_value.setText(str(self.deaths))
            if hasattr(self, 'kd_value'):
                self.kd_value.setText(kd_ratio)
            if hasattr(self, 'session_time_label'):
                self.session_time_label.setText(t("Session") + f": {self.session_time}")
            if hasattr(self, 'game_mode_label'):
                self.game_mode_label.setText(t("Mode") + f": {self.game_mode}")
            if hasattr(self, 'ship_label'):
                self.ship_label.setText(t("Ship") + f": {self.ship}")
            
            if hasattr(self, 'latest_kill_frame'):
                if self.last_kill_info:
                    victim = self.last_kill_info.get('victim', 'Unknown')
                    weapon = self.last_kill_info.get('weapon', 'Unknown')
                    location = self.last_kill_info.get('location', 'Unknown')
                    attacker = self.last_kill_info.get('attacker', 'Unknown')
                    game_mode = self.last_kill_info.get('game_mode', 'Unknown')                    
                    if hasattr(self, 'latest_kill_attacker'):
                        self.latest_kill_attacker.setText(t("Attacker") + f": {attacker}")
                    if hasattr(self, 'latest_kill_engagement'):
                        formatted_weapon = KillParser.format_weapon(weapon)
                        self.latest_kill_engagement.setText(t("Engagement") + f": {formatted_weapon}")
                    if hasattr(self, 'latest_kill_method'):
                        self.latest_kill_method.setText(t("Method") + ": " + t("Player destruction"))
                    if hasattr(self, 'latest_kill_victim'):
                        self.latest_kill_victim.setText(t("Victim") + f": {victim}")
                    if hasattr(self, 'latest_kill_location'):
                        formatted_location = KillParser.format_zone(location)
                        self.latest_kill_location.setText(t("Location") + f": {formatted_location}")
                    if hasattr(self, 'latest_kill_organization'):
                        self.latest_kill_organization.setText(t("Organization") + ": " + t("None") + " (" + t("Tag") + ": " + t("None") + ")")
                else:
                    if hasattr(self, 'latest_kill_attacker'):
                        self.latest_kill_attacker.setText(t("Attacker") + ": --")
                    if hasattr(self, 'latest_kill_engagement'):
                        self.latest_kill_engagement.setText(t("Engagement") + ": --")
                    if hasattr(self, 'latest_kill_method'):
                        self.latest_kill_method.setText(t("Method") + ": --")
                    if hasattr(self, 'latest_kill_victim'):
                        self.latest_kill_victim.setText(t("Victim") + ": --")
                    if hasattr(self, 'latest_kill_location'):
                        self.latest_kill_location.setText(t("Location") + ": --")
                    if hasattr(self, 'latest_kill_organization'):
                        self.latest_kill_organization.setText(t("Organization") + ": -- (" + t("Tag") + ": --)")

            if hasattr(self, 'latest_death_frame'):
                if self.last_death_info:
                    attacker = self.last_death_info.get('attacker', 'Unknown')
                    weapon = self.last_death_info.get('weapon', 'Unknown')
                    location = self.last_death_info.get('location', 'Unknown')
                    timestamp = self.last_death_info.get('timestamp', 'Unknown')
                    game_mode = self.last_death_info.get('game_mode', 'Unknown')
                    
                    if hasattr(self, 'latest_death_attacker'):
                        self.latest_death_attacker.setText(t("Attacker") + f": {attacker}")
                    if hasattr(self, 'latest_death_organization'):
                        self.latest_death_organization.setText(t("Organization") + ": " + t("None") + " (" + t("Tag") + ": " + t("None") + ")")
                    if hasattr(self, 'latest_death_location'):
                        formatted_location = KillParser.format_zone(location)
                        self.latest_death_location.setText(t("Location") + f": {formatted_location}")
                    if hasattr(self, 'latest_death_damage_type'):
                        formatted_weapon = KillParser.format_weapon(weapon)
                        self.latest_death_damage_type.setText(t("Damage Type") + f": {formatted_weapon}")
                else:
                    if hasattr(self, 'latest_death_attacker'):
                        self.latest_death_attacker.setText(t("Attacker") + ": --")
                    if hasattr(self, 'latest_death_organization'):
                        self.latest_death_organization.setText(t("Organization") + ": -- (" + t("Tag") + ": --)")
                    if hasattr(self, 'latest_death_location'):
                        self.latest_death_location.setText(t("Location") + ": --")
                    if hasattr(self, 'latest_death_damage_type'):
                        self.latest_death_damage_type.setText(t("Damage Type") + ": --")

        elif self.display_mode == 'horizontal':
            if hasattr(self, 'kills_value_h'):
                self.kills_value_h.setText(str(self.kills))
            if hasattr(self, 'deaths_value_h'):
                self.deaths_value_h.setText(str(self.deaths))
            if hasattr(self, 'kd_value_h'):
                self.kd_value_h.setText(kd_ratio)
            if hasattr(self, 'session_time_label_h'):
                self.session_time_label_h.setText(t("Session") + f": {self.session_time}")
            if hasattr(self, 'game_mode_label_h'):
                self.game_mode_label_h.setText(t("Mode") + f": {self.game_mode}")
            if hasattr(self, 'ship_label_h'):
                self.ship_label_h.setText(t("Ship") + f": {self.ship}")
            
            if hasattr(self, 'latest_kill_info_h'):
                if self.last_kill_info:
                    kill_text = f"{self.last_kill_info.get('victim', t('Unknown'))}"
                    self.latest_kill_info_h.setText(kill_text)
                else:
                    self.latest_kill_info_h.setText(t("No kills yet"))
            
            if hasattr(self, 'latest_death_info_h'):
                if self.last_death_info:
                    death_text = t("By") + f": {self.last_death_info.get('attacker', t('Unknown'))}"
                    self.latest_death_info_h.setText(death_text)
                else:
                    self.latest_death_info_h.setText(t("No deaths yet"))

        self.adjust_size_to_content()
    
    def adjust_size_to_content(self):
        """Dynamically adjust overlay size based on content"""
        if self.display_mode == 'faded':
            return

        if self.display_mode == 'detailed':
            self.setMinimumSize(400, 350)
            self.resize(700, 600)
                
        elif self.display_mode == 'compact':
            self.setMinimumSize(320, 200)
            self.resize(350, 220)
                
        elif self.display_mode == 'minimal':
            self.setMinimumSize(120, 70)
            self.resize(120, 70)
        elif self.display_mode == 'horizontal':
            self.setMinimumSize(800, 120)
            self.resize(1200, 120)
    
    def handle_content_update(self):
        """Handle content updates and ensure proper sizing"""
        if hasattr(self, 'layout') and self.layout():
            self.layout().update()

        QApplication.processEvents()
        self.adjust_size_to_content()
        self.update_display()