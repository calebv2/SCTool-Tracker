# Death_kill.py

def format_death_kill(log_line: str, data: dict, registered_user: str, timestamp: str, last_game_mode: str):
    from urllib.parse import quote
    from Kill_form import fetch_player_details, fetch_victim_image_base64
    from kill_parser import KillParser

    attacker = data.get('attacker', 'Unknown')
    zone = data.get('zone', 'Unknown')
    weapon = data.get('weapon', 'Unknown')
    formatted_zone = KillParser.format_zone(zone)
    formatted_weapon = KillParser.format_weapon(weapon)
    details = fetch_player_details(attacker)
    attacker_image_data_uri = fetch_victim_image_base64(attacker)
    attacker_profile_url = f"https://robertsspaceindustries.com/citizens/{quote(attacker)}"
    attacker_link = f'<a href="{attacker_profile_url}" style="color:#f04747; text-decoration:none;">{attacker}</a>'

    readout = f"""
<html>
<body>
    <table width="600" cellspacing="0" cellpadding="15"
           style="background-color:#121212; font-family:Arial, sans-serif;
                  color:#e0e0e0; box-shadow: 0 0 15px 5px #f04747, 0 0 25px 10px rgba(240, 71, 71, 0.7); 
                  border-radius: 8px; margin-bottom: 10px;">
        <tr>
            <td colspan="2" style="border-bottom: 1px solid #333333; padding-bottom: 8px;">
                <div style="font-size:28px; font-weight:bold; color: #f04747; text-shadow: 0 0 5px rgba(240, 71, 71, 0.7);">YOU DIED</div>
            </td>
        </tr>
        <tr>
            <td style="vertical-align:top; padding-top: 12px; width: 70%;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="background-color: rgba(0, 204, 255, 0.1); padding: 8px; border-radius: 4px;">
                            <p style="font-size:14px; margin:4px 0;"><b>Game Mode:</b> <span style="color: #00ccff; text-shadow: 0 0 2px rgba(0, 204, 255, 0.3);">{last_game_mode if last_game_mode else 'Unknown'}</span></p>
                            <p style="font-size:14px; margin:4px 0;"><b>Timestamp:</b> {timestamp}</p>
                        </td>
                    </tr>
                    <tr><td style="height: 8px;"></td></tr>
                    <tr>
                        <td style="background-color: rgba(240, 71, 71, 0.1); padding: 8px; border-radius: 4px;">
                            <p style="font-size:14px; margin:4px 0;"><b>Attacker:</b> {attacker_link}</p>
                            <p style="font-size:14px; margin:4px 0;">
                                <b>Organization:</b> {details.get('org_name', 'None')} (Tag: 
                                <a href="https://robertsspaceindustries.com/en/orgs/{details.get('org_tag', 'None')}" 
                                   style="color:#f04747; text-decoration:none;">{details.get('org_tag', 'None')}</a>)
                            </p>
                        </td>
                    </tr>
                    <tr><td style="height: 8px;"></td></tr>
                    <tr>
                        <td style="background-color: rgba(255, 204, 0, 0.1); padding: 8px; border-radius: 4px;">
                            <p style="font-size:14px; margin:4px 0;"><b>Location:</b> {formatted_zone}</p>
                            <p style="font-size:14px; margin:4px 0;"><b>Damage Type:</b> {formatted_weapon}</p>
                        </td>
                    </tr>
                </table>
            </td>
            <td style="vertical-align:top; text-align:right; padding-top: 12px; width: 30%;">
                <div style="border-radius: 50%; padding: 3px; box-shadow: 0 0 10px #f04747;">
                    <img src="{attacker_image_data_uri}" width="100" height="100"
                         style="object-fit:cover; border-radius: 50%;" alt="Profile Image">
                </div>
            </td>
        </tr>
    </table>
    <br>
</body>
</html>
"""
    return readout