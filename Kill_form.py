# Kill_form.py

import sys
import os
import subprocess
import json
import re
import base64
import atexit
import logging
import time
import requests
import ctypes
import webbrowser
import shutil
from kill_parser import VERSION
from datetime import datetime
from packaging import version
from bs4 import BeautifulSoup
from urllib.parse import quote
from typing import Optional, Dict, Any, List

from utlity import apply_styles as apply_styles_func
from Registered_kill import format_registered_kill

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLineEdit, QPushButton, QTextBrowser,
    QFileDialog, QVBoxLayout, QHBoxLayout, QMessageBox, QGroupBox, QCheckBox,
    QSlider, QFormLayout, QLabel, QComboBox, QDialog, QSizePolicy, QProgressDialog,
    QSystemTrayIcon, QMenu, QAction, QFrame, QGraphicsOpacityEffect, QScrollArea
)
from PyQt5.QtGui import QIcon, QDesktopServices, QPixmap, QPainter, QBrush, QPen, QColor, QPainterPath
from PyQt5.QtCore import (
    Qt, QUrl, QTimer, QStandardPaths, QDir, QSize, QRect, QPropertyAnimation, QEasingCurve
)
from PyQt5.QtMultimedia import QSoundEffect

from Kill_thread import ApiSenderThread, TailThread, RescanThread, MissingKillsDialog
from kill_parser import KILL_LOG_PATTERN, CHROME_USER_AGENT
from twitch_integration import TwitchIntegration, process_twitch_callbacks
from kill_clip import ButtonAutomation, process_button_automation_callbacks, ButtonAutomationWidget
from responsive_ui import ScreenScaler, ResponsiveUIHelper, make_popup_responsive

from utlity import init_ui, load_config, load_local_kills, apply_styles, CollapsibleSettingsPanel, styled_message_box, check_for_updates_ui

from language_manager import language_manager, t
from language_selector_widget import LanguageSelector
from translation_utils import translate_application, setup_auto_translation
from utlity import TranslationMixin

APP_MUTEX_NAME = "SCToolKillfeedMutex_A5F301E7-D3E9-4F6F-BD57-4A114F103240"
app_instance = None

def is_already_running():
    """Check if another instance of the application is already running"""
    if sys.platform.startswith('win'):
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, APP_MUTEX_NAME)
        last_error = ctypes.windll.kernel32.GetLastError()
        if last_error == 183:
            return True
    return False

def find_existing_window():
    """Find and activate the existing application window"""
    if sys.platform.startswith('win'):
        try:
            FindWindow = ctypes.windll.user32.FindWindowW
            SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow
            ShowWindow = ctypes.windll.user32.ShowWindow
            hwnd = FindWindow(None, f"SCTool Killfeed {VERSION}")
            
            if hwnd:
                ShowWindow(hwnd, 9)
                SetForegroundWindow(hwnd)
                return True
        except Exception as e:
            logging.error(f"Error finding existing window: {e}")
    return False

def dark_title_bar_for_pyqt5(widget: QWidget) -> None:
    if sys.platform.startswith("win"):
        try:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
            hwnd = widget.winId().__int__()
            value = ctypes.c_int(2)
            set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
        except Exception as e:
            logging.error(f"Error enabling dark title bar: {e}")

def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_appdata_paths() -> tuple[str, str, str]:
    appdata_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not appdata_dir:
        appdata_dir = os.path.expanduser("~")
    tracker_dir = os.path.join(appdata_dir, "SCTool_Tracker")
    QDir().mkpath(tracker_dir)

    config_file = os.path.join(tracker_dir, "config.json")
    log_file = os.path.join(tracker_dir, "kill_logger.log")
    return config_file, log_file, tracker_dir

CONFIG_FILE, LOG_FILE, TRACKER_DIR = get_appdata_paths()

