# kill_clip.py

import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, List
import ctypes
from ctypes import wintypes

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QCheckBox, QSlider, QGroupBox, QFormLayout, QListWidget, QListWidgetItem,
    QMessageBox, QDialog, QDialogButtonBox, QSpinBox, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from overlays.form import HotkeyCapture

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
    'quote': 0xDE, "'": 0xDE,    'ctrl': 0x11, 'control': 0x11,
    'lctrl': 0xA2, 'leftctrl': 0xA2, 'left_ctrl': 0xA2,
    'rctrl': 0xA3, 'rightctrl': 0xA3, 'right_ctrl': 0xA3,
    
    'alt': 0x12, 'menu': 0x12,
    'lalt': 0xA4, 'leftalt': 0xA4, 'left_alt': 0xA4,
    'ralt': 0xA5, 'rightalt': 0xA5, 'right_alt': 0xA5,
    
    'shift': 0x10,
    'lshift': 0xA0, 'leftshift': 0xA0, 'left_shift': 0xA0,
    'rshift': 0xA1, 'rightshift': 0xA1, 'right_shift': 0xA1,
    
    'win': 0x5B, 'windows': 0x5B, 'meta': 0x5B,
    'lwin': 0x5B, 'leftwin': 0x5B, 'left_win': 0x5B,
    'rwin': 0x5C, 'rightwin': 0x5C, 'right_win': 0x5C
}

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

KEYEVENTF_KEYUP = 0x0002

BUTTON_CONFIG_FILE = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "SCTool_Tracker", "button_automation_config.json")

