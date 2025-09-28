# color_manager.py

import os
import json
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QColorDialog
from typing import Dict, Any

class ColorManager:
    """Manages custom colors for overlays with persistence"""
    
    def __init__(self):
        self.config_file = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "SCTool_Tracker", "custom_colors.json")
        self.custom_colors = self.load_custom_colors()
        
    def get_default_color_scheme(self) -> Dict[str, QColor]:
        """Get the default grey color scheme for custom theme"""
        return {
            'background': QColor(80, 80, 80, 180),
            'border': QColor(120, 120, 120, 200),
            'text_primary': QColor(220, 220, 220, 255),
            'text_secondary': QColor(180, 180, 180, 255),
            'accent': QColor(140, 140, 140, 255),
            'kill_color': QColor(160, 160, 160, 255),
            'death_color': QColor(100, 100, 100, 255),
            'info_color': QColor(130, 130, 130, 255)
        }
    
    def load_custom_colors(self) -> Dict[str, Any]:
        """Load custom color configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    colors = {}
                    for key, color_dict in data.items():
                        if isinstance(color_dict, dict) and 'r' in color_dict:
                            colors[key] = QColor(
                                color_dict['r'], 
                                color_dict['g'], 
                                color_dict['b'], 
                                color_dict.get('a', 255)
                            )
                        else:
                            colors[key] = QColor(color_dict)
                    
                    default_colors = self.get_default_color_scheme()
                    for key, default_color in default_colors.items():
                        if key not in colors:
                            colors[key] = default_color
                    
                    return colors
        except Exception as e:
            print(f"Error loading custom colors: {e}")

        return self.get_default_color_scheme()
    
    def save_custom_colors(self):
        """Save custom color configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            color_data = {}
            for key, color in self.custom_colors.items():
                color_data[key] = {
                    'r': color.red(),
                    'g': color.green(),
                    'b': color.blue(),
                    'a': color.alpha()
                }
            
            with open(self.config_file, 'w') as f:
                json.dump(color_data, f, indent=2)
        except Exception as e:
            print(f"Error saving custom colors: {e}")
    
    def get_color(self, color_name: str) -> QColor:
        """Get a specific color by name"""
        return self.custom_colors.get(color_name, self.get_default_color_scheme().get(color_name, QColor(255, 255, 255)))
    
    def set_color(self, color_name: str, color: QColor):
        """Set a custom color and save to file"""
        self.custom_colors[color_name] = color
        self.save_custom_colors()
    
    def get_all_colors(self) -> Dict[str, QColor]:
        """Get all custom colors"""
        return self.custom_colors.copy()
    
    def copy_theme_colors(self, theme_colors: Dict[str, QColor]):
        """Copy colors from a theme dictionary"""
        for key, color in theme_colors.items():
            self.custom_colors[key] = QColor(color)
        self.save_custom_colors()
    
    def get_color_names(self) -> list:
        """Get list of all available color names"""
        return list(self.custom_colors.keys())
    
    def get_color_display_names(self) -> Dict[str, str]:
        """Get human-readable display names for colors"""
        return {
            'background': 'Background',
            'border': 'Border',
            'text_primary': 'Primary Text',
            'text_secondary': 'Secondary Text',
            'accent': 'Accent Color',
            'kill_color': 'Kill Color',
            'death_color': 'Death Color',
            'info_color': 'Info Color'
        }

color_manager = ColorManager()
