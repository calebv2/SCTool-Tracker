# Kill_form.py

import sys
import os
import json
import re
import base64
import atexit
import logging
import time
import requests
import ctypes
import webbrowser
from datetime import datetime
from packaging import version
from bs4 import BeautifulSoup
from urllib.parse import quote
from typing import Optional, Dict, Any, List

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLineEdit, QPushButton, QTextBrowser,
    QFileDialog, QVBoxLayout, QHBoxLayout, QMessageBox, QGroupBox, QCheckBox,
    QSlider, QFormLayout, QLabel, QComboBox, QDialog
)
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtCore import (
    Qt, QUrl, QTimer, QStandardPaths, QDir
)
from PyQt5.QtMultimedia import QSoundEffect

from Kill_thread import ApiSenderThread, TailThread, RescanThread, MissingKillsDialog
from kill_parser import KILL_LOG_PATTERN, CHROME_USER_AGENT

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

def fetch_player_details(playername: str) -> Dict[str, str]:
    if playername in PLAYER_DETAILS_CACHE:
        return PLAYER_DETAILS_CACHE[playername]

    details = {"enlistment_date": "None", "occupation": "None", "org_name": "None", "org_tag": "None"}
    try:
        url = f"https://robertsspaceindustries.com/citizens/{playername}"
        response = SESSION.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            enlistment_label = soup.find("span", class_="label", string="Enlisted")
            if enlistment_label:
                enlistment_date_elem = enlistment_label.find_next("strong", class_="value")
                if enlistment_date_elem:
                    details["enlistment_date"] = enlistment_date_elem.text.strip()

        api_url = "https://robertsspaceindustries.com/api/spectrum/search/member/autocomplete"
        autocomplete_name = playername[:-1] if len(playername) > 1 else playername
        payload = {"community_id": "1", "text": autocomplete_name}
        headers2 = {"Content-Type": "application/json"}
        response2 = SESSION.post(api_url, headers=headers2, json=payload, timeout=10)
        if response2.status_code == 200:
            data = response2.json()
            correct_player = None
            for member in data.get("data", {}).get("members", []):
                if member.get("nickname", "").lower() == playername.lower():
                    correct_player = member
                    break
            if correct_player:
                badges = correct_player.get("meta", {}).get("badges", [])
                for badge in badges:
                    if "url" in badge and "/orgs/" in badge["url"]:
                        details["org_name"] = badge.get("name", "None")
                        parts = badge["url"].split('/')
                        details["org_tag"] = parts[-1] if parts[-1] else "None"
                    elif "name" in badge and details["occupation"] == "None":
                        details["occupation"] = badge.get("name", "None")
        else:
            logging.error(f"Autocomplete API request failed for {playername} with status code {response2.status_code}")
    except Exception as e:
        logging.error(f"Error fetching player details for {playername}: {e}")

    PLAYER_DETAILS_CACHE[playername] = details
    return details

def fetch_victim_image_base64(victim_name: str) -> str:
    default_image_url = "https://cdn.robertsspaceindustries.com/static/images/account/avatar_default_big.jpg"
    url = f"https://robertsspaceindustries.com/citizens/{quote(victim_name)}"
    final_url = default_image_url
    try:
        response = SESSION.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            profile_pic = soup.select_one('.thumb img')
            if profile_pic and profile_pic.has_attr("src"):
                src = profile_pic['src']
                if src.startswith("http://") or src.startswith("https://"):
                    final_url = src
                else:
                    if not src.startswith("/"):
                        src = "/" + src
                    final_url = f"https://robertsspaceindustries.com{src}"
    except Exception as e:
        logging.error(f"Error determining victim image URL for {victim_name}: {e}")
        final_url = default_image_url
    try:
        r = SESSION.get(final_url, timeout=10)
        if r.status_code == 200:
            content_type = r.headers.get("Content-Type", "image/jpeg")
            if not content_type or "image" not in content_type:
                content_type = "image/jpeg"
            b64_data = base64.b64encode(r.content).decode("utf-8")
            return f"data:{content_type};base64,{b64_data}"
    except Exception as e:
        logging.error(f"Error fetching actual image data for {victim_name}: {e}")
    return default_image_url

