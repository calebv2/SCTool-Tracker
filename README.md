# SCTool Tracker

## Video instructions

`https://www.youtube.com/watch?v=d8SwnmVPuGI`

## Overview

SCTool Tracker is an application for Star Citizen that monitors the game's log file to track and record player kills and deaths. 7. **Twitch Integration (twitch_integration.py)**: Handles Twitch authentication, chat messaging, and clip creation
8. **Game Overlay System (overlay.py)**: Advanced overlay system with 5 display modes, global hotkeys, and real-time statistics
9. **Profile System (fetch.py)**: Retrieves player profiles and avatar images from RSI website
10. **Responsive UI (responsive_ui.py)**: Handles high-DPI display scaling and responsive interface elements
11. **Utility Functions (utlity.py)**: Common utilities and helper functions for UI and configuration tool provides real-time notifications about combat events and sends this data to the SCTool API to maintain your combat statistics. The current version is 4.6.

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
- **Twitch Integration**: Create clips and post kill messages to your Twitch chat with configurable delays
- **Button Automation System**: Automatically execute custom key sequences after kill events
- **User Profile Images**: Display profile images fetched from RSI website with organization info
- **Start with Windows**: Option to launch automatically on system startup
- **Responsive Design**: Adapts to different screen resolutions and DPI settings with automatic scaling
- **Modern UI**: Sleek, dark-themed interface with customizable settings and themes

## Game Overlay System

SCTool Tracker includes a powerful **Game Overlay System** that provides real-time statistics directly on top of Star Citizen while you play. This overlay system offers multiple display modes, customizable themes, and advanced features for enhanced gameplay experience.

### Overlay Features

- **5 Display Modes**: Choose from Minimal, Compact, Detailed, Horizontal, and Faded notification modes
- **Global Hotkey Support**: System-wide hotkey detection (default: `Ctrl+\``) for overlay toggling
- **Real-time Statistics**: Live kill/death counts, K/D ratio, session time, ship info, and game mode
- **Kill/Death Notifications**: Rich notifications in faded mode with player organization info and profile images
- **Customization Options**: 3 themes (Default, Dark, Neon), opacity control, positioning, and animations
- **Advanced Control Panel**: Comprehensive configuration interface with all overlay settings
- **Integration Features**: Seamless integration with main application for live data updates
- **Visual Effects**: Animations, glow effects, drag-and-drop positioning, and visual feedback

### Display Modes

#### 1. Minimal Mode
- **Purpose**: Ultra-compact display showing only essential kill/death counts
- **Features**: Small footprint, minimal UI elements, perfect for competitive gameplay
- **Layout**: Simple kill and death counters with minimal styling

#### 2. Compact Mode (Default)
- **Purpose**: Balanced view with essential statistics in a clean layout
- **Features**: Kills, deaths, K/D ratio, session time, game mode, and ship information
- **Layout**: Organized grid layout with clear sections and mode cycling button

#### 3. Detailed Mode
- **Purpose**: Comprehensive statistics display for detailed performance tracking
- **Features**: Full statistics, latest kill/death information, session details
- **Layout**: Expanded view with additional information panels and enhanced styling

#### 4. Horizontal Mode
- **Purpose**: Wide-format display optimized for ultrawide monitors
- **Features**: All statistics arranged horizontally with separated sections
- **Layout**: Horizontal layout with statistics, session info, and latest events side-by-side

#### 5. Faded Mode
- **Purpose**: Notification-only mode that appears during kill/death events
- **Features**: Rich notifications with player profile images, organization info, weapon details
- **Layout**: Large notification panels that fade in/out during combat events

### Global Hotkey System

The overlay includes a sophisticated global hotkey system that works system-wide:

- **Default Hotkey**: `Ctrl+\`` (Ctrl + backtick)
- **Customizable**: Change to any key combination through the control panel
- **System-wide Detection**: Works even when Star Citizen is in focus
- **Windows API Integration**: Uses native Windows API for reliable hotkey detection
- **Examples**: `ctrl+\``, `alt+f1`, `ctrl+shift+h`, `f12`

### Themes and Customization

