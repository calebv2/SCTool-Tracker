"""
Star Citizen–Styled SCtool Logger
Version: 2.3
"""

import sys
import os
import re
import json
import base64
import requests
import logging
import atexit
import time
import ctypes
from ctypes import wintypes
from datetime import datetime
from packaging import version
from urllib.parse import quote

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QTextBrowser, QFileDialog, QVBoxLayout, QHBoxLayout, QMessageBox,
    QGroupBox, QCheckBox, QSlider, QFormLayout
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QThread, QStandardPaths, QDir
from PyQt5.QtMultimedia import QSoundEffect
from bs4 import BeautifulSoup

#####################################################################
# Enable dark title bar on Windows
#####################################################################
def dark_title_bar_for_pyqt5(widget):
    if sys.platform.startswith("win"):
        try:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
            hwnd = widget.winId().__int__()
            value = ctypes.c_int(2)
            set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
        except Exception as e:
            logging.error(f"Error enabling dark title bar: {e}")

#####################################################################
# Locate resources for PyInstaller or development
#####################################################################
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

#####################################################################
# Redirect config and log files to a writable location (AppData)
#####################################################################
def get_appdata_paths():
    appdata_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not appdata_dir:
        appdata_dir = os.path.expanduser("~")
    tracker_dir = os.path.join(appdata_dir, "SCTool_Tracker")
    QDir().mkpath(tracker_dir)
    config_file = os.path.join(tracker_dir, "config.json")
    log_file = os.path.join(tracker_dir, "kill_logger.log")
    return config_file, log_file

CONFIG_FILE, LOG_FILE = get_appdata_paths()

#####################################################################
# Latest Chrome User-Agent for HTTP requests
#####################################################################
CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/112.0.5615.121 Safari/537.36"
)