class ButtonAutomation:
    def __init__(self) -> None:
        self.enabled = False
        self.button_sequences: List[Dict[str, Any]] = []
        self.press_delay_seconds = 0
        self.sequence_delay_ms = 100
        self.hold_duration_ms = 50
        
        self.pending_presses: Dict[str, Dict[str, Any]] = {}
        self.press_callbacks = {}
        
        self.last_execution_time = 0
        self.debounce_ms = 500
        
        self.sequence_last_execution = {}
        self.sequence_debounce_ms = 1000
        self.skip_recent_kills = False
        self.skip_recent_kills_ms = 5000
        
        self.is_executing = False
        
        self.load_config()

    def load_config(self) -> None:
        """Load button automation configuration from file"""
        try:
            config_dir = os.path.dirname(BUTTON_CONFIG_FILE)
            os.makedirs(config_dir, exist_ok=True)
            
            if os.path.exists(BUTTON_CONFIG_FILE):
                with open(BUTTON_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.enabled = config.get('enabled', False)
                self.button_sequences = config.get('button_sequences', [])
                self.press_delay_seconds = config.get('press_delay_seconds', 0)
                self.sequence_delay_ms = config.get('sequence_delay_ms', 100)
                self.hold_duration_ms = config.get('hold_duration_ms', 50)
                self.debounce_ms = config.get('debounce_ms', 500)
                self.sequence_debounce_ms = config.get('sequence_debounce_ms', 1000)
                self.skip_recent_kills = config.get('skip_recent_kills', False)
                self.skip_recent_kills_ms = config.get('skip_recent_kills_ms', 5000)
                
                for seq in self.button_sequences:
                    if 'skip_if_recent' not in seq:
                        seq['skip_if_recent'] = False
                
                logging.info(f"Button automation config loaded: {len(self.button_sequences)} sequences")
            else:
                self._create_default_config()
                logging.info("Created default button automation config with sample sequences")
        except Exception as e:
            logging.error(f"Error loading button automation config: {e}")
            self.enabled = False
            self.button_sequences = []
            self.debounce_ms = 500
            self.sequence_debounce_ms = 1000
            self.skip_recent_kills = False
            self.skip_recent_kills_ms = 5000

    def _create_default_config(self) -> None:
        """Create default configuration file with sample data"""
        try:
            config_dir = os.path.dirname(BUTTON_CONFIG_FILE)
            os.makedirs(config_dir, exist_ok=True)
            
            self.enabled = False
            self.button_sequences = [
                {
                    "name": "GForce",
                    "key_sequence": "alt+shift+f10",
                    "enabled": True,
                    "skip_if_recent": False
                },
                {
                    "name": "wertwer",
                    "key_sequence": "s",
                    "enabled": True,
                    "skip_if_recent": False
                }
            ]
            self.press_delay_seconds = 0
            self.sequence_delay_ms = 100
            self.hold_duration_ms = 50
            self.debounce_ms = 500
            self.sequence_debounce_ms = 1000
            self.skip_recent_kills = False
            self.skip_recent_kills_ms = 5000
            self.save_config()
        except Exception as e:
            logging.error(f"Error creating default button automation config: {e}")

    def save_config(self) -> None:
        """Save button automation configuration to file"""
        try:
            config_dir = os.path.dirname(BUTTON_CONFIG_FILE)
            os.makedirs(config_dir, exist_ok=True)
            
            config = {
                'enabled': self.enabled,
                'button_sequences': self.button_sequences,
                'press_delay_seconds': self.press_delay_seconds,
                'sequence_delay_ms': self.sequence_delay_ms,
                'hold_duration_ms': self.hold_duration_ms,
                'debounce_ms': getattr(self, 'debounce_ms', 500),
                'sequence_debounce_ms': getattr(self, 'sequence_debounce_ms', 1000),
                'skip_recent_kills': getattr(self, 'skip_recent_kills', False),
                'skip_recent_kills_ms': getattr(self, 'skip_recent_kills_ms', 5000)
            }
            
            with open(BUTTON_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
                
            logging.info("Button automation config saved")
        except Exception as e:
            logging.error(f"Error saving button automation config: {e}")

    def set_sequence_debounce_time(self, milliseconds: int) -> None:
        """Set the per-sequence debounce time"""
        self.sequence_debounce_ms = max(100, int(milliseconds))
        logging.info(f"Sequence debounce time set to {self.sequence_debounce_ms}ms")
        self.save_config()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable button automation"""
        self.enabled = enabled
        self.save_config()
        logging.info(f"Button automation {'enabled' if enabled else 'disabled'}")

    def set_press_delay(self, seconds: int) -> None:
        """Set the delay in seconds before pressing buttons after a kill"""
        self.press_delay_seconds = max(0, int(seconds))
        logging.info(f"Button press delay set to {self.press_delay_seconds} seconds")
        self.save_config()

    def set_sequence_delay(self, milliseconds: int) -> None:
        """Set the delay between keys in a sequence"""
        self.sequence_delay_ms = max(10, int(milliseconds))
        logging.info(f"Sequence delay set to {self.sequence_delay_ms}ms")
        self.save_config()

    def set_hold_duration(self, milliseconds: int) -> None:
        """Set how long to hold each key"""
        self.hold_duration_ms = max(10, int(milliseconds))
        logging.info(f"Key hold duration set to {self.hold_duration_ms}ms")
        self.save_config()

    def add_button_sequence(self, name: str, key_sequence: str, enabled: bool = True, skip_if_recent: bool = False) -> bool:
        """Add a new button sequence"""
        try:
            if not self._validate_key_sequence(key_sequence):
                logging.error(f"Invalid key sequence: {key_sequence}")
                return False
            
            for i, seq in enumerate(self.button_sequences):
                if seq['name'] == name:
                    self.button_sequences[i] = {
                        'name': name,
                        'key_sequence': key_sequence,
                        'enabled': enabled,
                        'skip_if_recent': skip_if_recent
                    }
                    self.save_config()
                    logging.info(f"Updated button sequence: {name} -> {key_sequence}")
                    return True
            
            self.button_sequences.append({
                'name': name,
                'key_sequence': key_sequence,
                'enabled': enabled,
                'skip_if_recent': skip_if_recent
            })
            self.save_config()
            logging.info(f"Added button sequence: {name} -> {key_sequence}")
            return True
            
        except Exception as e:
            logging.error(f"Error adding button sequence: {e}")
            return False

    def remove_button_sequence(self, name: str) -> bool:
        """Remove a button sequence by name"""
        try:
            for i, seq in enumerate(self.button_sequences):
                if seq['name'] == name:
                    del self.button_sequences[i]
                    self.save_config()
                    logging.info(f"Removed button sequence: {name}")
                    return True
            
            logging.warning(f"Button sequence not found: {name}")
            return False
        except Exception as e:
            logging.error(f"Error removing button sequence: {e}")
            return False

    def toggle_sequence_enabled(self, name: str) -> bool:
        """Toggle enabled state of a sequence"""
        try:
            for seq in self.button_sequences:
                if seq['name'] == name:
                    seq['enabled'] = not seq.get('enabled', True)
                    self.save_config()
                    logging.info(f"Toggled sequence {name}: {'enabled' if seq['enabled'] else 'disabled'}")
                    return seq['enabled']
            
            logging.warning(f"Button sequence not found: {name}")
            return False
        except Exception as e:
            logging.error(f"Error toggling sequence: {e}")
            return False

    def _validate_key_sequence(self, key_sequence: str) -> bool:
        """Validate that a key sequence contains valid keys"""
        try:
            if not key_sequence or not key_sequence.strip():
                logging.error("Empty key sequence")
                return False
                
            parts = key_sequence.lower().split(',')
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                if '+' in part:
                    combo_parts = part.split('+')
                    for combo_part in combo_parts:
                        combo_part = combo_part.strip()
                        if not combo_part:
                            logging.error("Empty key in combination")
                            return False
                        if combo_part not in VK_CODES:
                            logging.error(f"Invalid key in combination: {combo_part}")
                            return False
                else:
                    if part not in VK_CODES:
                        logging.error(f"Invalid key: {part}")
                        return False
            
            return True
        except Exception as e:
            logging.error(f"Error validating key sequence: {e}")
            return False

    def set_debounce_time(self, milliseconds: int) -> None:
        """Set the debounce time to prevent rapid multiple executions"""
        self.debounce_ms = max(0, int(milliseconds))
        logging.info(f"Button automation debounce set to {self.debounce_ms}ms")
        self.save_config()

    def execute_kill_automation(self, kill_data: Dict[str, Any], callback: Callable[[str, Dict[str, Any]], None] = None) -> None:
        """Execute button automation for a kill event"""
        if not self.enabled or not self.button_sequences:
            logging.debug("Button automation disabled or no sequences configured")
            return
        
        if self.is_executing:
            logging.debug("Automation already executing, skipping to prevent feedback loop")
            return
        
        current_time = time.time() * 1000
        if current_time - self.last_execution_time < self.debounce_ms:
            logging.debug(f"Ignoring rapid execution (debounce: {self.debounce_ms}ms)")
            return
        
        self.last_execution_time = current_time
        
        press_request_id = f"button_press_{int(time.time())}_{hash(str(kill_data))}"
        
        if callback:
            self.press_callbacks[press_request_id] = callback
            
        try:
            if self.press_delay_seconds > 0:
                threading.Thread(
                    target=self._delayed_press_worker,
                    args=(kill_data, press_request_id),
                    daemon=True
                ).start()
            else:
                threading.Thread(
                    target=self._execute_button_sequences,
                    args=(kill_data, press_request_id),
                    daemon=True
                ).start()
                
        except Exception as e:
            logging.error(f"Error starting button automation: {e}")
            if callback:
                callback("error", kill_data)

    def _delayed_press_worker(self, kill_data: Dict[str, Any], press_request_id: str) -> None:
        """Worker thread that waits for the specified delay before pressing buttons"""
        try:
            logging.info(f"Waiting {self.press_delay_seconds} seconds before button automation...")
            time.sleep(self.press_delay_seconds)
            self._execute_button_sequences(kill_data, press_request_id)
        except Exception as e:
            logging.error(f"Error in delayed button press worker: {e}")
            self._handle_press_result("error", kill_data, press_request_id)

    def _execute_button_sequences(self, kill_data: Dict[str, Any], press_request_id: str) -> None:
        """Execute all enabled button sequences"""
        try:
            self.is_executing = True
            
            executed_sequences = []
            skipped_sequences = []
            current_time = time.time() * 1000
            recent_kill_detected = False
            if self.skip_recent_kills and hasattr(kill_data, 'get'):
                timestamp = kill_data.get('timestamp')
                if timestamp:
                    try:
                        kill_time = datetime.fromisoformat(timestamp)
                        kill_time_ms = kill_time.timestamp() * 1000
                        if current_time - kill_time_ms < self.skip_recent_kills_ms:
                            recent_kill_detected = True
                            logging.info(f"Recent kill detected within {self.skip_recent_kills_ms}ms")
                    except (ValueError, TypeError) as e:
                        logging.error(f"Error parsing kill timestamp: {e}")
            
            for sequence in self.button_sequences:
                if not sequence.get('enabled', True):
                    continue
                
                name = sequence['name']
                key_sequence = sequence['key_sequence']
                
                last_exec_time = self.sequence_last_execution.get(name, 0)
                if current_time - last_exec_time < self.sequence_debounce_ms:
                    logging.debug(f"Skipping sequence '{name}' due to debouncing ({self.sequence_debounce_ms}ms)")
                    continue
                
                if sequence.get('skip_if_recent', False) and recent_kill_detected:
                    logging.info(f"Skipping sequence '{name}' due to recent kill")
                    skipped_sequences.append(name)
                    continue
                
                logging.info(f"Executing button sequence: {name} ({key_sequence})")
                
                if self._press_key_sequence(key_sequence):
                    executed_sequences.append(name)
                    self.sequence_last_execution[name] = current_time
                    logging.info(f"Successfully executed sequence: {name}")
                else:
                    logging.error(f"Failed to execute sequence: {name}")
                
                if self.sequence_delay_ms > 0:
                    time.sleep(self.sequence_delay_ms / 1000.0)
            
            if executed_sequences:
                result = f"Executed sequences: {', '.join(executed_sequences)}"
                if skipped_sequences:
                    result += f" | Skipped due to recent kill: {', '.join(skipped_sequences)}"
            else:
                if skipped_sequences:
                    result = f"All sequences skipped due to recent kill: {', '.join(skipped_sequences)}"
                else:
                    result = "No sequences executed"
            
            self._handle_press_result(result, kill_data, press_request_id)
            
        except Exception as e:
            logging.error(f"Error executing button sequences: {e}")
            self._handle_press_result("error", kill_data, press_request_id)
        finally:
            self.is_executing = False

    def _press_key_sequence(self, key_sequence: str) -> bool:
        """Press a sequence of keys/combinations"""
        try:
            parts = key_sequence.lower().split(',')
            
            for i, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue
                
                if '+' in part:
                    if not self._press_key_combination(part):
                        return False
                else:
                    if not self._press_single_key(part):
                        return False
                
                if i < len(parts) - 1 and self.sequence_delay_ms > 0:
                    time.sleep(self.sequence_delay_ms / 1000.0)
            
            return True
            
        except Exception as e:
            logging.error(f"Error pressing key sequence: {e}")
            return False

    def _press_key_combination(self, combination: str) -> bool:
        """Press a key combination like 'ctrl+c'"""
        try:
            parts = combination.split('+')
            keys_to_press = []
            
            for part in parts:
                part = part.strip()
                if part in VK_CODES:
                    keys_to_press.append(VK_CODES[part])
                else:
                    logging.error(f"Unknown key in combination: {part}")
                    return False
            
            for vk_code in keys_to_press:
                scan_code = ctypes.windll.user32.MapVirtualKeyW(vk_code, 0)
                ctypes.windll.user32.keybd_event(vk_code, scan_code, 0, 0)
                time.sleep(0.001)
            
            if self.hold_duration_ms > 0:
                time.sleep(self.hold_duration_ms / 1000.0)
            
            for vk_code in reversed(keys_to_press):
                scan_code = ctypes.windll.user32.MapVirtualKeyW(vk_code, 0)
                ctypes.windll.user32.keybd_event(vk_code, scan_code, KEYEVENTF_KEYUP, 0)
                time.sleep(0.001)
            
            logging.debug(f"Pressed key combination: {combination}")
            return True
            
        except Exception as e:
            logging.error(f"Error pressing key combination {combination}: {e}")
            return False

    def _press_single_key(self, key: str) -> bool:
        """Press a single key"""
        try:
            if key not in VK_CODES:
                logging.error(f"Unknown key: {key}")
                return False
            
            vk_code = VK_CODES[key]
            scan_code = ctypes.windll.user32.MapVirtualKeyW(vk_code, 0)
            
            ctypes.windll.user32.keybd_event(vk_code, scan_code, 0, 0)
            
            if self.hold_duration_ms > 0:
                time.sleep(self.hold_duration_ms / 1000.0)
            else:
                time.sleep(0.01)
            
            ctypes.windll.user32.keybd_event(vk_code, scan_code, KEYEVENTF_KEYUP, 0)
            
            logging.debug(f"Pressed single key: {key}")
            return True
            
        except Exception as e:
            logging.error(f"Error pressing single key {key}: {e}")
            return False

    def _handle_press_result(self, result: str, kill_data: Dict[str, Any], press_request_id: str) -> None:
        """Store the press result to be processed by the main thread"""
        if not hasattr(self, '_press_results'):
            self._press_results = {}
        self._press_results[press_request_id] = (result, kill_data)

    def process_press_callbacks(self) -> List[tuple]:
        """Process press callbacks in the main thread - returns list of (result, kill_data) tuples"""
        results = []
        
        if hasattr(self, '_press_results'):
            for press_request_id, (result, kill_data) in self._press_results.items():
                results.append((result, kill_data))
                
                if press_request_id in self.press_callbacks:
                    try:
                        self.press_callbacks[press_request_id](result, kill_data)
                    except Exception as e:
                        logging.error(f"Error in press callback: {e}")
                    del self.press_callbacks[press_request_id]
            
            self._press_results.clear()
        
        return results

    def is_ready(self) -> bool:
        """Check if button automation is ready to use"""
        return self.enabled and len(self.button_sequences) > 0

    def get_sequence_count(self) -> int:
        """Get the number of configured sequences"""
        return len(self.button_sequences)

    def get_enabled_sequence_count(self) -> int:
        """Get the number of enabled sequences"""
        return len([seq for seq in self.button_sequences if seq.get('enabled', True)])

    def get_sequences_info(self) -> List[Dict[str, Any]]:
        """Get information about all configured sequences"""
        return [
            {
                'name': seq['name'],
                'key_sequence': seq['key_sequence'],
                'enabled': seq.get('enabled', True),
                'skip_if_recent': seq.get('skip_if_recent', False)
            }
            for seq in self.button_sequences
        ]

    def disable_all_sequences(self) -> None:
        """Disable all sequences without removing them"""
        for seq in self.button_sequences:
            seq['enabled'] = False
        self.save_config()
        logging.info("Disabled all button sequences")

    def enable_all_sequences(self) -> None:
        """Enable all sequences"""
        for seq in self.button_sequences:
            seq['enabled'] = True
        self.save_config()
        logging.info("Enabled all button sequences")

    def test_sequence(self, name: str) -> bool:
        """Test a specific sequence by executing it immediately"""
        try:
            for sequence in self.button_sequences:
                if sequence['name'] == name:
                    key_sequence = sequence['key_sequence']
                    logging.info(f"Testing button sequence: {name} ({key_sequence})")
                    
                    result = self._press_key_sequence(key_sequence)
                    if result:
                        logging.info(f"Test successful: {name}")
                    else:
                        logging.error(f"Test failed: {name}")
                    return result
            
            logging.error(f"Sequence not found for testing: {name}")
            return False
            
        except Exception as e:
            logging.error(f"Error testing sequence {name}: {e}")
            return False

    def set_skip_recent_kills(self, enabled: bool) -> None:
        """Enable or disable skipping recent kills globally"""
        self.skip_recent_kills = enabled
        self.save_config()
        logging.info(f"Skip recent kills {'enabled' if enabled else 'disabled'}")

    def set_skip_recent_kills_time(self, milliseconds: int) -> None:
        """Set the time threshold in milliseconds for recent kills"""
        self.skip_recent_kills_ms = max(500, int(milliseconds))
        self.save_config()
        logging.info(f"Skip recent kills time set to {self.skip_recent_kills_ms}ms")

    def toggle_sequence_skip_if_recent(self, name: str) -> bool:
        """Toggle whether a sequence should be skipped if there was a recent kill"""
        try:
            for seq in self.button_sequences:
                if seq['name'] == name:
                    seq['skip_if_recent'] = not seq.get('skip_if_recent', False)
                    self.save_config()
                    logging.info(f"Toggled 'skip if recent' for {name}: {seq['skip_if_recent']}")
                    return seq['skip_if_recent']
            
            logging.warning(f"Button sequence not found: {name}")
            return False
        except Exception as e:
            logging.error(f"Error toggling skip if recent: {e}")
            return False

def process_button_automation_callbacks(button_automation) -> None:
    """Process any pending button automation callbacks in the main thread"""
    if hasattr(button_automation, 'process_press_callbacks'):
        press_results = button_automation.process_press_callbacks()
        for result, kill_data in press_results:
            logging.info(f"Button automation result: {result}")

class ButtonSequenceDialog(QDialog):
    """Dialog for adding/editing button sequences"""
    
    def __init__(self, parent=None, sequence_data=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.sequence_data = sequence_data
        self.setup_ui()
        
        if sequence_data:
            self.load_sequence_data()
    def setup_ui(self):
        try:
            from language_manager import t
        except ImportError:
            def t(text):
                return text
                
        self.setWindowTitle(t("Add/Edit Button Sequence"))
        self.setModal(True)
        self.resize(400, 300)
        
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #222222;
                color: #ffffff;
            }
            QDialog::title {
                background-color: #ffffff;
                color: #ffffff;
            }
            QLabel, QGroupBox, QCheckBox, QPushButton, QTextEdit, QLineEdit, QSpinBox {
                color: #ffffff;
                background: transparent;
            }
            QMessageBox QLabel, QMessageBox QPushButton {
                color: #ffffff;
            }
            QDialogButtonBox QPushButton {
                color: #ffffff;
            }
            /* Fix for input fields and their text */
            QLineEdit, QTextEdit {
                background-color: #1e1e1e;
                color: #f0f0f0;
            }
            QSpinBox {
                color: #ffffff;
                background-color: #1e1e1e;
            }
            /* Title bar styling */
            QWidget#windowTitle {
                background-color: #ffffff;
                color: #ffffff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        self.name_label = QLabel(t("Sequence Name:"))
        self.name_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
        layout.addWidget(self.name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(t("e.g., 'Screenshot', 'Quick Chat'"))
        self.name_input.setStyleSheet(
            "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 12px; "
            "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
            "QLineEdit:hover, QLineEdit:focus { border-color: #ff6b35; }"
        )
        layout.addWidget(self.name_input)
        
        self.sequence_group = QGroupBox(t("Key Sequence"))
        self.sequence_group.setStyleSheet(
            "QGroupBox { color: #ffffff; font-weight: bold; background: transparent; border: 1px solid #333333; "
            "border-radius: 8px; margin-top: 10px; padding-top: 10px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 10px 0 10px; }"
        )
        sequence_layout = QVBoxLayout(self.sequence_group)
        sequence_layout.setContentsMargins(15, 15, 15, 15)
        sequence_layout.setSpacing(10)
        
        self.sequence_desc = QLabel(t("Enter key sequence (comma-separated):"))
        self.sequence_desc.setStyleSheet("QLabel { color: #cccccc; font-size: 13px; background: transparent; border: none; }")
        sequence_layout.addWidget(self.sequence_desc)
        
        self.sequence_input = QTextEdit()
        self.sequence_input.setMaximumHeight(80)
        self.sequence_input.setStyleSheet(
            "QTextEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 12px; "
            "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
            "QTextEdit:hover, QTextEdit:focus { border-color: #ff6b35; }"
        )
        self.sequence_input.setPlaceholderText(t("Examples: ctrl+c"))
        sequence_layout.addWidget(self.sequence_input)
        
        self.help_label = QLabel()
        help_parts = [
            t("Supported formats:"),
            f"• {t('Single keys: f12, space, enter')}",
            f"• {t('Combinations: ctrl+c, alt+tab')}"
        ]
        help_text = "\n".join(help_parts)
        self.help_label.setText(help_text)
        self.help_label.setStyleSheet("color: #888888; font-size: 11px;")
        sequence_layout.addWidget(self.help_label)
        
        layout.addWidget(self.sequence_group)
        self.capture_group = QGroupBox(t("Or Capture Hotkey"))
        self.capture_group.setStyleSheet(
            "QGroupBox { color: #ffffff; font-weight: bold; background: transparent; border: 1px solid #333333; "
            "border-radius: 8px; margin-top: 10px; padding-top: 10px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 10px 0 10px; }"
        )
        capture_layout = QVBoxLayout(self.capture_group)
        capture_layout.setContentsMargins(15, 15, 15, 15)
        
        self.capture_instruction = QLabel(t("Click 'Capture' multiple times to build a sequence:"))
        self.capture_instruction.setStyleSheet("color: #cccccc; font-size: 12px;")
        capture_layout.addWidget(self.capture_instruction)
        
        self.hotkey_capture = HotkeyCapture()
        self.hotkey_capture.hotkey_captured.connect(self.on_hotkey_captured)
        capture_layout.addWidget(self.hotkey_capture)
        
        capture_button_layout = QHBoxLayout()
        
        self.clear_capture_button = QPushButton(t("Clear Sequence"))
        self.clear_capture_button.clicked.connect(self.clear_captured_sequence)
        self.clear_capture_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
            "padding: 8px 12px; font-weight: bold; }"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #4a4a4a, stop:1 #303030); }"
            "QPushButton:pressed { background: #202020; }"
        )
        capture_button_layout.addWidget(self.clear_capture_button)
        
        capture_button_layout.addStretch()
        capture_layout.addLayout(capture_button_layout)
        
        layout.addWidget(self.capture_group)
        
        checkbox_layout = QVBoxLayout()
        checkbox_layout.setSpacing(10)
        
        self.enabled_checkbox = QCheckBox(t("Enable this sequence"))
        self.enabled_checkbox.setChecked(True)
        self.enabled_checkbox.setStyleSheet(
            "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; }"
            "QCheckBox::indicator { width: 20px; height: 20px; }"
            "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
            "QCheckBox::indicator:checked { border: 1px solid #ff6b35; background-color: #ff6b35; border-radius: 3px; }"
        )
        checkbox_layout.addWidget(self.enabled_checkbox)
        
        self.skip_recent_checkbox = QCheckBox(t("Skip if another kill happens within time limit"))
        self.skip_recent_checkbox.setChecked(False)
        self.skip_recent_checkbox.setStyleSheet(
            "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; }"
            "QCheckBox::indicator { width: 20px; height: 20px; }"
            "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
            "QCheckBox::indicator:checked { border: 1px solid #ff6b35; background-color: #ff6b35; border-radius: 3px; }"
        )
        checkbox_layout.addWidget(self.skip_recent_checkbox)
        
        layout.addLayout(checkbox_layout)
        self.test_button = QPushButton(t("Test Sequence"))
        self.test_button.clicked.connect(self.test_sequence)
        self.test_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
            "padding: 12px; font-weight: bold; }"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #4a4a4a, stop:1 #303030); }"
            "QPushButton:pressed { background: #202020; }"
        )
        layout.addWidget(self.test_button)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.setStyleSheet(
            "QDialogButtonBox QPushButton { background-color: #2a2a2a; color: white; "
            "border: 1px solid #555555; padding: 8px 16px; font-weight: bold; }"
            "QDialogButtonBox QPushButton:hover { background-color: #3a3a3a; border: 1px solid #777777; }"
            "QDialogButtonBox QPushButton:pressed { background-color: #ff6b35; }"
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
    
    def load_sequence_data(self):
        """Load existing sequence data into the dialog"""
        if self.sequence_data:
            self.name_input.setText(self.sequence_data.get('name', ''))
            self.sequence_input.setPlainText(self.sequence_data.get('key_sequence', ''))
            self.enabled_checkbox.setChecked(self.sequence_data.get('enabled', True))
            self.skip_recent_checkbox.setChecked(self.sequence_data.get('skip_if_recent', False))

    def on_hotkey_captured(self, hotkey: str):
        """Handle captured hotkey - avoid duplicates when pressing the same key multiple times"""
        current_text = self.sequence_input.toPlainText().strip()
        
        parts = [part.strip() for part in current_text.split(',') if part.strip()]
        
        if parts and parts[-1] == hotkey:
            logging.debug(f"Ignoring duplicate hotkey: {hotkey}")
            return
        
        if current_text:
            new_text = f"{current_text}, {hotkey}"
        else:
            new_text = hotkey
        
        self.sequence_input.setPlainText(new_text)
    
    def clear_captured_sequence(self):
        """Clear the captured sequence"""
        self.sequence_input.clear()
    
    def test_sequence(self):
        """Test the current sequence"""
        from language_manager import t
        
        sequence = self.sequence_input.toPlainText().strip()
        if not sequence:
            msg = QMessageBox(self)
            msg.setWindowTitle(t("Test Sequence"))
            msg.setIcon(QMessageBox.Warning)
            msg.setText(t("Please enter a key sequence first."))
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #222222;
                    color: #ffffff;
                }
                QMessageBox QLabel {
                    color: #ffffff;
                }
                QMessageBox QPushButton {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QMessageBox QPushButton:hover {
                    background-color: #3a3a3a;
                    border: 1px solid #777777;
                }
            """)
            msg.exec_()
            return
        temp_automation = ButtonAutomation()
        temp_automation.add_button_sequence("test", sequence, True)
        
        if temp_automation.test_sequence("test"):
            msg = QMessageBox(self)
            msg.setWindowTitle(t("Test Sequence"))
            msg.setIcon(QMessageBox.Information)
            msg.setText(t("Sequence executed successfully!"))
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #222222;
                    color: #ffffff;
                }
                QMessageBox QLabel {
                    color: #ffffff;
                }
                QMessageBox QPushButton {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QMessageBox QPushButton:hover {
                    background-color: #3a3a3a;
                    border: 1px solid #777777;
                }
            """)
            msg.exec_()
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle(t("Test Sequence"))
            msg.setIcon(QMessageBox.Warning)
            msg.setText(t("Failed to execute sequence. Please check the key format."))            
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #222222;
                    color: #ffffff;
                }
                QMessageBox QLabel {
                    color: #ffffff;
                }
                QMessageBox QPushButton {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QMessageBox QPushButton:hover {
                    background-color: #3a3a3a;
                    border: 1px solid #777777;
                }
            """)
            msg.exec_()
    
    def get_sequence_data(self) -> Optional[Dict[str, Any]]:
        """Get the sequence data from the dialog"""
        name = self.name_input.text().strip()
        sequence = self.sequence_input.toPlainText().strip()
        
        if not name or not sequence:
            return None
        
        return {
            'name': name,
            'key_sequence': sequence,
            'enabled': self.enabled_checkbox.isChecked(),
            'skip_if_recent': self.skip_recent_checkbox.isChecked()
        }

    def update_translations(self):
        """Update UI text for current language"""
        try:
            from language_manager import t
            
            self.setWindowTitle(t("Add/Edit Button Sequence"))
            
            if hasattr(self, 'name_label'):
                self.name_label.setText(t("Sequence Name:"))
            if hasattr(self, 'sequence_desc'):
                self.sequence_desc.setText(t("Enter key sequence (comma-separated):"))
            if hasattr(self, 'capture_instruction'):
                self.capture_instruction.setText(t("Click 'Capture' multiple times to build a sequence:"))
            if hasattr(self, 'help_label'):
                help_parts = [
                    t("Supported formats:"),
                    f"• {t('Single keys: f12, space, enter')}",
                    f"• {t('Combinations: ctrl+c, alt+tab')}"
                ]
                help_text = "\n".join(help_parts)
                self.help_label.setText(help_text)
                self.help_label.update()
            if hasattr(self, 'sequence_group'):
                self.sequence_group.setTitle(t("Key Sequence"))
            if hasattr(self, 'capture_group'):
                self.capture_group.setTitle(t("Or Capture Hotkey"))
            
            if hasattr(self, 'clear_capture_button'):
                self.clear_capture_button.setText(t("Clear Sequence"))
            if hasattr(self, 'test_button'):
                self.test_button.setText(t("Test Sequence"))

            if hasattr(self, 'button_box'):
                for button in self.button_box.buttons():
                    role = self.button_box.buttonRole(button)
                    if role == QDialogButtonBox.AcceptRole:
                        button.setText(t("OK"))
                    elif role == QDialogButtonBox.RejectRole:
                        button.setText(t("Cancel"))
            
            if hasattr(self, 'enabled_checkbox'):
                self.enabled_checkbox.setText(t("Enable this sequence"))
            if hasattr(self, 'skip_recent_checkbox'):
                self.skip_recent_checkbox.setText(t("Skip if another kill happens within time limit"))

            if hasattr(self, 'name_input'):
                self.name_input.setPlaceholderText(t("e.g., 'Screenshot', 'Quick Chat'"))
            if hasattr(self, 'sequence_input'):
                self.sequence_input.setPlaceholderText(t("Examples: ctrl+c"))
                
        except Exception as e:
            logging.error(f"Error updating ButtonSequenceDialog translations: {e}")

    def showEvent(self, event):
        """Override showEvent to ensure translations are applied"""
        super().showEvent(event)
        try:
            self.update_translations()
        except Exception as e:
            logging.error(f"Error updating translations on show: {e}")

