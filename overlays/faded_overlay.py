# faded_overlay.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from language_manager import t

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QApplication
)
from PyQt5.QtCore import (
    QTimer, QPropertyAnimation, Qt, QEasingCurve
)
from PyQt5.QtGui import (
    QPixmap, QPainter, QBrush, QPen, QColor
)
import base64
import re

def create_faded_ui(self):
    """Create faded notification overlay - only shows during kill/death events"""
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    self.faded_container = QWidget()
    self.faded_container.setStyleSheet("background: transparent;")
    self.faded_container.hide()
    
    layout.addWidget(self.faded_container)
    
    self.setLayout(layout)
    self.setMinimumSize(50, 50)
    self.resize(50, 50)

    self.fade_timer = QTimer()
    self.fade_timer.timeout.connect(self.fade_notification)

    self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
    self.fade_animation.finished.connect(self.hide_faded_notification)

def show_death_notification(self, attacker: str, weapon: str, zone: str, game_mode: str = "Unknown"):
    """Show death notification in faded mode with org info and profile image"""
    if self.display_mode != 'faded':
        return
    
    self.stop_all_faded_animations()
    self.clear_faded_container()
    
    try:
        from fetch import fetch_player_details, fetch_victim_image_base64
        from kill_parser import KillParser
        
        details = fetch_player_details(attacker)
        attacker_image_data_uri = fetch_victim_image_base64(attacker)
        formatted_zone = KillParser.format_zone(zone)
        formatted_weapon = KillParser.format_weapon(weapon)
        
        if formatted_weapon != 'Unknown':
            weapon_clean = formatted_weapon
        else:
            weapon_clean = clean_weapon_name(weapon)
            
    except ImportError:
        details = {'org_name': 'Unknown', 'org_tag': 'Unknown'}
        attacker_image_data_uri = ""
        formatted_zone = zone.replace('_', ' ').title()
        weapon_clean = clean_weapon_name(weapon)

    notification_widget = QWidget()
    notification_layout = QVBoxLayout(notification_widget)
    notification_layout.setContentsMargins(20, 15, 20, 15)
    notification_layout.setSpacing(10)
    
    header_row = QHBoxLayout()
    notification_layout.addLayout(header_row)
    
    header_text = QLabel(t("YOU DIED"))
    header_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    header_text.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['death_color'].name()};
            font-size: 24px;
            font-weight: bold;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    header_row.addWidget(header_text, 1)
    
    image_container = QWidget()
    image_container.setFixedSize(80, 80)
    image_container.setVisible(False)
    
    image_label = QLabel()
    image_label.setFixedSize(80, 80)
    
    image_layout = QVBoxLayout(image_container)
    image_layout.setContentsMargins(0, 0, 0, 0)
    image_layout.addWidget(image_label)
    
    header_row.addWidget(image_container, 0, Qt.AlignRight)
    
    attacker_label = QLabel(f"{t('KILLED BY:')} {attacker.upper()}")
    attacker_label.setAlignment(Qt.AlignLeft)
    attacker_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['text_primary'].name()};
            font-size: 20px;
            font-weight: bold;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    notification_layout.addWidget(attacker_label)

    org_name = details.get('org_name', 'None')
    org_tag = details.get('org_tag', 'None')
    
    org_widget = QWidget()
    org_layout = QVBoxLayout(org_widget)
    org_layout.setContentsMargins(0, 0, 0, 0)
    org_layout.setSpacing(4)
    
    if org_name != 'None' and org_name != 'Unknown':
        org_label = QLabel(f"{t('Organization')}: {org_name}")
        org_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 16px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        org_layout.addWidget(org_label)
        
        if org_tag != 'None' and org_tag != 'Unknown':
            tag_label = QLabel(f"{t('Tag')}: [{org_tag}]")
            tag_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['accent'].name()};
                    font-size: 14px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }}
            """)
            org_layout.addWidget(tag_label)
    else:
        org_label = QLabel(f"{t('Organization')}: {t('Independent')}")
        org_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 16px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        org_layout.addWidget(org_label)
    
    notification_layout.addWidget(org_widget)

    details_widget = QWidget()
    details_layout = QVBoxLayout(details_widget)
    details_layout.setContentsMargins(0, 0, 0, 0)
    details_layout.setSpacing(6)

    weapon_label = QLabel(f"{t('Weapon')}: {weapon_clean}")
    weapon_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['text_primary'].name()};
            font-size: 16px;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)

    location_label = QLabel(f"{t('Location')}: {formatted_zone}")
    location_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['text_primary'].name()};
            font-size: 16px;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)

    mode_label = QLabel(f"{t('Mode')}: {game_mode}")
    mode_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['info_color'].name()};
            font-size: 14px;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    
    details_layout.addWidget(weapon_label)
    details_layout.addWidget(location_label)
    details_layout.addWidget(mode_label)
    notification_layout.addWidget(details_widget)

    # Now populate the image if available
    if attacker_image_data_uri:
        try:
            if attacker_image_data_uri.startswith('data:image'):
                from PyQt5.QtGui import QPixmap
                import base64
                
                header, data = attacker_image_data_uri.split(',', 1)
                image_data = base64.b64decode(data)
                
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)

                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

                    circular_pixmap = QPixmap(80, 80)
                    circular_pixmap.fill(Qt.transparent)
                    
                    painter = QPainter(circular_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.setBrush(QBrush(scaled_pixmap))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(0, 0, 80, 80)

                    painter.setPen(QPen(QColor(self.colors['death_color']), 3))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(1, 1, 78, 78)
                    painter.end()
                    
                    image_label.setPixmap(circular_pixmap)
                    image_container.setVisible(True)
                    
        except Exception as e:
            image_label.setText("No Image")
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['text_secondary'].name()};
                    font-size: 10px;
                    background-color: {self.colors['background'].name()};
                    border: 2px solid {self.colors['death_color'].name()};
                    border-radius: 40px;
                }}
            """)
            image_container.setVisible(True)

    try:
        if self.faded_container and self.faded_container.layout():
            old_layout = self.faded_container.layout()
            while old_layout.count():
                child = old_layout.takeAt(0)
                if child.widget():
                    child.widget().setParent(None)
            old_layout.setParent(None)
    except (RuntimeError, AttributeError):
        pass
    
    new_layout = QVBoxLayout(self.faded_container)
    new_layout.setContentsMargins(0, 0, 0, 0)
    new_layout.addWidget(notification_widget)

    self.show_faded_notification()

