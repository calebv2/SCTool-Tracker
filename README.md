# SCTool Tracker

## Video instructions

`https://www.youtube.com/watch?v=d8SwnmVPuGI`

## Overview

SCTool Tracker is an application for Star Citizen that monitors the game's log file to track and record player kills and deaths. This tool provides real-time notifications about combat events and sends this data to the SCTool API to maintain your combat statistics.

## How It Works

The tracker operates by:

1. **Log File Monitoring**: The application continuously reads the Star Citizen Game.log file to detect combat events.
2. **Event Parsing**: When a kill or death event is detected, it extracts relevant information such as attacker, victim, weapon, location, and timestamp.
3. **UI Display**: Combat events are displayed in the application with formatted panels showing detailed information about each event.
4. **API Integration**: Kill data can be sent to the starcitizentool.com API to track your statistics over time.
5. **Ship Detection**: The tracker can detect which ship you're using for accurate kill attribution.

## Getting Started

### Requirements
- Windows operating system
- Star Citizen installed
- Python 3.8+ (if running from source)
- PyQt5 (if running from source)

### Installation

1. Download the latest release from [starcitizentool.com/download-sctool](https://starcitizentool.com/download-sctool)
2. Extract the files to a location of your choice
3. Run the SCTool Tracker executable

### Configuration

1. **API Key**: Enter your API key from starcitizentool.com in the provided field
2. **Game.log Path**: Select your Star Citizen Game.log file location (typically in the game's LIVE folder)
3. **Sound Settings**: Configure optional sound notifications for kills
4. **Killer Ship**: Select or enter your current ship for proper attribution

## Features

- **Real-time Kill/Death Tracking**: Instantly see your combat events as they happen
- **API Integration**: Send your kills to the SCTool API for statistics tracking
- **Ship Detection**: Automatically detects your current ship
- **Kill Sound**: Optional sound notification when you get a kill
- **Missing Kill Detection**: Scan for kills that might have been missed
- **Game Mode Detection**: Identifies which game mode you're playing (PU, Arena Commander, etc.)

## Building Your Own Tracker

If you want to build your own tracker that integrates with the SCTool API, follow these guidelines:

### API Integration

1. **Obtain an API Key**: Contact starcitizentool.com to get an API key
2. **API Endpoints**: 
   - Kills: `https://starcitizentool.com/api/v1/kills`
   - Deaths: `https://starcitizentool.com/api/v1/deaths`

### Required Headers

```
Content-Type: application/json
X-API-Key: YOUR_API_KEY
User-Agent: YOUR_APPLICATION_NAME
X-Client-ID: YOUR_CLIENT_ID
X-Client-Version: YOUR_VERSION
```

### Payload Structure

When sending a kill event to the API, your JSON payload should include:

```json
{
  "log_line": "Raw log line from the game",
  "game_mode": "Game mode (PU, Elimination, etc.)",
  "killer_ship": "Ship used by the attacker (optional)",
  "method": "Vehicle destruction or Player destruction"
}
```

### Log File Format

Star Citizen combat events follow this pattern in the log file:

```
<timestamp> [Notice] <Actor Death> CActor::Kill: 'victim' [victim_geid] in zone 'zone' killed by 'attacker' [attacker_geid] using 'weapon' [...] with damage type 'damage_type' from direction x: X, y: Y, z: Z [...]
```

You'll need to parse this format to extract the necessary information.

### Implementation Tips

1. **Log File Monitoring**: Use file reading techniques that can handle file rotation and changes
2. **Player Registration**: Look for login events to determine the local player's handle
3. **Game Mode Detection**: Monitor for game mode change events
4. **Ship Detection**: Parse relevant log entries to determine the player's current ship
5. **Duplicate Prevention**: Track already-logged kills to prevent duplicates
6. **Error Handling**: Implement retry logic for API requests

## Contributing

Contributions to SCTool Tracker are welcome! If you'd like to contribute:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

SCTool Tracker is proprietary software. Unauthorized distribution or modification is prohibited.

## Contact

For support or inquiries, please visit [starcitizentool.com](https://starcitizentool.com).