class KillLoggerGUI(QMainWindow):
    __client_id__ = "kill_logger_client"
    __version__ = "3.6"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SCTool Killfeed 3.6")
        self.setWindowIcon(QIcon(resource_path("chris2.ico")))
        self.kill_count = 0
        self.monitor_thread: Optional[TailThread] = None
        self.rescan_thread: Optional[RescanThread] = None
        self.missing_kills_queue: List[dict] = []
        self.api_endpoint = "https://starcitizentool.com/api/v1/kills"
        self.user_agent = CHROME_USER_AGENT
        self.local_user_name = ""
        self.dark_mode_enabled = True
        self.kill_sound_enabled = False
        self.kill_sound_effect = QSoundEffect()
        self.kill_sound_path = resource_path("kill.wav")
        self.kill_sound_volume = 100
        self.api_key = ""
        self.registration_attempts = 0
        self.local_kills: Dict[str, bool] = {}
        self.kills_local_file = LOCAL_KILLS_FILE
        self.persistent_info = {
            "monitoring": "",
            "registered": "",
            "game_mode": "",
            "api_connection": ""
        }

        self.init_ui()
        self.load_config()
        self.load_local_kills()
        self.apply_styles()

    def init_ui(self) -> None:
        main_widget = QWidget()
        main_widget.setStyleSheet(
            "QWidget { background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #1a1a1a, stop:1 #0d0d0d); "
            "border: 1px solid #2a2a2a; border-radius: 8px; }"
        )
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        settings_group = QGroupBox()
        settings_layout = QFormLayout()
        settings_layout.setSpacing(10)
        settings_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        settings_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        
        self.send_to_api_checkbox = QCheckBox("Send Kills to API")
        self.send_to_api_checkbox.setChecked(True)
        self.send_to_api_checkbox.setStyleSheet(
            "QCheckBox { color: #ffffff; spacing: 5px; background: transparent; border: none; }"
            "QCheckBox::indicator { width: 16px; height: 16px; }"
            "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
            "QCheckBox::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 3px; }"
            "QCheckBox::indicator:checked:disabled { border: 1px solid #666666; background-color: #333333; border-radius: 3px; }"
        )
        settings_layout.addRow(self.send_to_api_checkbox)

        api_key_label = QLabel("API Key:")
        api_key_label.setStyleSheet("color: #ffffff; font-weight: bold; background: transparent; border: none;")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your API key here")
        self.api_key_input.setStyleSheet(
            "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 6px; "
            "border: 1px solid #2a2a2a; border-radius: 4px; }"
            "QLineEdit:hover, QLineEdit:focus { border-color: #f04747; }"
        )
        settings_layout.addRow(api_key_label, self.api_key_input)
        
        game_log_label = QLabel("Game.log Path:")
        game_log_label.setStyleSheet("color: #ffffff; font-weight: bold; background: transparent; border: none;")
        log_path_layout = QHBoxLayout()
        self.log_path_input = QLineEdit()
        self.log_path_input.setPlaceholderText("Enter path to your Game.log")
        self.log_path_input.setStyleSheet(
            "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 6px; "
            "border: 1px solid #2a2a2a; border-radius: 4px; }"
            "QLineEdit:hover, QLineEdit:focus { border-color: #f04747; }"
        )
        browse_log_btn = QPushButton("Browse")
        browse_log_btn.setIcon(QIcon(resource_path("browse_icon.png")))
        browse_log_btn.setStyleSheet(
            "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
            "border: 1px solid #2a2a2a; border-radius: 4px; padding: 6px; }"
            "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
        )
        browse_log_btn.clicked.connect(self.browse_file)
        log_path_layout.addWidget(self.log_path_input)
        log_path_layout.addWidget(browse_log_btn)
        settings_layout.addRow(game_log_label, log_path_layout)
        
        killer_ship_label = QLabel("Killer Ship:")
        killer_ship_label.setStyleSheet("color: #ffffff; font-weight: bold; background: transparent; border: none;")
        self.ship_combo = QComboBox()
        self.ship_combo.setEditable(True)
        self.load_ship_options()
        self.ship_combo.currentTextChanged.connect(self.on_ship_combo_changed)
        self.ship_combo.setStyleSheet(
            "QComboBox { background-color: #1e1e1e; color: #f0f0f0; padding: 6px; "
            "border: 1px solid #2a2a2a; border-radius: 4px; padding-right: 20px; }"
            "QComboBox:hover { border-color: #f04747; }"
            "QComboBox::drop-down { border: none; width: 20px; }"
            "QComboBox::down-arrow { width: 0; height: 0; border-left: 5px solid transparent; "
            "   border-right: 5px solid transparent; border-top: 5px solid #f04747; margin-right: 8px; }"
            "QComboBox QAbstractItemView { background-color: #1e1e1e; color: #f0f0f0; "
            "selection-background-color: #f04747; selection-color: white; border: 1px solid #2a2a2a; }"
            "QComboBox QScrollBar:vertical { background: #1a1a1a; width: 12px; margin: 0px; }"
            "QComboBox QScrollBar::handle:vertical { background: #2a2a2a; min-height: 20px; border-radius: 6px; }"
            "QComboBox QScrollBar::handle:vertical:hover { background: #f04747; }"
            "QComboBox QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
            "QComboBox QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }"
        )
        settings_layout.addRow(killer_ship_label, self.ship_combo)
        
        sound_group = QGroupBox()
        sound_layout = QFormLayout()
        sound_layout.setSpacing(10)
        sound_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        sound_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        sound_layout.setContentsMargins(10, 10, 10, 10)
        
        self.kill_sound_checkbox = QCheckBox("Enable Kill Sound")
        self.kill_sound_checkbox.setChecked(False)
        self.kill_sound_checkbox.stateChanged.connect(self.on_kill_sound_toggled)
        self.kill_sound_checkbox.setStyleSheet(
            "QCheckBox { color: #ffffff; spacing: 5px; background: transparent; border: none; }"
            "QCheckBox::indicator { width: 16px; height: 16px; }"
            "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
            "QCheckBox::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 3px; }"
            "QCheckBox::indicator:checked:disabled { border: 1px solid #666666; background-color: #333333; border-radius: 3px; }"
        )
        sound_layout.addRow(self.kill_sound_checkbox)

        sound_file_label = QLabel("Kill Sound File:")
        sound_file_label.setStyleSheet("color: #ffffff; font-weight: bold; background: transparent; border: none;")
        sound_path_layout = QHBoxLayout()
        self.kill_sound_path_input = QLineEdit()
        self.kill_sound_path_input.setText(self.kill_sound_path)
        self.kill_sound_path_input.setStyleSheet(
            "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 6px; "
            "border: 1px solid #2a2a2a; border-radius: 4px; }"
            "QLineEdit:hover, QLineEdit:focus { border-color: #f04747; }"
        )
        sound_browse_btn = QPushButton("Browse")
        sound_browse_btn.setStyleSheet(
            "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
            "border: 1px solid #2a2a2a; border-radius: 4px; padding: 6px; }"
            "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
        )
        sound_browse_btn.clicked.connect(self.on_kill_sound_file_browse)
        sound_path_layout.addWidget(self.kill_sound_path_input)
        sound_path_layout.addWidget(sound_browse_btn)
        sound_layout.addRow(sound_file_label, sound_path_layout)
        
        volume_label = QLabel("Volume:")
        volume_label.setStyleSheet("color: #ffffff; font-weight: bold; background: transparent; border: none;")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.kill_sound_volume)
        self.volume_slider.valueChanged.connect(self.on_kill_sound_volume_changed)
        self.volume_slider.setStyleSheet(
            "QSlider::groove:horizontal { border: 1px solid #2a2a2a; height: 10px; "
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a1a1a, stop:1 #2a2a2a); "
            "margin: 2px 0; border-radius: 5px; }"
            "QSlider::handle:horizontal { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #f04747, stop:1 #d03737); border: 1px solid #2a2a2a; "
            "width: 20px; height: 20px; margin: -6px 0; border-radius: 10px; }"
            "QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0 #d03737, stop:1 #f04747); border-radius: 5px; }"
            "QSlider::handle:horizontal:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #ff5757, stop:1 #e04747); border: 1px solid #f04747; }"
        )
        sound_layout.addRow(volume_label, self.volume_slider)
        
        sound_group.setLayout(sound_layout)
        sound_group.setStyleSheet(
            "QGroupBox { background-color: #0f0f0f; border: 1px solid #2a2a2a; border-radius: 6px; margin-top: 14px; padding-top: 16px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; color: #f04747; "
            "padding: 0 8px; background-color: #0f0f0f; font-weight: bold; }"
            "QLabel { background: transparent; border: none; }"
        )
        settings_layout.addRow(sound_group)
        
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Monitoring")
        self.start_button.setIcon(QIcon(resource_path("start_icon.png")))
        self.start_button.clicked.connect(self.toggle_monitoring)
        self.start_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
            "border-radius: 4px; padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #f04747, stop:1 #d03737); }"
            "QPushButton:pressed { background: #d03737; }"
        )
        button_layout.addWidget(self.start_button)
        
        self.rescan_button = QPushButton("Find Missed Kills")
        self.rescan_button.setIcon(QIcon(resource_path("search_icon.png")))
        self.rescan_button.clicked.connect(self.on_rescan_button_clicked)
        self.rescan_button.setEnabled(False)
        self.rescan_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
            "border-radius: 4px; padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #f04747, stop:1 #d03737); }"
            "QPushButton:pressed { background: #d03737; }"
        )
        button_layout.addWidget(self.rescan_button)
        
        self.files_button = QPushButton("SCTool Tracker Files")
        self.files_button.setIcon(QIcon(resource_path("files_icon.png")))
        self.files_button.clicked.connect(self.open_tracker_files)
        self.files_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #323232, stop:1 #232323); color: white; border: none; "
            "border-radius: 4px; padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #f04747, stop:1 #d03737); }"
            "QPushButton:pressed { background: #d03737; }"
        )
        button_layout.addWidget(self.files_button)
        
        settings_layout.addRow(button_layout)
        settings_group.setLayout(settings_layout)
        settings_group.setStyleSheet(
            "QGroupBox { background-color: #0f0f0f; border: 1px solid #2a2a2a; border-radius: 6px; margin-top: 14px; padding-top: 16px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; color: #f04747; "
            "padding: 0 8px; background-color: #0f0f0f; font-weight: bold; }"
            "QLabel { background: transparent; border: none; }"
        )
        main_layout.addWidget(settings_group)
        
        self.kill_display = QTextBrowser()
        self.kill_display.setReadOnly(True)
        self.kill_display.setOpenExternalLinks(True)
        self.kill_display.setStyleSheet(
            "QTextBrowser { background-color: #121212; border: 1px solid #2a2a2a; border-radius: 4px; padding: 10px; }"
            "QTextBrowser QScrollBar:vertical { background: #1a1a1a; width: 12px; margin: 0px; }"
            "QTextBrowser QScrollBar::handle:vertical { background: #2a2a2a; min-height: 20px; border-radius: 6px; }"
            "QTextBrowser QScrollBar::handle:vertical:hover { background: #f04747; }"
            "QTextBrowser QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
            "QTextBrowser QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }"
        )
        main_layout.addWidget(self.kill_display, stretch=1)
        
        self.bottom_info_label = QLabel()
        self.bottom_info_label.setStyleSheet(
            "QLabel { color: #a0a0a0; background-color: #141414; "
            "font-size: 13px; padding: 10px 15px; "
            "border-top: 1px solid #2a2a2a; }"
            "QLabel span { color: #f04747; font-weight: bold; }"
        )
        self.bottom_info_label.setText("")
        main_layout.addWidget(self.bottom_info_label)
        
        self.send_to_api_checkbox.stateChanged.connect(self.update_api_status)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.setMinimumSize(900, 700)

    def update_bottom_info(self, key: str, message: str) -> None:
        self.persistent_info[key] = message
        
        # Format with HTML to allow styled spans
        info_items = []
        for k in ["monitoring", "registered", "game_mode", "api_connection"]:
            if self.persistent_info[k]:
                # Extract label and value
                parts = self.persistent_info[k].split(": ", 1)
                if len(parts) == 2:
                    label, value = parts
                    info_items.append(f"{label}: <span>{value}</span>")
                else:
                    info_items.append(self.persistent_info[k])
        
        info_text = " | ".join(info_items)
        self.bottom_info_label.setText(info_text)

    def show_temporary_popup(self, message: str):
        msgBox = QMessageBox(self)
        msgBox.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        msgBox.setWindowTitle("Info")
        msgBox.setText(message)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.show()

    def on_ship_combo_changed(self, new_ship: str) -> None:
        self.save_config()
        if self.monitor_thread and self.monitor_thread.isRunning():
            new_ship = new_ship.strip()
            if not new_ship:
                new_ship = "No Ship"
            self.monitor_thread.current_attacker_ship = new_ship
            self.monitor_thread.update_config_killer_ship(new_ship)

    def apply_styles(self) -> None:
        style = """
            QWidget { background-color: #0d0d0d; color: #f0f0f0; font-family: 'Segoe UI', sans-serif; }
            QGroupBox { border: 1px solid #2a2a2a; border-radius: 8px; margin-top: 10px; background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a1a1a, stop:1 #141414); }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; color: #f04747; font-weight: bold; }
            QLineEdit { background-color: #1e1e1e; border: 1px solid #2a2a2a; border-radius: 4px; padding: 6px; color: #f0f0f0; }
            QPushButton { background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #303030, stop:1 #1e1e1e); border: 1px solid #2a2a2a; border-radius: 4px; padding: 8px 12px; color: #f0f0f0; font-weight: bold; }
            QPushButton:hover { background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #454545, stop:1 #303030); border-color: #f04747; }
            QPushButton:pressed { background-color: #1e1e1e; }
            QCheckBox { color: #f0f0f0; }
            QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #2a2a2a; border-radius: 3px; background-color: #1e1e1e; }
            QCheckBox::indicator:checked { background-color: #f04747; }
            QTextBrowser { background-color: #121212; border: 1px solid #2a2a2a; border-radius: 4px; padding: 10px; font-family: 'Consolas', monospace; }
            QComboBox { background-color: #1e1e1e; border: 1px solid #2a2a2a; border-radius: 4px; padding: 6px; color: #f0f0f0; }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { width: 0; height: 0; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 5px solid #f04747; margin-right: 8px; }
            QComboBox QAbstractItemView { background-color: #1e1e1e; color: #f0f0f0; selection-background-color: #f04747; }
            a { color: #f04747; }
        """
        self.setStyleSheet(style)

    def load_local_kills(self):
        if os.path.isfile(self.kills_local_file):
            try:
                with open(self.kills_local_file, 'r', encoding='utf-8') as f:
                    self.local_kills = json.load(f)
                logging.info(f"Loaded {len(self.local_kills)} kills from local JSON.")
            except Exception as e:
                logging.error(f"Failed to load local kills: {e}")
                self.local_kills = {}
        else:
            self.local_kills = {}
            self.save_local_kills()

    def save_local_kills(self):
        try:
            with open(self.kills_local_file, 'w', encoding='utf-8') as f:
                json.dump(self.local_kills, f, indent=4)
            logging.info(f"Saved {len(self.local_kills)} kills to local JSON.")
        except Exception as e:
            logging.error(f"Failed to save local kills: {e}")

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
                    self.show_temporary_popup("No kills selected to send.")
            else:
                self.show_temporary_popup("Missing kills were not sent.")
        else:
            self.show_temporary_popup("No missing kills found.")

    def send_missing_kills(self, missing_kills: List[dict]) -> None:
        self.missing_kills_queue = missing_kills
        self.send_next_missing_kill()

    def send_next_missing_kill(self) -> None:
        if not self.missing_kills_queue:
            self.show_temporary_popup("All missing kills processed.")
            return

        kill = self.missing_kills_queue.pop(0)
        local_key = kill["local_key"]
        payload = kill["payload"]
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
            'User-Agent': self.user_agent,
            'X-Client-ID': self.__client_id__,
            'X-Client-Version': self.__version__
        }
        api_thread = ApiSenderThread(self.api_endpoint, headers, payload, local_key, parent=self)
        api_thread.apiResponse.connect(lambda msg, key=local_key: self.handle_missing_api_response(msg, key))
        api_thread.start()

    def handle_missing_api_response(self, msg: str, local_key: str) -> None:
        self.show_temporary_popup(msg)
        if msg.startswith("Duplicate kill"):
            self.local_kills[local_key] = True
            self.save_local_kills()

        QTimer.singleShot(500, self.send_next_missing_kill)

    def ping_api(self) -> bool:
        headers = {
            'X-API-Key': self.api_key,
            'User-Agent': self.user_agent,
            'X-Client-ID': self.__client_id__,
            'X-Client-Version': self.__version__
        }
        ping_url = "https://starcitizentool.com/api/v1/ping"
        try:
            response = requests.get(ping_url, headers=headers, timeout=5)
            if response.status_code == 200:
                self.update_bottom_info("api_connection", "API Connected")
                return True
            else:
                logging.error(f"Ping API returned status code: {response.status_code}")
                self.update_bottom_info("api_connection", "Error API not connected")
                return False
        except Exception as e:
            logging.error(f"Error pinging API: {e}")
            self.update_bottom_info("api_connection", "Error API not connected")
            return False

    def toggle_monitoring(self) -> None:
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait(3000)
            self.monitor_thread = None
            self.start_button.setText("Start Monitoring")
            self.update_bottom_info("monitoring", "Monitoring stopped.")
            self.update_bottom_info("api_connection", "")
            self.save_config()
            self.delete_local_kills()
            self.delete_kill_logger_log()
            self.rescan_button.setEnabled(False)
        else:
            self.update_bottom_info("api_connection", "")
            new_api_key = self.api_key_input.text().strip()
            new_log_path = self.log_path_input.text().strip()
            self.api_key = new_api_key
            self.local_user_name = ""
            self.registration_attempts = 0

            if self.send_to_api_checkbox.isChecked():
                if not new_api_key:
                    QMessageBox.warning(self, "Input Error", "Please enter your API key.")
                    return
                if not self.ping_api():
                    QMessageBox.critical(
                        self, "API Error",
                        "Unable to connect to the API. Check your network and API key."
                    )
                    return

            if not new_log_path or not os.path.isfile(new_log_path):
                QMessageBox.warning(self, "Input Error", "Please enter a valid path to your Game.log file.")
                return

            killer_ship = "No Ship"
            if os.path.isfile(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    killer_ship = config.get("killer_ship", "No Ship")
                except Exception as e:
                    logging.error(f"Error reading config for killer ship: {e}")

            self.monitor_thread = TailThread(new_log_path, CONFIG_FILE)
            self.monitor_thread.current_attacker_ship = killer_ship
            self.monitor_thread.ship_updated.connect(self.on_ship_updated)
            self.monitor_thread.payload_ready.connect(self.handle_payload)
            self.monitor_thread.kill_detected.connect(self.on_kill_detected)
            self.monitor_thread.death_detected.connect(self.on_death_detected)
            self.monitor_thread.player_registered.connect(self.on_player_registered)
            self.monitor_thread.game_mode_changed.connect(self.on_game_mode_changed)
            self.monitor_thread.start()
            self.on_ship_updated(killer_ship)
            self.start_button.setText("Stop Monitoring")
            self.update_bottom_info("monitoring", "Monitoring started...")
            self.save_config()
            self.rescan_button.setEnabled(True)

    def on_player_registered(self, text: str) -> None:
        match = re.search(r"Registered user:\s+(.+)$", text)
        if match:
            handle = match.group(1).strip()
            self.local_user_name = handle
            if self.monitor_thread:
                self.monitor_thread.registered_user = handle
            logging.info(f"Local registered user set to: {handle}")
            self.update_bottom_info("registered", f"Registered user: {handle}")
            self.save_config()

    def on_game_mode_changed(self, mode_msg: str) -> None:
        self.update_bottom_info("game_mode", mode_msg)

    def on_kill_detected(self, readout: str, attacker: str) -> None:
        self.append_kill_readout(readout)
        if self.kill_sound_enabled:
            self.kill_sound_effect.setSource(QUrl.fromLocalFile(self.kill_sound_path))
            self.kill_sound_effect.setVolume(self.kill_sound_volume / 100.0)
            self.kill_sound_effect.play()

    def on_death_detected(self, readout: str, attacker: str) -> None:
        self.append_kill_readout(readout)

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
            "sent_to_api": False
        }
        self.save_local_kills()
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

    def handle_api_response(self, message: str, local_key: str, timestamp: str) -> None:
        normalized_message = message.strip().lower()
        ignore_responses = {"npc kill not logged.", "subside kill not logged.", "self kill not logged."}
        if normalized_message in ignore_responses:
            logging.info(f"Ignored kill event for {local_key} with message: {message}")
            return
        if local_key in self.local_kills:
            self.local_kills[local_key]["api_response"] = message
            logging.info(f"[{timestamp}] Updated local kill {local_key} with API response: {message}")
            self.save_local_kills()

    def append_kill_readout(self, text: str) -> None:
        self.kill_display.append(text)
        self.kill_display.verticalScrollBar().setValue(self.kill_display.verticalScrollBar().maximum())

    def closeEvent(self, event) -> None:
        if self.monitor_thread and self.monitor_thread.isRunning():
            reply = QMessageBox.question(
                self, 'Confirm Exit',
                "Monitoring is active. Stop and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.monitor_thread.stop()
                self.monitor_thread.wait(3000)
                self.monitor_thread = None
                self.start_button.setText("Start Monitoring")
            else:
                event.ignore()
                return

        if self.rescan_thread and self.rescan_thread.isRunning():
            self.rescan_thread.stop()
            self.rescan_thread.wait(3000)
            self.rescan_thread = None

        self.delete_local_kills()
        self.delete_kill_logger_log()
        event.accept()

    def delete_local_kills(self):
        if os.path.isfile(self.kills_local_file):
            try:
                os.remove(self.kills_local_file)
                logging.info("Local kills JSON removed on close.")
            except Exception as e:
                logging.error(f"Failed to delete local kills JSON: {e}")

    def load_config(self) -> None:
        if os.path.isfile(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.kill_sound_enabled = config.get('kill_sound', False)
                self.kill_sound_checkbox.setChecked(self.kill_sound_enabled)
                self.kill_sound_path = config.get('kill_sound_path', resource_path("kill.wav"))
                self.kill_sound_volume = config.get('kill_sound_volume', 100)
                self.log_path_input.setText(config.get('log_path', ''))
                self.api_key = config.get('api_key', '')
                self.api_key_input.setText(self.api_key)
                self.local_user_name = config.get('local_user_name', '')
                self.kill_sound_path_input.setText(self.kill_sound_path)
                self.volume_slider.setValue(self.kill_sound_volume)
                self.send_to_api_checkbox.setChecked(config.get('send_to_api', True))
                self.ship_combo.setCurrentText("No Ship")
            except Exception as e:
                logging.error(f"Failed to load config: {e}")

    def save_config(self) -> None:
        ship_value = self.ship_combo.currentText().strip()
        if not ship_value:
            ship_value = "No Ship"
        config = {
            'monitoring_active': self.monitor_thread.isRunning() if self.monitor_thread else False,
            'kill_sound': self.kill_sound_enabled,
            'kill_sound_path': self.kill_sound_path_input.text().strip(),
            'kill_sound_volume': self.volume_slider.value(),
            'log_path': self.log_path_input.text().strip(),
            'api_key': self.api_key_input.text().strip(),
            'local_user_name': self.local_user_name,
            'send_to_api': self.send_to_api_checkbox.isChecked(),
            'killer_ship': ship_value
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def delete_kill_logger_log(self) -> None:
        try:
            if os.path.isfile(LOG_FILE):
                os.remove(LOG_FILE)
        except Exception as e:
            logging.error(f"Failed to delete kill_logger.log: {e}")

    def check_for_updates(self) -> None:
        try:
            base_api_url = "https://starcitizentool.com/api/v1"
            r = requests.get(f"{base_api_url}/latest_version", timeout=10)
            r.raise_for_status()
            data = r.json()
            latest = data.get('latest_version')
            if latest and version.parse(self.__version__) < version.parse(latest):
                download_url = data.get('download_url', 'https://starcitizentool.com/download-sctool')
                self.notify_update(latest_version=latest, download_url=download_url)
        except Exception as e:
            logging.error(f"Failed to check for updates: {e}")

    def notify_update(self, latest_version: str, download_url: str) -> None:
        update_message = (
            f"<p>A new version (<b>{latest_version}</b>) is available!</p>"
            f"<p><a href='{download_url}'>Download latest update here</a></p>"
        )
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Update Available")
        msg_box.setText(update_message)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setTextInteractionFlags(Qt.TextBrowserInteraction)
        msg_box.setStandardButtons(QMessageBox.Ok)
        if msg_box.exec_() == QMessageBox.Ok:
            sys.exit(0)

    def load_ship_options(self) -> None:
        ships_file = os.path.join(TRACKER_DIR, "ships.json")
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

    def showCustomMessageBox(self, title, message, icon=QMessageBox.Information):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setStyleSheet(
            "QMessageBox { background-color: #0d0d0d; color: #f0f0f0; }"
            "QLabel { color: #f0f0f0; }"
            "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
            "border: 1px solid #2a2a2a; border-radius: 4px; padding: 6px 12px; }"
            "QPushButton:hover { background-color: #f04747; }"
        )
        
        return msg_box.exec_()

    def open_tracker_files(self) -> None:
        webbrowser.open(TRACKER_DIR)

    def on_ship_updated(self, ship: str) -> None:
        index = self.ship_combo.findText(ship)
        if index != -1:
            self.ship_combo.setCurrentIndex(index)
        else:
            self.ship_combo.addItem(ship)
            self.ship_combo.setCurrentIndex(self.ship_combo.count() - 1)

    def update_api_status(self) -> None:
        if self.send_to_api_checkbox.isChecked():
            if self.ping_api():
                self.update_bottom_info("api_connection", "API Connected")
            else:
                self.update_bottom_info("api_connection", "Error API not connected")
        else:
            self.update_bottom_info("api_connection", "API Disabled")

def style_form_label(label):
    label.setStyleSheet("QLabel { color: #cccccc; font-weight: 500; }")
    return label

def cleanup_log_file() -> None:
    try:
        import logging
        logging.shutdown()
        if os.path.isfile(LOG_FILE):
            os.remove(LOG_FILE)
            print(f"{LOG_FILE} deleted successfully.")
    except Exception as e:
        print(f"Failed to delete {LOG_FILE}: {e}")

atexit.register(cleanup_log_file)

def main() -> None:
    app = QApplication(sys.argv)
    gui = KillLoggerGUI()
    gui.check_for_updates()
    dark_title_bar_for_pyqt5(gui)
    gui.show()
    sys.exit(app.exec_())
