# utlity.py

import os
import re
import sys
import json
import time
import logging
import shutil
import requests

from responsive_ui import ScreenScaler
from overlay import GameOverlay, OverlayControlPanel
from PyQt5.QtGui import QKeyEvent
from datetime import datetime, timedelta
from PyQt5.QtGui import QIcon, QDesktopServices, QPixmap, QPainter, QBrush, QPen, QColor, QPainterPath, QKeySequence
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QFormLayout, QComboBox, QCheckBox,
    QSlider, QFileDialog, QTextBrowser, QScrollArea, QFrame,
    QSizePolicy, QApplication, QStackedWidget, QMessageBox
)

from PyQt5.QtCore import (
    Qt, QUrl, QTimer, QStandardPaths, QDir, QSize, QRect
)

from kill_clip import ButtonAutomationWidget

class ScreenScaler:
    @staticmethod
    def get_screen_info():
        """Fallback method"""
        screen = QApplication.primaryScreen()
        screen_size = screen.availableGeometry()
        return screen_size.width(), screen_size.height(), 1.0
        
    @staticmethod
    def scale_size(size, scale_factor):
        """Fallback method"""
        return int(size * scale_factor)

def get_appdata_paths() -> tuple[str, str, str]:
    appdata_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not appdata_dir:
        appdata_dir = os.path.expanduser("~")
    tracker_dir = os.path.join(appdata_dir, "SCTool_Tracker")
    QDir().mkpath(tracker_dir)

    config_file = os.path.join(tracker_dir, "config.json")
    log_file = os.path.join(tracker_dir, "kill_logger.log")
    return config_file, log_file, tracker_dir

def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

CONFIG_FILE, LOG_FILE, TRACKER_DIR = get_appdata_paths()