logging.basicConfig(
    filename=LOG_FILE,
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

LOCAL_KILLS_FILE = os.path.join(TRACKER_DIR, "logged_kills.json")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": CHROME_USER_AGENT})
PLAYER_DETAILS_CACHE: Dict[str, Dict[str, str]] = {}

class KillLoggerGUI(QMainWindow, TranslationMixin):
    __client_id__ = "kill_logger_client"
    __version__ = VERSION

    def __init__(self) -> None:
        super().__init__()
        self.twitch_chat_message_template = "🔫 {username} just killed {victim}! 🚀 {profile_url}"
        self.setWindowTitle(t(f"SCTool Killfeed {VERSION}"))
        self.setWindowIcon(QIcon(resource_path("chris2.ico")))
        self.kill_count = 0
        self.death_count = 0
        self.monitor_thread: Optional[TailThread] = None
        self.rescan_thread: Optional[RescanThread] = None
        self.missing_kills_queue: List[dict] = []
        self.api_endpoint = "https://starcitizentool.com/api/v1/kills"
        self.user_agent = CHROME_USER_AGENT
        self.local_user_name = ""
        self.dark_mode_enabled = True
        
        _, _, self.scale_factor = ScreenScaler.get_screen_info()
        self.ui_helper = ResponsiveUIHelper(self)
        
        self.kill_sound_enabled = False
        self.kill_sound_effect = QSoundEffect()
        self.kill_sound_path = resource_path("kill.wav")
        self.kill_sound_volume = 100
        
        self.death_sound_enabled = False
        self.death_sound_effect = QSoundEffect()
        self.death_sound_path = resource_path("death.wav")
        self.death_sound_volume = 100
        
        self.api_key = ""
        self.registration_attempts = 0
        self.local_kills: Dict[str, Any] = {}
        self.kills_local_file = LOCAL_KILLS_FILE
        self.persistent_info = {
            "monitoring": "",
            "registered": "",
            "game_mode": "",
            "api_connection": "",
            "twitch_connected": ""
        }
        
        self.minimize_to_tray = False
        self.start_with_system = False
        self.tray_icon = None
        self.tray_menu = None
        self.last_animation_timer = None
        
        self.stats_panel_visible = True
        self.twitch_enabled = False
        self.auto_connect_twitch = False
        self.twitch = TwitchIntegration()
        self.clip_creation_enabled = True
        self.chat_posting_enabled = True
        self.clips: Dict[str, str] = {}
        
        self.twitch_callback_timer = QTimer()
        self.twitch_callback_timer.timeout.connect(lambda: process_twitch_callbacks(self))
        self.twitch_callback_timer.start(1000)
        self.last_clip_creation_time = 0
        
        self.button_automation = ButtonAutomation()
        self.button_automation_callback_timer = QTimer()
        self.button_automation_callback_timer.timeout.connect(lambda: process_button_automation_callbacks(self))
        self.button_automation_callback_timer.start(1000)
        
        self.current_clip_group_id = ""
        self.clip_group_window_seconds = 10
        self.clip_groups: Dict[str, List[str]] = {}
        self.latest_kill_info = None
        self.latest_death_info = None
        
        self.apply_styles = lambda: apply_styles_func(self)
        
        init_ui(self)
        load_config(self)
        load_local_kills(self)
        apply_styles(self)
        self.initialize_system_tray()  
        self.rescan_button.setEnabled(False)
        self.handle_auto_connect_twitch()
        
        self.setup_translation_system()
        
        self.update_ui_scaling()

    def create_nav_button(self, text, obj_name=None):
        """Create a styled navigation button for the sidebar"""
        button = QPushButton(text)
        button.setStyleSheet(
            "QPushButton { text-align: left; padding: 12px 15px; font-weight: bold; color: #bbbbbb; "
            "background-color: transparent; border: none; border-left: 3px solid transparent; }"
            "QPushButton:hover { color: #ffffff; background-color: #222222; border-left: 3px solid #f04747; }"
            "QPushButton:checked { color: #ffffff; background-color: #252525; border-left: 3px solid #f04747; }"
        )
        if obj_name:
            button.setObjectName(obj_name)
        return button

    def create_stat_card(self, label_text, value_text, value_color):
        """Create a styled stat card widget"""
        card = QWidget()
        card.setStyleSheet("border: none; background: #1a1a1a; border-radius: 8px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        value = QLabel(value_text)
        value.setObjectName("stat_value")
        value.setStyleSheet(
            f"QLabel {{ color: {value_color}; font-size: 24px; font-weight: bold; background: transparent; border: none; }}"
        )
        value.setAlignment(Qt.AlignCenter)
        
        label = QLabel(label_text)
        label.setStyleSheet(
            "QLabel { color: #aaaaaa; font-size: 12px; background: transparent; border: none; }"
        )
        label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(value)
        layout.addWidget(label)
        
        return card

    def initialize_system_tray(self) -> None:
        """Set up the system tray icon and menu"""
        if QSystemTrayIcon.isSystemTrayAvailable():

            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon(resource_path("chris2.ico")))
            self.tray_icon.setToolTip("SCTool Killfeed")
            self.tray_menu = QMenu()
            show_action = QAction("Open SCTool", self)
            show_action.triggered.connect(self.show_from_tray)
            stats_action = QAction(f"Kills: {self.kill_count} | Deaths: {self.death_count}", self)
            stats_action.setEnabled(False)
            
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.quit_application)            
            self.tray_menu.addAction(show_action)
            self.tray_menu.addAction(stats_action)
            self.tray_menu.addSeparator()
            self.tray_menu.addAction(quit_action)
            self.tray_icon.setContextMenu(self.tray_menu)
            self.tray_stats_timer = QTimer(self)
            self.tray_stats_timer.timeout.connect(lambda: self.update_tray_stats(stats_action))
            self.tray_stats_timer.start(5000)
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
            
            self.tray_icon.show()
            
            logging.info("System tray icon initialized")
            
    def update_tray_stats(self, stats_action: QAction) -> None:
        """Update the kill/death stats in the tray menu"""
        if self.tray_icon and stats_action:
            stats_action.setText(f"Kills: {self.kill_count} | Deaths: {self.death_count}")
            
    def on_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle activation of the tray icon"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_from_tray()
            
    def show_from_tray(self) -> None:
        """S
        he main window when activated from tray"""
        self.showNormal()
        self.activateWindow()
        
    def quit_application(self) -> None:
        """Completely quit the application including tray icon"""
        if self.tray_icon:
            self.tray_icon.hide()
        self.close()
        
    def setup_autostart(self, enable: bool) -> None:
        """Set up or remove the autostart entry for Windows"""
        if sys.platform.startswith("win"):
            import winreg
            
            try:
                app_path = os.path.abspath(sys.executable)
                app_name = "SCTool_Killfeed"
                
                registry_key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
                )
                
                if enable:
                    winreg.SetValueEx(registry_key, app_name, 0, winreg.REG_SZ, f'"{app_path}"')
                    logging.info(f"Added application to startup: {app_path}")
                else:
                    try:
                        winreg.DeleteValue(registry_key, app_name)
                        logging.info("Removed application from startup")
                    except FileNotFoundError:
                        pass
                    
                winreg.CloseKey(registry_key)
                return True
                
            except Exception as e:
                logging.error(f"Error managing autostart: {e}")
                return False
        else:
            logging.warning("Autostart is only supported on Windows")
            return False

    def save_config(self) -> None:
        ship_value = self.ship_combo.currentText().strip()
        if not ship_value:
            ship_value = "No Ship"
        
        config = {
            'monitoring_active': self.monitor_thread.isRunning() if self.monitor_thread else False,
            'kill_sound': self.kill_sound_enabled,
            'kill_sound_path': self.kill_sound_path_input.text().strip(),
            'kill_sound_volume': self.volume_slider.value(),
            'death_sound': self.death_sound_enabled,
            'death_sound_path': self.death_sound_path_input.text().strip(),
            'death_sound_volume': self.death_volume_slider.value(),
            'log_path': self.log_path_input.text().strip(),
            'api_key': self.api_key_input.text().strip(),
            'local_user_name': self.local_user_name,
            'send_to_api': self.send_to_api_checkbox.isChecked(),
            'killer_ship': ship_value,
            'twitch_enabled': self.twitch_enabled,
            'auto_connect_twitch': self.auto_connect_twitch,
            'twitch_channel': self.twitch_channel_input.text().strip(),
            'clip_creation_enabled': self.clip_creation_enabled,
            'chat_posting_enabled': self.chat_posting_enabled,
            'clips': self.clips,
            'clip_delay_seconds': self.clip_delay_slider.value(),
            'minimize_to_tray': self.minimize_to_tray,
            'start_with_system': self.start_with_system,
            'twitch_chat_message_template': self.twitch_chat_message_template,
            'language': language_manager.current_language
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def on_rescan_button_clicked(self) -> None:
        log_path = self.log_path_input.text().strip()
        if not log_path or not os.path.isfile(log_path):
            self.showCustomMessageBox("Input Error", "Please enter a valid path to your Game.log file.", QMessageBox.Warning)
            return

        if self.rescan_thread and self.rescan_thread.isRunning():
            self.rescan_thread.stop()
            self.rescan_thread.wait(3000)
            self.rescan_thread = None

        registered_user = self.local_user_name
        self.rescan_thread = RescanThread(log_path, registered_user, parent=self)
        self.rescan_thread.rescanFinished.connect(self.rescan_finished_handler)
        self.rescan_thread.start()

    def rescan_finished_handler(self, found_kills: List[dict]) -> None:
        missing = []
        missing_details = ""
        for kill in found_kills:
            if kill["local_key"] not in self.local_kills:
                missing.append(kill)
                parts = kill["local_key"].split("::")
                if len(parts) >= 3:
                    timestamp, victim, game_mode = parts[0], parts[1], parts[2]
                    missing_details += f"{timestamp} - {victim} ({game_mode})\n"
                else:
                    missing_details += kill["local_key"] + "\n"

        if missing:
            dialog = MissingKillsDialog(missing, self)
            if dialog.exec_() == QDialog.Accepted:
                selected_kills = dialog.getSelectedKills()
                if selected_kills:
                    self.send_missing_kills(selected_kills)
                else:
                    self.append_kill_readout(f"<div style='color: #FF9800; font-weight: bold; margin: 10px 0;'>⚠️ {t('No kills selected to send.')}</div>")
            else:
                self.append_kill_readout(f"<div style='color: #FF9800; font-weight: bold; margin: 10px 0;'>⚠️ {t('Missing kills were not sent.')}</div>")
        else:
            self.append_kill_readout(f"<div style='color: #2196F3; font-weight: bold; margin: 10px 0;'>ℹ️ {t('No missing kills found.')}</div>")
    
    def display_missing_kill(self, kill: dict) -> None:
        """Display a missing kill in the kill feed"""
        try:
            payload = kill.get("payload", {})
            local_key = kill.get("local_key", "")
            
            timestamp = kill.get("timestamp", "")
            parts = local_key.split("::")
            game_mode = parts[2] if len(parts) >= 3 else "Unknown"
            
            log_line = payload.get("log_line", "")
            
            match = KILL_LOG_PATTERN.search(log_line)
            if match:
                data = match.groupdict()
                attacker = data.get('attacker', '').strip()

                if attacker and attacker == self.local_user_name:
                    self.update_user_profile_image(attacker)
                
                if "killer_ship" not in data and "killer_ship" in payload:
                    data["killer_ship"] = payload["killer_ship"]
                
                readout, _ = format_registered_kill(
                    log_line, data, self.local_user_name, timestamp, game_mode, success=True
                )
                
                self.append_kill_readout_no_count(readout)
            
                if local_key not in self.local_kills:
                    self.local_kills[local_key] = {
                        "payload": payload,
                        "timestamp": timestamp,
                        "attacker": attacker,
                        "readout": readout,
                        "sent_to_api": False,
                        "local_key": local_key                    
                    }
                    self.save_local_kills()
                
                logging.info(f"Displayed missing kill in feed: {local_key}")
        except Exception as e:
            logging.error(f"Error displaying missing kill: {e}")
    
    def send_next_missing_kill(self) -> None:
        if not self.missing_kills_queue:
            return

        kill = self.missing_kills_queue.pop(0)
        local_key = kill["local_key"]
        payload = kill["payload"]
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'X-API-Key': self.api_key,
            'User-Agent': self.user_agent,
            'X-Client-ID': self.__client_id__,
            'X-Client-Version': self.__version__
        }
        api_thread = ApiSenderThread(self.api_endpoint, headers, payload, local_key, parent=self)
        api_thread.apiResponse.connect(lambda msg, response_data, key=local_key: self.handle_missing_api_response(msg, key, response_data))
        api_thread.start()
        
    def send_missing_kills(self, missing_kills: List[dict]) -> None:
        self.missing_kills_queue = missing_kills.copy()
        self.missing_kills_results = {
            'duplicates': [],
            'new_kills': [],
            'errors': [],
            'total': len(missing_kills)
        }

        self.append_kill_readout(f"<div style='color: #4CAF50; font-weight: bold; margin: 10px 0;'>📤 {t('Processing {count} missing kills...').format(count=len(missing_kills))}</div>")
        
        for index, kill in enumerate(missing_kills):
            QTimer.singleShot(index * 500, lambda k=kill: self.send_single_missing_kill(k))

    def send_single_missing_kill(self, kill: dict) -> None:
        """Send a single missing kill to the API"""
        local_key = kill["local_key"]
        payload = kill["payload"]
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'X-API-Key': self.api_key,
            'User-Agent': self.user_agent,
            'X-Client-ID': self.__client_id__,
            'X-Client-Version': self.__version__
        }
        
        self.display_missing_kill(kill)

        api_thread = ApiSenderThread(self.api_endpoint, headers, payload, local_key, parent=self)
        api_thread.apiResponse.connect(lambda msg, response_data, key=local_key: self.handle_missing_api_response(msg, key, response_data))
        api_thread.start()

    def handle_missing_api_response(self, msg: str, local_key: str, response_data=None) -> None:
        success = False
        is_duplicate = False

        if msg.startswith("Duplicate kill"):
            logging.info(f"Kill {local_key} already exists on server")
            success = True
            is_duplicate = True
            self.missing_kills_results['duplicates'].append(local_key)
        elif "kill logged successfully" in msg.lower() or msg.strip() == "":
            logging.info(f"Kill {local_key} sent successfully")
            success = True
            self.missing_kills_results['new_kills'].append(local_key)
            
            if local_key in self.local_kills:
                readout = self.local_kills[local_key].get("readout", "")
                if "YOU KILLED" in readout:
                    self.kill_count += 1
                    self.update_kill_death_stats()
                    logging.info(f"Incremented kill count to {self.kill_count} for new kill: {local_key}")
                elif "YOU DIED" in readout:
                    self.death_count += 1
                    self.update_kill_death_stats()
                    logging.info(f"Incremented death count to {self.death_count} for new death: {local_key}")
        else:
            logging.error(f"Failed to send kill {local_key}: {msg}")
            self.missing_kills_results['errors'].append({'key': local_key, 'error': msg})

        self.missing_kills_queue = [k for k in self.missing_kills_queue if k.get("local_key") != local_key]

        processed_count = (len(self.missing_kills_results['duplicates']) + 
                        len(self.missing_kills_results['new_kills']) + 
                        len(self.missing_kills_results['errors']))
        
        if processed_count >= self.missing_kills_results['total']:
            self.post_missing_kills_summary()

    def post_missing_kills_summary(self) -> None:
        """Post a detailed summary of missing kills processing to the kill feed"""
        results = self.missing_kills_results

        summary_html = "<div style='background-color: #1a1a1a; border-left: 4px solid #4CAF50; padding: 15px; margin: 10px 0; border-radius: 5px;'>"
        summary_html += f"<div style='color: #4CAF50; font-weight: bold; font-size: 16px; margin-bottom: 10px;'>📊 {t('Missing Kills Processing Complete')}</div>"

        summary_html += f"<div style='color: #ffffff; margin-bottom: 8px;'>{t('Total processed')}: <span style='color: #4CAF50; font-weight: bold;'>{results['total']}</span></div>"
        
        if results['new_kills']:
            summary_html += f"<div style='color: #ffffff; margin-bottom: 8px;'>✅ {t('New kills sent')}: <span style='color: #4CAF50; font-weight: bold;'>{len(results['new_kills'])}</span></div>"

            summary_html += "<div style='margin-left: 20px; margin-bottom: 8px;'>"
            for kill_key in results['new_kills']:
                parts = kill_key.split("::")
                if len(parts) >= 2:
                    victim = parts[1]
                    timestamp = parts[0]
                    summary_html += f"<div style='color: #81C784; font-size: 12px;'>• {victim} ({timestamp})</div>"
            summary_html += "</div>"
        
        if results['duplicates']:
            summary_html += f"<div style='color: #ffffff; margin-bottom: 8px;'>⚠️ {t('Duplicates found')}: <span style='color: #FFA726; font-weight: bold;'>{len(results['duplicates'])}</span></div>"

            summary_html += "<div style='margin-left: 20px; margin-bottom: 8px;'>"
            for kill_key in results['duplicates']:
                parts = kill_key.split("::")
                if len(parts) >= 2:
                    victim = parts[1]
                    timestamp = parts[0]
                    summary_html += f"<div style='color: #FFB74D; font-size: 12px;'>• {victim} ({timestamp}) - {t('already on server')}</div>"
            summary_html += "</div>"
        
        if results['errors']:
            summary_html += f"<div style='color: #ffffff; margin-bottom: 8px;'>❌ {t('Errors')}: <span style='color: #F44336; font-weight: bold;'>{len(results['errors'])}</span></div>"

            summary_html += "<div style='margin-left: 20px; margin-bottom: 8px;'>"
            for error_item in results['errors']:
                kill_key = error_item['key']
                error_msg = error_item['error']
                parts = kill_key.split("::")
                if len(parts) >= 2:
                    victim = parts[1]
                    timestamp = parts[0]
                    summary_html += f"<div style='color: #EF5350; font-size: 12px;'>• {victim} ({timestamp}) - {error_msg}</div>"
            summary_html += "</div>"
        
        summary_html += "</div>"

        self.append_kill_readout(summary_html)
        self.missing_kills_results = {'duplicates': [], 'new_kills': [], 'errors': [], 'total': 0}

    def on_player_registered(self, text: str) -> None:
        match = re.search(r"Registered user:\s+(.+)$", text)
        if match:
            self.local_user_name = match.group(1).strip()
            self.user_display.setText(f"{self.local_user_name}")
            self.update_bottom_info("registered", text)
            self.save_config()
            self.rescan_button.setEnabled(True)
            QTimer.singleShot(500, lambda: self.update_user_profile_image(self.local_user_name))

    def open_tracker_files(self) -> None:
        webbrowser.open(TRACKER_DIR)

    def generate_api_diagnostic_report(self) -> str:
        """Generate a comprehensive diagnostic report for API connection issues"""
        import platform
        import sys
        
        diagnostic_info = {
            "timestamp": datetime.now().isoformat(),
            "application": {
                "version": getattr(self, '__version__', 'Unknown'),
                "client_id": getattr(self, '__client_id__', 'Unknown'),
                "user_agent": getattr(self, 'user_agent', 'Unknown')
            },
            "system": {
                "platform": platform.platform(),
                "python_version": sys.version,
                "architecture": platform.architecture()[0]
            },
            "api_configuration": {
                "endpoint": getattr(self, 'api_endpoint', 'Not configured'),
                "api_key_provided": bool(getattr(self, 'api_key', None)),
                "api_key_length": len(getattr(self, 'api_key', '')) if getattr(self, 'api_key', None) else 0,
                "send_to_api_enabled": getattr(self, 'send_to_api_checkbox', None) and self.send_to_api_checkbox.isChecked()
            },
            "network_test": {}
        }
        
        try:
            import socket
            import urllib.parse
            
            if hasattr(self, 'api_endpoint') and self.api_endpoint:
                parsed_url = urllib.parse.urlparse(self.api_endpoint)
                hostname = parsed_url.hostname
                port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((hostname, port))
                sock.close()
                
                diagnostic_info["network_test"] = {
                    "hostname": hostname,
                    "port": port,
                    "socket_connection": "SUCCESS" if result == 0 else f"FAILED (error code: {result})"
                }
                
                try:
                    ping_url = self.api_endpoint.replace('/kills', '/ping')
                    headers = {
                        'Accept': 'application/json',
                        'X-API-Key': getattr(self, 'api_key', ''),
                        'User-Agent': getattr(self, 'user_agent', 'Unknown')
                    }
                    
                    import requests
                    ping_response = requests.get(ping_url, headers=headers, timeout=10)
                    diagnostic_info["api_ping_test"] = {
                        "ping_url": ping_url,
                        "status_code": ping_response.status_code,
                        "response_length": len(ping_response.text),
                        "content_type": ping_response.headers.get('content-type', 'Unknown'),
                        "response_preview": ping_response.text[:200] + "..." if len(ping_response.text) > 200 else ping_response.text,
                        "cloudflare_challenge": "just a moment" in ping_response.text.lower() or "cloudflare" in ping_response.text.lower()
                    }
                    
                    if ping_response.status_code != 200:
                        diagnostic_info["api_ping_test"]["error_details"] = f"HTTP {ping_response.status_code}: {ping_response.reason}"
                        
                        if ping_response.status_code == 403 and diagnostic_info["api_ping_test"]["cloudflare_challenge"]:
                            diagnostic_info["api_ping_test"]["issue_type"] = "CLOUDFLARE_SECURITY_CHALLENGE"
                            diagnostic_info["api_ping_test"]["not_api_key_issue"] = True
                        
                except Exception as ping_error:
                    diagnostic_info["api_ping_test"] = {
                        "error": str(ping_error),
                        "error_type": type(ping_error).__name__
                    }
                    
        except Exception as e:
            diagnostic_info["network_test"]["error"] = str(e)
        
        report = "=== SCTool Tracker API Diagnostic Report ===\n\n"
        report += f"Generated: {diagnostic_info['timestamp']}\n\n"
        
        report += "APPLICATION INFO:\n"
        for key, value in diagnostic_info["application"].items():
            report += f"  {key}: {value}\n"
        
        report += "\nSYSTEM INFO:\n"
        for key, value in diagnostic_info["system"].items():
            report += f"  {key}: {value}\n"
        
        report += "\nAPI CONFIGURATION:\n"
        for key, value in diagnostic_info["api_configuration"].items():
            report += f"  {key}: {value}\n"
        
        report += "\nNETWORK TEST:\n"
        for key, value in diagnostic_info["network_test"].items():
            report += f"  {key}: {value}\n"
        
        # Add API ping test results if available
        if "api_ping_test" in diagnostic_info:
            report += "\nAPI PING TEST:\n"
            for key, value in diagnostic_info["api_ping_test"].items():
                report += f"  {key}: {value}\n"
        
        report += "\n=== End of Diagnostic Report ===\n"
        
        return report

    def test_api_key_validity(self) -> dict:
        """Test API key validity and return detailed results"""
        test_results = {
            "api_key_format_valid": False,
            "ping_successful": False,
            "status_code": None,
            "error_message": "",
            "recommendations": []
        }
        
        api_key = getattr(self, 'api_key', '')
        if api_key and len(api_key) >= 32:
            test_results["api_key_format_valid"] = True
        else:
            test_results["recommendations"].append("API key appears too short or missing")
        
        try:
            ping_url = self.api_endpoint.replace('/kills', '/ping')
            headers = {
                'Accept': 'application/json',
                'X-API-Key': api_key,
                'User-Agent': self.user_agent,
                'X-Client-ID': self.__client_id__,
                'X-Client-Version': self.__version__
            }
            
            response = requests.get(ping_url, headers=headers, timeout=10)
            test_results["status_code"] = response.status_code
            
            if response.status_code == 200:
                test_results["ping_successful"] = True
            elif response.status_code == 401:
                test_results["error_message"] = "Invalid or expired API key"
                test_results["recommendations"].append("Check your API key at https://starcitizentool.com/profile")
            elif response.status_code == 403:
                if "just a moment" in response.text.lower() or "cloudflare" in response.text.lower():
                    test_results["error_message"] = "Cloudflare security challenge blocking access"
                    test_results["recommendations"].extend([
                        "This is NOT an API key problem - Cloudflare is blocking your requests",
                        "Try using a VPN from a different location",
                        "Contact support - this may require server configuration changes",
                        "Wait and try again later (may be temporary)"
                    ])
                else:
                    test_results["error_message"] = "Access forbidden"
                    test_results["recommendations"].append("Verify your account permissions")
            elif response.status_code == 404:
                test_results["error_message"] = "API endpoint not found"
                test_results["recommendations"].append("Update to the latest version")
            elif response.status_code >= 500:
                test_results["error_message"] = "Server error"
                test_results["recommendations"].append("Server is temporarily unavailable, try again later")
            else:
                test_results["error_message"] = f"Unexpected status code: {response.status_code}"
                test_results["recommendations"].append("Contact support with this diagnostic information")
                
        except requests.exceptions.RequestException as e:
            test_results["error_message"] = str(e)
            test_results["recommendations"].append("Check your internet connection")
            
        return test_results

    def analyze_user_case_7_20_2025(self, diagnostic_report: str) -> str:
        """Analyze the specific user case from July 20, 2025 and provide targeted advice"""
        analysis = []
        
        if "socket_connection: SUCCESS" in diagnostic_report:
            analysis.append("✓ Network connectivity to server is working")
        
        if "api_key_length: 48" in diagnostic_report:
            analysis.append("✓ API key length appears correct (48 characters)")
        
        if "send_to_api_enabled: True" in diagnostic_report:
            analysis.append("✓ API integration is enabled")
        
        analysis.append("\n🔍 LIKELY CAUSES FOR YOUR ISSUE:")
        analysis.append("1. API key may be invalid/expired (most common)")
        analysis.append("2. API key may not be properly formatted")
        analysis.append("3. Server-side validation issue")
        analysis.append("4. Account permissions issue")
        
        analysis.append("\n📋 RECOMMENDED ACTIONS:")
        analysis.append("1. Double-check your API key at https://starcitizentool.com/profile")
        analysis.append("2. Copy and paste the API key carefully (no extra spaces)")
        analysis.append("3. Try generating a new API key if available")
        analysis.append("4. Verify your account is in good standing")
        analysis.append("5. Contact support with your diagnostic information")
        
        return "\n".join(analysis)

    def try_cloudflare_bypass_headers(self) -> dict:
        """Generate headers that might help bypass Cloudflare challenges"""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'X-API-Key': self.api_key,
            'X-Client-ID': self.__client_id__,
            'X-Client-Version': self.__version__
        }

    def ping_api_with_retry(self) -> bool:
        """Try pinging the API with different approaches to work around Cloudflare"""
        if self.ping_api():
            return True
            
        logging.info("Normal API ping failed, trying with enhanced headers for Cloudflare...")
        
        try:
            ping_url = self.api_endpoint.replace('/kills', '/ping')
            headers = self.try_cloudflare_bypass_headers()
            
            response = requests.get(ping_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                logging.info("API ping successful with enhanced headers")
                return True
            else:
                logging.error(f"API ping with enhanced headers also failed: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"Enhanced API ping failed: {e}")
            return False

    def ping_api(self) -> bool:
        """Test API connectivity by pinging the server"""
        try:
            ping_url = self.api_endpoint.replace('/kills', '/ping')
            
            headers = {
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'X-API-Key': self.api_key,
                'User-Agent': self.user_agent,
                'X-Client-ID': self.__client_id__,
                'X-Client-Version': self.__version__
            }
            
            logging.info(f"Attempting API ping to: {ping_url}")
            logging.info(f"API key prefix (first 12 chars): {self.api_key[:12] + '...' if len(self.api_key) > 12 else self.api_key}")
            logging.debug(f"Ping headers: {headers}")
            
            logging.info("Making GET request to API ping endpoint...")
            response = requests.get(ping_url, headers=headers, timeout=10)
            
            logging.info(f"API ping response status: {response.status_code}")
            logging.info(f"Response headers: {dict(response.headers)}")
            logging.info(f"Raw response content (first 1000 chars): {response.text[:1000]}")
            logging.debug(f"Full response content: {response.text}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'application/json' not in content_type:
                    logging.warning(f"API ping returned non-JSON content type: {content_type}")
                    logging.warning(f"Response body: {response.text}")
                    return False
                
                try:
                    data = response.json()
                    logging.debug(f"Parsed JSON response: {data}")
                    
                    if 'registered_in_game_name' in data:
                        registered_name = data['registered_in_game_name']
                        if registered_name and not self.local_user_name:
                            self.local_user_name = registered_name
                            if hasattr(self, 'user_display'):
                                self.user_display.setText(f"{self.local_user_name}")
                            logging.info(f"Retrieved registered username from API: {registered_name}")
                    
                    logging.info("API ping successful")
                    return True
                    
                except ValueError as json_error:
                    logging.error(f"Failed to parse JSON from ping response: {json_error}")
                    logging.error(f"Response content: {response.text}")
                    return False
                    
            elif response.status_code == 400:
                # Try to parse error message even on 400
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Unknown error')
                    logging.warning(f"API ping returned 400: {error_msg}")
                except ValueError:
                    logging.warning(f"API ping failed with status 400, non-JSON response: {response.text}")
                return False
                
            elif response.status_code == 401:
                logging.error("API ping failed: Invalid API key (401 Unauthorized)")
                logging.error("TROUBLESHOOTING: Your API key appears to be invalid or expired.")
                logging.error("SOLUTION: Please check your API key at https://starcitizentool.com/profile")
                return False
                
            elif response.status_code == 403:
                logging.error("API ping failed: Access forbidden (403 Forbidden)")
                
                # Check if this is a Cloudflare challenge
                if "just a moment" in response.text.lower() or "cloudflare" in response.text.lower():
                    logging.error("CLOUDFLARE SECURITY CHALLENGE DETECTED")
                    logging.error("This is not an API key issue - Cloudflare is blocking the request")
                    logging.error("TROUBLESHOOTING: Cloudflare security is preventing access")
                    logging.error("SOLUTIONS:")
                    logging.error("  1. Try using a VPN from a different location")
                    logging.error("  2. Contact support - this is a server-side security setting issue")
                    logging.error("  3. Wait and try again later (temporary block)")
                    logging.error("  4. Check if your IP is on any blocklists")
                else:
                    logging.error("TROUBLESHOOTING: Your API key may not have sufficient permissions.")
                    logging.error("SOLUTION: Please verify your account status at https://starcitizentool.com/profile")
                return False
                
            elif response.status_code == 404:
                logging.error("API ping failed: Endpoint not found (404 Not Found)")
                logging.error(f"TROUBLESHOOTING: The API endpoint {ping_url} was not found.")
                logging.error("SOLUTION: This may indicate a server issue or outdated client version.")
                return False
                
            elif response.status_code >= 500:
                logging.error(f"API ping failed: Server error ({response.status_code})")
                logging.error("TROUBLESHOOTING: The API server is experiencing issues.")
                logging.error("SOLUTION: Please try again later or contact support if the issue persists.")
                return False
                
            else:
                logging.warning(f"API ping failed with status code: {response.status_code}")
                logging.warning(f"Response content: {response.text}")
                logging.error(f"TROUBLESHOOTING: Unexpected HTTP status code {response.status_code}")
                logging.error("SOLUTION: Please share this diagnostic information with support.")
                return False
                
        except requests.exceptions.ConnectionError as e:
            logging.error(f"API ping failed - Connection Error: {e}")
            logging.error("This usually indicates network connectivity issues or incorrect API endpoint URL")
            logging.error(f"Attempted URL: {ping_url}")
            return False
        except requests.exceptions.Timeout as e:
            logging.error(f"API ping failed - Timeout Error: {e}")
            logging.error("The API server took too long to respond (>10 seconds)")
            return False
        except requests.exceptions.HTTPError as e:
            logging.error(f"API ping failed - HTTP Error: {e}")
            return False
        except requests.exceptions.RequestException as e:
            logging.error(f"API ping failed with network error: {e}")
            logging.error(f"Request error type: {type(e).__name__}")
            return False
        except ValueError as json_error:
            logging.error(f"API ping failed with JSON parsing error: {json_error}")
            logging.error("This usually means the server returned non-JSON content (HTML error page, etc.)")
            return False
        except Exception as e:
            logging.error(f"API ping failed with unexpected error: {e}")
            logging.error(f"Error type: {type(e).__name__}")
            logging.error(f"Error args: {e.args}")
            import traceback
            logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def detect_cloudflare_challenge(self, response_text: str, status_code: int) -> bool:
        """Detect if a response is a Cloudflare challenge page"""
        cloudflare_indicators = [
            "just a moment",
            "cloudflare",
            "checking your browser",
            "please wait",
            "security check",
            "ray id"
        ]
        
        if status_code == 403:
            response_lower = response_text.lower()
            return any(indicator in response_lower for indicator in cloudflare_indicators)
        
        return False

    def update_api_status(self) -> None:
        if self.send_to_api_checkbox.isChecked():
            if self.ping_api():
                self.update_bottom_info("api_connection", "API Connected")
                self.update_api_indicator(True)
            else:
                self.update_bottom_info("api_connection", "Error API not connected")
                self.update_api_indicator(False)
        else:
            self.update_bottom_info("api_connection", "API Disabled")
            self.update_api_indicator(False)

    def on_game_mode_changed(self, mode_msg: str) -> None:
        self.update_bottom_info("game_mode", mode_msg)
        
        if "Monitoring game mode:" in mode_msg:
            mode_name = mode_msg.replace("Monitoring game mode:", "").strip()
        else:
            mode_name = mode_msg.strip()
        
        if hasattr(self, 'game_mode_display'):
            self.game_mode_display.setText(f"Mode: {mode_name}")
            
            if mode_name != "Unknown":
                if hasattr(self, 'game_mode_indicator'):
                    self.game_mode_indicator.setStyleSheet(
                        "QLabel { background-color: #00ff41; border-radius: 6px; border: 1px solid #00cc33; }"
                    )
                self.game_mode_display.setStyleSheet(
                    "QLabel { color: #00ff41; font-size: 11px; font-weight: bold; background: transparent; border: none; }"
                )
            else:
                if hasattr(self, 'game_mode_indicator'):
                    self.game_mode_indicator.setStyleSheet(
                        "QLabel { background-color: #666666; border-radius: 6px; border: 1px solid #444444; }"
                    )
                self.game_mode_display.setStyleSheet(
                    "QLabel { color: #666666; font-size: 11px; font-weight: bold; background: transparent; border: none; }"
                )

    def on_kill_detected(self, readout: str, attacker: str) -> None:
        self.append_kill_readout(readout)
        if self.kill_sound_enabled:
            self.kill_sound_effect.setSource(QUrl.fromLocalFile(self.kill_sound_path))
            self.kill_sound_effect.setVolume(self.kill_sound_volume / 100.0)
            self.kill_sound_effect.play()

    def on_death_detected(self, readout: str, attacker: str) -> None:
        self.append_death_readout(readout)
        if self.death_sound_enabled:
            self.death_sound_effect.setSource(QUrl.fromLocalFile(self.death_sound_path))
            self.death_sound_effect.setVolume(self.death_sound_volume / 100.0)
            self.death_sound_effect.play()

    def export_logs(self) -> None:
        """Export the kill/death log entries to an HTML file."""
        if not self.kill_display.document().isEmpty():
            options = QFileDialog.Options()
            current_date = datetime.now().strftime("%Y-%m-%d")
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Logs", f"SCTool_Logs_{current_date}.html",
                "HTML Files (*.html);;All Files (*)", options=options
            )
            
            if file_path:
                try:
                    html_content = f"""<!DOCTYPE html>
                                        <html>
                                        <head>
                                            <meta charset="UTF-8">
                                            <title>SCTool Killfeed Export - {current_date}</title>
                                            <style>
                                                body {{
                                                    background-color: #0d0d0d;
                                                    color: #f0f0f0;
                                                    font-family: 'Segoe UI', Arial, sans-serif;
                                                    margin: 20px;
                                                    padding: 0;
                                                }}
                                                .header {{
                                                    background-color: #151515;
                                                    padding: 15px;
                                                    margin-bottom: 20px;
                                                    border-radius: 10px;
                                                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
                                                }}
                                                .header h1 {{
                                                    color: #f04747;
                                                    margin: 0;
                                                    font-size: 24px;
                                                }}
                                                .header p {{
                                                    margin: 5px 0 0 0;
                                                    color: #aaaaaa;
                                                }}
                                                a {{
                                                    color: #f04747;
                                                    text-decoration: none;
                                                }}
                                                a:hover {{
                                                    text-decoration: underline;
                                                }}
                                            </style>
                                        </head>
                                        <body>
                                            <div class="header">
                                                <h1>{t("SCTool Killfeed Export")}</h1>
                                                <p>{t("Date")}: {current_date}</p>
                                                <p>{t("User")}: {self.local_user_name or t("Unknown")}</p>
                                                <p>{t("Session Stats")}: {t("Kills")}: {self.kill_count} | {t("Deaths")}: {self.death_count}</p>
                                            </div>
                                            {self.kill_display.toHtml()}
                                        </body>
                                        </html>
                                    """

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    self.show_temporary_popup(f"Logs exported successfully to {file_path}")
                    
                    try:
                        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                    except:
                        pass
                        
                except Exception as e:
                    logging.error(f"Error exporting logs: {e}")
                    self.showCustomMessageBox("Export Error", f"Failed to export logs: {str(e)}", QMessageBox.Critical)
        else:
            self.showCustomMessageBox(t("Nothing to Export"), t("There are no logs to export."), QMessageBox.Information)

    def export_debug_logs(self) -> None:
        """Export debug logs and diagnostic information for troubleshooting"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Debug Information", f"SCTool_Debug_{current_date}.txt",
                "Text Files (*.txt);;All Files (*)", options=options
            )
            
            if file_path:
                debug_content = []
                
                debug_content.append(self.generate_api_diagnostic_report())
                debug_content.append("\n" + "="*60 + "\n")
                
                debug_content.append("CURRENT CONFIGURATION:\n")
                config_info = {
                    "API Key Set": bool(getattr(self, 'api_key', None)),
                    "API Endpoint": getattr(self, 'api_endpoint', 'Not set'),
                    "Send to API": getattr(self, 'send_to_api_checkbox', None) and self.send_to_api_checkbox.isChecked() if hasattr(self, 'send_to_api_checkbox') else False,
                    "Twitch Enabled": getattr(self, 'twitch_enabled', False),
                    "Local Username": getattr(self, 'local_user_name', 'Not set'),
                    "Kill Count": getattr(self, 'kill_count', 0),
                    "Death Count": getattr(self, 'death_count', 0),
                }
                for key, value in config_info.items():
                    debug_content.append(f"  {key}: {value}\n")
                
                debug_content.append("\n" + "="*60 + "\n")
                
                debug_content.append("RECENT LOG FILE CONTENT (last 50 lines):\n")
                try:
                    log_file_path = os.path.join(TRACKER_DIR, "kill_logger.log")
                    if os.path.exists(log_file_path):
                        with open(log_file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            recent_lines = lines[-50:] if len(lines) > 50 else lines
                            debug_content.extend(recent_lines)
                    else:
                        debug_content.append("Log file not found\n")
                except Exception as e:
                    debug_content.append(f"Error reading log file: {e}\n")
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(debug_content)
                
                self.show_temporary_popup(f"Debug information exported to {file_path}")
                
                clipboard = QApplication.clipboard()
                clipboard.setText(''.join(debug_content))
                
                info_box = QMessageBox(self)
                info_box.setWindowTitle("Debug Export Complete")
                info_box.setIcon(QMessageBox.Information)
                info_box.setText(
                    f"Debug information has been:\n\n"
                    f"• Saved to: {file_path}\n"
                    f"• Copied to clipboard\n\n"
                    f"You can now share this information with support."
                )
                info_box.exec_()
                
        except Exception as e:
            logging.error(f"Error exporting debug logs: {e}")
            self.showCustomMessageBox("Export Error", f"Failed to export debug logs: {str(e)}", QMessageBox.Critical)

    def auto_update(self, latest_version: str, download_url: str) -> None:
        """Download and install the latest version of the application without requiring admin rights"""      
        try:
            progress = QProgressDialog("Downloading update...", "Cancel", 0, 100, self)
            progress.setWindowTitle(f"Updating to v{latest_version}")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            
            auto_update_url = "https://starcitizentool.com/api/v1/download-update"
            logging.info(f"Using auto-update API endpoint: {auto_update_url}")
            
            user_temp_dir = os.path.join(TRACKER_DIR, "Updates")
            os.makedirs(user_temp_dir, exist_ok=True)
            downloaded_file = os.path.join(user_temp_dir, f"SCTool_Killfeed_{latest_version}_Setup.exe")
            
            headers = {
                'User-Agent': self.user_agent,
                'X-Client-ID': self.__client_id__,
                'X-Client-Version': self.__version__
            }
            
            logging.info(f"Downloading update from: {auto_update_url}")
            download_response = requests.get(auto_update_url, headers=headers, stream=True, timeout=30)
            download_response.raise_for_status()
            file_size = int(download_response.headers.get('Content-Length', 0))
            logging.info(f"Update file size: {file_size} bytes")
            
            downloaded_size = 0
            with open(downloaded_file, 'wb') as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    if progress.wasCanceled():
                        logging.info("Update canceled by user")
                        if os.path.exists(downloaded_file):
                            os.remove(downloaded_file)
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if file_size > 0:
                            percent = int((downloaded_size / file_size) * 100)
                            progress.setValue(percent)
            
            if os.path.getsize(downloaded_file) < 1000000:
                raise Exception("Downloaded file appears incomplete (too small)")
                
            progress.setValue(100)
            self.save_config()
            launcher_file = os.path.join(user_temp_dir, "update_launcher.bat")
            with open(launcher_file, 'w') as f:
                f.write('@echo off\n')
                f.write('echo SCTool Tracker Update\n')
                f.write('ping 127.0.0.1 -n 4 > nul\n')
                f.write(f'echo Running update: {downloaded_file}\n')
                f.write(f'start "" "{downloaded_file}"\n')
                f.write('echo Update process complete\n')
                f.write('exit\n')
            
            self.showCustomMessageBox(
                "Update Ready",
                "The update has been downloaded and will start automatically after you close this application.",
                QMessageBox.Information
            )

            subprocess.Popen(['cmd', '/c', 'start', '/min', '', launcher_file], 
                            shell=True,
                            stdin=None, stdout=None, stderr=None,
                            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
            os._exit(0)

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error during update: {e}")
            self.showCustomMessageBox(
                "Update Failed",
                f"Network error: {str(e)}\n\nPlease update manually from:\nhttps://starcitizentool.com/download-sctool",
                QMessageBox.Critical
            )
        except Exception as e:
            logging.error(f"Auto-update failed: {e}")
            self.showCustomMessageBox(
                "Update Failed",
                f"Could not update automatically: {str(e)}\n\nPlease update manually from:\nhttps://starcitizentool.com/download-sctool",                
                QMessageBox.Critical
            )

    def delete_local_kills(self):
        if os.path.isfile(self.kills_local_file):
            try:
                os.remove(self.kills_local_file)
                logging.info("Local kills JSON removed on close.")
            except Exception as e:
                logging.error(f"Failed to delete local kills JSON: {e}")

    def delete_kill_logger_log(self) -> None:
        try:
            if os.path.isfile(LOG_FILE):
                os.remove(LOG_FILE)
        except Exception as e:
            logging.error(f"Failed to delete kill_logger.log: {e}")

    def showCustomMessageBox(self, title: str, message: str, icon: QMessageBox.Icon = QMessageBox.Information) -> None:
        """Show a custom styled message box"""
        from utlity import styled_message_box
        msg_box = styled_message_box(self, title, message, icon)
        msg_box.exec_()

    def handle_api_response(self, message: str, local_key: str, timestamp: str, response_data: dict = None) -> None:
        normalized_message = message.strip().lower()
        
        if response_data and "kill" in response_data and isinstance(response_data["kill"], dict):
            kill_id = response_data["kill"].get("id")
            if kill_id and local_key in self.local_kills:
                self.local_kills[local_key]["api_kill_id"] = kill_id
                logging.info(f"Stored API kill ID {kill_id} for local key: {local_key}")
                self.save_local_kills()

        if "npc kill not logged" in normalized_message or "npc not logged" in normalized_message:
            logging.info(f"API identified NPC kill: {local_key}")

            if local_key in self.local_kills and "readout" in self.local_kills[local_key]:
                readout_to_remove = self.local_kills[local_key]["readout"]
                
                html_content = self.kill_display.toHtml()
                
                if readout_to_remove in html_content:
                    new_html = html_content.replace(readout_to_remove, "")
                    self.kill_display.setHtml(new_html)
                    self.kill_count -= 1
                    if self.kill_count < 0:
                        self.kill_count = 0
                    self.update_kill_death_stats()
                    logging.info(f"Removed NPC kill from display and adjusted kill count to {self.kill_count}")

                del self.local_kills[local_key]
                self.save_local_kills()
                logging.info(f"Removed NPC kill from local storage: {local_key}")
            return

        ignore_responses = {"subside kill not logged.", "self kill not logged."}
        if normalized_message in ignore_responses:
            logging.info(f"Ignored kill event for {local_key} with message: {message}")
            return
            
        if local_key in self.local_kills:
            self.local_kills[local_key]["api_response"] = message
            logging.info(f"[{timestamp}] Updated local kill {local_key} with API response: {message}")
            self.save_local_kills()

    def append_kill_readout(self, text: str) -> None:
        is_kill = "YOU KILLED" in text
        is_death = "YOU DIED" in text
        
        if is_kill:
            self.kill_count += 1
        elif is_death:
            self.death_count += 1
        
        self.update_kill_death_stats()
        
        cursor = self.kill_display.textCursor()
        cursor.movePosition(cursor.End)
        self.kill_display.setTextCursor(cursor)

        self.kill_display.append(text)
        
        if self.last_animation_timer:
            self.last_animation_timer.stop()
            
        highlight_style = """
            <style type='text/css'>
                @keyframes fadeIn {
                    0% { opacity: 0; transform: translateY(-10px); }
                    100% { opacity: 1; transform: translateY(0); }
                }
                .newEntry {
                    animation: fadeIn 0.5s ease-out;
                }
            </style>
        """

        self.kill_display.verticalScrollBar().setValue(
            self.kill_display.verticalScrollBar().maximum()
        )

    def append_kill_readout_no_count(self, text: str) -> None:
        """Append kill readout to display without incrementing kill/death counts"""
        cursor = self.kill_display.textCursor()
        cursor.movePosition(cursor.End)
        self.kill_display.setTextCursor(cursor)

        self.kill_display.append(text)
        
        if self.last_animation_timer:
            self.last_animation_timer.stop()
            
        highlight_style = """
            <style type='text/css'>
                @keyframes fadeIn {
                    0% { opacity: 0; transform: translateY(-10px); }
                    100% { opacity: 1; transform: translateY(0); }
                }
                .newEntry {
                    animation: fadeIn 0.5s ease-out;
                }
            </style>
        """

        self.kill_display.verticalScrollBar().setValue(
            self.kill_display.verticalScrollBar().maximum()
        )

    def append_death_readout(self, text: str) -> None:
        """Append death readout to display and increment death count"""
        self.death_count += 1
        self.update_kill_death_stats()
        
        cursor = self.kill_display.textCursor()
        cursor.movePosition(cursor.End)
        self.kill_display.setTextCursor(cursor)

        self.kill_display.append(text)
        
        if self.last_animation_timer:
            self.last_animation_timer.stop()
            
        highlight_style = """
            <style type='text/css'>
                @keyframes fadeIn {
                    0% { opacity: 0; transform: translateY(-10px); }
                    100% { opacity: 1; transform: translateY(0); }
                }
                .newEntry {
                    animation: fadeIn 0.5s ease-out;
                }
            </style>
        """

        self.kill_display.verticalScrollBar().setValue(
            self.kill_display.verticalScrollBar().maximum()
        )

    def fetch_user_image(self, username: str) -> None:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            url = f"https://robertsspaceindustries.com/citizens/{quote(username)}"
            response = SESSION.get(url, timeout=10, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                profile_img = soup.select_one('.profile.left-col .inner.clearfix .thumb img')
                
                if profile_img and profile_img.get('src'):
                    image_url = profile_img.get('src')
                    if image_url.startswith('/'):
                        image_url = f"https://robertsspaceindustries.com{image_url}"
                    
                    img_response = SESSION.get(image_url, timeout=10, headers=headers)
                    if img_response.status_code == 200:
                        pixmap = self.create_circular_pixmap_from_data(img_response.content)
                        self.user_profile_image.setPixmap(pixmap)
                        logging.info(f"Successfully loaded profile image for {username}")
                        return
                    else:
                        logging.warning(f"Could not fetch image from {image_url}, status code: {img_response.status_code}")
                else:
                    logging.warning(f"Could not find profile image for user {username}")
            else:
                logging.warning(f"Failed to fetch profile page for {username}, status code: {response.status_code}")
        
        except Exception as e:
            logging.error(f"Error fetching user image for {username}: {e}")

    def save_local_kills(self):
        try:
            with open(self.kills_local_file, 'w', encoding='utf-8') as f:
                json.dump(self.local_kills, f, indent=4)
            logging.info(f"Saved {len(self.local_kills)} kills to local JSON.")
        except Exception as e:
            logging.error(f"Failed to save local kills: {e}")

    def check_for_updates(self, show_optional=False) -> None:
         """Check for newer versions of the application with proper minimum version handling
         
         Args:
             show_optional (bool): If True, shows optional update dialogs. If False, only shows required updates.
         """
         try:
             update_url = "https://starcitizentool.com/api/v1/check-update"
             headers = {
                 'User-Agent': self.user_agent,
                 'X-Client-ID': self.__client_id__,
                 'X-Client-Version': self.__version__
             }
             
             params = {
                 'version': self.__version__
             }
 
             logging.info(f"Checking for updates... Current version: {self.__version__}")
             
             response = requests.get(update_url, headers=headers, params=params, timeout=10)
             
             if response.status_code == 200:
                 data = response.json()
                 
                 latest_version = data.get('latest_version')
                 minimum_required_version = data.get('minimum_required_version')
                 update_available = data.get('update_available', False)
                 update_required = data.get('update_required', False)
                 update_optional = data.get('update_optional', False)
                 download_url = data.get('download_url', 'https://starcitizentool.com/download-sctool')
                 
                 logging.info(f"Update check response: latest={latest_version}, minimum={minimum_required_version}, "
                             f"available={update_available}, required={update_required}, optional={update_optional}")
                 
                 if update_required:
                     logging.info(f"Forced update required: {latest_version} (current: {self.__version__})")
                     self.notify_forced_update(latest_version, minimum_required_version, download_url)
                 elif update_optional and show_optional:
                     logging.info(f"Optional update available: {latest_version} (current: {self.__version__})")
                     self.notify_optional_update(latest_version, download_url)
                 elif update_optional:
                     logging.info(f"Optional update available but not displaying: {latest_version} (current: {self.__version__})")
                 else:
                     logging.info(f"No updates available. Current version: {self.__version__}, Latest: {latest_version}")
             else:
                 logging.warning(f"Update check failed with status code: {response.status_code}")
         except Exception as e:
             logging.error(f"Error checking for updates: {e}")
 
    def notify_update(self, latest_version: str, download_url: str) -> None:
        update_message = (
            f"<p>A new version (<b>{latest_version}</b>) is available!</p>"
            f"<p>Please choose your update method:</p>"
        )

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(t("Update Required"))
        msg_box.setText(update_message)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setTextInteractionFlags(Qt.TextBrowserInteraction)

        auto_btn = msg_box.addButton("Auto Update", QMessageBox.AcceptRole)
        manual_btn = msg_box.addButton("Download Manually", QMessageBox.ActionRole)
        close_btn = msg_box.addButton("Exit Application", QMessageBox.RejectRole)

        msg_box.setDefaultButton(auto_btn)
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowCloseButtonHint)

        msg_box.exec_()

        clicked_button = msg_box.clickedButton()
        if clicked_button == auto_btn:
            self.auto_update(latest_version, download_url)
        elif clicked_button == manual_btn:
            QDesktopServices.openUrl(QUrl(download_url))
            self.save_config()
            sys.exit(0)
        else:
            self.save_config()
            import os
            os._exit(0)    

    def notify_optional_update(self, latest_version: str, download_url: str) -> None:
        """Show optional update dialog when user manually checks for updates"""
        update_message = (
            f"<p>A new version (<b>{latest_version}</b>) is available!</p>"
            f"<p><b>Your version:</b> {self.__version__}</p>"
            f"<p>You can update now or continue using your current version.</p>"
            f"<p>This update includes bug fixes and new features.</p>"
        )

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(t("Update Available"))
        msg_box.setText(update_message)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setTextInteractionFlags(Qt.TextBrowserInteraction)

        auto_btn = msg_box.addButton("Update Now", QMessageBox.AcceptRole)
        manual_btn = msg_box.addButton("Download Manually", QMessageBox.ActionRole)
        later_btn = msg_box.addButton("Remind Me Later", QMessageBox.RejectRole)

        msg_box.setDefaultButton(auto_btn)
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowCloseButtonHint)

        msg_box.exec_()
        
        clicked_button = msg_box.clickedButton()
        if clicked_button == auto_btn:
            self.auto_update(latest_version, download_url)
        elif clicked_button == manual_btn:
            QDesktopServices.openUrl(QUrl(download_url))
        else:
            logging.info("User chose to be reminded later about update")

    def notify_forced_update(self, latest_version: str, minimum_version: str, download_url: str) -> None:
        """Show forced update dialog when user's version is below minimum required"""
        update_message = (
            f"<h3 style='color: #ff6b6b;'>🚨 Update Required</h3>"
            f"<p><b>Your version:</b> {self.__version__}</p>"
            f"<p><b>Latest version:</b> {latest_version}</p>"
            f"<p><b>Minimum required:</b> {minimum_version}</p>"
            f"<hr>"
            f"<p style='color: #ff6b6b;'><b>Your version is no longer supported.</b></p>"
            f"<p>You must update to continue using SCTool Tracker.</p>"
            f"<p>📖 <a href='https://github.com/calebv2/SCTool-Tracker/blob/main/README.md'>View changelog and release notes</a></p>"
        )

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(t("Update Required"))
        msg_box.setText(update_message)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setTextInteractionFlags(Qt.TextBrowserInteraction)

        auto_btn = msg_box.addButton("Update Now", QMessageBox.AcceptRole)
        exit_btn = msg_box.addButton("Exit Application", QMessageBox.RejectRole)

        msg_box.setDefaultButton(auto_btn)
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowCloseButtonHint)

        msg_box.exec_()

        clicked_button = msg_box.clickedButton()
        if clicked_button == auto_btn:
            self.auto_update(latest_version, download_url)
        else:
            logging.info("User chose to exit instead of updating")
            self.save_config()
            import sys
            sys.exit(0)

    def check_for_updates_with_optional(self) -> None:
        """Enhanced version of check_for_updates that properly handles minimum version logic"""
        try:
            update_url = "https://starcitizentool.com/api/v1/check-update"
            headers = {
                'User-Agent': self.user_agent,
                'X-Client-ID': self.__client_id__,
                'X-Client-Version': self.__version__
            }
            
            params = {
                'version': self.__version__
            }

            logging.info(f"Checking for updates... Current version: {self.__version__}")
            
            response = requests.get(update_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                latest_version = data.get('latest_version')
                minimum_required_version = data.get('minimum_required_version')
                update_available = data.get('update_available', False)
                update_required = data.get('update_required', False)
                update_optional = data.get('update_optional', False)
                download_url = data.get('download_url', 'https://starcitizentool.com/download-sctool')
                
                logging.info(f"Update check response: latest={latest_version}, minimum={minimum_required_version}, "
                            f"available={update_available}, required={update_required}, optional={update_optional}")
                
                from utlity import show_forced_update_dialog, show_optional_update_dialog, show_up_to_date_dialog
                
                if update_required:
                    show_forced_update_dialog(self, latest_version, minimum_required_version, download_url)
                elif update_optional:
                    show_optional_update_dialog(self, latest_version, download_url)
                else:
                    show_up_to_date_dialog(self, self.__version__)
            else:
                logging.warning(f"Update check failed with status code: {response.status_code}")
                from utlity import show_update_check_failed_dialog
                show_update_check_failed_dialog(self)
        except Exception as e:
            logging.error(f"Error checking for updates: {e}")
            from utlity import show_update_check_failed_dialog
            show_update_check_failed_dialog(self)

    def on_ship_updated(self, ship: str) -> None:
        index = self.ship_combo.findText(ship)
        if index != -1:
            self.ship_combo.setCurrentIndex(index)
        else:
            self.ship_combo.addItem(ship)
            self.ship_combo.setCurrentIndex(self.ship_combo.count() - 1)
        
        self.update_current_ship_display(ship)
        
        if hasattr(self, 'update_overlay_stats'):
            self.update_overlay_stats()

    def update_current_ship_display(self, ship_name: str) -> None:
        """Update the current ship display in the UI"""
        if hasattr(self, 'current_ship_display'):
            display_text = ship_name if ship_name and ship_name != "No Ship" else "No Ship"
            self.current_ship_display.setText(display_text)
            
            if ship_name and ship_name != "No Ship":
                self.current_ship_display.setStyleSheet(
                    "QLabel { color: #00ff41; font-size: 11px; font-weight: bold; background: transparent; border: none; }"
                )
                if hasattr(self, 'ship_indicator'):
                    self.ship_indicator.setStyleSheet(
                        "QLabel { background-color: #00ff41; border-radius: 6px; border: 1px solid #00cc33; }"
                    )
            else:
                self.current_ship_display.setStyleSheet(
                    "QLabel { color: #666666; font-size: 11px; font-weight: bold; background: transparent; border: none; }"
                )
                if hasattr(self, 'ship_indicator'):
                    self.ship_indicator.setStyleSheet(
                        "QLabel { background-color: #666666; border-radius: 6px; border: 1px solid #444444; }"
                    )

    def handle_death_payload(self, payload: dict, timestamp: str, attacker: str, readout: str) -> None:
        """Process and send death events to the API"""
        data = payload.get('log_line', '')
        match = KILL_LOG_PATTERN.search(data)
        if not match:
            return

        victim = payload.get('victim_name', '')
        current_game_mode = payload.get('game_mode', 'Unknown')
        local_key = f"death_{timestamp}::{victim}::{current_game_mode}"

        if local_key in self.local_kills:
            self.show_temporary_popup("Death already in local JSON. Skipping API call.")
            return

        self.local_kills[local_key] = {
            "payload": payload,
            "timestamp": timestamp,
            "attacker": attacker,
            "readout": readout,
            "sent_to_api": False,
            "event_type": "death"
        }

        self.latest_death_info = {
            "victim": victim,
            "attacker": attacker,
            "weapon": payload.get('weapon', 'Unknown'),
            "location": payload.get('location', 'Unknown'),
            "timestamp": timestamp,
            "game_mode": current_game_mode
        }

        self.update_overlay_stats()

        if hasattr(self, 'game_overlay'):
            if self.game_overlay.display_mode == 'faded':
                self.game_overlay.show_death_notification(
                    attacker=attacker,
                    weapon=payload.get('weapon', 'Unknown'),
                    zone=payload.get('location', 'Unknown'),
                    game_mode=current_game_mode
                )
            elif self.game_overlay.display_mode == 'custom':
                self.game_overlay.show_custom_death_notification(
                    attacker=attacker,
                    weapon=payload.get('weapon', 'Unknown'),
                    zone=payload.get('location', 'Unknown'),
                    game_mode=current_game_mode
                )
        
        self.save_local_kills()
        if self.send_to_api_checkbox.isChecked():
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'X-API-Key': self.api_key,
                'User-Agent': self.user_agent,
                'X-Client-ID': self.__client_id__,
                'X-Client-Version': self.__version__
            }

            deaths_endpoint = f"{self.api_endpoint.replace('/kills', '/deaths')}"
            
            api_thread = ApiSenderThread(deaths_endpoint, headers, payload, local_key, parent=self)
            api_thread.apiResponse.connect(lambda msg: self.handle_api_response(msg, local_key, timestamp))
            api_thread.start()
        else:
            logging.info("Send to API is disabled; death payload not sent.")

    def update_api_with_clip_url(self, local_key: str, clip_url: str) -> None:
        """Send an update to the API with the clip URL for an existing kill"""
        if not self.send_to_api_checkbox.isChecked() or not self.api_key:
            logging.info("API updates disabled or no API key, skipping clip URL update")
            return
            
        if local_key not in self.local_kills:
            logging.warning(f"Cannot update clip URL for unknown kill: {local_key}")
            return
            
        kill_data = self.local_kills[local_key]
        victim_name = kill_data.get("victim", "")
        
        update_payload = {
            "clip_url": clip_url,
            "timestamp": kill_data.get("timestamp", ""),
            "victim_name": victim_name
        }
        
        api_kill_id = kill_data.get("api_kill_id")
        if api_kill_id:
            update_payload["kill_id"] = api_kill_id
        
        logging.info(f"Updating API with clip URL: {clip_url} for kill {local_key}, victim: {victim_name}")
        
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
            'User-Agent': self.user_agent
        }
        
        update_endpoint = f"{self.api_endpoint}/update-clip"
        
        try:
            logging.debug(f"Sending clip update payload: {update_payload}")
            
            response = requests.post(update_endpoint, json=update_payload, headers=headers, timeout=10)
            logging.info(f"API response for clip update: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                logging.info(f"Successfully updated API with clip URL for kill {local_key}")
                self.local_kills[local_key]["clip_url_sent_to_api"] = True
                self.save_local_kills()
            else:
                logging.error(f"Failed to update API with clip URL. Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            logging.error(f"Error updating API with clip URL: {e}")

    def on_tab_clicked(self):
        sender = self.sender()
        
        if self.settings_collapsed:
            self.settings_collapsed = False
            self.collapse_indicator.setText("▼")
        
        for i, button in enumerate(self.tab_buttons):
            checked = (button == sender)
            button.setChecked(checked)
            self.panels[i].setVisible(checked and not self.settings_collapsed)

    def toggle_stats_panel(self):
        self.stats_panel_visible = not self.stats_panel_visible
        if self.stats_panel_visible:
            self.stats_panel.setMaximumHeight(16777215)
            self.toggle_stats_btn.setText("▲")
        else:
            self.stats_panel.setMaximumHeight(0)
            self.toggle_stats_btn.setText("▼")
    
    def update_session_time(self):
        if not self.session_start_time:
            return
            
        elapsed = datetime.now() - self.session_start_time
        hours, remainder = divmod(elapsed.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        else:
            time_str = f"{int(minutes):02d}:{int(seconds):02d}"
            
        self.session_time_display.setText(time_str)
        self.update_overlay_stats()
    
    def update_kill_death_stats(self):
        self.kill_count_display.setText(str(self.kill_count))
        
        self.death_count_display.setText(str(self.death_count))

        if self.death_count > 0:
            ratio = self.kill_count / self.death_count
            self.kd_ratio_display.setText(f"{ratio:.2f}")
        else:
            if self.kill_count > 0:
                self.kd_ratio_display.setText(str(self.kill_count))
            else:
                self.kd_ratio_display.setText("--")

        self.update_overlay_stats()

    def update_overlay_stats(self):
        """Update the overlay with current stats"""
        if hasattr(self, 'game_overlay') and self.game_overlay.is_visible:
            session_time = "00:00"
            if hasattr(self, 'session_time_display'):
                session_time = self.session_time_display.text().replace('Session: ', '')
            
            ship = "Unknown"
            if hasattr(self, 'ship_combo'):
                ship = self.ship_combo.currentText() or "Unknown"

            game_mode = "Unknown"
            if hasattr(self, 'game_mode_display'):
                mode_text = self.game_mode_display.text()
                if mode_text.startswith('Mode: '):
                    game_mode = mode_text.replace('Mode: ', '')

            kill_streak = 0
            if hasattr(self, 'kill_count') and hasattr(self, 'death_count'):
                kill_streak = max(0, self.kill_count - self.death_count)
            
            self.game_overlay.update_stats(
                kills=self.kill_count,
                deaths=self.death_count,
                session_time=session_time,
                ship=ship,
                game_mode=game_mode,
                kill_streak=kill_streak,
                latest_kill=self.latest_kill_info,
                latest_death=self.latest_death_info
            )

    def update_monitor_indicator(self, is_monitoring: bool):
        if is_monitoring:
            self.monitoring_indicator.setStyleSheet(
                "QLabel { background-color: #4CAF50; border-radius: 8px; border: 1px solid #388E3C; }"
            )
        else:
            self.monitoring_indicator.setStyleSheet(
                "QLabel { background-color: #F44336; border-radius: 8px; border: 1px solid #D32F2F; }"
            )

    def update_api_indicator(self, is_connected: bool):
        if is_connected:
            self.api_indicator.setStyleSheet(
                "QLabel { background-color: #4CAF50; border-radius: 8px; border: 1px solid #388E3C; }"
            )
        else:
            self.api_indicator.setStyleSheet(
                "QLabel { background-color: #F44336; border-radius: 8px; border: 1px solid #D32F2F; }"
            )

    def update_twitch_indicator(self, is_connected: bool):
        if is_connected:
            self.twitch_indicator.setStyleSheet(
                "background-color: #9146FF; border-radius: 4px; padding: 4px;"
            )
            self.twitch_indicator.setText(t("Twitch Connected"))
        else:
            self.twitch_indicator.setStyleSheet(
                "background-color: #f04747; border-radius: 4px; padding: 4px;"
            )
            self.twitch_indicator.setText(t("Twitch Not Connected"))

    def update_bottom_info(self, key: str, message: str) -> None:
        self.persistent_info[key] = message

        if key == "monitoring":
            is_monitoring = "started" in message.lower()
            self.update_monitor_indicator(is_monitoring)
            if is_monitoring and not self.session_timer.isActive():
                self.session_start_time = datetime.now()
                self.session_timer.start(1000)
                self.kill_count = 0
                self.death_count = 0
                self.update_kill_death_stats()
            elif not is_monitoring and self.session_timer.isActive():
                self.session_timer.stop()
        
        elif key == "api_connection":
            is_connected = "connected" in message.lower()
            self.update_api_indicator(is_connected)
        
        elif key == "registered":
            if ": " in message:
                username = message.split(": ", 1)[1]
                self.user_display.setText(f"{username}")
        
        elif key == "game_mode":
            if ": " in message:
                mode = message.split(": ", 1)[1]
                self.game_mode_display.setText(f"Mode: {mode}")
                
        elif key == "twitch_connected":
            is_connected = "connected" in message.lower()
            self.update_twitch_indicator(is_connected)

    def toggle_settings_panels(self) -> None:
        self.settings_collapsed = not self.settings_collapsed
        self.collapse_indicator.setText("▼" if not self.settings_collapsed else "▲")
        
        if self.settings_collapsed:
            for panel in self.panels:
                panel.setVisible(False)
                
            for button in self.tab_buttons:
                button.setChecked(False)
        else:
            checked_found = False
            for i, button in enumerate(self.tab_buttons):
                if button.isChecked():
                    self.panels[i].setVisible(True)
                    checked_found = True
                    break
                    
            if not checked_found and self.tab_buttons:
                self.tab_buttons[0].setChecked(True)
                self.panels[0].setVisible(True)

    def create_form_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; }")
        return label

    def set_default_user_image(self) -> None:
        """Set a default profile image for the user"""
        try:
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(26, 26, 26)))
            painter.setPen(QPen(QColor(51, 51, 51), 2))
            painter.drawEllipse(2, 2, 60, 60)
            painter.setPen(QPen(QColor(150, 150, 150), 2))
            painter.drawText(QRect(0, 0, 64, 64), Qt.AlignCenter, "?")
            painter.end()
            self.user_profile_image.setPixmap(pixmap)
            
            default_image_url = "https://cdn.robertsspaceindustries.com/static/images/account/avatar_default_big.jpg"
            QTimer.singleShot(500, lambda: self.fetch_default_image(default_image_url))
        except Exception as e:
            logging.error(f"Error setting default user image: {e}")
            
    def fetch_default_image(self, url):
        """Fetch the default profile image from URL"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                
                circular_pixmap = QPixmap(64, 64)
                circular_pixmap.fill(Qt.transparent)
                painter = QPainter(circular_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath()
                path.addEllipse(2, 2, 60, 60)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, pixmap.scaled(64, 64, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                painter.end()
                
                self.user_profile_image.setPixmap(circular_pixmap)
        except Exception as e:
            logging.error(f"Error fetching default image: {e}")
    
    def closeEvent(self, event) -> None:
        if self.monitor_thread and self.monitor_thread.isRunning():
            reply = QMessageBox.question(
                self, t('Confirm Exit'),
                t("Monitoring is active. Stop and exit?"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.monitor_thread.stop()
                self.monitor_thread.wait(3000)
                self.monitor_thread = None
                self.start_button.setText(t("START MONITORING"))
            else:
                event.ignore()
                return
        if self.rescan_thread and self.rescan_thread.isRunning():
            self.rescan_thread.stop()
            self.rescan_thread.wait(3000)
            self.rescan_thread = None

        if hasattr(self, 'twitch_callback_timer') and self.twitch_callback_timer:
            self.twitch_callback_timer.stop()
            
        if hasattr(self, 'button_automation_callback_timer') and self.button_automation_callback_timer:
            self.button_automation_callback_timer.stop()
            
        if hasattr(self, 'session_timer') and self.session_timer:
            self.session_timer.stop()
            
        if hasattr(self, 'tray_stats_timer') and self.tray_stats_timer:
            self.tray_stats_timer.stop()

        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None

        if hasattr(self, 'twitch') and self.twitch:
            try:
                self.twitch.disconnect()
            except Exception as e:
                logging.error(f"Error disconnecting from Twitch during shutdown: {e}")

        if hasattr(self, 'ship_combo'):
            self.ship_combo.setCurrentText("No Ship")
            logging.info("Reset ship selection to 'No Ship' on application close")

        self.clips = {}
        self.clip_groups = {}
        self.save_config()
        
        self.delete_local_kills()
        self.delete_kill_logger_log()
        event.accept()

    def connect_to_twitch(self) -> None:
        """Initiate Twitch authentication process"""
        if not self.twitch_enabled:
            self.showCustomMessageBox("Twitch Integration", "Please enable Twitch integration first", QMessageBox.Information)
            return
            
        channel_name = self.twitch_channel_input.text().strip()
        if not channel_name:
            return
            
        self.twitch.set_broadcaster_name(channel_name)

        def auth_callback(success: bool) -> None:
            if success:
                self.update_bottom_info("twitch_connected", "Twitch Connected")
                self.save_config()
            else:
                self.update_bottom_info("twitch_connected", "Twitch Not Connected")
                self.showCustomMessageBox("Twitch Integration", 
                                        "Failed to connect to Twitch.\n\nMake sure you are entering your correct Twitch channel name.", 
                                        QMessageBox.Warning)
        
        self.twitch.authenticate(auth_callback)

    def disconnect_from_twitch(self) -> None:
        if self.twitch:
            try:
                self.twitch.disconnect()
                self.update_twitch_indicator(False)
                self.update_bottom_info("twitch_connected", "Twitch Not Connected")
                self.twitch_enabled = False
                self.twitch_enabled_checkbox.setChecked(False)
                self.show_temporary_popup("Disconnected from Twitch")
                self.save_config()
                logging.info("Disconnected from Twitch")
            except Exception as e:
                logging.error(f"Error disconnecting from Twitch: {e}")
                self.show_temporary_popup(f"Error disconnecting from Twitch: {e}")

    def on_twitch_enabled_changed(self, state: int) -> None:
        """Handle Twitch integration enabled/disabled"""
        self.twitch_enabled = (state == Qt.Checked)
        
        self.twitch_channel_input.setEnabled(self.twitch_enabled)
        
        if self.twitch_enabled:
            channel_name = self.twitch_channel_input.text().strip()
            if channel_name and channel_name != self.twitch.broadcaster_name:
                self.twitch.set_broadcaster_name(channel_name)

            if not self.twitch.is_ready():
                self.connect_to_twitch()
        else:
            self.update_bottom_info("twitch_connected", "Twitch Disabled")
        
        self.save_config()

    def on_auto_connect_twitch_changed(self, state: int) -> None:
        """Handle auto-connect to Twitch setting change"""
        self.auto_connect_twitch = (state == Qt.Checked)
        self.save_config()

    def on_create_clip_finished(self, clip_url: str, kill_data: Dict[str, Any]) -> None:
        """Callback when clip creation is finished"""
        local_key = kill_data.get("local_key")
        if not local_key or not clip_url:
            return

        self.clips[local_key] = clip_url
        self.save_config()

        readout = kill_data.get("readout", "")
        if readout:
            readout_with_clip = readout.replace("</body>",
                f'<div style="margin-top: 10px; text-align: center;">'
                f'<a href="{clip_url}" style="color:#6441A4; text-decoration:none; font-weight:bold; '
                f'padding:8px 16px; background-color:rgba(100, 65, 164, 0.2); border-radius:4px; '
                f'border:1px solid #6441A4;" target="_blank">'
                f'Watch Kill Clip</a></div></body>')
            
            text = self.kill_display.toHtml()
            text = text.replace(readout, readout_with_clip)
            self.kill_display.setHtml(text)
           
            logging.info(f"Added clip URL to kill display: {clip_url}")

            if local_key in self.local_kills:
                self.local_kills[local_key]["readout"] = readout_with_clip
                self.local_kills[local_key]["clip_url"] = clip_url
                self.save_local_kills()

                self.update_api_with_clip_url(local_key, clip_url)

    def create_circular_pixmap_from_data(self, image_data) -> QPixmap:
        """Create a circular pixmap from image data"""
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            result = QPixmap(64, 64)
            result.fill(Qt.transparent)
            
            painter = QPainter(result)
            painter.setRenderHint(QPainter.Antialiasing)

            path = QPainterPath()
            path.addEllipse(2, 2, 60, 60)

            painter.setBrush(QBrush(QColor(26, 26, 26)))
            painter.setPen(QPen(QColor(51, 51, 51), 2))
            painter.drawEllipse(2, 2, 60, 60)
            painter.setClipPath(path)
            painter.drawPixmap(2, 2, pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            painter.end()
            return result
        except Exception as e:
            logging.error(f"Error creating circular pixmap: {e}")
            
            result = QPixmap(64, 64)
            result.fill(Qt.transparent)
            
            painter = QPainter(result)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(26, 26, 26)))
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.drawEllipse(2, 2, 60, 60)
            painter.end()
            
            return result

    def update_user_profile_image(self, username: str) -> None:
        try:
            if not username or not username.strip():
                logging.warning("No username provided for profile image update")
                self.set_default_user_image()
                return
                
            username = username.strip()
            logging.info(f"Updating profile image for user: {username}")

            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(26, 26, 26)))
            painter.setPen(QPen(QColor(0, 255, 0), 2))
            painter.drawEllipse(2, 2, 60, 60)
            painter.setPen(QPen(QColor(200, 200, 200), 2))
            painter.drawText(QRect(0, 0, 64, 64), Qt.AlignCenter, username[0].upper())
            painter.end()
            self.user_profile_image.setPixmap(pixmap)

            QTimer.singleShot(100, lambda: self.fetch_user_image(username))
        except Exception as e:
            logging.error(f"Error updating user profile image for {username}: {e}")
            self.set_default_user_image()

    def create_kill_clip(self, kill_data: Dict[str, Any]) -> None:
        """Create a Twitch clip for a kill event or assign to an existing clip group"""
        if not self.twitch_enabled or not self.clip_creation_enabled:
            return
            
        if not self.twitch.is_ready():
            logging.warning("Tried to create clip but Twitch integration is not ready")
            return
            
        local_key = kill_data.get("local_key", "")
        timestamp = kill_data.get("timestamp", "")

        current_time = time.time()

        if (current_time - self.last_clip_creation_time) <= self.clip_group_window_seconds and self.current_clip_group_id:

            logging.info(f"Adding kill {local_key} to existing clip group {self.current_clip_group_id}")
            
            if self.current_clip_group_id not in self.clip_groups:
                self.clip_groups[self.current_clip_group_id] = []
                
            self.clip_groups[self.current_clip_group_id].append(local_key)

            if self.current_clip_group_id in self.clips:
                clip_url = self.clips[self.current_clip_group_id]
                if clip_url:
                    self.on_create_clip_finished(clip_url, kill_data)
                    logging.info(f"Applied existing clip URL to kill in same group: {local_key}")
                    return
            return

        self.last_clip_creation_time = current_time
        self.current_clip_group_id = f"clip_group_{timestamp}"
        self.clip_groups[self.current_clip_group_id] = [local_key]
        logging.info(f"Created new clip group {self.current_clip_group_id} for kill {local_key}")

        self.twitch.create_clip(kill_data, lambda url, data: self.handle_clip_created_for_group(url, data, self.current_clip_group_id))

    def handle_clip_created_for_group(self, clip_url: str, kill_data: Dict[str, Any], group_id: str) -> None:
        """Handle clip creation for a kill group - applies clip URL to all kills in the group"""
        if not clip_url or not group_id:
            return

        self.clips[group_id] = clip_url
        self.on_create_clip_finished(clip_url, kill_data)

        if group_id in self.clip_groups:
            for local_key in self.clip_groups[group_id]:
                if kill_data.get("local_key") == local_key:
                    continue

                if local_key in self.local_kills:
                    group_kill_data = {
                        "local_key": local_key,
                        "readout": self.local_kills[local_key].get("readout", "")
                    }
                    self.on_create_clip_finished(clip_url, group_kill_data)
                    logging.info(f"Applied group clip URL to kill: {local_key}")
        logging.info(f"Processed clip for kill group {group_id} with {len(self.clip_groups.get(group_id, []))} kills")

    def on_clip_creation_toggled(self, state: int) -> None:
        """Handle clip creation enabled/disabled"""
        self.clip_creation_enabled = (state == Qt.Checked)
        self.save_config()

    def on_chat_posting_toggled(self, state: int) -> None:
        """Handle chat posting enabled/disabled"""
        self.chat_posting_enabled = (state == Qt.Checked)
        logging.info(f"Twitch chat posting set to: {self.chat_posting_enabled}")
        self.save_config()

    def on_clip_delay_changed(self, value: int) -> None:
        """Handle clip delay slider value changes"""
        self.twitch.set_clip_delay(value)        
        self.clip_delay_value.setText(f"{value} seconds")
        logging.info(f"Clip delay set to {value} seconds")
        self.save_config()

    def toggle_overlay(self, enabled: bool) -> None:
        """Handle overlay enabled/disabled"""
        if hasattr(self, 'game_overlay'):
            if enabled:
                self.game_overlay.show_overlay()
               
                logging.info("Advanced game overlay enabled")
                self.update_overlay_stats()
            else:
                self.game_overlay.hide_overlay()
                logging.info("Advanced game overlay disabled")
        else:
            logging.warning("Advanced game overlay not initialized")

    def toggle_monitoring(self) -> None:
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait(3000)
            self.monitor_thread = None
            self.start_button.setText(t("START MONITORING"))
            self.start_button.setIcon(QIcon(resource_path("start_icon.png")))
            self.update_bottom_info("monitoring", "Monitoring stopped")
            self.update_bottom_info("api_connection", "")
            self.save_config()
            self.delete_local_kills()
            self.delete_kill_logger_log()
            self.rescan_button.setEnabled(False)
            self.set_default_user_image()
            
            if self.session_timer.isActive():
                self.session_timer.stop()
        else:
            self.update_bottom_info("api_connection", "")
            new_api_key = self.api_key_input.text().strip()
            new_log_path = self.log_path_input.text().strip()
            self.api_key = new_api_key
            self.local_user_name = ""
            self.registration_attempts = 0
            
            logging.info("=" * 60)
            logging.info("STARTING MONITORING SESSION")
            logging.info(f"Timestamp: {datetime.now().isoformat()}")
            logging.info(f"User attempting to start monitoring with API enabled: {self.send_to_api_checkbox.isChecked()}")
            logging.info(f"API key provided: {bool(new_api_key)}")
            logging.info(f"Log path provided: {bool(new_log_path) and os.path.isfile(new_log_path) if new_log_path else False}")
            logging.info("=" * 60)

            if self.send_to_api_checkbox.isChecked():
                if not new_api_key:
                    logging.warning("API connection attempt failed: No API key provided")
                    QMessageBox.warning(self, "Input Error", "Please enter your API key.")
                    return
                
                logging.info(f"Attempting API connection with endpoint: {getattr(self, 'api_endpoint', 'Not set')}")
                logging.info(f"API key length: {len(new_api_key) if new_api_key else 0} characters")
                logging.info(f"API key prefix: {new_api_key[:8] + '...' if new_api_key and len(new_api_key) > 8 else 'Too short'}")
                
                if not self.ping_api_with_retry():
                    error_details = {
                        "api_endpoint": getattr(self, 'api_endpoint', 'Not set'),
                        "api_key_provided": bool(new_api_key),
                        "api_key_length": len(new_api_key) if new_api_key else 0,
                        "user_agent": getattr(self, 'user_agent', 'Not set'),
                        "client_id": getattr(self, '__client_id__', 'Not set'),
                        "client_version": getattr(self, '__version__', 'Not set'),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    logging.error("API CONNECTION FAILURE - Please share this log with support:")
                    logging.error(f"Error details: {json.dumps(error_details, indent=2)}")
                    
                    try:
                        import socket
                        import urllib.parse
                        
                        if hasattr(self, 'api_endpoint') and self.api_endpoint:
                            parsed_url = urllib.parse.urlparse(self.api_endpoint)
                            hostname = parsed_url.hostname
                            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
                            
                            logging.info(f"Testing network connectivity to {hostname}:{port}")
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(5)
                            result = sock.connect_ex((hostname, port))
                            sock.close()
                            
                            if result == 0:
                                logging.info("Network connectivity to API host: SUCCESS")
                            else:
                                logging.error(f"Network connectivity to API host: FAILED (error code: {result})")
                        
                    except Exception as network_error:
                        logging.error(f"Network diagnostic failed: {network_error}")
                    
                    if hasattr(self, 'ping_api'):
                        logging.info("ping_api method is available")
                    else:
                        logging.error("ping_api method is not implemented")
                    
                    logging.info("Running detailed API key diagnostics...")
                    api_test_results = self.test_api_key_validity()
                    
                    logging.error("API KEY TEST RESULTS:")
                    for key, value in api_test_results.items():
                        logging.error(f"  {key}: {value}")
                    
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("API Connection Error")
                    msg_box.setIcon(QMessageBox.Critical)
                    
                    error_text = "Unable to connect to the API."
                    
                    is_cloudflare_issue = (api_test_results.get("status_code") == 403 and 
                                         any("cloudflare" in rec.lower() for rec in api_test_results.get("recommendations", [])))
                    
                    if is_cloudflare_issue:
                        error_text = "🛡️ CLOUDFLARE SECURITY BLOCKING ACCESS\n\n"
                        error_text += "This is NOT an API key problem!\n"
                        error_text += "Cloudflare's security system is blocking your requests."
                    elif api_test_results.get("status_code"):
                        error_text += f"\n\nServer returned status code: {api_test_results['status_code']}"
                        
                    if api_test_results.get("error_message") and not is_cloudflare_issue:
                        error_text += f"\nError: {api_test_results['error_message']}"
                    
                    msg_box.setText(error_text)
                    
                    if is_cloudflare_issue:
                        detail_text = "🚨 CLOUDFLARE SECURITY CHALLENGE DETECTED\n\n"
                        detail_text += "WHAT THIS MEANS:\n"
                        detail_text += "• Your API key is probably fine\n"
                        detail_text += "• Cloudflare thinks your requests look suspicious\n"
                        detail_text += "• This affects some users but not others\n"
                        detail_text += "• It's based on location, IP reputation, etc.\n\n"
                        detail_text += "SOLUTIONS (try in order):\n"
                        detail_text += "1. Try using a VPN from a different country\n"
                        detail_text += "2. Wait 30 minutes and try again\n"
                        detail_text += "3. Restart your router to get a new IP address\n"
                        detail_text += "4. Contact support with this diagnostic report\n\n"
                        detail_text += "NOTE: The developer needs to whitelist your IP or adjust Cloudflare settings.\n"
                    else:
                        detail_text = "TROUBLESHOOTING STEPS:\n\n"
                        if api_test_results.get("recommendations"):
                            for i, rec in enumerate(api_test_results["recommendations"], 1):
                                detail_text += f"{i}. {rec}\n"
                        else:
                            detail_text += "1. Check your network connection\n"
                            detail_text += "2. Verify your API key at https://starcitizentool.com/profile\n"
                            detail_text += "3. Try again in a few minutes\n"
                    
                    detail_text += "\nDIAGNOSTIC INFORMATION:\n"
                    detail_text += f"• Network connectivity to server: ✓ SUCCESS\n"
                    detail_text += f"• API key format valid: {'✓' if api_test_results.get('api_key_format_valid') else '✗'}\n"
                    detail_text += f"• API key length: {len(getattr(self, 'api_key', ''))}\n"
                    if api_test_results.get("status_code"):
                        detail_text += f"• Server response code: {api_test_results['status_code']}\n"
                    
                    detail_text += "\nUse the diagnostic buttons below to get more detailed information."
                    
                    msg_box.setDetailedText(detail_text)
                    
                    ok_btn = msg_box.addButton("OK", QMessageBox.AcceptRole)
                    diagnostic_btn = msg_box.addButton("Copy Quick Diagnostic", QMessageBox.ActionRole)
                    full_debug_btn = msg_box.addButton("Export Debug Info", QMessageBox.ActionRole)
                    
                    msg_box.setDefaultButton(ok_btn)
                    msg_box.exec_()
                    
                    clicked_btn = msg_box.clickedButton()
                    if clicked_btn == diagnostic_btn:
                        try:
                            diagnostic_report = self.generate_api_diagnostic_report()
                            clipboard = QApplication.clipboard()
                            clipboard.setText(diagnostic_report)
                            
                            info_box = QMessageBox(self)
                            info_box.setWindowTitle("Quick Diagnostic Copied")
                            info_box.setIcon(QMessageBox.Information)
                            info_box.setText(
                                "Quick diagnostic information has been copied to your clipboard.\n\n"
                                "Paste this when reporting the issue for faster troubleshooting."
                            )
                            info_box.exec_()
                            
                        except Exception as e:
                            logging.error(f"Failed to generate diagnostic report: {e}")
                            self.showCustomMessageBox("Error", "Failed to generate diagnostic report.")
                    
                    elif clicked_btn == full_debug_btn:
                        self.export_debug_logs()
                    
                    return
                
                logging.info("API connection successful")
                self.update_api_status()

            if self.twitch_enabled and self.clip_creation_enabled and not self.twitch_channel_input.text().strip():
                QMessageBox.warning(self, "Twitch Integration", t("Please enter a Twitch channel name in the Twitch settings to enable clip creation and chat messages."))

            if not new_log_path or not os.path.isfile(new_log_path):
                QMessageBox.warning(self, "Input Error", t("Please enter a valid path to your Game.log file."))
                return

            killer_ship = "No Ship"
            if os.path.isfile(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    killer_ship = config.get('killer_ship', 'No Ship')
                except Exception as e:
                    logging.error(f"Failed to load config for killer_ship: {e}")
                    killer_ship = "No Ship"

            self.monitor_thread = TailThread(new_log_path, CONFIG_FILE)
            self.monitor_thread.current_attacker_ship = killer_ship
            self.monitor_thread.ship_updated.connect(self.on_ship_updated)
            self.monitor_thread.payload_ready.connect(self.handle_payload)
            self.monitor_thread.death_payload_ready.connect(self.handle_death_payload)
            self.monitor_thread.kill_detected.connect(self.on_kill_detected)
            self.monitor_thread.death_detected.connect(self.on_death_detected)
            self.monitor_thread.player_registered.connect(self.on_player_registered)
            self.monitor_thread.game_mode_changed.connect(self.on_game_mode_changed)
            self.monitor_thread.start()
            self.on_ship_updated(killer_ship)
            self.start_button.setText(t("STOP MONITORING"))
            self.start_button.setIcon(QIcon(resource_path("stop_icon.png")))
            self.update_bottom_info("monitoring", "Monitoring started...")
            self.save_config()
            self.rescan_button.setEnabled(True)
            
            self.session_start_time = datetime.now()
            self.session_timer.start(1000)
            self.kill_count = 0
            self.death_count = 0
            self.update_kill_death_stats()

    def handle_payload(self, payload: dict, timestamp: str, attacker: str, readout: str) -> None:
        match = KILL_LOG_PATTERN.search(payload.get('log_line', ''))
        if not match:
            return

        if not payload.get("killer_ship"):
            payload["killer_ship"] = (
                self.monitor_thread.current_attacker_ship
                if self.monitor_thread and self.monitor_thread.current_attacker_ship
                else "No Ship"
            )

        if payload.get("killer_ship") == "No Ship":
            payload.pop("killer_ship")

        data = match.groupdict()
        victim = data.get('victim', '').lower().strip()
        current_game_mode = (
            self.monitor_thread.last_game_mode
            if self.monitor_thread and self.monitor_thread.last_game_mode
            else "Unknown"
        )
        local_key = f"{timestamp}::{victim}::{current_game_mode}"

        if local_key in self.local_kills:
            self.show_temporary_popup("Kill already in local JSON. Skipping API call.")
            return

        self.local_kills[local_key] = {
            "payload": payload,
            "timestamp": timestamp,
            "attacker": attacker,
            "readout": readout,
            "sent_to_api": False,
            "local_key": local_key
        }
        self.save_local_kills()

        kill_data = {
            "local_key": local_key,
            "victim": victim,
            "timestamp": timestamp,
            "readout": readout
        }

        self.latest_kill_info = {
            "victim": data.get('victim', 'Unknown'),
            "weapon": data.get('weapon', 'Unknown'),
            "location": data.get('zone', 'Unknown'),
            "timestamp": timestamp,
            "attacker": self.local_user_name,
            "game_mode": current_game_mode
        }

        self.update_overlay_stats()

        if hasattr(self, 'game_overlay'):
            if self.game_overlay.display_mode == 'faded':
                self.game_overlay.show_kill_notification(
                    victim=data.get('victim', 'Unknown'),
                    weapon=data.get('weapon', 'Unknown'),
                    zone=data.get('zone', 'Unknown'),
                    game_mode=current_game_mode
                )
            elif self.game_overlay.display_mode == 'custom':
                self.game_overlay.show_custom_kill_notification(
                    victim=data.get('victim', 'Unknown'),
                    weapon=data.get('weapon', 'Unknown'),
                    zone=data.get('zone', 'Unknown'),
                    game_mode=current_game_mode
                )

        if self.twitch_enabled and self.twitch.is_ready():
            if self.clip_creation_enabled:
                self.create_kill_clip(kill_data)

            if self.chat_posting_enabled:
                rsi_url = f"https://robertsspaceindustries.com/en/citizens/{victim}"
                message = self.twitch_chat_message_template.format(
                    username=self.local_user_name,
                    victim=victim,
                    profile_url=rsi_url
                )
                try:
                    self.twitch.send_chat_message(message)
                except Exception as e:
                    logging.error(f"Error sending Twitch chat message: {e}")

        if hasattr(self, 'button_automation') and self.button_automation:
            try:
                self.button_automation.execute_kill_automation(kill_data)
            except Exception as e:
                logging.error(f"Error executing button automation: {e}")

        if self.send_to_api_checkbox.isChecked():
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key,
                'User-Agent': self.user_agent,
                'X-Client-ID': self.__client_id__,
                'X-Client-Version': self.__version__
            }
            api_thread = ApiSenderThread(self.api_endpoint, headers, payload, local_key, parent=self)
            api_thread.apiResponse.connect(lambda msg: self.handle_api_response(msg, local_key, timestamp))
            api_thread.start()
        else:
            logging.info("Send to API is disabled; kill payload not sent.")

    def browse_file(self) -> None:        
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Game.log File", "",
            "Log Files (*.log);;All Files (*)",
            options=options
        )
        if file_path:
            self.log_path_input.setText(file_path)
            
    def load_ship_options(self) -> None:
        ships_file = os.path.join(TRACKER_DIR, "ships.json")
        
        if not os.path.exists(ships_file):
            app_ships_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ships.json")
            if os.path.exists(app_ships_file):
                try:
                    shutil.copy2(app_ships_file, ships_file)
                    logging.info(f"Copied ships.json from {app_ships_file} to {ships_file}")
                except Exception as e:
                    logging.error(f"Error copying ships.json: {e}")
        
        self.ship_combo.clear()
        try:
            if os.path.exists(ships_file):
                with open(ships_file, 'r', encoding='utf-8') as f:
                    ships_data = json.load(f)
                if isinstance(ships_data, dict) and "ships" in ships_data:
                    ships = ships_data["ships"]
                    if isinstance(ships, list) and ships:
                        self.ship_combo.addItems(ships)
        except Exception as e:
            logging.error(f"Error loading ship options from {ships_file}: {e}")
            
    def show_temporary_popup(self, message, duration=2000):
        """Show a stylish temporary popup message that fades out"""
        popup = QFrame(self)

        border_radius = ScreenScaler.scale_size(8, self.scale_factor)
        popup.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(34, 34, 34, 220);
                border: 1px solid #444444;
                border-radius: {border_radius}px;
            }}
        """)
        popup.setFrameShape(QFrame.StyledPanel)
        
        layout = QVBoxLayout(popup)

        margin = ScreenScaler.scale_size(10, self.scale_factor)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        top_row = QHBoxLayout()
        label = QLabel(message)

        font_size = ScreenScaler.scale_font_size(14, self.scale_factor)
        padding = ScreenScaler.scale_size(10, self.scale_factor)
        label.setStyleSheet(f"color: #ffffff; font-size: {font_size}px; background: transparent; padding: {padding}px;")
        label.setAlignment(Qt.AlignCenter)
        top_row.addWidget(label, 1)

        close_btn_size = ScreenScaler.scale_size(20, self.scale_factor)
        close_btn = QPushButton("×")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                color: #aaaaaa;
                font-size: {ScreenScaler.scale_font_size(16, self.scale_factor)}px;
                font-weight: bold;
                border: none;
                background: transparent;
                width: {close_btn_size}px;
                height: {close_btn_size}px;
            }}
            QPushButton:hover {{
                color: #ffffff;
            }}
        """)
        close_btn.setFixedSize(close_btn_size, close_btn_size)
        close_btn.clicked.connect(popup.hide)
        top_row.addWidget(close_btn)
        layout.addLayout(top_row)
        
        popup_width = ScreenScaler.scale_size(300, self.scale_factor)
        popup_height = ScreenScaler.scale_size(100, self.scale_factor)
        
        popup.setGeometry(
            (self.width() - popup_width) // 2,
            (self.height() - popup_height) // 2,
            popup_width, popup_height
        )
        popup.show()
        
        self.popup_opacity = QGraphicsOpacityEffect(popup)
        popup.setGraphicsEffect(self.popup_opacity)
        self.popup_opacity.setOpacity(1.0)
        
        self.fade_animation = QPropertyAnimation(self.popup_opacity, b"opacity")
        self.fade_animation.setDuration(duration)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutQuad)
        self.fade_animation.finished.connect(popup.deleteLater)
        
        QTimer.singleShot(500, self.fade_animation.start)

    def on_ship_combo_changed(self, new_ship: str) -> None:
        self.save_config()
        if self.monitor_thread and self.monitor_thread.isRunning():
            new_ship = new_ship.strip()
            if not new_ship:
                new_ship = "No Ship"
            self.monitor_thread.current_attacker_ship = new_ship
            self.monitor_thread.update_config_killer_ship(new_ship)

        self.update_current_ship_display(new_ship)

        if hasattr(self, 'update_overlay_stats'):
            self.update_overlay_stats()

    def on_kill_sound_toggled(self, state: int) -> None:
        self.kill_sound_enabled = (state == Qt.Checked)
        self.save_config()

    def on_kill_sound_file_browse(self) -> None:
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Kill Sound File", "",
            "Audio Files (*.wav *.mp3 *.ogg);;All Files (*)",
            options=options
        )
        if file_path:
            self.kill_sound_path = file_path
            self.kill_sound_path_input.setText(file_path)
            self.save_config()

    def on_kill_sound_volume_changed(self, value: int) -> None:
        self.kill_sound_volume = value
        self.save_config()

    def test_kill_sound(self) -> None:
        """Test the selected kill sound with current volume settings."""
        sound_path = self.kill_sound_path_input.text().strip()
        
        if not sound_path:
            QMessageBox.warning(self, "No Sound File", "Please select a sound file first.")
            return
            
        if not os.path.exists(sound_path):
            QMessageBox.warning(self, "File Not Found", f"The sound file '{sound_path}' was not found.")
            return
            
        try:
            self.kill_sound_effect.setSource(QUrl.fromLocalFile(sound_path))
            self.kill_sound_effect.setVolume(self.kill_sound_volume / 100.0)
            self.kill_sound_effect.play()
        except Exception as e:
            QMessageBox.critical(self, "Sound Test Failed", f"Failed to play sound file:\n{str(e)}")

    def on_death_sound_toggled(self, state: int) -> None:
        self.death_sound_enabled = (state == Qt.Checked)
        self.save_config()

    def on_death_sound_file_browse(self) -> None:
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Death Sound File", "",
            "Audio Files (*.wav *.mp3 *.ogg);;All Files (*)",
            options=options
        )
        if file_path:
            self.death_sound_path = file_path
            self.death_sound_path_input.setText(file_path)
            self.save_config()

    def on_death_sound_volume_changed(self, value: int) -> None:
        self.death_sound_volume = value
        self.save_config()

    def test_death_sound(self) -> None:
        """Test the selected death sound with current volume settings."""
        sound_path = self.death_sound_path_input.text().strip()
        
        if not sound_path:
            QMessageBox.warning(self, "No Sound File", "Please select a sound file first.")
            return
            
        if not os.path.exists(sound_path):
            QMessageBox.warning(self, "File Not Found", f"The sound file '{sound_path}' was not found.")
            return
            
        try:
            self.death_sound_effect.setSource(QUrl.fromLocalFile(sound_path))
            self.death_sound_effect.setVolume(self.death_sound_volume / 100.0)
            self.death_sound_effect.play()
        except Exception as e:
            QMessageBox.critical(self, "Sound Test Failed", f"Failed to play sound file:\n{str(e)}")

    def on_minimize_to_tray_changed(self, state: int) -> None:
        """Handle minimize to tray checkbox state change"""
        self.minimize_to_tray = (state == Qt.Checked)
        self.save_config()
        logging.info(f"Minimize to tray set to: {self.minimize_to_tray}")

    def on_start_with_system_changed(self, state: int) -> None:
        """Handle start with system checkbox state change"""
        self.start_with_system = (state == Qt.Checked)
        self.setup_autostart(self.start_with_system)
        self.save_config()
        logging.info(f"Start with system set to: {self.start_with_system}")

    def changeEvent(self, event) -> None:
        """Handle window state change events for minimizing to tray"""
        if event.type() == 105:
            if self.windowState() & Qt.WindowMinimized:
                if self.minimize_to_tray:
                    QTimer.singleShot(0, self.hide_to_tray)
                if hasattr(self, 'game_overlay') and self.game_overlay and self.game_overlay.is_visible:
                    self.game_overlay.show()
                    self.game_overlay.raise_()
                    self.game_overlay.activateWindow()
                
        super().changeEvent(event)
    def hide_to_tray(self):
        """Hide main window to system tray"""
        self.hide()
        if hasattr(self, 'game_overlay') and self.game_overlay and self.game_overlay.is_visible:
            self.game_overlay.show()
            self.game_overlay.raise_()
    
    def show_from_tray(self) -> None:
        """Show the main window when activated from tray"""
        self.showNormal()
        self.activateWindow()
        if hasattr(self, 'game_overlay') and self.game_overlay and self.game_overlay.is_visible:
            self.game_overlay.show()
            self.game_overlay.raise_()
    def switch_page(self, index):
        """Switch to the specified page and update selected navigation button state"""
        self.content_stack.setCurrentIndex(index)
        
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)

    def resizeEvent(self, event) -> None:
        """Handle window resize events to adjust UI elements"""
        super().resizeEvent(event)

        if hasattr(self, 'ui_helper') and self.ui_helper:
            width = self.width()
            if width < 800:
                font_size = 10
            elif width < 1200:
                font_size = 12
            else:
                font_size = 14
                
            font_size = ScreenScaler.scale_font_size(font_size, self.scale_factor)

            if hasattr(self, 'kill_display'):
                font = self.kill_display.font()
                font.setPointSize(font_size)
                self.kill_display.setFont(font)

                if hasattr(self, 'log_path_input'):
                    min_width = ScreenScaler.scale_size(300, self.scale_factor)
                    self.log_path_input.setMinimumWidth(min_width)
                
    def update_ui_scaling(self) -> None:
        """Update UI elements according to current scale factor"""
        if not hasattr(self, 'scale_factor') or not hasattr(self, 'ui_helper'):
            _, _, self.scale_factor = ScreenScaler.get_screen_info()
            self.ui_helper = ResponsiveUIHelper(self)
            
        if hasattr(self, 'kill_display'):
            font = self.kill_display.font()
            font.setPointSize(ScreenScaler.scale_font_size(12, self.scale_factor))
            self.kill_display.setFont(font)
        
        if hasattr(self, 'log_path_input'):
            min_width = ScreenScaler.scale_size(300, self.scale_factor)
            self.log_path_input.setMinimumWidth(min_width)
        
        for panel in getattr(self, 'panels', []):
            if hasattr(panel, 'setMinimumHeight'):
                min_height = ScreenScaler.scale_size(200, self.scale_factor)
                panel.setMinimumHeight(min_height)
                
        for btn in getattr(self, 'nav_buttons', []):
            font = btn.font()
            font.setPointSize(ScreenScaler.scale_font_size(10, self.scale_factor))
            btn.setFont(font)
            
        self.apply_styles()

    def on_twitch_message_changed(self) -> None:
        """Handle Twitch chat message template changes"""
        self.twitch_chat_message_template = self.twitch_message_input.text()
        if not self.twitch_chat_message_template:
            self.twitch_chat_message_template = "🔫 {username} just killed {victim}! 🚀 {profile_url}"
            self.twitch_message_input.setText(self.twitch_chat_message_template)

        self.save_config()

    def handle_auto_connect_twitch(self) -> None:
        """Automatically connect to Twitch on startup if auto-connect is enabled"""
        if not self.auto_connect_twitch:
            logging.info("Auto-connect to Twitch is disabled")
            return
            
        if not self.twitch_enabled:
            logging.info("Auto-connect skipped: Twitch integration is disabled")
            return
            
        channel_name = self.twitch_channel_input.text().strip()
        if not channel_name:
            logging.warning("Auto-connect skipped: No Twitch channel name configured")
            return
            
        self.twitch.set_broadcaster_name(channel_name)
        
        if self.twitch.is_ready():
            logging.info("Twitch integration ready with existing credentials")
            self.update_bottom_info("twitch_connected", "Twitch Connected")
            return
        
        if hasattr(self.twitch, 'access_token') and self.twitch.access_token:
            logging.info("Twitch credentials found but not ready - may need manual re-authentication")
            self.update_bottom_info("twitch_connected", "Twitch Not Connected")
            return
        
        logging.info("No Twitch credentials found on startup - manual authentication required")
        self.update_bottom_info("twitch_connected", "Twitch Not Connected")

    def setup_translation_system(self) -> None:
        """Initialize the translation system and language selector"""
        try:
            if hasattr(self, 'config_file'):
                language_manager.load_language_preference(self.config_file)
            
            self.language_selector = LanguageSelector(self)
            
            if hasattr(self, 'content_stack'):
                self.add_language_selector_to_preferences()
            
            setup_auto_translation(self, self.language_selector)
            
            translate_application(self)
            
            logging.info("Translation system initialized with English text storage")
            
        except Exception as e:
            logging.error(f"Error setting up translation system: {e}")
    
    def force_translation_refresh(self):
        """Force a complete translation refresh - useful when translations get stuck"""
        try:
            logging.info(f"Forcing translation refresh for language: {language_manager.current_language}")
            
            from translation_utils import immediate_translate_application
            immediate_translate_application(self)
            
            if hasattr(self, 'language_selector') and self.language_selector:
                if hasattr(self.language_selector, 'force_refresh_translations'):
                    self.language_selector.force_refresh_translations()
            
            logging.info("Force translation refresh completed")
            return True
            
        except Exception as e:
            logging.error(f"Error in force_translation_refresh: {e}")
            return False
    
    def get_current_language_info(self):
        """Get information about the current language state for debugging"""
        try:
            info = {
                'current_language': language_manager.current_language,
                'available_languages': list(language_manager.get_available_languages().keys()),
                'translations_loaded': language_manager.current_language in language_manager.translations,
                'has_language_selector': hasattr(self, 'language_selector') and self.language_selector is not None
            }
            
            if info['translations_loaded'] and language_manager.current_language != 'en':
                translation_count = len(language_manager.translations[language_manager.current_language])
                info['translation_count'] = translation_count
            
            return info
            
        except Exception as e:
            logging.error(f"Error getting language info: {e}")
            return {'error': str(e)}
        
    def add_language_selector_to_preferences(self):
        """Add the language selector to the preferences section"""
        try:
            if hasattr(self, 'language_selector_container') and hasattr(self, 'language_selector_layout'):
                language_header = QLabel(t("Language:"))
                language_header.setStyleSheet(
                    "QLabel { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; font-weight: 500; }"
                )
                self.language_selector_layout.addWidget(language_header)

                selector_container = QWidget()
                selector_container.setStyleSheet("background: transparent; border: none;")
                selector_layout = QHBoxLayout(selector_container)
                selector_layout.setContentsMargins(30, 0, 0, 0)
                selector_layout.setSpacing(10)
                
                selector_layout.addWidget(self.language_selector)
                selector_layout.addStretch()
                
                self.language_selector_layout.addWidget(selector_container)
                
                language_desc = QLabel(t("Choose your preferred language for the application interface"))
                language_desc.setStyleSheet(
                    "QLabel { color: #999999; font-size: 12px; background: transparent; border: none; margin-left: 30px; }"
                )
                language_desc.setWordWrap(True)
                self.language_selector_layout.addWidget(language_desc)
                
                logging.info("Language selector added to preferences section")
            else:
                logging.error("Language selector container not found in preferences")
                
        except Exception as e:
            logging.error(f"Error adding language selector to preferences: {e}")

def style_form_label(label):
    label.setStyleSheet("QLabel { color: #cccccc; font-weight: 500; }")
    return label

def cleanup_log_file() -> None:
    try:
        logging.shutdown()

        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            try:
                handler.close()
                root_logger.removeHandler(handler)
            except Exception as e:
                print(f"Error closing handler: {e}")

        if os.path.isfile(LOG_FILE):
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    os.remove(LOG_FILE)
                    print(f"Successfully deleted {LOG_FILE}")
                    break
                except PermissionError:
                    if attempt < max_retries - 1:
                        print(f"File still in use, retrying in 0.5s... (attempt {attempt+1}/{max_retries})")
                        time.sleep(0.5)
                    else:
                        print(f"Could not delete {LOG_FILE} after {max_retries} attempts - file may still be locked")
                except Exception as e:
                    print(f"Error deleting {LOG_FILE}: {e}")
                    break
    except Exception as e:
        print(f"Exception during cleanup of {LOG_FILE}: {e}")

atexit.register(cleanup_log_file)

def main(start_minimized=False) -> None:
    if is_already_running():
        logging.info("Another instance of SCTool Killfeed is already running.")
        find_existing_window()
        sys.exit(0)

    app = QApplication(sys.argv)
    
    screen = QApplication.primaryScreen()
    if screen:
        screen_rect = screen.availableGeometry()
        logging.info(f"Screen resolution: {screen_rect.width()}x{screen_rect.height()}")
    
    gui = KillLoggerGUI()
    gui.check_for_updates()
    dark_title_bar_for_pyqt5(gui)
    
    if hasattr(gui, 'update_ui_scaling'):
        gui.update_ui_scaling()

    if start_minimized and gui.minimize_to_tray:
        logging.info("Starting application minimized to tray")
        global app_instance
        app_instance = gui
        gui.tray_icon.show()
    else:
        gui.show()
    
    sys.exit(app.exec_())