# html_templates.py

from typing import Dict, Any
from language_manager import t

class KillEventTemplate:
    """Base template class for kill/death events matching faded overlay exactly"""
    
    @staticmethod
    def get_color_scheme() -> Dict[str, str]:
        """Get the exact color scheme from faded overlay (default theme)"""
        return {
            'background': 'rgba(0, 0, 0, 0.7)',
            'text_primary': '#ffffff',
            'text_secondary': '#c8c8c8',
            'accent': "#414141",
            'kill_color': "#ffffff",
            'death_color': '#f04747',
            'info_color': '#00ccff'
        }
    
    @staticmethod
    def get_base_styles() -> str:
        """Common CSS styles for all kill events"""
        return """
            body {
                margin: 0;
                padding: 0;
            }
            .newEntry {
                position: relative;
                display: inline-block;
                width: 100%;
            }
            .event-table {
                width: 100%;
                cellspacing: 0;
                cellpadding: 15px;
                background-color: #121212;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #e0e0e0;
                border-radius: 10px;
                margin-bottom: 15px;
                overflow: hidden;
            }
            .header-cell {
                background: linear-gradient(135deg, #151515, #0d0d0d);
                border-bottom: 1px solid #333333;
                padding: 12px 15px;
            }
            .header-title {
                font-size: 22px;
                font-weight: bold;
                text-shadow: 0 0 5px;
                display: flex;
                align-items: center;
            }
            .status-dot {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 10px;
                box-shadow: 0 0 5px;
            }
            .content-left {
                vertical-align: top;
                padding-top: 15px;
                width: 70%;
            }
            .content-right {
                vertical-align: top;
                text-align: right;
                padding-top: 15px;
                width: 30%;
            }
            .info-table {
                width: 100%;
                border-collapse: separate;
                border-spacing: 0 8px;
            }
            .info-card {
                padding: 12px;
                border-radius: 8px;
                border-left: 3px solid;
            }
            .info-text {
                font-size: 14px;
                margin: 4px 0;
            }
            .profile-container {
                border-radius: 50%;
                padding: 3px;
                box-shadow: 0 0 10px;
            }
            .profile-image-wrapper {
                position: relative;
                overflow: hidden;
                border-radius: 50%;
            }
            .profile-image {
                width: 110px;
                height: 110px;
                object-fit: cover;
                border-radius: 50%;
            }
            .profile-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                border-radius: 50%;
                box-shadow: inset 0 0 20px;
            }
            .link-style {
                text-decoration: none;
            }
        """

    @staticmethod
    def format_org_info(details: Dict[str, str]) -> str:
        """Format organization information consistently"""
        org_name = details.get('org_name', t('None'))
        org_tag = details.get('org_tag', t('None'))
        org_url = f"https://robertsspaceindustries.com/en/orgs/{org_tag}"
        
        return f"""{org_name} 
            <span style="color: #888888;">({t("Tag")}:</span>
            <a href="{org_url}" style="color: inherit; text-decoration: none;">
                {org_tag}
            </a><span style="color: #888888;">)</span>"""

class RegisteredKillTemplate(KillEventTemplate):
    """Template for registered kill events - QWebEngineView/QTextBrowser compatible"""
    
    @classmethod
    def render(cls, data: Dict[str, Any]) -> str:
        """Render kill notification for QWebEngineView (with fallback to QTextBrowser)"""
        colors = cls.get_color_scheme()
        org_name = data['details'].get('org_name', 'None')
        org_tag = data['details'].get('org_tag', 'None')
        
        org_section = ""
        if org_name != 'None' and org_name != 'Unknown':
            if org_tag != 'None' and org_tag != 'Unknown':
                org_section = f"""<div style="color: {colors['text_secondary']}; font-size: 16px; font-family: 'Consolas', monospace; margin: 2px 0;">{t('Organization')}: <a href="https://robertsspaceindustries.com/en/orgs/{org_tag}" style="color: {colors['text_secondary']}; text-decoration: none;" target="_blank">{org_name}</a></div>"""
                org_section += f"""<div style="color: {colors['accent']}; font-size: 14px; font-family: 'Consolas', monospace; margin: 2px 0;">{t('Tag')}: <a href="https://robertsspaceindustries.com/en/orgs/{org_tag}" style="color: {colors['accent']}; text-decoration: none;" target="_blank">[{org_tag}]</a></div>"""
            else:
                org_section = f"""<div style="color: {colors['text_secondary']}; font-size: 16px; font-family: 'Consolas', monospace; margin: 2px 0;">{t('Organization')}: {org_name}</div>"""
        else:
            org_section = f"""<div style="color: {colors['text_secondary']}; font-size: 16px; font-family: 'Consolas', monospace; margin: 2px 0;">{t('Organization')}: {t('Independent')}</div>"""
        
        return f"""
<div style="
    background: {colors['background']}; 
    border-left: 4px solid #ff4444; 
    border-radius: 8px; 
    padding: 15px; 
    margin: 5px;
">
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="vertical-align: top; padding-right: 15px;">
                <div style="color: {colors['kill_color']}; font-size: 24px; font-weight: bold; font-family: 'Consolas', monospace;">
                    {t("YOU KILLED")}
                </div>
                
                <div style="color: {colors['text_primary']}; font-size: 20px; font-weight: bold; font-family: 'Consolas', monospace; margin-top: 10px;">
                    <a href="https://robertsspaceindustries.com/en/citizens/{data['victim']}" style="color: {colors['text_primary']}; text-decoration: none;" target="_blank">
                        {data['victim'].upper()}
                    </a>
                </div>
                
                <div style="margin-top: 8px;">
                    {org_section}
                </div>
                
                <div style="margin-top: 10px;">
                    <div style="color: {colors['text_primary']}; font-size: 16px; font-family: 'Consolas', monospace; margin: 2px 0;">
                        {t('Weapon')}: {data['engagement']}
                    </div>
                    <div style="color: {colors['text_primary']}; font-size: 16px; font-family: 'Consolas', monospace; margin: 2px 0;">
                        {t('Location')}: {data['formatted_zone']}
                    </div>
                    <div style="color: {colors['info_color']}; font-size: 14px; font-family: 'Consolas', monospace; margin: 2px 0;">
                        {t('Mode')}: {data['game_mode']}
                    </div>
                </div>
            </td>
            <td style="width: 200px; text-align: right; vertical-align: middle;">
                <img src="{data['victim_image_data_uri']}" style="
                    width: 150%; 
                    height: 150%; 
                    max-width: 200px; 
                    max-height: 200px; 
                    object-fit: cover;
                    display: block;
                ">
            </td>
        </tr>
    </table>
</div>
"""