#### Available Themes
1. **Default**: Balanced color scheme with green accents
2. **Dark**: High-contrast dark theme for better visibility
3. **Neon**: Vibrant neon colors for a futuristic look

#### Customization Options
- **Opacity Control**: Adjust transparency from 10% to 100%
- **Position Control**: Drag and drop positioning or use preset positions
- **Animation Toggle**: Enable/disable visual effects and animations
- **Lock Position**: Prevent accidental movement of the overlay
- **Font Scaling**: Automatic scaling based on system DPI settings

### Kill/Death Notifications (Faded Mode)

When using Faded mode, the overlay shows rich notifications for combat events:

#### Kill Notifications
- **Header**: "YOU KILLED" with glowing green text
- **Victim Information**: Player name, organization, and tag
- **Combat Details**: Weapon used, location, and game mode
- **Profile Image**: Circular avatar with organization-themed border
- **Visual Effects**: Glow effects and smooth animations

#### Death Notifications
- **Header**: "YOU DIED" with glowing red text
- **Attacker Information**: Player name, organization, and tag
- **Combat Details**: Weapon used, location, and game mode
- **Profile Image**: Circular avatar with death-themed border
- **Visual Effects**: Red glow effects and fade-out animations

### Overlay Control Panel

Access the advanced control panel through the main application to configure:

#### Basic Controls
- **Enable/Disable Overlay**: Toggle overlay visibility
- **Lock Position**: Prevent accidental movement
- **Display Mode Selection**: Choose from 5 available modes

#### Appearance Settings
- **Theme Selection**: Choose from Default, Dark, or Neon themes
- **Opacity Slider**: Adjust transparency level
- **Animation Toggle**: Enable/disable visual effects

#### Position Controls
- **Preset Positions**: Top-left, top-right, bottom-left, bottom-right, center
- **Reset Position**: Return to default position
- **Manual Positioning**: Drag and drop the overlay to desired location

#### Global Hotkey Configuration
- **Enable/Disable Hotkeys**: Toggle global hotkey functionality
- **Current Hotkey Display**: Shows the active key combination
- **Hotkey Capture**: Record new key combinations
- **Examples and Guidelines**: Built-in help for valid key combinations

### Technical Implementation

#### Integration Points
- **Live Data Updates**: Real-time synchronization with main application
- **Kill/Death Events**: Automatic notification triggering from combat parser
- **Session Statistics**: Live updates of kills, deaths, K/D ratio, and session time
- **Ship Detection**: Automatic ship information updates
- **Game Mode Detection**: Real-time game mode display

#### Performance Features
- **Efficient Rendering**: Optimized drawing with minimal CPU usage
- **Memory Management**: Proper cleanup and resource management
- **Thread Safety**: Safe multi-threaded operation with the main application
- **Configuration Persistence**: Automatic saving of user preferences

### Setup and Usage

#### Installation
The overlay system is included with SCTool Tracker and requires no additional setup. It's automatically available when you install the main application.

#### First-Time Setup
1. **Launch SCTool Tracker**: Start the main application
2. **Open Control Panel**: Access overlay settings through the main interface
3. **Enable Overlay**: Check "Enable Game Overlay" in the control panel
4. **Choose Display Mode**: Select your preferred mode from the dropdown
5. **Configure Hotkey**: Set up your preferred hotkey combination
6. **Position Overlay**: Drag to your desired screen location

#### Daily Usage
1. **Toggle with Hotkey**: Use your configured hotkey to show/hide the overlay
2. **Cycle Modes**: Click the mode button on the overlay to cycle through display modes
3. **Adjust Opacity**: Use Ctrl + Mouse wheel while hovering over the overlay
4. **Reposition**: Drag the overlay to move it (when not locked)

### Troubleshooting

#### Common Issues
- **Overlay Not Showing**: Check if overlay is enabled in control panel
- **Hotkey Not Working**: Verify hotkey is enabled and combination is valid
- **Performance Issues**: Disable animations if experiencing frame rate drops
- **Positioning Problems**: Use reset position button in control panel
- **Display Issues**: Try different themes or adjust opacity settings