#####################################################################
# Set up logging
#####################################################################
logging.basicConfig(
    filename=LOG_FILE,
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

#####################################################################
# Regular expression patterns for parsing log entries
#####################################################################
CHARACTER_CREATION_PATTERN = re.compile(
    r"<?[^>]*cterStatus_Character> Character: createdAt (?P<createdAt>\d+) - updatedAt (?P<updatedAt>\d+) - "
    r"geid (?P<geid>\d+) - accountId (?P<accountId>\d+) - name (?P<name>[\w\-]+) - state (?P<state>\w+) "
    r"\[Team_GameServices\]\[Login\]"
)

KILL_LOG_PATTERN = re.compile(
    r"<(?P<timestamp>[^>]+)> \[Notice\] <Actor Death> CActor::Kill: '(?P<victim>[^']+)' \[(?P<victim_geid>\d+)\] in zone '(?P<zone>[^']+)' "
    r"killed by '(?P<attacker>[^']+)' \[(?P<attacker_geid>\d+)\] using '(?P<weapon>[^']+)' \[.*\] with damage type '(?P<damage_type>\w+)' "
    r"from direction x: (?P<x>-?[\d.]+), y: (?P<y>-?[\d.]+), z: (?P<z>-?[\d.]+) \[.*\]"
)

GAME_MODE_PATTERN = re.compile(
    r"<(?P<timestamp>[^>]+)> Loading GameModeRecord='(?P<game_mode>[^']+)' with EGameModeId='[^']+'"
)

GAME_MODE_MAPPING = {
    'EA_TeamElimination': 'EA_TeamElimination',
    'SC_Default': 'SC_Default',
    'EA_FPSGunGame': 'EA_FPSGunGame',
    'EA_TonkRoyale_TeamBattle': 'EA_TonkRoyale_TeamBattle',
    'EA_FreeFlight': 'EA_FreeFlight',
    'EA_SquadronBattle': 'EA_SquadronBattle',
    'EA_VehicleKillConfirmed': 'EA_VehicleKillConfirmed',
    'EA_FPSKillConfirmed': 'EA_FPSKillConfirmed',
    'EA_Control': 'EA_Control',
    'EA_Duel': 'EA_Duel'
}

#####################################################################
# Utility to trim numeric suffix from names
#####################################################################
def trim_suffix(name):
    if not name:
        return 'Unknown'
    return re.sub(r'_\d+$', '', name)

#####################################################################
# Fetch player details (enlistment, occupation, organization)
#####################################################################
def fetch_player_details(playername):
    details = {
        "enlistment_date": "None",
        "occupation": "None",
        "org_name": "None",
        "org_tag": "None"
    }
    try:
        url = f"https://robertsspaceindustries.com/citizens/{playername}"
        headers = {"User-Agent": CHROME_USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            enlistment_label = soup.find("span", class_="label", string="Enlisted")
            if enlistment_label:
                enlistment_date_elem = enlistment_label.find_next("strong", class_="value")
                if enlistment_date_elem:
                    details["enlistment_date"] = enlistment_date_elem.text.strip()
        # Second API call for additional info
        api_url = "https://robertsspaceindustries.com/api/spectrum/search/member/autocomplete"
        autocomplete_name = playername[:-1] if len(playername) > 1 else playername
        payload = {"community_id": "1", "text": autocomplete_name}
        headers2 = {"Content-Type": "application/json"}
        response2 = requests.post(api_url, headers=headers2, json=payload, timeout=10)
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
                    elif "name" in badge:
                        if details["occupation"] == "None":
                            details["occupation"] = badge.get("name", "None")
        else:
            logging.error(f"Autocomplete API request failed for {playername} with status code {response2.status_code}")
    except Exception as e:
        logging.error(f"Error fetching player details for {playername}: {e}")
    return details

#####################################################################
# Fetch & encode the victim's RSI image in Base64
#####################################################################
def fetch_victim_image_base64(victim_name):
    default_image_url = "https://cdn.robertsspaceindustries.com/static/images/account/avatar_default_big.jpg"
    url = f"https://robertsspaceindustries.com/citizens/{quote(victim_name)}"
    headers = {"User-Agent": CHROME_USER_AGENT}
    final_url = default_image_url

    try:
        response = requests.get(url, headers=headers, timeout=10)
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
        r = requests.get(final_url, headers=headers, timeout=10)
        if r.status_code == 200:
            content_type = r.headers.get("Content-Type", "image/jpeg")
            if not content_type or "image" not in content_type:
                content_type = "image/jpeg"
            b64_data = base64.b64encode(r.content).decode("utf-8")
            return f"data:{content_type};base64,{b64_data}"
    except Exception as e:
        logging.error(f"Error fetching actual image data for {victim_name}: {e}")

    return default_image_url

#####################################################################
# TailThread: Monitors the log file for new entries
#####################################################################
class TailThread(QThread):
    kill_detected = pyqtSignal(str, str)
    player_registered = pyqtSignal(str)
    game_mode_changed = pyqtSignal(str)

    def __init__(self, file_path, callback):
        super().__init__()
        self.file_path = file_path
        self.callback = callback
        self._stop_event = False
        self.player_mapping = {}
        self.last_game_mode = None
        self.registered_user = None

    def is_file_same(self, file):
        try:
            current_stat = os.stat(self.file_path)
            file_stat = os.fstat(file.fileno())
            return (current_stat.st_dev == file_stat.st_dev and
                    current_stat.st_ino == file_stat.st_ino)
        except Exception as e:
            logging.error(f"Error checking if file is same: {e}")
            return False

    def run(self):
        logging.info("TailThread started.")
        while not self._stop_event:
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.process_existing_player_registrations(f)
                    f.seek(0, os.SEEK_END)
                    logging.info(f"Started tailing {self.file_path} for new entries...")
                    while not self._stop_event:
                        line = f.readline()
                        if not line:
                            if not self.is_file_same(f):
                                logging.info(f"{self.file_path} has been rotated. Reopening.")
                                break
                            time.sleep(0.1)
                            continue
                        stripped_line = line.strip()
                        logging.debug(f"Read new line: {stripped_line}")
                        self.process_line(stripped_line)
            except Exception as e:
                logging.error(f"Error in TailThread: {e}")
            time.sleep(1)
        logging.info("TailThread terminated.")

    def process_existing_player_registrations(self, f):
        logging.info("Processing existing entries for player registrations and game modes...")
        for line in f:
            stripped_line = line.strip()
            char_match = CHARACTER_CREATION_PATTERN.search(stripped_line)
            if char_match:
                data = char_match.groupdict()
                geid = data.get('geid')
                name = data.get('name')
                if geid and name:
                    self.player_mapping[geid] = name
                    self.player_registered.emit(f"Registered player: {name} with geid: {geid}")
                    logging.info(f"Registered player: {name} geid: {geid}")
                continue
            game_mode_match = GAME_MODE_PATTERN.search(stripped_line)
            if game_mode_match:
                data = game_mode_match.groupdict()
                raw = data.get('game_mode')
                mapped = GAME_MODE_MAPPING.get(raw)
                if mapped and mapped != self.last_game_mode:
                    self.last_game_mode = mapped
                    self.game_mode_changed.emit(f"Monitoring game mode: {mapped}")
                elif not mapped:
                    logging.warning(f"Unknown game mode '{raw}'")

    def process_line(self, line):
        if not self.registered_user:
            logging.info("No registered user set; ignoring kill event.")
            return

        char_match = CHARACTER_CREATION_PATTERN.search(line)
        if char_match:
            data = char_match.groupdict()
            geid = data.get('geid')
            name = data.get('name')
            if geid and name:
                self.player_mapping[geid] = name
                self.player_registered.emit(f"Registered player: {name} with geid: {geid}")
                logging.info(f"Registered player: {name} geid: {geid}")
            return

        gm = GAME_MODE_PATTERN.search(line)
        if gm:
            data = gm.groupdict()
            gm_raw = data.get('game_mode')
            mapped = GAME_MODE_MAPPING.get(gm_raw)
            if mapped and mapped != self.last_game_mode:
                self.last_game_mode = mapped
                self.game_mode_changed.emit(f"Monitoring game mode: {mapped}")
            elif not mapped:
                logging.warning(f"Unknown game mode '{gm_raw}' encountered.")
            return

        kill_match = KILL_LOG_PATTERN.search(line)
        if kill_match:
            data = kill_match.groupdict()
            timestamp_iso = data.get('timestamp')
            try:
                timestamp = datetime.fromisoformat(timestamp_iso.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                timestamp = timestamp_iso

            victim_geid = data.get('victim_geid')
            victim = data.get('victim')
            attacker_geid = data.get('attacker_geid')
            attacker = data.get('attacker')
            zone = data.get('zone')
            damage_type = data.get('damage_type')
            weapon = data.get('weapon')
            trimmed_weapon = trim_suffix(weapon)
            trimmed_zone = trim_suffix(zone)
            victim_name = self.player_mapping.get(victim_geid, victim)
            attacker_name = self.player_mapping.get(attacker_geid, attacker)

            if victim_name.lower() == attacker_name.lower():
                logging.info("Ignoring suicide kill event.")
                return

            if attacker_name.lower() != self.registered_user.lower():
                logging.info("Ignoring kill event: kill not performed by the registered user.")
                return

            details = fetch_player_details(victim_name)
            victim_image_data_uri = fetch_victim_image_base64(victim_name)
            victim_profile_url = f"https://robertsspaceindustries.com/citizens/{quote(victim_name)}"
            victim_link = f'<a href="{victim_profile_url}" style="color:#f04747; text-decoration:none;">{victim_name}</a>'
            readout = f"""
            <html>
            <body>
                <table width="600" cellspacing="0" cellpadding="15" style=" background-color:#121212; font-family:Arial, sans-serif; color:#e0e0e0; box-shadow: 0 0 15px 5px #f04747, 0 0 20px 10px #f04747;">
                <tr>
                    <td style="vertical-align:top;">
                    <div style="font-size:20px; font-weight:bold; margin-bottom:10px;">New Kill Recorded</div>
                    <p style="font-size:14px; margin:4px 0;"><b>Attacker:</b> {attacker_name}</p>
                    <p style="font-size:14px; margin:4px 0;"><b>Victim:</b> {victim_link}</p>
                    <p style="font-size:14px; margin:4px 0;"><b>Engagement Victim:</b> {trimmed_zone}</p>
                    <p style="font-size:14px; margin:4px 0;"><b>Engagement Attacker:</b> {damage_type} using {trimmed_weapon}</p>
                    <p style="font-size:14px; margin:4px 0;"><b>Game Mode:</b> {self.last_game_mode if self.last_game_mode else 'Unknown'}</p>
                    <p style="font-size:14px; margin:4px 0;"><b>Timestamp:</b> {timestamp}</p>
                    <p style="font-size:14px; margin:4px 0;">
                        <b>Organization:</b> {details['org_name']} (Tag: 
                        <a href="https://robertsspaceindustries.com/en/orgs/{details['org_tag']}" style="color:#f04747; text-decoration:none;">{details['org_tag']}</a>)
                    </p>
                    </td>
                    <td style="vertical-align:top; text-align:right;">
                    <img src="{victim_image_data_uri}" width="100" height="100" style="object-fit:cover;" alt="Profile Image">
                    </td>
                </tr>
                </table>
                <br>
            </body>
            </html>
            """
            self.kill_detected.emit(readout, attacker_name)
            payload = {
                'log_line': line,
                'game_mode': self.last_game_mode if self.last_game_mode else "Unknown"
            }
            self.send_payload(payload, timestamp, attacker_name, readout)
            return

    def send_payload(self, payload, timestamp, attacker, readout):
        self.callback(payload, timestamp, attacker, readout)

    def stop(self):
        logging.info("Stopping TailThread.")
        self._stop_event = True

    def current_time(self):
        return time.strftime('%Y-%m-%dT%H:%M:%S')

#####################################################################
# Main GUI for the Kill Logger Client (Single-screen design)
#####################################################################
class KillLoggerGUI(QMainWindow):
    __client_id__ = "kill_logger_client"
    __version__ = "2.3"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCtool Logger 2.3")
        self.setWindowIcon(QIcon(resource_path("chris2.ico")))
        self.kill_count = 0
        self.monitor_thread = None
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

        self.init_ui()
        self.load_config()
        self.apply_styles()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Settings Section
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout()
        settings_layout.setSpacing(10)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your API key here")
        settings_layout.addRow("API Key:", self.api_key_input)

        log_path_layout = QHBoxLayout()
        self.log_path_input = QLineEdit()
        self.log_path_input.setPlaceholderText("Enter path to your Game.log")
        browse_log_btn = QPushButton("Browse")
        browse_log_btn.setIcon(QIcon(resource_path("browse_icon.png")))
        browse_log_btn.clicked.connect(self.browse_file)
        log_path_layout.addWidget(self.log_path_input)
        log_path_layout.addWidget(browse_log_btn)
        settings_layout.addRow("Game.log Path:", log_path_layout)

        # Kill Sound Settings
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

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # Kill Logs Section (using a QTextBrowser)
        self.kill_display = QTextBrowser()
        self.kill_display.setReadOnly(True)
        self.kill_display.setOpenExternalLinks(True)
        main_layout.addWidget(self.kill_display, stretch=1)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("color: #cfcfcf;")
        self.setMinimumSize(900, 700)

    def apply_styles(self):
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

    def on_kill_sound_toggled(self, state):
        self.kill_sound_enabled = (state == Qt.Checked)
        self.save_config()

    def on_kill_sound_file_browse(self):
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

    def on_kill_sound_volume_changed(self, value):
        self.kill_sound_volume = value
        self.save_config()

    def browse_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Game.log File", "",
            "Log Files (*.log);;All Files (*)", options=options
        )
        if file_path:
            self.log_path_input.setText(file_path)

    def ping_api(self):
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

    def toggle_monitoring(self):
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait()
            self.monitor_thread = None
            self.start_button.setText("Start Monitoring")
            self.append_kill_readout("Monitoring stopped.")
            self.status_bar.showMessage("Monitoring stopped.", 5000)
            self.save_config()
            self.delete_kill_logger_log()
        else:
            self.load_config()
            self.local_user_name = ""
            self.registration_attempts = 0

            self.api_key = self.api_key_input.text().strip()
            log_path = self.log_path_input.text().strip()
            if not self.api_key:
                QMessageBox.warning(self, "Input Error", "Please enter your API key.")
                return
            if not log_path or not os.path.isfile(log_path):
                QMessageBox.warning(self, "Input Error", "Please enter a valid path to your Game.log file.")
                return

            if not self.ping_api():
                QMessageBox.critical(self, "API Error", "Unable to connect to the API. Check your network and API key.")
                return

            self.monitor_thread = TailThread(log_path, self.handle_payload)
            self.monitor_thread.kill_detected.connect(self.on_kill_detected)
            self.monitor_thread.player_registered.connect(self.append_api_response)
            self.monitor_thread.player_registered.connect(self.on_player_registered)
            self.monitor_thread.game_mode_changed.connect(self.on_game_mode_changed)
            self.monitor_thread.start()
            self.start_button.setText("Stop Monitoring")
            self.append_kill_readout("Monitoring started...")
            self.status_bar.showMessage("Monitoring started.", 5000)
            self.save_config()

    def on_player_registered(self, text):
        match = re.search(r"Registered player:\s+(.+?)\s+with geid:\s+(\d+)", text)
        if match:
            name = match.group(1).strip()
            if not self.local_user_name:
                self.local_user_name = name
                if self.monitor_thread:
                    self.monitor_thread.registered_user = self.local_user_name
                logging.info(f"Local registered user set to: {self.local_user_name}")
                self.registration_attempts = 0
                msg = f"Connected to API, monitoring kills for {self.local_user_name}"
                self.status_bar.showMessage(msg, 5000)
                self.append_kill_readout(msg)
                self.save_config()

    def on_game_mode_changed(self, mode_msg):
        self.status_bar.showMessage(mode_msg, 5000)
        self.append_kill_readout(mode_msg)

    def on_kill_detected(self, readout, attacker):
        self.append_kill_readout(readout)
        if self.kill_sound_enabled:
            self.kill_sound_effect.setSource(QUrl.fromLocalFile(self.kill_sound_path))
            self.kill_sound_effect.setVolume(self.kill_sound_volume / 100.0)
            self.kill_sound_effect.play()

    def handle_payload(self, payload, timestamp, attacker, readout):
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
            'User-Agent': self.user_agent,
            'X-Client-ID': self.__client_id__,
            'X-Client-Version': self.__version__
        }
        max_retries = 5
        retry_count = 0
        backoff = 1
        while retry_count < max_retries:
            try:
                resp = requests.post(self.api_endpoint, headers=headers, json=payload, timeout=10)
                if resp.status_code == 201:
                    kill_id_resp = resp.json().get('kill_id', 'N/A')
                    formatted = (
                        f"[{timestamp}] VICTIM: {payload.get('victim_name', 'N/A')} killed by {payload.get('player_name', 'N/A')} "
                        f"with game mode '{payload.get('game_mode', 'Unknown')}' (Kill ID: {kill_id_resp})"
                    )
                    logging.info(formatted)
                    return
                elif resp.status_code == 200:
                    data = resp.json()
                    if data.get("message") == "NPC not logged":
                        logging.info(f"[{timestamp}] NPC kill detected; kill not logged.")
                        return
                elif 400 <= resp.status_code < 500:
                    error_text = f"[{timestamp}] Failed to log kill: {resp.status_code} - {resp.text}"
                    logging.error(error_text)
                    QMessageBox.critical(self, "API Error", error_text)
                    return
                else:
                    raise requests.exceptions.HTTPError(f"Server error: {resp.status_code}")
            except requests.exceptions.RequestException as e:
                retry_count += 1
                error_text = f"[{timestamp}] API request failed (Attempt {retry_count}/{max_retries}): {e}"
                logging.error(error_text)
                time.sleep(backoff)
                backoff *= 2

        fail_text = f"[{timestamp}] Error sending kill data after {max_retries} attempts."
        logging.error(fail_text)
        retry = QMessageBox.question(
            self,
            "API Error",
            f"{fail_text}\nWould you like to try sending this kill again?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if retry == QMessageBox.Yes:
            self.handle_payload(payload, timestamp, attacker, readout)
        else:
            return

    def append_kill_readout(self, text):
        self.kill_display.append(text)
        self.kill_display.verticalScrollBar().setValue(self.kill_display.verticalScrollBar().maximum())

    def append_api_response(self, text):
        logging.info(text)

    def closeEvent(self, event):
        if self.monitor_thread and self.monitor_thread.isRunning():
            reply = QMessageBox.question(
                self, 'Confirm Exit',
                "Monitoring is active. Stop and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.monitor_thread.stop()
                self.monitor_thread.wait()
                self.monitor_thread = None
                self.start_button.setText("Start Monitoring")
                self.append_kill_readout("Monitoring stopped.")
                self.status_bar.showMessage("Monitoring stopped.", 5000)
                self.save_config()
                self.delete_kill_logger_log()
                event.accept()
            else:
                event.ignore()
                return
        else:
            self.delete_kill_logger_log()
            event.accept()

    def load_config(self):
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
            except Exception as e:
                logging.error(f"Failed to load config: {e}")

    def save_config(self):
        config = {
            'monitoring_active': self.monitor_thread.isRunning() if self.monitor_thread else False,
            'kill_sound': self.kill_sound_enabled,
            'kill_sound_path': self.kill_sound_path_input.text().strip(),
            'kill_sound_volume': self.volume_slider.value(),
            'log_path': self.log_path_input.text().strip(),
            'api_key': self.api_key_input.text().strip(),
            'local_user_name': self.local_user_name
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def delete_kill_logger_log(self):
        try:
            if os.path.isfile(LOG_FILE):
                os.remove(LOG_FILE)
        except Exception as e:
            logging.error(f"Failed to delete kill_logger.log: {e}")

    def check_for_updates(self):
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

    def notify_update(self, latest_version, download_url):
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

def cleanup_log_file():
    try:
        if os.path.isfile(LOG_FILE):
            os.remove(LOG_FILE)
            print(f"{LOG_FILE} deleted successfully.")
    except Exception as e:
        print(f"Failed to delete {LOG_FILE}: {e}")

atexit.register(cleanup_log_file)

def main():
    app = QApplication(sys.argv)
    gui = KillLoggerGUI()
    gui.check_for_updates()
    dark_title_bar_for_pyqt5(gui)
    gui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
