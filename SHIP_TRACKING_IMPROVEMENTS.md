# Ship Tracking Improvements

## Problem Statement

The system was incorrectly categorizing kills as "Player destruction" even when the player was in a ship and used ship-mounted weapons or turrets. This happened because:

1. **Vehicle Destruction** only triggered when `damage_type == "vehicledestruction"` (ship exploding)
2. **Ship-based kills with weapons** (like turrets, ship guns shooting players) had damage types like "Bullet", "Energy", etc.
3. The system defaulted to "Player destruction" for any non-vehicledestruction damage type

### Example Case
```
Kill: UNIBaller69 killed Orelion_Khane using MXOX_NeutronRepeater_S3
Damage Type: Bullet
Expected: Vehicle destruction (because player was in ship)
Actual (before fix): Player destruction
```

## Solution

### 1. Added Ship Occupancy Tracking

**File: `Kill_thread.py`**

Added a new state variable `is_in_ship` to track whether the player is currently in a ship:

```python
self.is_in_ship: bool = False  # Track whether player is currently in a ship
```

### 2. Update Ship State on Vehicle Events

**Vehicle Control Get In** (when entering a ship):
```python
self.current_attacker_ship = cleaned_ship
self.is_in_ship = True  # Player is now in a ship
```

**Vehicle Control Get Out** (when exiting a ship):
```python
self.current_attacker_ship = "No Ship"
self.is_in_ship = False  # Player is no longer in a ship
```

**Player Death**:
```python
self.current_attacker_ship = "No Ship"
self.is_in_ship = False  # Player died, no longer in ship
```

### 3. Enhanced Kill Method Determination

**File: `kill_event_formatter.py`**

Updated `determine_engagement_and_method()` to consider ship occupancy:

```python
def determine_engagement_and_method(damage_type: str, killer_ship: str, formatted_weapon: str, is_in_ship: bool = False):
    if damage_type.lower() == "vehicledestruction":
        # Vehicle was destroyed (ship explosion killed player)
        method = "Vehicle destruction"
        engagement = f"{ship} using {weapon}" if ship else weapon
    else:
        # Player entity died (not vehicle destruction)
        method = "Player destruction"
        # Include ship name if player was in a ship
        engagement = f"{ship} using {weapon}" if is_in_ship and ship else weapon
```

**Key Logic:**
- **Method** is determined ONLY by damage_type:
  - `"vehicledestruction"` → "Vehicle destruction"
  - Anything else → "Player destruction"
- **Engagement** shows ship name when `is_in_ship = True`

**Result Matrix:**

| Killer State | Damage Type | Method | Engagement Example |
|-------------|-------------|--------|-------------------|
| In ship | vehicledestruction | Vehicle destruction | "AEGS Sabre using Size 3 Cannon" |
| In ship | Bullet/Energy/etc | Player destruction | "AEGS Sabre using Mantis GT-220" |
| On foot | Bullet/Energy/etc | Player destruction | "P4-AR Rifle" |
| On foot | vehicledestruction | Vehicle destruction | "Grenade" |

### 4. Pass Ship State Through the Chain

**Updated function signatures:**
- `format_registered_kill()` - Added `is_in_ship` parameter
- `RegisteredKillFormatter.format_event()` - Added `is_in_ship` parameter
- `determine_engagement_and_method()` - Added `is_in_ship` parameter

**Updated call in Kill_thread.py:**
```python
readout, payload = format_registered_kill(
    line, data, self.registered_user, full_timestamp, 
    captured_game_mode, success=True, is_in_ship=self.is_in_ship
)
```

## How It Works Now

### Scenario 1: Ship Weapons Kill Player (On-Foot or In-Ship)
1. Player enters ship → `is_in_ship = True`, `current_attacker_ship = "AEGS Sabre"`
2. Player kills someone with ship weapons → `damage_type = "Bullet"` (player entity died, not ship)
3. System checks: `damage_type != "vehicledestruction"`
4. Engagement shows ship: `"AEGS Sabre using MXOX Neutron Repeater S3"`
5. **Result: Method = "Player destruction"** ✅

### Scenario 2: Ship Destruction (Ship Explodes)
1. Player in ship destroys enemy ship
2. Enemy ship explodes, killing the pilot → `damage_type = "vehicledestruction"`
3. **Result: Method = "Vehicle destruction"** ✅

### Scenario 3: On-Foot Kill
1. Player exits ship → `is_in_ship = False`, `current_attacker_ship = "No Ship"`
2. Player kills someone with FPS weapon → `damage_type = "Bullet"`
3. System checks: `is_in_ship = False`
4. Engagement shows only weapon: `"P4-AR Rifle"`
5. **Result: Method = "Player destruction"** ✅

### Scenario 4: Player Dies Then Respawns
1. Player dies → `is_in_ship = False`, `current_attacker_ship = "No Ship"`
2. Player spawns and kills on foot
3. **Result: Method = "Player destruction"** ✅

## Benefits

1. **Accurate Classification**: 
   - **Vehicle destruction** = Ship/vehicle was destroyed (explosion)
   - **Player destruction** = Player entity died (regardless of weapon used)
2. **Enhanced Context**: Shows ship name in engagement description when player was in a ship
3. **Smart State Management**: System knows when you're in/out of ships
4. **Backwards Compatible**: Doesn't break existing vehicle destruction detection
5. **Proper Distinction**: Distinguishes between destroying a vehicle vs killing a player

## Additional Fix: GLSN Manufacturer Support

Added "GLSN" to the list of recognized ship manufacturer codes in:
- Jump Drive processing (line ~421)
- Vehicle Control Get In processing (line ~454)  
- Ship history reconstruction (line ~281)
- RescanThread ship tracking (line ~950)

Now recognizes: ORIG, CRUS, RSI, AEGS, VNCL, DRAK, ANVL, BANU, MISC, CNOU, XIAN, GAMA, TMBL, ESPR, KRIG, GRIN, XNAA, MRAI, **GLSN**

## Mid-Session Startup Enhancement

### Problem
When starting the program mid-game, the system didn't know if the player was currently in a ship or on foot.

### Solution
Enhanced `reconstruct_ship_history()` method to:
1. Scan through entire log file from beginning
2. Track all Vehicle Control Get In/Out events
3. Track player deaths (which reset ship state)
4. Determine final ship state before live monitoring begins
5. Set both `current_attacker_ship` AND `is_in_ship` flags correctly

**Result:** Starting mid-session now correctly shows:
- Ship name in UI if player is currently in a ship
- "No Ship" if player is on foot
- Proper `is_in_ship` state for accurate kill classification

## Testing Recommendations

1. **In ship, kill on-foot player with ship weapons** → Should show "Player destruction" with ship name in engagement (e.g., "AEGS Sabre using Mantis GT-220")
2. **In ship, destroy enemy ship** → Should show "Vehicle destruction" with ship name in engagement
3. **Exit ship and kill on foot** → Should show "Player destruction" with only weapon name
4. **Die, respawn, kill on foot** → Should show "Player destruction" with only weapon name
5. **Use GLSN manufacturer ships** → Should not show manufacturer warning
