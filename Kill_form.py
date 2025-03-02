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
from datetime import datetime
from packaging import version
from bs4 import BeautifulSoup
from urllib.parse import quote
from typing import Optional, Dict, Any, List
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLineEdit, QPushButton,
    QTextBrowser, QFileDialog, QVBoxLayout, QHBoxLayout, QMessageBox,
    QGroupBox, QCheckBox, QSlider, QFormLayout, QLabel, QDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QUrl, QTimer, QStandardPaths, QDir
from PyQt5.QtMultimedia import QSoundEffect

from Kill_thread import ApiSenderThread, TailThread, RescanThread
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

def trim_suffix(name: Optional[str]) -> str:
    if not name:
        return 'Unknown'
    return re.sub(r'_\d+$', '', name)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": CHROME_USER_AGENT})
PLAYER_DETAILS_CACHE: Dict[str, Dict[str, str]] = {}

def fetch_player_details(playername: str) -> Dict[str, str]:
    if playername in PLAYER_DETAILS_CACHE:
        return PLAYER_DETAILS_CACHE[playername]
    details = {
        "enlistment_date": "None",
        "occupation": "None",
        "org_name": "None",
        "org_tag": "None"
    }
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
    __version__ = "2.6"
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SCTool Killfeed 2.6")
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
        self.init_ui()
        self.load_config()
        self.load_local_kills()
        self.apply_styles()
        
    def init_ui(self) -> None:
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout()
        settings_layout.setSpacing(10)
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your API key here")
        settings_layout.addRow("API Key:", self.api_key_input)
        self.send_to_api_checkbox = QCheckBox("Send Kills to API")
        self.send_to_api_checkbox.setChecked(True)
        settings_layout.addRow(self.send_to_api_checkbox)
        log_path_layout = QHBoxLayout()
        self.log_path_input = QLineEdit()
        self.log_path_input.setPlaceholderText("Enter path to your Game.log")
        browse_log_btn = QPushButton("Browse")
        browse_log_btn.setIcon(QIcon(resource_path("browse_icon.png")))
        browse_log_btn.clicked.connect(self.browse_file)
        log_path_layout.addWidget(self.log_path_input)
        log_path_layout.addWidget(browse_log_btn)
        settings_layout.addRow("Game.log Path:", log_path_layout)
        sound_group = QGroupBox("Kill Sound Settings")
        sound_layout = QFormLayout()
        sound_path_layout = QHBoxLayout()
        self.kill_sound_path_input = QLineEdit()
        self.kill_sound_path_input.setText(self.kill_sound_path)
        sound_browse_btn = QPushButton("Browse")
        sound_browse_btn.clicked.connect(self.on_kill_sound_file_browse)
        sound_path_layout.addWidget(self.kill_sound_path_input)
        sound_path_layout.addWidget(sound_browse_btn)
        sound_layout.addRow("Kill Sound File:", sound_path_layout)
        self.kill_sound_checkbox = QCheckBox("Enable Kill Sound")
        self.kill_sound_checkbox.setChecked(False)
        self.kill_sound_checkbox.stateChanged.connect(self.on_kill_sound_toggled)
        sound_layout.addRow(self.kill_sound_checkbox)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.kill_sound_volume)
        self.volume_slider.valueChanged.connect(self.on_kill_sound_volume_changed)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #2a2a2a;
                height: 8px;
                background: #1e1e1e;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #f04747;
                border: 1px solid #2a2a2a;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #f04747;
                border-radius: 4px;
            }
        """)
        sound_layout.addRow("Volume:", self.volume_slider)
        sound_group.setLayout(sound_layout)
        settings_layout.addRow(sound_group)
        self.start_button = QPushButton("Start Monitoring")
        self.start_button.setIcon(QIcon(resource_path("start_icon.png")))
        self.start_button.clicked.connect(self.toggle_monitoring)
        settings_layout.addRow(self.start_button)
        self.rescan_button = QPushButton("Find Missed Kills")
        self.rescan_button.setIcon(QIcon(resource_path("search_icon.png")))
        self.rescan_button.clicked.connect(self.on_rescan_button_clicked)
        self.rescan_button.setEnabled(False)
        settings_layout.addRow(self.rescan_button)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        self.kill_display = QTextBrowser()
        self.kill_display.setReadOnly(True)
        self.kill_display.setOpenExternalLinks(True)
        main_layout.addWidget(self.kill_display, stretch=1)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("color: #cfcfcf;")
        self.setMinimumSize(900, 700)

    def apply_styles(self) -> None:
        style = """
        QWidget {
            background-color: #141414;
            color: #cfcfcf;
            font-family: "Segoe UI", sans-serif;
        }
        QGroupBox {
            border: 1px solid #2a2a2a;
            border-radius: 8px;
            margin-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 10px;
            color: #f04747;
            font-weight: bold;
        }
        QLineEdit, QSlider {
            background-color: #1e1e1e;
            border: 1px solid #2a2a2a;
            padding: 4px;
            color: #cfcfcf;
        }
        QPushButton {
            background-color: #1e1e1e;
            border: 1px solid #2a2a2a;
            border-radius: 4px;
            padding: 6px 12px;
            color: #cfcfcf;
        }
        QPushButton:hover {
            background-color: #2a2a2a;
        }
        QCheckBox {
            color: #cfcfcf;
        }
        QTextBrowser {
            background-color: #20232a;
            border: 1px solid #2a2a2a;
            padding: 10px;
        }
        a {
            color: #f04747;
        }
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
            "Audio Files (*.wav *.mp3 *.ogg);;All Files (*)", options=options
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
            "Log Files (*.log);;All Files (*)", options=options
        )
        if file_path:
            self.log_path_input.setText(file_path)

    def on_rescan_button_clicked(self) -> None:
        log_path = self.log_path_input.text().strip()
        if not log_path or not os.path.isfile(log_path):
            QMessageBox.warning(self, "Input Error", "Please enter a valid path to your Game.log file.")
            return

        if self.rescan_thread and self.rescan_thread.isRunning():
            self.rescan_thread.stop()
            self.rescan_thread.wait(3000)
            self.rescan_thread = None

        registered_user = self.local_user_name
        self.rescan_thread = RescanThread(log_path, registered_user, parent=self)
        self.rescan_thread.rescanFinished.connect(self.rescan_finished_handler)
        self.rescan_thread.start()
        self.append_kill_readout("Rescan started. This may take a while if the log is large...")
        self.status_bar.showMessage("Rescanning log for missed kills...", 5000)

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
            prompt_text = f"{len(missing)} missing kill(s) found:\n\n{missing_details}\nLog these kills to the API?"
            reply = QMessageBox.question(self, "Missing Kills Found",
                                        prompt_text,
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.send_missing_kills(missing)
            else:
                self.append_kill_readout("Missing kills were not sent.")
        else:
            self.append_kill_readout("No missing kills found.")

    def send_missing_kills(self, missing_kills: List[dict]) -> None:
        self.missing_kills_queue = missing_kills
        self.send_next_missing_kill()

    def send_next_missing_kill(self) -> None:
        if not self.send_to_api_checkbox.isChecked():
            logging.info("Send to API disabled; skipping missing kills API calls.")
            self.append_kill_readout("API sending disabled. Missing kills stored locally only.")
            return

        if not self.missing_kills_queue:
            self.append_kill_readout("All missing kills processed.")
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
        api_thread.apiResponse.connect(lambda msg, key=local_key: self.handle_api_response(msg, key, kill["timestamp"]))
        api_thread.start()

    def handle_missing_api_response(self, msg: str, local_key: str) -> None:
        self.append_kill_readout(msg)
        if msg.startswith("Accepted kill:") or msg.startswith("Duplicate kill"):
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
                if self.local_user_name:
                    msg = f"Connected to API, monitoring kills for {self.local_user_name}"
                    self.status_bar.showMessage(msg, 5000)
                    self.append_kill_readout(msg)
                elif self.registration_attempts >= 3:
                    msg = "Connected to API, monitoring kills (Player name not found)"
                    self.status_bar.showMessage(msg, 5000)
                    self.append_kill_readout(msg)
                return True
            else:
                logging.error(f"Ping API returned status code: {response.status_code}")
                self.status_bar.showMessage("Failed to connect to API", 5000)
                return False
        except Exception as e:
            logging.error(f"Error pinging API: {e}")
            self.status_bar.showMessage("Error pinging API", 5000)
            return False

    def toggle_monitoring(self) -> None:
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait(3000)
            self.monitor_thread = None
            self.start_button.setText("Start Monitoring")
            self.append_kill_readout("Monitoring stopped.")
            self.status_bar.showMessage("Monitoring stopped.", 5000)
            self.save_config()
            self.delete_local_kills()
            self.delete_kill_logger_log()
            self.rescan_button.setEnabled(False)
        else:
            self.load_config()
            self.registration_attempts = 0
            self.api_key = self.api_key_input.text().strip()
            log_path = self.log_path_input.text().strip()
            send_to_api_enabled = self.send_to_api_checkbox.isChecked()

            if send_to_api_enabled:
                if not self.api_key:
                    QMessageBox.warning(self, "Input Error", "Please enter your API key.")
                    return
                if not self.ping_api():
                    QMessageBox.critical(self, "API Error", "Unable to connect to the API. Check your network and API key.")
                    return

            if not log_path or not os.path.isfile(log_path):
                QMessageBox.warning(self, "Input Error", "Please enter a valid path to your Game.log file.")
                return

            from Kill_thread import TailThread
            self.monitor_thread = TailThread(log_path, None)
            self.monitor_thread.payload_ready.connect(self.handle_payload)
            self.monitor_thread.kill_detected.connect(self.on_kill_detected)
            self.monitor_thread.death_detected.connect(self.on_death_detected)
            self.monitor_thread.player_registered.connect(self.append_api_response)
            self.monitor_thread.player_registered.connect(self.on_player_registered)
            self.monitor_thread.game_mode_changed.connect(self.on_game_mode_changed)
            self.monitor_thread.start()
            self.start_button.setText("Stop Monitoring")
            self.append_kill_readout("Monitoring started...")
            self.status_bar.showMessage("Monitoring started.", 5000)
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
            self.status_bar.showMessage(f"Monitoring kills for local user: {handle}", 5000)
            self.save_config()

    def on_game_mode_changed(self, mode_msg: str) -> None:
        self.status_bar.showMessage(mode_msg, 5000)
        self.append_kill_readout(mode_msg)

    def on_kill_detected(self, readout: str, attacker: str) -> None:
        self.append_kill_readout(readout)
        if self.kill_sound_enabled:
            self.kill_sound_effect.setSource(QUrl.fromLocalFile(self.kill_sound_path))
            self.kill_sound_effect.setVolume(self.kill_sound_volume / 100.0)
            self.kill_sound_effect.play()

    def handle_payload(self, payload: dict, timestamp: str, attacker: str, readout: str) -> None:
        logging.info(f"Send to API checkbox state: {self.send_to_api_checkbox.isChecked()}")
        match = KILL_LOG_PATTERN.search(payload.get('log_line', ''))
        if not match:
            logging.warning(f"[{timestamp}] handle_payload: No match in log line, skipping.")
            return
        data = match.groupdict()
        victim = data.get('victim', '').lower().strip()
        current_game_mode = self.monitor_thread.last_game_mode if self.monitor_thread.last_game_mode else "Unknown"
        local_key = f"{timestamp}::{victim}::{current_game_mode}"
        if local_key in self.local_kills:
            logging.info(f"[{timestamp}] Kill already stored locally under key: {local_key}. Skipping API call.")
            self.append_kill_readout("Kill already in local JSON. Skipping API call.")
            return

        self.local_kills[local_key] = {
            "payload": payload,
            "timestamp": timestamp,
            "attacker": attacker,
            "readout": readout,
            "sent_to_api": False
        }
        logging.info(f"[{timestamp}] Saving kill locally with key: {local_key}.")
        self.save_local_kills()

        if not self.send_to_api_checkbox.isChecked():
            logging.info("Send to API disabled; not sending kill to API.")
            self.append_kill_readout("API sending disabled. Kill stored locally only.")
            return

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

    def handle_api_response(self, message: str, local_key: str, timestamp: str) -> None:
        self.append_kill_readout(message)
        if local_key in self.local_kills:
            self.local_kills[local_key]["api_response"] = message
            logging.info(f"[{timestamp}] Updated local kill {local_key} with API response: {message}")
            self.save_local_kills()

    def append_kill_readout(self, text: str) -> None:
        self.kill_display.append(text)
        self.kill_display.verticalScrollBar().setValue(self.kill_display.verticalScrollBar().maximum())

    def append_api_response(self, text: str) -> None:
        logging.info(text)
        self.append_kill_readout(text)

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
                self.append_kill_readout("Monitoring stopped.")
                self.status_bar.showMessage("Monitoring stopped.", 5000)
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
                self.local_user_name = config.get('local_user_name', "")
                self.kill_sound_path_input.setText(self.kill_sound_path)
                self.volume_slider.setValue(self.kill_sound_volume)
                send_to_api = config.get('send_to_api', True)
                self.send_to_api_checkbox.setChecked(send_to_api)
            except Exception as e:
                logging.error(f"Failed to load config: {e}")

    def save_config(self) -> None:
        config = {
            'monitoring_active': self.monitor_thread.isRunning() if self.monitor_thread else False,
            'kill_sound': self.kill_sound_enabled,
            'kill_sound_path': self.kill_sound_path_input.text().strip(),
            'kill_sound_volume': self.volume_slider.value(),
            'log_path': self.log_path_input.text().strip(),
            'api_key': self.api_key_input.text().strip(),
            'local_user_name': self.local_user_name,
            'send_to_api': self.send_to_api_checkbox.isChecked()
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

    def on_death_detected(self, readout: str, attacker: str) -> None:
        self.append_kill_readout(readout)
        if self.kill_sound_enabled:
            self.kill_sound_effect.setSource(QUrl.fromLocalFile(self.kill_sound_path))
            self.kill_sound_effect.setVolume(self.kill_sound_volume / 100.0)
            self.kill_sound_effect.play()

class RetryDialog(QDialog):
    def __init__(self, fail_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Error")
        self.reason_text = ""
        layout = QVBoxLayout()
        self.label = QLabel(fail_text)
        layout.addWidget(self.label)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter a reason or note here...")
        layout.addWidget(self.input_field)
        button_layout = QHBoxLayout()
        self.btn_yes = QPushButton("Yes")
        self.btn_no = QPushButton("No")
        self.btn_yes.clicked.connect(self.on_yes)
        self.btn_no.clicked.connect(self.on_no)
        button_layout.addWidget(self.btn_yes)
        button_layout.addWidget(self.btn_no)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def on_yes(self):
        self.reason_text = self.input_field.text()
        self.accept()

    def on_no(self):
        self.reject()

def cleanup_log_file() -> None:
    try:
        import logging
        logging.shutdown()  # Close all logging handlers
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
