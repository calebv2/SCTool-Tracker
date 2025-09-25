# detailed_overlay.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from language_manager import t

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt

def create_detailed_ui(self):
    """Create detailed overlay with full information"""
    container_widget = QWidget()
    container_widget.setStyleSheet("background: transparent; border: none;")
    
    layout = QVBoxLayout(container_widget)
    layout.setContentsMargins(15, 12, 15, 12)
    layout.setSpacing(8)
    
    header_layout = QHBoxLayout()
    header_layout.setSpacing(8)
    
    title = QLabel(t("SCTool Killfeed Overlay"))
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
    
    layout.addLayout(header_layout)

    stats_grid = QGridLayout()
    stats_grid.setSpacing(5)

    kills_label = QLabel(t("KILLS"))
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
    
    deaths_label = QLabel(t("DEATHS"))
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
    
    kd_label = QLabel(t("K/D RATIO"))
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

    self.session_time_label = QLabel(t("Session") + ": 00:00")
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

    self.game_mode_label = QLabel(t("Mode") + ": " + t("Unknown"))
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

    self.ship_label = QLabel(t("Ship") + ": " + t("Unknown"))
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
                border-radius: 4px;
                margin: 2px;
            }}
        """)
        latest_kill_layout = QVBoxLayout(self.latest_kill_frame)
        latest_kill_layout.setContentsMargins(8, 6, 8, 6)
        latest_kill_layout.setSpacing(4)
        
        latest_title = QLabel(t("LATEST KILL"))
        latest_title.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['kill_color'].name()};
                font-size: 19px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        latest_title.setAlignment(Qt.AlignLeft)
        
        self.latest_kill_attacker = QLabel(t("Attacker") + ": --")
        self.latest_kill_attacker.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.latest_kill_attacker.setAlignment(Qt.AlignLeft)
        
        self.latest_kill_engagement = QLabel(t("Engagement") + ": --")
        self.latest_kill_engagement.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.latest_kill_engagement.setAlignment(Qt.AlignLeft)
        
        self.latest_kill_method = QLabel(t("Method") + ": --")
        self.latest_kill_method.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.latest_kill_method.setAlignment(Qt.AlignLeft)
        
        self.latest_kill_victim = QLabel(t("Victim") + ": --")
        self.latest_kill_victim.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.latest_kill_victim.setAlignment(Qt.AlignLeft)
        
        self.latest_kill_location = QLabel(t("Location") + ": --")
        self.latest_kill_location.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.latest_kill_location.setAlignment(Qt.AlignLeft)
        
        self.latest_kill_organization = QLabel(t("Organization") + ": -- (" + t("Tag") + ": --)")
        self.latest_kill_organization.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.latest_kill_organization.setAlignment(Qt.AlignLeft)
        
        latest_kill_layout.addWidget(latest_title)
        latest_kill_layout.addWidget(self.latest_kill_attacker)
        latest_kill_layout.addWidget(self.latest_kill_engagement)
        latest_kill_layout.addWidget(self.latest_kill_method)
        latest_kill_layout.addWidget(self.latest_kill_victim)
        latest_kill_layout.addWidget(self.latest_kill_location)
        latest_kill_layout.addWidget(self.latest_kill_organization)
        layout.addWidget(self.latest_kill_frame)

    if self.config.get('show_latest_death', True):
        self.latest_death_frame = QFrame()
        self.latest_death_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(40, 0, 0, 100);
                border-radius: 4px;
                margin: 2px;
            }}
        """)
        latest_death_layout = QVBoxLayout(self.latest_death_frame)
        latest_death_layout.setContentsMargins(8, 6, 8, 6)
        latest_death_layout.setSpacing(4)
        
        death_title = QLabel(t("LATEST DEATH"))
        death_title.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['death_color'].name()};
                font-size: 19px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        death_title.setAlignment(Qt.AlignLeft)
        
        self.latest_death_attacker = QLabel(t("Attacker") + ": --")
        self.latest_death_attacker.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.latest_death_attacker.setAlignment(Qt.AlignLeft)
        
        self.latest_death_organization = QLabel(t("Organization") + ": -- (" + t("Tag") + ": --)")
        self.latest_death_organization.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.latest_death_organization.setAlignment(Qt.AlignLeft)
        
        self.latest_death_location = QLabel(t("Location") + ": --")
        self.latest_death_location.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.latest_death_location.setAlignment(Qt.AlignLeft)
        
        self.latest_death_damage_type = QLabel(t("Damage Type") + ": --")
        self.latest_death_damage_type.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_primary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.latest_death_damage_type.setAlignment(Qt.AlignLeft)
        
        latest_death_layout.addWidget(death_title)
        latest_death_layout.addWidget(self.latest_death_attacker)
        latest_death_layout.addWidget(self.latest_death_organization)
        latest_death_layout.addWidget(self.latest_death_location)
        latest_death_layout.addWidget(self.latest_death_damage_type)
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
    self.setMinimumSize(400, 400)
    self.resize(1000, 600)

    container_widget.adjustSize()