logging.basicConfig(
    filename=LOG_FILE,
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def init_ui(self) -> None:
    main_widget = QWidget()
    main_widget.setStyleSheet(
        "QWidget { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
        "stop:0 #1a1a1a, stop:1 #0d0d0d); "
        "border: 1px solid #2a2a2a; border-radius: 10px; }"
    )
    main_layout = QHBoxLayout()
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)
    sidebar = QWidget()
    sidebar.setFixedWidth(220)
    sidebar.setStyleSheet(
        "QWidget { background-color: #151515; border-right: 1px solid #2a2a2a; "
        "border-top-left-radius: 10px; border-bottom-left-radius: 10px; "
        "border-top-right-radius: 0px; border-bottom-right-radius: 0px; }"
    )
    sidebar_layout = QVBoxLayout(sidebar)
    sidebar_layout.setContentsMargins(0, 15, 0, 15)
    sidebar_layout.setSpacing(2)
    logo_container = QWidget()
    logo_container.setStyleSheet("border: none; background: transparent;")
    logo_layout = QVBoxLayout(logo_container)
    logo_layout.setContentsMargins(10, 0, 10, 20)

    self.user_profile_image = QLabel()
    self.user_profile_image.setFixedSize(64, 64)
    self.user_profile_image.setStyleSheet(
        "QLabel { border-radius: 32px; border: 2px solid #333333; background-color: #1a1a1a; }"
    )
    self.user_profile_image.setAlignment(Qt.AlignCenter)
    logo_layout.addWidget(self.user_profile_image, alignment=Qt.AlignCenter)
    self.set_default_user_image()
    
    app_title = QLabel("SCTool Tracker")
    app_title.setStyleSheet(
        "QLabel { color: #f04747; font-size: 16px; font-weight: bold; background: transparent; border: none; }"
    )
    app_title.setAlignment(Qt.AlignCenter)
    logo_layout.addWidget(app_title)
    
    self.user_display = QLabel("User: Not logged in")
    self.user_display.setStyleSheet(
        "QLabel { color: #f0f0f0; font-size: 12px; background: transparent; border: none; }"
    )
    self.user_display.setAlignment(Qt.AlignCenter)
    logo_layout.addWidget(self.user_display)
    
    sidebar_layout.addWidget(logo_container)
    status_container = QWidget()
    status_container.setStyleSheet("border: none; background: transparent;")
    status_layout = QVBoxLayout(status_container)
    status_layout.setContentsMargins(15, 0, 15, 15)
    status_layout.setSpacing(10)
    
    monitoring_status = QHBoxLayout()
    self.monitoring_indicator = QLabel()
    self.monitoring_indicator.setFixedSize(12, 12)
    self.update_monitor_indicator(False)
    monitoring_label = QLabel("MONITORING")
    monitoring_label.setStyleSheet("QLabel { color: #999999; font-size: 11px; background: transparent; border: none; }")
    monitoring_status.addWidget(self.monitoring_indicator)
    monitoring_status.addWidget(monitoring_label)
    monitoring_status.addStretch()
    
    api_status = QHBoxLayout()
    self.api_indicator = QLabel()
    self.api_indicator.setFixedSize(12, 12)
    self.update_api_indicator(False)
    api_label = QLabel("API CONNECTED")
    api_label.setStyleSheet("QLabel { color: #999999; font-size: 11px; background: transparent; border: none; }")
    api_status.addWidget(self.api_indicator)
    api_status.addWidget(api_label)
    api_status.addStretch()
    
    twitch_status = QHBoxLayout()
    self.twitch_indicator = QLabel()
    self.twitch_indicator.setFixedSize(12, 12)
    self.update_twitch_indicator(False)
    twitch_label = QLabel("TWITCH CONNECTED")
    twitch_label.setStyleSheet("QLabel { color: #999999; font-size: 11px; background: transparent; border: none; }")
    twitch_status.addWidget(self.twitch_indicator)
    twitch_status.addWidget(twitch_label)
    twitch_status.addStretch()
    
    game_mode_status = QHBoxLayout()
    self.game_mode_indicator = QLabel()
    self.game_mode_indicator.setFixedSize(12, 12)
    self.game_mode_indicator.setStyleSheet(
        "QLabel { background-color: #00ccff; border-radius: 6px; border: 1px solid #0099cc; }"
    )
    game_mode_label = QLabel("GAME MODE")
    game_mode_label.setStyleSheet("QLabel { color: #999999; font-size: 11px; background: transparent; border: none; }")
    game_mode_status.addWidget(self.game_mode_indicator)
    game_mode_status.addWidget(game_mode_label)
    game_mode_status.addStretch()
    
    self.game_mode_display = QLabel("Mode: Unknown")
    self.game_mode_display.setStyleSheet(
        "QLabel { color: #00ccff; font-size: 11px; font-weight: bold; background: transparent; border: none; }"
    )
    
    ship_status = QHBoxLayout()
    self.ship_indicator = QLabel()
    self.ship_indicator.setFixedSize(12, 12)
    self.ship_indicator.setStyleSheet(
        "QLabel { background-color: #666666; border-radius: 6px; border: 1px solid #444444; }"
    )
    ship_label = QLabel("CURRENT SHIP")
    ship_label.setStyleSheet("QLabel { color: #999999; font-size: 11px; background: transparent; border: none; }")
    ship_status.addWidget(self.ship_indicator)
    ship_status.addWidget(ship_label)
    ship_status.addStretch()
    
    self.current_ship_display = QLabel("No Ship")
    self.current_ship_display.setStyleSheet(
        "QLabel { color: #666666; font-size: 11px; font-weight: bold; background: transparent; border: none; }"
    )
    
    status_layout.addLayout(monitoring_status)
    status_layout.addLayout(api_status)
    status_layout.addLayout(twitch_status)
    status_layout.addLayout(game_mode_status)
    status_layout.addWidget(self.game_mode_display)
    status_layout.addLayout(ship_status)
    status_layout.addWidget(self.current_ship_display)
    
    sidebar_layout.addWidget(status_container)
    self.start_button = QPushButton("START MONITORING")
    self.start_button.setIcon(QIcon(resource_path("start_icon.png")))
    self.start_button.clicked.connect(self.toggle_monitoring)
    self.start_button.setStyleSheet(
        "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
        "border-radius: 4px; padding: 10px; font-weight: bold; font-size: 12px; "
        "margin: 5px 10px; }"
        "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #4a4a4a, stop:1 #303030); }"
        "QPushButton:pressed { background: #202020; }"
    )
    sidebar_layout.addWidget(self.start_button)
    self.rescan_button = QPushButton("FIND MISSED KILLS")
    self.rescan_button.setIcon(QIcon(resource_path("search_icon.png")))
    self.rescan_button.clicked.connect(self.on_rescan_button_clicked)
    self.rescan_button.setEnabled(False)
    self.rescan_button.setToolTip("You must start monitoring first before searching for missed kills")
    self.rescan_button.setStyleSheet(
        "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
        "border-radius: 4px; padding: 10px; font-weight: bold; font-size: 12px; "
        "margin: 5px 10px; }"
        "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #4a4a4a, stop:1 #303030); }"
        "QPushButton:pressed { background: #202020; }"        "QPushButton:disabled { background: #222222; color: #666666; }"
    )
    sidebar_layout.addWidget(self.rescan_button)
    
    # Check for Updates button
    self.update_button = QPushButton("CHECK FOR UPDATES")
    self.update_button.setIcon(QIcon(resource_path("update_icon.png")))
    self.update_button.clicked.connect(lambda: check_for_updates_ui(self))
    self.update_button.setToolTip("Check for the latest version of SCTool Tracker")
    self.update_button.setStyleSheet(
        "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
        "border-radius: 4px; padding: 10px; font-weight: bold; font-size: 12px; "
        "margin: 5px 10px; }"
        "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #4a4a4a, stop:1 #303030); }"
        "QPushButton:pressed { background: #202020; }"
    )
    sidebar_layout.addWidget(self.update_button)
    
    separator = QWidget()
    separator.setFixedHeight(1)
    separator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    separator.setStyleSheet("background-color: #2a2a2a; margin: 10px 15px;")
    sidebar_layout.addWidget(separator)
    self.nav_buttons = []

    killfeed_btn = self.create_nav_button("Killfeed", "dashboard")
    killfeed_btn.setCheckable(True)
    killfeed_btn.setChecked(True)
    self.nav_buttons.append(killfeed_btn)
    sidebar_layout.addWidget(killfeed_btn)

    killfeed_settings_btn = self.create_nav_button("Killfeed Settings", "killfeed_tab")
    killfeed_settings_btn.setCheckable(True)
    self.nav_buttons.append(killfeed_settings_btn)
    sidebar_layout.addWidget(killfeed_settings_btn)    
    api_btn = self.create_nav_button("API Settings", "api_tab") 
    api_btn.setCheckable(True)
    self.nav_buttons.append(api_btn)
    sidebar_layout.addWidget(api_btn)

    sound_btn = self.create_nav_button("Sound Settings", "sound_tab")
    sound_btn.setCheckable(True)
    self.nav_buttons.append(sound_btn)
    sidebar_layout.addWidget(sound_btn)
    
    twitch_btn = self.create_nav_button("Twitch Integration", "twitch_tab")
    twitch_btn.setCheckable(True)
    self.nav_buttons.append(twitch_btn)
    sidebar_layout.addWidget(twitch_btn)

    button_automation_btn = self.create_nav_button("Button Automation", "button_automation_tab")
    button_automation_btn.setCheckable(True)
    self.nav_buttons.append(button_automation_btn)
    sidebar_layout.addWidget(button_automation_btn)

    overlay_btn = self.create_nav_button("Game Overlay", "overlay_tab")
    overlay_btn.setCheckable(True)
    self.nav_buttons.append(overlay_btn)
    sidebar_layout.addWidget(overlay_btn)

    support_btn = self.create_nav_button("Support", "support_tab")
    support_btn.setCheckable(True)
    self.nav_buttons.append(support_btn)
    sidebar_layout.addWidget(support_btn)
    
    sidebar_layout.addStretch(1)
    main_layout.addWidget(sidebar)

    content_area = QWidget()
    content_area.setStyleSheet(
        "QWidget { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
        "stop:0 #1a1a1a, stop:1 #0d0d0d); "
        "border-top-left-radius: 0px; border-bottom-left-radius: 0px; "
        "border-top-right-radius: 10px; border-bottom-right-radius: 10px; }"
    )
    content_layout = QVBoxLayout(content_area)
    content_layout.setContentsMargins(15, 15, 15, 15)
    content_layout.setSpacing(15)

    self.stats_panel = QWidget()
    self.stats_panel.setStyleSheet(
        "QWidget { background-color: rgba(20, 20, 20, 0.8); border-radius: 8px; "
        "border: 1px solid #333333; }"
    )
    stats_layout = QHBoxLayout(self.stats_panel)
    stats_layout.setContentsMargins(15, 15, 15, 15)
    stats_layout.setSpacing(20)
    
    kill_stats = self.create_stat_card("KILLS", "0", "#66ff66")
    death_stats = self.create_stat_card("DEATHS", "0", "#f04747")
    kd_stats = self.create_stat_card("K/D RATIO", "--", "#00ccff")
    session_stats = self.create_stat_card("SESSION TIME", "00:00", "#ffffff")
    
    self.kill_count_display = kill_stats.findChild(QLabel, "stat_value")
    self.death_count_display = death_stats.findChild(QLabel, "stat_value")
    self.kd_ratio_display = kd_stats.findChild(QLabel, "stat_value")
    self.session_time_display = session_stats.findChild(QLabel, "stat_value")
    
    stats_layout.addWidget(kill_stats)
    stats_layout.addWidget(death_stats)
    stats_layout.addWidget(kd_stats)
    stats_layout.addWidget(session_stats)
    
    content_layout.addWidget(self.stats_panel)
    self.content_stack = QStackedWidget()
    killfeed_page = QWidget()
    killfeed_layout = QVBoxLayout(killfeed_page)
    killfeed_layout.setContentsMargins(0, 0, 0, 0)
    killfeed_layout.setSpacing(15)    
    kill_feed_container = QWidget()
    kill_feed_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    kill_feed_container.setStyleSheet(
        "QWidget { background-color: rgba(20, 20, 20, 0.8); border-radius: 8px; "
        "border: 1px solid #333333; }"
    )
    kill_feed_layout = QVBoxLayout(kill_feed_container)
    kill_feed_layout.setContentsMargins(15, 15, 15, 15)
    kill_feed_layout.setSpacing(10)
    kill_feed_header = QLabel("KILL FEED")
    kill_feed_header.setStyleSheet(
        "QLabel { color: #f0f0f0; font-size: 14px; font-weight: bold; "
        "background: transparent; border: none; }"
    )
    kill_feed_layout.addWidget(kill_feed_header)
    
    self.kill_display = QTextBrowser()
    self.kill_display.setReadOnly(True)
    self.kill_display.setOpenExternalLinks(True)
    self.kill_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.kill_display.setMinimumHeight(200)
    self.kill_display.setStyleSheet(
        "QTextBrowser { background-color: #121212; border: 1px solid #2a2a2a; border-radius: 8px; padding: 10px; }"
        "QTextBrowser QScrollBar:vertical { background: #1a1a1a; width: 12px; margin: 0px; }"
        "QTextBrowser QScrollBar::handle:vertical { background: #2a2a2a; min-height: 20px; border-radius: 6px; }"
        "QTextBrowser QScrollBar::handle:vertical:hover { background: #f04747; }"
        "QTextBrowser QScrollBar::add-line:vertical, QTextBrowser QScrollBar::sub-line:vertical { height: 0px; }"
        "QTextBrowser QScrollBar::add-page:vertical, QTextBrowser QScrollBar::sub-page:vertical { background: none; }"
    )
    kill_feed_layout.addWidget(self.kill_display, 1)
    
    killfeed_layout.addWidget(kill_feed_container, 1)

    killfeed_settings_page = QWidget()
    killfeed_settings_layout = QVBoxLayout(killfeed_settings_page)
    killfeed_settings_layout.setContentsMargins(0, 0, 0, 0)
    killfeed_settings_layout.setSpacing(15)

    tracking_card = QWidget()
    tracking_card.setStyleSheet(
        "QWidget { background-color: rgba(20, 20, 20, 0.8); border-radius: 8px; "
        "border: 1px solid #333333; }"
    )
    tracking_layout = QFormLayout(tracking_card)
    tracking_layout.setContentsMargins(20, 20, 20, 20)
    tracking_layout.setSpacing(15)
    tracking_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    
    tracking_header = QLabel("TRACKING CONFIGURATION")
    tracking_header.setStyleSheet(
        "QLabel { color: #2196F3; font-size: 18px; font-weight: bold; background: transparent; border: none; }"
    )
    tracking_layout.addRow(tracking_header)
    
    tracking_desc = QLabel("Configure the core settings for tracking your Star Citizen gameplay and kills.")
    tracking_desc.setStyleSheet(
        "QLabel { color: #cccccc; font-size: 13px; background: transparent; border: none; margin-bottom: 10px; }"
    )
    tracking_desc.setWordWrap(True)
    tracking_layout.addRow(tracking_desc)
    
    separator = QFrame()
    separator.setFrameShape(QFrame.HLine)
    separator.setStyleSheet("QFrame { color: #333333; background-color: #333333; border: none; max-height: 1px; }")
    tracking_layout.addRow(separator)

    log_path_label = QLabel("Game.log Path:")
    log_path_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
    
    log_path_container = QWidget()
    log_path_container.setStyleSheet("background: transparent; border: none;")
    log_path_layout = QHBoxLayout(log_path_container)
    log_path_layout.setContentsMargins(0, 0, 0, 0)
    log_path_layout.setSpacing(10)
    
    self.log_path_input = QLineEdit()
    self.log_path_input.setPlaceholderText("Enter path to your Game.log")
    self.log_path_input.setStyleSheet(
        "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 12px; "
        "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
        "QLineEdit:hover, QLineEdit:focus { border-color: #f04747; }"
    )
    
    browse_log_btn = QPushButton("Browse")
    browse_log_btn.setIcon(QIcon(resource_path("browse_icon.png")))
    browse_log_btn.setStyleSheet(
        "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
        "border: 1px solid #2a2a2a; border-radius: 4px; padding: 12px; }"
        "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
    )
    browse_log_btn.setFixedWidth(120)
    browse_log_btn.clicked.connect(self.browse_file)
    
    log_path_layout.addWidget(self.log_path_input)
    log_path_layout.addWidget(browse_log_btn)
    
    tracking_layout.addRow(log_path_label, log_path_container)

    log_help = QLabel("Path to your Star Citizen Game.log file (typically StarCitizen\\LIVE\\game.log)")
    log_help.setStyleSheet("QLabel { color: #aaaaaa; font-style: italic; background: transparent; border: none; }")
    log_help.setWordWrap(True)
    tracking_layout.addRow("", log_help)
    
    ship_label = QLabel("Current Ship:")
    ship_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
    
    self.ship_combo = QComboBox()
    self.ship_combo.setEditable(True)
    self.load_ship_options()

    self.ship_combo.currentTextChanged.connect(self.on_ship_combo_changed)
    
    if hasattr(self, 'current_ship_display'):
        current_ship = self.ship_combo.currentText() or "No Ship"
        self.update_current_ship_display(current_ship)

    self.ship_combo.setStyleSheet(
        "QComboBox { background-color: #1e1e1e; color: #f0f0f0; padding: 12px; "
        "border: 1px solid #2a2a2a; border-radius: 4px; padding-right: 20px; font-size: 14px; }"
        "QComboBox:hover { border-color: #f04747; }"
        "QComboBox::drop-down { border: none; width: 20px; }"
        "QComboBox::down-arrow { width: 0; height: 0; border-left: 5px solid transparent; "
        "   border-right: 5px solid transparent; border-top: 5px solid #f04747; margin-right: 8px; }"
        "QComboBox QAbstractItemView { background-color: #1e1e1e; color: #f0f0f0; "
        "selection-background-color: #f04747; selection-color: white; border: 1px solid #2a2a2a; }"
    )
    self.ship_combo.setMinimumWidth(300)
    
    tracking_layout.addRow(ship_label, self.ship_combo)

    ship_help = QLabel("Select the ship you're currently flying (included with kill data)")
    ship_help.setStyleSheet("QLabel { color: #aaaaaa; font-style: italic; background: transparent; border: none; }")
    ship_help.setWordWrap(True)
    tracking_layout.addRow("", ship_help)
    
    killfeed_settings_layout.addWidget(tracking_card)
    data_card = QWidget()
    data_card.setStyleSheet(
        "QWidget { background-color: rgba(20, 20, 20, 0.8); border-radius: 8px; "
        "border: 1px solid #333333; }"
    )
    data_layout = QVBoxLayout(data_card)
    data_layout.setContentsMargins(20, 20, 20, 20)
    data_layout.setSpacing(20)
    
    data_header = QLabel("DATA MANAGEMENT")
    data_header.setStyleSheet(
        "QLabel { color: #f0f0f0; font-size: 18px; font-weight: bold; background: transparent; border: none; }"
    )
    data_layout.addWidget(data_header)
    
    data_desc = QLabel("Export your kill logs and access application data files for backup or troubleshooting.")
    data_desc.setStyleSheet(
        "QLabel { color: #cccccc; font-size: 13px; background: transparent; border: none; }"
    )
    data_desc.setWordWrap(True)
    data_layout.addWidget(data_desc)

    data_buttons_container = QWidget()
    data_buttons_container.setStyleSheet("background: transparent; border: none;")
    data_buttons_layout = QHBoxLayout(data_buttons_container)
    data_buttons_layout.setContentsMargins(0, 0, 0, 0)
    data_buttons_layout.setSpacing(15)
    
    self.export_button = QPushButton("EXPORT LOGS")
    self.export_button.setIcon(QIcon(resource_path("export_icon.png")))
    self.export_button.clicked.connect(self.export_logs)
    self.export_button.setStyleSheet(
        "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
        "border-radius: 4px; padding: 12px 18px; font-weight: bold; font-size: 13px; }"
        "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #4a4a4a, stop:1 #303030); }"
        "QPushButton:pressed { background: #202020; }"
    )
    
    self.files_button = QPushButton("OPEN DATA FOLDER")
    self.files_button.setIcon(QIcon(resource_path("files_icon.png")))
    self.files_button.clicked.connect(self.open_tracker_files)
    self.files_button.setStyleSheet(
        "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
        "border-radius: 4px; padding: 12px 18px; font-weight: bold; font-size: 13px; }"
        "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #4a4a4a, stop:1 #303030); }"
        "QPushButton:pressed { background: #202020; }"
    )
    
    data_buttons_layout.addWidget(self.export_button)
    data_buttons_layout.addWidget(self.files_button)
    data_buttons_layout.addStretch()
    
    data_layout.addWidget(data_buttons_container)
    
    data_help = QLabel("• Export logs creates an HTML file with all recorded kills and deaths\n"
                      "• Data folder contains configuration files, logs, and saved kill records")
    data_help.setStyleSheet(
        "QLabel { color: #aaaaaa; font-size: 12px; background: transparent; border: none; }"
    )
    data_help.setWordWrap(True)
    data_layout.addWidget(data_help)
    
    killfeed_settings_layout.addWidget(data_card)
    preferences_card = QWidget()
    preferences_card.setStyleSheet(
        "QWidget { background-color: rgba(20, 20, 20, 0.8); border-radius: 8px; "
        "border: 1px solid #333333; }"
    )
    preferences_layout = QVBoxLayout(preferences_card)
    preferences_layout.setContentsMargins(20, 20, 20, 20)
    preferences_layout.setSpacing(15)
    
    preferences_header = QLabel("APPLICATION PREFERENCES")
    preferences_header.setStyleSheet(
        "QLabel { color: #f0f0f0; font-size: 18px; font-weight: bold; background: transparent; border: none; }"
    )
    preferences_layout.addWidget(preferences_header)

    preferences_desc = QLabel("Configure how SCTool Tracker behaves when starting and minimizing.")
    preferences_desc.setStyleSheet(
        "QLabel { color: #cccccc; font-size: 13px; background: transparent; border: none; }"
    )
    preferences_desc.setWordWrap(True)
    preferences_layout.addWidget(preferences_desc)
    
    tray_container = QWidget()
    tray_container.setStyleSheet("background: transparent; border: none;")
    tray_layout = QVBoxLayout(tray_container)
    tray_layout.setContentsMargins(0, 0, 0, 0)
    tray_layout.setSpacing(8)
    
    self.minimize_to_tray_checkbox = QCheckBox("Minimize to system tray")
    self.minimize_to_tray_checkbox.setChecked(self.minimize_to_tray)
    self.minimize_to_tray_checkbox.stateChanged.connect(self.on_minimize_to_tray_changed)
    self.minimize_to_tray_checkbox.setStyleSheet(
        "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; font-weight: 500; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 3px; }"
    )
    tray_layout.addWidget(self.minimize_to_tray_checkbox)
    
    tray_desc = QLabel("When minimized, the application will hide in the system tray instead of the taskbar")
    tray_desc.setStyleSheet(
        "QLabel { color: #999999; font-size: 12px; background: transparent; border: none; margin-left: 30px; }"
    )
    tray_desc.setWordWrap(True)
    tray_layout.addWidget(tray_desc)
    
    preferences_layout.addWidget(tray_container)
    
    autostart_container = QWidget()
    autostart_container.setStyleSheet("background: transparent; border: none;")
    autostart_layout = QVBoxLayout(autostart_container)
    autostart_layout.setContentsMargins(0, 0, 0, 0)
    autostart_layout.setSpacing(8)
    
    self.start_with_system_checkbox = QCheckBox("Start with Windows")
    self.start_with_system_checkbox.setChecked(self.start_with_system)
    self.start_with_system_checkbox.stateChanged.connect(self.on_start_with_system_changed)
    self.start_with_system_checkbox.setStyleSheet(
        "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; font-weight: 500; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 3px; }"
    )
    autostart_layout.addWidget(self.start_with_system_checkbox)
    
    autostart_desc = QLabel("Launch SCTool Tracker automatically when your computer starts")
    autostart_desc.setStyleSheet(
        "QLabel { color: #999999; font-size: 12px; background: transparent; border: none; margin-left: 30px; }"
    )
    autostart_desc.setWordWrap(True)
    autostart_layout.addWidget(autostart_desc)
    
    preferences_layout.addWidget(autostart_container)    
    killfeed_settings_layout.addWidget(preferences_card)
    killfeed_settings_layout.addStretch(1)

    api_page = QWidget()
    api_layout = QVBoxLayout(api_page)
    api_layout.setContentsMargins(0, 0, 0, 0)
    api_layout.setSpacing(15)
    
    api_card = QWidget()
    api_card.setStyleSheet(
        "QWidget { background-color: rgba(20, 20, 20, 0.8); border-radius: 8px; "
        "border: 1px solid #333333; }"
    )
    api_card_layout = QFormLayout(api_card)
    api_card_layout.setContentsMargins(20, 20, 20, 20)
    api_card_layout.setSpacing(15)
    api_card_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    
    api_header = QLabel("API CONNECTION")
    api_header.setStyleSheet(
        "QLabel { color: #00BCD4; font-size: 18px; font-weight: bold; background: transparent; border: none; }"
    )
    api_card_layout.addRow(api_header)
    
    api_desc = QLabel("Connect to the SCTool online service to track your kill statistics across sessions and compare with other players.")
    api_desc.setStyleSheet(
        "QLabel { color: #cccccc; font-size: 13px; background: transparent; border: none; }"
    )
    api_desc.setWordWrap(True)
    api_card_layout.addRow(api_desc)
    
    self.send_to_api_checkbox = QCheckBox("Send Kills to API")
    self.send_to_api_checkbox.setChecked(True)
    self.send_to_api_checkbox.setStyleSheet(
        "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 3px; }"
    )
    api_card_layout.addRow("", self.send_to_api_checkbox)
    
    api_key_label = QLabel("API Key:")
    api_key_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; }")
    self.api_key_input = QLineEdit()
    self.api_key_input.setPlaceholderText("Enter your API key here")

    self.api_key_input.setStyleSheet(
        "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 12px; "
        "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
        "QLineEdit:hover, QLineEdit:focus { border-color: #f04747; }"
    )
    self.api_key_input.setMinimumWidth(300)
    api_card_layout.addRow(api_key_label, self.api_key_input)
    
    api_help = QLabel()
    api_help.setText(
        "Your API key connects your account to the SCTool Tracker service.<br><br>"
        "<b>How to get an API key:</b><br>"
        "1. Visit <a href='https://starcitizentool.com/'>starcitizentool.com</a> and log in<br>"
        "2. You must be in a Discord server that has the SCTool Discord bot and had been given the member or allowed role<br>"
        "3. After login, select which Discord server to associate with your kills<br>"
        "4. Navigate to <a href='https://starcitizentool.com/kills/manage_api_keys'>starcitizentool.com/kills/manage_api_keys</a><br>"
        "5. Verify your in-game name<br>"
        "6. Generate an API key and paste it here<br>"
        "Instructions are also available <a href='https://www.youtube.com/watch?v=L62qvxopKak'>HERE</a>"
    )
    api_help.setStyleSheet(
        "QLabel { color: #aaaaaa; background: transparent; border: none; }"
        "QLabel a { color: #f04747; text-decoration: none; }"
        "QLabel a:hover { text-decoration: underline; }"
    )
    api_help.setTextFormat(Qt.RichText)
    api_help.setOpenExternalLinks(True)
    api_help.setWordWrap(True)
    api_card_layout.addRow("", api_help)
    
    api_link_container = QWidget()
    api_link_container.setStyleSheet("background: transparent; border: none;")
    api_link_layout = QHBoxLayout(api_link_container)
    api_link_layout.setContentsMargins(0, 10, 0, 0)
    
    api_link_button = QPushButton("MANAGE API KEYS")
    api_link_button.setIcon(QIcon(resource_path("link_icon.png")))
    api_link_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://starcitizentool.com/kills/manage_api_keys")))
    api_link_button.setStyleSheet(
        "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
        "border-radius: 4px; padding: 10px 16px; font-weight: bold; font-size: 13px; }"
        "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #4a4a4a, stop:1 #303030); }"
        "QPushButton:pressed { background: #202020; }"
    )
    api_link_button.setMaximumWidth(250)
    
    api_link_layout.addWidget(api_link_button)
    api_link_layout.addStretch()
    api_card_layout.addRow("", api_link_container)
    
    api_layout.addWidget(api_card)
    api_layout.addStretch(1)

    sound_page = QWidget()
    sound_layout = QVBoxLayout(sound_page)
    sound_layout.setContentsMargins(0, 0, 0, 0)
    sound_layout.setSpacing(15)
    
    sound_card = QWidget()
    sound_card.setStyleSheet(
        "QWidget { background-color: rgba(20, 20, 20, 0.8); border-radius: 8px; "
        "border: 1px solid #333333; }"
    )
    sound_card_layout = QFormLayout(sound_card)
    sound_card_layout.setContentsMargins(20, 20, 20, 20)
    sound_card_layout.setSpacing(15)
    sound_card_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    
    sound_header = QLabel("SOUND OPTIONS")
    sound_header.setStyleSheet(
        "QLabel { color: #FF9800; font-size: 18px; font-weight: bold; background: transparent; border: none; }"
    )
    sound_card_layout.addRow(sound_header)
    
    sound_desc = QLabel("Configure sound notifications for when you get kills in Star Citizen.")
    sound_desc.setStyleSheet(
        "QLabel { color: #cccccc; font-size: 13px; background: transparent; border: none; margin-bottom: 10px; }"
    )
    sound_desc.setWordWrap(True)
    sound_card_layout.addRow(sound_desc)
    
    sound_separator = QFrame()
    sound_separator.setFrameShape(QFrame.HLine)
    sound_separator.setStyleSheet("QFrame { color: #333333; background-color: #333333; border: none; max-height: 1px; }")
    sound_card_layout.addRow(sound_separator)
    
    self.kill_sound_checkbox = QCheckBox("Enable Kill Sound")
    self.kill_sound_checkbox.setChecked(False)
    self.kill_sound_checkbox.stateChanged.connect(self.on_kill_sound_toggled)
    self.kill_sound_checkbox.setStyleSheet(
        "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 3px; }"
    )
    sound_card_layout.addRow("", self.kill_sound_checkbox)
    
    sound_path_label = QLabel("Kill Sound File:")
    sound_path_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
    
    sound_path_container = QWidget()
    sound_path_container.setStyleSheet("background: transparent; border: none;")
    sound_path_layout = QHBoxLayout(sound_path_container)
    sound_path_layout.setContentsMargins(0, 0, 0, 0)
    sound_path_layout.setSpacing(10)
    
    self.kill_sound_path_input = QLineEdit()
    self.kill_sound_path_input.setText(self.kill_sound_path)
    self.kill_sound_path_input.setStyleSheet(
        "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 12px; "
        "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
        "QLineEdit:hover, QLineEdit:focus { border-color: #f04747; }"
    )
    
    sound_browse_btn = QPushButton("Browse")
    sound_browse_btn.setStyleSheet(
        "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
        "border: 1px solid #2a2a2a; border-radius: 4px; padding: 12px; }"
        "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
    )
    sound_browse_btn.setFixedWidth(120)
    sound_browse_btn.clicked.connect(self.on_kill_sound_file_browse)
    
    test_sound_btn = QPushButton("Test Sound")
    test_sound_btn.setIcon(QIcon(resource_path("volume_icon.png")))
    test_sound_btn.setStyleSheet(
        "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
        "border: 1px solid #2a2a2a; border-radius: 4px; padding: 12px; }"
        "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
    )
    test_sound_btn.setFixedWidth(120)
    test_sound_btn.clicked.connect(self.test_kill_sound)
    
    sound_path_layout.addWidget(self.kill_sound_path_input)
    sound_path_layout.addWidget(sound_browse_btn)
    sound_path_layout.addWidget(test_sound_btn)
    
    sound_card_layout.addRow(sound_path_label, sound_path_container)
    
    volume_label = QLabel("Volume:")
    volume_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
    
    volume_container = QWidget()
    volume_container.setStyleSheet("background: transparent; border: none;")
    volume_layout = QVBoxLayout(volume_container)
    volume_layout.setContentsMargins(0, 0, 0, 0)
    volume_layout.setSpacing(10)
    
    self.volume_slider = QSlider(Qt.Horizontal)
    self.volume_slider.setRange(0, 100)
    self.volume_slider.setValue(self.kill_sound_volume)
    self.volume_slider.valueChanged.connect(self.on_kill_sound_volume_changed)
    self.volume_slider.setStyleSheet(
        "QSlider::groove:horizontal { border: 1px solid #2a2a2a; height: 10px; "
        "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a1a1a, stop:1 #2a2a2a); "
        "margin: 2px 0; border-radius: 5px; }"
        "QSlider::handle:horizontal { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #f04747, stop:1 #d03737); border: 1px solid #2a2a2a; "
        "width: 20px; height: 20px; margin: -6px 0; border-radius: 10px; }"
        "QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        "stop:0 #d03737, stop:1 #f04747); border-radius: 5px; }"        "QSlider::handle:horizontal:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #ff5757, stop:1 #e04747); border: 1px solid #f04747; }"
    )
    volume_layout.addWidget(self.volume_slider)

    self.volume_percentage = QLabel(f"{self.kill_sound_volume}%")
    self.volume_percentage.setAlignment(Qt.AlignCenter)
    self.volume_percentage.setStyleSheet("QLabel { color: #f0f0f0; background: transparent; border: none; }")
    volume_layout.addWidget(self.volume_percentage)

    self.volume_slider.valueChanged.connect(lambda value: self.volume_percentage.setText(f"{value}%"))
    
    sound_card_layout.addRow(volume_label, volume_container)
    
    # Death Sound Section
    death_separator = QFrame()
    death_separator.setFrameShape(QFrame.HLine)
    death_separator.setStyleSheet("QFrame { color: #333333; background-color: #333333; border: none; max-height: 1px; }")
    sound_card_layout.addRow(death_separator)
    
    self.death_sound_checkbox = QCheckBox("Enable Death Sound")
    self.death_sound_checkbox.setChecked(False)
    self.death_sound_checkbox.stateChanged.connect(self.on_death_sound_toggled)
    self.death_sound_checkbox.setStyleSheet(
        "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 3px; }"
    )
    sound_card_layout.addRow("", self.death_sound_checkbox)
    
    death_sound_path_label = QLabel("Death Sound File:")
    death_sound_path_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
    
    death_sound_path_container = QWidget()
    death_sound_path_container.setStyleSheet("background: transparent; border: none;")
    death_sound_path_layout = QHBoxLayout(death_sound_path_container)
    death_sound_path_layout.setContentsMargins(0, 0, 0, 0)
    death_sound_path_layout.setSpacing(10)
    
    self.death_sound_path_input = QLineEdit()
    self.death_sound_path_input.setText(self.death_sound_path)
    self.death_sound_path_input.setStyleSheet(
        "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 12px; "
        "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
        "QLineEdit:hover, QLineEdit:focus { border-color: #f04747; }"
    )
    
    death_sound_browse_btn = QPushButton("Browse")
    death_sound_browse_btn.setStyleSheet(
        "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
        "border: 1px solid #2a2a2a; border-radius: 4px; padding: 12px; }"
        "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
    )
    death_sound_browse_btn.setFixedWidth(120)
    death_sound_browse_btn.clicked.connect(self.on_death_sound_file_browse)
    
    test_death_sound_btn = QPushButton("Test Sound")
    test_death_sound_btn.setIcon(QIcon(resource_path("volume_icon.png")))
    test_death_sound_btn.setStyleSheet(
        "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
        "border: 1px solid #2a2a2a; border-radius: 4px; padding: 12px; }"
        "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
    )
    test_death_sound_btn.setFixedWidth(120)
    test_death_sound_btn.clicked.connect(self.test_death_sound)
    
    death_sound_path_layout.addWidget(self.death_sound_path_input)
    death_sound_path_layout.addWidget(death_sound_browse_btn)
    death_sound_path_layout.addWidget(test_death_sound_btn)
    
    sound_card_layout.addRow(death_sound_path_label, death_sound_path_container)
    
    death_volume_label = QLabel("Death Sound Volume:")
    death_volume_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
    
    death_volume_container = QWidget()
    death_volume_container.setStyleSheet("background: transparent; border: none;")
    death_volume_layout = QVBoxLayout(death_volume_container)
    death_volume_layout.setContentsMargins(0, 0, 0, 0)
    death_volume_layout.setSpacing(10)
    
    self.death_volume_slider = QSlider(Qt.Horizontal)
    self.death_volume_slider.setRange(0, 100)
    self.death_volume_slider.setValue(self.death_sound_volume)
    self.death_volume_slider.valueChanged.connect(self.on_death_sound_volume_changed)
    self.death_volume_slider.setStyleSheet(
        "QSlider::groove:horizontal { border: 1px solid #2a2a2a; height: 10px; "
        "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a1a1a, stop:1 #2a2a2a); "
        "margin: 2px 0; border-radius: 5px; }"
        "QSlider::handle:horizontal { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #f04747, stop:1 #d03737); border: 1px solid #2a2a2a; "
        "width: 20px; height: 20px; margin: -6px 0; border-radius: 10px; }"
        "QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        "stop:0 #d03737, stop:1 #f04747); border-radius: 5px; }"
        "QSlider::handle:horizontal:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #ff5757, stop:1 #e04747); border: 1px solid #f04747; }"
    )
    death_volume_layout.addWidget(self.death_volume_slider)

    self.death_volume_percentage = QLabel(f"{self.death_sound_volume}%")
    self.death_volume_percentage.setAlignment(Qt.AlignCenter)
    self.death_volume_percentage.setStyleSheet("QLabel { color: #f0f0f0; background: transparent; border: none; }")
    death_volume_layout.addWidget(self.death_volume_percentage)

    self.death_volume_slider.valueChanged.connect(lambda value: self.death_volume_percentage.setText(f"{value}%"))
    
    sound_card_layout.addRow(death_volume_label, death_volume_container)
    
    sound_layout.addWidget(sound_card)
    sound_layout.addStretch(1)
    
    twitch_page = QWidget()
    twitch_layout = QVBoxLayout(twitch_page)
    twitch_layout.setContentsMargins(0, 0, 0, 0)
    twitch_layout.setSpacing(15)
    
    twitch_card = QWidget()
    twitch_card.setStyleSheet(
        "QWidget { background-color: rgba(20, 20, 20, 0.8); border-radius: 8px; "
        "border: 1px solid #333333; }"
    )
    twitch_card_layout = QFormLayout(twitch_card)
    twitch_card_layout.setContentsMargins(20, 20, 20, 20)
    twitch_card_layout.setSpacing(15)
    twitch_card_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    
    twitch_header = QLabel("TWITCH INTEGRATION")
    twitch_header.setStyleSheet(
        "QLabel { color: #9146FF; font-size: 18px; font-weight: bold; background: transparent; border: none; }"
    )
    twitch_card_layout.addRow(twitch_header)
    
    twitch_desc = QLabel("Connect your Twitch account to automatically create clips of your kills during your stream.")
    twitch_desc.setStyleSheet(
        "QLabel { color: #cccccc; font-size: 13px; background: transparent; border: none; }"
        )
    twitch_desc.setWordWrap(True)
    twitch_card_layout.addRow(twitch_desc)
    
    self.twitch_enabled_checkbox = QCheckBox("Enable Twitch Integration")
    self.twitch_enabled_checkbox.setChecked(False)
    self.twitch_enabled_checkbox.setStyleSheet(
        "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #9146FF; background-color: #9146FF; border-radius: 3px; }"
    )
    twitch_card_layout.addRow("", self.twitch_enabled_checkbox)
    
    self.auto_connect_twitch_checkbox = QCheckBox("Auto-connect to Twitch on launch")
    self.auto_connect_twitch_checkbox.setChecked(False)
    self.auto_connect_twitch_checkbox.setStyleSheet(
        "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #9146FF; background-color: #9146FF; border-radius: 3px; }"
    )
    twitch_card_layout.addRow("", self.auto_connect_twitch_checkbox)
    
    twitch_channel_label = QLabel("Twitch Channel:")
    twitch_channel_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
    
    self.twitch_channel_input = QLineEdit()
    self.twitch_channel_input.setPlaceholderText("Enter your Twitch channel name")
    self.twitch_channel_input.setStyleSheet(
        "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 12px; "
        "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
        "QLineEdit:hover, QLineEdit:focus { border-color: #9146FF; }"
    )
    self.twitch_channel_input.setMinimumWidth(300)
    
    twitch_card_layout.addRow(twitch_channel_label, self.twitch_channel_input)
    
    twitch_buttons = QWidget()
    twitch_buttons.setStyleSheet("background: transparent; border: none;")
    twitch_buttons_layout = QHBoxLayout(twitch_buttons)
    twitch_buttons_layout.setContentsMargins(0, 0, 0, 0)
    twitch_buttons_layout.setSpacing(10)
    
    self.twitch_connect_button = QPushButton("Connect Twitch")
    self.twitch_connect_button.clicked.connect(self.connect_to_twitch)
    self.twitch_connect_button.setStyleSheet(
        "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #9146FF, stop:1 #7a33e5); color: white; border: none; "
        "border-radius: 4px; padding: 12px; font-weight: bold; }"
        "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #a366ff, stop:1 #8a3bff); }"
        "QPushButton:pressed { background: #7a33e5; }"
    )
    
    self.twitch_disconnect_button = QPushButton("Disconnect Twitch")
    self.twitch_disconnect_button.clicked.connect(self.disconnect_from_twitch)
    self.twitch_disconnect_button.setStyleSheet(
        "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #3a3a3a, stop:1 #202020); color: white; border: none; "
        "border-radius: 4px; padding: 12px; font-weight: bold; }"
        "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #4a4a4a, stop:1 #303030); }"
        "QPushButton:pressed { background: #202020; }"
    )
    
    twitch_buttons_layout.addWidget(self.twitch_connect_button)
    twitch_buttons_layout.addWidget(self.twitch_disconnect_button)
    twitch_buttons_layout.addStretch()
    
    twitch_card_layout.addRow("", twitch_buttons)
    clip_section_label = QLabel("CLIP SETTINGS")
    clip_section_label.setStyleSheet(
        "QLabel { color: #9146FF; font-size: 16px; font-weight: bold; background: transparent; border: none; margin-top: 10px; }"
    )
    twitch_card_layout.addRow(clip_section_label)

    self.clip_creation_checkbox = QCheckBox("Create Twitch clips on kill")
    self.clip_creation_checkbox.setChecked(self.clip_creation_enabled)
    self.clip_creation_checkbox.stateChanged.connect(self.on_clip_creation_toggled)
    self.clip_creation_checkbox.setStyleSheet(
        "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #9146FF; background-color: #9146FF; border-radius: 3px; }"
    )

    twitch_card_layout.addRow("", self.clip_creation_checkbox)
    
    self.chat_posting_checkbox = QCheckBox("Post kills to Twitch chat")
    self.chat_posting_checkbox.setChecked(True)
    self.chat_posting_checkbox.stateChanged.connect(self.on_chat_posting_toggled)
    self.chat_posting_checkbox.setStyleSheet(
        "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #9146FF; background-color: #9146FF; border-radius: 3px; }"
    )
    twitch_card_layout.addRow("", self.chat_posting_checkbox)
    
    chat_message_label = QLabel("Customize Twitch chat message:")
    chat_message_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")

    self.twitch_message_input = QLineEdit()
    self.twitch_message_input.setPlaceholderText("E.g.: 🔫 {username} just killed {victim}! 🚀 {profile_url}")
    self.twitch_message_input.setText(self.twitch_chat_message_template)
    self.twitch_message_input.setStyleSheet(
        "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 12px; "
        "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
        "QLineEdit:hover, QLineEdit:focus { border-color: #9146FF; }"
    )
    self.twitch_message_input.setMinimumWidth(300)
    self.twitch_message_input.editingFinished.connect(self.on_twitch_message_changed)

    message_help = QLabel("Available placeholders: {username}, {victim}, {profile_url}")
    message_help.setStyleSheet("QLabel { color: #aaaaaa; font-style: italic; background: transparent; border: none; }")
    message_help.setWordWrap(True)

    twitch_card_layout.addRow(chat_message_label, self.twitch_message_input)
    twitch_card_layout.addRow("", message_help)

    clip_delay_label = QLabel("Delay after kill:")
    clip_delay_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
    
    clip_delay_container = QWidget()
    clip_delay_container.setStyleSheet("background: transparent; border: none;")
    clip_delay_layout = QHBoxLayout(clip_delay_container)
    clip_delay_layout.setContentsMargins(0, 0, 0, 0)
    clip_delay_layout.setSpacing(10)
    
    self.clip_delay_slider = QSlider(Qt.Horizontal)
    self.clip_delay_slider.setRange(0, 60)
    self.clip_delay_slider.setValue(self.twitch.clip_delay_seconds)
    self.clip_delay_slider.setStyleSheet(
        "QSlider::groove:horizontal { border: 1px solid #2a2a2a; height: 10px; "
        "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a1a1a, stop:1 #2a2a2a); "
        "margin: 2px 0; border-radius: 5px; }"
        "QSlider::handle:horizontal { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #9146FF, stop:1 #7a33e5); border: 1px solid #2a2a2a; "
        "width: 20px; height: 20px; margin: -6px 0; border-radius: 10px; }"
        "QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        "stop:0 #7a33e5, stop:1 #9146FF); border-radius: 5px; }"
        "QSlider::handle:horizontal:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #a366ff, stop:1 #8a3bff); border: 1px solid #9146FF; }"
    )
    
    self.clip_delay_value = QLabel(f"{self.twitch.clip_delay_seconds} seconds")
    self.clip_delay_value.setStyleSheet("QLabel { color: #ffffff; background: transparent; border: none; font-size: 14px; }")
    self.clip_delay_slider.valueChanged.connect(self.on_clip_delay_changed)
    
    clip_delay_layout.addWidget(self.clip_delay_slider)
    clip_delay_layout.addWidget(self.clip_delay_value)
    
    twitch_card_layout.addRow(clip_delay_label, clip_delay_container)
    note_label = QLabel("Note: Clip creation requires you to be actively streaming on Twitch")
    note_label.setStyleSheet("QLabel { color: #aaaaaa; font-style: italic; background: transparent; border: none; }")
    note_label.setWordWrap(True)
    twitch_card_layout.addRow("", note_label)
    
    twitch_layout.addWidget(twitch_card)
    twitch_layout.addStretch(1)
    
    overlay_page = QWidget()
    overlay_layout = QVBoxLayout(overlay_page)
    overlay_layout.setContentsMargins(0, 0, 0, 0)
    overlay_layout.setSpacing(15)
    
    overlay_card = QWidget()
    overlay_card.setStyleSheet(
        "QWidget { background-color: rgba(20, 20, 20, 0.8); border-radius: 8px; "
        "border: 1px solid #333333; }"
    )

    overlay_card_layout = QFormLayout(overlay_card)
    overlay_card_layout.setContentsMargins(20, 20, 20, 20)
    overlay_card_layout.setSpacing(15)
    overlay_card_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    
    overlay_header = QLabel("GAME OVERLAY")
    overlay_header.setStyleSheet("QLabel { color: #00ff41; font-size: 18px; font-weight: bold; background: transparent; border: none; }")

    overlay_card_layout.addRow(overlay_header)
    
    overlay_desc = QLabel("Configure the in-game overlay that displays your kill/death statistics in real-time while playing Star Citizen.")
    overlay_desc.setStyleSheet("QLabel { color: #cccccc; font-size: 13px; background: transparent; border: none; }")

    overlay_desc.setWordWrap(True)
    overlay_card_layout.addRow(overlay_desc)
    self.game_overlay = GameOverlay(None)
    self.game_overlay.parent_tracker = self
    self.overlay_settings = OverlayControlPanel(self.game_overlay, self)
    self.overlay_settings.overlay_toggled.connect(self.toggle_overlay)
    
    overlay_card_layout.addRow("", self.overlay_settings)
    
    overlay_layout.addWidget(overlay_card)
    
    support_page = QWidget()
    support_layout = QVBoxLayout(support_page)
    support_layout.setContentsMargins(0, 0, 0, 0)
    support_layout.setSpacing(15)
    
    support_card = QWidget()
    support_card.setStyleSheet(
        "QWidget { background-color: rgba(20, 20, 20, 0.8); border-radius: 8px; "
        "border: 1px solid #333333; }"
    )

    support_card_layout = QFormLayout(support_card)
    support_card_layout.setContentsMargins(20, 20, 20, 20)
    support_card_layout.setSpacing(15)
    support_card_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    
    support_header = QLabel("SUPPORT & HELP")
    support_header.setStyleSheet("QLabel { color: #4CAF50; font-size: 18px; font-weight: bold; background: transparent; border: none; }")
    support_card_layout.addRow(support_header)
    
    api_setup_header = QLabel("API Setup")
    api_setup_header.setStyleSheet("QLabel { color: #FFA726; font-size: 16px; font-weight: bold; background: transparent; border: none; margin-top: 15px; }")
    support_card_layout.addRow(api_setup_header)
    
    api_steps_text = """
        <b>Important Steps:</b><br><br>
        <b>1. Admin Setup:</b> An administrator in your Discord server must first configure the allowed member role within the SCTool Admin Config section.<br><br>
        <b>2. Login:</b> Ensure you are logged into SCTool on this website.<br><br>
        <b>3. Navigate:</b> Go to your Member Server section.<br><br>
        <b>4. Manage API:</b> Find and access the 'Manage API' section to set up your API key.<br><br>
        <b>Note:</b> You need a verified API key to use the Kill Feed feature.
    """
    
    api_steps_label = QLabel(api_steps_text)
    api_steps_label.setStyleSheet("QLabel { color: #cccccc; font-size: 13px; background: transparent; border: none; padding: 10px; }")
    api_steps_label.setWordWrap(True)
    support_card_layout.addRow(api_steps_label)

    help_header = QLabel("Need Help?")
    help_header.setStyleSheet("QLabel { color: #FFA726; font-size: 16px; font-weight: bold; background: transparent; border: none; margin-top: 15px; }")
    support_card_layout.addRow(help_header)

    video_btn = QPushButton("📺 Watch Setup Video")
    video_btn.setStyleSheet("""
        QPushButton {
            background-color: #FF6B6B;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #FF5252;
        }
        QPushButton:pressed {
            background-color: #E53935;
        }
    """)
    video_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.youtube.com/watch?v=d8SwnmVPuGI")))
    support_card_layout.addRow("", video_btn)

    discord_btn = QPushButton("💬 Join SCTool Discord")
    discord_btn.setStyleSheet("""
        QPushButton {
            background-color: #7289DA;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #5B6EAE;
        }
        QPushButton:pressed {
            background-color: #4E5D94;
        }
    """)
    discord_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://discord.gg/PCXmwGPZ94")))
    support_card_layout.addRow("", discord_btn)

    github_btn = QPushButton("📚 GitHub Documentation")
    github_btn.setStyleSheet("""
        QPushButton {
            background-color: #24292e;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1c2024;
        }
        QPushButton:pressed {
            background-color: #14171a;
        }    """)
    github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/calebv2/SCTool-Tracker/tree/main")))
    support_card_layout.addRow("", github_btn)

    support_dev_header = QLabel("Support Development")
    support_dev_header.setStyleSheet("QLabel { color: #FFA726; font-size: 16px; font-weight: bold; background: transparent; border: none; margin-top: 15px; }")
    support_card_layout.addRow(support_dev_header)

    patreon_btn = QPushButton("❤️ Support on Patreon")
    patreon_btn.setStyleSheet("""
        QPushButton {
            background-color: #F96854;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #E85D47;
        }
        QPushButton:pressed {
            background-color: #D7523A;
        }
    """)
    patreon_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://patreon.com/VenutoMan")))
    support_card_layout.addRow("", patreon_btn)

    kofi_btn = QPushButton("☕ Buy me a Coffee")
    kofi_btn.setStyleSheet("""
        QPushButton {
            background-color: #29ABE0;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #2196CC;
        }
        QPushButton:pressed {
            background-color: #1976B3;
        }
    """)
    kofi_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://ko-fi.com/sctool")))
    support_card_layout.addRow("", kofi_btn)

    version_label = QLabel("Ensure you have the latest version and stay up to date.")
    version_label.setStyleSheet("QLabel { color: #888888; font-size: 12px; background: transparent; border: none; margin-top: 10px; }")
    version_label.setWordWrap(True)
    support_card_layout.addRow(version_label)
    
    support_layout.addWidget(support_card)
    support_layout.addStretch(1)
    
    button_automation_page = QWidget()
    button_automation_layout = QVBoxLayout(button_automation_page)
    button_automation_layout.setContentsMargins(0, 0, 0, 0)
    button_automation_layout.setSpacing(15)
    
    button_automation_card = QWidget()
    button_automation_card.setStyleSheet(
        "QWidget { background-color: rgba(20, 20, 20, 0.8); border-radius: 8px; "
        "border: 1px solid #333333; }"
    )

    button_automation_card_layout = QFormLayout(button_automation_card)
    button_automation_card_layout.setContentsMargins(20, 20, 20, 20)
    button_automation_card_layout.setSpacing(15)
    button_automation_card_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    
    button_automation_header = QLabel("BUTTON AUTOMATION")
    button_automation_header.setStyleSheet("QLabel { color: #ff6b35; font-size: 18px; font-weight: bold; background: transparent; border: none; }")

    button_automation_card_layout.addRow(button_automation_header)
    
    button_automation_desc = QLabel("Automatically press customizable button combinations after kill events. "
                                    "Configure sequences of keys that will be pressed when you get a kill in Star Citizen."
    )

    button_automation_desc.setStyleSheet("QLabel { color: #cccccc; font-size: 13px; background: transparent; border: none; }")

    button_automation_desc.setWordWrap(True)
    button_automation_card_layout.addRow(button_automation_desc)

    self.button_automation_widget = ButtonAutomationWidget(self.button_automation, self)
    button_automation_card_layout.addRow("", self.button_automation_widget)
    
    button_automation_layout.addWidget(button_automation_card)
    button_automation_layout.addStretch()
    
    button_automation_scroll = QScrollArea()
    button_automation_scroll.setWidget(button_automation_page)
    button_automation_scroll.setWidgetResizable(True)
    button_automation_scroll.setFrameShape(QScrollArea.NoFrame)
    button_automation_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
    
    killfeed_scroll = QScrollArea()
    killfeed_scroll.setWidget(killfeed_page)
    killfeed_scroll.setWidgetResizable(True)
    killfeed_scroll.setFrameShape(QScrollArea.NoFrame)
    killfeed_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

    killfeed_settings_scroll = QScrollArea()
    killfeed_settings_scroll.setWidget(killfeed_settings_page)
    killfeed_settings_scroll.setWidgetResizable(True)
    killfeed_settings_scroll.setFrameShape(QScrollArea.NoFrame)
    killfeed_settings_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")    
    api_scroll = QScrollArea()
    api_scroll.setWidget(api_page)
    api_scroll.setWidgetResizable(True)
    api_scroll.setFrameShape(QScrollArea.NoFrame)
    api_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
    
    sound_scroll = QScrollArea()
    sound_scroll.setWidget(sound_page)
    sound_scroll.setWidgetResizable(True)
    sound_scroll.setFrameShape(QScrollArea.NoFrame)
    sound_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")    
    twitch_scroll = QScrollArea()
    twitch_scroll.setWidget(twitch_page)
    twitch_scroll.setWidgetResizable(True)
    twitch_scroll.setFrameShape(QScrollArea.NoFrame)
    twitch_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
    
    overlay_scroll = QScrollArea()
    overlay_scroll.setWidget(overlay_page)
    overlay_scroll.setWidgetResizable(True)
    overlay_scroll.setFrameShape(QScrollArea.NoFrame)    
    overlay_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

    support_scroll = QScrollArea()
    support_scroll.setWidget(support_page)
    support_scroll.setWidgetResizable(True)
    support_scroll.setFrameShape(QScrollArea.NoFrame)    
    support_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

    self.content_stack.addWidget(killfeed_scroll)
    self.content_stack.addWidget(killfeed_settings_scroll)
    
    self.content_stack.addWidget(api_scroll)
    self.content_stack.addWidget(sound_scroll)
    
    self.content_stack.addWidget(twitch_scroll)
    self.content_stack.addWidget(button_automation_scroll)
    self.content_stack.addWidget(overlay_scroll)
    self.content_stack.addWidget(support_scroll)
    self.content_stack.setCurrentIndex(0)
    
    for i, button in enumerate(self.nav_buttons):
        button.clicked.connect(lambda checked, index=i: self.switch_page(index))
    
    content_layout.addWidget(self.content_stack)
    main_layout.addWidget(content_area, stretch=1)
    main_widget.setLayout(main_layout)
    
    self.setCentralWidget(main_widget)
    
    screen = QApplication.primaryScreen()
    screen_size = screen.availableGeometry()
    
    screen_width = screen_size.width()
    screen_height = screen_size.height()
    
    if hasattr(self, 'scale_factor'):
        scale = self.scale_factor
    else:
        base_width = 1920
        base_height = 1080
        width_scale = screen_width / base_width
        height_scale = screen_height / base_height
        
        scale = min(width_scale, height_scale)
        if scale < 0.7:
            scale = 0.7
    
    min_width = int(600 * scale)
    min_height = int(500 * scale)
    self.setMinimumSize(min_width, min_height)
    
    self.session_start_time = None
    self.session_timer = QTimer()
    self.session_timer.timeout.connect(self.update_session_time)
    
    self.send_to_api_checkbox.stateChanged.connect(self.update_api_status)
    self.twitch_enabled_checkbox.stateChanged.connect(self.on_twitch_enabled_changed)
    self.auto_connect_twitch_checkbox.stateChanged.connect(self.on_auto_connect_twitch_changed)

