# overlay.py

import json
import os
import re
from datetime import datetime
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, 
    QCheckBox, QPushButton, QSlider, QComboBox, QSpinBox,
    QColorDialog, QGroupBox, QGridLayout, QTextEdit, QScrollArea,
    QApplication
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QLinearGradient, 
    QRadialGradient, QPixmap, QPainterPath, QFontMetrics
)

class GameOverlay(QWidget):
    """Overlay for Star Citizen"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_tracker = parent
        self.is_dragging = False
        self.drag_position = QPoint()
        self.resize_mode = False
        self.config_file = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "SCTool_Tracker", "overlay_config.json")
        self.config = self.load_config()
        
        self.live_update_timer = QTimer()
        self.live_update_timer.timeout.connect(self.update_live_data)
        self.live_update_timer.start(1000)

        self.is_enabled = self.config.get('enabled', False)
        self.is_visible = False
        self.display_mode = self.config.get('display_mode', 'compact')
        self.opacity_level = self.config.get('opacity', 0.9)
        self.show_animations = self.config.get('animations', True)
        self.is_locked = self.config.get('locked', False)
        
        self.kills = 0
        self.deaths = 0
        self.session_time = "00:00"
        self.ship = "Unknown"
        self.game_mode = "Unknown"
        self.last_kill_info = None
        self.last_death_info = None
        self.kill_streak = 0
        self.best_kill_streak = 0
        self.session_start = datetime.now()
        self.theme = self.config.get('theme', 'default')
        self.colors = self.get_theme_colors()
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animations)
        self.pulse_alpha = 0
        self.pulse_direction = 1
        
        self.setup_overlay()
        self.create_ui()
        self.load_position()

        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_config)
        self.save_timer.start(5000)
        
        if self.is_enabled:
            self.show_overlay()
        
    def set_enabled(self, enabled: bool):
        """Set overlay enabled state and save to config"""
        self.is_enabled = enabled
        self.config['enabled'] = enabled
        if enabled:
            self.show_overlay()
        else:
            self.hide_overlay()

    def load_config(self) -> Dict[str, Any]:
        """Load overlay configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading overlay config: {e}")
        return {
            'position': {'x': 50, 'y': 50},
            'size': {'width': 300, 'height': 200},
            'opacity': 0.9,
            'display_mode': 'compact',
            'theme': 'default',
            'animations': True,
            'show_latest_kill': True,
            'show_session_stats': True,
            'auto_hide_delay': 0,
            'font_size': 12,
            'locked': False,
            'enabled': False
        }
    
    def save_config(self):
        """Save overlay configuration to file"""
        try:
            self.config['position'] = {'x': self.x(), 'y': self.y()}
            self.config['size'] = {'width': self.width(), 'height': self.height()}
            self.config['opacity'] = self.opacity_level
            self.config['display_mode'] = self.display_mode
            self.config['enabled'] = self.is_enabled
            self.config['theme'] = self.theme
            self.config['animations'] = self.show_animations
            self.config['locked'] = self.is_locked

            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving overlay config: {e}")
    
    def get_theme_colors(self) -> Dict[str, QColor]:
        """Get colors for the current theme"""
        themes = {
            'default': {
                'background': QColor(0, 0, 0, 180),
                'border': QColor(0, 255, 65, 200),
                'text_primary': QColor(255, 255, 255, 255),
                'text_secondary': QColor(200, 200, 200, 255),
                'accent': QColor(0, 255, 65, 255),
                'kill_color': QColor(102, 255, 102, 255),
                'death_color': QColor(240, 71, 71, 255),
                'info_color': QColor(0, 204, 255, 255)
            },
            'dark': {
                'background': QColor(15, 15, 15, 200),
                'border': QColor(60, 60, 60, 200),
                'text_primary': QColor(255, 255, 255, 255),
                'text_secondary': QColor(180, 180, 180, 255),
                'accent': QColor(255, 140, 0, 255),
                'kill_color': QColor(76, 175, 80, 255),
                'death_color': QColor(244, 67, 54, 255),
                'info_color': QColor(33, 150, 243, 255)
            },
            'neon': {
                'background': QColor(5, 5, 5, 190),
                'border': QColor(0, 255, 255, 220),
                'text_primary': QColor(0, 255, 255, 255),
                'text_secondary': QColor(0, 200, 200, 255),
                'accent': QColor(255, 0, 255, 255),
                'kill_color': QColor(0, 255, 127, 255),
                'death_color': QColor(255, 20, 147, 255),
                'info_color': QColor(0, 191, 255, 255)
            }        }
        return themes.get(self.theme, themes['default'])
    
    def setup_overlay(self):
        """Setup overlay window properties"""
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.BypassWindowManagerHint |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        
        size = self.config.get('size', {'width': 300, 'height': 200})
        self.setMinimumSize(150, 80)
        self.setMaximumSize(500, 800)
        self.resize(size['width'], size['height'])    
        self.setWindowOpacity(self.opacity_level)
        
        if self.is_locked:
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.SizeAllCursor)
    def setParent(self, parent):
        """Override setParent to maintain independence"""
        self.parent_tracker = parent
        super().setParent(None)
    
    def closeEvent(self, event):
        """Handle close event - just hide instead of closing"""
        self.hide_overlay()
        event.ignore()
    def load_position(self):
        """Load position from config"""
        pos = self.config.get('position', {'x': 50, 'y': 50})
        self.move(pos['x'], pos['y'])
    def create_ui(self):
        """Create overlay UI elements based on display mode"""
        if self.layout():
            QWidget().setLayout(self.layout())
        
        if self.display_mode == 'minimal':
            self.create_minimal_ui()
        elif self.display_mode == 'detailed':
            self.create_detailed_ui()
        elif self.display_mode == 'horizontal':
            self.create_horizontal_ui()
        else:
            self.create_compact_ui()
        
        self.adjust_size_to_content()
    
    def create_minimal_ui(self):
        """Create minimal overlay showing kills and deaths with counts"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(2)
        header_layout.setContentsMargins(0, 0, 0, 0)

        header_layout.addStretch()
        
        mode_btn = QPushButton("○")
        mode_btn.setFixedSize(12, 12)
        mode_btn.clicked.connect(self.cycle_display_mode)
        mode_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {self.colors['border'].name()};
                border-radius: 6px;
                color: {self.colors['text_secondary'].name()};
                font-size: 8px;
            }}
            QPushButton:hover {{
                background: {self.colors['accent'].name()};
            }}
        """)
        header_layout.addWidget(mode_btn)
        
        layout.addLayout(header_layout)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)

        kills_section = QVBoxLayout()
        kills_section.setSpacing(0)
        
        kills_label = QLabel("KILLS")
        kills_label.setAlignment(Qt.AlignCenter)
        kills_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 10px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        self.kills_count = QLabel("0")
        self.kills_count.setAlignment(Qt.AlignCenter)
        self.kills_count.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['kill_color'].name()};
                font-size: 16px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        kills_section.addWidget(kills_label)
        kills_section.addWidget(self.kills_count)

        deaths_section = QVBoxLayout()
        deaths_section.setSpacing(0)
        
        deaths_label = QLabel("DEATHS")
        deaths_label.setAlignment(Qt.AlignCenter)
        deaths_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 10px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        self.deaths_count = QLabel("0")
        self.deaths_count.setAlignment(Qt.AlignCenter)
        self.deaths_count.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['death_color'].name()};
                font-size: 16px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        deaths_section.addWidget(deaths_label)
        deaths_section.addWidget(self.deaths_count)
        
        stats_layout.addLayout(kills_section)
        stats_layout.addLayout(deaths_section)
        
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
        self.setMinimumSize(120, 70)
        self.resize(120, 70)
    
    def create_compact_ui(self):
        """Create compact overlay with essential info in an improved layout"""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        title = QLabel("SCTool Killfeed")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['accent'].name()};
                font-size: 18px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        mode_btn = QPushButton("◐")
        mode_btn.setFixedSize(18, 18)
        mode_btn.clicked.connect(self.cycle_display_mode)
        mode_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {self.colors['border'].name()};
                border-radius: 9px;
                color: {self.colors['text_secondary'].name()};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {self.colors['accent'].name()};
            }}
        """)
        header_layout.addWidget(mode_btn)
        
        layout.addLayout(header_layout)

        stats_container = QHBoxLayout()
        stats_container.setSpacing(15)

        kills_section = QVBoxLayout()
        kills_section.setSpacing(2)
        
        kills_label = QLabel("KILLS")
        kills_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 11px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        kills_label.setAlignment(Qt.AlignCenter)
        
        self.kills_value_c = QLabel("0")
        self.kills_value_c.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['kill_color'].name()};
                font-size: 24px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.kills_value_c.setAlignment(Qt.AlignCenter)
        
        kills_section.addWidget(kills_label)
        kills_section.addWidget(self.kills_value_c)

        deaths_section = QVBoxLayout()
        deaths_section.setSpacing(2)
        
        deaths_label = QLabel("DEATHS")
        deaths_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 11px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        deaths_label.setAlignment(Qt.AlignCenter)
        
        self.deaths_value_c = QLabel("0")
        self.deaths_value_c.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['death_color'].name()};
                font-size: 24px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.deaths_value_c.setAlignment(Qt.AlignCenter)
        
        deaths_section.addWidget(deaths_label)
        deaths_section.addWidget(self.deaths_value_c)

        kd_section = QVBoxLayout()
        kd_section.setSpacing(2)
        
        kd_label = QLabel("K/D")
        kd_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 11px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        kd_label.setAlignment(Qt.AlignCenter)
        
        self.kd_value_c = QLabel("--")
        self.kd_value_c.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['info_color'].name()};
                font-size: 24px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.kd_value_c.setAlignment(Qt.AlignCenter)
        
        kd_section.addWidget(kd_label)
        kd_section.addWidget(self.kd_value_c)
        
        stats_container.addLayout(kills_section)
        stats_container.addLayout(deaths_section)
        stats_container.addLayout(kd_section)
        
        layout.addLayout(stats_container)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"color: {self.colors['border'].name()};")
        layout.addWidget(separator)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.session_label_c = QLabel("Session: 00:00")
        self.session_label_c.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['info_color'].name()};
                font-size: 16px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.session_label_c.setAlignment(Qt.AlignLeft)

        self.game_mode_label_c = QLabel("Mode: Unknown")
        self.game_mode_label_c.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.game_mode_label_c.setAlignment(Qt.AlignLeft)
        self.game_mode_label_c.setWordWrap(True)

        self.ship_label_c = QLabel("Ship: Unknown")
        self.ship_label_c.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.ship_label_c.setAlignment(Qt.AlignLeft)
        self.ship_label_c.setWordWrap(True)
        
        info_layout.addWidget(self.session_label_c)
        info_layout.addWidget(self.game_mode_label_c)
        info_layout.addWidget(self.ship_label_c)
        
        layout.addLayout(info_layout)
        
        self.setLayout(layout)
        self.setMinimumSize(320, 200)
        self.resize(350, 220)

    def create_detailed_ui(self):
        """Create detailed overlay with full information"""
        container_widget = QWidget()
        container_widget.setStyleSheet("background: transparent; border: none;")
        
        layout = QVBoxLayout(container_widget)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        title = QLabel("SCTool Killfeed Overlay")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['accent'].name()};
                font-size: 25px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        mode_btn = QPushButton("◑")
        mode_btn.setFixedSize(20, 20)
        mode_btn.clicked.connect(self.cycle_display_mode)
        mode_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {self.colors['border'].name()};
                border-radius: 10px;
                color: {self.colors['text_secondary'].name()};
                font-size: 25px;
            }}
            QPushButton:hover {{
                background: {self.colors['accent'].name()};
            }}
        """)
        header_layout.addWidget(mode_btn)
        
        layout.addLayout(header_layout)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(5)

        kills_label = QLabel("KILLS")
        kills_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        self.kills_value = QLabel("0")
        self.kills_value.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['kill_color'].name()};
                font-size: 26px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.kills_value.setAlignment(Qt.AlignCenter)
        
        deaths_label = QLabel("DEATHS")
        deaths_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        self.deaths_value = QLabel("0")
        self.deaths_value.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['death_color'].name()};
                font-size: 26px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.deaths_value.setAlignment(Qt.AlignCenter)
        
        kd_label = QLabel("K/D RATIO")
        kd_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        self.kd_value = QLabel("--")
        self.kd_value.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['info_color'].name()};
                font-size: 26px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.kd_value.setAlignment(Qt.AlignCenter)
        
        stats_grid.addWidget(kills_label, 0, 0)
        stats_grid.addWidget(self.kills_value, 1, 0)
        stats_grid.addWidget(deaths_label, 0, 1)
        stats_grid.addWidget(self.deaths_value, 1, 1)
        stats_grid.addWidget(kd_label, 0, 2)
        stats_grid.addWidget(self.kd_value, 1, 2)
        
        layout.addLayout(stats_grid)

        session_info_layout = QVBoxLayout()
        session_info_layout.setSpacing(4)

        self.session_time_label = QLabel("Session: 00:00")
        self.session_time_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['info_color'].name()};
                font-size: 21px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.session_time_label.setAlignment(Qt.AlignLeft)

        self.game_mode_label = QLabel("Mode: Unknown")
        self.game_mode_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 18px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.game_mode_label.setAlignment(Qt.AlignLeft)
        self.game_mode_label.setWordWrap(True)

        self.ship_label = QLabel("Ship: Unknown")
        self.ship_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 18px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.ship_label.setAlignment(Qt.AlignLeft)
        self.ship_label.setWordWrap(True)
        
        session_info_layout.addWidget(self.session_time_label)
        session_info_layout.addWidget(self.game_mode_label)
        session_info_layout.addWidget(self.ship_label)
        layout.addLayout(session_info_layout)
        
        if self.config.get('show_latest_kill', True):
            self.latest_kill_frame = QFrame()
            self.latest_kill_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(0, 40, 0, 100);
                    border: 1px solid {self.colors['kill_color'].name()};
                    border-radius: 4px;
                    margin: 2px;
                }}
            """)
            latest_kill_layout = QVBoxLayout(self.latest_kill_frame)
            latest_kill_layout.setContentsMargins(6, 4, 6, 4)
            latest_kill_layout.setSpacing(2)
            
            latest_title = QLabel("LATEST KILL")
            latest_title.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['kill_color'].name()};
                    font-size: 19px;
                    font-weight: bold;
                    background: transparent;
                }}
            """)
            latest_title.setAlignment(Qt.AlignCenter)
            
            self.latest_kill_info = QLabel("No kills yet")
            self.latest_kill_info.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['text_primary'].name()};
                    font-size: 20px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }}
            """)
            self.latest_kill_info.setAlignment(Qt.AlignCenter)
            self.latest_kill_info.setWordWrap(True)
            
            latest_kill_layout.addWidget(latest_title)
            latest_kill_layout.addWidget(self.latest_kill_info)
            layout.addWidget(self.latest_kill_frame)

        if self.config.get('show_latest_death', True):
            self.latest_death_frame = QFrame()
            self.latest_death_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(40, 0, 0, 100);
                    border: 1px solid {self.colors['death_color'].name()};
                    border-radius: 4px;
                    margin: 2px;
                }}
            """)
            latest_death_layout = QVBoxLayout(self.latest_death_frame)
            latest_death_layout.setContentsMargins(6, 4, 6, 4)
            latest_death_layout.setSpacing(2)
            
            death_title = QLabel("LATEST DEATH")
            death_title.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['death_color'].name()};
                    font-size: 19px;
                    font-weight: bold;
                    background: transparent;
                }}
            """)
            death_title.setAlignment(Qt.AlignCenter)
            
            self.latest_death_info = QLabel("No deaths yet")
            self.latest_death_info.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['text_primary'].name()};
                    font-size: 20px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }}
            """)
            self.latest_death_info.setAlignment(Qt.AlignCenter)
            self.latest_death_info.setWordWrap(True)
            
            latest_death_layout.addWidget(death_title)
            latest_death_layout.addWidget(self.latest_death_info)
            layout.addWidget(self.latest_death_frame)

        scroll_area = QScrollArea()
        scroll_area.setWidget(container_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {self.colors['background'].name()};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.colors['accent'].name()};
                border-radius: 4px;
                min-height: 15px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.colors['text_primary'].name()};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
        self.setMinimumSize(400, 450)
        self.resize(700, 800)

        container_widget.adjustSize()
    
    def create_horizontal_ui(self):
        """Create horizontal overlay with full information arranged horizontally"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 6, 12, 6)
        main_layout.setSpacing(8)

        title_layout = QHBoxLayout()
        title_layout.setSpacing(5)
        
        title = QLabel("SCTool Killfeed")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['accent'].name()};
                font-size: 16px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        mode_btn = QPushButton("◩")
        mode_btn.setFixedSize(16, 16)
        mode_btn.clicked.connect(self.cycle_display_mode)
        mode_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {self.colors['border'].name()};
                border-radius: 8px;
                color: {self.colors['text_secondary'].name()};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {self.colors['accent'].name()};
            }}
        """)
        title_layout.addWidget(mode_btn)
        
        main_layout.addLayout(title_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        stats_section = QHBoxLayout()
        stats_section.setSpacing(15)
        
        kills_container = QVBoxLayout()
        kills_container.setSpacing(0)
        kills_label = QLabel("KILLS")
        kills_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        kills_label.setAlignment(Qt.AlignCenter)
        self.kills_value_h = QLabel("0")
        self.kills_value_h.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['kill_color'].name()};
                font-size: 20px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.kills_value_h.setAlignment(Qt.AlignCenter)
        kills_container.addWidget(kills_label)
        kills_container.addWidget(self.kills_value_h)

        deaths_container = QVBoxLayout()
        deaths_container.setSpacing(0)
        deaths_label = QLabel("DEATHS")
        deaths_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        deaths_label.setAlignment(Qt.AlignCenter)
        self.deaths_value_h = QLabel("0")
        self.deaths_value_h.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['death_color'].name()};
                font-size: 20px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.deaths_value_h.setAlignment(Qt.AlignCenter)
        deaths_container.addWidget(deaths_label)
        deaths_container.addWidget(self.deaths_value_h)

        kd_container = QVBoxLayout()
        kd_container.setSpacing(0)
        kd_label = QLabel("K/D")
        kd_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        kd_label.setAlignment(Qt.AlignCenter)
        self.kd_value_h = QLabel("--")
        self.kd_value_h.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['info_color'].name()};
                font-size: 20px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.kd_value_h.setAlignment(Qt.AlignCenter)
        kd_container.addWidget(kd_label)
        kd_container.addWidget(self.kd_value_h)
        
        stats_section.addLayout(kills_container)
        stats_section.addLayout(deaths_container)
        stats_section.addLayout(kd_container)
        
        content_layout.addLayout(stats_section)

        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setStyleSheet(f"color: {self.colors['border'].name()};")
        content_layout.addWidget(separator1)

        session_info_section = QVBoxLayout()
        session_info_section.setSpacing(2)
        
        self.session_time_label_h = QLabel("Session: 00:00")
        self.session_time_label_h.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['info_color'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        self.game_mode_label_h = QLabel("Mode: Unknown")
        self.game_mode_label_h.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.game_mode_label_h.setWordWrap(True)
        
        self.ship_label_h = QLabel("Ship: Unknown")
        self.ship_label_h.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.ship_label_h.setWordWrap(True)
        
        session_info_section.addWidget(self.session_time_label_h)
        session_info_section.addWidget(self.game_mode_label_h)
        session_info_section.addWidget(self.ship_label_h)
        
        content_layout.addLayout(session_info_section)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet(f"color: {self.colors['border'].name()};")
        content_layout.addWidget(separator2)

        right_section = QHBoxLayout()
        right_section.setSpacing(20)
        
        if self.config.get('show_latest_kill', True):
            kill_info = QVBoxLayout()
            kill_info.setSpacing(2)
            kill_title = QLabel("LATEST KILL")
            kill_title.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['kill_color'].name()};
                    font-size: 10px;
                    font-weight: bold;
                    background: transparent;
                }}
            """)
            kill_title.setAlignment(Qt.AlignCenter)
            self.latest_kill_info_h = QLabel("No kills yet")
            self.latest_kill_info_h.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['text_primary'].name()};
                    font-size: 12px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }}
            """)
            self.latest_kill_info_h.setAlignment(Qt.AlignCenter)
            kill_info.addWidget(kill_title)
            kill_info.addWidget(self.latest_kill_info_h)
            right_section.addLayout(kill_info)
        
        if self.config.get('show_latest_death', True):
            death_info = QVBoxLayout()
            death_info.setSpacing(2)
            death_title = QLabel("LATEST DEATH")
            death_title.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['death_color'].name()};
                    font-size: 10px;
                    font-weight: bold;
                    background: transparent;
                }}
            """)
            death_title.setAlignment(Qt.AlignCenter)
            self.latest_death_info_h = QLabel("No deaths yet")
            self.latest_death_info_h.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['text_primary'].name()};
                    font-size: 12px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }}
            """)
            self.latest_death_info_h.setAlignment(Qt.AlignCenter)
            death_info.addWidget(death_title)
            death_info.addWidget(self.latest_death_info_h)
            right_section.addLayout(death_info)
        
        content_layout.addLayout(right_section)
        main_layout.addLayout(content_layout)
        
        self.setLayout(main_layout)
        self.setMinimumSize(800, 120)
        self.resize(1200, 120)

    def cycle_display_mode(self):
        """Cycle through display modes"""
        modes = ['minimal', 'compact', 'detailed', 'horizontal']
        current_index = modes.index(self.display_mode)
        next_index = (current_index + 1) % len(modes)
        self.display_mode = modes[next_index]
        self.config['display_mode'] = self.display_mode
        self.create_ui()
        self.update_display()
        self.adjust_size_to_content()
        self.show_mode_change_indicator()
    
    def show_mode_change_indicator(self):
        """Show a brief indicator of mode change"""
        if hasattr(self, 'mode_indicator') and self.mode_indicator is not None:
            try:
                self.mode_indicator.deleteLater()
            except RuntimeError:
                pass
        
        self.mode_indicator = QLabel(f"Mode: {self.display_mode.title()}")
        self.mode_indicator.setParent(self)
        self.mode_indicator.setStyleSheet(f"""
            QLabel {{
                background: {self.colors['accent'].name()};
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        self.mode_indicator.adjustSize()
        self.mode_indicator.move(10, 10)
        self.mode_indicator.show()
        QTimer.singleShot(2000, self._safe_delete_mode_indicator)
    
    def _safe_delete_mode_indicator(self):
        """Safely delete mode indicator if it still exists"""
        if hasattr(self, 'mode_indicator') and self.mode_indicator is not None:
            try:
                self.mode_indicator.deleteLater()
                self.mode_indicator = None
            except RuntimeError:
                pass
    
    def paintEvent(self, event):
        """Draw overlay background with enhanced visuals"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(2, 2, -2, -2)
        
        gradient = QLinearGradient(0, 0, 0, rect.height())
        bg_color = QColor(self.colors['background'])
        bg_color.setAlpha(int(bg_color.alpha() * self.opacity_level))
        
        gradient.setColorAt(0.0, bg_color)
        darker_bg = QColor(bg_color)
        darker_bg.setRgb(
            max(0, bg_color.red() - 20),
            max(0, bg_color.green() - 20),
            max(0, bg_color.blue() - 20),
            bg_color.alpha()
        )
        gradient.setColorAt(1.0, darker_bg)
        
        painter.setBrush(QBrush(gradient))

        border_color = QColor(self.colors['border'])
        if self.show_animations and self.animation_timer.isActive():
            alpha = int(border_color.alpha() * (0.7 + 0.3 * abs(self.pulse_alpha)))
            border_color.setAlpha(alpha)
        
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(rect, 8, 8)
        
        if self.display_mode == 'detailed':
            corner_size = 8
            corner_rect = rect.adjusted(rect.width() - corner_size, rect.height() - corner_size, 0, 0)
            painter.setPen(QPen(self.colors['text_secondary'], 1))

    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton and not self.is_locked:
            self.is_dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle dragging"""
        if self.is_dragging and event.buttons() == Qt.LeftButton and not self.is_locked:
            new_pos = event.globalPos() - self.drag_position
            self.move(new_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self.is_dragging = False
        event.accept()
    
    def wheelEvent(self, event):
        """Handle mouse wheel for opacity adjustment"""
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y() / 120
            new_opacity = max(0.3, min(1.0, self.opacity_level + delta * 0.1))
            self.set_opacity(new_opacity)
            event.accept()
    
    def set_opacity(self, opacity: float):
        """Set overlay opacity"""
        self.opacity_level = opacity
        self.config['opacity'] = opacity
        self.setWindowOpacity(opacity)
        self.update()
    def set_theme(self, theme: str):
        """Change overlay theme"""
        self.theme = theme
        self.config['theme'] = theme
        self.colors = self.get_theme_colors()
        self.create_ui()
        self.update_display()
    
    def toggle_animations(self, enabled: bool):
        """Toggle animations"""
        self.show_animations = enabled
        self.config['animations'] = enabled
        
        if enabled:
            self.animation_timer.start(50)
        else:
            self.animation_timer.stop()
    
    def set_locked(self, locked: bool):
        """Set overlay lock state"""
        self.is_locked = locked
        self.config['locked'] = locked
        if locked:
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.SizeAllCursor)
    
    def update_animations(self):
        """Update animation states"""
        if not self.show_animations:
            return
        
        self.pulse_alpha += self.pulse_direction * 0.05
        if self.pulse_alpha >= 1.0:
            self.pulse_alpha = 1.0
            self.pulse_direction = -1
        elif self.pulse_alpha <= 0.0:
            self.pulse_alpha = 0.0
            self.pulse_direction = 1
        
        self.update()
    
    def update_live_data(self):
        """Update live data like session time, ship info, etc."""
        if not self.is_visible or not self.parent_tracker:
            return

        if hasattr(self.parent_tracker, 'session_time_display'):
            session_time_text = self.parent_tracker.session_time_display.text()
            if session_time_text != self.session_time:
                self.session_time = session_time_text
                self.update_session_time_display()

        if hasattr(self.parent_tracker, 'ship_combo'):
            current_ship = self.parent_tracker.ship_combo.currentText() or "Unknown"
            if current_ship != self.ship:
                self.ship = current_ship
                self.update_ship_display()
        
        if hasattr(self.parent_tracker, 'game_mode_display'):
            mode_text = self.parent_tracker.game_mode_display.text()
            if mode_text.startswith('Mode: '):
                current_mode = mode_text[6:]
                if current_mode != self.game_mode:
                    self.game_mode = current_mode
                    self.update_game_mode_display()

    def update_session_time_display(self):
        """Update only session time labels without full UI refresh"""
        if self.display_mode == 'compact':
            if hasattr(self, 'session_label_c'):
                self.session_label_c.setText(f"Session: {self.session_time}")
                
        elif self.display_mode == 'detailed':
            if hasattr(self, 'session_time_label'):
                self.session_time_label.setText(f"Session: {self.session_time}")
                
        elif self.display_mode == 'horizontal':
            if hasattr(self, 'session_time_label_h'):
                self.session_time_label_h.setText(f"Session: {self.session_time}")

    def update_ship_display(self):
        """Update only ship labels without full UI refresh"""
        if self.display_mode == 'compact':
            if hasattr(self, 'ship_label_c'):
                self.ship_label_c.setText(f"Ship: {self.ship}")
                
        elif self.display_mode == 'detailed':
            if hasattr(self, 'ship_label'):
                self.ship_label.setText(f"Ship: {self.ship}")
                
        elif self.display_mode == 'horizontal':
            if hasattr(self, 'ship_label_h'):
                self.ship_label_h.setText(f"Ship: {self.ship}")

    def update_game_mode_display(self):
        """Update only game mode labels without full UI refresh"""
        if self.display_mode == 'compact':
            if hasattr(self, 'game_mode_label_c'):
                self.game_mode_label_c.setText(f"Mode: {self.game_mode}")
                
        elif self.display_mode == 'detailed':
            if hasattr(self, 'game_mode_label'):
                self.game_mode_label.setText(f"Mode: {self.game_mode}")
                
        elif self.display_mode == 'horizontal':
            if hasattr(self, 'game_mode_label_h'):
                self.game_mode_label_h.setText(f"Mode: {self.game_mode}")

    def hide_overlay(self):
        """Hide the overlay"""
        self.is_visible = False
        self.hide()
        self.animation_timer.stop()
        if hasattr(self, 'live_update_timer'):
            self.live_update_timer.stop()

    def show_overlay(self):
        """Show the overlay"""
        self.is_visible = True
        self.show()
        if self.show_animations:
            self.animation_timer.start(50)
        if hasattr(self, 'live_update_timer'):
            self.live_update_timer.start(1000)
    
    def update_stats(self, kills: int, deaths: int, session_time: str = "00:00", 
        ship: str = "Unknown", game_mode: str = "Unknown", 
        kill_streak: int = 0, latest_kill: Optional[Dict] = None,
        latest_death: Optional[Dict] = None):
        """Update overlay with new stats"""
        if latest_kill:
            self.last_kill_info = latest_kill
            
        if latest_death:
            self.last_death_info = latest_death
            
        if kills > self.kills:
            self.kill_streak = kill_streak
            if self.kill_streak > self.best_kill_streak:
                self.best_kill_streak = self.kill_streak
        elif deaths > self.deaths:
            self.kill_streak = 0
        
        self.kills = kills
        self.deaths = deaths
        self.session_time = session_time
        self.ship = ship
        self.game_mode = game_mode
        
        self.update_display()
    
    def clean_weapon_name(self, weapon_name: str) -> str:
        """Clean weapon name by removing long ID strings and replacing underscores with spaces"""
        
        weapon_name = re.sub(r'_\d+$', '', weapon_name)
        
        weapon_name = weapon_name.replace('_', ' ')

        weapon_name = re.sub(r'\s+\d+$', '', weapon_name)
        
        return weapon_name.strip()

    def update_display(self):
        """Update the display based on current mode and data"""
        if not hasattr(self, 'layout') or not self.layout():
            return
        
        if self.deaths > 0:
            kd_ratio = f"{self.kills / self.deaths:.2f}"
        else:
            kd_ratio = str(self.kills) if self.kills > 0 else "--"
        
        if self.display_mode == 'minimal':
            if hasattr(self, 'kills_count'):
                self.kills_count.setText(str(self.kills))
            if hasattr(self, 'deaths_count'):
                self.deaths_count.setText(str(self.deaths))
                
        elif self.display_mode == 'compact':
            if hasattr(self, 'kills_value_c'):
                self.kills_value_c.setText(str(self.kills))
            if hasattr(self, 'deaths_value_c'):
                self.deaths_value_c.setText(str(self.deaths))
            if hasattr(self, 'kd_value_c'):
                self.kd_value_c.setText(kd_ratio)
            if hasattr(self, 'session_label_c'):
                self.session_label_c.setText(f"Session: {self.session_time}")
            if hasattr(self, 'game_mode_label_c'):
                self.game_mode_label_c.setText(f"Mode: {self.game_mode}")
            if hasattr(self, 'ship_label_c'):
                self.ship_label_c.setText(f"Ship: {self.ship}")
                
        elif self.display_mode == 'detailed':
            if hasattr(self, 'kills_value'):
                self.kills_value.setText(str(self.kills))
            if hasattr(self, 'deaths_value'):
                self.deaths_value.setText(str(self.deaths))
            if hasattr(self, 'kd_value'):
                self.kd_value.setText(kd_ratio)
            if hasattr(self, 'session_time_label'):
                self.session_time_label.setText(f"Session: {self.session_time}")
            if hasattr(self, 'game_mode_label'):
                self.game_mode_label.setText(f"Mode: {self.game_mode}")
            if hasattr(self, 'ship_label'):
                self.ship_label.setText(f"Ship: {self.ship}")
            
            if hasattr(self, 'latest_kill_frame') and hasattr(self, 'latest_kill_info'):
                if self.last_kill_info is not None:
                    victim = self.last_kill_info.get('victim', 'Unknown')
                    weapon = self.last_kill_info.get('weapon', 'Unknown')
                    clean_weapon = self.clean_weapon_name(weapon)
                    self.latest_kill_info.setText(f"{victim}\n{clean_weapon}")
                else:
                    self.latest_kill_info.setText("No kills yet")

            if hasattr(self, 'latest_death_frame') and hasattr(self, 'latest_death_info'):
                if self.last_death_info is not None:
                    attacker = self.last_death_info.get('attacker', 'Unknown')
                    weapon = self.last_death_info.get('weapon', 'Unknown')
                    clean_weapon = self.clean_weapon_name(weapon)
                    self.latest_death_info.setText(f"Killed by: {attacker}\n{clean_weapon}")
                else:
                    self.latest_death_info.setText("No deaths yet")

        elif self.display_mode == 'horizontal':
            if hasattr(self, 'kills_value_h'):
                self.kills_value_h.setText(str(self.kills))
            if hasattr(self, 'deaths_value_h'):
                self.deaths_value_h.setText(str(self.deaths))
            if hasattr(self, 'kd_value_h'):
                self.kd_value_h.setText(kd_ratio)
            if hasattr(self, 'session_time_label_h'):
                self.session_time_label_h.setText(f"Session: {self.session_time}")
            if hasattr(self, 'game_mode_label_h'):
                self.game_mode_label_h.setText(f"Mode: {self.game_mode}")
            if hasattr(self, 'ship_label_h'):
                self.ship_label_h.setText(f"Ship: {self.ship}")
            
            if hasattr(self, 'latest_kill_info_h'):
                if self.last_kill_info is not None:
                    victim = self.last_kill_info.get('victim', 'Unknown')
                    weapon = self.last_kill_info.get('weapon', 'Unknown')
                    clean_weapon = self.clean_weapon_name(weapon)
                    self.latest_kill_info_h.setText(f"{victim}\n{clean_weapon}")
                else:
                    self.latest_kill_info_h.setText("No kills yet")

            if hasattr(self, 'latest_death_info_h'):
                if self.last_death_info is not None:
                    attacker = self.last_death_info.get('attacker', 'Unknown')
                    weapon = self.last_death_info.get('weapon', 'Unknown')
                    clean_weapon = self.clean_weapon_name(weapon)
                    self.latest_death_info_h.setText(f"Killed by: {attacker}\n{clean_weapon}")
                else:
                    self.latest_death_info_h.setText("No deaths yet")

        self.adjust_size_to_content()
    
    def adjust_size_to_content(self):
        """Dynamically adjust overlay size based on content"""
        if self.display_mode == 'detailed':
            scroll_area = self.findChild(QScrollArea)
            if scroll_area and scroll_area.widget():
                container_widget = scroll_area.widget()
                container_widget.updateGeometry()
                container_widget.adjustSize()
                content_height = container_widget.sizeHint().height()

                padding = 30
                total_height = min(content_height + padding, 600)
                
                current_width = max(self.width(), 350)
                
                final_height = max(total_height, 200)
                final_height = min(final_height, 600)
                
                self.resize(current_width, final_height)
                    
                self.config['size'] = {'width': current_width, 'height': final_height}
                
        elif self.display_mode == 'compact':
            if hasattr(self, 'layout') and self.layout():
                self.layout().activate()
                self.adjustSize()
                
                min_width, min_height = 220, 120
                current_size = self.size()
                
                new_width = max(current_size.width(), min_width)
                new_height = max(current_size.height(), min_height)
                
                max_height = 180
                new_height = min(new_height, max_height)
                
                self.resize(new_width, new_height)
                self.config['size'] = {'width': new_width, 'height': new_height}
                
        elif self.display_mode == 'minimal':
            self.resize(80, 40)
            self.config['size'] = {'width': 80, 'height': 40}
        elif self.display_mode == 'horizontal':
            min_width = 800
            min_height = 80
            current_size = self.size()
            
            new_width = max(current_size.width(), min_width)
            new_height = min(current_size.height(), min_height)
            
            self.resize(new_width, min_height)
            self.config['size'] = {'width': new_width, 'height': min_height}
    
    def handle_content_update(self):
        """Handle content updates and ensure proper sizing"""
        if hasattr(self, 'layout') and self.layout():
            self.layout().update()

        QApplication.processEvents()
        self.adjust_size_to_content()
        self.update_display()

class OverlayControlPanel(QFrame):
    """Advanced control panel for overlay configuration"""
    
    overlay_toggled = pyqtSignal(bool)
    
    def __init__(self, overlay: GameOverlay, parent=None):
        super().__init__(parent)
        self.overlay = overlay
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the control panel UI"""
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 20, 20, 0.9);
                border-radius: 8px;
                border: 1px solid #333333;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)
        
        header = QLabel("GAME OVERLAY")
        header.setStyleSheet("""
            QLabel {
                color: #f0f0f0;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
                margin-bottom: 10px;
            }
        """)
        content_layout.addWidget(header)
        
        desc = QLabel("Overlay system with multiple display modes, customizable themes, "
                     "and real-time statistics. The overlay shows your kill/death stats, session information, "
                     "and latest kill details while playing Star Citizen.")
        desc.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 13px;
                background: transparent;
                border: none;
                margin-bottom: 15px;
            }
        """)
        desc.setWordWrap(True)
        content_layout.addWidget(desc)
        basic_group = QGroupBox("Basic Controls")
        basic_group.setStyleSheet("QGroupBox { color: #f0f0f0; }")
        basic_layout = QVBoxLayout(basic_group)
        basic_layout.setSpacing(10)

        self.enable_checkbox = QCheckBox("Enable Game Overlay")
        self.enable_checkbox.setChecked(self.overlay.is_enabled)
        self.enable_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                spacing: 10px;
                background: transparent;
                border: none;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border: 2px solid #333333;
                border-radius: 3px;
                background-color: #1e1e1e;
            }            
            QCheckBox::indicator:checked {
                background-color: #00ff41;
                border-color: #00ff41;
            }
        """)
        self.enable_checkbox.toggled.connect(self.toggle_overlay)
        basic_layout.addWidget(self.enable_checkbox)
        
        self.lock_checkbox = QCheckBox("Lock Overlay Position")
        self.lock_checkbox.setChecked(self.overlay.is_locked)
        self.lock_checkbox.setStyleSheet(self.enable_checkbox.styleSheet())
        self.lock_checkbox.toggled.connect(self.overlay.set_locked)
        basic_layout.addWidget(self.lock_checkbox)
        
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Display Mode:")
        mode_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; }")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Minimal", "Compact", "Detailed", "Horizontal"])
        self.mode_combo.setCurrentText(self.overlay.display_mode.title())
        self.mode_combo.currentTextChanged.connect(self.change_display_mode)
        self.mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e1e1e;
                color: #f0f0f0;
                padding: 8px;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                min-width: 100px;
            }
            QComboBox:hover { border-color: #00ff41; }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #f0f0f0;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e1e;
                color: #f0f0f0;
                selection-background-color: #00ff41;
            }
        """)
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        basic_layout.addLayout(mode_layout)
        
        content_layout.addWidget(basic_group)
        
        appearance_group = QGroupBox("Appearance")
        appearance_group.setStyleSheet("QGroupBox { color: #f0f0f0; }")
        appearance_layout = QVBoxLayout(appearance_group)
        appearance_layout.setSpacing(10)
        
        opacity_layout = QHBoxLayout()
        opacity_label = QLabel("Opacity:")
        opacity_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; }")
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(int(self.overlay.opacity_level * 100))
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #2a2a2a;
                height: 8px;
                background: #1a1a1a;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00ff41;
                border: 1px solid #2a2a2a;
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #00ff41;
                border-radius: 4px;
            }
        """)
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        
        self.opacity_label = QLabel(f"{int(self.overlay.opacity_level * 100)}%")
        self.opacity_label.setStyleSheet("QLabel { color: #ffffff; min-width: 40px; }")
        
        opacity_layout.addWidget(opacity_label)
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        appearance_layout.addLayout(opacity_layout)
        
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; }")
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Dark", "Neon"])
        self.theme_combo.setCurrentText(self.overlay.theme.title())
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        self.theme_combo.setStyleSheet(self.mode_combo.styleSheet())
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        appearance_layout.addLayout(theme_layout)
        
        self.animations_checkbox = QCheckBox("Enable Animations")
        self.animations_checkbox.setChecked(self.overlay.show_animations)
        self.animations_checkbox.setStyleSheet(self.enable_checkbox.styleSheet())
        self.animations_checkbox.toggled.connect(self.overlay.toggle_animations)
        appearance_layout.addWidget(self.animations_checkbox)
        
        content_layout.addWidget(appearance_group)

        position_group = QGroupBox("Position & Size")
        position_group.setStyleSheet("QGroupBox { color: #f0f0f0; }")
        position_layout = QVBoxLayout(position_group)
        position_layout.setSpacing(10)
        
        pos_buttons_layout = QHBoxLayout()
        
        pos_tl_btn = QPushButton("Top Left")
        pos_tl_btn.clicked.connect(lambda: self.set_position("top-left"))
        
        pos_tr_btn = QPushButton("Top Right")
        pos_tr_btn.clicked.connect(lambda: self.set_position("top-right"))
        
        pos_bl_btn = QPushButton("Bottom Left")
        pos_bl_btn.clicked.connect(lambda: self.set_position("bottom-left"))
        
        pos_br_btn = QPushButton("Bottom Right")
        pos_br_btn.clicked.connect(lambda: self.set_position("bottom-right"))
        
        pos_center_btn = QPushButton("Center")
        pos_center_btn.clicked.connect(lambda: self.set_position("center"))
        
        for btn in [pos_tl_btn, pos_tr_btn, pos_bl_btn, pos_br_btn, pos_center_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e1e1e;
                    color: #f0f0f0;
                    border: 1px solid #2a2a2a;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 15px;
                }
                QPushButton:hover {
                    border-color: #00ff41;
                    background-color: #2a2a2a;
                }
            """)
            pos_buttons_layout.addWidget(btn)
        
        position_layout.addLayout(pos_buttons_layout)
        
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self.reset_position)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e;
                color: #f0f0f0;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                border-color: #00ff41;
                background-color: #2a2a2a;
            }
        """)
        position_layout.addWidget(reset_btn)
        
        content_layout.addWidget(position_group)
        
        instructions = QLabel("""
        <b>Instructions:</b><br>
        • Left-click and drag to move the overlay<br>
        • Ctrl + Mouse wheel to adjust opacity<br>
        • Click the mode button (◐/◑) on overlay to cycle modes<br>
        • Overlay stays on top of all windows including games
        """)
        instructions.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 15px;
                background: rgba(30, 30, 30, 0.5);
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 10px;
                margin-top: 10px;
            }
        """)
        instructions.setWordWrap(True)
        content_layout.addWidget(instructions)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
    
    def toggle_overlay(self, enabled: bool):
        """Toggle overlay visibility"""
        self.overlay.set_enabled(enabled)
        self.overlay_toggled.emit(enabled)
    
    def update_opacity(self, value: int):
        """Update overlay opacity"""
        opacity = value / 100.0
        self.overlay.set_opacity(opacity)
        self.opacity_label.setText(f"{value}%")
    
    def change_display_mode(self, mode_text: str):
        """Change overlay display mode"""
        mode = mode_text.lower()
        self.overlay.display_mode = mode
        self.overlay.config['display_mode'] = mode
        self.overlay.create_ui()
        self.overlay.update_display()
    
    def change_theme(self, theme_text: str):
        """Change overlay theme"""
        theme = theme_text.lower()
        self.overlay.set_theme(theme)
    
    def set_position(self, position: str):
        """Set overlay to predefined position"""
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        
        positions = {
            "top-left": (50, 50),
            "top-right": (screen.width() - self.overlay.width() - 50, 50),
            "bottom-left": (50, screen.height() - self.overlay.height() - 100),
            "bottom-right": (screen.width() - self.overlay.width() - 50, 
                           screen.height() - self.overlay.height() - 100),
            "center": (screen.width() // 2 - self.overlay.width() // 2,
                      screen.height() // 2 - self.overlay.height() // 2)
        }
        
        if position in positions:
            x, y = positions[position]
            self.overlay.move(x, y)
    
    def reset_position(self):
        """Reset overlay to default position"""
        self.set_position("top-right")