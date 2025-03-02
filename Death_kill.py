# Death_kill.py

def format_death_kill(log_line: str, data: dict, registered_user: str, timestamp: str, last_game_mode: str):
    from urllib.parse import quote
    from Kill_form import fetch_player_details, fetch_victim_image_base64
    from kill_parser import KillParser

    attacker = data.get('attacker', 'Unknown')
    zone = data.get('zone', 'Unknown')
    damage_type = data.get('damage_type', 'Unknown')
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
    <table width="600" cellspacing="0" cellpadding="15" style="background-color:#121212; font-family:Arial, sans-serif; color:#e0e0e0; box-shadow: 0 0 15px 5px #f04747, 0 0 20px 10px #f04747;">
    <tr>
        <td style="vertical-align:top;">
        <div style="font-size:20px; font-weight:bold; margin-bottom:10px;">You were killed by:</div>
        <p style="font-size:14px; margin:4px 0;"><b>Attacker:</b> {attacker_link}</p>
        <p style="font-size:14px; margin:4px 0;"><b>Engagement Zone:</b> {formatted_zone}</p>
        <p style="font-size:14px; margin:4px 0;"><b>Damage Type:</b> {damage_type} using {formatted_weapon}</p>
        <p style="font-size:14px; margin:4px 0;"><b>Game Mode:</b> {last_game_mode if last_game_mode else 'Unknown'}</p>
        <p style="font-size:14px; margin:4px 0;"><b>Timestamp:</b> {timestamp}</p>
        <p style="font-size:14px; margin:4px 0;">
            <b>Organization:</b> {details.get('org_name', 'None')} (Tag: 
            <a href="https://robertsspaceindustries.com/en/orgs/{details.get('org_tag', 'None')}" style="color:#f04747; text-decoration:none;">{details.get('org_tag', 'None')}</a>)
        </p>
        </td>
        <td style="vertical-align:top; text-align:right;">
        <img src="{attacker_image_data_uri}" width="100" height="100" style="object-fit:cover;" alt="Profile Image">
        </td>
    </tr>
    </table>
    <br>
</body>
</html>
"""
    return readout