def create_nav_button(self, text, obj_name=None):
    """Create a styled navigation button for the sidebar"""
    button = QPushButton(text)
    button.setStyleSheet(
        "QPushButton { text-align: left; padding: 12px 15px; font-weight: bold; color: #bbbbbb; "
        "background-color: transparent; border: none; border-left: 3px solid transparent; }"
        "QPushButton:hover { color: #ffffff; background-color: #222222; border-left: 3px solid #f04747; }"
        "QPushButton:checked { color: #ffffff; background-color: #252525; border-left: 3px solid #f04747; }"
    )
    if obj_name:
        button.setObjectName(obj_name)
    return button

def create_stat_card(self, label_text, value_text, value_color):
    """Create a styled stat card widget"""
    card = QWidget()
    card.setStyleSheet("border: none; background: #1a1a1a; border-radius: 8px;")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(5)
    
    value = QLabel(value_text)
    value.setObjectName("stat_value")
    value.setStyleSheet(f"QLabel {{ color: {value_color}; font-size: 24px; font-weight: bold; background: transparent; border: none; }}")
    value.setAlignment(Qt.AlignCenter)
    
    label = QLabel(label_text)
    label.setStyleSheet("QLabel { color: #aaaaaa; font-size: 12px; background: transparent; border: none; }")
    label.setAlignment(Qt.AlignCenter)
    
    layout.addWidget(value)
    layout.addWidget(label)
    
    return card

