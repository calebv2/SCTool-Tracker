# compact_overlay.py

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

def create_compact_ui(self):
    """Create compact overlay with essential info in an improved layout"""
    layout = QVBoxLayout()
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(8)

    header_layout = QHBoxLayout()
    header_layout.setSpacing(8)
    
    title = QLabel(t("SCTool Killfeed"))
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
    
    kills_label = QLabel(t("KILLS"))
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
    
    deaths_label = QLabel(t("DEATHS"))
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

    self.session_label_c = QLabel(t("Session: 00:00"))
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

    self.game_mode_label_c = QLabel(t("Mode: Unknown"))
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

    self.ship_label_c = QLabel(t("Ship: Unknown"))
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