#### Advanced Solutions
- **Multiple Monitors**: Overlay supports multi-monitor setups
- **High DPI Displays**: Automatic scaling for 4K and high-DPI screens
- **Game Compatibility**: Works with all Star Citizen game modes
- **Antivirus Conflicts**: Add SCTool to antivirus exclusions if hotkeys don't work

## Button Automation System

SCTool Tracker includes a powerful **Button Automation System** that allows you to automatically execute custom key sequences when you get a kill in Star Citizen. This feature is perfect for streamers who want to trigger effects, activate StreamDeck actions, or perform any automated tasks based on kill events.

### Features

- **Custom Key Sequences**: Define any combination of keys and modifiers to be pressed automatically
- **Multiple Sequences**: Configure multiple button sequences with individual enable/disable controls
- **Configurable Delays**: Set delays before execution and between key presses for precise timing
- **Debounce Protection**: Built-in protection against rapid-fire executions to prevent system overload
- **Sequence Management**: Easy-to-use interface for adding, editing, and removing button sequences
- **Real-time Testing**: Test your sequences immediately to ensure they work as expected

### Configuration Options

#### Timing Controls
- **Press Delay**: Set a delay (in seconds) before any buttons are pressed after a kill event
- **Sequence Delay**: Configure the delay (in milliseconds) between individual key presses in a sequence
- **Hold Duration**: Set how long each key is held down (in milliseconds)
- **Debounce Time**: Prevent rapid executions with configurable debounce timing per sequence

#### Key Sequence Format

Button sequences use a simple, intuitive format:

**Single Keys**: `f1`, `space`, `enter`, `a`, `1`

**Key Combinations**: `ctrl+c`, `alt+f4`, `ctrl+shift+s`

**Multiple Actions**: `f1, ctrl+c, space, enter` (comma-separated for multiple actions)

**Supported Keys**:
- **Letters**: a-z
- **Numbers**: 0-9, numpad0-numpad9
- **Function Keys**: f1-f12
- **Modifiers**: ctrl, alt, shift, win
- **Special Keys**: space, enter, tab, esc, backspace, delete
- **Arrow Keys**: up, down, left, right
- **Other Keys**: home, end, pageup, pagedown, insert, and many more

### Usage Examples

#### Streaming Applications
- **OBS Scene Switch**: `f1` - Switch to a "Kill Cam" scene
- **Sound Effect**: `ctrl+f1` - Trigger a custom sound effect hotkey
- **StreamDeck Action**: `f9` - Activate a StreamDeck macro for kill celebrations

#### Game Enhancements  
- **Screenshot**: `printscreen` - Automatically capture screenshots of kills
- **Highlight Recording**: `alt+f9` - Start/stop highlight recording (NVIDIA ShadowPlay)
- **Communication**: `enter, g, g, enter` - Quick "gg" in game chat

#### Advanced Sequences
- **Multi-step Actions**: `f1, ctrl+shift+r, space, f2` - Complex multi-step automations
- **Delayed Actions**: Configure press delays to time actions perfectly with game events

### Setup Instructions

#### Basic Setup
1. **Navigate to Button Automation**: Click "Button Automation" in the main application sidebar
2. **Enable Automation**: Check "Enable Button Automation" to activate the system
3. **Add Sequence**: Click "Add New Sequence" to create your first automation
4. **Configure Sequence**: 
   - Enter a descriptive name for your sequence
   - Define your key sequence using the format guide
   - Test the sequence to ensure it works correctly
5. **Adjust Timing**: Fine-tune delays and timing settings as needed

#### Advanced Configuration
1. **Timing Optimization**: 
   - Start with default timing settings
   - Adjust **Press Delay** if you need time between the kill and automation
   - Modify **Sequence Delay** for faster or slower key presses
   - Set **Hold Duration** based on target application requirements

2. **Multiple Sequences**:
   - Create separate sequences for different purposes
   - Use descriptive names like "OBS Scene Switch", "Sound Effect", "StreamDeck Macro"
   - Enable/disable individual sequences as needed

3. **Testing and Debugging**:
   - Use the built-in test function to verify sequences work correctly
   - Monitor the application logs for button automation events
   - Test with your target applications to ensure proper integration

