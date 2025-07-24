# minimal_overlay.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from language_manager import t

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt   

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
    
    kills_label = QLabel(t("KILLS"))
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
    
    deaths_label = QLabel(t("DEATHS"))
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
    
    mode_text = t('Mode')
    unknown_text = t('Unknown')
    self.game_mode_label_m = QLabel(f"{mode_text}: {unknown_text}")
    self.game_mode_label_m.setAlignment(Qt.AlignCenter)
    self.game_mode_label_m.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['text_secondary'].name()};
            font-size: 8px;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    layout.addWidget(self.game_mode_label_m)
    
    self.setLayout(layout)
    self.setMinimumSize(120, 85)
    self.resize(120, 85)