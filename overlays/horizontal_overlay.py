# horizontal_overlay.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from language_manager import t

from PyQt5.QtWidgets import (
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QPushButton, 
    QFrame
)
from PyQt5.QtCore import Qt

def create_horizontal_ui(self):
    """Create horizontal overlay with full information arranged horizontally"""
    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(12, 6, 12, 6)
    main_layout.setSpacing(8)

    title_layout = QHBoxLayout()
    title_layout.setSpacing(5)
    
    title = QLabel(t("SCTool Killfeed"))
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
    kills_label = QLabel(t("KILLS"))
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
    deaths_label = QLabel(t("DEATHS"))
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
    kd_label = QLabel(t("K/D"))
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
    
    self.session_time_label_h = QLabel(t("Session") + ": 00:00")
    self.session_time_label_h.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['info_color'].name()};
            font-size: 14px;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    
    self.game_mode_label_h = QLabel(t("Mode") + ": " + t("Unknown"))
    self.game_mode_label_h.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['text_secondary'].name()};
            font-size: 14px;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    self.game_mode_label_h.setWordWrap(True)
    
    self.ship_label_h = QLabel(t("Ship") + ": " + t("Unknown"))
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
        kill_title = QLabel(t("LATEST KILL"))
        kill_title.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['kill_color'].name()};
                font-size: 10px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        kill_title.setAlignment(Qt.AlignCenter)
        self.latest_kill_info_h = QLabel(t("No kills yet"))
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
        death_title = QLabel(t("LATEST DEATH"))
        death_title.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['death_color'].name()};
                font-size: 10px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        death_title.setAlignment(Qt.AlignCenter)
        self.latest_death_info_h = QLabel(t("No deaths yet"))
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