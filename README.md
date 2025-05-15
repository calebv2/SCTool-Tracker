# SCTool Tracker

## Video instructions

`https://www.youtube.com/watch?v=d8SwnmVPuGI`

## Overview

SCTool Tracker is an application for Star Citizen that monitors the game's log file to track and record player kills and deaths. This tool provides real-time notifications about combat events and sends this data to the SCTool API to maintain your combat statistics. The current version is 4.6.

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
- Python 3.10+ (recommended, if running from source)
- PyQt5 5.15.0+ (if running from source)
- BeautifulSoup4 4.9.0+ (if running from source)
- Requests 2.25.0+ (if running from source)
- Packaging 20.0+ (if running from source)

### Installation

1. Download the latest release (v4.6) from [starcitizentool.com/download-sctool](https://starcitizentool.com/download-sctool)
2. Run the installer (SCTool_Killfeed_4.6_Setup.exe)
3. Follow the installation wizard instructions
4. Launch SCTool Tracker from your desktop or start menu

For manual installation:
1. Download the standalone executable
2. Extract the files to a location of your choice
3. Run Kill_main.exe

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
- **Session Statistics**: Track kills, deaths, and K/D ratio for your current session
- **Rescan Capability**: Search through your game logs to find kills that may have been missed
- **Export Functionality**: Save your combat logs as HTML for future reference
- **Auto-Updates**: Automatically download and install the latest version
- **System Tray Integration**: Minimize to system tray for unobtrusive operation
- **Twitch Integration**: Create clips and post kill messages to your Twitch chat
- **User Profile Images**: Display profile images fetched from RSI website
- **Start with Windows**: Option to launch automatically on system startup
- **Responsive Design**: Adapts to different screen resolutions and DPI settings
- **Modern UI**: Sleek, dark-themed interface with customizable settings

## Technical Architecture

The SCTool Tracker is built with a modular architecture consisting of several key components:

### Core Components

1. **Main Application (Kill_main.py)**: Entry point that initializes the GUI and monitoring systems
2. **GUI Interface (Kill_form.py)**: PyQt5-based interface that displays kill/death events and provides user controls
3. **Log Monitoring (Kill_thread.py)**: Background threads that monitor the game log file in real-time
4. **Event Parser (kill_parser.py)**: Specialized parser that extracts combat data from log entries
5. **Event Formatters (Registered_kill.py, Death_kill.py)**: Format extracted data into visual HTML displays
6. **Twitch Integration (twitch_integration.py)**: Handles Twitch authentication, chat messaging, and clip creation
7. **Profile System (fetch.py)**: Retrieves player profiles and avatar images from RSI website
8. **Responsive UI (responsive_ui.py)**: Handles high-DPI display scaling and responsive interface elements
9. **Utility Functions (utlity.py)**: Common utilities and helper functions for UI and configuration

### Data Flow

1. TailThread monitors the Game.log file for new entries
2. When a combat event is detected, the log line is parsed using regular expressions
3. Extracted data is formatted into HTML and displayed in the application
4. Player profile images are fetched from the RSI website for both the user and victims
5. If API integration is enabled, the data is sent to the SCTool API
6. Local statistics are updated and displayed in the session panel
7. If Twitch integration is enabled, kill events can trigger clip creation and chat messages
8. Responsive UI system adjusts the interface based on screen resolution and DPI

### File Structure

- **Kill_main.py**: Main entry point of the application
- **Kill_form.py**: Main GUI implementation and application logic
- **Kill_thread.py**: Background monitoring threads and API communication
- **kill_parser.py**: Log parsing and data extraction utilities
- **Registered_kill.py**: Formats kill events for display
- **Death_kill.py**: Formats death events for display
- **twitch_integration.py**: Twitch API integration for clips and chat
- **fetch.py**: Functions for fetching profile data and images
- **responsive_ui.py**: High-DPI support and responsive interface scaling
- **utlity.py**: Utility functions and UI helpers
- **README.md**: Documentation
- **config.json**: User configuration storage
- **ships.json**: Ship database and recognition data
- **twitch_config.json**: Twitch integration settings

## Log File Parsing Details

Star Citizen logs combat events in a specific format that the tracker parses. The key patterns include:

### Kill Events

```
<timestamp> [Notice] <Actor Death> CActor::Kill: 'victim' [victim_geid] in zone 'zone' killed by 'attacker' [attacker_geid] using 'weapon' [...] with damage type 'damage_type' from direction x: X, y: Y, z: Z [...]
```

### Ship Detection

The tracker identifies the player's current ship through:

1. **Jump Drive Events**: When a player uses a quantum drive
2. **Interior Zone Changes**: When a player enters or exits a ship
3. **Manual Selection**: User can manually select their current ship

### Game Mode Detection

Game modes are detected through log entries following this pattern:

```
<timestamp> Loading GameModeRecord='game_mode' with EGameModeId='id'
```

### Profile Image System

The tracker retrieves player profile images from the RSI website using the following process:

1. **Image Lookup**: The system queries the RSI website profile page for a given username
2. **Image Extraction**: BeautifulSoup parses the HTML to locate the profile image URL
3. **Circular Display**: Images are processed into circular avatars with a border
4. **Default Fallback**: If no image is found or an error occurs, a default image is displayed
5. **Caching**: Profile data is cached to reduce API calls and improve performance

### Twitch Integration

The tracker offers comprehensive Twitch integration:

1. **Authentication**: OAuth authentication flow for secure connection to Twitch
2. **Clip Creation**: Automatically creates clips when you get a kill
3. **Chat Messages**: Posts kill notifications to your Twitch chat
4. **Clip Delay**: Configurable delay for clip creation after a kill event
5. **Custom Messages**: Customizable templates for Twitch chat messages

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

When sending a death event to the API, your JSON payload should include:

```json
{
  "log_line": "Raw log line from the game",
  "game_mode": "Game mode (PU, Elimination, etc.)",
  "victim_name": "Name of the victim",
  "attacker_name": "Name of the attacker",
  "weapon": "Weapon used",
  "damage_type": "Type of damage",
  "location": "Location of death",
  "timestamp": "Timestamp of the death",
  "event_type": "death"
}
```

### Development Setup

1. Clone the repository or start a new Python project
2. Install required dependencies:
   ```
   pip install PyQt5 beautifulsoup4 requests packaging
   ```
3. Implement the core components: log monitoring, parsing, and API integration
4. Test with actual Star Citizen log files

### Building the Executable

1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```
2. Build the standalone executable:
   ```
   pyinstaller --onefile --icon=chris2.ico --name=Kill_main Kill_main.py
   ```
3. For the installer build, use Inno Setup with the included SCTool.iss script
4. The compiled installer will be generated as SCTool_Killfeed_[version]_Setup.exe

## Troubleshooting

Common issues and solutions:

- **Ship Not Detected**: Manually select your ship in the Killer Ship dropdown
- **Kills Not Showing**: Verify the path to your Game.log file is correct
- **API Connection Fails**: Check your network connection and API key
- **Missed Kills**: Use the "Find Missed Kills" feature to scan for unregistered kills
- **Application Crashes**: Check the kill_logger.log file in the application data folder for error details
- **Twitch Integration Issues**: Ensure your Twitch channel name is correct and try reconnecting
- **Profile Images Not Loading**: Check your internet connection or RSI website availability
- **Display Scaling Issues**: Enable high-DPI scaling in Windows for better UI rendering

## Data Storage

The application stores configuration and data in the following locations:

- **Configuration**: `%APPDATA%\SCTool_Tracker\config.json`
- **Local Kill Cache**: `%APPDATA%\SCTool_Tracker\logged_kills.json`
- **Application Logs**: `%APPDATA%\SCTool_Tracker\kill_logger.log`
- **Updates**: `%APPDATA%\SCTool_Tracker\Updates\`
- **Twitch Settings**: `twitch_config.json` in the application directory
- **Ship Database**: `ships.json` in the application directory
- **Sound Files**: `kill.wav` in the application directory
- **Profile Images**: Fetched at runtime from RSI website

## Auto-Update System

The application includes an automatic update system that:

1. **Checks for Updates**: Periodically checks for new versions on the SCTool server
2. **Downloads Updates**: Automatically downloads new versions when available
3. **Installation**: Prompts the user to install the update or installs silently based on settings
4. **Update Storage**: Downloaded updates are stored in `%APPDATA%\SCTool_Tracker\Updates\`
5. **Version Checking**: Uses semantic versioning to determine when updates are available

## Contributing

Contributions to SCTool Tracker are welcome! If you'd like to contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Implement your changes
4. Test thoroughly with actual Star Citizen logs
5. Update documentation as needed
6. Commit your changes (`git commit -m 'Add some amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Submit a pull request

### Development Suggestions

- **Log Patterns**: Star Citizen frequently updates its log format. Adding support for new patterns is always valuable.
- **UI Improvements**: The application uses PyQt5 and can benefit from UI/UX enhancements.
- **Performance Optimization**: Improving the log parsing efficiency for large log files.
- **Additional Game Modes**: Adding support for new Star Citizen game modes as they're released.

## Contact

For support or inquiries:
- Website: [starcitizentool.com](https://starcitizentool.com)
- Email: support@starcitizentool.com
- Discord: Join our community server at [discord.gg/starcitizentool](https://discord.gg/starcitizentool)
- YouTube: Watch tutorials at [youtube.com/starcitizentool](https://youtube.com/starcitizentool)

## License

SCTool Tracker is proprietary software. All rights reserved.