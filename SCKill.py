__client_id__ = "kill_logger_client"
__version__ = "2.0"

import sys
import os
import re
import json
import requests
import logging
import atexit
import uuid
import time
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
from packaging import version
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtCore import (
    Qt, pyqtSignal, QThread, QStandardPaths, QDir, QUrl, QPoint, QRect
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QTextEdit, QFileDialog, QVBoxLayout, QHBoxLayout, QMessageBox,
    QGroupBox, QGridLayout, QSizePolicy, QSplitter,
    QCheckBox, QSpinBox,
    QFrame
)
from PyQt5.QtGui import QIcon, QFont

#####################################################################
# Enable dark title bar on Windows 10/11 using DwmSetWindowAttribute.
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

####################################################################
# Locate resources for PyInstaller or development.
####################################################################
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

####################################################################
# Redirect config and log files to a writable location (AppData).
####################################################################
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

####################################################################
# Define the latest Chrome User-Agent for HTTP requests.
####################################################################
CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)

####################################################################
# Set up logging.
####################################################################
logging.basicConfig(
    filename=LOG_FILE,
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

####################################################################
# Regular expression patterns for parsing log entries.
####################################################################
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

####################################################################
# Utility to trim numeric suffix from names.
####################################################################
def trim_suffix(name):
    if not name:
        return 'Unknown'
    return re.sub(r'_\d+$', '', name)

####################################################################
# TailThread: Monitors the log file for new entries.
####################################################################
class TailThread(QThread):
    kill_detected = pyqtSignal(str)
    player_registered = pyqtSignal(str)

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
                if mapped:
                    self.last_game_mode = mapped
                else:
                    logging.warning(f"Unknown game mode '{raw}'")
    
    def process_line(self, line):
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
            if mapped:
                self.last_game_mode = mapped
            else:
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

            readout = (
                f"ID: {str(uuid.uuid4())}<br>"
                f"VICTIM: <a href='https://robertsspaceindustries.com/citizens/{victim_name}'>{victim_name}</a><br>"
                f"KILLED BY: {attacker_name}<br>"
                f"TIME: {timestamp}<br>"
                f"SHIP/ZONE TYPE: {trimmed_zone}<br>"
                f"DAMAGE: {damage_type}<br>"
                f"WEAPON: {trimmed_weapon}<br>"
                f"GAME MODE: {self.last_game_mode if self.last_game_mode else 'Unknown'}<br>"
                "<hr>"
            )

            self.kill_detected.emit(readout)
            payload = {'log_line': line}
            self.send_payload(payload, timestamp, attacker_name, readout)
            return

    def send_payload(self, payload, timestamp, attacker, readout):
        self.callback(payload, timestamp, attacker, readout)

    def stop(self):
        logging.info("Stopping TailThread.")
        self._stop_event = True

    def current_time(self):
        return time.strftime('%Y-%m-%dT%H:%M:%S')

####################################################################
# Main GUI for the Kill Logger Client.
####################################################################
class KillLoggerGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon(resource_path("chris2.ico")))
        self.setWindowTitle("SCtool Logger 2.0")

        self.kill_count = 0
        self.monitor_thread = None

        self.api_endpoint = "https://starcitizentool.com/api/v1/kills"
        self.user_agent = CHROME_USER_AGENT
        self.local_user_name = None

        self.dark_mode_enabled = False
        self.kill_sound_enabled = False
        self.kill_sound_effect = QSoundEffect()
        self.kill_sound_path = resource_path("kill.wav")
        self.kill_sound_volume = 100
        self.api_key = ""

        self.init_ui()
        self.load_config()
        self.apply_dark_mode(self.dark_mode_enabled)
        self.auto_start_monitoring_if_configured()

    def init_ui(self):
        central_widget = QWidget()
        central_layout = QVBoxLayout()
        central_layout.setContentsMargins(10, 10, 10, 10)
        central_layout.setSpacing(10)

        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()

        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your API key here")
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)

        log_path_layout = QHBoxLayout()
        log_path_label = QLabel("Game.log Path:")
        self.log_path_input = QLineEdit()
        self.log_path_input.setPlaceholderText("Enter path to your Game.log")
        browse_button = QPushButton("Browse")
        browse_button.setIcon(QIcon(resource_path("browse_icon.png")))
        browse_button.clicked.connect(self.browse_file)
        log_path_layout.addWidget(log_path_label)
        log_path_layout.addWidget(self.log_path_input)
        log_path_layout.addWidget(browse_button)

        extras_group = QGroupBox("Extras")
        extras_layout = QHBoxLayout()

        self.dark_mode_checkbox = QCheckBox("Enable Dark Mode")
        self.dark_mode_checkbox.setChecked(False)
        self.dark_mode_checkbox.stateChanged.connect(self.on_dark_mode_toggled)

        self.kill_sound_checkbox = QCheckBox("Enable Kill Sound")
        self.kill_sound_checkbox.setChecked(False)
        self.kill_sound_checkbox.stateChanged.connect(self.on_kill_sound_toggled)

        extras_layout.addWidget(self.dark_mode_checkbox)
        extras_layout.addWidget(self.kill_sound_checkbox)
        extras_group.setLayout(extras_layout)

        kill_sound_group = QGroupBox("Kill Sound Settings")
        kill_sound_layout = QVBoxLayout()

        sound_path_layout = QHBoxLayout()
        self.kill_sound_path_label = QLabel("Kill Sound File:")
        self.kill_sound_path_input = QLineEdit()
        self.kill_sound_path_input.setText(self.kill_sound_path)
        self.kill_sound_path_browse_button = QPushButton("Browse")
        self.kill_sound_path_browse_button.clicked.connect(self.on_kill_sound_file_browse)
        sound_path_layout.addWidget(self.kill_sound_path_label)
        sound_path_layout.addWidget(self.kill_sound_path_input)
        sound_path_layout.addWidget(self.kill_sound_path_browse_button)

        volume_layout = QHBoxLayout()
        volume_label = QLabel("Kill Sound Volume:")
        self.kill_sound_volume_spinbox = QSpinBox()
        self.kill_sound_volume_spinbox.setRange(0, 100)
        self.kill_sound_volume_spinbox.setValue(self.kill_sound_volume)
        self.kill_sound_volume_spinbox.valueChanged.connect(self.on_kill_sound_volume_changed)
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.kill_sound_volume_spinbox)

        kill_sound_layout.addLayout(sound_path_layout)
        kill_sound_layout.addLayout(volume_layout)
        kill_sound_group.setLayout(kill_sound_layout)

        self.start_button = QPushButton("Start Monitoring")
        self.start_button.setIcon(QIcon(resource_path("start_icon.png")))
        self.start_button.clicked.connect(self.toggle_monitoring)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)

        settings_layout.addLayout(api_key_layout)
        settings_layout.addLayout(log_path_layout)
        settings_layout.addWidget(extras_group)
        settings_layout.addWidget(kill_sound_group)
        settings_layout.addLayout(button_layout)
        settings_group.setLayout(settings_layout)

        logs_group = QGroupBox("Logs")
        logs_layout = QVBoxLayout()

        kill_readouts_group = QGroupBox("Kill Readouts")
        kill_readouts_layout = QVBoxLayout()
        self.kill_display = QTextEdit()
        self.kill_display.setReadOnly(True)
        kill_readouts_layout.addWidget(self.kill_display)
        kill_readouts_group.setLayout(kill_readouts_layout)

        logs_layout.addWidget(kill_readouts_group)
        logs_group.setLayout(logs_layout)

        central_layout.addWidget(settings_group, stretch=0)
        central_layout.addWidget(logs_group, stretch=1)
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)
        self.status_bar = self.statusBar()

    ####################################################################
    # Dark Mode and Kill Sound Toggle Handlers
    ####################################################################
    def on_dark_mode_toggled(self, state):
        self.dark_mode_enabled = (state == Qt.Checked)
        self.apply_dark_mode(self.dark_mode_enabled)
        self.save_config()

    def apply_dark_mode(self, enable):
        base_layout_styles = """
        QGroupBox {
            padding: 10px;
            margin-top: 8px;
        }
        QLabel {
            padding: 2px;
            background-color: transparent;
        }
        QPushButton {
            padding: 6px;
            margin: 4px;
        }
        QHeaderView::section {
            padding: 4px;
        }
        """
        if enable:
            dark_color_styles = """
            QMainWindow, QWidget, QDialog, QFrame {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QGroupBox {
                background-color: #2d2d2d;
                border: 1px solid #444444;
                color: #ffffff;
            }
            QPushButton {
                background-color: #444444;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox, QCheckBox {
                background-color: #3d3d3d;
                color: #ffffff;
                selection-background-color: #555555;
                selection-color: #ffffff;
            }
            """
            full_stylesheet = base_layout_styles + dark_color_styles
        else:
            light_color_styles = """
            QMainWindow, QWidget, QDialog, QFrame {
                background-color: #ffffff;
                color: #000000;
            }
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                color: #000000;
            }
            QPushButton {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #cccccc;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox, QCheckBox {
                background-color: #f9f9f9;
                color: #000000;
                selection-background-color: #d0d0d0;
                selection-color: #000000;
            }
            """
            full_stylesheet = base_layout_styles + light_color_styles
        self.setStyleSheet(full_stylesheet)

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

    ####################################################################
    # Monitoring Logic
    ####################################################################
    def browse_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Game.log File", "",
            "Log Files (*.log);;All Files (*)", options=options
        )
        if file_path:
            self.log_path_input.setText(file_path)

    def toggle_monitoring(self):
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait()
            self.monitor_thread = None
            self.start_button.setText("Start Monitoring")
            self.append_kill_readout("Monitoring stopped.\n")
            self.status_bar.showMessage("Monitoring stopped.", 5000)
            self.save_config()
            self.delete_kill_logger_log()
        else:
            self.api_key = self.api_key_input.text().strip()
            log_path = self.log_path_input.text().strip()
            if not self.api_key:
                QMessageBox.warning(self, "Input Error", "Please enter your API key.")
                return
            if not log_path or not os.path.isfile(log_path):
                QMessageBox.warning(self, "Input Error", "Please enter a valid path to your Game.log file.")
                return
            self.monitor_thread = TailThread(log_path, self.handle_payload)
            self.monitor_thread.kill_detected.connect(self.append_kill_readout)
            self.monitor_thread.player_registered.connect(self.append_api_response)
            self.monitor_thread.player_registered.connect(self.on_player_registered)
            self.monitor_thread.start()
            self.start_button.setText("Stop Monitoring")
            self.append_kill_readout("Monitoring started...\n")
            self.status_bar.showMessage("Monitoring started.", 5000)
            self.save_config()

    def on_player_registered(self, text):
        match = re.search(r"Registered player:\s+(.+?)\s+with geid:\s+(\d+)", text)
        if match:
            name = match.group(1).strip()
            if self.local_user_name is None:
                self.local_user_name = name
                if self.monitor_thread:
                    self.monitor_thread.registered_user = self.local_user_name
                logging.info(f"Local registered user set to: {self.local_user_name}")

    def handle_payload(self, payload, timestamp, attacker, readout):
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
            'User-Agent': self.user_agent,
            'X-Client-ID': __client_id__,
            'X-Client-Version': __version__
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
                        f"with game mode '{payload.get('game_mode', 'Unknown')}' (Kill ID: {kill_id_resp})\n"
                    )
                    logging.info(formatted)
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
        QMessageBox.critical(self, "API Error", fail_text)

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
                self.append_kill_readout("Monitoring stopped.\n")
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
                self.monitoring_active = config.get('monitoring_active', False)
                self.dark_mode_enabled = config.get('dark_mode', False)
                self.kill_sound_enabled = config.get('kill_sound', False)
                self.kill_sound_path = config.get('kill_sound_path', resource_path("kill.wav"))
                self.kill_sound_volume = config.get('kill_sound_volume', 100)
                self.log_path_input.setText(config.get('log_path', ''))
                self.api_key = config.get('api_key', '')
                self.api_key_input.setText(self.api_key)
                self.dark_mode_checkbox.setChecked(self.dark_mode_enabled)
                self.kill_sound_checkbox.setChecked(self.kill_sound_enabled)
                self.kill_sound_path_input.setText(self.kill_sound_path)
                self.kill_sound_volume_spinbox.setValue(self.kill_sound_volume)
            except Exception as e:
                logging.error(f"Failed to load config: {e}")
                self.monitoring_active = False
        else:
            self.monitoring_active = False

    def save_config(self):
        config = {
            'monitoring_active': self.monitor_thread.isRunning() if self.monitor_thread else False,
            'dark_mode': self.dark_mode_enabled,
            'kill_sound': self.kill_sound_enabled,
            'kill_sound_path': self.kill_sound_path_input.text().strip(),
            'kill_sound_volume': self.kill_sound_volume_spinbox.value(),
            'log_path': self.log_path_input.text().strip(),
            'api_key': self.api_key_input.text().strip()
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def auto_start_monitoring_if_configured(self):
        log_path = self.log_path_input.text().strip()
        if self.monitoring_active and log_path and os.path.isfile(log_path):
            self.monitor_thread = TailThread(log_path, self.handle_payload)
            self.monitor_thread.kill_detected.connect(self.append_kill_readout)
            self.monitor_thread.player_registered.connect(self.append_api_response)
            self.monitor_thread.player_registered.connect(self.on_player_registered)
            self.monitor_thread.start()
            self.start_button.setText("Stop Monitoring")
            self.append_kill_readout("Monitoring started automatically...\n")
            self.status_bar.showMessage("Monitoring started automatically.", 5000)

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
            if latest and version.parse(__version__) < version.parse(latest):
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