def show_kill_notification(self, victim: str, weapon: str, zone: str, game_mode: str = "Unknown"):
    """Show kill notification in faded mode with org info and profile image"""
    if self.display_mode != 'faded':
        return

    self.stop_all_faded_animations()
    self.clear_faded_container()

    try:
        from fetch import fetch_player_details, fetch_victim_image_base64
        from kill_parser import KillParser
        import re
        
        details = fetch_player_details(victim)
        victim_image_data_uri = fetch_victim_image_base64(victim)
        formatted_zone = KillParser.format_zone(zone)
        formatted_weapon = KillParser.format_weapon(weapon)
        
        weapon_clean = re.sub(r'_\d+$', '', weapon)
        weapon_clean = weapon_clean.replace("_", " ")
        weapon_clean = re.sub(r'\s+\d+$', '', weapon_clean)
        if formatted_weapon != 'Unknown':
            weapon_clean = formatted_weapon
            
    except ImportError:
        details = {'org_name': 'Unknown', 'org_tag': 'Unknown'}
        victim_image_data_uri = ""
        formatted_zone = zone.replace('_', ' ').title()
        weapon_clean = clean_weapon_name(weapon)
    
    notification_widget = QWidget()
    notification_layout = QVBoxLayout(notification_widget)
    notification_layout.setContentsMargins(20, 15, 20, 15)
    notification_layout.setSpacing(10)
    
    header_row = QHBoxLayout()
    notification_layout.addLayout(header_row)
    
    header_text = QLabel(t("YOU KILLED"))
    header_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    header_text.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['kill_color'].name()};
            font-size: 24px;
            font-weight: bold;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    header_row.addWidget(header_text, 1)
    
    image_container = QWidget()
    image_container.setFixedSize(80, 80)
    image_container.setVisible(False)
    
    image_label = QLabel()
    image_label.setFixedSize(80, 80)
    
    image_layout = QVBoxLayout(image_container)
    image_layout.setContentsMargins(0, 0, 0, 0)
    image_layout.addWidget(image_label)
    
    header_row.addWidget(image_container, 0, Qt.AlignRight)
    
    victim_label = QLabel(t(victim.upper()))
    victim_label.setAlignment(Qt.AlignLeft)
    victim_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['death_color'].name()};
            font-size: 24px;
            font-weight: bold;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    notification_layout.addWidget(victim_label)
    
    org_name = details.get('org_name', 'None')
    org_tag = details.get('org_tag', 'None')
    
    org_widget = QWidget()
    org_layout = QVBoxLayout(org_widget)
    org_layout.setContentsMargins(0, 0, 0, 0)
    org_layout.setSpacing(4)
    
    if org_name != 'None' and org_name != 'Unknown':
        org_label = QLabel(f"{t('Organization')}: {org_name}")
        org_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 16px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        org_layout.addWidget(org_label)
        
        if org_tag != 'None' and org_tag != 'Unknown':
            tag_label = QLabel(f"{t('Tag')}: [{org_tag}]")
            tag_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['accent'].name()};
                    font-size: 14px;
                    font-family: 'Consolas', monospace;
                    background: transparent;
                }}
            """)
            org_layout.addWidget(tag_label)
    else:
        org_label = QLabel(f"{t('Organization')}: {t('Independent')}")
        org_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_secondary'].name()};
                font-size: 16px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        org_layout.addWidget(org_label)
    
    notification_layout.addWidget(org_widget)
    
    details_widget = QWidget()
    details_layout = QVBoxLayout(details_widget)
    details_layout.setContentsMargins(0, 0, 0, 0)
    details_layout.setSpacing(6)

    weapon_label = QLabel(f"{t('Weapon')}: {weapon_clean}")
    weapon_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['text_primary'].name()};
            font-size: 16px;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    
    location_label = QLabel(f"{t('Location')}: {formatted_zone}")
    location_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['text_primary'].name()};
            font-size: 16px;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    
    mode_label = QLabel(f"{t('Mode')}: {game_mode}")
    mode_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['info_color'].name()};
            font-size: 14px;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    
    details_layout.addWidget(weapon_label)
    details_layout.addWidget(location_label)
    details_layout.addWidget(mode_label)
    notification_layout.addWidget(details_widget)

    if victim_image_data_uri:
        try:
            if victim_image_data_uri.startswith('data:image'):
                from PyQt5.QtGui import QPixmap
                import base64
                
                header, data = victim_image_data_uri.split(',', 1)
                image_data = base64.b64decode(data)
                
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)

                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    
                    circular_pixmap = QPixmap(80, 80)
                    circular_pixmap.fill(Qt.transparent)
                    
                    painter = QPainter(circular_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.setBrush(QBrush(scaled_pixmap))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(0, 0, 80, 80)
                    
                    painter.setPen(QPen(QColor(self.colors['kill_color']), 3))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(1, 1, 78, 78)
                    painter.end()
                    
                    image_label.setPixmap(circular_pixmap)
                    image_container.setVisible(True)
                    
        except Exception as e:
            image_label.setText("No Image")
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['text_secondary'].name()};
                    font-size: 10px;
                    background-color: {self.colors['background'].name()};
                    border: 2px solid {self.colors['kill_color'].name()};
                    border-radius: 40px;
                }}
            """)
            image_container.setVisible(True)

    try:
        self.faded_container.setLayout(QVBoxLayout())
        self.faded_container.layout().setContentsMargins(0, 0, 0, 0)
        self.faded_container.layout().addWidget(notification_widget)
    except (RuntimeError, AttributeError):
        return
    
    self.show_faded_notification()

