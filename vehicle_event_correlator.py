# vehicle_event_correlator.py

import re
import time
import logging
from typing import Dict, List, Optional, Tuple, NamedTuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading

from kill_parser import KillParser

@dataclass
class VehicleDestroyEvent:
    """Represents a vehicle destruction event"""
    timestamp: str
    vehicle_id: str
    vehicle_name: str
    zone: str
    position: Tuple[float, float, float]
    destroyer_id: str
    destroyer_name: str
    destroy_level: int
    damage_cause: str
    log_time: float

@dataclass
class ActorDeathEvent:
    """Represents an actor death event"""
    timestamp: str
    victim: str
    victim_id: str
    attacker: str
    attacker_id: str
    weapon: str
    damage_type: str
    zone: str
    log_time: float

class VehicleEventCorrelator:
    """
    Correlates vehicle destruction events with actor death events
    to properly identify victims of vehicle kills
    """
    
    def __init__(self, correlation_timeout: float = 0.0, event_callback=None):
        self.correlation_timeout = correlation_timeout
        self.disabled_timeout = 0.0
        self.destroyed_timeout = 1.0
        self.pending_vehicle_events: List[VehicleDestroyEvent] = []
        self._pending_lock = threading.Lock()
        self._cleanup_interval = 0.1
        self._cleanup_thread: Optional[threading.Thread] = None
        self._cleanup_stop = threading.Event()
        self.event_callback = event_callback
        self.logger = logging.getLogger(__name__)
        self.npc_patterns = ["pu_", "npc", "ai", "enemy", "criminal", "soldier", "engineer",
                            "gunner", "sniper", "shipjacker"]
        
        self.vehicle_destroy_pattern = re.compile(
            r'<(?P<timestamp>[^>]+)> \[Notice\] <Vehicle Destruction> '
            r'CVehicle::OnAdvanceDestroyLevel: Vehicle \'(?P<vehicle_name>[^\']+)\' '
            r'\[(?P<vehicle_id>\d+)\] in zone \'(?P<zone>[^\']+)\' '
            r'\[pos x: (?P<x>-?[\d.]+), y: (?P<y>-?[\d.]+), z: (?P<z>-?[\d.]+) '
            r'vel x: [^]]+\] driven by \'(?P<driver>[^\']*)\' \[(?P<driver_id>\d*)\] '
            r'advanced from destroy level (?P<from_level>\d+) to (?P<to_level>\d+) '
            r'caused by \'(?P<destroyer>[^\']+)\' \[(?P<destroyer_id>\d+)\] with \'(?P<damage_cause>[^\']+)\''
        )
        
        self.actor_death_pattern = re.compile(
            r"<(?P<timestamp>[^>]+)> \[Notice\] <Actor Death> CActor::Kill: '(?P<victim>[^']+)' "
            r"\[(?P<victim_geid>\d+)\] in zone '(?P<zone>[^']+)' "
            r"killed by '(?P<attacker>[^']+)' \[(?P<attacker_geid>\d+)\] using '(?P<weapon>[^']+)' \[.*\] "
            r"with damage type '(?P<damage_type>\w+)' "
            r"from direction x: (?P<x>-?[\d.]+), y: (?P<y>-?[\d.]+), z: (?P<z>-?[\d.]+) \[.*?\]"
        )

    def process_log_line(self, line: str) -> Tuple[Optional[Dict], List[Dict]]:
        """        
        Vehicle Destruction Level Understanding:
        - 0→1 (Soft Death): Ship disabled not flyable.
        - 1→2 (Hard Death): Ship completely destroyed.
        
        IMPORTANT: Only generates kills when actual HUMAN PLAYERS die in vehicles.
        Vehicle entity deaths (like ARGO_ATLS_6282649965732) are filtered out.
        """
        current_time = time.time()
        correlated_events = []
        
        vehicle_match = self.vehicle_destroy_pattern.search(line)
        if vehicle_match:
            vehicle_event = self._parse_vehicle_event(vehicle_match, current_time)
            if vehicle_event:
                should_buffer = False
                
                if vehicle_event.damage_cause.lower() == 'ejection':
                    self.logger.info(f"Ejection detected: {vehicle_event.destroyer_name} ejected from {vehicle_event.vehicle_name}")
                    ejection_event = self._create_ejection_event(vehicle_event)
                    if ejection_event:
                        correlated_events.append(ejection_event)
                    return None, correlated_events
                
                if vehicle_event.destroy_level == 1:
                    timeout = self.disabled_timeout
                elif vehicle_event.destroy_level == 2:
                    timeout = self.destroyed_timeout
                else:
                    timeout = self.correlation_timeout
                
                if vehicle_event.destroyer_name.lower() in ['unknown', ''] or vehicle_event.destroyer_id == '0':
                    should_buffer = True
                    self.logger.info(f"Buffering vehicle destruction (unknown destroyer): {vehicle_event.vehicle_name} (level {vehicle_event.destroy_level})")
                
                elif timeout == 0:
                    self.logger.info(f"Processing immediate vehicle event (0 timeout): {vehicle_event.vehicle_name} by {vehicle_event.destroyer_name}")
                    display_event = self._create_vehicle_destruction_event(vehicle_event)
                    if display_event:
                        correlated_events.append(display_event)
                    should_buffer = False
                
                elif vehicle_event.destroy_level == 1:
                    if timeout > 0:
                        should_buffer = True
                        self.logger.info(f"Buffering vehicle disabled event for {timeout}s: {vehicle_event.vehicle_name} by {vehicle_event.destroyer_name}")
                    else:
                        self.logger.info(f"Creating immediate vehicle disabled event: {vehicle_event.vehicle_name} by {vehicle_event.destroyer_name}")
                        display_event = self._create_vehicle_destruction_event(vehicle_event)
                        if display_event:
                            correlated_events.append(display_event)
                        should_buffer = False
                
                elif vehicle_event.destroy_level == 2:
                    if timeout > 0:
                        should_buffer = True
                        self.logger.info(f"Buffering vehicle hard death for occupant correlation ({timeout}s): {vehicle_event.vehicle_name}")
                    else:
                        self.logger.info(f"Creating immediate vehicle destroyed event: {vehicle_event.vehicle_name} by {vehicle_event.destroyer_name}")
                        display_event = self._create_vehicle_destruction_event(vehicle_event)
                        if display_event:
                            correlated_events.append(display_event)
                        should_buffer = False
                
                if should_buffer:
                    with self._pending_lock:
                        self.pending_vehicle_events.append(vehicle_event)
                else:
                    self.logger.info(f"Processing immediate vehicle destruction: {vehicle_event.vehicle_name} level {vehicle_event.destroy_level}")
                    kill_event = self._create_kill_event_from_vehicle(vehicle_event)
                    if kill_event:
                        correlated_events.append(kill_event)

        actor_match = self.actor_death_pattern.search(line)
        if actor_match:
            actor_event = self._parse_actor_event(actor_match, current_time)
            if actor_event and actor_event.damage_type.lower() == 'vehicledestruction':
                if self._is_vehicle_entity_death(actor_event.victim):
                    self.logger.debug(f"Skipping vehicle entity death: {actor_event.victim}")
                    return None, correlated_events
                
                if KillParser.is_npc(actor_event.victim, actor_event.victim_id):
                    self.logger.debug(f"Skipping NPC vehicle death: {actor_event.victim}")
                    return None, correlated_events
                
                correlated_vehicle = self._find_correlating_vehicle_event(actor_event)
                if correlated_vehicle:
                    self.logger.info(f"Correlated actor death with vehicle destruction: {actor_event.victim} in {correlated_vehicle.vehicle_name}")
                    kill_event = self._create_correlated_kill_event(correlated_vehicle, actor_event)
                    if kill_event:
                        correlated_events.append(kill_event)
                    with self._pending_lock:
                        try:
                            self.pending_vehicle_events.remove(correlated_vehicle)
                        except ValueError:
                            self.logger.debug("Pending vehicle event already removed by cleanup thread")
                else:
                    self.logger.debug(f"No vehicle correlation found for actor death: {actor_event.victim}")
        
        expired_display_events = self._cleanup_expired_events(current_time)
        
        correlated_events.extend(expired_display_events)
        
        return None, correlated_events

    def _parse_vehicle_event(self, match, log_time: float) -> Optional[VehicleDestroyEvent]:
        """Parse vehicle destruction event from regex match"""
        try:
            data = match.groupdict()
            return VehicleDestroyEvent(
                timestamp=data.get('timestamp', ''),
                vehicle_id=data.get('vehicle_id', ''),
                vehicle_name=data.get('vehicle_name', ''),
                zone=data.get('zone', ''),
                position=(
                    float(data.get('x', 0)),
                    float(data.get('y', 0)),
                    float(data.get('z', 0))
                ),
                destroyer_id=data.get('destroyer_id', ''),
                destroyer_name=data.get('destroyer', ''),
                destroy_level=int(data.get('to_level', 0)),
                damage_cause=data.get('damage_cause', 'Combat'),
                log_time=log_time
            )
        except (ValueError, KeyError) as e:
            self.logger.error(f"Error parsing vehicle event: {e}")
            return None

    def _parse_actor_event(self, match, log_time: float) -> Optional[ActorDeathEvent]:
        """Parse actor death event from regex match"""
        try:
            data = match.groupdict()
            return ActorDeathEvent(
                timestamp=data.get('timestamp', ''),
                victim=data.get('victim', ''),
                victim_id=data.get('victim_geid', ''),
                attacker=data.get('attacker', ''),
                attacker_id=data.get('attacker_geid', ''),
                weapon=data.get('weapon', ''),
                damage_type=data.get('damage_type', ''),
                zone=data.get('zone', ''),
                log_time=log_time
            )
        except (ValueError, KeyError) as e:
            self.logger.error(f"Error parsing actor event: {e}")
            return None

    def _is_vehicle_entity_death(self, victim_name: str) -> bool:
        """
        Determine if this is a vehicle entity death rather than a player death.
        Vehicle entities often have patterns like:
        - Long numeric IDs: ARGO_ATLS_6282649965732
        - AI module names: AIModule_Unmanned_PU_*
        - Vehicle type names as IDs
        """
        if not victim_name:
            return True
            
        if re.match(r'^[A-Z]{3,4}_[A-Za-z0-9_]+_\d{10,}$', victim_name):
            self.logger.debug(f"Identified vehicle entity: {victim_name}")
            return True
            
        if victim_name.startswith('AIModule_') or victim_name.startswith('AI_'):
            self.logger.debug(f"Identified AI entity: {victim_name}")
            return True
            
        vehicle_prefixes = ['AEGS_', 'ANVL_', 'CRUS_', 'DRAK_', 'MISC_', 'ORIG_', 'RSI_', 'ARGO_', 'BANU_', 'CNOU_', 'XIAN_', 'GAMA_', 'TMBL_', 'ESPR_', 'KRIG_', 'GRIN_', 'XNAA_', 'MRAI_', 'VNCL_']
        if any(victim_name.startswith(prefix) for prefix in vehicle_prefixes):
            if not re.search(r'[a-z]', victim_name.lower()) or '_' in victim_name:
                self.logger.debug(f"Identified vehicle type entity: {victim_name}")
                return True
                
        return False

    def _find_correlating_vehicle_event(self, actor_event: ActorDeathEvent) -> Optional[VehicleDestroyEvent]:
        """Find a vehicle event that correlates with the actor death"""
        best_match = None
        best_score = 0
        
        self.logger.debug(f"Looking for correlation for actor death: {actor_event.victim} in zone: {actor_event.zone}")
        
        for vehicle_event in self.pending_vehicle_events:
            score = self._calculate_correlation_score(vehicle_event, actor_event)
            self.logger.debug(f"  Vehicle {vehicle_event.vehicle_name}: score={score:.2f}")
            if score > best_score and score > 0.3:
                best_score = score
                best_match = vehicle_event
        
        if best_match:
            self.logger.debug(f"  Best match: {best_match.vehicle_name} with score {best_score:.2f}")
        else:
            self.logger.debug(f"  No match found above threshold")
        
        return best_match

    def _create_vehicle_destruction_event(self, vehicle_event: VehicleDestroyEvent) -> Dict:
        """Create a vehicle destruction display event (not a kill)"""
        name_lower = (vehicle_event.vehicle_name or '').lower()
        if vehicle_event.destroy_level in (1, 2):
            for pattern in self.npc_patterns:
                if pattern in name_lower:
                    self.logger.debug(f"Skipping display for AI/NPC vehicle '{vehicle_event.vehicle_name}' (pattern '{pattern}')")
                    return None

        cleaned_vehicle = vehicle_event.vehicle_name.replace('_', ' ')

        return {
            'event_type': 'vehicle_destruction',
            'timestamp': vehicle_event.timestamp,
            'vehicle_name': cleaned_vehicle,
            'destroyer': vehicle_event.destroyer_name,
            'destroyer_id': vehicle_event.destroyer_id,
            'zone': vehicle_event.zone,
            'destroy_level': vehicle_event.destroy_level,
            'damage_cause': getattr(vehicle_event, 'damage_cause', 'Combat'),
            'log_line': f"VEHICLE DESTROYED: {cleaned_vehicle} destroyed by {vehicle_event.destroyer_name}",
            'display_only': True
        }

    def _create_ejection_event(self, vehicle_event: VehicleDestroyEvent) -> Dict:
        """Create an ejection display event"""
        name_lower = (vehicle_event.vehicle_name or '').lower()
        for pattern in self.npc_patterns:
            if pattern in name_lower:
                self.logger.debug(f"Skipping display for AI/NPC vehicle ejection '{vehicle_event.vehicle_name}' (pattern '{pattern}')")
                return None

        cleaned_vehicle = vehicle_event.vehicle_name.replace('_', ' ')

        return {
            'event_type': 'ejection',
            'timestamp': vehicle_event.timestamp,
            'vehicle_name': cleaned_vehicle,
            'pilot': vehicle_event.destroyer_name,
            'pilot_id': vehicle_event.destroyer_id,
            'zone': vehicle_event.zone,
            'destroy_level': vehicle_event.destroy_level,
            'damage_cause': 'Ejection',
            'log_line': f"EJECTION: {vehicle_event.destroyer_name} ejected from {cleaned_vehicle}",
            'display_only': True
        }

    def _calculate_correlation_score(self, vehicle_event: VehicleDestroyEvent, actor_event: ActorDeathEvent) -> float:
        """Calculate correlation score between vehicle and actor events"""
        score = 0.0
        
        time_diff = abs(actor_event.log_time - vehicle_event.log_time)
        if time_diff <= 5.0:
            score += 0.5
        elif time_diff <= 15.0:
            score += 0.3
        else:
            return 0.0
        
        """Destruction level analysis - crucial for understanding the event
        0→1: Soft death (ship disabled) - occupants may survive, less likely to cause immediate death
        1→2: Hard death (ship destroyed) - occupants likely killed"""
        
        destroy_level_factor = 1.0
        if vehicle_event.destroy_level == 1:
            destroy_level_factor = 0.7
            self.logger.debug(f"  Vehicle soft death (0→1): reducing correlation likelihood")
        elif vehicle_event.destroy_level == 2:
            destroy_level_factor = 1.2
            self.logger.debug(f"  Vehicle hard death (1→2): increasing correlation likelihood")
        
        zone_match = False
        if (vehicle_event.zone == actor_event.zone or 
            vehicle_event.vehicle_name == actor_event.zone or
            vehicle_event.vehicle_id in actor_event.zone):
            zone_match = True
            score += 0.3
        
        if vehicle_event.destroy_level == 1 and zone_match:
            self.logger.debug(f"  Vehicle soft death with occupant death - likely correlation")
            score += 0.2
        
        if vehicle_event.destroy_level == 1 and not zone_match:
            self.logger.debug(f"  Vehicle soft death without zone match - likely player downing")
            score *= 0.5
        
        if (vehicle_event.destroyer_name.lower() != 'unknown' and 
            vehicle_event.destroyer_name == actor_event.attacker):
            score += 0.2
        
        if actor_event.damage_type.lower() == 'vehicledestruction':
            score += 0.1

        score *= destroy_level_factor
        
        return score

    def _create_kill_event_from_vehicle(self, vehicle_event: VehicleDestroyEvent) -> Optional[Dict]:
        """Create kill event from vehicle destruction (when destroyer is known)"""

        return None

    def _create_correlated_kill_event(self, vehicle_event: VehicleDestroyEvent, actor_event: ActorDeathEvent) -> Optional[Dict]:
        """Create kill event from correlated vehicle and actor events"""
        
        if KillParser.is_npc(actor_event.victim, actor_event.victim_id):
            self.logger.info(f"NPC kill detected in vehicle correlation (victim: {actor_event.victim}). Not processing.")
            return None
        
        if vehicle_event.destroy_level == 1:
            kill_context = "soft_death"
            log_description = f"CORRELATED: Vehicle '{vehicle_event.vehicle_name}' disabled (0→1), occupant '{actor_event.victim}' killed by '{actor_event.attacker}'"
        elif vehicle_event.destroy_level == 2:
            kill_context = "hard_death"
            log_description = f"CORRELATED: Vehicle '{vehicle_event.vehicle_name}' destroyed (1→2), killing '{actor_event.victim}' by '{actor_event.attacker}'"
        else:
            kill_context = "unknown_death"
            log_description = f"CORRELATED: Vehicle '{vehicle_event.vehicle_name}' destroyed, killing '{actor_event.victim}' by '{actor_event.attacker}'"
        
        return {
            'event_type': 'correlated_vehicle_kill',
            'kill_context': kill_context,
            'timestamp': actor_event.timestamp,
            'victim': actor_event.victim,
            'victim_id': actor_event.victim_id,
            'attacker': actor_event.attacker,
            'attacker_id': actor_event.attacker_id,
            'weapon': actor_event.weapon,
            'damage_type': 'vehicledestruction',
            'zone': actor_event.zone,
            'vehicle_name': vehicle_event.vehicle_name,
            'vehicle_id': vehicle_event.vehicle_id,
            'destroy_level': vehicle_event.destroy_level,
            'vehicle_zone': vehicle_event.zone,
            'log_line': log_description
        }

    def _cleanup_expired_events(self, current_time: float) -> List[Dict]:
        """Remove vehicle events that have exceeded their specific timeout and create display events for them"""
        expired_events = []
        remaining_events = []

        with self._pending_lock:
            for event in list(self.pending_vehicle_events):
                if event.destroy_level == 1:
                    timeout = self.disabled_timeout
                elif event.destroy_level == 2:
                    timeout = self.destroyed_timeout
                else:
                    timeout = self.correlation_timeout

                if current_time - event.log_time >= timeout:
                    display_event = self._create_vehicle_destruction_event(event)
                    if display_event:
                        expired_events.append(display_event)
                        destruction_type = "DISABLED" if event.destroy_level == 1 else "DESTROYED" if event.destroy_level == 2 else "DAMAGED"
                        self.logger.info(f"Timeout ({timeout}s): Creating vehicle {destruction_type.lower()} event for {event.vehicle_name}")
                    else:
                        self.logger.debug(f"Timeout ({timeout}s): Skipping AI/NPC vehicle display for {event.vehicle_name}")
                    try:
                        self.pending_vehicle_events.remove(event)
                    except ValueError:
                        pass
                else:
                    remaining_events.append(event)
        
        if expired_events:
            self.logger.debug(f"Converted {len(expired_events)} expired vehicle events to display events")
        
        return expired_events

    def start_cleanup_thread(self) -> None:
        """Start background cleanup thread. Safe to call multiple times."""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return

        self._cleanup_stop.clear()
        def _run():
            self.logger.debug("VehicleEventCorrelator cleanup thread started")
            while not self._cleanup_stop.is_set():
                try:
                    now = time.time()
                    expired = self._cleanup_expired_events(now)
                    if expired and self.event_callback:
                        for event in expired:
                            self.event_callback(event)
                except Exception:
                    self.logger.exception("Exception in cleanup thread")
                self._cleanup_stop.wait(self._cleanup_interval)
            self.logger.debug("VehicleEventCorrelator cleanup thread stopping")

        self._cleanup_thread = threading.Thread(target=_run, daemon=True, name="VECleanupThread")
        self._cleanup_thread.start()

    def stop_cleanup_thread(self, wait: bool = False) -> None:
        """Signal the cleanup thread to stop. If wait=True join the thread."""
        self._cleanup_stop.set()
        if wait and self._cleanup_thread:
            self._cleanup_thread.join(timeout=2.0)

    def get_pending_count(self) -> int:
        """Get count of pending vehicle events waiting for correlation"""
        return len(self.pending_vehicle_events)

    def clear_pending_events(self) -> None:
        """Clear all pending vehicle events (useful for testing or reset)"""
        count = len(self.pending_vehicle_events)
        self.pending_vehicle_events.clear()
        if count > 0:
            self.logger.info(f"Cleared {count} pending vehicle events")