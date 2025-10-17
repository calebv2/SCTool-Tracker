# kill_event_formatter.py

import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from urllib.parse import quote

from fetch import fetch_player_details, fetch_victim_image_base64
from kill_parser import KillParser
from language_manager import t
from html_templates import RegisteredKillTemplate, DeathEventTemplate
from player_cache import get_player_cache


class KillEventFormatter(ABC):
    """Base class for formatting kill/death events"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @staticmethod
    def validate_input_data(data: Dict[str, Any], required_fields: list) -> None:
        """Validate that required fields are present in input data"""
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
    
    @staticmethod
    def safe_get_player_details(player_name: str) -> Dict[str, str]:
        """Safely fetch player details with caching and error handling"""
        cache = get_player_cache()
        
        cached_details = cache.get_player_details(player_name)
        if cached_details is not None:
            return cached_details
        
        try:
            details = fetch_player_details(player_name)
            cache.cache_player_details(player_name, details)
            return details
        except Exception as e:
            logging.error(f"Failed to fetch player details for {player_name}: {e}")
            error_details = {'org_name': t('Error'), 'org_tag': t('Error')}
            cache.cache_player_details(player_name, error_details)
            return error_details
    
    @staticmethod
    def safe_get_player_image(player_name: str) -> str:
        """Safely fetch player image with caching and error handling"""
        cache = get_player_cache()
        cached_image = cache.get_player_image(player_name)
        if cached_image is not None:
            return cached_image
        
        try:
            image_data = fetch_victim_image_base64(player_name)
            cache.cache_player_image(player_name, image_data)
            return image_data
        except Exception as e:
            logging.error(f"Failed to fetch player image for {player_name}: {e}")
            default_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
            cache.cache_player_image(player_name, default_image)
            return default_image
    
    @staticmethod
    def create_player_profile_url(player_name: str) -> str:
        """Create RSI profile URL for a player"""
        return f"https://robertsspaceindustries.com/citizens/{quote(player_name)}"
    
    @staticmethod
    def create_player_link(player_name: str, color: str = "#f04747") -> str:
        """Create HTML link for player profile"""
        profile_url = KillEventFormatter.create_player_profile_url(player_name)
        return f'<a href="{profile_url}" style="color:{color}; text-decoration:none;">{player_name}</a>'
    
    @staticmethod
    def format_timestamp(timestamp: str) -> str:
        """Format timestamp for display"""
        return timestamp.split(" ")[0] if " " in timestamp else timestamp
    
    @staticmethod
    def format_game_mode(game_mode: Optional[str]) -> str:
        """Format game mode with fallback"""
        return game_mode if game_mode else t('Unknown')
    
    @abstractmethod
    def format_event(self, log_line: str, data: dict, **kwargs) -> Any:
        """Abstract method for formatting events"""
        pass


class RegisteredKillFormatter(KillEventFormatter):
    """Formatter for registered kill events"""
    
    @staticmethod
    def process_killer_ship(killer_ship: str) -> str:
        """Process and clean killer ship name"""
        if not killer_ship:
            return ""

        killer_ship = re.sub(r'_\d+$', '', killer_ship)
        killer_ship = killer_ship.replace("_", " ")
        killer_ship = re.sub(r'\s+\d+$', '', killer_ship)
        
        if killer_ship.lower() == t("no ship").lower():
            killer_ship = ""
        
        return killer_ship
    
    @staticmethod
    def determine_engagement_and_method(damage_type: str, killer_ship: str, formatted_weapon: str, is_in_ship: bool = False) -> Tuple[str, str]:
        """
        Determine engagement description and method
        
        Args:
            damage_type: Type of damage (e.g., 'vehicledestruction', 'Bullet')
            killer_ship: Name of the ship (if any)
            formatted_weapon: Formatted weapon name
            is_in_ship: Whether the player was in a ship at the time of the kill
            
        Returns:
            Tuple of (engagement description, method)
            
        Logic:
            - Vehicle destruction = A ship/vehicle was destroyed (damage_type == "vehicledestruction")
            - Player destruction = A player entity died (any other damage type)
            - Engagement shows ship name if player was in a ship during the kill
        """
        if damage_type.lower() == "vehicledestruction":
            if killer_ship.lower() not in [t("vehicle destruction").lower(), t("player destruction").lower(), ""]:
                engagement = f"{killer_ship} {t('using')} {formatted_weapon}"
            else:
                engagement = formatted_weapon
            method = t("Vehicle destruction")
        else:
            if is_in_ship and killer_ship and killer_ship.lower() not in [t("vehicle destruction").lower(), t("player destruction").lower(), t("no ship").lower(), ""]:
                engagement = f"{killer_ship} {t('using')} {formatted_weapon}"
            else:
                engagement = formatted_weapon
            method = t("Player destruction")
        
        return engagement, method
    
    def format_event(
        self, 
        log_line: str, 
        data: dict, 
        registered_user: str,
        full_timestamp: str,
        last_game_mode: str,
        success: bool = True,
        is_in_ship: bool = False
    ) -> Tuple[str, Dict[str, Any]]:
        """Format registered kill event"""
        try:
            self.validate_input_data(data, ['victim', 'zone', 'damage_type', 'weapon'])

            victim = data.get('victim', 'Unknown')
            zone = data.get('zone', 'Unknown')
            damage_type = data.get('damage_type', 'Unknown')
            weapon = data.get('weapon', 'Unknown')
            raw_killer_ship = data.get('killer_ship', t("Player destruction"))
            killer_ship = self.process_killer_ship(raw_killer_ship)
            formatted_zone = KillParser.format_zone(zone)
            formatted_weapon = KillParser.format_weapon(weapon)
            engagement, method = self.determine_engagement_and_method(
                damage_type, killer_ship, formatted_weapon, is_in_ship
            )

            details = self.safe_get_player_details(victim)
            victim_image_data_uri = self.safe_get_player_image(victim)
            victim_link = self.create_player_link(victim)
            display_timestamp = self.format_timestamp(full_timestamp)
            game_mode = self.format_game_mode(last_game_mode)
            
            template_data = {
                'victim': victim,
                'display_timestamp': display_timestamp,
                'game_mode': game_mode,
                'registered_user': registered_user,
                'engagement': engagement,
                'method': method,
                'victim_link': victim_link,
                'formatted_zone': formatted_zone,
                'details': details,
                'victim_image_data_uri': victim_image_data_uri
            }
            
            readout = RegisteredKillTemplate.render(template_data)
            
            payload_ship = killer_ship if killer_ship.lower() not in [
                t("vehicle destruction").lower(), t("player destruction").lower()
            ] else ""
            
            payload = {
                'log_line': log_line.strip(),
                'game_mode': game_mode,
                'killer_ship': payload_ship,
                'method': method
            }
            
            return readout, payload
            
        except Exception as e:
            self.logger.error(f"Error formatting registered kill: {e}")
            raise


class DeathEventFormatter(KillEventFormatter):
    """Formatter for death events"""
    
    def format_event(
        self,
        log_line: str,
        data: dict,
        registered_user: str,
        timestamp: str,
        last_game_mode: str
    ) -> str:
        """Format death event"""
        try:
            self.validate_input_data(data, ['attacker', 'zone', 'weapon'])

            attacker = data.get('attacker', 'Unknown')
            zone = data.get('zone', 'Unknown')
            weapon = data.get('weapon', 'Unknown')

            formatted_zone = KillParser.format_zone(zone)
            formatted_weapon = KillParser.format_weapon(weapon)

            details = self.safe_get_player_details(attacker)
            attacker_image_data_uri = self.safe_get_player_image(attacker)
            attacker_link = self.create_player_link(attacker)
            
            game_mode = self.format_game_mode(last_game_mode)
            
            template_data = {
                'game_mode': game_mode,
                'timestamp': timestamp,
                'attacker': attacker,
                'attacker_link': attacker_link,
                'details': details,
                'formatted_zone': formatted_zone,
                'formatted_weapon': formatted_weapon,
                'attacker_image_data_uri': attacker_image_data_uri
            }

            return DeathEventTemplate.render(template_data)
            
        except Exception as e:
            self.logger.error(f"Error formatting death event: {e}")
            raise