def show_faded_notification(self):
    """Show the faded notification and start timers"""
    if not hasattr(self, 'faded_container'):
        return

    if hasattr(self, 'positioning_mode') and self.positioning_mode:
        pass
    else:
        self.stop_all_faded_animations()

    try:
        self.faded_container.adjustSize()
        self.adjustSize()

        natural_size = self.faded_container.sizeHint()
        min_width = max(natural_size.width() + 20, 600)
        min_height = max(natural_size.height() + 20, 250)
    except (RuntimeError, AttributeError):
        min_width = 300
        min_height = 150
    self.resize(min_width, min_height)

    self.faded_container.show()
    self.setWindowOpacity(self.opacity_level)
    self.show()

    if not (hasattr(self, 'positioning_mode') and self.positioning_mode):
        if hasattr(self, 'fade_timer'):
            self.fade_timer.start(8000)

def show_faded_positioning_helper(self):
    """Show a temporary positioning helper for faded mode that matches notification size"""
    self.clear_faded_container()

    self.positioning_mode = True

    notification_widget = QWidget()
    notification_layout = QVBoxLayout(notification_widget)
    notification_layout.setContentsMargins(20, 15, 20, 15)
    notification_layout.setSpacing(10)
    
    header_row = QHBoxLayout()
    notification_layout.addLayout(header_row)
    
    header_text = QLabel(t("POSITIONING HELPER"))
    header_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    header_text.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['accent'].name()};
            font-size: 24px;
            font-weight: bold;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    header_row.addWidget(header_text, 1)
    
    image_container = QWidget()
    image_container.setFixedSize(80, 80)
    
    self.countdown_label = QLabel("30")
    self.countdown_label.setAlignment(Qt.AlignCenter)
    self.countdown_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['accent'].name()};
            font-size: 24px;
            font-weight: bold;
            font-family: 'Consolas', monospace;
            background-color: {self.colors['background'].name()};
            border: 3px solid {self.colors['accent'].name()};
            border-radius: 40px;
        }}
    """)
    self.countdown_label.setFixedSize(80, 80)
    
    image_layout = QVBoxLayout(image_container)
    image_layout.setContentsMargins(0, 0, 0, 0)
    image_layout.addWidget(self.countdown_label)
    
    header_row.addWidget(image_container, 0, Qt.AlignRight)
    
    player_label = QLabel(t("SAMPLE PLAYER NAME"))
    player_label.setAlignment(Qt.AlignLeft)
    player_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['text_primary'].name()};
            font-size: 20px;
            font-weight: bold;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    notification_layout.addWidget(player_label)

    org_widget = QWidget()
    org_layout = QVBoxLayout(org_widget)
    org_layout.setContentsMargins(0, 0, 0, 0)
    org_layout.setSpacing(4)
    
    org_label = QLabel(t("Organization") + ": " + t("Example Organization"))
    org_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['text_secondary'].name()};
            font-size: 16px;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    org_layout.addWidget(org_label)
    
    tag_label = QLabel(t("Tag") + ": [EXMP]")
    tag_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['accent'].name()};
            font-size: 14px;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    org_layout.addWidget(tag_label)
    
    notification_layout.addWidget(org_widget)

    # Details widget
    details_widget = QWidget()
    details_layout = QVBoxLayout(details_widget)
    details_layout.setContentsMargins(0, 0, 0, 0)
    details_layout.setSpacing(6)
    
    weapon_label = QLabel(t("Weapon") + ": " + t("Sample Weapon Name"))
    weapon_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['text_primary'].name()};
            font-size: 16px;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    
    location_label = QLabel(t("Location") + ": " + t("Sample Location"))
    location_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['text_primary'].name()};
            font-size: 16px;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    
    mode_label = QLabel(t("Mode") + ": " + t("Arena Commander"))
    mode_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['info_color'].name()};
            font-size: 14px;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    
    instruction_label = QLabel(t("Drag to position this overlay"))
    instruction_label.setStyleSheet(f"""
        QLabel {{
            color: {self.colors['accent'].name()};
            font-size: 12px;
            font-style: italic;
            font-family: 'Consolas', monospace;
            background: transparent;
        }}
    """)
    
    details_layout.addWidget(weapon_label)
    details_layout.addWidget(location_label)
    details_layout.addWidget(mode_label)
    details_layout.addWidget(instruction_label)
    notification_layout.addWidget(details_widget)

    try:
        self.faded_container.setLayout(QVBoxLayout())
        self.faded_container.layout().setContentsMargins(0, 0, 0, 0)
        self.faded_container.layout().addWidget(notification_widget)
    except (RuntimeError, AttributeError):
        return

    self.faded_container.adjustSize()
    self.adjustSize()

    natural_size = self.faded_container.sizeHint()
    min_width = max(natural_size.width() + 20, 300)
    min_height = max(natural_size.height() + 20, 150)
    self.resize(min_width, min_height)

    self.faded_container.show()
    self.show()

    self.countdown_seconds = 30
    self.countdown_timer = QTimer()
    self.countdown_timer.timeout.connect(self.update_countdown)
    self.countdown_timer.start(1000)

def stop_all_faded_animations(self):
    """Stop all animations and timers related to faded notifications"""

    if hasattr(self, 'fade_timer') and self.fade_timer.isActive():
        self.fade_timer.stop()
    
    if hasattr(self, 'fade_animation') and self.fade_animation.state() == QPropertyAnimation.Running:
        self.fade_animation.stop()
    
    self.setWindowOpacity(self.opacity_level)
    
    if hasattr(self, 'positioning_mode'):
        self.positioning_mode = False

def fade_notification(self):
    """Fade the notification (skip if in positioning mode)"""
    if hasattr(self, 'positioning_mode') and self.positioning_mode:
        return
    
    if not hasattr(self, 'faded_container') or not self.faded_container.isVisible():
        return
        
    if hasattr(self, 'fade_timer'):
        self.fade_timer.stop()

    self.fade_animation.setDuration(2000)
    self.fade_animation.setStartValue(self.opacity_level)
    self.fade_animation.setEndValue(0.0)
    self.fade_animation.setEasingCurve(QEasingCurve.OutQuad)
    self.fade_animation.start()

def hide_faded_notification(self):
    """Hide faded notification (skip if in positioning mode)"""
    if hasattr(self, 'positioning_mode') and self.positioning_mode:
        return
    
    if hasattr(self, 'fade_animation') and self.fade_animation.state() == QPropertyAnimation.Running:
        return
        
    if hasattr(self, 'faded_container'):
        self.faded_container.hide()
    self.hide()
    self.setWindowOpacity(self.opacity_level)

def hide_positioning_helper(self):
    """Hide the positioning helper and return to normal faded mode"""
    if hasattr(self, 'positioning_mode'):
        self.positioning_mode = False
        
    if hasattr(self, 'countdown_timer'):
        try:
            self.countdown_timer.stop()
            self.countdown_timer.deleteLater()
        except (RuntimeError, AttributeError):
            pass
        delattr(self, 'countdown_timer')
        
    if hasattr(self, 'countdown_label'):
        self.countdown_label = None
        delattr(self, 'countdown_label')
        
    if hasattr(self, 'countdown_seconds'):
        delattr(self, 'countdown_seconds')
        
    if hasattr(self, 'faded_container'):
        self.faded_container.hide()
        
    self.hide()
    self.resize(50, 50)

def update_countdown(self):
    """Update the countdown display"""
    if not hasattr(self, 'countdown_label') or not hasattr(self, 'countdown_seconds'):
        if hasattr(self, 'countdown_timer'):
            self.countdown_timer.stop()
        return
        
    try:
        if self.countdown_label is None or not hasattr(self.countdown_label, 'setText'):
            if hasattr(self, 'countdown_timer'):
                self.countdown_timer.stop()
            return
    except RuntimeError:
        if hasattr(self, 'countdown_timer'):
            self.countdown_timer.stop()
        return
        
    self.countdown_seconds -= 1
    
    if self.countdown_seconds > 0:
        try:
            self.countdown_label.setText(str(self.countdown_seconds))
            
            if self.countdown_seconds <= 10:
                color = self.colors['death_color'].name()
            elif self.countdown_seconds <= 30:
                color = self.colors['kill_color'].name()
            else:
                color = self.colors['accent'].name()
            
            self.countdown_label.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 24px;
                    font-weight: bold;
                    font-family: 'Consolas', monospace;
                    background-color: {self.colors['background'].name()};
                    border: 3px solid {color};
                    border-radius: 40px;
                }}
            """)
        except RuntimeError:
            if hasattr(self, 'countdown_timer'):
                self.countdown_timer.stop()
            return
    else:
        self.hide_positioning_helper()

