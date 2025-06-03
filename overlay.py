# overlay.py

import json
import os
import re
import base64
from datetime import datetime
import sys
import ctypes
from ctypes import wintypes
import threading
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, 
    QCheckBox, QPushButton, QSlider, QComboBox, QSpinBox,
    QColorDialog, QGroupBox, QGridLayout, QTextEdit, QScrollArea,
    QApplication
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize, QPropertyAnimation, QEasingCurve, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QLinearGradient, 
    QRadialGradient, QPixmap, QPainterPath, QFontMetrics
)

class HotkeyCapture(QWidget):
    """Widget for capturing hotkey combinations"""
    hotkey_captured = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.capturing = False
        self.pressed_keys = set()
        self.modifier_names = {
            Qt.Key_Control: 'ctrl',
            Qt.Key_Alt: 'alt',
            Qt.Key_Shift: 'shift',
            Qt.Key_Meta: 'win'
        }
        
        self.key_names = {
            Qt.Key_A: 'a', Qt.Key_B: 'b', Qt.Key_C: 'c', Qt.Key_D: 'd', Qt.Key_E: 'e',
            Qt.Key_F: 'f', Qt.Key_G: 'g', Qt.Key_H: 'h', Qt.Key_I: 'i', Qt.Key_J: 'j',
            Qt.Key_K: 'k', Qt.Key_L: 'l', Qt.Key_M: 'm', Qt.Key_N: 'n', Qt.Key_O: 'o',
            Qt.Key_P: 'p', Qt.Key_Q: 'q', Qt.Key_R: 'r', Qt.Key_S: 's', Qt.Key_T: 't',
            Qt.Key_U: 'u', Qt.Key_V: 'v', Qt.Key_W: 'w', Qt.Key_X: 'x', Qt.Key_Y: 'y',
            Qt.Key_Z: 'z',
            Qt.Key_0: '0', Qt.Key_1: '1', Qt.Key_2: '2', Qt.Key_3: '3', Qt.Key_4: '4',
            Qt.Key_5: '5', Qt.Key_6: '6', Qt.Key_7: '7', Qt.Key_8: '8', Qt.Key_9: '9',
            Qt.Key_F1: 'f1', Qt.Key_F2: 'f2', Qt.Key_F3: 'f3', Qt.Key_F4: 'f4',
            Qt.Key_F5: 'f5', Qt.Key_F6: 'f6', Qt.Key_F7: 'f7', Qt.Key_F8: 'f8',
            Qt.Key_F9: 'f9', Qt.Key_F10: 'f10', Qt.Key_F11: 'f11', Qt.Key_F12: 'f12',
            Qt.Key_Space: 'space', Qt.Key_Enter: 'enter', Qt.Key_Return: 'enter',
            Qt.Key_Escape: 'esc', Qt.Key_Tab: 'tab', Qt.Key_Backspace: 'backspace',
            Qt.Key_Delete: 'delete', Qt.Key_Insert: 'insert', Qt.Key_Home: 'home',
            Qt.Key_End: 'end', Qt.Key_PageUp: 'pageup', Qt.Key_PageDown: 'pagedown',
            Qt.Key_Up: 'up', Qt.Key_Down: 'down', Qt.Key_Left: 'left', Qt.Key_Right: 'right',
            Qt.Key_QuoteLeft: '`',
            Qt.Key_Minus: '-', 
            Qt.Key_Equal: '=', 
            Qt.Key_Semicolon: ';',
            Qt.Key_Apostrophe: "'", 
            Qt.Key_Comma: ',', 
            Qt.Key_Period: '.', 
            Qt.Key_Slash: '/',
            Qt.Key_Backslash: '\\', 
            Qt.Key_BracketLeft: '[', 
            Qt.Key_BracketRight: ']'
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.capture_button = QPushButton("Click to Capture Hotkey")
        self.capture_button.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e;
                color: #f0f0f0;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                min-height: 30px;
            }
            QPushButton:hover {
                border-color: #00ff41;
                background-color: #2a2a2a;
            }
            QPushButton:pressed {
                background-color: #00ff41;
                color: #000000;
            }
        """)
        self.capture_button.clicked.connect(self.start_capture)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 12px;
                font-style: italic;
            }
        """)
        
        layout.addWidget(self.capture_button)
        layout.addWidget(self.status_label)
    
    def start_capture(self):
        """Start capturing hotkey combination"""
        self.capturing = True
        self.pressed_keys.clear()
        self.capture_button.setText("Press key combination...")
        self.capture_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: #ffffff;
                border: 1px solid #ff6666;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                min-height: 30px;
                font-weight: bold;
            }
        """)
        self.status_label.setText("Press your desired key combination now...")
        self.setFocus()
        self.grabKeyboard()
    
    def stop_capture(self):
        """Stop capturing and process the result"""
        self.capturing = False
        self.releaseKeyboard()
        self.capture_button.setText("Click to Capture Hotkey")
        self.capture_button.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e;
                color: #f0f0f0;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                min-height: 30px;
            }
            QPushButton:hover {
                border-color: #00ff41;
                background-color: #2a2a2a;
            }
            QPushButton:pressed {
                background-color: #00ff41;
                color: #000000;
            }
        """)
        
        if self.pressed_keys:
            modifiers = []
            main_key = None
            
            for key in self.pressed_keys:
                if key in self.modifier_names:
                    modifiers.append(self.modifier_names[key])
                elif key in self.key_names:
                    main_key = self.key_names[key]
            
            if main_key:
                modifier_order = ['ctrl', 'alt', 'shift', 'win']
                sorted_modifiers = [mod for mod in modifier_order if mod in modifiers]
                
                if sorted_modifiers:
                    hotkey = '+'.join(sorted_modifiers) + '+' + main_key
                else:
                    hotkey = main_key
                
                self.status_label.setText(f"Captured: {hotkey}")
                self.hotkey_captured.emit(hotkey)
            else:
                self.status_label.setText("No valid key detected. Try again.")
        else:
            self.status_label.setText("No keys detected. Try again.")
    
    def keyPressEvent(self, event):
        """Handle key press during capture"""
        if not self.capturing:
            super().keyPressEvent(event)
            return
        
        key = event.key()
        
        if key == Qt.Key_Escape:
            self.stop_capture()
            self.status_label.setText("Capture cancelled.")
            return

        self.pressed_keys.add(key)

        current_combo = self.build_current_combo()
        if current_combo:
            self.status_label.setText(f"Current: {current_combo}")
        
        event.accept()
    
    def keyReleaseEvent(self, event):
        """Handle key release during capture"""
        if not self.capturing:
            super().keyReleaseEvent(event)
            return

        QTimer.singleShot(100, self.stop_capture)
        event.accept()
    
    def build_current_combo(self):
        """Build current combination string for display"""
        modifiers = []
        main_key = None
        
        for key in self.pressed_keys:
            if key in self.modifier_names:
                modifiers.append(self.modifier_names[key])
            elif key in self.key_names:
                main_key = self.key_names[key]
        
        if main_key:
            modifier_order = ['ctrl', 'alt', 'shift', 'win']
            sorted_modifiers = [mod for mod in modifier_order if mod in modifiers]
            
            if sorted_modifiers:
                return '+'.join(sorted_modifiers) + '+' + main_key
            else:
                return main_key
        elif modifiers:
            return '+'.join(modifiers) + '+...'
        
        return ""

