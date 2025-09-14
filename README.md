# SCTool Tracker

## Video instructions

`https://www.youtube.com/watch?v=d8SwnmVPuGI`

## Overview

SCTool Tracker is an advanced application for Star Citizen that monitors the game's log file to track and record player kills and deaths. This tool provides real-time notifications about combat events and sends this data to the SCTool API to maintain your combat statistics. The current version is 5.4.

### Key Features at a Glance

- **Real-time Combat Tracking**: Monitor kills and deaths as they happen in-game
- **Advanced Game Overlay**: 5 different overlay modes with global hotkey support
- **Dual Sound Notifications**: Separate customizable audio alerts for kills and deaths
- **Twitch Integration**: Automatic clip creation and chat messaging
- **Button Automation**: Execute custom key sequences on kill events
- **Profile System**: Fetch player avatars and organization info from RSI website
- **System Tray Integration**: Minimize to tray with persistent monitoring
- **Auto-start Capability**: Launch automatically with Windows
- **High-DPI Support**: Responsive design for all screen resolutions

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

#### Recommended Method (Installer)
1. Download the latest release (v5.4) from [starcitizentool.com/download-sctool](https://starcitizentool.com/download-sctool)
2. Run the installer (`SCTool_Killfeed_5.4_Setup.exe`)
3. Follow the installation wizard instructions
4. Launch SCTool Tracker from your desktop or start menu

#### Manual Installation (Standalone)
1. Download the standalone executable from the releases page
2. Extract the files to a location of your choice (e.g., `C:\Program Files\SCTool Tracker\`)
3. Run `Kill_main.exe` to start the application

#### System Requirements
- **Operating System**: Windows 10 or later (64-bit recommended)
- **Memory**: 2 GB RAM minimum, 4 GB recommended
- **Storage**: 500 MB free disk space
- **Network**: Internet connection for API integration and profile fetching
- **Star Citizen**: Must be installed and have generated at least one Game.log file

### Configuration

#### Essential Setup
1. **API Key**: Enter your API key from starcitizentool.com in the provided field
2. **Game.log Path**: Select your Star Citizen Game.log file location (typically in `[Star Citizen Install]\LIVE\Game.log`)
3. **Player Name**: Enter your in-game character name for accurate kill attribution
4. **Killer Ship**: Select or enter your current ship for proper kill tracking

#### Optional Settings
- **Sound Settings**: Configure custom sound notifications for kills (supports .wav, .mp3, .ogg)
- **System Tray**: Enable minimize to tray functionality
- **Auto-start**: Launch SCTool automatically when Windows starts
- **UI Scaling**: Adjust interface scaling for high-DPI displays

## Features

- **Real-time Kill/Death Tracking**: Instantly see your combat events as they happen
- **API Integration**: Send your kills and deaths to the SCTool API for statistics tracking
- **Ship Detection**: Automatically detects your current ship
- **Sound Notifications**: Customizable audio alerts for kill and death events with independent volume controls
- **Missing Kill Detection**: Rescan your log files to find previously undetected kills
- **Game Mode Detection**: Automatically identifies Arena Commander, Persistent Universe, and other modes
- **Session Statistics**: Real-time tracking of kills, deaths, K/D ratio, and session duration
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
- **Advanced Control Panel**: Configuration interface with all overlay settings
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
- **Purpose**: Statistics display for detailed performance tracking
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

## Sound Notification System

SCTool Tracker includes a dual sound notification system that plays audio alerts for both kills and deaths in Star Citizen.

### Sound Features

- **Dual Sound Systems**: Separate customizable sound notifications for kills and deaths
- **Custom Sound Files**: Support for .wav, .mp3, and .ogg audio formats
- **Independent Volume Control**: Adjustable volume sliders from 0-100% for both kill and death sounds
- **File Browser**: Easy sound file selection through built-in file browser
- **Default Sounds**: Includes default `kill.wav` and `death.wav` files for immediate use
- **Real-time Testing**: Test your selected sound files before saving

### Configuration

#### Kill Sound Setup
1. **Navigate to Settings**: Go to the main settings page in SCTool Tracker
2. **Enable Kill Sound**: Check the "Play sound on kill" checkbox
3. **Select Audio File**: 
   - Use the default `kill.wav` file (included)
   - Browse for your custom sound file using the "Browse" button
   - Supported formats: .wav, .mp3, .ogg
4. **Adjust Volume**: Use the volume slider to set your preferred audio level
5. **Test Sound**: Click the test button to preview your sound selection

#### Death Sound Setup
1. **Enable Death Sound**: Check the "Play sound on death" checkbox in settings
2. **Select Death Audio File**: 
   - Use the default `death.wav` file (included)
   - Browse for your custom death sound file using the "Browse" button
   - Supported formats: .wav, .mp3, .ogg
3. **Adjust Death Volume**: Use the separate death volume slider to set your preferred audio level
4. **Test Death Sound**: Click the death sound test button to preview your selection

#### Sound File Recommendations
- **Duration**: Keep sounds short (1-3 seconds) to avoid overlapping with rapid events
- **Volume**: Choose sounds that are audible but not disruptive to gameplay
- **Format**: .wav files offer the best compatibility and performance
- **Quality**: Use high-quality audio files for best results
- **Differentiation**: Use distinctly different sounds for kills vs deaths to provide clear audio feedback

### Integration with Gameplay

The dual sound system is designed to enhance your gaming experience:

- **Immediate Feedback**: Audio confirmation of both successful kills and deaths
- **Event Differentiation**: Distinct sounds help you quickly identify kill vs death events
- **Customization**: Use sounds that match your playstyle or streaming setup
- **Performance**: Minimal impact on game performance
- **Reliability**: Consistent playback even during intense combat scenarios

### Troubleshooting Sound Issues

#### Common Problems
- **No Sound Playing**: Verify audio file paths and format compatibility
- **Volume Too Low/High**: Adjust the respective volume sliders in settings
- **Audio Conflicts**: Check for conflicts with other audio software
- **File Format Issues**: Convert audio files to .wav format if experiencing problems
- **One Sound Type Not Working**: Check that both kill and death sounds are enabled and configured separately

#### Advanced Solutions
- **Audio Drivers**: Ensure Windows audio drivers are up to date
- **Exclusive Mode**: Disable exclusive mode for audio devices if experiencing conflicts
- **Multiple Audio Devices**: Verify SCTool is using the correct audio output device
- **Antivirus Blocking**: Add audio files to antivirus exclusions if playback is blocked

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

The tracker offers Twitch integration with advanced configuration options:

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
   - Clip Updates: `https://starcitizentool.com/api/v1/kills/update-clip`

### Required Headers

The application sends the following headers with all API requests:

```json
{
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "X-API-Key": "YOUR_API_KEY",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "X-Client-ID": "kill_logger_client",
    "X-Client-Version": "5.7"
}
```

### Payload Structure

**Kill Event Payload:**

When a kill is detected and sent to the kills endpoint, the JSON payload structure is:

```json
{
    "log_line": "Full game log line with timestamp and kill details",
    "game_mode": "Mapped game mode (PU, Team Elimination, Elimination, Gun Rush, etc.)",
    "killer_ship": "Ship name if vehicle destruction, empty string if player destruction",
    "method": "Vehicle destruction or Player destruction"
}
```

**Death Event Payload:**

When a death is detected and sent to the deaths endpoint, the JSON payload structure is:

```json
{
    "log_line": "Full game log line with timestamp and death details",
    "game_mode": "Mapped game mode (PU, Team Elimination, Elimination, etc.)",
    "victim_name": "Player who died",
    "attacker_name": "Player who killed",
    "weapon": "Weapon used from log",
    "damage_type": "Damage type from log",
    "location": "Zone/location from log",
    "timestamp": "Full timestamp in YYYY-MM-DD HH:MM:SS format",
    "event_type": "death"
}
```

**Clip URL Update Payload:**

For updating existing kills with Twitch clip URLs via the update-clip endpoint:

```json
{
    "clip_url": "Twitch clip URL",
    "timestamp": "Kill timestamp", 
    "victim_name": "Victim name",
    "kill_id": "API kill ID if available"
}
```

### API Request Configuration

- **HTTP Method**: POST for all endpoints
- **Timeout**: 10 seconds
- **SSL Verification**: Enabled by default (configurable)
- **Retry Logic**: Up to 5 retries with exponential backoff (1s, 2s, 4s, 8s, 16s)
- **Threading**: Asynchronous requests using QThread to prevent UI blocking

### API Response Handling

- **201 Created**: Kill/death logged successfully
- **200 OK**: Alternative success response
- **400-499**: Client error, no retry attempted
- **500+**: Server error, triggers retry logic
- **Duplicate Detection**: Server responds with "duplicate" message for already logged events

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

### Common Issues and Solutions

#### Application Issues
- **Ship Not Detected**: Manually select your ship in the Killer Ship dropdown menu
- **Kills Not Showing**: Verify the path to your Game.log file is correct and the file has recent entries
- **API Connection Fails**: Check your network connection, verify your API key, and ensure starcitizentool.com is accessible
- **Application Crashes**: Check the `kill_logger.log` file in `%APPDATA%\SCTool_Tracker\` for error details
- **Missed Kills**: Use the "Find Missed Kills" feature to scan for unregistered kills in your log history

#### Overlay Issues  
- **Overlay Not Appearing**: Verify overlay is enabled in the control panel and check hotkey configuration
- **Global Hotkey Not Working**: Ensure hotkey is enabled, try different key combinations, or add SCTool to antivirus exclusions
- **Overlay Performance Issues**: Disable animations in the overlay control panel for better performance
- **Positioning Problems**: Use the reset position button in the overlay control panel
- **Display Issues on High-DPI**: Enable Windows display scaling compatibility mode

#### Integration Issues
- **Twitch Integration Issues**: Ensure your Twitch channel name is correct, verify OAuth authentication, and try reconnecting
- **Profile Images Not Loading**: Check your internet connection and RSI website availability
- **Button Automation Not Working**: Verify sequences are enabled, check key format, and test individual sequences

#### System Issues
- **Display Scaling Issues**: Enable high-DPI scaling in Windows for better UI rendering, or adjust scaling in application settings
- **Auto-start Not Working**: Run as administrator to set registry entries, or manually add to Windows startup folder
- **System Tray Issues**: Ensure system tray is enabled in Windows settings and notification area is accessible

### Advanced Troubleshooting

#### Log Analysis
1. Navigate to `%APPDATA%\SCTool_Tracker\`
2. Open `kill_logger.log` in a text editor
3. Look for ERROR or WARNING messages
4. Check timestamps around when issues occurred

#### Configuration Reset
1. Close SCTool Tracker completely
2. Navigate to `%APPDATA%\SCTool_Tracker\`
3. Backup then delete `config.json`
4. Restart the application (will create default config)

#### Network Diagnostics
1. Test API connectivity: `ping starcitizentool.com`
2. Check firewall settings for SCTool Tracker
3. Verify Windows network adapter settings
4. Test with different network connection if available

#### Performance Optimization
- **Reduce CPU Usage**: Disable unnecessary overlays and animations
- **Memory Management**: Restart application periodically for long gaming sessions
- **Disk Space**: Ensure adequate free space in `%APPDATA%` folder
- **Antivirus Exclusions**: Add SCTool directory to antivirus exclusions

## Data Storage and Configuration

The application stores configuration and data in the following locations:

### Configuration Files
- **Main Configuration**: `%APPDATA%\SCTool_Tracker\config.json` - Core application settings
- **Twitch Settings**: `twitch_config.json` in application directory - OAuth tokens and integration settings  
- **Button Automation**: `button_automation_config.json` in application directory - Key sequences and timing
- **Overlay Configuration**: Saved within main config.json - Display modes, themes, and positioning

### Data Storage
- **Local Kill Cache**: `%APPDATA%\SCTool_Tracker\logged_kills.json` - Cached kill/death events
- **Application Logs**: `%APPDATA%\SCTool_Tracker\kill_logger.log` - Debug and error logs
- **Updates**: `%APPDATA%\SCTool_Tracker\Updates\` - Downloaded update files

### Static Resources
- **Ship Database**: `ships.json` in application directory - Complete Star Citizen ship list
- **Sound Files**: `kill.wav` and `death.wav` in application directory - Default kill and death notification sounds
- **Default Assets**: `avatar_default_big.jpg` and icons in application directory
- **Profile Images**: Fetched at runtime from RSI website and cached temporarily in memory

### Configuration File Examples

#### Button Automation Config (`button_automation_config.json`)
```json
{
    "enabled": false,
    "button_sequences": [
        {
            "name": "StreamDeck Trigger",
            "key_sequence": "alt+shift+f10",
            "enabled": true
        }
    ],
    "press_delay_seconds": 0,
    "sequence_delay_ms": 100,
    "hold_duration_ms": 50,
    "debounce_ms": 500,
    "sequence_debounce_ms": 1000
}
```

#### Twitch Config (`twitch_config.json`)
```json
{
    "client_id": "your_twitch_client_id",
    "client_secret": "your_twitch_client_secret",
    "broadcaster_name": "your_twitch_username",
    "broadcaster_id": "",
    "access_token": "",
    "refresh_token": "",
    "token_expiry": null,
    "clip_delay_seconds": 10
}
```

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

## Contact and Support

### Official Resources
- **Website**: [starcitizentool.com](https://starcitizentool.com) - Download, documentation, and API registration
- **Discord**: Join our community server for support and discussions
- **YouTube**: Watch video tutorials and feature demonstrations

### Getting Help
1. **Check Documentation**: Review this README and the in-app help sections
2. **Search Discord**: Many common issues are discussed in our Discord community
3. **Check Logs**: Review the application logs in `%APPDATA%\SCTool_Tracker\kill_logger.log`
4. **Report Issues**: Use Discord or GitHub issues for bug reports with log files attached

### Version Information
- **Current Version**: 5.4
- **Release Date**: Updated regularly with Star Citizen patches
- **Compatibility**: Star Citizen Live, PTU, and Arena Commander modes
- **Platform**: Windows 10/11 (64-bit recommended)

### License and Legal
SCTool Tracker is provided as-is for use with Star Citizen. This tool does not modify game files or provide any competitive advantage - it only reads available log data that the game generates during normal gameplay.