def clear_faded_container(self):
    """Clear the faded container content safely"""

    if hasattr(self, 'countdown_timer') and self.countdown_timer.isActive():
        self.countdown_timer.stop()
        self.countdown_timer.deleteLater()
        if hasattr(self, 'countdown_timer'):
            delattr(self, 'countdown_timer')

    if hasattr(self, 'countdown_label'):
        self.countdown_label = None
        if hasattr(self, 'countdown_label'):
            delattr(self, 'countdown_label')
        
    if hasattr(self, 'countdown_seconds'):
        if hasattr(self, 'countdown_seconds'):
            delattr(self, 'countdown_seconds')

    if hasattr(self, 'faded_container') and self.faded_container is not None:
        try:
            if self.faded_container.layout():
                old_layout = self.faded_container.layout()
                while old_layout.count():
                    child = old_layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
        except RuntimeError:
            pass

    self.faded_container = QWidget()
    self.faded_container.setAttribute(Qt.WA_TransparentForMouseEvents)
    self.faded_container.setStyleSheet("background: transparent;")

    try:
        if hasattr(self, 'layout') and self.layout():
            self.layout().addWidget(self.faded_container)
    except (RuntimeError, AttributeError):
        pass

def clean_weapon_name(weapon_name: str) -> str:
    """Clean weapon name by removing long ID strings and replacing underscores with spaces"""
    weapon_name = re.sub(r'_\d+$', '', weapon_name)
    weapon_name = weapon_name.replace('_', ' ')
    weapon_name = re.sub(r'\s+\d+$', '', weapon_name)
    return weapon_name.strip()