class DeathEventTemplate(KillEventTemplate):
    """Template for death events - QWebEngineView/QTextBrowser compatible"""
    
    @classmethod
    def render(cls, data: Dict[str, Any]) -> str:
        """Render death notification for QWebEngineView (with fallback to QTextBrowser)"""
        colors = cls.get_color_scheme()
        org_name = data['details'].get('org_name', 'None')
        org_tag = data['details'].get('org_tag', 'None')
        
        org_section = ""
        if org_name != 'None' and org_name != 'Unknown':
            if org_tag != 'None' and org_tag != 'Unknown':
                org_section = f"""<div style="color: {colors['text_secondary']}; font-size: 16px; font-family: 'Consolas', monospace; margin: 2px 0;">{t('Organization')}: <a href="https://robertsspaceindustries.com/en/orgs/{org_tag}" style="color: {colors['text_secondary']}; text-decoration: none;" target="_blank">{org_name}</a></div>"""
                org_section += f"""<div style="color: {colors['accent']}; font-size: 14px; font-family: 'Consolas', monospace; margin: 2px 0;">{t('Tag')}: <a href="https://robertsspaceindustries.com/en/orgs/{org_tag}" style="color: {colors['accent']}; text-decoration: none;" target="_blank">[{org_tag}]</a></div>"""
            else:
                org_section = f"""<div style="color: {colors['text_secondary']}; font-size: 16px; font-family: 'Consolas', monospace; margin: 2px 0;">{t('Organization')}: {org_name}</div>"""
        else:
            org_section = f"""<div style="color: {colors['text_secondary']}; font-size: 16px; font-family: 'Consolas', monospace; margin: 2px 0;">{t('Organization')}: {t('Independent')}</div>"""
        
        return f"""
<div style="
    background: {colors['background']}; 
    border-left: 4px solid #ff4444; 
    border-radius: 8px; 
    padding: 15px; 
    margin: 5px;
">
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="vertical-align: top; padding-right: 15px;">
                <div style="color: {colors['death_color']}; font-size: 24px; font-weight: bold; font-family: 'Consolas', monospace;">
                    {t("YOU DIED")}
                </div>
                
                <div style="color: {colors['text_primary']}; font-size: 20px; font-weight: bold; font-family: 'Consolas', monospace; margin-top: 10px;">
                    {t('KILLED BY')}: <a href="https://robertsspaceindustries.com/en/citizens/{data['attacker']}" style="color: {colors['text_primary']}; text-decoration: none;" target="_blank">{data['attacker'].upper()}</a>
                </div>
                
                <div style="margin-top: 8px;">
                    {org_section}
                </div>
                
                <div style="margin-top: 10px;">
                    <div style="color: {colors['text_primary']}; font-size: 16px; font-family: 'Consolas', monospace; margin: 2px 0;">
                        {t('Weapon')}: {data['formatted_weapon']}
                    </div>
                    <div style="color: {colors['text_primary']}; font-size: 16px; font-family: 'Consolas', monospace; margin: 2px 0;">
                        {t('Location')}: {data['formatted_zone']}
                    </div>
                    <div style="color: {colors['info_color']}; font-size: 14px; font-family: 'Consolas', monospace; margin: 2px 0;">
                        {t('Mode')}: {data['game_mode']}
                    </div>
                </div>
            </td>
            <td style="width: 200px; text-align: right; vertical-align: middle;">
                <img src="{data['attacker_image_data_uri']}" style="
                    width: 150%; 
                    height: 150%; 
                    max-width: 200px; 
                    max-height: 200px; 
                    object-fit: cover;
                    display: block;
                ">
            </td>
                    display: block;
                ">
            </td>
        </tr>
    </table>
</div>
"""