### Integration with Other Applications

#### OBS Studio
- Map function keys to scene transitions, source visibility, or recording controls
- Example: `f1` for "Kill Cam" scene, `f2` for normal gameplay scene

#### StreamDeck
- Configure StreamDeck to respond to specific hotkeys triggered by kill events
- Create complex multi-step automations triggered by simple key sequences

#### Game Overlays
- Integrate with game overlay software that responds to hotkey inputs
- Trigger visual effects, counters, or notifications synchronized with kills

#### Communication Tools
- Send quick messages in Discord, TeamSpeak, or game chat
- Example: `ctrl+shift+d, k, i, l, l, enter` for Discord quick message

### Security and Performance

#### Safety Features
- **Debounce Protection**: Prevents system overload from rapid kill events
- **Validation**: All key sequences are validated before execution
- **Error Handling**: Robust error handling prevents system instability
- **Resource Management**: Efficient execution with minimal system impact

#### Performance Considerations
- Button automation uses minimal CPU and memory resources
- Sequences execute in separate threads to avoid blocking the main application
- Built-in rate limiting prevents excessive system calls
- Automatic cleanup of completed automation tasks

### Troubleshooting

#### Common Issues
- **Sequences Not Executing**: Verify Button Automation is enabled and sequences are active
- **Wrong Keys Pressed**: Check key sequence format and test individual keys
- **Timing Issues**: Adjust sequence delay and hold duration settings
- **Application Not Responding**: Increase press delay or reduce sequence complexity

#### Advanced Solutions
- **Antivirus Interference**: Add SCTool to antivirus exclusions if key presses are blocked
- **Game Focus Issues**: Ensure target application accepts background key input
- **Complex Sequences**: Break down complex sequences into simpler, more reliable steps
- **Debugging**: Enable debug logging to trace sequence execution and identify issues

## Technical Architecture

The SCTool Tracker is built with a modular architecture consisting of several key components:

### Core Components

1. **Main Application (Kill_main.py)**: Entry point that initializes the GUI and monitoring systems
2. **GUI Interface (Kill_form.py)**: PyQt5-based interface that displays kill/death events and provides user controls
3. **Log Monitoring (Kill_thread.py)**: Background threads that monitor the game log file in real-time
4. **Event Parser (kill_parser.py)**: Specialized parser that extracts combat data from log entries
5. **Event Formatters (Registered_kill.py, Death_kill.py)**: Format extracted data into visual HTML displays
6. **Twitch Integration (twitch_integration.py)**: Handles Twitch authentication, chat messaging, and clip creation
7. **Game Overlay System (overlay.py)**: Advanced overlay system with 5 display modes, global hotkeys, and real-time statistics
8. **Profile System (fetch.py)**: Retrieves player profiles and avatar images from RSI website
9. **Button Automation (kill_clip.py)**: Automated key sequence execution system for kill events
10. **Responsive UI (responsive_ui.py)**: Handles high-DPI display scaling and responsive interface elements
11. **Utility Functions (utlity.py)**: Common utilities and helper functions for UI and configuration

### Data Flow

1. TailThread monitors the Game.log file for new entries
2. When a combat event is detected, the log line is parsed using regular expressions
3. Extracted data is formatted into HTML and displayed in the application
4. Combat events trigger overlay notifications and statistics updates in real-time
5. Player profile images are fetched from the RSI website for both the user and victims
6. If API integration is enabled, the data is sent to the SCTool API
7. Local statistics are updated and displayed in both the session panel and overlay
8. If Twitch integration is enabled, kill events can trigger clip creation and chat messages
9. If Button Automation is enabled, configured key sequences are executed after kill events
10. Overlay system updates live statistics and shows rich notifications in faded mode
11. Responsive UI system adjusts the interface based on screen resolution and DPI
12. All events and errors are logged for debugging and troubleshooting purposes

### File Structure