class ButtonAutomationWidget(QWidget):
    """Main widget for button automation configuration"""
    
    def __init__(self, button_automation=None, parent=None):
        super().__init__(parent)
        self.button_automation = button_automation or ButtonAutomation()
        self.setup_ui()
        self.refresh_sequences()
    
    def setup_ui(self):
        try:
            from language_manager import t
        except ImportError:
            def t(text):
                return text
                
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        self.master_enabled = QCheckBox(t("Enable Button Automation"))
        self.master_enabled.setChecked(self.button_automation.enabled)
        self.master_enabled.toggled.connect(self.on_master_enabled_changed)
        self.master_enabled.setStyleSheet(
            "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; }"
            "QCheckBox::indicator { width: 20px; height: 20px; }"
            "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
            "QCheckBox::indicator:checked { border: 1px solid #ff6b35; background-color: #ff6b35; border-radius: 3px; }"
        )
        layout.addWidget(self.master_enabled)
        
        settings_group = QGroupBox(t("Automation Settings"))
        settings_group.setStyleSheet(
            "QGroupBox { color: #ffffff; font-weight: bold; background: transparent; border: 1px solid #333333; "
            "border-radius: 8px; margin-top: 10px; padding-top: 10px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 10px 0 10px; }"
        )
        settings_layout = QFormLayout(settings_group)
        settings_layout.setContentsMargins(15, 15, 15, 15)
        settings_layout.setSpacing(15)
        settings_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        press_delay_label = QLabel(t("Press Delay:"))
        press_delay_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
        
        delay_container = QWidget()
        delay_container.setStyleSheet("background: transparent; border: none;")
        delay_layout = QHBoxLayout(delay_container)
        delay_layout.setContentsMargins(0, 0, 0, 0)
        delay_layout.setSpacing(10)
        
        self.delay_slider = QSlider(Qt.Horizontal)
        self.delay_slider.setRange(0, 10)
        self.delay_slider.setValue(self.button_automation.press_delay_seconds)
        self.delay_slider.valueChanged.connect(self.on_delay_changed)
        self.delay_slider.setStyleSheet(
            "QSlider::groove:horizontal { border: 1px solid #2a2a2a; height: 10px; "
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a1a1a, stop:1 #2a2a2a); "
            "margin: 2px 0; border-radius: 5px; }"
            "QSlider::handle:horizontal { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #ff6b35, stop:1 #d85527); border: 1px solid #2a2a2a; "
            "width: 20px; height: 20px; margin: -6px 0; border-radius: 10px; }"
            "QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0 #d85527, stop:1 #ff6b35); border-radius: 5px; }"
            "QSlider::handle:horizontal:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #ff8555, stop:1 #f55527); border: 1px solid #ff6b35; }"
        )
        delay_layout.addWidget(self.delay_slider)
        
        self.delay_label = QLabel(f"{self.button_automation.press_delay_seconds} seconds")
        self.delay_label.setStyleSheet("QLabel { color: #ffffff; background: transparent; border: none; }")
        self.delay_label.setAlignment(Qt.AlignCenter)
        delay_layout.addWidget(self.delay_label)
        
        settings_layout.addRow(press_delay_label, delay_container)
        
        sequence_delay_label = QLabel("Sequence Delay:")
        sequence_delay_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
        
        self.sequence_delay_spin = QSpinBox()
        self.sequence_delay_spin.setRange(10, 10000)
        self.sequence_delay_spin.setSuffix(" ms")
        self.sequence_delay_spin.setValue(self.button_automation.sequence_delay_ms)
        self.sequence_delay_spin.valueChanged.connect(self.on_sequence_delay_changed)
        self.sequence_delay_spin.setStyleSheet(
            "QSpinBox { background-color: #1e1e1e; color: #f0f0f0; padding: 8px; "
            "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
            "QSpinBox:hover, QSpinBox:focus { border-color: #ff6b35; }"
            "QSpinBox::up-button, QSpinBox::down-button { background-color: #2a2a2a; border: none; width: 16px; }"
            "QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #ff6b35; }"
        )
        settings_layout.addRow(sequence_delay_label, self.sequence_delay_spin)
        
        hold_duration_label = QLabel("Key Hold Duration:")
        hold_duration_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
        
        self.hold_duration_spin = QSpinBox()
        self.hold_duration_spin.setRange(10, 5000)
        self.hold_duration_spin.setSuffix(" ms")
        self.hold_duration_spin.setValue(self.button_automation.hold_duration_ms)
        self.hold_duration_spin.valueChanged.connect(self.on_hold_duration_changed)
        self.hold_duration_spin.setStyleSheet(
            "QSpinBox { background-color: #1e1e1e; color: #f0f0f0; padding: 8px; "
            "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
            "QSpinBox:hover, QSpinBox:focus { border-color: #ff6b35; }"
            "QSpinBox::up-button, QSpinBox::down-button { background-color: #2a2a2a; border: none; width: 16px; }"
            "QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #ff6b35; }"
        )
        settings_layout.addRow(hold_duration_label, self.hold_duration_spin)
        
        recent_kills_group = QGroupBox(t("Recent Kills Protection"))
        recent_kills_group.setStyleSheet(
            "QGroupBox { color: #ffffff; font-weight: bold; background: transparent; border: 1px solid #333333; "
            "border-radius: 8px; margin-top: 10px; padding-top: 10px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 10px 0 10px; }"
        )
        recent_kills_layout = QVBoxLayout(recent_kills_group)
        recent_kills_layout.setContentsMargins(15, 15, 15, 15)
        recent_kills_layout.setSpacing(15)
        
        self.skip_recent_kills_checkbox = QCheckBox(t("Skip key presses if another kill happens within time limit"))
        self.skip_recent_kills_checkbox.setChecked(self.button_automation.skip_recent_kills)
        self.skip_recent_kills_checkbox.toggled.connect(self.on_skip_recent_kills_changed)
        self.skip_recent_kills_checkbox.setStyleSheet(
            "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; }"
            "QCheckBox::indicator { width: 20px; height: 20px; }"
            "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
            "QCheckBox::indicator:checked { border: 1px solid #ff6b35; background-color: #ff6b35; border-radius: 3px; }"
        )
        recent_kills_layout.addWidget(self.skip_recent_kills_checkbox)
        
        skip_time_container = QWidget()
        skip_time_layout = QHBoxLayout(skip_time_container)
        skip_time_layout.setContentsMargins(0, 0, 0, 0)
        skip_time_layout.setSpacing(10)
        
        skip_time_label = QLabel(t("Time limit:"))
        skip_time_label.setStyleSheet("QLabel { color: #ffffff; background: transparent; border: none; font-size: 14px; }")
        skip_time_layout.addWidget(skip_time_label)
        
        self.skip_time_slider = QSlider(Qt.Horizontal)
        self.skip_time_slider.setRange(500, 10000)
        self.skip_time_slider.setSingleStep(100)
        self.skip_time_slider.setPageStep(1000)
        self.skip_time_slider.setValue(self.button_automation.skip_recent_kills_ms)
        self.skip_time_slider.valueChanged.connect(self.on_skip_time_changed)
        self.skip_time_slider.setStyleSheet(
            "QSlider::groove:horizontal { border: 1px solid #2a2a2a; height: 10px; "
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a1a1a, stop:1 #2a2a2a); "
            "margin: 2px 0; border-radius: 5px; }"
            "QSlider::handle:horizontal { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #ff6b35, stop:1 #d85527); border: 1px solid #2a2a2a; "
            "width: 20px; height: 20px; margin: -6px 0; border-radius: 10px; }"
            "QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0 #d85527, stop:1 #ff6b35); border-radius: 5px; }"
            "QSlider::handle:horizontal:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #ff8555, stop:1 #f55527); border: 1px solid #ff6b35; }"
        )
        skip_time_layout.addWidget(self.skip_time_slider)
        
        self.skip_time_label = QLabel(f"{self.button_automation.skip_recent_kills_ms / 1000:.1f} seconds")
        self.skip_time_label.setStyleSheet("QLabel { color: #cccccc; min-width: 80px; text-align: right; }")
        skip_time_layout.addWidget(self.skip_time_label)
        
        recent_kills_layout.addWidget(skip_time_container)
        
        layout.addWidget(recent_kills_group)
        
        sequences_group = QGroupBox("Button Sequences")
        sequences_group.setStyleSheet(
            "QGroupBox { color: #ffffff; font-weight: bold; background: transparent; border: 1px solid #333333; "
            "border-radius: 8px; margin-top: 10px; padding-top: 10px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 10px 0 10px; }"
        )
        sequences_layout = QVBoxLayout(sequences_group)
        sequences_layout.setContentsMargins(15, 15, 15, 15)
        sequences_layout.setSpacing(15)
        
        self.sequence_list = QListWidget()
        self.sequence_list.itemDoubleClicked.connect(self.edit_sequence)
        self.sequence_list.setStyleSheet(
            "QListWidget { background-color: #1e1e1e; color: #ffffff; border: 1px solid #333333; "
            "border-radius: 4px; padding: 5px; }"
            "QListWidget::item { padding: 8px; border-bottom: 1px solid #333333; }"
            "QListWidget::item:selected { background-color: #ff6b35; color: #ffffff; }"
            "QListWidget::item:hover { background-color: #2a2a2a; }"
        )
        sequences_layout.addWidget(self.sequence_list)
        
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add Sequence")
        self.add_button.clicked.connect(self.add_sequence)
        self.add_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
            "border-radius: 4px; padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #4a4a4a, stop:1 #303030); }"
            "QPushButton:pressed { background: #ff6b35; }"
        )
        button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_sequence)
        self.edit_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
            "border-radius: 4px; padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #4a4a4a, stop:1 #303030); }"
            "QPushButton:pressed { background: #ff6b35; }"
        )
        button_layout.addWidget(self.edit_button)
        
        self.test_button = QPushButton("Test")
        self.test_button.clicked.connect(self.test_sequence)
        self.test_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
            "border-radius: 4px; padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #4a4a4a, stop:1 #303030); }"
            "QPushButton:pressed { background: #ff6b35; }"
        )
        button_layout.addWidget(self.test_button)
        
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_sequence)
        self.remove_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
            "border-radius: 4px; padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #4a4a4a, stop:1 #303030); }"
            "QPushButton:pressed { background: #ff6b35; }"
        )
        button_layout.addWidget(self.remove_button)
        
        button_layout.addStretch()
        
        self.enable_all_button = QPushButton("Enable All")
        self.enable_all_button.clicked.connect(self.enable_all_sequences)
        self.enable_all_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
            "border-radius: 4px; padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #4a4a4a, stop:1 #303030); }"
            "QPushButton:pressed { background: #ff6b35; }"
        )
        button_layout.addWidget(self.enable_all_button)
        
        self.disable_all_button = QPushButton("Disable All")
        self.disable_all_button.clicked.connect(self.disable_all_sequences)
        self.disable_all_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
            "border-radius: 4px; padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #4a4a4a, stop:1 #303030); }"
            "QPushButton:pressed { background: #ff6b35; }"
        )
        button_layout.addWidget(self.disable_all_button)
        
        sequences_layout.addLayout(button_layout)
        
        layout.addWidget(sequences_group)
        
        self.status_label = QLabel()
        self.update_status()
        layout.addWidget(self.status_label)
    
    def on_master_enabled_changed(self, enabled: bool):
        """Handle master enable checkbox changes"""
        self.button_automation.set_enabled(enabled)
        self.update_status()
    
    def on_delay_changed(self, value: int):
        """Handle delay slider changes"""
        self.button_automation.set_press_delay(value)
        self.delay_label.setText(f"{value} seconds")
    
    def on_sequence_delay_changed(self, value: int):
        """Handle sequence delay changes"""
        self.button_automation.set_sequence_delay(value)
    
    def on_hold_duration_changed(self, value: int):
        """Handle hold duration changes"""
        self.button_automation.set_hold_duration(value)
    
    def on_skip_recent_kills_changed(self, enabled):
        """Handle toggle of skip recent kills checkbox"""
        self.button_automation.set_skip_recent_kills(enabled)
        self.skip_time_slider.setEnabled(enabled)
        
    def on_skip_time_changed(self, value):
        """Handle change of skip time slider"""
        self.button_automation.set_skip_recent_kills_time(value)
        self.skip_time_label.setText(f"{value / 1000:.1f} seconds")
    
    def add_sequence(self):
        """Add a new sequence"""
        try:
            from language_manager import t
        except ImportError:
            def t(text):
                return text
            
        dialog = ButtonSequenceDialog(self)
        try:
            dialog.update_translations()
        except Exception as e:
            logging.debug(f"Error updating dialog translations: {e}")
            
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_sequence_data()
            if data:
                if self.button_automation.add_button_sequence(
                    data['name'], 
                    data['key_sequence'], 
                    data['enabled'],
                    data['skip_if_recent']
                ):
                    self.refresh_sequences()
                    self.update_status()
                else:
                    QMessageBox.warning(self, t("Add Sequence"), t("Failed to add sequence. Please check the key format."))
    
    def edit_sequence(self):
        """Edit the selected sequence"""
        try:
            from language_manager import t
        except ImportError:
            def t(text):
                return text
                
        current_item = self.sequence_list.currentItem()
        if not current_item:
            return
        
        sequence_name = current_item.data(Qt.UserRole)
        sequence_data = None
        
        for seq in self.button_automation.button_sequences:
            if seq['name'] == sequence_name:
                sequence_data = seq
                break
        
        if sequence_data:
            dialog = ButtonSequenceDialog(self, sequence_data)
            try:
                dialog.update_translations()
            except Exception as e:
                logging.debug(f"Error updating dialog translations: {e}")
                
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_sequence_data()
                if data:
                    self.button_automation.remove_button_sequence(sequence_name)
                    if self.button_automation.add_button_sequence(
                        data['name'], 
                        data['key_sequence'], 
                        data['enabled'],
                        data['skip_if_recent']
                    ):
                        self.refresh_sequences()
                        self.update_status()
                    else:
                        QMessageBox.warning(self, t("Edit Sequence"), t("Failed to update sequence. Please check the key format."))
    
    def test_sequence(self):
        """Test the selected sequence"""
        try:
            from language_manager import t
        except ImportError:
            def t(text):
                return text
                
        current_item = self.sequence_list.currentItem()
        if not current_item:
            QMessageBox.information(self, t("Test Sequence"), t("Please select a sequence to test."))
            return
        
        sequence_name = current_item.data(Qt.UserRole)
        
        if self.button_automation.test_sequence(sequence_name):
            QMessageBox.information(self, t("Test Sequence"), t("Sequence '{sequence_name}' executed successfully!").format(sequence_name=sequence_name))
        else:
            QMessageBox.warning(self, t("Test Sequence"), t("Failed to execute sequence '{sequence_name}'.").format(sequence_name=sequence_name))
    
    def remove_sequence(self):
        """Remove the selected sequence"""
        try:
            from language_manager import t
        except ImportError:
            def t(text):
                return text
                
        current_item = self.sequence_list.currentItem()
        if not current_item:
            return
        
        sequence_name = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, 
            t("Remove Sequence"), 
            t("Are you sure you want to remove the sequence '{sequence_name}'?").format(sequence_name=sequence_name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.button_automation.remove_button_sequence(sequence_name):
                self.refresh_sequences()
                self.update_status()
    
    def enable_all_sequences(self):
        """Enable all sequences"""
        self.button_automation.enable_all_sequences()
        self.refresh_sequences()
        self.update_status()
    
    def disable_all_sequences(self):
        """Disable all sequences"""
        self.button_automation.disable_all_sequences()
        self.refresh_sequences()
        self.update_status()
    
    def refresh_sequences(self):
        """Refresh the sequence list"""
        self.sequence_list.clear()
        
        for seq in self.button_automation.button_sequences:
            name = seq['name']
            key_sequence = seq['key_sequence']
            enabled = seq.get('enabled', True)
            status = "✓" if enabled else "✗"
            display_text = f"{status} {name} - {key_sequence}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, name)
            
            if enabled:
                item.setForeground(Qt.white)
            else:
                item.setForeground(Qt.gray)
            
            self.sequence_list.addItem(item)
    
    def update_status(self):
        """Update the status label"""
        try:
            from language_manager import t
        except ImportError:
            def t(text):
                return text
                
        total = self.button_automation.get_sequence_count()
        enabled_count = self.button_automation.get_enabled_sequence_count()
        
        if self.button_automation.enabled:
            status = f"{t('Status: Enabled')} - {enabled_count}/{total} {t('sequences active')}"
            self.status_label.setStyleSheet("color: #ff6b35; font-weight: bold; background: transparent; border: none; font-size: 14px;")
        else:
            status = f"{t('Status: Disabled')} - {total} {t('sequences configured')}"
            self.status_label.setStyleSheet("color: #888888; font-weight: bold; background: transparent; border: none; font-size: 14px;")
        
        self.status_label.setText(status)
    
    def update_translations(self):
        """Update UI text for current language"""
        try:
            from language_manager import t
            
            if hasattr(self, 'master_enabled'):
                self.master_enabled.setText(t("Enable Button Automation"))
            
            if hasattr(self, 'add_button'):
                self.add_button.setText(t("Add Sequence"))
            if hasattr(self, 'edit_button'):
                self.edit_button.setText(t("Edit"))
            if hasattr(self, 'test_button'):
                self.test_button.setText(t("Test"))
            if hasattr(self, 'remove_button'):
                self.remove_button.setText(t("Remove"))
            if hasattr(self, 'enable_all_button'):
                self.enable_all_button.setText(t("Enable All"))
            if hasattr(self, 'disable_all_button'):
                self.disable_all_button.setText(t("Disable All"))
            
            try:
                for widget in self.findChildren(QLabel):
                    text = widget.text()
                    if text == "Automation Settings":
                        widget.setText(t("Automation Settings"))
                    elif text == "Button Sequences":
                        widget.setText(t("Button Sequences"))
                    elif text == "Press Delay:":
                        widget.setText(t("Press Delay:"))
                    elif text == "Sequence Delay:":
                        widget.setText(t("Sequence Delay:"))
                    elif text == "Key Hold Duration:":
                        widget.setText(t("Key Hold Duration"))
                    elif text == "Skip Recent Kills:":
                        widget.setText(t("Skip Recent Kills"))
                    elif text == "Time limit:":
                        widget.setText(t("Time limit:"))
                    elif text == "Note: Each sequence can be individually set to skip on recent kills":
                        widget.setText(t("Note: Each sequence can be individually set to skip on recent kills"))
                    elif text.endswith(" seconds"):
                        seconds = text.replace(" seconds", "")
                        widget.setText(f"{seconds} {t('seconds')}")
                    elif text.startswith("Status: Enabled"):
                        if "sequences active" in text:
                            parts = text.split("-")
                            if len(parts) > 1:
                                count_part = parts[1].strip()
                                widget.setText(f"{t('Status: Enabled')} - {count_part.replace('sequences active', t('sequences active'))}")
                        else:
                            widget.setText(t("Status: Enabled"))
                    elif text.startswith("Status: Disabled"):
                        if "sequences configured" in text:
                            parts = text.split("-")
                            if len(parts) > 1:
                                count_part = parts[1].strip()
                                widget.setText(f"{t('Status: Disabled')} - {count_part.replace('sequences configured', t('sequences configured'))}")
                        else:
                            widget.setText(t("Status: Disabled"))
            except Exception as e:
                logging.debug(f"Error updating Button Automation label translations: {e}")
            
            try:
                for group_box in self.findChildren(QGroupBox):
                    title = group_box.title()
                    if title == "Automation Settings":
                        group_box.setTitle(t("Automation Settings"))
                    elif title == "Button Sequences":
                        group_box.setTitle(t("Button Sequences"))
                    elif title == "Recent Kills Protection":
                        group_box.setTitle(t("Recent Kills Protection"))
            except Exception as e:
                logging.debug(f"Error updating Button Automation group box translations: {e}")
                
            try:
                if hasattr(self, 'skip_recent_kills_checkbox'):
                    self.skip_recent_kills_checkbox.setText(t("Skip key presses if another kill happens within time limit"))
            except Exception as e:
                logging.debug(f"Error updating Button Automation checkbox translations: {e}")
                
            self.refresh_sequences()
            self.update_status()
            
        except Exception as e:
            logging.error(f"Error updating Button Automation translations: {e}")

    def get_button_automation(self) -> ButtonAutomation:
        """Get the button automation instance"""
        return self.button_automation