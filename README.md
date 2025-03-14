# SCTool-Tracker

Sending data to the api

Required:
- victim_name
- timestamp
- player_name

Optional:
- victim_engagement
- attacker_engagement
- clip_url
- game_mode (must be one of the supported modes)

You can also send the complete log line using the field log_line. The log line must be in the expected format so that the API can parse and extract the necessary fields. Optionally, you can also include game_mode and clip_url with the log line payload.

Build the Application

Use the provided spec file (Kill_main.spec) to generate the executable:

run - pyinstaller Kill_main.spec
 
This will generate your application executable based on the specifications defined in Kill_main.spec. The executable will be located in the dist folder created by PyInstaller.
