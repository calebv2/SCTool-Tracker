# detailed_overlay.py

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
    self.setMinimumSize(400, 350)
    self.resize(700, 600)

    container_widget.adjustSize()