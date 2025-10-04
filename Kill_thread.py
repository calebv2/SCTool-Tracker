# Kill_thread.py

import os
import re
import base64
import requests
import logging
import json
import time
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote
from typing import Optional, Dict, Any, List

from PyQt5.QtCore import pyqtSignal, QThread, QDir, QTimer, Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QMessageBox
)

from language_manager import t

from kill_parser import GAME_MODE_MAPPING, GAME_MODE_PATTERN, KILL_LOG_PATTERN, CHROME_USER_AGENT, KillParser
from language_manager import t

from Registered_kill import format_registered_kill
from vehicle_event_correlator import VehicleEventCorrelator

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": CHROME_USER_AGENT})
cleanupPattern = re.compile(r'^(.+?)_\d+$')

class MissingKillsDialog(QDialog):
    def __init__(self, missing_kills, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("Missing Kills Found"))
        self.missing_kills = missing_kills
        self.checkbox_list = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        info_label = QLabel(t("Select which kills you'd like to send:"))
        layout.addWidget(info_label)

        self.toggle_checkbox = QCheckBox(t("Deselect All"))
        self.toggle_checkbox.setChecked(True)
        self.toggle_checkbox.stateChanged.connect(self.on_toggle_changed)
        layout.addWidget(self.toggle_checkbox)

        for kill in self.missing_kills:
            local_key = kill.get("local_key", "Unknown")
            parts = local_key.split("::")
            if len(parts) >= 3:
                label_text = f"{parts[1]} ({parts[2]})"
            else:
                label_text = local_key
            checkbox = QCheckBox(label_text)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.on_individual_checkbox_changed)
            layout.addWidget(checkbox)
            self.checkbox_list.append((checkbox, kill))

        button_layout = QHBoxLayout()
        send_button = QPushButton(t("Send Selected"))
        send_button.clicked.connect(self.accept)
        cancel_button = QPushButton(t("Cancel"))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(send_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.initStyles()

    def on_toggle_changed(self, state):
        """Handle toggle checkbox state change - toggles all checkboxes and updates text"""
        if state == Qt.Checked:
            self.toggle_checkbox.setText(t("Deselect All"))
            for checkbox, _ in self.checkbox_list:
                checkbox.blockSignals(True)
                checkbox.setChecked(True)
                checkbox.blockSignals(False)
        else:
            self.toggle_checkbox.setText(t("Select All"))
            for checkbox, _ in self.checkbox_list:
                checkbox.blockSignals(True)
                checkbox.setChecked(False)
                checkbox.blockSignals(False)

    def getSelectedKills(self):
        selected = []
        for checkbox, kill_data in self.checkbox_list:
            if checkbox.isChecked():
                selected.append(kill_data)
        return selected

    def on_select_all_changed(self, state):
        """Handle Select All checkbox state change"""
        if state == Qt.Checked:
            self.deselect_all_checkbox.blockSignals(True)
            self.deselect_all_checkbox.setChecked(False)
            self.deselect_all_checkbox.blockSignals(False)
            
            for checkbox, _ in self.checkbox_list:
                checkbox.blockSignals(True)
                checkbox.setChecked(True)
                checkbox.blockSignals(False)

    def on_deselect_all_changed(self, state):
        """Handle Deselect All checkbox state change"""
        if state == Qt.Checked:
            self.select_all_checkbox.blockSignals(True)
            self.select_all_checkbox.setChecked(False)
            self.select_all_checkbox.blockSignals(False)
            
            for checkbox, _ in self.checkbox_list:
                checkbox.blockSignals(True)
                checkbox.setChecked(False)
                checkbox.blockSignals(False)

    def on_individual_checkbox_changed(self, state):
        """Handle individual checkbox state changes to update toggle checkbox state and text"""
        all_checked = True
        all_unchecked = True
        
        for checkbox, _ in self.checkbox_list:
            if checkbox.isChecked():
                all_unchecked = False
            else:
                all_checked = False
        
        self.toggle_checkbox.blockSignals(True)
        
        if all_checked:
            self.toggle_checkbox.setChecked(True)
            self.toggle_checkbox.setText(t("Deselect All"))
        elif all_unchecked:
            self.toggle_checkbox.setChecked(False)
            self.toggle_checkbox.setText(t("Select All"))
        else:
            self.toggle_checkbox.setChecked(False)
            self.toggle_checkbox.setText(t("Select All"))
        
        self.toggle_checkbox.blockSignals(False)

    def initStyles(self):
        self.setStyleSheet(
            "QDialog { background-color: #0d0d0d; color: #f0f0f0; border: 1px solid #f04747; }"
            "QLabel { color: #f0f0f0; font-weight: bold; font-size: 14px; }"
            "QCheckBox { color: #f0f0f0; }"
            "QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #2a2a2a; "
            "   border-radius: 3px; background-color: #1e1e1e; }"
            "QCheckBox::indicator:checked { background-color: #f04747; }"
            "QPushButton { background-color: #1e1e1e; border: 1px solid #2a2a2a; "
            "   border-radius: 4px; padding: 8px 12px; color: #f0f0f0; }"
            "QPushButton:hover { background-color: #2a2a2a; border-color: #f04747; }"
        )

class TailThread(QThread):
    kill_detected = pyqtSignal(str, str)
    death_detected = pyqtSignal(str, str)
    player_registered = pyqtSignal(str)
    game_mode_changed = pyqtSignal(str)
    payload_ready = pyqtSignal(dict, str, str, str)
    death_payload_ready = pyqtSignal(dict, str, str, str)
    ship_updated = pyqtSignal(str)

    def __init__(self, file_path: str, config_file: Optional[str] = None, callback=None, parent=None) -> None:
        super().__init__(parent)
        self.file_path = file_path
        self.config_file = config_file
        self._stop_event = False
        self.last_game_mode: str = "Unknown"
        self.registered_user: Optional[str] = None
        self.has_registered = False
        self.current_attacker_ship: Optional[str] = "Player destruction"
        self.gui_parent = parent
        
        self.vehicle_correlator = VehicleEventCorrelator(event_callback=self.handle_correlated_vehicle_kill)
        self.vehicle_correlator.start_cleanup_thread()

    def reset_killer_ship(self) -> None:
        self.current_attacker_ship = "No Ship"
        self.update_config_killer_ship("No Ship")
        self.ship_updated.emit("No Ship")

    def update_config_killer_ship(self, ship: str) -> None:
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        logging.debug(f"Config file {self.config_file} is empty; using default config")
                        config = {}
                    else:
                        try:
                            config = json.loads(content)
                        except json.JSONDecodeError as e:
                            logging.error(f"Error parsing JSON config at {self.config_file}: {e}")
                            config = {}
            except Exception as e:
                logging.error(f"Error reading config file {self.config_file}: {e}")
                config = {}
            config["killer_ship"] = ship
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                logging.info(f"Updated config with killer_ship: {ship}")
            except Exception as e:
                logging.error(f"Error saving config with killer_ship: {e}")

    def clear_config_killer_ship(self) -> None:
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        logging.debug(f"Config file {self.config_file} is empty when clearing killer_ship; using default config")
                        config = {}
                    else:
                        try:
                            config = json.loads(content)
                        except json.JSONDecodeError as e:
                            logging.error(f"Error parsing JSON config for clearing killer_ship at {self.config_file}: {e}")
                            config = {}
            except Exception as e:
                logging.error(f"Error reading config for clearing killer_ship: {e}")
                config = {}
            if "killer_ship" in config:
                del config["killer_ship"]
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                logging.info("Cleared killer_ship from config.")
            except Exception as e:
                logging.error(f"Error saving config while clearing killer_ship: {e}")

    def reconstruct_ship_history(self, f) -> None:
        """Reconstruct ship history from the beginning of the log file to get current ship state"""
        logging.info("Reconstructing ship history from log file...")
        current_pos = f.tell()
        f.seek(0)
        
        jump_drive_pattern = re.compile(r'\(adam:\s+(?P<ship>(?:[A-Za-z0-9_]+?)(?=_\d+\s+in zone)|[A-Za-z0-9_]+)\s+in zone')
        last_ship = None
        ship_count = 0
        
        try:
            for line in f:
                if self._stop_event:
                    break
                    
                stripped = line.strip()
                j_match = jump_drive_pattern.search(stripped)
                if j_match:
                    raw_ship = j_match.group('ship')
                    
                    if not re.match(r'^(ORIG|CRUS|RSI|AEGS|VNCL|DRAK|ANVL|BANU|MISC|CNOU|XIAN|GAMA|TMBL|ESPR|KRIG|GRIN|XNAA|MRAI)', raw_ship):
                        continue
                    
                    cleaned_ship = re.sub(r'_\d+$', '', raw_ship)
                    cleaned_ship = cleaned_ship.replace('_', ' ')
                    cleaned_ship = re.sub(r'\s+\d+$', '', cleaned_ship)
                    
                    last_ship = cleaned_ship
                    ship_count += 1
                    
        except Exception as e:
            logging.error(f"Error reconstructing ship history: {e}")
        finally:
            f.seek(current_pos)
            
        if last_ship:
            self.current_attacker_ship = last_ship
            self.update_config_killer_ship(last_ship)
            self.ship_updated.emit(last_ship)
            logging.info(f"Ship history reconstruction: Found {ship_count} ship changes, current ship: {last_ship}")
        else:
            logging.info("Ship history reconstruction: No ships found in log history")

    def run(self) -> None:
        logging.info("TailThread started.")
        timeout_seconds = 10
        while not self._stop_event:
            try:
                with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                    self.process_existing_player_registrations(f)
                    self.reconstruct_ship_history(f)
                    f.seek(0, os.SEEK_END)
                    last_activity = time.time()
                    logging.info(f"Started tailing {self.file_path} for new entries...")
                    while not self._stop_event:
                        line = f.readline()
                        if line:
                            self.process_line(line.strip())
                            last_activity = time.time()
                        else:
                            try:
                                current_size = os.path.getsize(self.file_path)
                                if f.tell() > current_size:
                                    logging.info("Detected file truncation. Resetting pointer to beginning.")
                                    f.seek(0, os.SEEK_SET)
                                    last_activity = time.time()
                            except Exception as e:
                                logging.error(f"Error checking file size: {e}")
                            
                            if time.time() - last_activity > timeout_seconds:
                                try:
                                    if os.path.getsize(self.file_path) == 0:
                                        logging.info("Log file appears empty. Waiting for new entries...")
                                        f.seek(0, os.SEEK_SET)
                                        last_activity = time.time()
                                except Exception as e:
                                    logging.error(f"Error checking file size: {e}")
                            time.sleep(0.1)
            except Exception as e:
                logging.error(f"Error in TailThread: {e}")
            time.sleep(0.5)
        logging.info("TailThread terminated.")

    def process_existing_player_registrations(self, f) -> None:
        logging.info("Processing existing entries for legacy login responses and game modes...")
        for line in f:
            stripped_line = line.strip()
            legacy_login_match = re.search(
                r"<(?P<timestamp>[^>]+)> \[Notice\] <Legacy login response> \[CIG-net\] User Login Success - Handle\[(?P<handle>[^\]]+)\]",
                stripped_line
            )
            if legacy_login_match:
                handle = legacy_login_match.group('handle').strip()
                if self.registered_user != handle:
                    self.registered_user = handle
                    self.has_registered = True
                    self.player_registered.emit(f"Registered user: {handle}")
                    logging.info(f"Updated registered user to: {handle}")
            gm_match = GAME_MODE_PATTERN.search(stripped_line)
            if gm_match:
                data = gm_match.groupdict()
                raw = data.get('game_mode')
                mapped = GAME_MODE_MAPPING.get(raw)
                if mapped and mapped != self.last_game_mode:
                    self.last_game_mode = mapped
                    self.game_mode_changed.emit(f"Monitoring game mode: {mapped}")
                    self.reset_killer_ship()
                elif not mapped:
                    logging.warning(f"Unknown game mode '{raw}'")

    def process_jump_drive_line(self, line: str) -> None:
        match = re.search(r'\(adam:\s+(?P<ship>(?:[A-Za-z0-9_]+?)(?=_\d+\s+in zone)|[A-Za-z0-9_]+)\s+in zone', line)
        if match:
            raw_ship = match.group('ship')
            if not re.match(r'^(ORIG|CRUS|RSI|AEGS|VNCL|DRAK|ANVL|BANU|MISC|CNOU|XIAN|GAMA|TMBL|ESPR|KRIG|GRIN|XNAA|MRAI)', raw_ship):
                logging.warning(f"Jump Drive: Ship name doesn't have a recognized manufacturer code: {raw_ship}")
                return

            cleaned_ship = re.sub(r'_\d+$', '', raw_ship)
            cleaned_ship = cleaned_ship.replace('_', ' ')
            cleaned_ship = re.sub(r'\s+\d+$', '', cleaned_ship)
            
            self.current_attacker_ship = cleaned_ship
            logging.info(f"Jump Drive: Updated killer ship to: {cleaned_ship}")
            self.update_config_killer_ship(cleaned_ship)
            self.ship_updated.emit(cleaned_ship)

    def process_line(self, line: str) -> None:
        """Process a single line from the log file"""
        try:
            _, correlated_events = self.vehicle_correlator.process_log_line(line.strip())
            for event in correlated_events:
                self.handle_correlated_vehicle_kill(event)
        except Exception as e:
            logging.error(f"Error processing vehicle correlation: {e}")
        
        if "<Jump Drive Requesting State Change>" in line:
            self.process_jump_drive_line(line)
        legacy_login_match = re.search(
            r"<(?P<timestamp>[^>]+)> \[Notice\] <Legacy login response> \[CIG-net\] User Login Success - Handle\[(?P<handle>[^\]]+)\]",
            line
        )
        if legacy_login_match:
            handle = legacy_login_match.group('handle').strip()
            if self.registered_user != handle:
                self.registered_user = handle
                self.has_registered = True
                self.player_registered.emit(f"Registered user updated: {handle}")
                logging.info(f"Updated registered user to: {handle}")
            return
        gm_match = GAME_MODE_PATTERN.search(line)
        if gm_match:
            data = gm_match.groupdict()
            gm_raw = data.get('game_mode')
            mapped = GAME_MODE_MAPPING.get(gm_raw, gm_raw)
            if mapped and mapped != self.last_game_mode:
                self.last_game_mode = mapped
                self.game_mode_changed.emit(f"Monitoring game mode: {mapped}")
            elif not mapped:
                logging.warning(f"Unknown game mode '{gm_raw}' encountered.")
            return
        kill_match = KILL_LOG_PATTERN.search(line)
        if kill_match:
            self.handle_kill_event(line, kill_match)

    def handle_correlated_vehicle_kill(self, event: dict) -> None:
        """Handle events from vehicle correlation system"""
        if not self.registered_user:
            return
        
        event_type = event.get('event_type', 'unknown')
        
        if event_type == 'vehicle_destruction':
            self.handle_vehicle_destruction_event(event)
        elif event_type == 'correlated_vehicle_kill':
            self.handle_actual_vehicle_kill(event)
        elif event_type == 'ejection':
            self.handle_ejection_event(event)
        elif event_type == 'seat_exit':
            self.handle_seat_exit_event(event)
        else:
            logging.warning(f"Unknown event type from correlator: {event_type}")
    
    def handle_vehicle_destruction_event(self, event: dict) -> None:
        """Handle pure vehicle destruction events (no occupants killed)"""
        destroyer = event.get('destroyer', '').strip()
        vehicle_name = event.get('vehicle_name', '')
        timestamp = event.get('timestamp', '')
        destroy_level = event.get('destroy_level', 0)
        
        if KillParser.is_npc(destroyer):
            logging.info(f"NPC vehicle destruction detected (destroyer: {destroyer}). Not showing.")
            return
        
        if self.gui_parent:
            if destroy_level == 1 and not getattr(self.gui_parent, 'show_vehicle_disabled', True):
                logging.debug(f"Vehicle disabled event hidden by user preference: {vehicle_name}")
                return
            elif destroy_level == 2 and not getattr(self.gui_parent, 'show_vehicle_destroyed', True):
                logging.debug(f"Vehicle destroyed event hidden by user preference: {vehicle_name}")
                return
        
        cleaned_vehicle = re.sub(r'_\d+$', '', vehicle_name)
        cleaned_vehicle = re.sub(r'\s+\d+$', '', cleaned_vehicle)
        cleaned_vehicle = cleaned_vehicle.replace('_', ' ')
        
        if destroyer.lower() == self.registered_user.strip().lower():
            if destroy_level == 1:
                destruction_type = "DISABLED"
            elif destroy_level == 2:
                destruction_type = "DESTROYED"
            else:
                destruction_type = "DAMAGED"
            empty_line_html = ''
            if destruction_type == 'DESTROYED':
                empty_line_html = '<div style="font-size: 14px; color: #ff9900; margin-bottom: 3px;">EMPTY VEHICLE DESTROYED</div>'

            readout = f"""
            <div class="newEntry">
                <table class="event-table" style="background: linear-gradient(135deg, #151515, #0d0d0d); color: #e0e0e0; border-radius: 10px; margin-bottom: 15px; width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 12px 15px; text-align: left; border-bottom: 1px solid #333333;">
                            <div style="font-size: 18px; font-weight: bold; color: #00ccff; margin-bottom: 5px;">VEHICLE {destruction_type}</div>
                            {empty_line_html}
                            <div style="font-size: 14px; color: #c8c8c8;">{cleaned_vehicle}</div>
                        </td>
                    </tr>
                </table>
            </div>
            """
            
            self.kill_detected.emit(readout, destroyer)
            logging.info(f"Vehicle destruction displayed: {vehicle_name} {destruction_type.lower()} by {destroyer}")
            
    def handle_actual_vehicle_kill(self, event: dict) -> None:
        """Handle actual kills from vehicle destruction with occupants"""
        victim = event.get('victim', '').strip()
        attacker = event.get('attacker', '').strip()
        vehicle_name = event.get('vehicle_name', '')
        timestamp = event.get('timestamp', '')
        victim_id = event.get('victim_id', '0')
        attacker_id = event.get('attacker_id', '0')
        weapon = event.get('weapon', 'Unknown')
        zone = event.get('zone', 'Unknown')

        if KillParser.is_npc(attacker):
            logging.info(f"NPC vehicle kill detected (attacker: {attacker}). Not showing.")
            return
        
        cleaned_vehicle = re.sub(r'_\d+$', '', vehicle_name)
        cleaned_vehicle = cleaned_vehicle.replace('_', ' ')
        
        if attacker.lower() == self.registered_user.strip().lower():
            try:
                synthetic_log_line = (
                    f"<{timestamp}> [Notice] <Actor Death> CActor::Kill: '{victim}' "
                    f"[{victim_id}] in zone '{zone}' "
                    f"killed by '{attacker}' [{attacker_id}] using '{weapon}' [0] "
                    f"with damage type 'vehicledestruction' "
                    f"from direction x: 0.0, y: 0.0, z: 0.0 [0]"
                )
                
                fake_data = {
                    'victim': victim,
                    'attacker': attacker,
                    'weapon': weapon,
                    'damage_type': 'vehicledestruction',
                    'zone': zone,
                    'killer_ship': cleaned_vehicle
                }
                
                captured_game_mode = self.last_game_mode if self.last_game_mode and self.last_game_mode != "Unknown" else "Unknown"
                readout, payload = format_registered_kill(
                    synthetic_log_line, fake_data, self.registered_user, timestamp, captured_game_mode, success=True
                )
                self.kill_detected.emit(readout, attacker)
                self.payload_ready.emit(payload, timestamp, attacker, readout)
                logging.info(f"Processed correlated vehicle kill: {victim} killed by {attacker} in {cleaned_vehicle}")
            except Exception as e:
                logging.error(f"Error processing correlated kill: {e}")
                
        elif victim.lower() == self.registered_user.strip().lower():
            try:
                from Death_kill import format_death_kill
                
                synthetic_log_line = (
                    f"<{timestamp}> [Notice] <Actor Death> CActor::Kill: '{victim}' "
                    f"[{victim_id}] in zone '{zone}' "
                    f"killed by '{attacker}' [{attacker_id}] using '{weapon}' [0] "
                    f"with damage type 'vehicledestruction' "
                    f"from direction x: 0.0, y: 0.0, z: 0.0 [0]"
                )
                
                fake_data = {
                    'victim': victim,
                    'attacker': attacker,
                    'weapon': weapon,
                    'damage_type': 'vehicledestruction',
                    'zone': zone
                }
                
                captured_game_mode = self.last_game_mode if self.last_game_mode and self.last_game_mode != "Unknown" else "Unknown"
                readout = format_death_kill(synthetic_log_line, fake_data, self.registered_user, timestamp, captured_game_mode)
                self.death_detected.emit(readout, victim)
                
                death_payload = {
                    'log_line': synthetic_log_line,
                    'game_mode': captured_game_mode,
                    'victim_name': victim,
                    'attacker_name': attacker,
                    'weapon': weapon,
                    'damage_type': 'vehicledestruction',
                    'location': event.get('zone', 'Unknown'),
                    'timestamp': timestamp,
                    'event_type': 'death'
                }
                self.death_payload_ready.emit(death_payload, timestamp, attacker, readout)
                logging.info(f"Processed correlated vehicle death: {victim} killed by {attacker} in {cleaned_vehicle}")
            except Exception as e:
                logging.error(f"Error processing correlated death: {e}")

    def handle_ejection_event(self, event: dict) -> None:
        """Handle ejection events from vehicles"""
        pilot = event.get('pilot', '').strip()
        vehicle_name = event.get('vehicle_name', '')
        timestamp = event.get('timestamp', '')
        
        if KillParser.is_npc(pilot):
            logging.info(f"NPC ejection detected (pilot: {pilot}). Not showing.")
            return
        
        if self.gui_parent and not getattr(self.gui_parent, 'show_pilot_ejected', True):
            logging.debug(f"Pilot ejection event hidden by user preference: {pilot}")
            return
        
        cleaned_vehicle = re.sub(r'_\d+$', '', vehicle_name)
        cleaned_vehicle = re.sub(r'\s+\d+$', '', cleaned_vehicle)
        cleaned_vehicle = cleaned_vehicle.replace('_', ' ')
        
        if pilot.lower() != self.registered_user.strip().lower():
            readout = f"""
            <div class="newEntry">
                <table class="event-table" style="background: linear-gradient(135deg, #1a1a2e, #16213e); color: #e0e0e0; border-radius: 10px; margin-bottom: 15px; width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 12px 15px; text-align: left; border-bottom: 1px solid #333333;">
                            <div style="font-size: 18px; font-weight: bold; color: #00d9ff; margin-bottom: 5px;">{t("PILOT EJECTED")}</div>
                            <div style="font-size: 14px; color: #ffcc00; margin-bottom: 3px;">{pilot} {t("ejected from their ship")}</div>
                            <div style="font-size: 14px; color: #c8c8c8;">{cleaned_vehicle}</div>
                        </td>
                    </tr>
                </table>
            </div>
            """
            
            self.kill_detected.emit(readout, pilot)
            logging.info(f"Enemy ejection displayed: {pilot} ejected from {vehicle_name}")
        else:
            logging.info(f"Registered user ejection ignored: {pilot} ejected from {vehicle_name}")

    def handle_seat_exit_event(self, event: dict) -> None:
        """Handle pilot leaving seat events (after ship disabled)"""
        pilot = event.get('pilot', '').strip()
        vehicle_name = event.get('vehicle_name', '')
        timestamp = event.get('timestamp', '')
        
        if KillParser.is_npc(pilot):
            logging.info(f"NPC seat exit detected (pilot: {pilot}). Not showing.")
            return
        
        if self.gui_parent and not getattr(self.gui_parent, 'show_pilot_abandoned', True):
            logging.debug(f"Pilot abandoned ship event hidden by user preference: {pilot}")
            return
        
        if pilot.lower() != self.registered_user.strip().lower():
            readout = f"""
            <div class="newEntry">
                <table class="event-table" style="background: linear-gradient(135deg, #1a1a2e, #16213e); color: #e0e0e0; border-radius: 10px; margin-bottom: 15px; width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 12px 15px; text-align: left; border-bottom: 1px solid #333333;">
                            <div style="font-size: 18px; font-weight: bold; color: #ff6b6b; margin-bottom: 5px;">{t("PILOT ABANDONED SHIP")}</div>
                            <div style="font-size: 14px; color: #ffcc00; margin-bottom: 3px;">{pilot} {t("left their disabled ship")}</div>
                            <div style="font-size: 14px; color: #c8c8c8;">{vehicle_name}</div>
                        </td>
                    </tr>
                </table>
            </div>
            """
            
            self.kill_detected.emit(readout, pilot)
            logging.info(f"Pilot seat exit displayed: {pilot} left {vehicle_name}")
        else:
            logging.info(f"Registered user seat exit ignored: {pilot} left {vehicle_name}")

    def handle_kill_event(self, line: str, match_obj: re.Match) -> None:
        data = match_obj.groupdict()
        timestamp_iso = data.get('timestamp')
        try:
            dt = datetime.fromisoformat(timestamp_iso.replace('Z', '+00:00'))
            full_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
            display_timestamp = dt.strftime('%Y-%m-%d')
        except ValueError:
            full_timestamp = timestamp_iso
            display_timestamp = timestamp_iso

        victim = data.get('victim', '').strip()
        attacker = data.get('attacker', '').strip()

        if data.get("damage_type", "").lower() == "vehicledestruction":
            logging.debug(f"Skipping vehicledestruction event - will be handled by vehicle correlator: {victim} killed by {attacker}")
            return

        if KillParser.is_npc(victim):
            logging.info(f"NPC kill detected (victim: {victim}). Not processing.")
            return
            
        if "subside" in victim.lower() or "subside" in attacker.lower():
            return
        if not self.registered_user:
            return
        if (attacker.lower() == self.registered_user.strip().lower() and
            victim.lower() == self.registered_user.strip().lower()):
            try:
                from Death_kill import format_death_kill
                captured_game_mode = self.last_game_mode if self.last_game_mode and self.last_game_mode != "Unknown" else "Unknown"
                readout = format_death_kill(line, data, self.registered_user, display_timestamp, captured_game_mode)
                self.death_detected.emit(readout, victim)
            except Exception as e:
                logging.error(f"Error formatting suicide event: {e}")
            return

        captured_game_mode = self.last_game_mode if self.last_game_mode and self.last_game_mode != "Unknown" else "Unknown"
        data["killer_ship"] = "Player destruction"

        if attacker.lower() == self.registered_user.strip().lower():
            try:
                readout, payload = format_registered_kill(
                    line, data, self.registered_user, full_timestamp, captured_game_mode, success=True
                )
                self.kill_detected.emit(readout, attacker)
                self.payload_ready.emit(payload, full_timestamp, attacker, readout)
            except Exception as e:
                logging.error(f"Error formatting registered kill: {e}")
        elif victim.lower() == self.registered_user.strip().lower():
            try:
                from Death_kill import format_death_kill
                readout = format_death_kill(line, data, self.registered_user, full_timestamp, captured_game_mode)
                self.death_detected.emit(readout, victim)

                death_payload = {
                    'log_line': line.strip(),
                    'game_mode': captured_game_mode,
                    'victim_name': victim,
                    'attacker_name': attacker,
                    'weapon': data.get('weapon', 'Unknown'),
                    'damage_type': data.get('damage_type', 'Unknown'),
                    'location': data.get('zone', 'Unknown'),
                    'timestamp': full_timestamp,
                    'event_type': 'death'
                }
                self.death_payload_ready.emit(death_payload, full_timestamp, attacker, readout)
            except Exception as e:
                logging.error(f"Error formatting or sending death payload: {e}")
        else:
            logging.info("Ignoring kill event: registered user is neither attacker nor victim.")

    def stop(self) -> None:
        logging.info("Stopping TailThread.")
        self._stop_event = True
        if self.vehicle_correlator:
            self.vehicle_correlator.stop_cleanup_thread(wait=True)
        self.clear_config_killer_ship()

class RescanThread(QThread):
    rescanFinished = pyqtSignal(list)

    def __init__(self, file_path: str, registered_user: str, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.file_path = file_path
        self._stop_event = False
        self.found_kills: List[dict] = []
        self.registered_user = registered_user.lower() if registered_user else ""

    def run(self) -> None:
        current_game_mode = "Unknown"
        current_ship = ""
        jump_drive_pattern = re.compile(r'\(adam:\s+(?P<ship>(?:[A-Za-z0-9_]+?)(?=_\d+\s+in zone)|[A-Za-z0-9_]+)\s+in zone')
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    if self._stop_event:
                        break
                    stripped = line.strip()
                    if "Loading GameModeRecord=" in stripped:
                        gm_match = GAME_MODE_PATTERN.search(stripped)
                        if gm_match:
                            data = gm_match.groupdict()
                            raw = data.get('game_mode')
                            mapped = GAME_MODE_MAPPING.get(raw, "Unknown")
                            current_game_mode = mapped
                    j_match = jump_drive_pattern.search(stripped)
                    if j_match:
                        raw_ship = j_match.group('ship')

                        raw_ship = re.sub(r'_\d+$', '', raw_ship)
                        current_ship = raw_ship.replace('_', ' ')
                        current_ship = re.sub(r'\s+\d+$', '', current_ship)
                    if "CActor::Kill:" in stripped:
                        kill_match = KILL_LOG_PATTERN.search(stripped)
                        if kill_match:
                            data = kill_match.groupdict()
                            attacker = data.get('attacker', '').lower().strip()
                            victim = data.get('victim', '').lower().strip()

                            if KillParser.is_npc(victim):
                                logging.info(f"NPC kill detected during rescan (victim: {victim}). Skipping.")
                                continue
                            
                            if victim == self.registered_user:
                                logging.info(f"Skipping kill where registered user '{victim}' is the victim. Attacker: {attacker}")
                                continue
                                
                            if attacker == self.registered_user:
                                timestamp_iso = data.get('timestamp')
                                try:
                                    timestamp = datetime.fromisoformat(timestamp_iso.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
                                except ValueError:
                                    timestamp = timestamp_iso
                                local_key = f"{timestamp}::{victim}::{current_game_mode}"
                                payload = {'log_line': stripped, 'game_mode': current_game_mode}
                                if data.get("damage_type", "").lower() == "vehicledestruction":
                                    if current_ship:
                                        cleaned_ship = re.sub(r'_\d+$', '', current_ship)
                                        cleaned_ship = cleaned_ship.replace('_', ' ')
                                        cleaned_ship = re.sub(r'\s+\d+$', '', cleaned_ship)
                                        payload["killer_ship"] = cleaned_ship
                                    else:
                                        payload["killer_ship"] = "Unknown Ship"
                                else:
                                    payload["killer_ship"] = "Player destruction"
                                self.found_kills.append({
                                    "local_key": local_key,
                                    "payload": payload,
                                    "timestamp": timestamp
                                })
                    QThread.yieldCurrentThread()
        except Exception as e:
            logging.error(f"Error in RescanThread: {e}")
        self.rescanFinished.emit(self.found_kills)

    def stop(self) -> None:
        self._stop_event = True

class ApiSenderThread(QThread):
    apiResponse = pyqtSignal(str, object)

    def __init__(self, api_endpoint: str, headers: Dict[str, str], payload: dict, local_key: str, verify_ssl: bool = True, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.api_endpoint = api_endpoint
        self.headers = headers
        self.payload = payload
        self.local_key = local_key
        self.verify_ssl = verify_ssl
        self.retry_count = 0
        self.max_retries = 5
        self.backoff = 1

    def run(self) -> None:
        while self.retry_count < self.max_retries:
            try:
                if not self.verify_ssl:
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                resp = requests.post(self.api_endpoint, headers=self.headers, json=self.payload, timeout=10, verify=self.verify_ssl)
                if resp.status_code == 201:
                    data_resp = resp.json()
                    if isinstance(data_resp, dict):
                        server_msg = data_resp.get("message", "")
                        if "duplicate" in server_msg.lower():
                            self.apiResponse.emit("Duplicate kill. Not logged (server).", data_resp)
                        else:
                            self.apiResponse.emit("Kill logged successfully.", data_resp)
                    else:
                        self.apiResponse.emit("Kill logged successfully.", data_resp)
                    return
                elif resp.status_code == 200:
                    data_resp = resp.json()
                    if isinstance(data_resp, dict):
                        if data_resp.get("message") == "NPC not logged":
                            self.apiResponse.emit("NPC kill not logged.", data_resp)
                        else:
                            self.apiResponse.emit("Kill logged successfully.", data_resp)
                    else:
                        self.apiResponse.emit("Kill logged successfully.", data_resp)
                    return
                elif 400 <= resp.status_code < 500:
                    error_text = f"Failed to log kill: {resp.status_code} - {resp.text}"
                    self.apiResponse.emit(error_text, {})
                    return
                else:
                    raise requests.exceptions.HTTPError(f"Server error: {resp.status_code}")
            except requests.exceptions.RequestException as e:
                self.retry_count += 1
                error_text = f"API request failed (Attempt {self.retry_count}/{self.max_retries}): {e}"
                self.apiResponse.emit(error_text, {})
                if self.retry_count >= self.max_retries:
                    break
                time.sleep(self.backoff)
                self.backoff *= 2
        
        self.apiResponse.emit("API request failed after maximum retries.", {})