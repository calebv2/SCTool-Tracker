# SCTool Tracker

## Video instructions

`https://www.youtube.com/watch?v=d8SwnmVPuGI`

## Overview

SCTool Tracker is an advanced application for Star Citizen that monitors the game's log file to track and record player kills and deaths. This tool provides real-time notifications about combat events and sends this data to the SCTool API to maintain your combat statistics. The current version is 5.8.

### Key Features at a Glance

- **Real-time Combat Tracking**: Monitor kills and deaths as they happen in-game
- **Advanced Game Overlay**: 6 different overlay modes with global hotkey support
- **Multi-language Support**: Full internationalization with 8 supported languages
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
- PyInstaller 5.0.0+ (if building from source)

### Installation

#### Recommended Method (Installer)
1. Download the latest release (v5.8) from [starcitizentool.com/download-sctool](https://starcitizentool.com/download-sctool)
2. Run the installer (`SCTool_Killfeed_5.8_Setup.exe`)
3. Follow the installation wizard instructions
4. Launch SCTool Tracker from your desktop or start menu

#### Manual Installation (Standalone)
1. Download the standalone executable from the releases page
2. Extract the files to a location of your choice (e.g., `C:\Program Files\SCTool Tracker\`)
3. Run `Kill_main.exe` to start the application

#### Installation from Source
If you prefer to run SCTool Tracker from source code or want to contribute to development:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/calebv2/SCTool-Tracker.git
   cd SCTool-Tracker
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run from Source**:
   ```bash
   python Kill_main.py
   ```

4. **Build Executable (Optional)**:
   ```bash
   # Build standalone executable
   pyinstaller --onefile --icon=chris2.ico --name=Kill_main Kill_main.py
   
   # Build installer (requires Inno Setup)
   # Use the included SCTool.iss script with Inno Setup Compiler
   ```

#### Dependencies Installation
The project includes a `requirements.txt` file with all necessary dependencies:

```bash
# Core application dependencies
PyQt5>=5.15.0          # GUI framework
requests>=2.25.0       # HTTP requests for API integration
beautifulsoup4>=4.9.0  # HTML parsing for profile fetching
packaging>=20.0        # Version management utilities
pyinstaller>=5.0.0     # Executable building (development only)
```

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
- **Multi-language Interface**: Complete internationalization support with real-time language switching

## Multi-language Support

SCTool Tracker includes internationalization support, allowing you to use the application in your preferred language with full interface translation.

### Supported Languages

The application currently supports **8 languages** with complete interface translations:

1. **English** (en) - Default language
2. **German** (de) - Deutsch
3. **Spanish** (es) - Español
4. **French** (fr) - Français
5. **Italian** (it) - Italiano
6. **Japanese** (ja) - 日本語
7. **Russian** (ru) - Русский
8. **Chinese (Simplified)** (zh-cn) - 简体中文

### Language Features

- **Complete Interface Translation**: All UI elements, menus, buttons, labels, and messages are fully translated
- **Real-time Language Switching**: Change languages instantly without restarting the application
- **Persistent Language Preference**: Your selected language is automatically saved and restored
- **Overlay Translation**: Game overlay system supports all languages with proper text rendering
- **Context-aware Translations**: Smart translation system that considers context for better accuracy
- **Automatic Language Detection**: Can detect system language on first launch

### Language Configuration

#### Changing Language
1. **Navigate to Settings**: Open the main application and go to "Killfeed Settings"
2. **Language Selector**: Find the "Language" dropdown in the Application Preferences section
3. **Select Language**: Choose your preferred language from the dropdown menu
4. **Instant Update**: The interface will immediately update to the selected language
5. **Automatic Save**: Your language preference is automatically saved for future sessions

#### Language Selector Features
- **Visual Language Names**: Languages are displayed in both English and their native script
- **Flag Icons**: Visual language identification with country/region flags
- **Search Functionality**: Quickly find languages in the dropdown list
- **Keyboard Navigation**: Full keyboard support for language selection

### Technical Implementation

#### Translation System Architecture
- **Language Manager**: Centralized translation management with caching and optimization
- **Translation Files**: JSON-based translation files located in the `languages/` directory
- **Dynamic Loading**: Translation files are loaded dynamically and cached for performance
- **Fallback System**: Automatic fallback to English if translations are missing
- **Memory Optimization**: Efficient memory usage with smart caching strategies

#### Translation Coverage
- **UI Elements**: All buttons, labels, menus, and interface text
- **Error Messages**: Complete error and status message translations
- **Tooltips and Help Text**: Help system translation
- **Overlay System**: Full overlay interface translation including all display modes
- **Settings and Configuration**: All configuration options and settings descriptions
- **Notification Messages**: Kill/death notifications and system messages

#### Developer Features
- **Translation Validation**: Built-in validation system to ensure translation completeness
- **Debug Mode**: Advanced debugging tools for translation issues
- **Hot Reloading**: Development support for real-time translation updates
- **Missing Translation Detection**: Automatic detection and logging of missing translations

### Troubleshooting Language Issues

#### Common Problems
- **Language Not Changing**: Restart the application if language changes don't take effect immediately
- **Partial Translation**: Some elements may show in English - this indicates missing translations
- **Font Issues**: Some languages may require system font support for proper character display
- **Overlay Text Issues**: Ensure graphics drivers support Unicode text rendering

#### Advanced Solutions
- **Manual Language Reset**: Delete the language preference in the configuration file to reset to English
- **Translation Cache**: Clear application data to refresh translation cache
- **Font Installation**: Install appropriate fonts for languages with special character sets
- **System Locale**: Ensure your system supports the selected language's character encoding

## Game Overlay System

SCTool Tracker includes a powerful **Game Overlay System** that provides real-time statistics directly on top of Star Citizen while you play. This overlay system offers multiple display modes, customizable themes, and advanced features for enhanced gameplay experience.

### Overlay Features

- **6 Display Modes**: Choose from Minimal, Compact, Detailed, Horizontal, Faded notification, and Simple Text modes
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

#### 6. Simple Text Mode
- **Purpose**: Lightweight text-only display with minimal system impact
- **Features**: Basic kill/death counters in plain text format for maximum performance
- **Layout**: Clean, simple text display ideal for streaming overlays or low-spec systems

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
 - **Custom Sound Files**: Support for .wav, .mp3, and .ogg audio formats (you can add more formats in Settings — e.g. m4a, flac)
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
   - Supported formats: configurable in Settings (default: .wav, .mp3, .ogg)
4. **Adjust Volume**: Use the volume slider to set your preferred audio level
5. **Test Sound**: Click the test button to preview your sound selection

#### Death Sound Setup
1. **Enable Death Sound**: Check the "Play sound on death" checkbox in settings
2. **Select Death Audio File**: 
   - Use the default `death.wav` file (included)
   - Browse for your custom death sound file using the "Browse" button
   - Supported formats: configurable in Settings (default: .wav, .mp3, .ogg)
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

## API Integration and Combat Tracking System

The SCTool Tracker integrates with the SCTool API to send combat data for statistics tracking. This section details the exact payload structures and API specifications.

### Combat Event Processing

#### Kill vs Death Payload Tracking

The system sends **two different payload types** to the API:

1. **Kill Payloads** (sent to `/api/v1/kills`): What YOU did - tracking your kills
2. **Death Payloads** (sent to `/api/v1/deaths`): What happened to you - tracking your deaths

Only verified kills and deaths are sent to the API. Local copies of all events are saved regardless of API integration settings.

#### Ship State Tracking

The tracker maintains an `is_in_ship` state that affects how kills are classified:

**Ship Entry Event** (when entering a ship):
- Sets `current_attacker_ship` to the detected ship name
- Sets `is_in_ship = True`

**Ship Exit Event** (when exiting a ship):
- Sets `current_attacker_ship = "No Ship"`
- Sets `is_in_ship = False`

**Player Death Event**:
- Resets `current_attacker_ship = "No Ship"`
- Sets `is_in_ship = False`

**Mid-Session Startup**:
- The `reconstruct_ship_history()` method scans the entire log file on startup
- Identifies the player's current ship state before live monitoring begins
- Properly sets both `current_attacker_ship` and `is_in_ship` flags

### Kill Payload Specifications

**Endpoint**: `POST https://starcitizentool.com/api/v1/kills`

#### Kill Payload Structure

```json
{
    "log_line": "<2025-10-18T14:03:40.679Z> [Notice] <Actor Death> CActor::Kill: 'victim' [...] killed by 'attacker' [...] using 'weapon' [...] with damage type 'type' [...]",
    "game_mode": "PU",
    "killer_ship": "AEGS Vanguard or empty string",
    "weapon": "Ship Weapon or personal weapon name",
    "method": "Vehicle destruction OR Player destruction"
}
```

**Optional Fields**:
```json
{
    "clip_url": "Valid URL or null",
    "handle": "Player handle or null"
}
```

#### Kill Payload Field Reference

| Field | Type | Always? | Description |
|-------|------|---------|-------------|
| `log_line` | string | ✅ Yes | Full Star Citizen game log line |
| `game_mode` | string | ✅ Yes | Current game mode (PU, Squadron Battle, etc.) |
| `killer_ship` | string | ❌ No | **Removed if empty**. Present only in ship-based kills. Absent in on-foot kills. |
| `weapon` | string | ✅ Yes | Formatted weapon name. "Ship Weapon" if using ship weapons, otherwise personal weapon name. |
| `method` | string | ✅ Yes | "Vehicle destruction" (ship destroyed) or "Player destruction" (player killed) |
| `clip_url` | string | ❌ No | Valid Twitch clip URL if created |
| `handle` | string | ❌ No | Player handle for additional context |

#### Kill Scenarios and Payload Examples

##### Scenario 1: Ship vs Ship Combat
```json
{
    "log_line": "<2025-10-18T14:03:40.679Z> [Notice] <Actor Death> CActor::Kill: 'EnemyPilot' [201968593176] in zone 'pyro4' killed by 'UNIBaller69' [202153876664] using 'GLSN_Shiv_Weapon_S1_6766499376235' [Class GLSN_Shiv_Weapon_S1] with damage type 'Bullet' [...]",
    "game_mode": "PU",
    "killer_ship": "GLSN Shiv",
    "weapon": "Ship Weapon",
    "method": "Player destruction"
}
```
**Engagement Display**: "GLSN Shiv using Ship Weapon"

##### Scenario 2: Player vs Player Combat (On Foot)
```json
{
    "log_line": "<2025-10-18T14:03:40.679Z> [Notice] <Actor Death> CActor::Kill: 'EnemyPlayer' [201968593176] in zone 'pyro4' killed by 'UNIBaller69' [202153876664] using 'P4_AR_6766499376235' [Class P4_AR] with damage type 'Bullet' [...]",
    "game_mode": "PU",
    "weapon": "P4-AR",
    "method": "Player destruction"
}
```
**Note**: `killer_ship` is **NOT included** in JSON (player on foot = no ship)
**Engagement Display**: "P4-AR"

##### Scenario 3: Ship vs Player On Ground
```json
{
    "log_line": "<2025-10-18T14:03:40.679Z> [Notice] <Actor Death> CActor::Kill: 'GroundPlayer' [201968593176] in zone 'pyro4' killed by 'UNIBaller69' [202153876664] using 'AEGS_Vanguard_Weapon_S1_6766499376235' [Class AEGS_Vanguard_Weapon_S1] with damage type 'Energy' [...]",
    "game_mode": "PU",
    "killer_ship": "AEGS Vanguard",
    "weapon": "Ship Weapon",
    "method": "Player destruction"
}
```
**Engagement Display**: "AEGS Vanguard using Ship Weapon"

##### Scenario 4: Ground Player Destroys Ship
```json
{
    "log_line": "<2025-10-18T14:03:40.679Z> [Notice] <Actor Death> CActor::Kill: 'ShipPilot' [201968593176] in zone 'pyro4' killed by 'UNIBaller69' [202153876664] using 'MXOX_NeutronRepeater_S3_6766499376235' [Class MXOX_NeutronRepeater_S3] with damage type 'vehicledestruction' [...]",
    "game_mode": "PU",
    "weapon": "MXOX Neutron Repeater S3",
    "method": "Vehicle destruction"
}
```
**Note**: `killer_ship` is **NOT included** (player on foot)
**Engagement Display**: "MXOX Neutron Repeater S3"

#### Combat Outcome Matrix

| Kill Type | killer_ship | weapon | method | is_in_ship | Engagement Example |
|-----------|-------------|--------|--------|------------|-------------------|
| Ship destroys player | ✅ Present | "Ship Weapon" | "Player destruction" | True | "AEGS Sabre using Ship Weapon" |
| Ship destroys ship | ✅ Present | "Ship Weapon" | "Vehicle destruction" | True | "AEGS Sabre using Ship Weapon" |
| Player (ground) kills player (ground) | ❌ Removed | Personal weapon | "Player destruction" | False | "P4-AR Rifle" |
| Player (ground) destroys ship | ❌ Removed | Weapon name | "Vehicle destruction" | False | "MXOX Neutron Repeater S3" |

### Death Payload Specifications

**Endpoint**: `POST https://starcitizentool.com/api/v1/deaths`

#### Death Payload Structure

```json
{
    "log_line": "<2025-10-18T14:03:40.679Z> [Notice] <Actor Death> CActor::Kill: 'victim' [...] killed by 'attacker' [...] using 'weapon' [...] with damage type 'type' [...]",
    "game_mode": "PU",
    "victim_name": "UNIBaller69",
    "attacker_name": "EnemyPilot",
    "weapon": "Ship Weapon or personal weapon name",
    "damage_type": "Energy, Bullet, vehicledestruction, etc.",
    "location": "pyro4",
    "timestamp": "2025-10-18 14:03:40",
    "event_type": "death"
}
```

#### Death Payload Field Reference

| Field | Type | Always? | Description |
|-------|------|---------|-------------|
| `log_line` | string | ✅ Yes | Full game log line |
| `game_mode` | string | ✅ Yes | Current game mode |
| `victim_name` | string | ✅ Yes | Your character name |
| `attacker_name` | string | ✅ Yes | Who killed you |
| `weapon` | string | ✅ Yes | What killed you. "Ship Weapon" if hit by ship weapons. |
| `damage_type` | string | ✅ Yes | Type of damage (Energy, Bullet, vehicledestruction, etc.) |
| `location` | string | ✅ Yes | Zone where you died |
| `timestamp` | string | ✅ Yes | When you died (YYYY-MM-DD HH:MM:SS) |
| `event_type` | string | ✅ Yes | Always "death" |

#### Death Payload Examples

##### Death from Ship Pilot
```json
{
    "log_line": "<2025-10-18T14:03:40.679Z> [Notice] <Actor Death> CActor::Kill: 'UNIBaller69' [...] killed by 'EnemyPilot' [...] using 'GLSN_Shiv_Weapon_S1_6766499376235' [Class GLSN_Shiv_Weapon_S1] with damage type 'Energy' [...]",
    "game_mode": "PU",
    "victim_name": "UNIBaller69",
    "attacker_name": "EnemyPilot",
    "weapon": "Ship Weapon",
    "damage_type": "Energy",
    "location": "pyro4",
    "timestamp": "2025-10-18 14:03:40",
    "event_type": "death"
}
```

##### Death from Player On Ground
```json
{
    "log_line": "<2025-10-18T14:03:40.679Z> [Notice] <Actor Death> CActor::Kill: 'UNIBaller69' [...] killed by 'EnemyPlayer' [...] using 'FS9_Laser_Rifle_6766499376235' [Class FS9_Laser_Rifle] with damage type 'Energy' [...]",
    "game_mode": "PU",
    "victim_name": "UNIBaller69",
    "attacker_name": "EnemyPlayer",
    "weapon": "FS9 Laser Rifle",
    "damage_type": "Energy",
    "location": "pyro4",
    "timestamp": "2025-10-18 14:03:40",
    "event_type": "death"
}
```

##### Death from Ship Destruction
```json
{
    "log_line": "<2025-10-18T14:03:40.679Z> [Notice] <Actor Death> CActor::Kill: 'UNIBaller69' [...] killed by 'EnemyPlayer' [...] using 'MXOX_NeutronRepeater_S3_6766499376235' [Class MXOX_NeutronRepeater_S3] with damage type 'vehicledestruction' [...]",
    "game_mode": "PU",
    "victim_name": "UNIBaller69",
    "attacker_name": "EnemyPlayer",
    "weapon": "MXOX Neutron Repeater S3",
    "damage_type": "vehicledestruction",
    "location": "pyro4",
    "timestamp": "2025-10-18 14:03:40",
    "event_type": "death"
}
```

### API Client Specifications

This section defines the **exact** specifications that client applications must follow to successfully send data to the Dashboard API. Any deviation from these specifications will result in request rejection.

#### Base Requirements

**Authentication**
- **API Key**: Required in `X-API-Key` header
- **Client Identification**: Must identify as `kill_logger_client`
- **Version**: Must be exactly `5.8`

**HTTP Method**
- **Method**: `POST` only
- **Protocol**: HTTP/HTTPS

#### Required Headers (Exact Match)

```json
{
    "Content-Type": "application/json",
    "Accept": "application/json", 
    "X-API-Key": "[Your API Key]",
    "X-Client-ID": "kill_logger_client",
    "X-Client-Version": "5.8"
}
```

**Optional Headers (Allowed)**
```json
{
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
```

#### Field Validation Rules

**Kill Payload**
- **log_line**: Must match Star Citizen log format with timestamp pattern `<YYYY-MM-DDTHH:MM:SS.sssZ>`
- **game_mode**: Must be exactly one of: PU, Team Elimination, Gun Rush, Tonk Royale, Free Flight, Squadron Battle, Vehicle Kill Confirmed, FPS Kill Confirmed, Control, Duel, Unknown
- **killer_ship**: Empty string if no valid ship (e.g., on-foot kills). Removed from JSON if empty.
- **weapon**: Formatted weapon name from the game log
- **method**: Must be exactly "Vehicle destruction" or "Player destruction"

**Death Payload**
- **log_line**: Must match Star Citizen log format
- **game_mode**: Must be valid game mode
- **victim_name/attacker_name**: Alphanumeric with spaces/underscores/hyphens/dots allowed
- **weapon/damage_type/location**: Cannot be empty strings
- **timestamp**: Must be valid ISO timestamp format
- **event_type**: Must be exactly "death"

#### API Request Configuration

- **HTTP Method**: POST for all endpoints
- **Timeout**: 10 seconds
- **SSL Verification**: Enabled by default (configurable)
- **Retry Logic**: Up to 5 retries with exponential backoff (1s, 2s, 4s, 8s, 16s)
- **Threading**: Asynchronous requests using QThread to prevent UI blocking

#### API Response Handling

- **201 Created**: Kill/death logged successfully
- **200 OK**: Alternative success response
- **400-499**: Client error, no retry attempted
- **500+**: Server error, triggers retry logic
- **Duplicate Detection**: Server responds with "duplicate" message for already logged events

#### Error Response Format

When validation fails, you'll receive:
```json
{
    "error": "Request validation failed",
    "message": "Detailed error description",
    "code": "VALIDATION_ERROR"
}
```

#### Validation Behavior

**Request Acceptance**
- ✅ All required headers present with exact values
- ✅ Payload structure exactly matches specification
- ✅ All field validations pass
- ✅ Client ID is `kill_logger_client`
- ✅ Client version is exactly `5.8`
- ✅ Valid API key

**Request Rejection (HTTP 400)**
- ❌ Missing or incorrect headers
- ❌ Invalid payload structure  
- ❌ Field validation failures
- ❌ Unexpected fields in payload
- ❌ Wrong client ID or version

**Authentication Failures (HTTP 401)**
- ❌ Missing API key
- ❌ Invalid API key

#### Rate Limits

- **5000 requests per 60 seconds** (throttling)
- **1000 requests per minute** (rate limiting)

#### Security Notes

- Only requests matching this exact specification will be processed
- Any deviation results in immediate rejection
- All requests are logged for security monitoring
- Unexpected headers or fields are rejected
- Client version enforcement is strict

**Important**: This specification ensures absolute data consistency. Client applications must implement these requirements exactly to maintain API access.

## Building Your Own Tracker

If you want to build your own tracker that integrates with the SCTool API, follow these guidelines:

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
- **Current Version**: 5.8
- **Release Date**: Updated regularly with Star Citizen patches
- **Compatibility**: Star Citizen Live, PTU, and Arena Commander modes
- **Platform**: Windows 10/11 (64-bit recommended)

### License and Legal
SCTool Tracker is provided as-is for use with Star Citizen. This tool does not modify game files or provide any competitive advantage - it only reads available log data that the game generates during normal gameplay.