def switch_page(self, index):
    """Switch to the specified page in the stacked widget"""
    self.content_stack.setCurrentIndex(index)

    for i, button in enumerate(self.nav_buttons):
        button.setChecked(i == index)

def load_config(self) -> None:
    """Load configuration from config file"""
    try:
        if os.path.isfile(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    logging.warning("Configuration file is empty, using defaults")
                    return
                config = json.loads(content)

            self.api_key = config.get('api_key', '')
            self.api_key_input.setText(self.api_key)
            self.send_to_api_checkbox.setChecked(config.get('send_to_api', True))
            
            log_path = config.get('log_path', '')
            if log_path:
                self.log_path_input.setText(log_path)
            killer_ship = config.get('killer_ship', 'No Ship')
            if killer_ship != 'No Ship':
                index = self.ship_combo.findText(killer_ship)
                if index != -1:
                    self.ship_combo.setCurrentIndex(index)
                else:
                    self.ship_combo.addItem(killer_ship)
                    self.ship_combo.setCurrentIndex(self.ship_combo.count() - 1)
            
            self.kill_sound_enabled = config.get('kill_sound', False)
            self.kill_sound_checkbox.setChecked(self.kill_sound_enabled)
            kill_sound_path = config.get('kill_sound_path', '')
            if kill_sound_path and os.path.isfile(kill_sound_path):
                self.kill_sound_path = kill_sound_path
                self.kill_sound_path_input.setText(kill_sound_path)
            
            self.kill_sound_volume = config.get('kill_sound_volume', 100)
            self.volume_slider.setValue(self.kill_sound_volume)
            
            # Load death sound settings
            self.death_sound_enabled = config.get('death_sound', False)
            self.death_sound_checkbox.setChecked(self.death_sound_enabled)
            death_sound_path = config.get('death_sound_path', '')
            if death_sound_path and os.path.isfile(death_sound_path):
                self.death_sound_path = death_sound_path
                self.death_sound_path_input.setText(death_sound_path)
            
            self.death_sound_volume = config.get('death_sound_volume', 100)
            self.death_volume_slider.setValue(self.death_sound_volume)
            
            self.twitch_enabled = config.get('twitch_enabled', False)
            self.twitch_enabled_checkbox.setChecked(self.twitch_enabled)
            
            self.auto_connect_twitch = config.get('auto_connect_twitch', False)
            self.auto_connect_twitch_checkbox.setChecked(self.auto_connect_twitch)
            
            twitch_channel = config.get('twitch_channel', '')
            if twitch_channel:
                self.twitch_channel_input.setText(twitch_channel)
                self.twitch.set_broadcaster_name(twitch_channel)
                
            self.clip_creation_enabled = config.get('clip_creation_enabled', True)
            self.clip_creation_checkbox.setChecked(self.clip_creation_enabled)
            
            self.chat_posting_enabled = config.get('chat_posting_enabled', True)
            self.chat_posting_checkbox.setChecked(self.chat_posting_enabled)
            
            self.clips = config.get('clips', {})
            clip_delay = config.get('clip_delay_seconds', 0)
            self.twitch.set_clip_delay(clip_delay)
            self.clip_delay_slider.setValue(clip_delay)
            self.clip_delay_value.setText(f"{clip_delay} seconds")
            self.minimize_to_tray = config.get('minimize_to_tray', False)
            self.minimize_to_tray_checkbox.setChecked(self.minimize_to_tray)
            
            self.start_with_system = config.get('start_with_system', False)
            self.start_with_system_checkbox.setChecked(self.start_with_system)
            
            self.local_user_name = config.get('local_user_name', '')
            if self.local_user_name:
                self.user_display.setText(f"User: {self.local_user_name}")
                self.update_user_profile_image(self.local_user_name)
                self.rescan_button.setEnabled(True)
            
            if config.get('monitoring_active', False):
                QTimer.singleShot(500, self.toggle_monitoring)
                
            logging.info("Configuration loaded successfully")
    except json.JSONDecodeError as e:
        logging.error(f"Configuration file is corrupted (JSON error): {e}")
        logging.info("The config file will be recreated with default settings")
        try:
            os.remove(CONFIG_FILE)
            logging.info("Removed corrupted configuration file")
        except Exception as remove_error:
            logging.error(f"Could not remove corrupted config file: {remove_error}")
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        
def load_local_kills(self) -> None:
    """Load locally saved kills from JSON file"""
    try:
        if os.path.isfile(self.kills_local_file):
            with open(self.kills_local_file, 'r', encoding='utf-8') as f:
                self.local_kills = json.load(f)
                
            logging.info(f"Loaded {len(self.local_kills)} previous kills from local storage")
    except Exception as e:
        logging.error(f"Failed to load local kills: {e}")
        self.local_kills = {}

def styled_message_box(parent, title, text, icon=QMessageBox.Information, buttons=QMessageBox.Ok):
    """Create a stylish message box with consistent styling"""
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setIcon(icon)
    msg_box.setStandardButtons(buttons)
    msg_box.setTextFormat(Qt.RichText)
    msg_box.setTextInteractionFlags(Qt.TextBrowserInteraction)
    
    msg_box.setStyleSheet("""
        QMessageBox {
            background-color: #222222;
            color: #ffffff;
            border: 1px solid #444444;
        }
        QLabel {
            color: #ffffff;
            font-size: 14px;
        }
        QLabel a {
            color: #4CAF50;
            text-decoration: none;
        }
        QLabel a:hover {
            text-decoration: underline;
        }
        QPushButton {
            background-color: #2a2a2a;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 5px 15px;
            margin: 5px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #3a3a3a;
            border: 1px solid #777777;
        }
        QPushButton:pressed {
            background-color: #f04747;
        }
    """)
    
    return msg_box

def apply_styles(self) -> None:
    """Apply additional custom styles to the application"""
    scale_factor = 1.0
    if hasattr(self, 'scale_factor'):
        scale_factor = self.scale_factor
    
    padding = int(5 * scale_factor)
    border_radius = int(4 * scale_factor)
    
    app_style = f"""
        QMainWindow {{
            background-color: #0d0d0d;
        }}
        QToolTip {{
            background-color: #1e1e1e;
            color: #f0f0f0;
            border: 1px solid #3a3a3a;
            padding: {padding}px;
            border-radius: {border_radius}px;
        }}
        QPushButton {{
            padding: {padding}px {int(padding*2)}px;
        }}
        QLabel {{
            font-size: {int(12 * scale_factor)}px;
        }}
        QLineEdit, QComboBox, QTextEdit, QTextBrowser {{
            font-size: {int(12 * scale_factor)}px;
            padding: {int(4 * scale_factor)}px;
        }}
    """
    self.setStyleSheet(app_style)
    self.setWindowOpacity(0.98)
    
    dialog_style = """
        QDialog {
            background-color: #222222;
            color: #ffffff;
        }
        QDialog QLabel {
            color: #ffffff;
        }
        QDialog QPushButton {
            background-color: #2a2a2a;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 5px 15px;
            font-weight: bold;
        }
        QDialog QPushButton:hover {
            background-color: #3a3a3a;
        }
        QDialog QPushButton:pressed {
            background-color: #f04747;
        }
        QMessageBox {
            background-color: #222222;
        }
    """
    QApplication.instance().setStyleSheet(
        QApplication.instance().styleSheet() + dialog_style
    )

def check_for_updates_ui(self) -> None:
    """Check for newer versions of the application with minimum version support"""
    try:
        if hasattr(self, 'check_for_updates_with_optional') and callable(getattr(self, 'check_for_updates_with_optional')):
            self.check_for_updates_with_optional()
            return
            
        current_version = getattr(self, '__version__', '5.6.1')
        client_id = getattr(self, '__client_id__', 'sctool-tracker')
        user_agent = getattr(self, 'user_agent', 'SCTool-Tracker/5.6.1')
        
        update_url = "https://starcitizentool.com/api/v1/check-update"
        
        headers = {
            'User-Agent': user_agent,
            'X-Client-ID': client_id,
            'X-Client-Version': current_version
        }
        
        params = {
            'version': current_version
        }
        
        logging.info(f"Checking for updates... Current version: {current_version}")
        
        response = requests.get(update_url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            latest_version = data.get('latest_version')
            minimum_required_version = data.get('minimum_required_version')
            update_available = data.get('update_available', False)
            update_required = data.get('update_required', False)
            update_optional = data.get('update_optional', False)
            download_url = data.get('download_url', 'https://starcitizentool.com/download-sctool')
            
            logging.info(f"Update check response: latest={latest_version}, minimum={minimum_required_version}, "
                        f"available={update_available}, required={update_required}, optional={update_optional}")
            
            if update_required:
                show_forced_update_dialog(self, latest_version, minimum_required_version, download_url)
            elif update_optional:
                show_optional_update_dialog(self, latest_version, download_url)
            else:
                show_up_to_date_dialog(self, current_version)
        else:
            logging.warning(f"Update check failed with status code: {response.status_code}")
            show_update_check_failed_dialog(self)
            
    except Exception as e:
        logging.error(f"Error checking for updates: {e}")
        show_update_check_failed_dialog(self)

def show_forced_update_dialog(parent, latest_version: str, minimum_version: str, download_url: str) -> None:
    """Show dialog for forced updates (update required)"""
    current_version = getattr(parent, '__version__', '5.6.1')
    
    update_message = (
        f"<h3 style='color: #ff6b6b;'>🚨 Update Required</h3>"
        f"<p><b>Your version:</b> {current_version}</p>"
        f"<p><b>Latest version:</b> {latest_version}</p>"
        f"<p><b>Minimum required:</b> {minimum_version}</p>"
        f"<hr>"
        f"<p style='color: #ff6b6b;'><b>Your version is no longer supported.</b></p>"
        f"<p>You must update to continue using SCTool Tracker.</p>"
        f"<p>📖 <a href='https://github.com/calebv2/SCTool-Tracker/blob/main/README.md'>View changelog and release notes</a></p>"
    )

    msg_box = styled_message_box(
        parent, 
        "Update Required", 
        update_message, 
        QMessageBox.Critical,
        QMessageBox.NoButton
    )
    
    update_btn = msg_box.addButton("Update Now", QMessageBox.AcceptRole)
    exit_btn = msg_box.addButton("Exit Application", QMessageBox.RejectRole)
    
    msg_box.setDefaultButton(update_btn)
    msg_box.exec_()
    
    if msg_box.clickedButton() == update_btn:
        start_update_process(parent, latest_version, download_url)
    else:
        logging.info("User chose to exit instead of updating")
        QApplication.quit()

def show_optional_update_dialog(parent, latest_version: str, download_url: str) -> None:
    """Show dialog for optional updates"""
    current_version = getattr(parent, '__version__', '5.6.1')
    
    update_message = (
        f"<h3 style='color: #4CAF50;'>🎉 Update Available</h3>"
        f"<p><b>Your version:</b> {current_version}</p>"
        f"<p><b>Latest version:</b> {latest_version}</p>"
        f"<hr>"
        f"<p>A new version is available with improvements and new features!</p>"
        f"<p>📖 <a href='https://github.com/calebv2/SCTool-Tracker/blob/main/README.md'>View changelog and release notes</a></p>"
        f"<p><i>You can continue using your current version or update now.</i></p>"
    )

    msg_box = styled_message_box(
        parent, 
        "Update Available", 
        update_message, 
        QMessageBox.Information
    )
    
    update_btn = msg_box.addButton("Update Now", QMessageBox.AcceptRole)
    later_btn = msg_box.addButton("Remind Me Later", QMessageBox.ActionRole)
    skip_btn = msg_box.addButton("Skip This Version", QMessageBox.RejectRole)
    
    msg_box.setDefaultButton(update_btn)
    msg_box.exec_()
    
    if msg_box.clickedButton() == update_btn:
        start_update_process(parent, latest_version, download_url)
    elif msg_box.clickedButton() == later_btn:
        logging.info("User chose to be reminded later about update")
    else:
        logging.info("User chose to skip this version")

def show_up_to_date_dialog(parent, current_version: str) -> None:
    """Show dialog when application is up to date"""
    update_message = (
        f"<h3 style='color: #4CAF50;'>✅ You're Up to Date!</h3>"
        f"<p><b>Current version:</b> {current_version}</p>"
        f"<p>You have the latest version of SCTool Tracker.</p>"
        f"<p>No updates are needed at this time.</p>"
    )

    msg_box = styled_message_box(
        parent, 
        "Up to Date", 
        update_message, 
        QMessageBox.Information
    )
    msg_box.exec_()

def show_update_check_failed_dialog(parent) -> None:
    """Show dialog when update check fails"""
    update_message = (
        f"<h3 style='color: #ff9800;'>⚠️ Update Check Failed</h3>"
        f"<p>Unable to check for updates at this time.</p>"
        f"<p>Please check your internet connection and try again.</p>"
        f"<p>You can also visit <a href='https://starcitizentool.com/download-sctool'>starcitizentool.com</a> manually.</p>"
    )

    msg_box = styled_message_box(
        parent, 
        "Update Check Failed", 
        update_message, 
        QMessageBox.Warning
    )
    msg_box.exec_()

def start_update_process(parent, latest_version: str, download_url: str) -> None:
    """Start the update process"""
    try:
        if hasattr(parent, 'auto_update'):
            parent.auto_update(latest_version, download_url)
        else:
            logging.info(f"Opening download URL: {download_url}")
            QDesktopServices.openUrl(QUrl(download_url))
            
    except Exception as e:
        logging.error(f"Error starting update: {e}")
        QDesktopServices.openUrl(QUrl(download_url))

class CollapsibleSettingsPanel(QWidget):
    """Legacy class for backwards compatibility"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        
    def addWidget(self, widget):
        self.layout.addWidget(widget)