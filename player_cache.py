# player_cache.py

import time
import logging
from typing import Dict, Any, Optional, Tuple
from threading import Lock


class PlayerCache:
    """Thread-safe cache for player details and images"""
    
    def __init__(self, max_age_seconds: int = 3600):
        self.max_age = max_age_seconds
        self._details_cache: Dict[str, Tuple[Dict[str, str], float]] = {}
        self._image_cache: Dict[str, Tuple[str, float]] = {}
        self._lock = Lock()
        self.logger = logging.getLogger(__name__)
    
    def get_player_details(self, player_name: str) -> Optional[Dict[str, str]]:
        """Get cached player details if available and not expired"""
        with self._lock:
            if player_name in self._details_cache:
                details, timestamp = self._details_cache[player_name]
                if time.time() - timestamp < self.max_age:
                    self.logger.debug(f"Cache hit for player details: {player_name}")
                    return details
                else:
                    del self._details_cache[player_name]
            return None
    
    def cache_player_details(self, player_name: str, details: Dict[str, str]) -> None:
        """Cache player details with timestamp"""
        with self._lock:
            self._details_cache[player_name] = (details, time.time())
            self.logger.debug(f"Cached player details: {player_name}")
    
    def get_player_image(self, player_name: str) -> Optional[str]:
        """Get cached player image if available and not expired"""
        with self._lock:
            if player_name in self._image_cache:
                image_data, timestamp = self._image_cache[player_name]
                if time.time() - timestamp < self.max_age:
                    self.logger.debug(f"Cache hit for player image: {player_name}")
                    return image_data
                else:
                    del self._image_cache[player_name]
            return None
    
    def cache_player_image(self, player_name: str, image_data: str) -> None:
        """Cache player image with timestamp"""
        with self._lock:
            self._image_cache[player_name] = (image_data, time.time())
            self.logger.debug(f"Cached player image: {player_name}")
    
    def clear_expired_entries(self) -> None:
        """Remove all expired cache entries"""
        current_time = time.time()
        with self._lock:
            expired_details = [
                player for player, (_, timestamp) in self._details_cache.items()
                if current_time - timestamp >= self.max_age
            ]
            for player in expired_details:
                del self._details_cache[player]
            
            expired_images = [
                player for player, (_, timestamp) in self._image_cache.items()
                if current_time - timestamp >= self.max_age
            ]
            for player in expired_images:
                del self._image_cache[player]
            
            if expired_details or expired_images:
                self.logger.info(f"Cleared {len(expired_details)} expired details and {len(expired_images)} expired images")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        with self._lock:
            return {
                'details_entries': len(self._details_cache),
                'image_entries': len(self._image_cache)
            }
    
    def clear_all(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._details_cache.clear()
            self._image_cache.clear()
            self.logger.info("Cleared all cache entries")


_player_cache = PlayerCache()


def get_player_cache() -> PlayerCache:
    """Get the global player cache instance"""
    return _player_cache