- **Kill_main.py**: Main entry point of the application
- **Kill_form.py**: Main GUI implementation and application logic
- **Kill_thread.py**: Background monitoring threads and API communication
- **kill_parser.py**: Log parsing and data extraction utilities
- **overlay.py**: Advanced game overlay system with multiple display modes and global hotkey support
- **overlays/**: Directory containing specialized overlay components (minimal, compact, detailed, horizontal, faded)
- **kill_clip.py**: Button automation system and clip creation functionality
- **Registered_kill.py**: Formats kill events for display
- **Death_kill.py**: Formats death events for display
- **twitch_integration.py**: Twitch API integration for clips and chat
- **fetch.py**: Functions for fetching profile data and images from RSI website
- **responsive_ui.py**: High-DPI support and responsive interface scaling
- **utlity.py**: Utility functions, UI helpers, and configuration management
- **README.md**: Comprehensive documentation
- **config.json**: User configuration storage
- **ships.json**: Ship database and recognition data
- **twitch_config.json**: Twitch integration settings and authentication tokens
- **button_automation_config.json**: Button automation sequences and timing configuration
- **overlay_config.json**: Game overlay system configuration and preferences
- **requirements.txt**: Python package dependencies
- **kill.wav**: Default kill sound notification file
- **avatar_default_big.jpg**: Default profile image fallback

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

The tracker offers comprehensive Twitch integration with advanced configuration options:

#### Authentication and Connection
1. **OAuth Authentication**: Secure OAuth authentication flow for connecting to Twitch
2. **Auto-Connect**: Option to automatically connect to Twitch when the application starts
3. **Connection Status**: Real-time connection status indicator in the main interface
4. **Reconnection**: Automatic reconnection handling for network interruptions

#### Clip Creation Features
1. **Automatic Clip Creation**: Creates clips automatically when you get a kill
2. **Configurable Delay**: Set clip creation delay from 0-60 seconds after kill events
3. **Clip Grouping**: Groups multiple kills within a time window into single clips
4. **API Integration**: Clip URLs are automatically sent back to the SCTool API for statistics
5. **Error Handling**: Robust error handling for Twitch API limitations and network issues

#### Chat Integration
1. **Kill Notifications**: Automatically posts kill messages to your Twitch chat
2. **Custom Message Templates**: Configurable message formats with kill details
3. **Victim Information**: Include victim name, weapon, location, and other details
4. **Rate Limiting**: Built-in rate limiting to comply with Twitch chat restrictions

#### Advanced Configuration
- **Channel Setup**: Automatic channel detection and configuration
- **Scope Management**: Proper OAuth scope handling for clips and chat permissions
- **Token Management**: Secure token storage and automatic refresh handling
- **Callback Server**: Local callback server for OAuth authentication flow

#### Configuration Files
- **twitch_config.json**: Stores authentication tokens and user preferences
- **Clip Timing**: Configurable clip delay and grouping windows
- **Chat Templates**: Customizable message templates for different kill types

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
- **Overlay Not Appearing**: Verify overlay is enabled in the control panel and check hotkey configuration
- **Global Hotkey Not Working**: Ensure hotkey is enabled, try different key combinations, or add SCTool to antivirus exclusions
- **Overlay Performance Issues**: Disable animations in the overlay control panel for better performance

## Data Storage

The application stores configuration and data in the following locations:

- **Configuration**: `%APPDATA%\SCTool_Tracker\config.json`
- **Overlay Configuration**: `%APPDATA%\Roaming\SCTool_Tracker\overlay_config.json`
- **Button Automation**: `button_automation_config.json` in the application directory
- **Local Kill Cache**: `%APPDATA%\SCTool_Tracker\logged_kills.json`
- **Application Logs**: `%APPDATA%\SCTool_Tracker\kill_logger.log`
- **Updates**: `%APPDATA%\SCTool_Tracker\Updates\`
- **Twitch Settings**: `twitch_config.json` in the application directory
- **Ship Database**: `ships.json` in the application directory
- **Sound Files**: `kill.wav` in the application directory
- **Default Assets**: `avatar_default_big.jpg` and other default resources
- **Profile Images**: Fetched at runtime from RSI website and cached temporarily

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
- Discord: Join our community server at [discord.gg/starcitizentool](https://discord.gg/starcitizentool)
- YouTube: Watch tutorials at [youtube.com/starcitizentool](https://youtube.com/starcitizentool)