# form.py

import sys
import ctypes
from ctypes import wintypes

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LMENU = 0xA4
VK_RMENU = 0xA5
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_LWIN = 0x5B
VK_RWIN = 0x5C

class HotkeyCapture(QWidget):
    """Widget for capturing hotkey combinations"""
    hotkey_captured = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.capturing = False
        self.pressed_keys = set()
        self.captured_modifiers = []
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
    
    def get_specific_modifiers(self):
        """Get the specific left/right modifier keys that are currently pressed"""
        modifiers = []
        
        if user32.GetAsyncKeyState(VK_LCONTROL) & 0x8000:
            modifiers.append('lctrl')
        elif user32.GetAsyncKeyState(VK_RCONTROL) & 0x8000:
            modifiers.append('rctrl')
        
        if user32.GetAsyncKeyState(VK_LMENU) & 0x8000:
            modifiers.append('lalt')
        elif user32.GetAsyncKeyState(VK_RMENU) & 0x8000:
            modifiers.append('ralt')
        
        if user32.GetAsyncKeyState(VK_LSHIFT) & 0x8000:
            modifiers.append('lshift')
        elif user32.GetAsyncKeyState(VK_RSHIFT) & 0x8000:
            modifiers.append('rshift')
        
        if user32.GetAsyncKeyState(VK_LWIN) & 0x8000:
            modifiers.append('lwin')
        elif user32.GetAsyncKeyState(VK_RWIN) & 0x8000:
            modifiers.append('rwin')
            
        return modifiers
    
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
            }        """)
        
        layout.addWidget(self.capture_button)
        layout.addWidget(self.status_label)
    
    def start_capture(self):
        """Start capturing hotkey combination"""
        self.capturing = True
        self.pressed_keys.clear()
        self.captured_modifiers = []  # Clear captured modifiers
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
            }        """)
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
            specific_modifiers = self.captured_modifiers
            main_key = None
            
            for key in self.pressed_keys:
                if key in self.key_names:
                    main_key = self.key_names[key]
                    break
            
            if main_key:
                if specific_modifiers:
                    modifier_order = ['lctrl', 'rctrl', 'lalt', 'ralt', 'lshift', 'rshift', 'lwin', 'rwin']
                    sorted_modifiers = [mod for mod in modifier_order if mod in specific_modifiers]
                    hotkey = '+'.join(sorted_modifiers) + '+' + main_key
                else:
                    hotkey = main_key
                
                self.status_label.setText(f"Captured: {hotkey}")
                self.hotkey_captured.emit(hotkey)
            else:                self.status_label.setText("No valid key detected. Try again.")
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

        if key in self.modifier_names or key in self.key_names:
            self.captured_modifiers = self.get_specific_modifiers()

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
        specific_modifiers = self.captured_modifiers
        main_key = None
        
        for key in self.pressed_keys:
            if key in self.key_names:
                main_key = self.key_names[key]
                break
        
        if main_key:
            if specific_modifiers:
                modifier_order = ['lctrl', 'rctrl', 'lalt', 'ralt', 'lshift', 'rshift', 'lwin', 'rwin']
                sorted_modifiers = [mod for mod in modifier_order if mod in specific_modifiers]
                return '+'.join(sorted_modifiers) + '+' + main_key
            else:
                return main_key
        elif specific_modifiers:
            return '+'.join(specific_modifiers) + '+...'
        
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
            'quote': 0xDE, "'": 0xDE        }
        
        parts = key_combo.lower().split('+')

        self.modifiers = 0
        self.key_code = 0
        
        for part in parts:
            part = part.strip()
            if part in ['ctrl', 'control', 'lctrl', 'leftctrl', 'left_ctrl', 'rctrl', 'rightctrl', 'right_ctrl']:
                self.modifiers |= MOD_CONTROL
            elif part in ['shift', 'lshift', 'leftshift', 'left_shift', 'rshift', 'rightshift', 'right_shift']:
                self.modifiers |= MOD_SHIFT
            elif part in ['alt', 'lalt', 'leftalt', 'left_alt', 'ralt', 'rightalt', 'right_alt']:
                self.modifiers |= MOD_ALT
            elif part in ['win', 'windows', 'cmd', 'lwin', 'leftwin', 'left_win', 'rwin', 'rightwin', 'right_win']:
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