class GlobalHotkeyThread(QThread):
    """Thread to handle global hotkey detection"""
    hotkey_pressed = pyqtSignal()
    
    def __init__(self, key_combination="ctrl+`"):
        super().__init__()
        self.key_combination = key_combination
        self.running = False
        self.hotkey_id = 1
        self.thread_id = None
        self.modifiers = 0
        self.key_code = 0
        self.parse_key_combination(key_combination)
    
    def parse_key_combination(self, key_combo):
        """Parse key combination string into Windows key codes"""
        MOD_ALT = 0x0001
        MOD_CONTROL = 0x0002
        MOD_SHIFT = 0x0004
        MOD_WIN = 0x0008

        VK_CODES = {
            'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46,
            'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C,
            'm': 0x4D, 'n': 0x4E, 'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52,
            's': 0x53, 't': 0x54, 'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58,
            'y': 0x59, 'z': 0x5A,
            
            '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
            '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
            
            'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74,
            'f6': 0x75, 'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79,
            'f11': 0x7A, 'f12': 0x7B,

            'space': 0x20, 'enter': 0x0D, 'return': 0x0D, 'esc': 0x1B, 'escape': 0x1B,
            'tab': 0x09, 'backspace': 0x08, 'delete': 0x2E, 'del': 0x2E,
            'insert': 0x2D, 'ins': 0x2D, 'home': 0x24, 'end': 0x23,
            'pageup': 0x21, 'pagedown': 0x22, 'pgup': 0x21, 'pgdn': 0x22,

            'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
            'arrowup': 0x26, 'arrowdown': 0x28, 'arrowleft': 0x25, 'arrowright': 0x27,

            'numpad0': 0x60, 'numpad1': 0x61, 'numpad2': 0x62, 'numpad3': 0x63,
            'numpad4': 0x64, 'numpad5': 0x65, 'numpad6': 0x66, 'numpad7': 0x67,
            'numpad8': 0x68, 'numpad9': 0x69, 'multiply': 0x6A, 'add': 0x6B,
            'subtract': 0x6D, 'decimal': 0x6E, 'divide': 0x6F,

            'pause': 0x13, 'capslock': 0x14, 'caps': 0x14, 'numlock': 0x90,
            'scrolllock': 0x91, 'scroll': 0x91, 'printscreen': 0x2C, 'print': 0x2C,

            'semicolon': 0xBA, ';': 0xBA, 'equals': 0xBB, '=': 0xBB,
            'comma': 0xBC, ',': 0xBC, 'minus': 0xBD, '-': 0xBD,
            'period': 0xBE, '.': 0xBE, 'slash': 0xBF, '/': 0xBF,
            'grave': 0xC0, '`': 0xC0, 'backslash': 0xDC, '\\': 0xDC,
            'quote': 0xDE, "'": 0xDE
        }
        
        parts = key_combo.lower().split('+')

        self.modifiers = 0
        self.key_code = 0
        
        for part in parts:
            part = part.strip()
            if part in ['ctrl', 'control']:
                self.modifiers |= MOD_CONTROL
            elif part == 'shift':
                self.modifiers |= MOD_SHIFT
            elif part == 'alt':
                self.modifiers |= MOD_ALT
            elif part in ['win', 'windows', 'cmd']:
                self.modifiers |= MOD_WIN
            elif part in VK_CODES:
                self.key_code = VK_CODES[part]
            else:
                print(f"Warning: Unknown key '{part}' in hotkey combination '{key_combo}'")
    
    def run(self):
        """Run the hotkey detection loop"""
        if not sys.platform.startswith('win'):
            print("Global hotkeys are only supported on Windows")
            return
            
        if self.key_code == 0:
            print(f"Invalid hotkey combination: {self.key_combination}")
            return
            
        self.running = True
        
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        self.thread_id = kernel32.GetCurrentThreadId()
        
        success = user32.RegisterHotKey(None, self.hotkey_id, self.modifiers, self.key_code)
        if not success:
            error_code = kernel32.GetLastError()
            if error_code == 1409:
                print(f"Hotkey {self.key_combination} is already registered by another application")
            else:
                print(f"Failed to register hotkey {self.key_combination}. Error code: {error_code}")
            return
        
        print(f"Successfully registered global hotkey: {self.key_combination}")
        
        try:
            msg = wintypes.MSG()
            while self.running:
                bRet = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if bRet == 0 or bRet == -1:
                    break
                
                if msg.message == 0x0312:
                    if msg.wParam == self.hotkey_id:
                        self.hotkey_pressed.emit()
                
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
                
        finally:
            user32.UnregisterHotKey(None, self.hotkey_id)
            print(f"Unregistered hotkey: {self.key_combination}")
    
    def stop(self):
        """Stop the hotkey detection"""
        self.running = False
        if sys.platform.startswith('win') and self.thread_id:
            user32 = ctypes.windll.user32
            user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0) 

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
                print("Stopping existing hotkey thread...")
                self.hotkey_thread.stop()
                self.hotkey_thread.wait(2000)
                if self.hotkey_thread.isRunning():
                    print("Force terminating hotkey thread...")
                    self.hotkey_thread.terminate()
                    self.hotkey_thread.wait(1000)
            
            print(f"Setting up hotkey: {self.hotkey_combination}")
            self.hotkey_thread = GlobalHotkeyThread(self.hotkey_combination)
            self.hotkey_thread.hotkey_pressed.connect(self.toggle_overlay_visibility)
            self.hotkey_thread.start()
            
            QTimer.singleShot(500, lambda: self.check_hotkey_status())
            
        except Exception as e:
            print(f"Failed to setup global hotkey: {e}")
            import traceback
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
            self.cycle_display_mode()
            return
        
        if self.is_visible:
            self.hide_overlay()
            self.show_hotkey_notification("Overlay Hidden", f"Press {self.hotkey_combination.upper()} to show")
        else:
            self.set_enabled(True)
            self.show_overlay()
            self.show_hotkey_notification("Overlay Shown", f"Press {self.hotkey_combination.upper()} to hide")
    
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
                json.dump(self.config, f, indent=4)
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
            }        }
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
    
    def create_minimal_ui(self):
        """Create minimal overlay showing kills and deaths with counts"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(2)
        header_layout.setContentsMargins(0, 0, 0, 0)

        header_layout.addStretch()
        
        mode_btn = QPushButton("○")
        mode_btn.setFixedSize(12, 12)
        mode_btn.clicked.connect(self.cycle_display_mode)
        mode_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {self.colors['border'].name()};
                border-radius: 6px;
                color: {self.colors['text_secondary'].name()};
                font-size: 8px;
            }}
            QPushButton:hover {{
                background: {self.colors['accent'].name()};
            }}
        """)
        header_layout.addWidget(mode_btn)
        
        layout.addLayout(header_layout)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)

        kills_section = QVBoxLayout()
        kills_section.setSpacing(0)
        
        kills_label = QLabel("KILLS")
        kills_label.setAlignment(Qt.AlignCenter)
        kills_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 10px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        self.kills_count = QLabel("0")
        self.kills_count.setAlignment(Qt.AlignCenter)
        self.kills_count.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['kill_color'].name()};
                font-size: 16px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        kills_section.addWidget(kills_label)
        kills_section.addWidget(self.kills_count)

        deaths_section = QVBoxLayout()
        deaths_section.setSpacing(0)
        
        deaths_label = QLabel("DEATHS")
        deaths_label.setAlignment(Qt.AlignCenter)
        deaths_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 10px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        self.deaths_count = QLabel("0")
        self.deaths_count.setAlignment(Qt.AlignCenter)
        self.deaths_count.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['death_color'].name()};
                font-size: 16px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        deaths_section.addWidget(deaths_label)
        deaths_section.addWidget(self.deaths_count)
        
        stats_layout.addLayout(kills_section)
        stats_layout.addLayout(deaths_section)
        
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
        self.setMinimumSize(120, 70)
        self.resize(120, 70)
    
    def create_compact_ui(self):
        """Create compact overlay with essential info in an improved layout"""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        title = QLabel("SCTool Killfeed")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['accent'].name()};
                font-size: 18px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        mode_btn = QPushButton("◐")
        mode_btn.setFixedSize(18, 18)
        mode_btn.clicked.connect(self.cycle_display_mode)
        mode_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {self.colors['border'].name()};
                border-radius: 9px;
                color: {self.colors['text_secondary'].name()};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {self.colors['accent'].name()};
            }}
        """)
        header_layout.addWidget(mode_btn)
        
        layout.addLayout(header_layout)

        stats_container = QHBoxLayout()
        stats_container.setSpacing(15)

        kills_section = QVBoxLayout()
        kills_section.setSpacing(2)
        
        kills_label = QLabel("KILLS")
        kills_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 11px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        kills_label.setAlignment(Qt.AlignCenter)
        
        self.kills_value_c = QLabel("0")
        self.kills_value_c.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['kill_color'].name()};
                font-size: 24px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.kills_value_c.setAlignment(Qt.AlignCenter)
        
        kills_section.addWidget(kills_label)
        kills_section.addWidget(self.kills_value_c)

        deaths_section = QVBoxLayout()
        deaths_section.setSpacing(2)
        
        deaths_label = QLabel("DEATHS")
        deaths_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 11px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        deaths_label.setAlignment(Qt.AlignCenter)
        
        self.deaths_value_c = QLabel("0")
        self.deaths_value_c.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['death_color'].name()};
                font-size: 24px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.deaths_value_c.setAlignment(Qt.AlignCenter)
        
        deaths_section.addWidget(deaths_label)
        deaths_section.addWidget(self.deaths_value_c)

        kd_section = QVBoxLayout()
        kd_section.setSpacing(2)
        
        kd_label = QLabel("K/D")
        kd_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 11px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        kd_label.setAlignment(Qt.AlignCenter)
        
        self.kd_value_c = QLabel("--")
        self.kd_value_c.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['info_color'].name()};
                font-size: 24px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.kd_value_c.setAlignment(Qt.AlignCenter)
        
        kd_section.addWidget(kd_label)
        kd_section.addWidget(self.kd_value_c)
        
        stats_container.addLayout(kills_section)
        stats_container.addLayout(deaths_section)
        stats_container.addLayout(kd_section)
        
        layout.addLayout(stats_container)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"color: {self.colors['border'].name()};")
        layout.addWidget(separator)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.session_label_c = QLabel("Session: 00:00")
        self.session_label_c.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['info_color'].name()};
                font-size: 16px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.session_label_c.setAlignment(Qt.AlignLeft)

        self.game_mode_label_c = QLabel("Mode: Unknown")
        self.game_mode_label_c.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.game_mode_label_c.setAlignment(Qt.AlignLeft)
        self.game_mode_label_c.setWordWrap(True)

        self.ship_label_c = QLabel("Ship: Unknown")
        self.ship_label_c.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.ship_label_c.setAlignment(Qt.AlignLeft)
        self.ship_label_c.setWordWrap(True)
        
        info_layout.addWidget(self.session_label_c)
        info_layout.addWidget(self.game_mode_label_c)
        info_layout.addWidget(self.ship_label_c)
        
        layout.addLayout(info_layout)
        
        self.setLayout(layout)
        self.setMinimumSize(320, 200)
        self.resize(350, 220)

    def create_detailed_ui(self):
        """Create detailed overlay with full information"""
        container_widget = QWidget()
        container_widget.setStyleSheet("background: transparent; border: none;")
        
        layout = QVBoxLayout(container_widget)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        title = QLabel("SCTool Killfeed Overlay")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['accent'].name()};
                font-size: 25px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        mode_btn = QPushButton("◑")
        mode_btn.setFixedSize(20, 20)
        mode_btn.clicked.connect(self.cycle_display_mode)
        mode_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {self.colors['border'].name()};
                border-radius: 10px;
                color: {self.colors['text_secondary'].name()};
                font-size: 25px;
            }}
            QPushButton:hover {{
                background: {self.colors['accent'].name()};
            }}
        """)
        header_layout.addWidget(mode_btn)
        
        layout.addLayout(header_layout)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(5)

        kills_label = QLabel("KILLS")
        kills_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        self.kills_value = QLabel("0")
        self.kills_value.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['kill_color'].name()};
                font-size: 26px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.kills_value.setAlignment(Qt.AlignCenter)
        
        deaths_label = QLabel("DEATHS")
        deaths_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        self.deaths_value = QLabel("0")
        self.deaths_value.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['death_color'].name()};
                font-size: 26px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.deaths_value.setAlignment(Qt.AlignCenter)
        
        kd_label = QLabel("K/D RATIO")
        kd_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        self.kd_value = QLabel("--")
        self.kd_value.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['info_color'].name()};
                font-size: 26px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.kd_value.setAlignment(Qt.AlignCenter)
        
        stats_grid.addWidget(kills_label, 0, 0)
        stats_grid.addWidget(self.kills_value, 1, 0)
        stats_grid.addWidget(deaths_label, 0, 1)
        stats_grid.addWidget(self.deaths_value, 1, 1)
        stats_grid.addWidget(kd_label, 0, 2)
        stats_grid.addWidget(self.kd_value, 1, 2)
        
        layout.addLayout(stats_grid)

        session_info_layout = QVBoxLayout()
        session_info_layout.setSpacing(4)

        self.session_time_label = QLabel("Session: 00:00")
        self.session_time_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['info_color'].name()};
                font-size: 21px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.session_time_label.setAlignment(Qt.AlignLeft)

        self.game_mode_label = QLabel("Mode: Unknown")
        self.game_mode_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 18px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.game_mode_label.setAlignment(Qt.AlignLeft)
        self.game_mode_label.setWordWrap(True)

        self.ship_label = QLabel("Ship: Unknown")
        self.ship_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 18px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.ship_label.setAlignment(Qt.AlignLeft)
        self.ship_label.setWordWrap(True)
        
        session_info_layout.addWidget(self.session_time_label)
        session_info_layout.addWidget(self.game_mode_label)
        session_info_layout.addWidget(self.ship_label)
        layout.addLayout(session_info_layout)
        
        if self.config.get('show_latest_kill', True):
            self.latest_kill_frame = QFrame()
            self.latest_kill_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(0, 40, 0, 100);
                    border: 1px solid {self.colors['kill_color'].name()};
                    border-radius: 4px;
                    margin: 2px;
                }}
            """)
            latest_kill_layout = QVBoxLayout(self.latest_kill_frame)
            latest_kill_layout.setContentsMargins(6, 4, 6, 4)
            latest_kill_layout.setSpacing(2)
            
            latest_title = QLabel("LATEST KILL")
            latest_title.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['kill_color'].name()};
                    font-size: 19px;
                    font-weight: bold;
                    background: transparent;
                }}
            """)
            latest_title.setAlignment(Qt.AlignCenter)
            
            self.latest_kill_info = QLabel("No kills yet")
            self.latest_kill_info.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['text_primary'].name()};
                    font-size: 20px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }}
            """)
            self.latest_kill_info.setAlignment(Qt.AlignCenter)
            self.latest_kill_info.setWordWrap(True)
            
            latest_kill_layout.addWidget(latest_title)
            latest_kill_layout.addWidget(self.latest_kill_info)
            layout.addWidget(self.latest_kill_frame)

        if self.config.get('show_latest_death', True):
            self.latest_death_frame = QFrame()
            self.latest_death_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(40, 0, 0, 100);
                    border: 1px solid {self.colors['death_color'].name()};
                    border-radius: 4px;
                    margin: 2px;
                }}
            """)
            latest_death_layout = QVBoxLayout(self.latest_death_frame)
            latest_death_layout.setContentsMargins(6, 4, 6, 4)
            latest_death_layout.setSpacing(2)
            
            death_title = QLabel("LATEST DEATH")
            death_title.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['death_color'].name()};
                    font-size: 19px;
                    font-weight: bold;
                    background: transparent;
                }}
            """)
            death_title.setAlignment(Qt.AlignCenter)
            
            self.latest_death_info = QLabel("No deaths yet")
            self.latest_death_info.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['text_primary'].name()};
                    font-size: 20px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }}
            """)
            self.latest_death_info.setAlignment(Qt.AlignCenter)
            self.latest_death_info.setWordWrap(True)
            
            latest_death_layout.addWidget(death_title)
            latest_death_layout.addWidget(self.latest_death_info)
            layout.addWidget(self.latest_death_frame)

        scroll_area = QScrollArea()
        scroll_area.setWidget(container_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {self.colors['background'].name()};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.colors['accent'].name()};
                border-radius: 4px;
                min-height: 15px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.colors['text_primary'].name()};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
        self.setMinimumSize(400, 450)
        self.resize(700, 800)

        container_widget.adjustSize()
    
    def create_horizontal_ui(self):
        """Create horizontal overlay with full information arranged horizontally"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 6, 12, 6)
        main_layout.setSpacing(8)

        title_layout = QHBoxLayout()
        title_layout.setSpacing(5)
        
        title = QLabel("SCTool Killfeed")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['accent'].name()};
                font-size: 16px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        mode_btn = QPushButton("◩")
        mode_btn.setFixedSize(16, 16)
        mode_btn.clicked.connect(self.cycle_display_mode)
        mode_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {self.colors['border'].name()};
                border-radius: 8px;
                color: {self.colors['text_secondary'].name()};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {self.colors['accent'].name()};
            }}
        """)
        title_layout.addWidget(mode_btn)
        
        main_layout.addLayout(title_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        stats_section = QHBoxLayout()
        stats_section.setSpacing(15)
        
        kills_container = QVBoxLayout()
        kills_container.setSpacing(0)
        kills_label = QLabel("KILLS")
        kills_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        kills_label.setAlignment(Qt.AlignCenter)
        self.kills_value_h = QLabel("0")
        self.kills_value_h.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['kill_color'].name()};
                font-size: 20px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.kills_value_h.setAlignment(Qt.AlignCenter)
        kills_container.addWidget(kills_label)
        kills_container.addWidget(self.kills_value_h)

        deaths_container = QVBoxLayout()
        deaths_container.setSpacing(0)
        deaths_label = QLabel("DEATHS")
        deaths_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        deaths_label.setAlignment(Qt.AlignCenter)
        self.deaths_value_h = QLabel("0")
        self.deaths_value_h.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['death_color'].name()};
                font-size: 20px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.deaths_value_h.setAlignment(Qt.AlignCenter)
        deaths_container.addWidget(deaths_label)
        deaths_container.addWidget(self.deaths_value_h)

        kd_container = QVBoxLayout()
        kd_container.setSpacing(0)
        kd_label = QLabel("K/D")
        kd_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        kd_label.setAlignment(Qt.AlignCenter)
        self.kd_value_h = QLabel("--")
        self.kd_value_h.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['info_color'].name()};
                font-size: 20px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.kd_value_h.setAlignment(Qt.AlignCenter)
        kd_container.addWidget(kd_label)
        kd_container.addWidget(self.kd_value_h)
        
        stats_section.addLayout(kills_container)
        stats_section.addLayout(deaths_container)
        stats_section.addLayout(kd_container)
        
        content_layout.addLayout(stats_section)

        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setStyleSheet(f"color: {self.colors['border'].name()};")
        content_layout.addWidget(separator1)

        session_info_section = QVBoxLayout()
        session_info_section.setSpacing(2)
        
        self.session_time_label_h = QLabel("Session: 00:00")
        self.session_time_label_h.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['info_color'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        self.game_mode_label_h = QLabel("Mode: Unknown")
        self.game_mode_label_h.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.game_mode_label_h.setWordWrap(True)
        
        self.ship_label_h = QLabel("Ship: Unknown")
        self.ship_label_h.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.ship_label_h.setWordWrap(True)
        
        session_info_section.addWidget(self.session_time_label_h)
        session_info_section.addWidget(self.game_mode_label_h)
        session_info_section.addWidget(self.ship_label_h)
        
        content_layout.addLayout(session_info_section)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet(f"color: {self.colors['border'].name()};")
        content_layout.addWidget(separator2)

        right_section = QHBoxLayout()
        right_section.setSpacing(20)
        
        if self.config.get('show_latest_kill', True):
            kill_info = QVBoxLayout()
            kill_info.setSpacing(2)
            kill_title = QLabel("LATEST KILL")
            kill_title.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['kill_color'].name()};
                    font-size: 10px;
                    font-weight: bold;
                    background: transparent;
                }}
            """)
            kill_title.setAlignment(Qt.AlignCenter)
            self.latest_kill_info_h = QLabel("No kills yet")
            self.latest_kill_info_h.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['text_primary'].name()};
                    font-size: 12px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }}
            """)
            self.latest_kill_info_h.setAlignment(Qt.AlignCenter)
            kill_info.addWidget(kill_title)
            kill_info.addWidget(self.latest_kill_info_h)
            right_section.addLayout(kill_info)
        
        if self.config.get('show_latest_death', True):
            death_info = QVBoxLayout()
            death_info.setSpacing(2)
            death_title = QLabel("LATEST DEATH")
            death_title.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['death_color'].name()};
                    font-size: 10px;
                    font-weight: bold;
                    background: transparent;
                }}
            """)
            death_title.setAlignment(Qt.AlignCenter)
            self.latest_death_info_h = QLabel("No deaths yet")
            self.latest_death_info_h.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['text_primary'].name()};
                    font-size: 12px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }}
            """)
            self.latest_death_info_h.setAlignment(Qt.AlignCenter)
            death_info.addWidget(death_title)
            death_info.addWidget(self.latest_death_info_h)
            right_section.addLayout(death_info)
        
        content_layout.addLayout(right_section)
        main_layout.addLayout(content_layout)
        
        self.setLayout(main_layout)
        self.setMinimumSize(800, 120)
        self.resize(1200, 120)

    def create_faded_ui(self):
        """Create faded notification overlay - only shows during kill/death events"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.faded_container = QWidget()
        self.faded_container.setStyleSheet("background: transparent;")
        self.faded_container.hide()
        
        layout.addWidget(self.faded_container)
        
        self.setLayout(layout)
        self.setMinimumSize(50, 50)
        self.resize(50, 50)

        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self.fade_notification)

        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.finished.connect(self.hide_faded_notification)

    def show_death_notification(self, attacker: str, weapon: str, zone: str, game_mode: str = "Unknown"):
        """Show death notification in faded mode with org info and profile image"""
        if self.display_mode != 'faded':
            return
        
        self.clear_faded_container()
        
        try:
            from fetch import fetch_player_details, fetch_victim_image_base64
            from kill_parser import KillParser
            
            details = fetch_player_details(attacker)
            attacker_image_data_uri = fetch_victim_image_base64(attacker)
            formatted_zone = KillParser.format_zone(zone)
            formatted_weapon = KillParser.format_weapon(weapon)
            
            if formatted_weapon != 'Unknown':
                weapon_clean = formatted_weapon
            else:
                weapon_clean = self.clean_weapon_name(weapon)
                
        except ImportError:
            details = {'org_name': 'Unknown', 'org_tag': 'Unknown'}
            attacker_image_data_uri = ""
            formatted_zone = zone.replace('_', ' ').title()
            weapon_clean = self.clean_weapon_name(weapon)

        notification_widget = QWidget()
        notification_layout = QHBoxLayout(notification_widget)
        notification_layout.setContentsMargins(20, 15, 20, 15)
        notification_layout.setSpacing(20)

        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setSpacing(12)

        header = QLabel("YOU DIED")
        header.setAlignment(Qt.AlignLeft)
        header.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['death_color'].name()};
                font-size: 28px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
                text-shadow: 0 0 10px {self.colors['death_color'].name()};
            }}
        """)
        text_layout.addWidget(header)

        attacker_label = QLabel(f"KILLED BY: {attacker.upper()}")
        attacker_label.setAlignment(Qt.AlignLeft)
        attacker_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 20px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        text_layout.addWidget(attacker_label)

        org_name = details.get('org_name', 'None')
        org_tag = details.get('org_tag', 'None')
        
        org_info = QVBoxLayout()
        org_info.setSpacing(4)
        
        if org_name != 'None' and org_name != 'Unknown':
            org_label = QLabel(f"Organization: {org_name}")
            org_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['text_secondary'].name()};
                    font-size: 16px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }}
            """)
            org_info.addWidget(org_label)
            
            if org_tag != 'None' and org_tag != 'Unknown':
                tag_label = QLabel(f"Tag: [{org_tag}]")
                tag_label.setStyleSheet(f"""
                    QLabel {{
                        color: {self.colors['accent'].name()};
                        font-size: 14px;
                        font-family: 'Consolas', monospace;
                        background: transparent;
                    }}
                """)
                org_info.addWidget(tag_label)
        else:
            org_label = QLabel("Organization: Independent")
            org_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['text_secondary'].name()};
                    font-size: 16px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }}
            """)
            org_info.addWidget(org_label)
        
        text_layout.addLayout(org_info)

        details_layout = QVBoxLayout()
        details_layout.setSpacing(6)
        
        weapon_label = QLabel(f"Weapon: {weapon_clean}")
        weapon_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 16px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        location_label = QLabel(f"Location: {formatted_zone}")
        location_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 16px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        mode_label = QLabel(f"Mode: {game_mode}")
        mode_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['info_color'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        details_layout.addWidget(weapon_label)
        details_layout.addWidget(location_label)
        details_layout.addWidget(mode_label)
        text_layout.addLayout(details_layout)
        
        notification_layout.addWidget(text_container, 2)
        
        if attacker_image_data_uri:
            image_container = QWidget()
            image_container.setFixedSize(120, 120)
            
            image_label = QLabel()
            try:
                if attacker_image_data_uri.startswith('data:image'):
                    from PyQt5.QtGui import QPixmap
                    import base64
                    
                    header, data = attacker_image_data_uri.split(',', 1)
                    image_data = base64.b64decode(data)
                    
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)

                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

                        circular_pixmap = QPixmap(120, 120)
                        circular_pixmap.fill(Qt.transparent)
                        
                        painter = QPainter(circular_pixmap)
                        painter.setRenderHint(QPainter.Antialiasing)
                        painter.setBrush(QBrush(scaled_pixmap))
                        painter.setPen(Qt.NoPen)
                        painter.drawEllipse(0, 0, 120, 120)

                        painter.setPen(QPen(QColor(self.colors['death_color']), 3))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawEllipse(1, 1, 118, 118)
                        painter.end()
                        
                        image_label.setPixmap(circular_pixmap)
                        
            except Exception as e:
                image_label.setText("No Image")
                image_label.setAlignment(Qt.AlignCenter)
                image_label.setStyleSheet(f"""
                    QLabel {{
                        color: {self.colors['text_secondary'].name()};
                        font-size: 12px;
                        background-color: {self.colors['background'].name()};
                        border: 2px solid {self.colors['death_color'].name()};
                        border-radius: 60px;
                    }}
                """)
            
            image_label.setFixedSize(120, 120)
            
            image_layout = QVBoxLayout(image_container)
            image_layout.setContentsMargins(0, 0, 0, 0)
            image_layout.addWidget(image_label)
            
            notification_layout.addWidget(image_container, 0)
        
        self.faded_container.setLayout(QVBoxLayout())
        self.faded_container.layout().setContentsMargins(0, 0, 0, 0)
        self.faded_container.layout().addWidget(notification_widget)

        self.show_faded_notification()

    def show_kill_notification(self, victim: str, weapon: str, zone: str, game_mode: str = "Unknown"):
        """Show kill notification in faded mode with org info and profile image"""
        if self.display_mode != 'faded':
            return
        
        self.clear_faded_container()

        try:
            from fetch import fetch_player_details, fetch_victim_image_base64
            from kill_parser import KillParser
            import re
            
            details = fetch_player_details(victim)
            victim_image_data_uri = fetch_victim_image_base64(victim)
            formatted_zone = KillParser.format_zone(zone)
            formatted_weapon = KillParser.format_weapon(weapon)
            
            weapon_clean = re.sub(r'_\d+$', '', weapon)
            weapon_clean = weapon_clean.replace("_", " ")
            weapon_clean = re.sub(r'\s+\d+$', '', weapon_clean)
            if formatted_weapon != 'Unknown':
                weapon_clean = formatted_weapon
                
        except ImportError:
            details = {'org_name': 'Unknown', 'org_tag': 'Unknown'}
            victim_image_data_uri = ""
            formatted_zone = zone.replace('_', ' ').title()
            weapon_clean = self.clean_weapon_name(weapon)
        
        notification_widget = QWidget()
        notification_layout = QHBoxLayout(notification_widget)
        notification_layout.setContentsMargins(20, 15, 20, 15)
        notification_layout.setSpacing(20)
        
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setSpacing(12)
        
        header = QLabel("YOU KILLED")
        header.setAlignment(Qt.AlignLeft)
        header.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['kill_color'].name()};
                font-size: 28px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
                text-shadow: 0 0 10px {self.colors['kill_color'].name()};
            }}
        """)
        text_layout.addWidget(header)
        
        victim_label = QLabel(victim.upper())
        victim_label.setAlignment(Qt.AlignLeft)
        victim_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['death_color'].name()};
                font-size: 24px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
                text-shadow: 0 0 8px {self.colors['death_color'].name()};
            }}
        """)
        text_layout.addWidget(victim_label)
        
        org_name = details.get('org_name', 'None')
        org_tag = details.get('org_tag', 'None')
        
        org_info = QVBoxLayout()
        org_info.setSpacing(4)
        
        if org_name != 'None' and org_name != 'Unknown':
            org_label = QLabel(f"Organization: {org_name}")
            org_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['text_secondary'].name()};
                    font-size: 16px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }}
            """)
            org_info.addWidget(org_label)
            
            if org_tag != 'None' and org_tag != 'Unknown':
                tag_label = QLabel(f"Tag: [{org_tag}]")
                tag_label.setStyleSheet(f"""
                    QLabel {{
                        color: {self.colors['accent'].name()};
                        font-size: 14px;
                        font-family: 'Consolas', monospace;
                        background: transparent;
                    }}
                """)
                org_info.addWidget(tag_label)
        else:
            org_label = QLabel("Organization: Independent")
            org_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['text_secondary'].name()};
                    font-size: 16px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }}
            """)
            org_info.addWidget(org_label)
        
        text_layout.addLayout(org_info)
        
        details_layout = QVBoxLayout()
        details_layout.setSpacing(6)
        
        weapon_label = QLabel(f"Weapon: {weapon_clean}")
        weapon_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 16px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        location_label = QLabel(f"Location: {formatted_zone}")
        location_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 16px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        mode_label = QLabel(f"Mode: {game_mode}")
        mode_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['info_color'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        details_layout.addWidget(weapon_label)
        details_layout.addWidget(location_label)
        details_layout.addWidget(mode_label)
        text_layout.addLayout(details_layout)
        
        notification_layout.addWidget(text_container, 2)

        if victim_image_data_uri:
            image_container = QWidget()
            image_container.setFixedSize(120, 120)
            
            image_label = QLabel()
            try:
                if victim_image_data_uri.startswith('data:image'):
                    from PyQt5.QtGui import QPixmap
                    
                    header, data = victim_image_data_uri.split(',', 1)
                    image_data = base64.b64decode(data)
                    
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)

                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                        
                        circular_pixmap = QPixmap(120, 120)
                        circular_pixmap.fill(Qt.transparent)
                        
                        painter = QPainter(circular_pixmap)
                        painter.setRenderHint(QPainter.Antialiasing)
                        painter.setBrush(QBrush(scaled_pixmap))
                        painter.setPen(Qt.NoPen)
                        painter.drawEllipse(0, 0, 120, 120)
                        
                        painter.setPen(QPen(QColor(self.colors['death_color']), 3))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawEllipse(1, 1, 118, 118)
                        painter.end()
                        
                        image_label.setPixmap(circular_pixmap)
                        
            except Exception as e:
                image_label.setText("No Image")
                image_label.setAlignment(Qt.AlignCenter)
                image_label.setStyleSheet(f"""
                    QLabel {{
                        color: {self.colors['text_secondary'].name()};
                        font-size: 12px;
                        background-color: {self.colors['background'].name()};
                        border: 2px solid {self.colors['death_color'].name()};
                        border-radius: 60px;
                    }}
                """)
            
            image_label.setFixedSize(120, 120)
            
            image_layout = QVBoxLayout(image_container)
            image_layout.setContentsMargins(0, 0, 0, 0)
            image_layout.addWidget(image_label)
            
            notification_layout.addWidget(image_container, 0)

        self.faded_container.setLayout(QVBoxLayout())
        self.faded_container.layout().setContentsMargins(0, 0, 0, 0)
        self.faded_container.layout().addWidget(notification_widget)
        
        self.show_faded_notification()

    def clear_faded_container(self):
        """Clear the faded container content"""
        if hasattr(self, 'faded_container') and self.faded_container.layout():
            while self.faded_container.layout().count():
                child = self.faded_container.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

    def show_faded_notification(self):
        """Show the faded notification and start timers"""
        if not hasattr(self, 'faded_container'):
            return

        if hasattr(self, 'fade_timer'):
            self.fade_timer.stop()
        if hasattr(self, 'fade_animation'):
            self.fade_animation.stop()

        self.faded_container.adjustSize()
        self.adjustSize()

        min_width = max(self.faded_container.sizeHint().width() + 20, 300)
        min_height = max(self.faded_container.sizeHint().height() + 20, 150)
        self.resize(min_width, min_height)

        self.faded_container.show()
        self.setWindowOpacity(self.opacity_level)
        self.show()

        self.fade_timer.start(8000)

    def fade_notification(self):
        """Start the fade out animation"""
        if hasattr(self, 'fade_timer'):
            self.fade_timer.stop()

        self.fade_animation.setDuration(2000)
        self.fade_animation.setStartValue(self.opacity_level)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutQuad)
        self.fade_animation.start()

    def hide_faded_notification(self):
        """Hide the faded notification after fade completes"""
        if hasattr(self, 'faded_container'):
            self.faded_container.hide()
        self.hide()
        self.setWindowOpacity(self.opacity_level)

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
            if self.show_animations and self.animation_timer.isActive():
                pulse_intensity = 0.5 + 0.5 * abs(self.pulse_alpha)
                alpha = int(border_color.alpha() * pulse_intensity)
                border_color.setAlpha(alpha)
                
                border_width = int(2 + 2 * abs(self.pulse_alpha))
            else:
                border_width = 2
            
            painter.setPen(QPen(border_color, border_width))
            painter.drawRoundedRect(rect, 8, 8)

            if hasattr(self, 'kill_glow_alpha') and self.kill_glow_alpha > 0:
                glow_color = QColor(self.colors['kill_color'])
                glow_color.setAlpha(int(255 * self.kill_glow_alpha * 0.3))
                painter.setPen(QPen(glow_color, 4))
                painter.drawRoundedRect(rect.adjusted(-2, -2, 2, 2), 10, 10)

            if hasattr(self, 'death_glow_alpha') and self.death_glow_alpha > 0:
                glow_color = QColor(self.colors['death_color'])
                glow_color.setAlpha(int(255 * self.death_glow_alpha * 0.3))
                painter.setPen(QPen(glow_color, 4))
                painter.drawRoundedRect(rect.adjusted(-2, -2, 2, 2), 10, 10)

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
        """Show a brief indicator of mode change"""
        if hasattr(self, 'mode_indicator') and self.mode_indicator is not None:
            try:
                self.mode_indicator.deleteLater()
            except RuntimeError:
                pass
        
        self.mode_indicator = QLabel(f"Mode: {self.display_mode.title()}")
        self.mode_indicator.setParent(self)
        self.mode_indicator.setStyleSheet(f"""
            QLabel {{
                background: {self.colors['accent'].name()};
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        self.mode_indicator.adjustSize()
        self.mode_indicator.move(10, 10)
        self.mode_indicator.show()
        QTimer.singleShot(2000, self._safe_delete_mode_indicator)
    
    def _safe_delete_mode_indicator(self):
        """Safely delete mode indicator if it still exists"""
        if hasattr(self, 'mode_indicator') and self.mode_indicator is not None:
            try:
                self.mode_indicator.deleteLater()
                self.mode_indicator = None
            except RuntimeError:
                pass

    def show_faded_positioning_helper(self):
        """Show a temporary positioning helper for faded mode"""
        self.clear_faded_container()
        
        helper_widget = QWidget()
        helper_layout = QVBoxLayout(helper_widget)
        helper_layout.setContentsMargins(20, 15, 20, 15)
        helper_layout.setSpacing(10)
        
        title = QLabel("FADED MODE")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['accent'].name()};
                font-size: 18px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        subtitle = QLabel("Position Helper")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        instruction = QLabel("Drag to position\nWill hide in 30 seconds")
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 12px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        helper_layout.addWidget(title)
        helper_layout.addWidget(subtitle)
        helper_layout.addWidget(instruction)
        
        self.faded_container.setLayout(QVBoxLayout())
        self.faded_container.layout().setContentsMargins(0, 0, 0, 0)
        self.faded_container.layout().addWidget(helper_widget)

        self.faded_container.adjustSize()
        self.adjustSize()
        self.resize(200, 120)
        
        self.faded_container.show()
        self.show()

        QTimer.singleShot(30000, self.hide_positioning_helper)

    def hide_positioning_helper(self):
        """Hide the positioning helper and return to normal faded mode"""
        if hasattr(self, 'faded_container'):
            self.faded_container.hide()
        self.hide()
        self.resize(50, 50)

    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton and not self.is_locked:
            if self.display_mode == 'faded' and hasattr(self, 'faded_container') and self.faded_container.isVisible():
                QTimer.singleShot(8000, self.hide_positioning_helper)
            
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
                current_mode = mode_text[6:]
                if current_mode != self.game_mode:
                    self.game_mode = current_mode
                    self.update_game_mode_display()

    def update_session_time_display(self):
        """Update only session time labels without full UI refresh"""
        if self.display_mode == 'compact':
            if hasattr(self, 'session_label_c'):
                self.session_label_c.setText(f"Session: {self.session_time}")
                
        elif self.display_mode == 'detailed':
            if hasattr(self, 'session_time_label'):
                self.session_time_label.setText(f"Session: {self.session_time}")
                
        elif self.display_mode == 'horizontal':
            if hasattr(self, 'session_time_label_h'):
                self.session_time_label_h.setText(f"Session: {self.session_time}")

    def update_ship_display(self):
        """Update only ship labels without full UI refresh"""
        if self.display_mode == 'compact':
            if hasattr(self, 'ship_label_c'):
                self.ship_label_c.setText(f"Ship: {self.ship}")
                
        elif self.display_mode == 'detailed':
            if hasattr(self, 'ship_label'):
                self.ship_label.setText(f"Ship: {self.ship}")
                
        elif self.display_mode == 'horizontal':
            if hasattr(self, 'ship_label_h'):
                self.ship_label_h.setText(f"Ship: {self.ship}")

    def update_game_mode_display(self):
        """Update only game mode labels without full UI refresh"""
        if self.display_mode == 'compact':
            if hasattr(self, 'game_mode_label_c'):
                self.game_mode_label_c.setText(f"Mode: {self.game_mode}")
                
        elif self.display_mode == 'detailed':
            if hasattr(self, 'game_mode_label'):
                self.game_mode_label.setText(f"Mode: {self.game_mode}")
                
        elif self.display_mode == 'horizontal':
            if hasattr(self, 'game_mode_label_h'):
                self.game_mode_label_h.setText(f"Mode: {self.game_mode}")

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
    
    def clean_weapon_name(self, weapon_name: str) -> str:
        """Clean weapon name by removing long ID strings and replacing underscores with spaces"""
        
        weapon_name = re.sub(r'_\d+$', '', weapon_name)
        
        weapon_name = weapon_name.replace('_', ' ')

        weapon_name = re.sub(r'\s+\d+$', '', weapon_name)
        
        return weapon_name.strip()

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
                
        elif self.display_mode == 'compact':
            if hasattr(self, 'kills_value_c'):
                self.kills_value_c.setText(str(self.kills))
            if hasattr(self, 'deaths_value_c'):
                self.deaths_value_c.setText(str(self.deaths))
            if hasattr(self, 'kd_value_c'):
                self.kd_value_c.setText(kd_ratio)
            if hasattr(self, 'session_label_c'):
                self.session_label_c.setText(f"Session: {self.session_time}")
            if hasattr(self, 'game_mode_label_c'):
                self.game_mode_label_c.setText(f"Mode: {self.game_mode}")
            if hasattr(self, 'ship_label_c'):
                self.ship_label_c.setText(f"Ship: {self.ship}")
                
        elif self.display_mode == 'detailed':
            if hasattr(self, 'kills_value'):
                self.kills_value.setText(str(self.kills))
            if hasattr(self, 'deaths_value'):
                self.deaths_value.setText(str(self.deaths))
            if hasattr(self, 'kd_value'):
                self.kd_value.setText(kd_ratio)
            if hasattr(self, 'session_time_label'):
                self.session_time_label.setText(f"Session: {self.session_time}")
            if hasattr(self, 'game_mode_label'):
                self.game_mode_label.setText(f"Mode: {self.game_mode}")
            if hasattr(self, 'ship_label'):
                self.ship_label.setText(f"Ship: {self.ship}")
            
            if hasattr(self, 'latest_kill_frame') and hasattr(self, 'latest_kill_info'):
                if self.last_kill_info is not None:
                    victim = self.last_kill_info.get('victim', 'Unknown')
                    weapon = self.last_kill_info.get('weapon', 'Unknown')
                    clean_weapon = self.clean_weapon_name(weapon)
                    self.latest_kill_info.setText(f"{victim}\n{clean_weapon}")
                else:
                    self.latest_kill_info.setText("No kills yet")

            if hasattr(self, 'latest_death_frame') and hasattr(self, 'latest_death_info'):
                if self.last_death_info is not None:
                    attacker = self.last_death_info.get('attacker', 'Unknown')
                    weapon = self.last_death_info.get('weapon', 'Unknown')
                    clean_weapon = self.clean_weapon_name(weapon)
                    self.latest_death_info.setText(f"Killed by: {attacker}\n{clean_weapon}")
                else:
                    self.latest_death_info.setText("No deaths yet")

        elif self.display_mode == 'horizontal':
            if hasattr(self, 'kills_value_h'):
                self.kills_value_h.setText(str(self.kills))
            if hasattr(self, 'deaths_value_h'):
                self.deaths_value_h.setText(str(self.deaths))
            if hasattr(self, 'kd_value_h'):
                self.kd_value_h.setText(kd_ratio)
            if hasattr(self, 'session_time_label_h'):
                self.session_time_label_h.setText(f"Session: {self.session_time}")
            if hasattr(self, 'game_mode_label_h'):
                self.game_mode_label_h.setText(f"Mode: {self.game_mode}")
            if hasattr(self, 'ship_label_h'):
                self.ship_label_h.setText(f"Ship: {self.ship}")
            
            if hasattr(self, 'latest_kill_info_h'):
                if self.last_kill_info is not None:
                    victim = self.last_kill_info.get('victim', 'Unknown')
                    weapon = self.last_kill_info.get('weapon', 'Unknown')
                    clean_weapon = self.clean_weapon_name(weapon)
                    self.latest_kill_info_h.setText(f"{victim}\n{clean_weapon}")
                else:
                    self.latest_kill_info_h.setText("No kills yet")

            if hasattr(self, 'latest_death_info_h'):
                if self.last_death_info is not None:
                    attacker = self.last_death_info.get('attacker', 'Unknown')
                    weapon = self.last_death_info.get('weapon', 'Unknown')
                    clean_weapon = self.clean_weapon_name(weapon)
                    self.latest_death_info_h.setText(f"Killed by: {attacker}\n{clean_weapon}")
                else:
                    self.latest_death_info_h.setText("No deaths yet")

        self.adjust_size_to_content()
    
    def adjust_size_to_content(self):
        """Dynamically adjust overlay size based on content"""
        if self.display_mode == 'faded':
            return

        if self.display_mode == 'detailed':
            scroll_area = self.findChild(QScrollArea)
            if scroll_area and scroll_area.widget():
                container_widget = scroll_area.widget()
                container_widget.updateGeometry()
                container_widget.adjustSize()
                content_height = container_widget.sizeHint().height()

                padding = 30
                total_height = min(content_height + padding, 600)
                
                current_width = max(self.width(), 350)
                
                final_height = max(total_height, 200)
                final_height = min(final_height, 600)
                
                self.resize(current_width, final_height)
                    
                self.config['size'] = {'width': current_width, 'height': final_height}
                
        elif self.display_mode == 'compact':
            if hasattr(self, 'layout') and self.layout():
                self.layout().activate()
                self.adjustSize()
                
                min_width, min_height = 220, 120
                current_size = self.size()
                
                new_width = max(current_size.width(), min_width)
                new_height = max(current_size.height(), min_height)
                
                max_height = 180
                new_height = min(new_height, max_height)
                
                self.resize(new_width, new_height)
                self.config['size'] = {'width': new_width, 'height': new_height}
                
        elif self.display_mode == 'minimal':
            self.resize(80, 40)
            self.config['size'] = {'width': 80, 'height': 40}
        elif self.display_mode == 'horizontal':
            min_width = 800
            min_height = 80
            current_size = self.size()
            
            new_width = max(current_size.width(), min_width)
            new_height = min(current_size.height(), min_height)
            
            self.resize(new_width, min_height)
            self.config['size'] = {'width': new_width, 'height': min_height}
    
    def handle_content_update(self):
        """Handle content updates and ensure proper sizing"""
        if hasattr(self, 'layout') and self.layout():
            self.layout().update()

        QApplication.processEvents()
        self.adjust_size_to_content()
        self.update_display()

class OverlayControlPanel(QFrame):
    """Advanced control panel for overlay configuration"""
    
    overlay_toggled = pyqtSignal(bool)
    
    def __init__(self, overlay: GameOverlay, parent=None):
        super().__init__(parent)
        self.overlay = overlay
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the control panel UI"""
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 20, 20, 0.9);
                border-radius: 8px;
                border: 1px solid #333333;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)
        
        header = QLabel("GAME OVERLAY")
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
        content_layout.addWidget(header)
        
        desc = QLabel("Overlay system with multiple display modes, customizable themes, "
                     "and real-time statistics. The overlay shows your kill/death stats, session information, "
                     "and latest kill details while playing Star Citizen.")
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
        content_layout.addWidget(desc)
        basic_group = QGroupBox("Basic Controls")
        basic_group.setStyleSheet("QGroupBox { color: #f0f0f0; }")
        basic_layout = QVBoxLayout(basic_group)
        basic_layout.setSpacing(10)

        self.enable_checkbox = QCheckBox("Enable Game Overlay")
        self.enable_checkbox.setChecked(self.overlay.is_enabled)
        self.enable_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                spacing: 10px;
                background: transparent;
                border: none;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border: 2px solid #333333;
                border-radius: 3px;
                background-color: #1e1e1e;
            }            
            QCheckBox::indicator:checked {
                background-color: #00ff41;
                border-color: #00ff41;
            }
        """)
        self.enable_checkbox.toggled.connect(self.toggle_overlay)
        basic_layout.addWidget(self.enable_checkbox)
        
        self.lock_checkbox = QCheckBox("Lock Overlay Position")
        self.lock_checkbox.setChecked(self.overlay.is_locked)
        self.lock_checkbox.setStyleSheet(self.enable_checkbox.styleSheet())
        self.lock_checkbox.toggled.connect(self.overlay.set_locked)
        basic_layout.addWidget(self.lock_checkbox)
        
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Display Mode:")
        mode_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; }")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Minimal", "Compact", "Detailed", "Horizontal", "Faded"])
        self.mode_combo.setCurrentText(self.overlay.display_mode.title())
        self.mode_combo.currentTextChanged.connect(self.change_display_mode)
        self.mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e1e1e;
                color: #f0f0f0;
                padding: 8px;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                min-width: 100px;
            }
            QComboBox:hover { border-color: #00ff41; }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #f0f0f0;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e1e;
                color: #f0f0f0;
                selection-background-color: #00ff41;
            }
        """)
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        basic_layout.addLayout(mode_layout)
        
        content_layout.addWidget(basic_group)
        
        appearance_group = QGroupBox("Appearance")
        appearance_group.setStyleSheet("QGroupBox { color: #f0f0f0; }")
        appearance_layout = QVBoxLayout(appearance_group)
        appearance_layout.setSpacing(10)
        
        opacity_layout = QHBoxLayout()
        opacity_label = QLabel("Opacity:")
        opacity_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; }")
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(int(self.overlay.opacity_level * 100))
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #2a2a2a;
                height: 8px;
                background: #1a1a1a;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00ff41;
                border: 1px solid #2a2a2a;
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #00ff41;
                border-radius: 4px;
            }
        """)
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        
        self.opacity_label = QLabel(f"{int(self.overlay.opacity_level * 100)}%")
        self.opacity_label.setStyleSheet("QLabel { color: #ffffff; min-width: 40px; }")
        
        opacity_layout.addWidget(opacity_label)
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        appearance_layout.addLayout(opacity_layout)
        
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; }")
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Dark", "Neon"])
        self.theme_combo.setCurrentText(self.overlay.theme.title())
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        self.theme_combo.setStyleSheet(self.mode_combo.styleSheet())
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        appearance_layout.addLayout(theme_layout)
        
        self.animations_checkbox = QCheckBox("Enable Animations")
        self.animations_checkbox.setChecked(self.overlay.show_animations)
        self.animations_checkbox.setStyleSheet(self.enable_checkbox.styleSheet())
        self.animations_checkbox.toggled.connect(self.overlay.toggle_animations)
        appearance_layout.addWidget(self.animations_checkbox)
        
        content_layout.addWidget(appearance_group)

        position_group = QGroupBox("Position & Size")
        position_group.setStyleSheet("QGroupBox { color: #f0f0f0; }")
        position_layout = QVBoxLayout(position_group)
        position_layout.setSpacing(10)
        
        pos_buttons_layout = QHBoxLayout()
        
        pos_tl_btn = QPushButton("Top Left")
        pos_tl_btn.clicked.connect(lambda: self.set_position("top-left"))
        
        pos_tr_btn = QPushButton("Top Right")
        pos_tr_btn.clicked.connect(lambda: self.set_position("top-right"))
        
        pos_bl_btn = QPushButton("Bottom Left")
        pos_bl_btn.clicked.connect(lambda: self.set_position("bottom-left"))
        
        pos_br_btn = QPushButton("Bottom Right")
        pos_br_btn.clicked.connect(lambda: self.set_position("bottom-right"))
        
        pos_center_btn = QPushButton("Center")
        pos_center_btn.clicked.connect(lambda: self.set_position("center"))
        
        for btn in [pos_tl_btn, pos_tr_btn, pos_bl_btn, pos_br_btn, pos_center_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e1e1e;
                    color: #f0f0f0;
                    border: 1px solid #2a2a2a;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 15px;
                }
                QPushButton:hover {
                    border-color: #00ff41;
                    background-color: #2a2a2a;
                }
            """)
            pos_buttons_layout.addWidget(btn)
        
        position_layout.addLayout(pos_buttons_layout)
        
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self.reset_position)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e;
                color: #f0f0f0;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                border-color: #00ff41;
                background-color: #2a2a2a;
            }
        """)
        position_layout.addWidget(reset_btn)
        
        content_layout.addWidget(position_group)
        
        hotkey_group = QGroupBox("Global Hotkey")
        hotkey_group.setStyleSheet("QGroupBox { color: #f0f0f0; }")
        hotkey_layout = QVBoxLayout(hotkey_group)
        hotkey_layout.setSpacing(10)
        
        self.hotkey_checkbox = QCheckBox("Enable Global Hotkey")
        self.hotkey_checkbox.setChecked(self.overlay.hotkey_enabled)
        self.hotkey_checkbox.setStyleSheet(self.enable_checkbox.styleSheet())
        self.hotkey_checkbox.toggled.connect(self.overlay.set_hotkey_enabled)
        hotkey_layout.addWidget(self.hotkey_checkbox)
        
        current_hotkey_layout = QHBoxLayout()
        current_label = QLabel("Current Hotkey:")
        current_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; }")
        
        self.current_hotkey_display = QLabel(self.overlay.hotkey_combination)
        self.current_hotkey_display.setStyleSheet("""
            QLabel {
                color: #00ff41;
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background-color: #2a2a2a;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px;
                min-width: 100px;
            }
        """)
        
        current_hotkey_layout.addWidget(current_label)
        current_hotkey_layout.addWidget(self.current_hotkey_display)
        current_hotkey_layout.addStretch()
        hotkey_layout.addLayout(current_hotkey_layout)
        
        self.hotkey_capture = HotkeyCapture()
        self.hotkey_capture.hotkey_captured.connect(self.on_hotkey_captured)
        hotkey_layout.addWidget(self.hotkey_capture)
        
        hotkey_info = QLabel("Use the capture button to record a key combination. Examples: 'ctrl+`', 'alt+f1', 'ctrl+shift+h'")
        hotkey_info.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 12px;
                font-style: italic;
            }
        """)
        hotkey_info.setWordWrap(True)
        hotkey_layout.addWidget(hotkey_info)
        
        content_layout.addWidget(hotkey_group)

        instructions = QLabel("""
        <b>Instructions:</b><br>
        • Left-click and drag to move the overlay<br>
        • Ctrl + Mouse wheel to adjust opacity<br>
        • Click the mode button (◐/◑) on overlay to cycle modes<br>
        • Use global hotkey to toggle overlay visibility<br>
        • Overlay stays on top of all windows including games
        """)
        instructions.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 15px;
                background: rgba(30, 30, 30, 0.5);
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 10px;
                margin-top: 10px;
            }
        """)
        instructions.setWordWrap(True)
        content_layout.addWidget(instructions)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

        helper_btn = QPushButton("Show Faded Mode Helper")
        helper_btn.clicked.connect(self.show_faded_helper)
        helper_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e;
                color: #f0f0f0;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                border-color: #00ff41;
                background-color: #2a2a2a;
            }
        """)
        position_layout.addWidget(helper_btn)
        
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self.reset_position)
    
    def show_faded_helper(self):
        """Manually show the faded positioning helper"""
        if self.overlay.display_mode == 'faded':
            self.overlay.show_faded_positioning_helper()
        else:
            old_mode = self.overlay.display_mode
            self.overlay.display_mode = 'faded'
            self.overlay.create_ui()
            self.overlay.show_faded_positioning_helper()
            
            def restore_mode():
                self.overlay.display_mode = old_mode
                self.overlay.config['display_mode'] = old_mode
                self.overlay.create_ui()
                self.overlay.update_display()
                if self.overlay.is_enabled:
                    self.overlay.show_overlay()
            
            QTimer.singleShot(6000, restore_mode)

    def on_hotkey_captured(self, hotkey_string):
        """Handle captured hotkey"""
        print(f"Captured hotkey: {hotkey_string}")
        self.current_hotkey_display.setText(hotkey_string)
        self.overlay.set_hotkey_combination(hotkey_string)

    
    def change_hotkey(self, combination: str):
        """Change global hotkey combination"""
        if combination.strip():
            clean_combo = combination.strip().lower()
            print(f"Changing hotkey to: {clean_combo}")
            
            test_thread = GlobalHotkeyThread(clean_combo)
            if test_thread.key_code == 0:
                print(f"Invalid hotkey combination: {clean_combo}")
                self.hotkey_capture.status_label.setText("Invalid combination! Try again.")
                return
            
            self.current_hotkey_display.setText(clean_combo)
            self.overlay.set_hotkey_combination(clean_combo)
            self.hotkey_capture.status_label.setText(f"Applied: {clean_combo}")

    def toggle_overlay(self, enabled: bool):
        """Toggle overlay visibility"""
        self.overlay.set_enabled(enabled)
        self.overlay_toggled.emit(enabled)
    
    def update_opacity(self, value: int):
        """Update overlay opacity"""
        opacity = value / 100.0
        self.overlay.set_opacity(opacity)
        self.opacity_label.setText(f"{value}%")
    
    def change_display_mode(self, mode_text: str):
        """Change overlay display mode"""
        mode = mode_text.lower()
        self.overlay.display_mode = mode
        self.overlay.config['display_mode'] = mode
        self.overlay.create_ui()
        self.overlay.update_display()

        if mode == 'faded':
            self.overlay.hide()
            QTimer.singleShot(100, self.overlay.show_faded_positioning_helper)
        elif self.overlay.is_enabled:
            self.overlay.show_overlay()
    
    def change_theme(self, theme_text: str):
        """Change overlay theme"""
        theme = theme_text.lower()
        self.overlay.set_theme(theme)
    
    def set_position(self, position: str):
        """Set overlay to predefined position"""
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        
        positions = {
            "top-left": (50, 50),
            "top-right": (screen.width() - self.overlay.width() - 50, 50),
            "bottom-left": (50, screen.height() - self.overlay.height() - 100),
            "bottom-right": (screen.width() - self.overlay.width() - 50, 
                           screen.height() - self.overlay.height() - 100),
            "center": (screen.width() // 2 - self.overlay.width() // 2,
                      screen.height() // 2 - self.overlay.height() // 2)
        }
        
        if position in positions:
            x, y = positions[position]
            self.overlay.move(x, y)
    
    def reset_position(self):
        """Reset overlay to default position"""
        self.set_position("top-right")