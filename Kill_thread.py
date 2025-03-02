# Kill_thread.py

import os
import re
import json
import base64
import requests
import logging
import time
from datetime import datetime
from urllib.parse import quote
from typing import Optional, Dict, Any, List
from PyQt5.QtCore import pyqtSignal, QThread, QDir, QTimer
from bs4 import BeautifulSoup

from kill_parser import GAME_MODE_MAPPING, GAME_MODE_PATTERN, KILL_LOG_PATTERN, CHROME_USER_AGENT

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": CHROME_USER_AGENT})

def trim_suffix(name: Optional[str]) -> str:
    if not name:
        return "Unknown"
    return re.sub(r'_\d+$', '', name)

def fetch_player_details(playername: str) -> Dict[str, str]:
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
        logging.error(f"Error fetching image data for {victim_name}: {e}")
    return default_image_url

class TailThread(QThread):
    kill_detected = pyqtSignal(str, str)
    death_detected = pyqtSignal(str, str)
    player_registered = pyqtSignal(str)
    game_mode_changed = pyqtSignal(str)
    payload_ready = pyqtSignal(dict, str, str, str)

    def __init__(self, file_path: str, callback) -> None:
        super().__init__()
        self.file_path = file_path
        self._stop_event = False
        self.player_mapping: Dict[str, str] = {}
        self.last_game_mode: str = "Unknown"
        self.registered_user: Optional[str] = None
        self.has_registered = False

    def is_file_same(self, file) -> bool:
        try:
            current_stat = os.stat(self.file_path)
            file_stat = os.fstat(file.fileno())
            return (current_stat.st_dev == file_stat.st_dev and
                    current_stat.st_ino == file_stat.st_ino)
        except Exception as e:
            logging.error(f"Error checking if file is same: {e}")
            return False

    def run(self) -> None:
        logging.info("TailThread started.")
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
                    self.process_line(line.strip())
        except Exception as e:
            logging.error(f"Error in TailThread: {e}")
        logging.info("TailThread terminated.")

    def process_existing_player_registrations(self, f) -> None:
        logging.info("Processing existing entries for legacy login responses and game modes...")
        for line in f:
            stripped_line = line.strip()
            legacy_login_match = re.search(
                r"<(?P<timestamp>[^>]+)> \[Notice\] <Legacy login response> \[CIG-net\] User Login Success - Handle\[(?P<handle>[^\]]+)\]",
                stripped_line
            )
            if legacy_login_match and not self.has_registered:
                handle = legacy_login_match.group('handle').strip()
                self.registered_user = handle
                self.has_registered = True
            gm_match = GAME_MODE_PATTERN.search(stripped_line)
            if gm_match:
                data = gm_match.groupdict()
                raw = data.get('game_mode')
                mapped = GAME_MODE_MAPPING.get(raw)
                if mapped and mapped != self.last_game_mode:
                    self.last_game_mode = mapped
                    self.game_mode_changed.emit(f"Monitoring game mode: {mapped}")
                elif not mapped:
                    logging.warning(f"Unknown game mode '{raw}'")

    def process_line(self, line: str) -> None:
        # Check for legacy login response and register the user if needed.
        legacy_login_match = re.search(
            r"<(?P<timestamp>[^>]+)> \[Notice\] <Legacy login response> \[CIG-net\] User Login Success - Handle\[(?P<handle>[^\]]+)\]",
            line
        )
        if legacy_login_match and not self.has_registered:
            handle = legacy_login_match.group('handle').strip()
            self.registered_user = handle
            self.has_registered = True
            return

        # Check for game mode update.
        gm_match = GAME_MODE_PATTERN.search(line)
        if gm_match:
            data = gm_match.groupdict()
            gm_raw = data.get('game_mode')
            self.raw_game_mode = gm_raw
            mapped = GAME_MODE_MAPPING.get(gm_raw, gm_raw)
            if mapped and mapped != self.last_game_mode:
                self.last_game_mode = mapped
                self.game_mode_changed.emit(f"Monitoring game mode: {mapped}")
            elif not mapped:
                logging.warning(f"Unknown game mode '{gm_raw}' encountered.")
            return

        # Process a kill event.
        kill_match = KILL_LOG_PATTERN.search(line)
        if kill_match:
            data = kill_match.groupdict()
            timestamp_iso = data.get('timestamp')
            try:
                timestamp = datetime.fromisoformat(timestamp_iso.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                timestamp = timestamp_iso

            victim = data.get('victim', '').strip()
            attacker = data.get('attacker', '').strip()
            if self.registered_user is None:
                return

            # Capture the current game mode at the time of the kill event.
            captured_game_mode = self.last_game_mode if self.last_game_mode and self.last_game_mode != "Unknown" else "Unknown"
            logging.info(f"Captured game mode for kill event: {captured_game_mode}")

            registered = self.registered_user.strip().lower()
            if attacker.lower() == registered:
                try:
                    from Registered_kill import format_registered_kill
                    readout, payload = format_registered_kill(line, data, self.registered_user, timestamp, captured_game_mode)
                    self.kill_detected.emit(readout, attacker)
                    logging.info(f"Payload to be sent: {payload}")
                    self.payload_ready.emit(payload, timestamp, attacker, readout)
                except Exception as e:
                    logging.error(f"Error formatting registered kill: {e}")
            elif victim.lower() == registered:
                try:
                    from Death_kill import format_death_kill
                    readout = format_death_kill(line, data, self.registered_user, timestamp, captured_game_mode)
                    self.death_detected.emit(readout, victim)
                except Exception as e:
                    logging.error(f"Error formatting death kill: {e}")
            else:
                logging.info("Ignoring kill event: registered user is neither attacker nor victim.")
            return
        
    def stop(self) -> None:
        logging.info("Stopping TailThread.")
        self._stop_event = True

    def current_time(self) -> str:
        return time.strftime('%Y-%m-%dT%H:%M:%S')

class RescanThread(QThread):
    rescanFinished = pyqtSignal(list)

    def __init__(self, file_path: str, registered_user: str, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.file_path = file_path
        self._stop_event = False
        self.found_kills: List[dict] = []
        self.registered_user = registered_user.lower() if registered_user else ""

    def run(self) -> None:
        logging.info("RescanThread started. Reading entire log from the beginning.")
        current_game_mode = "Unknown"

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if self._stop_event:
                        break

                    stripped = line.strip()
                    gm_match = GAME_MODE_PATTERN.search(stripped)
                    if gm_match:
                        data = gm_match.groupdict()
                        raw = data.get('game_mode')
                        mapped = GAME_MODE_MAPPING.get(raw, "Unknown")
                        current_game_mode = mapped

                    kill_match = KILL_LOG_PATTERN.search(stripped)
                    if kill_match:
                        data = kill_match.groupdict()
                        attacker = data.get('attacker', '').lower().strip()
                        victim   = data.get('victim', '').lower().strip()

                        if attacker == self.registered_user:
                            timestamp_iso = data.get('timestamp')
                            try:
                                timestamp = (datetime
                                             .fromisoformat(timestamp_iso.replace('Z', '+00:00'))
                                             .strftime('%Y-%m-%d %H:%M:%S'))
                            except ValueError:
                                timestamp = timestamp_iso

                            local_key = f"{timestamp}::{victim}::{current_game_mode}"
                            payload = {
                                'log_line': stripped,
                                'game_mode': current_game_mode
                            }

                            self.found_kills.append({
                                "local_key": local_key,
                                "payload": payload,
                                "timestamp": timestamp
                            })

                    QThread.yieldCurrentThread()
        except Exception as e:
            logging.error(f"Error in RescanThread: {e}")
        logging.info("RescanThread finished reading the log.")
        self.rescanFinished.emit(self.found_kills)

    def stop(self) -> None:
        self._stop_event = True

class ApiSenderThread(QThread):
    apiResponse = pyqtSignal(str)

    def __init__(self, api_endpoint: str, headers: Dict[str, str], payload: dict, local_key: str, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.api_endpoint = api_endpoint
        self.headers = headers
        self.payload = payload
        self.local_key = local_key
        self.retry_count = 0
        self.max_retries = 5
        self.backoff = 1

    def run(self) -> None:
        while self.retry_count < self.max_retries:
            try:
                resp = requests.post(self.api_endpoint, headers=self.headers, json=self.payload, timeout=10)
                if resp.status_code == 201:
                    data_resp = resp.json()
                    server_msg = data_resp.get("message", "")
                    if "duplicate" in server_msg.lower():
                        self.apiResponse.emit("Duplicate kill. Not logged (server).")
                    else:
                        self.apiResponse.emit(f"Accepted kill: {server_msg}")
                    return
                elif resp.status_code == 200:
                    data_resp = resp.json()
                    if data_resp.get("message") == "NPC not logged":
                        self.apiResponse.emit("NPC kill not logged.")
                    return
                elif 400 <= resp.status_code < 500:
                    error_text = f"Failed to log kill: {resp.status_code} - {resp.text}"
                    self.apiResponse.emit(error_text)
                    return
                else:
                    raise requests.exceptions.HTTPError(f"Server error: {resp.status_code}")
            except requests.exceptions.RequestException as e:
                self.retry_count += 1
                error_text = f"API request failed (Attempt {self.retry_count}/{self.max_retries}): {e}"
                self.apiResponse.emit(error_text)
                time.sleep(self.backoff)
                self.backoff *= 2
        self.apiResponse.emit("API request failed after maximum retries.")
