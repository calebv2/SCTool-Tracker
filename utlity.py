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
from language_manager import t, get_language_manager
from kill_parser import VERSION
from PyQt5.QtGui import QKeyEvent
from datetime import datetime, timedelta
from PyQt5.QtGui import QIcon, QDesktopServices, QPixmap, QPainter, QBrush, QPen, QColor, QPainterPath, QKeySequence
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QFormLayout, QComboBox, QCheckBox,
    QSlider, QFileDialog, QTextBrowser, QScrollArea, QFrame,
    QSizePolicy, QApplication, QStackedWidget, QMessageBox, QGroupBox,
    QGridLayout, QRadioButton, QButtonGroup
)

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
    try:
        from PyQt5.QtWebEngineWidgets import QWebEnginePage
    except Exception:
        QWebEnginePage = None
except ImportError:
    WEB_ENGINE_AVAILABLE = False
    print("QWebEngineView not available, falling back to QTextBrowser")

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
        "stop:0 #1a1a1a, stop:1 #0d0d0d); }"
    )
    main_layout = QHBoxLayout()
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)
    sidebar = QWidget()
    sidebar.setFixedWidth(220)
    sidebar.setStyleSheet(
        "QWidget { background-color: #151515; border-right: 1px solid #2a2a2a; }"
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
    
    self.user_display = QLabel(t("Not logged in"))
    self.user_display.setStyleSheet(
        "QLabel { color: #f0f0f0; font-size: 12px; background: transparent; border: none; }"
    )
    self.user_display.setAlignment(Qt.AlignCenter)
    logo_layout.addWidget(self.user_display)
    
    sidebar_layout.addWidget(logo_container)
    
    self.start_button = QPushButton(t("START MONITORING"))
    self.start_button.setIcon(QIcon(resource_path("play.png")))
    self.start_button.clicked.connect(self.toggle_monitoring)
    self.start_button.setToolTip("Start monitoring your Game.log file for kills and deaths")
    self.start_button.setStyleSheet(
        "QPushButton { "
        "background: rgba(76, 175, 80, 0.15); color: #4CAF50; border: 1px solid #4CAF50; "
        "border-radius: 6px; padding: 6px 12px; font-size: 11px; font-weight: bold; "
        "text-align: center; margin: 0px 8px; }"
        "QPushButton:hover { "
        "background: rgba(76, 175, 80, 0.25); border-color: #66BB6A; }"
        "QPushButton:pressed { "
        "background: #4CAF50; color: white; }"
    )
    sidebar_layout.addWidget(self.start_button)
    
    self.rescan_button = QPushButton("FIND MISSED KILLS")
    self.rescan_button.setIcon(QIcon(resource_path("missed.png")))
    self.rescan_button.clicked.connect(self.on_rescan_button_clicked)
    self.rescan_button.setEnabled(False)
    self.rescan_button.setToolTip("You must start monitoring first before searching for missed kills")
    self.rescan_button.setStyleSheet(
        "QPushButton { "
        "background: rgba(255, 152, 0, 0.15); color: #FF9800; border: 1px solid #FF9800; "
        "border-radius: 6px; padding: 6px 12px; font-size: 11px; font-weight: bold; "
        "text-align: center; margin: 0px 8px; }"
        "QPushButton:hover { "
        "background: rgba(255, 152, 0, 0.25); border-color: #FFB74D; }"
        "QPushButton:pressed { "
        "background: #FF9800; color: white; }"
        "QPushButton:disabled { "
        "background: rgba(102, 102, 102, 0.1); color: #666666; border-color: #666666; }"
    )
    sidebar_layout.addWidget(self.rescan_button)
    
    self.update_button = QPushButton("CHECK FOR UPDATES")
    self.update_button.setIcon(QIcon(resource_path("download.png")))
    self.update_button.clicked.connect(lambda: check_for_updates_ui(self))
    self.update_button.setToolTip("Check for the latest version of SCTool Tracker")
    self.update_button.setStyleSheet(
        "QPushButton { "
        "background: rgba(33, 150, 243, 0.15); color: #2196F3; border: 1px solid #2196F3; "
        "border-radius: 6px; padding: 6px 12px; font-size: 11px; font-weight: bold; "
        "text-align: center; margin: 0px 8px; }"
        "QPushButton:hover { "
        "background: rgba(33, 150, 243, 0.25); border-color: #64B5F6; }"
        "QPushButton:pressed { "
        "background: #2196F3; color: white; }"
    )
    sidebar_layout.addWidget(self.update_button)
    
    separator = QWidget()
    separator.setFixedHeight(1)
    separator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    separator.setStyleSheet("background-color: #2a2a2a; margin: 10px 15px;")
    sidebar_layout.addWidget(separator)
    self.nav_buttons = []

    killfeed_btn = self.create_nav_button(t("Killfeed"), "dashboard")
    killfeed_btn.setCheckable(True)
    killfeed_btn.setChecked(True)
    self.nav_buttons.append(killfeed_btn)
    sidebar_layout.addWidget(killfeed_btn)

    killfeed_settings_btn = self.create_nav_button(t("Killfeed Settings"), "killfeed_tab")
    killfeed_settings_btn.setCheckable(True)
    self.nav_buttons.append(killfeed_settings_btn)
    sidebar_layout.addWidget(killfeed_settings_btn)    
    api_btn = self.create_nav_button(t("API Settings"), "api_tab") 
    api_btn.setCheckable(True)
    self.nav_buttons.append(api_btn)
    sidebar_layout.addWidget(api_btn)

    sound_btn = self.create_nav_button(t("Sound Settings"), "sound_tab")
    sound_btn.setCheckable(True)
    self.nav_buttons.append(sound_btn)
    sidebar_layout.addWidget(sound_btn)
    
    twitch_btn = self.create_nav_button(t("Twitch Integration"), "twitch_tab")
    twitch_btn.setCheckable(True)
    self.nav_buttons.append(twitch_btn)
    sidebar_layout.addWidget(twitch_btn)

    button_automation_btn = self.create_nav_button(t("Button Automation"), "button_automation_tab")
    button_automation_btn.setCheckable(True)
    self.nav_buttons.append(button_automation_btn)
    sidebar_layout.addWidget(button_automation_btn)

    overlay_btn = self.create_nav_button(t("Game Overlay"), "overlay_tab")
    overlay_btn.setCheckable(True)
    self.nav_buttons.append(overlay_btn)
    sidebar_layout.addWidget(overlay_btn)

    support_btn = self.create_nav_button(t("Support"), "support_tab")
    support_btn.setCheckable(True)
    self.nav_buttons.append(support_btn)
    sidebar_layout.addWidget(support_btn)
    
    sidebar_layout.addStretch(1)
    main_layout.addWidget(sidebar)

    content_area = QWidget()
    content_area.setStyleSheet(
        "QWidget { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
        "stop:0 #1a1a1a, stop:1 #0d0d0d); }"
    )
    content_layout = QVBoxLayout(content_area)
    content_layout.setContentsMargins(15, 15, 15, 15)
    content_layout.setSpacing(15)

    self.stats_panel = QWidget()
    self.stats_panel.setStyleSheet(
        "QWidget { background-color: rgba(20, 20, 20, 0.8); "
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
    
    self.status_bar = QWidget()
    self.status_bar.setStyleSheet(
        "QWidget { background-color: rgba(20, 20, 20, 0.8); "
        "border: 1px solid #333333; border-radius: 8px; }"
    )
    status_bar_layout = QHBoxLayout(self.status_bar)
    status_bar_layout.setContentsMargins(15, 10, 15, 10)
    status_bar_layout.setSpacing(20)
    
    def create_horizontal_status_item(label_text, indicator_widget):
        item_container = QWidget()
        item_container.setStyleSheet("background: transparent; border: none;")
        item_layout = QHBoxLayout(item_container)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(8)
        
        indicator_widget.setFixedSize(10, 10)
        indicator_widget.setStyleSheet("QLabel { border-radius: 5px; }")
        
        label = QLabel(label_text)
        label.setStyleSheet(
            "QLabel { color: #cccccc; font-size: 11px; font-weight: 500; "
            "background: transparent; border: none; }"
        )
        
        item_layout.addWidget(indicator_widget)
        item_layout.addWidget(label)
        
        return item_container
    
    self.monitoring_indicator = QLabel()
    monitoring_status = create_horizontal_status_item("Monitoring", self.monitoring_indicator)
    status_bar_layout.addWidget(monitoring_status)
    self.update_monitor_indicator(False)
    
    self.api_indicator = QLabel()
    api_status = create_horizontal_status_item("API Connected", self.api_indicator)
    status_bar_layout.addWidget(api_status)
    self.update_api_indicator(False)
    
    self.twitch_indicator = QLabel()
    twitch_status = create_horizontal_status_item("Twitch Connected", self.twitch_indicator)
    status_bar_layout.addWidget(twitch_status)
    self.update_twitch_indicator(False)
    
    status_bar_layout.addStretch()
    
    content_layout.addWidget(self.status_bar)
    
    self.content_stack = QStackedWidget()
    killfeed_page = QWidget()
    killfeed_layout = QVBoxLayout(killfeed_page)
    killfeed_layout.setContentsMargins(0, 0, 0, 0)
    killfeed_layout.setSpacing(15)
    
    if WEB_ENGINE_AVAILABLE:
        self.kill_display = QWebEngineView()
        if QWebEnginePage is not None:
            class ExternalOpenWebPage(QWebEnginePage):
                def acceptNavigationRequest(self, url, _type, isMainFrame):
                    try:
                        if _type == QWebEnginePage.NavigationTypeLinkClicked:
                            QDesktopServices.openUrl(url)
                            return False
                    except Exception:
                        QDesktopServices.openUrl(url)
                        return False
                    return super().acceptNavigationRequest(url, _type, isMainFrame)

                def createWindow(self, _type):
                    from PyQt5.QtGui import QDesktopServices
                    def open_url_callback(url):
                        QDesktopServices.openUrl(url)
                    page = QWebEnginePage(self)
                    page.urlChanged.connect(open_url_callback)
                    return page

            self.kill_display.setPage(ExternalOpenWebPage(self.kill_display))
        self.kill_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.kill_display.setMinimumHeight(200)
        
        initial_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    background-color: rgba(20, 20, 20, 0.95);
                    color: white;
                    font-family: 'Consolas', monospace;
                    margin: 15px;
                    overflow-x: hidden;
                    border: 1px solid #333333;
                    border-radius: 8px;
                    min-height: calc(100vh - 50px);
                }
                ::-webkit-scrollbar {
                    width: 12px;
                }
                ::-webkit-scrollbar-track {
                    background: #1a1a1a;
                }
                ::-webkit-scrollbar-thumb {
                    background: #2a2a2a;
                    border-radius: 6px;
                }
                ::-webkit-scrollbar-thumb:hover {
                    background: #f04747;
                }
            </style>
        </head>
        <body>
            <div id="content"></div>
            <script>
                function appendHTML(html) {
                    document.getElementById('content').innerHTML += html;
                    window.scrollTo(0, document.body.scrollHeight);
                }
                function setHTML(html) {
                    document.getElementById('content').innerHTML = html;
                }
                function clearContent() {
                    document.getElementById('content').innerHTML = '';
                }
            </script>
        </body>
        </html>
        """
        self.kill_display.setHtml(initial_html)
        self.kill_display.setStyleSheet("""
            QWebEngineView {
                background-color: rgba(20, 20, 20, 0.8);
                border: 1px solid #333333;
                border-radius: 8px;
            }
        """)
        
    else:
        self.kill_display = QTextBrowser()
        self.kill_display.setReadOnly(True)
        self.kill_display.setOpenExternalLinks(True)
        self.kill_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.kill_display.setMinimumHeight(200)
        self.kill_display.setStyleSheet(
            "QTextBrowser { background-color: rgba(20, 20, 20, 0.8); border: 1px solid #333333; border-radius: 8px; padding: 15px; }"
            "QTextBrowser QScrollBar:vertical { background: #1a1a1a; width: 12px; margin: 0px; }"
            "QTextBrowser QScrollBar::handle:vertical { background: #2a2a2a; min-height: 20px; border-radius: 6px; }"
            "QTextBrowser QScrollBar::handle:vertical:hover { background: #f04747; }"
            "QTextBrowser QScrollBar::add-line:vertical, QTextBrowser QScrollBar::sub-line:vertical { height: 0px; }"
            "QTextBrowser QScrollBar::add-page:vertical, QTextBrowser QScrollBar::sub-page:vertical { background: none; }"
        )
    killfeed_layout.addWidget(self.kill_display, 1)
    killfeed_layout.addStretch(0)
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
    
    tracking_header = QLabel(t("TRACKING CONFIGURATION"))
    tracking_header.setStyleSheet(
        "QLabel { color: #2196F3; font-size: 18px; font-weight: bold; background: transparent; border: none; }"
    )
    tracking_layout.addRow(tracking_header)
    
    tracking_desc = QLabel(t("Configure the core settings for tracking your Star Citizen gameplay and kills."))
    tracking_desc.setStyleSheet(
        "QLabel { color: #cccccc; font-size: 13px; background: transparent; border: none; margin-bottom: 10px; }"
    )
    tracking_desc.setWordWrap(True)
    tracking_layout.addRow(tracking_desc)
    
    separator = QFrame()
    separator.setFrameShape(QFrame.HLine)
    separator.setStyleSheet("QFrame { color: #333333; background-color: #333333; border: none; max-height: 1px; }")
    tracking_layout.addRow(separator)

    log_path_label = QLabel(t("Game.log Path:"))
    log_path_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
    
    log_path_container = QWidget()
    log_path_container.setStyleSheet("background: transparent; border: none;")
    log_path_layout = QHBoxLayout(log_path_container)
    log_path_layout.setContentsMargins(0, 0, 0, 0)
    log_path_layout.setSpacing(10)
    
    self.log_path_input = QLineEdit()
    self.log_path_input.setPlaceholderText(t("Enter path to your Game.log"))
    self.log_path_input.setStyleSheet(
        "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 12px; "
        "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
        "QLineEdit:hover, QLineEdit:focus { border-color: #f04747; }"
    )
    
    browse_log_btn = QPushButton(t("Browse"))
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

    log_help = QLabel(t("Path to your Star Citizen Game.log file (typically StarCitizen\\LIVE\\game.log)"))
    log_help.setStyleSheet("QLabel { color: #aaaaaa; font-style: italic; background: transparent; border: none; }")
    log_help.setWordWrap(True)
    tracking_layout.addRow("", log_help)
    
    ship_container = QWidget()
    ship_container.setStyleSheet("background: transparent; border: none;")
    ship_layout = QHBoxLayout(ship_container)
    ship_layout.setContentsMargins(0, 0, 0, 0)
    ship_layout.setSpacing(15)
    
    ship_label = QLabel(t("Current Ship:"))
    ship_label.setStyleSheet("QLabel { color: #ffffff; font-weight: 500; background: transparent; border: none; font-size: 14px; }")
    ship_label.setMinimumWidth(80)
    ship_layout.addWidget(ship_label)
    
    self.ship_combo = QComboBox()
    self.ship_combo.setEditable(True)
    self.load_ship_options()

    self.ship_combo.currentTextChanged.connect(self.on_ship_combo_changed)
    
    if hasattr(self, 'current_ship_display'):
        current_ship = self.ship_combo.currentText() or "No Ship"
        self.update_current_ship_display(current_ship)

    self.ship_combo.setStyleSheet("""
        QComboBox {
            background-color: #1e1e1e;
            color: #f0f0f0;
            padding: 12px 16px;
            border: 1px solid #2a2a2a;
            border-radius: 4px;
            font-size: 14px;
            min-width: 200px;
            max-width: 300px;
            min-height: 20px;
        }
        QComboBox:hover, QComboBox:focus {
            border-color: #f04747;
        }
        QComboBox::drop-down {
            border: none;
            width: 30px;
            border-left: 1px solid #2a2a2a;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
            background-color: #2a2a2a;
        }
        QComboBox::drop-down:hover {
            background-color: #f04747;
        }
        QComboBox::down-arrow {
            image: none;
            border: none;
            width: 0px;
            height: 0px;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #f0f0f0;
            margin: 0px;
        }
        QComboBox QAbstractItemView {
            background-color: #1e1e1e;
            color: #f0f0f0;
            border: 2px solid #f04747;
            border-radius: 4px;
            selection-background-color: #f04747;
            selection-color: white;
            padding: 4px;
            min-width: 250px;
            max-height: 300px;
            outline: 0px;
            show-decoration-selected: 1;
        }
        QComboBox QAbstractItemView::item {
            padding: 8px 12px;
            border: none;
            background-color: transparent;
            min-height: 20px;
        }
        QComboBox QAbstractItemView::item:hover {
            background-color: #2a2a2a;
            color: #ffffff;
        }
        QComboBox QAbstractItemView::item:selected {
            background-color: #f04747;
            color: white;
        }
    """)
    
    self.ship_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    self.ship_combo.setFixedWidth(250)
    
    ship_layout.addWidget(self.ship_combo, 0)
    ship_layout.addStretch(1)
    
    tracking_layout.addRow("", ship_container)

    ship_help = QLabel(t("Select the ship you're currently flying (included with kill data)"))
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
    
    data_header = QLabel(t("DATA MANAGEMENT"))
    data_header.setStyleSheet(
        "QLabel { color: #f0f0f0; font-size: 18px; font-weight: bold; background: transparent; border: none; }"
    )
    data_layout.addWidget(data_header)
    
    data_desc = QLabel(t("Export your kill logs and access application data files for backup or troubleshooting."))
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
    
    self.export_button = QPushButton(t("EXPORT LOGS"))
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
    
    self.files_button = QPushButton(t("OPEN DATA FOLDER"))
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
    
    data_help = QLabel(t("• Export logs creates an HTML file with all recorded kills and deaths\\n• Data folder contains configuration files, logs, and saved kill records"))
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
    
    preferences_header = QLabel(t("APPLICATION PREFERENCES"))
    preferences_header.setStyleSheet(
        "QLabel { color: #f0f0f0; font-size: 18px; font-weight: bold; background: transparent; border: none; }"
    )
    preferences_layout.addWidget(preferences_header)

    preferences_desc = QLabel(t("Configure how SCTool Tracker behaves when starting and minimizing."))
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
    
    self.minimize_to_tray_checkbox = QCheckBox(t("Minimize to system tray"))
    self.minimize_to_tray_checkbox.setChecked(self.minimize_to_tray)
    self.minimize_to_tray_checkbox.stateChanged.connect(self.on_minimize_to_tray_changed)
    self.minimize_to_tray_checkbox.setStyleSheet(
        "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; font-weight: 500; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 3px; }"
    )
    tray_layout.addWidget(self.minimize_to_tray_checkbox)
    
    tray_desc = QLabel(t("When minimized, the application will hide in the system tray instead of the taskbar"))
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
    
    self.start_with_system_checkbox = QCheckBox(t("Start with Windows"))
    self.start_with_system_checkbox.setChecked(self.start_with_system)
    self.start_with_system_checkbox.stateChanged.connect(self.on_start_with_system_changed)
    self.start_with_system_checkbox.setStyleSheet(
        "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; font-weight: 500; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 3px; }"
    )
    autostart_layout.addWidget(self.start_with_system_checkbox)
    
    autostart_desc = QLabel(t("Launch SCTool Tracker automatically when your computer starts"))
    autostart_desc.setStyleSheet(
        "QLabel { color: #999999; font-size: 12px; background: transparent; border: none; margin-left: 30px; }"
    )
    autostart_desc.setWordWrap(True)
    autostart_layout.addWidget(autostart_desc)
    
    preferences_layout.addWidget(autostart_container)
    
    language_container = QWidget()
    language_container.setStyleSheet("background: transparent; border: none;")
    language_layout = QVBoxLayout(language_container)
    language_layout.setContentsMargins(0, 0, 0, 0)
    language_layout.setSpacing(8)
    
    self.language_selector_container = language_container
    self.language_selector_layout = language_layout
    
    preferences_layout.addWidget(language_container)
    
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
    
    api_header = QLabel(t("API CONNECTION"))
    api_header.setStyleSheet(
        "QLabel { color: #00BCD4; font-size: 18px; font-weight: bold; background: transparent; border: none; }"
    )
    api_card_layout.addRow(api_header)
    
    api_desc = QLabel(t("Connect to the SCTool online service to track your kill statistics across sessions and compare with other players."))
    api_desc.setStyleSheet(
        "QLabel { color: #cccccc; font-size: 13px; background: transparent; border: none; }"
    )
    api_desc.setWordWrap(True)
    api_card_layout.addRow(api_desc)
    
    self.send_to_api_checkbox = QCheckBox(t("Send Kills to API"))
    self.send_to_api_checkbox.setChecked(True)
    self.send_to_api_checkbox.setStyleSheet(
        "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 3px; }"
    )
    api_card_layout.addRow("", self.send_to_api_checkbox)
    
    api_key_label = QLabel(t("API Key:"))
    api_key_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; }")
    self.api_key_input = QLineEdit()
    self.api_key_input.setPlaceholderText(t("Enter your API key here"))

    self.api_key_input.setStyleSheet(
        "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 12px; "
        "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
        "QLineEdit:hover, QLineEdit:focus { border-color: #f04747; }"
    )
    self.api_key_input.setMinimumWidth(300)
    api_card_layout.addRow(api_key_label, self.api_key_input)
    
    self.disable_ssl_verification_checkbox = QCheckBox(t("⚠️ Disable SSL Certificate Verification (NOT RECOMMENDED)"))
    self.disable_ssl_verification_checkbox.setChecked(False)
    self.disable_ssl_verification_checkbox.setVisible(False)
    self.disable_ssl_verification_checkbox.stateChanged.connect(self.on_ssl_verification_changed)
    self.disable_ssl_verification_checkbox.setStyleSheet(
        "QCheckBox { color: #ff9800; spacing: 10px; background: transparent; border: none; font-size: 14px; font-weight: bold; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #ff9800; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #ff6b6b; background-color: #ff6b6b; border-radius: 3px; }"
    )
    
    ssl_warning_label = QLabel(
        "<span style='color: #ff6b6b; font-weight: bold;'>⚠️ WARNING:</span> "
        "Only use this if you have SSL certificate verification issues and have tried all other solutions. "
        "This reduces security and should be temporary. "
        "<b>Always fix your system configuration instead of using this option.</b>"
    )
    ssl_warning_label.setStyleSheet(
        "QLabel { color: #ff9800; background: rgba(255, 107, 107, 0.1); border: 1px solid #ff6b6b; "
        "border-radius: 4px; padding: 8px; font-size: 12px; }"
    )
    ssl_warning_label.setWordWrap(True)
    ssl_warning_label.setVisible(False)
    
    self.ssl_warning_container = QWidget()
    self.ssl_warning_container.setStyleSheet("background: transparent; border: none;")
    ssl_warning_layout = QVBoxLayout(self.ssl_warning_container)
    ssl_warning_layout.setContentsMargins(0, 0, 0, 0)
    ssl_warning_layout.setSpacing(5)
    ssl_warning_layout.addWidget(self.disable_ssl_verification_checkbox)
    ssl_warning_layout.addWidget(ssl_warning_label)
    self.ssl_warning_container.setVisible(False)
    
    api_card_layout.addRow("", self.ssl_warning_container)
    
    api_help = QLabel()
    api_help.setStyleSheet(
        "QLabel { color: #aaaaaa; background: transparent; border: none; }"
        "QLabel a { color: #f04747; text-decoration: none; }"
        "QLabel a:hover { text-decoration: underline; }"
    )
    api_help.setTextFormat(Qt.RichText)
    api_help.setOpenExternalLinks(True)
    api_help.setWordWrap(True)
    
    instructions_text = t('Instructions are also available HERE')
    if 'HERE' in instructions_text:
        base_text = instructions_text.replace('HERE', '')
        here_link = f'{base_text}<a href="{t("https://www.youtube.com/watch?v=L62qvxopKak")}" style="color: #f04747; text-decoration: underline;">HERE</a>'
    else:
        here_link = f'{instructions_text} <a href="{t("https://www.youtube.com/watch?v=L62qvxopKak")}" style="color: #f04747; text-decoration: underline;">HERE</a>'
    
    initial_api_help_text = (
        f"<b>{t('How to get an API key:')}</b><br><br>"
        f"{t('1. Visit starcitizentool.com and log in')}<br>"
        f"{t('2. You must be in a Discord server that has the SCTool Discord bot and had been given the member or allowed role')}<br>"
        f"{t('3. After login, select which Discord server to associate with your kills')}<br>"
        f"{t('4. Navigate to starcitizentool.com/kills/manage_api_keys')}<br>"
        f"{t('5. Verify your in-game name')}<br>"
        f"{t('6. Generate an API key and paste it here')}<br><br>"
        f"{here_link}"
    )
    api_help.setText(initial_api_help_text)
    
    self.api_help_label = api_help
    api_card_layout.addRow("", api_help)
    
    api_link_container = QWidget()
    api_link_container.setStyleSheet("background: transparent; border: none;")
    api_link_layout = QHBoxLayout(api_link_container)
    api_link_layout.setContentsMargins(0, 10, 0, 0)
    
    api_link_button = QPushButton(t("MANAGE API KEYS"))
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
    
    sound_header = QLabel(t("SOUND OPTIONS"))
    sound_header.setStyleSheet(
        "QLabel { color: #FF9800; font-size: 18px; font-weight: bold; background: transparent; border: none; }"
    )
    sound_card_layout.addRow(sound_header)
    
    sound_desc = QLabel(t("Configure sound notifications for when you get kills in Star Citizen."))
    sound_desc.setStyleSheet(
        "QLabel { color: #cccccc; font-size: 13px; background: transparent; border: none; margin-bottom: 10px; }"
    )
    sound_desc.setWordWrap(True)
    sound_card_layout.addRow(sound_desc)
    
    sound_separator = QFrame()
    sound_separator.setFrameShape(QFrame.HLine)
    sound_separator.setStyleSheet("QFrame { color: #333333; background-color: #333333; border: none; max-height: 1px; }")
    sound_card_layout.addRow(sound_separator)
    
    self.kill_sound_checkbox = QCheckBox(t("Enable Kill Sound"))
    self.kill_sound_checkbox.setChecked(False)
    self.kill_sound_checkbox.stateChanged.connect(self.on_kill_sound_toggled)
    self.kill_sound_checkbox.setStyleSheet(
        "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 3px; }"
    )
    sound_card_layout.addRow("", self.kill_sound_checkbox)
    
    kill_mode_label = QLabel(t("Kill Sound Mode:"))
    kill_mode_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
    
    kill_mode_container = QWidget()
    kill_mode_container.setStyleSheet("background: transparent; border: none;")
    kill_mode_layout = QVBoxLayout(kill_mode_container)
    kill_mode_layout.setContentsMargins(0, 0, 0, 0)
    kill_mode_layout.setSpacing(5)
    
    self.kill_sound_mode_group = QButtonGroup()
    
    self.kill_single_file_radio = QRadioButton(t("Single Sound File"))
    self.kill_single_file_radio.setChecked(True)
    self.kill_single_file_radio.setStyleSheet(
        "QRadioButton { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 13px; }"
        "QRadioButton::indicator { width: 16px; height: 16px; }"
        "QRadioButton::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 8px; }"
        "QRadioButton::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 8px; }"
    )
    
    self.kill_random_folder_radio = QRadioButton(t("Random from Folder"))
    self.kill_random_folder_radio.setStyleSheet(
        "QRadioButton { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 13px; }"
        "QRadioButton::indicator { width: 16px; height: 16px; }"
        "QRadioButton::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 8px; }"
        "QRadioButton::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 8px; }"
    )
    
    self.kill_sound_mode_group.addButton(self.kill_single_file_radio, 0)
    self.kill_sound_mode_group.addButton(self.kill_random_folder_radio, 1)
    self.kill_sound_mode_group.buttonClicked.connect(self.on_kill_sound_mode_changed)
    
    kill_mode_layout.addWidget(self.kill_single_file_radio)
    kill_mode_layout.addWidget(self.kill_random_folder_radio)
    
    sound_card_layout.addRow(kill_mode_label, kill_mode_container)
    
    sound_path_label = QLabel(t("Kill Sound File:"))
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
    self.kill_sound_path_input.setMinimumWidth(300)
    
    self.kill_sound_browse_btn = QPushButton(t("Browse"))
    self.kill_sound_browse_btn.setStyleSheet(
        "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
        "border: 1px solid #2a2a2a; border-radius: 4px; padding: 12px; }"
        "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
        "QPushButton:disabled { background-color: #0a0a0a; color: #666666; border-color: #1a1a1a; }"
    )
    self.kill_sound_browse_btn.setFixedWidth(120)
    self.kill_sound_browse_btn.setFixedHeight(44)
    self.kill_sound_browse_btn.clicked.connect(self.on_kill_sound_file_browse)
    
    self.kill_sound_test_btn = QPushButton(t("Test Sound"))
    self.kill_sound_test_btn.setIcon(QIcon(resource_path("volume_icon.png")))
    self.kill_sound_test_btn.setStyleSheet(
        "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
        "border: 1px solid #2a2a2a; border-radius: 4px; padding: 12px; }"
        "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
        "QPushButton:disabled { background-color: #0a0a0a; color: #666666; border-color: #1a1a1a; }"
    )
    self.kill_sound_test_btn.setFixedWidth(120)
    self.kill_sound_test_btn.setFixedHeight(44)
    self.kill_sound_test_btn.clicked.connect(self.test_kill_sound)
    
    sound_path_layout.addWidget(self.kill_sound_path_input)
    sound_path_layout.addWidget(self.kill_sound_browse_btn)
    sound_path_layout.addWidget(self.kill_sound_test_btn)
    
    sound_card_layout.addRow(sound_path_label, sound_path_container)
    
    kill_folder_label = QLabel(t("Kill Sound Folder:"))
    kill_folder_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
    
    kill_folder_container = QWidget()
    kill_folder_container.setStyleSheet("background: transparent; border: none;")
    kill_folder_layout = QHBoxLayout(kill_folder_container)
    kill_folder_layout.setContentsMargins(0, 0, 0, 0)
    kill_folder_layout.setSpacing(10)
    
    self.kill_sound_folder_input = QLineEdit()
    self.kill_sound_folder_input.setText(self.kill_sound_folder)
    self.kill_sound_folder_input.setStyleSheet(
        "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 12px; "
        "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
        "QLineEdit:hover, QLineEdit:focus { border-color: #f04747; }"
    )
    self.kill_sound_folder_input.setMinimumWidth(300)
    self.kill_sound_folder_input.setEnabled(False)
    
    kill_folder_browse_btn = QPushButton(t("Browse Folder"))
    kill_folder_browse_btn.setStyleSheet(
        "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
        "border: 1px solid #2a2a2a; border-radius: 4px; padding: 12px; }"
        "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
        "QPushButton:disabled { background-color: #0a0a0a; color: #666666; border-color: #1a1a1a; }"
    )
    kill_folder_browse_btn.setFixedWidth(140)
    kill_folder_browse_btn.setFixedHeight(44)
    kill_folder_browse_btn.clicked.connect(self.on_kill_sound_folder_browse)
    kill_folder_browse_btn.setEnabled(False)
    
    test_folder_sound_btn = QPushButton(t("Test Random"))
    test_folder_sound_btn.setIcon(QIcon(resource_path("volume_icon.png")))
    test_folder_sound_btn.setStyleSheet(
        "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
        "border: 1px solid #2a2a2a; border-radius: 4px; padding: 12px; }"
        "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
        "QPushButton:disabled { background-color: #0a0a0a; color: #666666; border-color: #1a1a1a; }"
    )
    test_folder_sound_btn.setFixedWidth(140)
    test_folder_sound_btn.setFixedHeight(44)
    test_folder_sound_btn.clicked.connect(self.test_kill_folder_sound)
    test_folder_sound_btn.setEnabled(False)
    
    self.kill_folder_browse_btn = kill_folder_browse_btn
    self.test_folder_sound_btn = test_folder_sound_btn
    
    kill_folder_layout.addWidget(self.kill_sound_folder_input)
    kill_folder_layout.addWidget(kill_folder_browse_btn)
    kill_folder_layout.addWidget(test_folder_sound_btn)
    
    sound_card_layout.addRow(kill_folder_label, kill_folder_container)
    
    volume_label = QLabel(t("Volume:"))
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
    
    death_separator = QFrame()
    death_separator.setFrameShape(QFrame.HLine)
    death_separator.setStyleSheet("QFrame { color: #333333; background-color: #333333; border: none; max-height: 1px; }")
    sound_card_layout.addRow(death_separator)
    
    self.death_sound_checkbox = QCheckBox(t("Enable Death Sound"))
    self.death_sound_checkbox.setChecked(False)
    self.death_sound_checkbox.stateChanged.connect(self.on_death_sound_toggled)
    self.death_sound_checkbox.setStyleSheet(
        "QCheckBox { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 14px; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
        "QCheckBox::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 3px; }"
        "QCheckBox::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 3px; }"
    )
    sound_card_layout.addRow("", self.death_sound_checkbox)
    
    death_mode_label = QLabel(t("Death Sound Mode:"))
    death_mode_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
    
    death_mode_container = QWidget()
    death_mode_container.setStyleSheet("background: transparent; border: none;")
    death_mode_layout = QVBoxLayout(death_mode_container)
    death_mode_layout.setContentsMargins(0, 0, 0, 0)
    death_mode_layout.setSpacing(5)
    
    self.death_sound_mode_group = QButtonGroup()
    
    self.death_single_file_radio = QRadioButton(t("Single Sound File"))
    self.death_single_file_radio.setChecked(True)
    self.death_single_file_radio.setStyleSheet(
        "QRadioButton { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 13px; }"
        "QRadioButton::indicator { width: 16px; height: 16px; }"
        "QRadioButton::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 8px; }"
        "QRadioButton::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 8px; }"
    )
    
    self.death_random_folder_radio = QRadioButton(t("Random from Folder"))
    self.death_random_folder_radio.setStyleSheet(
        "QRadioButton { color: #ffffff; spacing: 10px; background: transparent; border: none; font-size: 13px; }"
        "QRadioButton::indicator { width: 16px; height: 16px; }"
        "QRadioButton::indicator:unchecked { border: 1px solid #2a2a2a; background-color: #1e1e1e; border-radius: 8px; }"
        "QRadioButton::indicator:checked { border: 1px solid #f04747; background-color: #f04747; border-radius: 8px; }"
    )
    
    self.death_sound_mode_group.addButton(self.death_single_file_radio, 0)
    self.death_sound_mode_group.addButton(self.death_random_folder_radio, 1)
    self.death_sound_mode_group.buttonClicked.connect(self.on_death_sound_mode_changed)
    
    death_mode_layout.addWidget(self.death_single_file_radio)
    death_mode_layout.addWidget(self.death_random_folder_radio)
    
    sound_card_layout.addRow(death_mode_label, death_mode_container)
    
    death_sound_path_label = QLabel(t("Death Sound File:"))
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
    self.death_sound_path_input.setMinimumWidth(300)
    
    self.death_sound_browse_btn = QPushButton(t("Browse"))
    self.death_sound_browse_btn.setStyleSheet(
        "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
        "border: 1px solid #2a2a2a; border-radius: 4px; padding: 12px; }"
        "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
        "QPushButton:disabled { background-color: #0a0a0a; color: #666666; border-color: #1a1a1a; }"
    )
    self.death_sound_browse_btn.setFixedWidth(120)
    self.death_sound_browse_btn.setFixedHeight(44)
    self.death_sound_browse_btn.clicked.connect(self.on_death_sound_file_browse)
    
    self.death_sound_test_btn = QPushButton(t("Test Sound"))
    self.death_sound_test_btn.setIcon(QIcon(resource_path("volume_icon.png")))
    self.death_sound_test_btn.setStyleSheet(
        "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
        "border: 1px solid #2a2a2a; border-radius: 4px; padding: 12px; }"
        "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
        "QPushButton:disabled { background-color: #0a0a0a; color: #666666; border-color: #1a1a1a; }"
    )
    self.death_sound_test_btn.setFixedWidth(120)
    self.death_sound_test_btn.setFixedHeight(44)
    self.death_sound_test_btn.clicked.connect(self.test_death_sound)
    
    death_sound_path_layout.addWidget(self.death_sound_path_input)
    death_sound_path_layout.addWidget(self.death_sound_browse_btn)
    death_sound_path_layout.addWidget(self.death_sound_test_btn)
    
    sound_card_layout.addRow(death_sound_path_label, death_sound_path_container)
    
    death_folder_label = QLabel(t("Death Sound Folder:"))
    death_folder_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")
    
    death_folder_container = QWidget()
    death_folder_container.setStyleSheet("background: transparent; border: none;")
    death_folder_layout = QHBoxLayout(death_folder_container)
    death_folder_layout.setContentsMargins(0, 0, 0, 0)
    death_folder_layout.setSpacing(10)
    
    self.death_sound_folder_input = QLineEdit()
    self.death_sound_folder_input.setText(self.death_sound_folder)
    self.death_sound_folder_input.setStyleSheet(
        "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 12px; "
        "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
        "QLineEdit:hover, QLineEdit:focus { border-color: #f04747; }"
    )
    self.death_sound_folder_input.setMinimumWidth(300)
    self.death_sound_folder_input.setEnabled(False)
    
    death_folder_browse_btn = QPushButton(t("Browse Folder"))
    death_folder_browse_btn.setStyleSheet(
        "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
        "border: 1px solid #2a2a2a; border-radius: 4px; padding: 12px; }"
        "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
        "QPushButton:disabled { background-color: #0a0a0a; color: #666666; border-color: #1a1a1a; }"
    )
    death_folder_browse_btn.setFixedWidth(140)
    death_folder_browse_btn.setFixedHeight(44)
    death_folder_browse_btn.clicked.connect(self.on_death_sound_folder_browse)
    death_folder_browse_btn.setEnabled(False)
    
    test_death_folder_sound_btn = QPushButton(t("Test Random"))
    test_death_folder_sound_btn.setIcon(QIcon(resource_path("volume_icon.png")))
    test_death_folder_sound_btn.setStyleSheet(
        "QPushButton { background-color: #1e1e1e; color: #f0f0f0; "
        "border: 1px solid #2a2a2a; border-radius: 4px; padding: 12px; }"
        "QPushButton:hover { border-color: #f04747; background-color: #2a2a2a; }"
        "QPushButton:disabled { background-color: #0a0a0a; color: #666666; border-color: #1a1a1a; }"
    )
    test_death_folder_sound_btn.setFixedWidth(140)
    test_death_folder_sound_btn.setFixedHeight(44)
    test_death_folder_sound_btn.clicked.connect(self.test_death_folder_sound)
    test_death_folder_sound_btn.setEnabled(False)
    
    self.death_folder_browse_btn = death_folder_browse_btn
    self.test_death_folder_sound_btn = test_death_folder_sound_btn
    
    death_folder_layout.addWidget(self.death_sound_folder_input)
    death_folder_layout.addWidget(death_folder_browse_btn)
    death_folder_layout.addWidget(test_death_folder_sound_btn)
    
    sound_card_layout.addRow(death_folder_label, death_folder_container)
    
    death_volume_label = QLabel(t("Death Sound Volume:"))
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
    
    chat_message_label = QLabel("Twitch kill message:")
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

    death_message_label = QLabel("Twitch death message:")
    death_message_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; background: transparent; border: none; font-size: 14px; }")

    self.twitch_death_message_input = QLineEdit()
    self.twitch_death_message_input.setPlaceholderText("E.g.: 💀 {username} was killed by {attacker}! 😵 {profile_url}")
    self.twitch_death_message_input.setText(self.twitch_death_message_template)
    self.twitch_death_message_input.setStyleSheet(
        "QLineEdit { background-color: #1e1e1e; color: #f0f0f0; padding: 12px; "
        "border: 1px solid #2a2a2a; border-radius: 4px; font-size: 14px; }"
        "QLineEdit:hover, QLineEdit:focus { border-color: #9146FF; }"
    )
    self.twitch_death_message_input.setMinimumWidth(300)
    self.twitch_death_message_input.editingFinished.connect(self.on_twitch_death_message_changed)

    death_message_help = QLabel("Available placeholders: {username}, {attacker}, {profile_url}")
    death_message_help.setStyleSheet("QLabel { color: #aaaaaa; font-style: italic; background: transparent; border: none; }")
    death_message_help.setWordWrap(True)

    twitch_card_layout.addRow(death_message_label, self.twitch_death_message_input)
    twitch_card_layout.addRow("", death_message_help)

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
    
    self.clip_delay_value = QLabel(f"{self.twitch.clip_delay_seconds} {t('seconds')}")
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
    
    overlay_header = QLabel(t("GAME OVERLAY"))
    overlay_header.setStyleSheet("QLabel { color: #00ff41; font-size: 18px; font-weight: bold; background: transparent; border: none; }")

    overlay_card_layout.addRow(overlay_header)
    
    overlay_desc = QLabel(t("Configure the in-game overlay that displays your kill/death statistics in real-time while playing Star Citizen."))
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

    support_card_main_layout = QVBoxLayout(support_card)
    support_card_main_layout.setContentsMargins(20, 20, 20, 20)
    support_card_main_layout.setSpacing(15)
    
    header_container = QWidget()
    header_container.setStyleSheet("background: transparent; border: none;")
    header_layout = QHBoxLayout(header_container)
    header_layout.setContentsMargins(0, 0, 0, 0)
    header_layout.setSpacing(10)
    
    support_header = QLabel("SUPPORT & HELP")
    support_header.setStyleSheet("QLabel { color: #4CAF50; font-size: 18px; font-weight: bold; background: transparent; border: none; }")
    self.support_header = support_header
    header_layout.addWidget(support_header)
    
    try:
        madeby_image_path = os.path.join(os.path.dirname(__file__), "MadeBy.png")
        if os.path.exists(madeby_image_path):
            madeby_label = QLabel()
            madeby_pixmap = QPixmap(madeby_image_path)
            if not madeby_pixmap.isNull():
                scaled_pixmap = madeby_pixmap.scaledToWidth(120, Qt.SmoothTransformation)
                madeby_label.setPixmap(scaled_pixmap)
                madeby_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
                madeby_label.setStyleSheet("QLabel { background: transparent; border: none; }")
                header_layout.addStretch()
                header_layout.addWidget(madeby_label)
    except Exception as e:
        logging.debug(f"Could not load MadeBy.png: {e}")
    
    support_card_main_layout.addWidget(header_container)
    
    support_card_layout = QFormLayout()
    support_card_layout.setContentsMargins(0, 0, 0, 0)
    support_card_layout.setSpacing(15)
    support_card_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    
    api_setup_header = QLabel("API Setup")
    api_setup_header.setStyleSheet("QLabel { color: #FFA726; font-size: 16px; font-weight: bold; background: transparent; border: none; margin-top: 15px; }")
    self.api_setup_header = api_setup_header
    support_card_layout.addRow(api_setup_header)
    
    api_steps_text = (
        f"<b>{t('Important Steps:')}</b><br><br>"
        f"<b>1. {t('Admin Setup:')}</b> {t('An administrator in your Discord server must first configure the allowed member role within the SCTool Admin Config section.')}<br><br>"
        f"<b>2. {t('Login:')}</b> {t('Ensure you are logged into SCTool on this website.')}<br><br>"
        f"<b>3. {t('Navigate:')}</b> {t('Go to your Member Server section.')}<br><br>"
        f"<b>4. {t('Manage API:')}</b> {t('Find and access the Manage API section to set up your API key.')}<br><br>"
        f"<b>{t('Note:')}</b> {t('You need a verified API key to use the Kill Feed feature.')}"
    )
    
    api_steps_label = QLabel(api_steps_text)
    api_steps_label.setStyleSheet("QLabel { color: #cccccc; font-size: 13px; background: transparent; border: none; padding: 10px; }")
    api_steps_label.setWordWrap(True)
    self.api_steps_label = api_steps_label
    support_card_layout.addRow(api_steps_label)

    help_header = QLabel("Need Help?")
    help_header.setStyleSheet("QLabel { color: #FFA726; font-size: 16px; font-weight: bold; background: transparent; border: none; margin-top: 15px; }")
    self.help_header_label = help_header
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
    self.video_btn = video_btn
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
    self.discord_btn = discord_btn
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
    self.github_btn = github_btn
    support_card_layout.addRow("", github_btn)

    support_dev_header = QLabel("Support Development")
    support_dev_header.setStyleSheet("QLabel { color: #FFA726; font-size: 16px; font-weight: bold; background: transparent; border: none; margin-top: 15px; }")
    self.support_dev_header = support_dev_header
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
    self.patreon_btn = patreon_btn
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
    self.kofi_btn = kofi_btn
    support_card_layout.addRow("", kofi_btn)

    version_label = QLabel("Ensure you have the latest version and stay up to date.")
    version_label.setStyleSheet("QLabel { color: #888888; font-size: 12px; background: transparent; border: none; margin-top: 10px; }")
    version_label.setWordWrap(True)
    support_card_layout.addRow(version_label)
    
    form_widget = QWidget()
    form_widget.setLayout(support_card_layout)
    form_widget.setStyleSheet("background: transparent; border: none;")
    support_card_main_layout.addWidget(form_widget)
    
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
    
    killfeed_container = QWidget()
    killfeed_container_layout = QVBoxLayout(killfeed_container)
    killfeed_container_layout.setContentsMargins(0, 0, 0, 0)
    killfeed_container_layout.setSpacing(15)
    
    killfeed_scroll = QScrollArea()
    killfeed_scroll.setWidget(killfeed_page)
    killfeed_scroll.setWidgetResizable(True)
    killfeed_scroll.setFrameShape(QScrollArea.NoFrame)
    killfeed_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
    
    self.game_info_container = QWidget()
    self.game_info_container.setStyleSheet(
        "QWidget { background-color: rgba(20, 20, 20, 0.8); border: 1px solid #333333; border-radius: 8px; }"
    )
    self.game_info_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    game_info_layout = QHBoxLayout(self.game_info_container)
    game_info_layout.setContentsMargins(15, 10, 15, 10)
    game_info_layout.setSpacing(15)
    
    self.game_mode_display = QLabel("Mode: Unknown")
    self.game_mode_display.setStyleSheet(
        "QLabel { color: #00ccff; font-size: 11px; font-weight: 600; "
        "background: transparent; border: none; }"
    )
    self.game_mode_display.setAlignment(Qt.AlignLeft)
    self.game_mode_display.setWordWrap(False)
    self.game_mode_display.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
    game_info_layout.addWidget(self.game_mode_display)
    
    self.current_ship_display = QLabel("Ship Type: No Ship")
    self.current_ship_display.setStyleSheet(
        "QLabel { color: #999999; font-size: 11px; "
        "background: transparent; border: none; }"
    )
    self.current_ship_display.setAlignment(Qt.AlignLeft)
    self.current_ship_display.setWordWrap(True)
    self.current_ship_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    game_info_layout.addWidget(self.current_ship_display)
    
    killfeed_container_layout.addWidget(killfeed_scroll, 1)
    killfeed_container_layout.addWidget(self.game_info_container, 0)

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

    self.content_stack.addWidget(killfeed_container)
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
        "QPushButton:hover {border-left: 3px solid #f04747; }"
        "QPushButton:checked {border-left: 3px solid #f04747; }"
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
    
    try:
        if index == 0:
            self.update_main_ui_translations()
        elif index == 1:
            self.update_killfeed_settings_translations()
        elif index == 2:
            self.update_api_settings_translations()
        elif index == 3:
            self.update_sound_settings_translations()
        elif index == 4:
            self.update_twitch_settings_translations()
        elif index == 5:
            self.update_button_automation_translations()
        elif index == 6:
            self.update_overlay_settings_translations()
        elif index == 7:
            self.update_support_section_translations()
    except Exception as e:
        logging.error(f"Error updating translations for page {index}: {e}")

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
            
            self.disable_ssl_verification = config.get('disable_ssl_verification', False)
            self.disable_ssl_verification_checkbox.setChecked(self.disable_ssl_verification)
            
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
            
            self.kill_sound_mode = config.get('kill_sound_mode', 'single')
            if self.kill_sound_mode == 'random_folder':
                self.kill_random_folder_radio.setChecked(True)
                self.on_kill_sound_mode_changed()
            else:
                self.kill_single_file_radio.setChecked(True)
                self.on_kill_sound_mode_changed()
            
            kill_sound_folder = config.get('kill_sound_folder', '')
            if kill_sound_folder:
                self.kill_sound_folder = kill_sound_folder
                self.kill_sound_folder_input.setText(kill_sound_folder)
            
            self.death_sound_enabled = config.get('death_sound', False)
            self.death_sound_checkbox.setChecked(self.death_sound_enabled)
            death_sound_path = config.get('death_sound_path', '')
            if death_sound_path and os.path.isfile(death_sound_path):
                self.death_sound_path = death_sound_path
                self.death_sound_path_input.setText(death_sound_path)
            
            self.death_sound_volume = config.get('death_sound_volume', 100)
            self.death_volume_slider.setValue(self.death_sound_volume)
            
            self.death_sound_mode = config.get('death_sound_mode', 'single')
            if self.death_sound_mode == 'random_folder':
                self.death_random_folder_radio.setChecked(True)
                self.on_death_sound_mode_changed()
            else:
                self.death_single_file_radio.setChecked(True)
                self.on_death_sound_mode_changed()

            death_sound_folder = config.get('death_sound_folder', '')
            if death_sound_folder:
                self.death_sound_folder = death_sound_folder
                self.death_sound_folder_input.setText(death_sound_folder)
            
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
            self.clip_delay_value.setText(f"{clip_delay} {t('seconds')}")
            self.minimize_to_tray = config.get('minimize_to_tray', False)
            self.minimize_to_tray_checkbox.setChecked(self.minimize_to_tray)
            
            self.start_with_system = config.get('start_with_system', False)
            self.start_with_system_checkbox.setChecked(self.start_with_system)
            
            self.local_user_name = config.get('local_user_name', '')
            if self.local_user_name:
                self.user_display.setText(f"{self.local_user_name}")
                self.update_user_profile_image(self.local_user_name)
                self.rescan_button.setEnabled(True)
            
            self.twitch_chat_message_template = config.get('twitch_chat_message_template', "🔫 {username} just killed {victim}! 🚀 {profile_url}")
            if hasattr(self, 'twitch_message_input'):
                self.twitch_message_input.setText(self.twitch_chat_message_template)
            
            self.twitch_death_message_template = config.get('twitch_death_message_template', "💀 {username} was killed by {attacker}! 😵 {profile_url}")
            if hasattr(self, 'twitch_death_message_input'):
                self.twitch_death_message_input.setText(self.twitch_death_message_template)
            
            language_code = config.get('language', 'en')
            from language_manager import language_manager
            if language_manager.current_language != language_code:
                logging.info(f"Load config: updating language from {language_manager.current_language} to {language_code}")
                language_manager.set_language(language_code)
            else:
                logging.debug(f"Load config: language already set to {language_code}")
            
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
            color: #ffffff;
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
            
        current_version = getattr(self, '__version__', VERSION)
        client_id = getattr(self, '__client_id__', 'sctool-tracker')
        user_agent = getattr(self, 'user_agent', f'SCTool-Tracker/{VERSION}')
        
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
    current_version = getattr(parent, '__version__', VERSION)
    
    update_message = (
        f"<h3 style='color: #ff6b6b;'>🚨 {t('Update Required')}</h3>"
        f"<p><b>{t('Your version')}:</b> {current_version}</p>"
        f"<p><b>{t('Latest version')}:</b> {latest_version}</p>"
        f"<p><b>{t('Minimum required')}:</b> {minimum_version}</p>"
        f"<hr>"
        f"<p style='color: #ff6b6b;'><b>{t('Your version is no longer supported.')}</b></p>"
        f"<p>{t('You must update to continue using SCTool Tracker.')}</p>"
        f"<p>📖 <a href='https://github.com/calebv2/SCTool-Tracker/blob/main/README.md'>{t('View changelog and release notes')}</a></p>"
    )

    msg_box = styled_message_box(
        parent, 
        t("Update Required"), 
        update_message, 
        QMessageBox.Critical,
        QMessageBox.NoButton
    )
    
    update_btn = msg_box.addButton(t("Update Now"), QMessageBox.AcceptRole)
    exit_btn = msg_box.addButton(t("Exit Application"), QMessageBox.RejectRole)
    
    msg_box.setDefaultButton(update_btn)
    msg_box.exec_()
    
    if msg_box.clickedButton() == update_btn:
        start_update_process(parent, latest_version, download_url)
    else:
        logging.info("User chose to exit instead of updating")
        QApplication.quit()

def show_optional_update_dialog(parent, latest_version: str, download_url: str) -> None:
    """Show dialog for optional updates"""
    current_version = getattr(parent, '__version__', VERSION)
    
    update_message = (
        f"<h3 style='color: #4CAF50;'>🎉 {t('Update Available')}</h3>"
        f"<p><b>{t('Your version')}:</b> {current_version}</p>"
        f"<p><b>{t('Latest version')}:</b> {latest_version}</p>"
        f"<hr>"
        f"<p>{t('A new version is available with improvements and new features!')}</p>"
        f"<p>📖 <a href='https://github.com/calebv2/SCTool-Tracker/blob/main/README.md'>{t('View changelog and release notes')}</a></p>"
        f"<p><i>{t('You can continue using your current version or update now.')}</i></p>"
    )

    msg_box = styled_message_box(
        parent, 
        t("Update Available"), 
        update_message, 
        QMessageBox.Information
    )
    
    update_btn = msg_box.addButton(t("Update Now"), QMessageBox.AcceptRole)
    later_btn = msg_box.addButton(t("Remind Me Later"), QMessageBox.ActionRole)
    skip_btn = msg_box.addButton(t("Skip This Version"), QMessageBox.RejectRole)
    
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
        f"<h3 style='color: #4CAF50;'>✅ {t('You are Up to Date!')}</h3>"
        f"<p><b>{t('Current version')}:</b> {current_version}</p>"
        f"<p>{t('You have the latest version of SCTool Tracker.')}</p>"
        f"<p>{t('No updates are needed at this time.')}</p>"
    )

    msg_box = styled_message_box(
        parent, 
        t("Up to Date"), 
        update_message, 
        QMessageBox.Information
    )
    msg_box.exec_()

def show_update_check_failed_dialog(parent) -> None:
    """Show dialog when update check fails"""
    update_message = (
        f"<h3 style='color: #ff9800;'>⚠️ {t('Update Check Failed')}</h3>"
        f"<p>{t('Unable to check for updates at this time.')}</p>"
        f"<p>{t('Please check your internet connection and try again.')}</p>"
        f"<p>{t('You can also visit')} <a href='https://starcitizentool.com/download-sctool'>starcitizentool.com</a> {t('manually.')}></p>"
    )

    msg_box = styled_message_box(
        parent, 
        t("Update Check Failed"), 
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

class TranslationMixin:
    """Mixin class containing translation update methods"""
    
    def update_killfeed_settings_translations(self):
        """Update killfeed settings UI text for current language"""
        try:
            if hasattr(self, 'nav_buttons') and self.nav_buttons:
                nav_texts = [
                    t("Killfeed"),
                    t("Killfeed Settings"), 
                    t("API Settings"),
                    t("Sound Settings"),
                    t("Twitch Integration"),
                    t("Button Automation"),
                    t("Game Overlay"),
                    t("Support")
                ]
                for i, button in enumerate(self.nav_buttons):
                    if i < len(nav_texts):
                        button.setText(nav_texts[i])
            
            try:
                for widget in self.findChildren(QLabel):
                    text = widget.text()
                    if text == "TRACKING CONFIGURATION":
                        widget.setText(t("TRACKING CONFIGURATION"))
                    elif text.startswith("Configure the core settings"):
                        widget.setText(t("Configure the core settings for tracking your Star Citizen gameplay and kills."))
                    elif text == "Game.log Path:":
                        widget.setText(t("Game.log Path:"))
                    elif text.startswith("Path to your Star Citizen Game.log"):
                        widget.setText(t("Path to your Star Citizen Game.log file (typically StarCitizen\\LIVE\\game.log)"))
                    elif text == "Current Ship:":
                        widget.setText(t("Current Ship:"))
                    elif text.startswith("Select the ship you're currently flying"):
                        widget.setText(t("Select the ship you're currently flying (included with kill data)"))
                    elif text == "DATA MANAGEMENT":
                        widget.setText(t("DATA MANAGEMENT"))
                    elif text.startswith("Export your kill logs"):
                        widget.setText(t("Export your kill logs and access application data files for backup or troubleshooting."))
                    elif text.startswith("• Export logs creates"):
                        widget.setText(t("• Export logs creates an HTML file with all recorded kills and deaths\\n• Data folder contains configuration files, logs, and saved kill records"))
                    elif text == "APPLICATION PREFERENCES":
                        widget.setText(t("APPLICATION PREFERENCES"))
                    elif text.startswith("Configure how SCTool Tracker behaves"):
                        widget.setText(t("Configure how SCTool Tracker behaves when starting and minimizing."))
                    elif text.startswith("When minimized, the application will hide"):
                        widget.setText(t("When minimized, the application will hide in the system tray instead of the taskbar"))
                    elif text.startswith("Launch SCTool Tracker automatically"):
                        widget.setText(t("Launch SCTool Tracker automatically when your computer starts"))
                    elif text == "Language:":
                        widget.setText(t("Language:"))
                    elif text.startswith("Choose your preferred language"):
                        widget.setText(t("Choose your preferred language for the application interface"))
            except Exception as e:
                logging.debug(f"Error updating killfeed settings label translations: {e}")

            if hasattr(self, 'log_path_input'):
                self.log_path_input.setPlaceholderText(t("Enter path to your Game.log"))

            if hasattr(self, 'export_button'):
                self.export_button.setText(t("EXPORT LOGS"))
            if hasattr(self, 'files_button'):
                self.files_button.setText(t("OPEN DATA FOLDER"))

            if hasattr(self, 'send_to_api_checkbox'):
                self.send_to_api_checkbox.setText(t("Send kills to API"))
            if hasattr(self, 'minimize_to_tray_checkbox'):
                self.minimize_to_tray_checkbox.setText(t("Minimize to system tray"))
            if hasattr(self, 'start_with_system_checkbox'):
                self.start_with_system_checkbox.setText(t("Start with Windows"))
                
            try:
                for input_widget in self.findChildren(QLineEdit):
                    placeholder = input_widget.placeholderText()
                    if placeholder == "Enter path to your Game.log":
                        input_widget.setPlaceholderText(t("Enter path to your Game.log"))
            except Exception as e:
                logging.debug(f"Error updating killfeed settings input translations: {e}")
            
            try:
                for button in self.findChildren(QPushButton):
                    text = button.text()
                    if text == "Browse":
                        button.setText(t("Browse"))
            except Exception as e:
                logging.debug(f"Error updating killfeed settings button translations: {e}")
                
            logging.info("Killfeed settings translations updated")
            
        except Exception as e:
            logging.error(f"Error updating killfeed settings translations: {e}")

    def update_all_translations(self):
        """Update translations for all UI sections"""
        try:
            self.update_killfeed_settings_translations()
            self.update_api_settings_translations()
            self.update_sound_settings_translations()
            self.update_twitch_settings_translations()
            self.update_button_automation_translations()
            self.update_overlay_settings_translations()
            self.update_support_section_translations()
            self.update_main_ui_translations()
            
            self.force_update_all_overlay_translations()
            
            logging.info("All translations updated successfully")
            
        except Exception as e:
            logging.error(f"Error updating all translations: {e}")

    def force_update_all_overlay_translations(self):
        """Force update all overlay-related translations across the entire application"""
        try:
            app = QApplication.instance()
            if app:
                for widget in app.allWidgets():
                    try:
                        if hasattr(widget, 'update_translations'):
                            widget_class_name = widget.__class__.__name__.lower()
                            if any(term in widget_class_name for term in ['overlay', 'control', 'panel', 'hotkey']):
                                widget.update_translations()
                        
                        if isinstance(widget, QLabel) and hasattr(widget, 'text'):
                            text = widget.text()
                            if ("Use global hotkey to toggle overlay visibility" in text or
                                "Use global hotkey" in text and "overlay" in text and "visibility" in text or
                                "hotkey" in text.lower() and "overlay" in text.lower() and "toggle" in text.lower()):
                                widget.setText(f"""
                                    <b>{t('Instructions:')}</b><br>
                                    • {t('Left-click and drag to move the overlay')}<br>
                                    • {t('Ctrl + Mouse wheel to adjust opacity')}<br>
                                    • {t('Click the mode button (●/◐) on overlay to cycle modes')}<br>
                                    • {t('Use global hotkey to toggle overlay visibility')}<br>
                                    • {t('Overlay stays on top of all windows including games')}
                                    """)
                                logging.info(f"Force updated overlay instructions label with text: {text[:50]}...")
                    except Exception as e:
                        pass
                        
            logging.info("Force overlay translation update completed")
            
        except Exception as e:
            logging.error(f"Error in force_update_all_overlay_translations: {e}")

    def update_api_settings_translations(self):
        """Update API settings UI text for current language"""
        print(f"[DEBUG] update_api_settings_translations called - current language: {get_language_manager().current_language}")
        
        if hasattr(self, 'api_key_input'):
            self.api_key_input.setPlaceholderText(t("Enter your API key here"))
            print("[DEBUG] Updated API key input placeholder")

        if hasattr(self, 'api_help_label'):
            print("[DEBUG] Found api_help_label - updating with current language text")
            
            original_text = 'Instructions are also available HERE'
            translated_text = t(original_text)
            
            youtube_link = t("https://www.youtube.com/watch?v=L62qvxopKak")
            
            if original_text != translated_text:
                translated_here = t("HERE")
                if translated_here in translated_text:
                    here_link = translated_text.replace(translated_here, f'<a href="{youtube_link}" style="color: #f04747; text-decoration: underline;">{translated_here}</a>')
                else:
                    here_link = f'{translated_text} <a href="{youtube_link}" style="color: #f04747; text-decoration: underline;">{translated_here}</a>'
            else:
                here_link = f'{translated_text.replace("HERE", "")} <a href="{youtube_link}" style="color: #f04747; text-decoration: underline;">HERE</a>'
            
            api_help_text = (
                f"<b>{t('How to get an API key:')}</b><br><br>"
                f"{t('1. Visit starcitizentool.com and log in')}<br>"
                f"{t('2. You must be in a Discord server that has the SCTool Discord bot and had been given the member or allowed role')}<br>"
                f"{t('3. After login, select which Discord server to associate with your kills')}<br>"
                f"{t('4. Navigate to starcitizentool.com/kills/manage_api_keys')}<br>"
                f"{t('5. Verify your in-game name')}<br>"
                f"{t('6. Generate an API key and paste it here')}<br><br>"
                f"{here_link}"
            )
            self.api_help_label.setText(api_help_text)
            print(f"[DEBUG] API help label updated with full instructions")
            
            self.api_help_label.update()
            self.api_help_label.repaint()
            print("[DEBUG] Forced immediate repaint of api_help_label")
        else:
            print("[DEBUG] api_help_label reference not found")

        if hasattr(self, 'api_steps_label'):
            api_steps_text = (
                f"<b>{t('Important Steps:')}</b><br><br>"
                f"<b>1. {t('Admin Setup:')}</b> {t('An administrator in your Discord server must first configure the allowed member role within the SCTool Admin Config section.')}<br><br>"
                f"<b>2. {t('Login:')}</b> {t('Ensure you are logged into SCTool on this website.')}<br><br>"
                f"<b>3. {t('Navigate:')}</b> {t('Go to your Member Server section.')}<br><br>"
                f"<b>4. {t('Manage API:')}</b> {t('Find and access the Manage API section to set up your API key.')}<br><br>"
                f"<b>{t('Note:')}</b> {t('You need a verified API key to use the Kill Feed feature.')}"
            )
            self.api_steps_label.setText(api_steps_text)
            logging.info(f"API steps label updated with translations")

        try:
            for widget in self.findChildren(QLabel):
                text = widget.text()
                
                if text == "API CONNECTION":
                    widget.setText(t("API CONNECTION"))
                elif text == "API Settings" or text == "API SETTINGS":
                    widget.setText(t("API Settings"))
                
                elif text.startswith("Connect to the SCTool online service"):
                    widget.setText(t("Connect to the SCTool online service to track your kill statistics across sessions and compare with other players."))
                elif text.startswith("Your API key connects"):
                    widget.setText(t("Your API key connects your account to the SCTool Tracker service."))
                
                elif "<b>" in text and ("Important Steps:" in text or "Admin Setup:" in text or "Login:" in text or "Navigate:" in text or "Manage API:" in text):
                    api_steps_text = (
                        f"<b>{t('Important Steps:')}</b><br><br>"
                        f"<b>1. {t('Admin Setup:')}</b> {t('An administrator in your Discord server must first configure the allowed member role within the SCTool Admin Config section.')}<br><br>"
                        f"<b>2. {t('Login:')}</b> {t('Ensure you are logged into SCTool on this website.')}<br><br>"
                        f"<b>3. {t('Navigate:')}</b> {t('Go to your Member Server section.')}<br><br>"
                        f"<b>4. {t('Manage API:')}</b> {t('Find and access the Manage API section to set up your API key.')}<br><br>"
                        f"<b>{t('Note:')}</b> {t('You need a verified API key to use the Kill Feed feature.')}"
                    )
                    widget.setText(api_steps_text)
                    logging.info(f"Updated HTML formatted API steps widget with translations")
                    
        except Exception as e:
            logging.debug(f"Error updating API label translations: {e}")
        
        try:
            for button in self.findChildren(QPushButton):
                if button.text() == "MANAGE API KEYS":
                    button.setText(t("MANAGE API KEYS"))
        except Exception as e:
            logging.debug(f"Error updating API button translations: {e}")
        
        try:
            if hasattr(self, 'send_to_api_checkbox'):
                self.send_to_api_checkbox.setText(t("Send kills to API"))
            
            logging.info("API settings translations updated")
            
        except Exception as e:
            logging.error(f"Error updating API settings translations: {e}")

    def update_sound_settings_translations(self):
        """Update sound settings UI text for current language"""
        try:
            if hasattr(self, 'kill_sound_checkbox'):
                self.kill_sound_checkbox.setText(t("Enable Kill Sound"))
            if hasattr(self, 'death_sound_checkbox'):
                self.death_sound_checkbox.setText(t("Enable Death Sound"))
            if hasattr(self, 'kill_sound_test_button'):
                self.kill_sound_test_button.setText(t("Test Sound"))
            if hasattr(self, 'death_sound_test_button'):
                self.death_sound_test_button.setText(t("Test Sound"))
            if hasattr(self, 'kill_single_file_radio'):
                self.kill_single_file_radio.setText(t("Single Sound File"))
            if hasattr(self, 'kill_random_folder_radio'):
                self.kill_random_folder_radio.setText(t("Random from Folder"))
            if hasattr(self, 'death_single_file_radio'):
                self.death_single_file_radio.setText(t("Single Sound File"))
            if hasattr(self, 'death_random_folder_radio'):
                self.death_random_folder_radio.setText(t("Random from Folder"))
        except Exception as e:
            logging.error(f"Error updating sound settings translations: {e}")
        
        try:
            for widget in self.findChildren(QLabel):
                text = widget.text()
                if text == "SOUND OPTIONS":
                    widget.setText(t("SOUND OPTIONS"))
                elif text.startswith("Configure sound notifications"):
                    widget.setText(t("Configure sound notifications for when you get kills in Star Citizen."))
                elif text == "Kill Sound File:":
                    widget.setText(t("Kill Sound File:"))
                elif text == "Death Sound File:":
                    widget.setText(t("Death Sound File:"))
                elif text == "Volume:":
                    widget.setText(t("Volume:"))
                elif text == "Death Sound Volume:":
                    widget.setText(t("Death Sound Volume:"))
        except Exception as e:
            logging.debug(f"Error updating sound label translations: {e}")
        
        try:
            for button in self.findChildren(QPushButton):
                if button.text() == "Browse":
                    button.setText(t("Browse"))
                elif button.text() == "Test Sound":
                    button.setText(t("Test Sound"))
        except Exception as e:
            logging.debug(f"Error updating sound button translations: {e}")
        
        logging.info("Sound settings translations updated")

    def update_twitch_settings_translations(self):
        """Update Twitch settings UI text for current language"""
        try:
            if hasattr(self, 'twitch_enabled_checkbox'):
                self.twitch_enabled_checkbox.setText(t("Enable Twitch Integration"))
            if hasattr(self, 'auto_connect_twitch_checkbox'):
                self.auto_connect_twitch_checkbox.setText(t("Auto-connect to Twitch on startup"))
            if hasattr(self, 'clip_creation_checkbox'):
                self.clip_creation_checkbox.setText(t("Create Twitch clips on kill"))
            if hasattr(self, 'chat_posting_checkbox'):
                self.chat_posting_checkbox.setText(t("Post kills to Twitch chat"))
            if hasattr(self, 'twitch_connect_button'):
                self.twitch_connect_button.setText(t("Connect Twitch"))
            if hasattr(self, 'twitch_disconnect_button'):
                self.twitch_disconnect_button.setText(t("Disconnect Twitch"))
            if hasattr(self, 'twitch_channel_input'):
                self.twitch_channel_input.setPlaceholderText(t("Enter your Twitch channel name"))
            if hasattr(self, 'clip_delay_value') and hasattr(self, 'twitch') and hasattr(self.twitch, 'clip_delay_seconds'):
                self.clip_delay_value.setText(f"{self.twitch.clip_delay_seconds} {t('seconds')}")
            
            try:
                for widget in self.findChildren(QLabel):
                    text = widget.text()
                    if text == "TWITCH INTEGRATION":
                        widget.setText(t("TWITCH INTEGRATION"))
                    elif text.startswith("Connect your Twitch account"):
                        widget.setText(t("Connect your Twitch account to automatically create clips of your kills during your stream."))
                    elif text == "Enable Twitch Integration":
                        widget.setText(t("Enable Twitch Integration"))
                    elif text == "Auto-connect to Twitch on launch":
                        widget.setText(t("Auto-connect to Twitch on launch"))
                    elif text == "Twitch Channel:":
                        widget.setText(t("Twitch Channel:"))
                    elif text == "CLIP SETTINGS":
                        widget.setText(t("CLIP SETTINGS"))
                    elif text.startswith("Note: Clip creation requires"):
                        widget.setText(t("Note: Clip creation requires you to be actively streaming on Twitch"))
                    elif text == "Create Twitch clips on kill":
                        widget.setText(t("Create Twitch clips on kill"))
                    elif text == "Post kills to Twitch chat":
                        widget.setText(t("Post kills to Twitch chat"))
                    elif text == "Twitch kill message:":
                        widget.setText(t("Twitch kill message:"))
                    elif text == "Twitch death message:":
                        widget.setText(t("Twitch death message:"))
                    elif text.startswith("Available placeholders:") and "{username}, {victim}, {profile_url}" in text:
                        widget.setText(t("Available placeholders: {username}, {victim}, {profile_url}"))
                    elif text.startswith("Available placeholders:") and "{username}, {attacker}, {profile_url}" in text:
                        widget.setText(t("Available placeholders: {username}, {attacker}, {profile_url}"))
                    elif text == "Delay after kill:":
                        widget.setText(t("Delay after kill:"))
            except Exception as e:
                logging.debug(f"Error updating Twitch label translations: {e}")
            
            if hasattr(self, 'twitch_message_input'):
                placeholder = self.twitch_message_input.placeholderText()
                if placeholder and not placeholder.startswith("🔫"):
                    self.twitch_message_input.setPlaceholderText("🔫 {username} just killed {victim}! 🚀 {profile_url}")

            if hasattr(self, 'twitch_death_message_input'):
                placeholder = self.twitch_death_message_input.placeholderText()
                if placeholder and not placeholder.startswith("💀"):
                    self.twitch_death_message_input.setPlaceholderText("💀 {username} was killed by {attacker}! 😵 {profile_url}")
            
            logging.info("Twitch settings translations updated")
            
        except Exception as e:
            logging.error(f"Error updating Twitch settings translations: {e}")

    def update_button_automation_translations(self):
        """Update Button Automation settings UI text for current language"""
        try:
            if hasattr(self, 'button_automation_widget'):
                if hasattr(self.button_automation_widget, 'update_translations'):
                    self.button_automation_widget.update_translations()
            
            logging.info("Button Automation translations updated")
            
        except Exception as e:
            logging.error(f"Error updating Button Automation translations: {e}")

    def update_overlay_settings_translations(self):
        """Update Game Overlay settings UI text for current language"""
        try:
            if hasattr(self, 'overlay_settings'):
                if hasattr(self.overlay_settings, 'update_translations'):
                    self.overlay_settings.update_translations()
            
            if hasattr(self, 'game_overlay'):
                if hasattr(self.game_overlay, 'update_translations'):
                    self.game_overlay.update_translations()
            
            for widget in self.findChildren(QWidget):
                if hasattr(widget, 'update_translations') and 'overlay' in widget.__class__.__name__.lower():
                    try:
                        widget.update_translations()
                    except Exception as e:
                        logging.debug(f"Error updating overlay widget translations: {e}")
            
            try:
                for widget in self.findChildren(QLabel):
                    if hasattr(widget, 'text'):
                        text = widget.text()
                        if "Use global hotkey to toggle overlay visibility" in text:
                            widget.setText(f"""
        <b>{t('Instructions:')}</b><br>
        • {t('Left-click and drag to move the overlay')}<br>
        • {t('Ctrl + Mouse wheel to adjust opacity')}<br>
        • {t('Click the mode button (●/◐) on overlay to cycle modes')}<br>
        • {t('Use global hotkey to toggle overlay visibility')}<br>
        • {t('Overlay stays on top of all windows including games')}
        """)
                            overlay_labels_found += 1
            except Exception as e:
                logging.debug(f"Error updating overlay instructions labels: {e}")
            
            try:
                overlay_labels_found = 0
                
                for widget in self.findChildren(QLabel):
                    text = widget.text()
                    if text == "GAME OVERLAY":
                        widget.setText(t("GAME OVERLAY"))
                        overlay_labels_found += 1
                    elif text == "Game Overlay":
                        widget.setText(t("Game Overlay"))
                        overlay_labels_found += 1
                    elif text == "Superposición del Juego":
                        widget.setText(t("Game Overlay"))
                        overlay_labels_found += 1
                    elif text.startswith("Configure the in-game overlay"):
                        widget.setText(t("Configure the in-game overlay that displays your kill/death statistics in real-time while playing Star Citizen."))
                        overlay_labels_found += 1
                    elif text.startswith("Overlay system with multiple display modes"):
                        widget.setText(t("Overlay system with multiple display modes, customizable themes, and hotkey support"))
                        overlay_labels_found += 1
                    elif text == "Instructions:":
                        widget.setText(t("Instructions:"))
                        overlay_labels_found += 1
                    elif text == "• Press Ctrl+` to toggle the overlay":
                        widget.setText(t("• Press Ctrl+` to toggle the overlay"))
                        overlay_labels_found += 1
                    elif text == "• Ctrl + Mouse wheel to change opacity":
                        widget.setText(t("• Ctrl + Mouse wheel to change opacity"))
                        overlay_labels_found += 1
                    elif text == "• Click the mode selector (F1-F5) to cycle modes":
                        widget.setText(t("• Click the mode selector (F1-F5) to cycle modes"))
                        overlay_labels_found += 1
                    elif text == "• Use global hotkey to toggle overlay visibility":
                        widget.setText(t("• Use global hotkey to toggle overlay visibility"))
                        overlay_labels_found += 1
                    elif text == "• Overlay stays on top of windowed/borderless games":
                        widget.setText(t("• Overlay stays on top of windowed/borderless games"))
                        overlay_labels_found += 1
                    elif text == "Use the capture button to record a key combination":
                        widget.setText(t("Use the capture button to record a key combination"))
                        overlay_labels_found += 1
                    elif text == "Left-click and drag to move the overlay":
                        widget.setText(t("Left-click and drag to move the overlay"))
                        overlay_labels_found += 1
                    elif text == "Ctrl + Mouse wheel to adjust opacity":
                        widget.setText(t("Ctrl + Mouse wheel to adjust opacity"))
                        overlay_labels_found += 1
                    elif text == "Click the mode button (●/◐) on overlay to cycle modes":
                        widget.setText(t("Click the mode button (●/◐) on overlay to cycle modes"))
                        overlay_labels_found += 1
                    elif text == "Use global hotkey to toggle overlay visibility":
                        widget.setText(t("Use global hotkey to toggle overlay visibility"))
                        overlay_labels_found += 1
                    elif text == "Overlay stays on top of all windows including games":
                        widget.setText(t("Overlay stays on top of all windows including games"))
                        overlay_labels_found += 1
                    elif text.startswith("• Press Ctrl+`"):
                        widget.setText(t("• Press Ctrl+` to toggle the overlay"))
                        overlay_labels_found += 1
                    elif text.startswith("• Ctrl + Mouse wheel"):
                        widget.setText(t("• Ctrl + Mouse wheel to change opacity"))
                        overlay_labels_found += 1
                    elif text.startswith("• Click the mode selector"):
                        widget.setText(t("• Click the mode selector (F1-F5) to cycle modes"))
                        overlay_labels_found += 1
                    elif text.startswith("• Use global hotkey"):
                        widget.setText(t("• Use global hotkey to toggle overlay visibility"))
                        overlay_labels_found += 1
                    elif "Use global hotkey" in text and "overlay visibility" in text:
                        widget.setText(t("• Use global hotkey to toggle overlay visibility"))
                        overlay_labels_found += 1
                    elif "global hotkey" in text.lower() and "toggle" in text.lower() and "overlay" in text.lower():
                        widget.setText(t("• Use global hotkey to toggle overlay visibility"))
                        overlay_labels_found += 1
                    elif text.startswith("• Overlay stays on top"):
                        widget.setText(t("• Overlay stays on top of windowed/borderless games"))
                        overlay_labels_found += 1
                
                logging.debug(f"Overlay settings translation: Found {overlay_labels_found} overlay-related labels to translate")
            except Exception as e:
                logging.debug(f"Error updating Overlay section label translations: {e}")
            
            try:
                for button in self.findChildren(QPushButton):
                    text = button.text()
                    if text == "Click to Capture":
                        button.setText(t("Click to Capture"))
                    elif text == "Reset to Default":
                        button.setText(t("Reset to Default"))
                    elif text == "Reset Position":
                        button.setText(t("Reset Position"))
                    elif text == "Show Overlay":
                        button.setText(t("Show Overlay"))
                    elif text == "Hide Overlay":
                        button.setText(t("Hide Overlay"))
            except Exception as e:
                logging.debug(f"Error updating Overlay section button translations: {e}")
            
            logging.info("Game Overlay settings translations updated")
            
        except Exception as e:
            logging.error(f"Error updating Game Overlay settings translations: {e}")

    def update_support_section_translations(self):
        """Update Support section UI text for current language"""
        try:
            if hasattr(self, 'support_header'):
                self.support_header.setText(t("SUPPORT & HELP"))
                
            if hasattr(self, 'api_setup_header'):
                self.api_setup_header.setText(t("API Setup"))
                
            if hasattr(self, 'help_header_label'):
                self.help_header_label.setText(t("Need Help?"))
                
            if hasattr(self, 'support_dev_header'):
                self.support_dev_header.setText(t("Support Development"))
            
            if hasattr(self, 'api_steps_label'):
                api_steps_text = (
                    f"<b>{t('Important Steps:')}</b><br><br>"
                    f"<b>1. {t('Admin Setup:')}</b> {t('An administrator in your Discord server must first configure the allowed member role within the SCTool Admin Config section.')}<br><br>"
                    f"<b>2. {t('Login:')}</b> {t('Ensure you are logged into SCTool on this website.')}<br><br>"
                    f"<b>3. {t('Navigate:')}</b> {t('Go to your Member Server section.')}<br><br>"
                    f"<b>4. {t('Manage API:')}</b> {t('Find and access the Manage API section to set up your API key.')}<br><br>"
                    f"<b>{t('Note:')}</b> {t('You need a verified API key to use the Kill Feed feature.')}"
                )
                self.api_steps_label.setText(api_steps_text)
                logging.info(f"Updated API steps label with translated text: {t('Important Steps:')}")
            else:
                logging.warning("api_steps_label reference not found - using fallback method")
                
            if hasattr(self, 'video_btn'):
                self.video_btn.setText(f"📺 {t('Watch Setup Video')}")
                
            if hasattr(self, 'discord_btn'):
                self.discord_btn.setText(f"💬 {t('Join SCTool Discord')}")
                
            if hasattr(self, 'github_btn'):
                self.github_btn.setText(f"📚 {t('GitHub Documentation')}")
                
            if hasattr(self, 'patreon_btn'):
                self.patreon_btn.setText(f"❤️ {t('Support on Patreon')}")
                
            if hasattr(self, 'kofi_btn'):
                self.kofi_btn.setText(f"☕ {t('Buy me a Coffee')}")
            
            try:
                for widget in self.findChildren(QLabel):
                    text = widget.text()
                    if text.startswith("Ensure you have the latest version"):
                        widget.setText(t("Ensure you have the latest version and stay up to date."))
            except Exception as e:
                logging.debug(f"Error updating fallback Support label translations: {e}")

            try:
                for button in self.findChildren(QPushButton):
                    button_text = button.text()
                    if "GESTIONAR CLAVES API" in button_text or ("MANAGE API KEYS" in button_text and "manage" in button_text.lower()):
                        button.setText(t("MANAGE API KEYS"))
                    elif "Enviar Bajas a API" in button_text or ("Send Kills to API" in button_text and "send" in button_text.lower()):
                        button.setText(t("Send Kills to API"))
            except Exception as e:
                logging.debug(f"Error updating fallback Support button translations: {e}")
            
            logging.info("Support section translations updated")
            
        except Exception as e:
            logging.error(f"Error updating Support section translations: {e}")

    def update_main_ui_translations(self):
        try:
            """Update main UI elements like status displays and buttons"""
            if hasattr(self, 'start_button'):
                if hasattr(self, 'monitor_thread') and self.monitor_thread and self.monitor_thread.isRunning():
                    self.start_button.setText(t("STOP MONITORING"))
                else:
                    self.start_button.setText(t("START MONITORING"))
            elif hasattr(self, 'toggle_button'):
                if hasattr(self, 'monitor_thread') and self.monitor_thread and self.monitor_thread.isRunning():
                    self.toggle_button.setText(t("STOP MONITORING"))
                else:
                    self.toggle_button.setText(t("START MONITORING"))
            
            if hasattr(self, 'rescan_button'):
                self.rescan_button.setText(t("FIND MISSED KILLS"))
            
            if hasattr(self, 'update_button'):
                self.update_button.setText(t("CHECK FOR UPDATES"))
            
            if hasattr(self, 'export_button'):
                self.export_button.setText(t("EXPORT LOGS"))
            
            if hasattr(self, 'files_button'):
                self.files_button.setText(t("OPEN DATA FOLDER"))
            
            if hasattr(self, 'user_display'):
                current_text = self.user_display.text()
                if "Not logged in" in current_text or t("Not logged in") in current_text:
                    self.user_display.setText(t("Not logged in"))
                else:
                    if hasattr(self, 'local_user_name') and self.local_user_name:
                        self.user_display.setText(f"{self.local_user_name}")
                    else:
                        if ":" in current_text:
                            parts = current_text.split(":", 1)
                            if len(parts) == 2:
                                username = parts[1].strip()
                                if username:
                                    self.user_display.setText(f"{username}")
                        else:
                            self.user_display.setText(t("Not logged in"))
            
            if hasattr(self, 'twitch_indicator'):
                current_text = self.twitch_indicator.text()
                if current_text == "Twitch Connected" or "Conectado" in current_text:
                    self.twitch_indicator.setText(t("Twitch Connected"))
                elif current_text == "Twitch Not Connected" or "No conectado" in current_text or "Not Connected" in current_text:
                    self.twitch_indicator.setText(t("Twitch Not Connected"))
            
            if hasattr(self, 'game_mode_display'):
                current_text = self.game_mode_display.text()
                if ":" in current_text:
                    parts = current_text.split(":", 1)
                    if len(parts) == 2:
                        mode = parts[1].strip()
                        if mode == "Unknown" or mode == t("Unknown"):
                            self.game_mode_display.setText(t("Mode: Unknown"))
                        else:
                            self.game_mode_display.setText(f"{t('Mode:')} {mode}")
                else:
                    if current_text == "Unknown" or current_text == t("Unknown"):
                        self.game_mode_display.setText(t("Mode: Unknown"))
                    else:
                        self.game_mode_display.setText(f"{t('Mode:')} {current_text}")
            
            if hasattr(self, 'current_ship_display'):
                current_text = self.current_ship_display.text()
                if current_text in ["No Ship", t("No Ship"), "Ship Type: No Ship", t("Ship Type: No Ship")]:
                    self.current_ship_display.setText(t("Ship Type: No Ship"))
            
            try:
                for widget in self.findChildren(QLabel):
                    text = widget.text()
                    if text == "MONITORING":
                        widget.setText(t("MONITORING"))
                    elif text == "API CONNECTED":
                        widget.setText(t("API CONNECTED"))
                    elif text == "TWITCH CONNECTED":
                        widget.setText(t("TWITCH CONNECTED"))
                    elif text == "GAME MODE":
                        widget.setText(t("GAME MODE"))
                    elif text == "CURRENT SHIP":
                        widget.setText(t("CURRENT SHIP"))
                    elif text == "KILLFEED":
                        widget.setText(t("KILLFEED"))
                    elif text == "TRACKING CONFIGURATION":
                        widget.setText(t("TRACKING CONFIGURATION"))
                    elif text == "DATA MANAGEMENT":
                        widget.setText(t("DATA MANAGEMENT"))
                    elif text == "APPLICATION PREFERENCES":
                        widget.setText(t("APPLICATION PREFERENCES"))
                    elif text == "SCTool Tracker":
                        widget.setText(t("SCTool Tracker"))
                    elif text == "KILLS":
                        widget.setText(t("KILLS"))
                    elif text == "DEATHS":
                        widget.setText(t("DEATHS"))
                    elif text == "K/D RATIO":
                        widget.setText(t("K/D RATIO"))
                    elif text == "SESSION TIME":
                        widget.setText(t("SESSION TIME"))
                    elif text == "Game.log Path:":
                        widget.setText(t("Game.log Path:"))
                    elif text == "Current Ship:":
                        widget.setText(t("Current Ship:"))
                    elif text == "API Key:":
                        widget.setText(t("API Key:"))
                    elif text == "Language:":
                        widget.setText(t("Language:"))
                    elif text.startswith("Configure the core settings"):
                        widget.setText(t("Configure the core settings for tracking your Star Citizen gameplay and kills."))
                    elif text.startswith("Export your kill logs"):
                        widget.setText(t("Export your kill logs and access application data files for backup or troubleshooting."))
                    elif text.startswith("Configure how SCTool Tracker behaves"):
                        widget.setText(t("Configure how SCTool Tracker behaves when starting and minimizing."))
                    elif text.startswith("Path to your Star Citizen Game.log"):
                        widget.setText(t("Path to your Star Citizen Game.log file (typically StarCitizen\\LIVE\\game.log)"))
                    elif text.startswith("Select the ship you're currently flying"):
                        widget.setText(t("Select the ship you're currently flying (included with kill data)"))
                    elif text.startswith("When minimized, the application will hide"):
                        widget.setText(t("When minimized, the application will hide in the system tray instead of the taskbar"))
                    elif text.startswith("Launch SCTool Tracker automatically"):
                        widget.setText(t("Launch SCTool Tracker automatically when your computer starts"))
                    elif text.startswith("Choose your preferred language"):
                        widget.setText(t("Choose your preferred language for the application interface"))
            except Exception as e:
                logging.debug(f"Error updating main UI label translations: {e}")
            
            try:
                for checkbox in self.findChildren(QCheckBox):
                    text = checkbox.text()
                    if text == "Minimize to system tray":
                        checkbox.setText(t("Minimize to system tray"))
                    elif text == "Start with Windows":
                        checkbox.setText(t("Start with Windows"))
                    elif text == "Send kills to API":
                        checkbox.setText(t("Send kills to API"))
            except Exception as e:
                logging.debug(f"Error updating main UI checkbox translations: {e}")
            
            try:
                for input_widget in self.findChildren(QLineEdit):
                    placeholder = input_widget.placeholderText()
                    if placeholder == "Enter path to your Game.log":
                        input_widget.setPlaceholderText(t("Enter path to your Game.log"))
            except Exception as e:
                logging.debug(f"Error updating main UI input translations: {e}")
            
            logging.info("Main UI translations updated")
            
        except Exception as e:
            logging.error(f"Error updating main UI translations: {e}")