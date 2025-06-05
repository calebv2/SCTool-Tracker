# filepath: c:\Users\caleb\OneDrive\Desktop\SCTool Tracker\overlays\custom_overlay.py
# custom_overlay.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient, 
    QRadialGradient, QFont, QFontMetrics
)

class MoveableComponent(QFrame):
    """A moveable component that can be dragged independently"""
    
    position_changed = pyqtSignal(str, QPoint)  # component_id, new_position
    
    def __init__(self, component_id: str, title: str, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.title = title
        self.is_dragging = False
        self.drag_position = QPoint()
        self.is_locked = False
        
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: rgba(20, 20, 20, 0.9);
                border: 2px solid #333333;
                border-radius: 8px;
            }
            QFrame:hover {
                border-color: #555555;
            }
        """)
        
        # Make it stay on top and frameless
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
    def set_locked(self, locked: bool):
        """Set whether this component can be moved"""
        self.is_locked = locked
        if locked:
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.SizeAllCursor)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton and not self.is_locked:
            self.is_dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if event.buttons() == Qt.LeftButton and self.is_dragging and not self.is_locked:
            new_pos = event.globalPos() - self.drag_position
            self.move(new_pos)
            self.position_changed.emit(self.component_id, new_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            event.accept()

class StatsComponent(MoveableComponent):
    """Component showing kills, deaths, and K/D ratio"""
    
    def __init__(self, overlay_instance, parent=None):
        super().__init__("stats", "Statistics", parent)
        self.overlay = overlay_instance
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        
        # Title
        title = QLabel("STATISTICS")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['accent'].name()};
                font-size: 14px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
                border: none;
            }}
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Stats grid
        stats_layout = QGridLayout()
        stats_layout.setSpacing(8)
        
        # Kills
        kills_label = QLabel("KILLS")
        kills_label.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['text_secondary'].name()};
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        self.kills_value = QLabel("0")
        self.kills_value.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['kill_color'].name()};
                font-size: 20px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.kills_value.setAlignment(Qt.AlignCenter)
        
        # Deaths
        deaths_label = QLabel("DEATHS")
        deaths_label.setStyleSheet(kills_label.styleSheet())
        self.deaths_value = QLabel("0")
        self.deaths_value.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['death_color'].name()};
                font-size: 20px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.deaths_value.setAlignment(Qt.AlignCenter)
        
        # K/D Ratio
        kd_label = QLabel("K/D")
        kd_label.setStyleSheet(kills_label.styleSheet())
        self.kd_value = QLabel("--")
        self.kd_value.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['info_color'].name()};
                font-size: 16px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.kd_value.setAlignment(Qt.AlignCenter)
        
        stats_layout.addWidget(kills_label, 0, 0)
        stats_layout.addWidget(self.kills_value, 1, 0)
        stats_layout.addWidget(deaths_label, 0, 1)
        stats_layout.addWidget(self.deaths_value, 1, 1)
        stats_layout.addWidget(kd_label, 0, 2)
        stats_layout.addWidget(self.kd_value, 1, 2)
        
        layout.addLayout(stats_layout)
        
        # Adjust size
        self.adjustSize()
        self.setFixedSize(self.sizeHint())

class SessionInfoComponent(MoveableComponent):
    """Component showing session information"""
    
    def __init__(self, overlay_instance, parent=None):
        super().__init__("session", "Session Info", parent)
        self.overlay = overlay_instance
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # Title
        title = QLabel("SESSION")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['accent'].name()};
                font-size: 14px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
                border: none;
            }}
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Session time
        self.session_time_label = QLabel("Time: 00:00")
        self.session_time_label.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['info_color'].name()};
                font-size: 16px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        layout.addWidget(self.session_time_label)
        
        # Game mode
        self.game_mode_label = QLabel("Mode: Unknown")
        self.game_mode_label.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['text_secondary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.game_mode_label.setWordWrap(True)
        layout.addWidget(self.game_mode_label)
        
        # Ship
        self.ship_label = QLabel("Ship: Unknown")
        self.ship_label.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['text_secondary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.ship_label.setWordWrap(True)
        layout.addWidget(self.ship_label)
        
        # Adjust size
        self.adjustSize()
        self.setFixedSize(self.sizeHint())

class NotificationComponent(MoveableComponent):
    """Component for showing kill/death notifications (faded style)"""
    
    def __init__(self, overlay_instance, parent=None):
        super().__init__("notification", "Notifications", parent)
        self.overlay = overlay_instance
        self.notification_timer = QTimer()
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.setup_ui()
        self.hide()  # Hidden by default
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 12, 15, 12)
        self.main_layout.setSpacing(8)
        
        # Notification content will be added dynamically
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_layout.addWidget(self.content_widget)
        
        # Setup auto-hide timer
        self.notification_timer.timeout.connect(self.start_fade_out)
        self.fade_animation.finished.connect(self.hide)
        
    def show_kill_notification(self, victim: str, weapon: str, zone: str, game_mode: str = "Unknown"):
        """Show kill notification"""
        self.clear_content()
        
        # Header
        header = QLabel("YOU KILLED")
        header.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['kill_color'].name()};
                font-size: 24px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        header.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(header)
        
        # Victim
        victim_label = QLabel(f"VICTIM: {victim.upper()}")
        victim_label.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['text_primary'].name()};
                font-size: 18px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        victim_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(victim_label)
        
        # Details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(4)
        
        weapon_clean = self.overlay.clean_weapon_name(weapon)
        formatted_zone = zone.replace('_', ' ').title()
        
        weapon_label = QLabel(f"Weapon: {weapon_clean}")
        weapon_label.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['text_primary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        location_label = QLabel(f"Location: {formatted_zone}")
        location_label.setStyleSheet(weapon_label.styleSheet())
        
        mode_label = QLabel(f"Mode: {game_mode}")
        mode_label.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['info_color'].name()};
                font-size: 12px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        details_layout.addWidget(weapon_label)
        details_layout.addWidget(location_label)
        details_layout.addWidget(mode_label)
        
        self.content_layout.addLayout(details_layout)
        
        self.show_notification()
        
    def show_death_notification(self, attacker: str, weapon: str, zone: str, game_mode: str = "Unknown"):
        """Show death notification"""
        self.clear_content()
        
        # Header
        header = QLabel("YOU DIED")
        header.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['death_color'].name()};
                font-size: 24px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        header.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(header)
        
        # Attacker
        attacker_label = QLabel(f"KILLED BY: {attacker.upper()}")
        attacker_label.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['text_primary'].name()};
                font-size: 18px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        attacker_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(attacker_label)
        
        # Details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(4)
        
        weapon_clean = self.overlay.clean_weapon_name(weapon)
        formatted_zone = zone.replace('_', ' ').title()
        
        weapon_label = QLabel(f"Weapon: {weapon_clean}")
        weapon_label.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['text_primary'].name()};
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        location_label = QLabel(f"Location: {formatted_zone}")
        location_label.setStyleSheet(weapon_label.styleSheet())
        
        mode_label = QLabel(f"Mode: {game_mode}")
        mode_label.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['info_color'].name()};
                font-size: 12px;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        
        details_layout.addWidget(weapon_label)
        details_layout.addWidget(location_label)
        details_layout.addWidget(mode_label)
        
        self.content_layout.addLayout(details_layout)
        
        self.show_notification()
        
    def show_notification(self):
        """Show the notification with fade in"""
        self.adjustSize()
        self.setFixedSize(self.sizeHint())
        self.setWindowOpacity(0.0)
        self.show()
        
        # Fade in
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.start()
          # Auto-hide after 4 seconds
        self.notification_timer.start(4000)
        
    def start_fade_out(self):
        """Start fade out animation - allows moving during fade like faded overlay"""
        self.notification_timer.stop()
        self.fade_animation.setDuration(2000)  # Longer fade like faded overlay
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutQuad)  # Same easing as faded overlay
        self.fade_animation.start()
        
    def clear_content(self):
        """Clear existing content"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

class KillStreakComponent(MoveableComponent):
    """Component showing current kill streak"""
    
    def __init__(self, overlay_instance, parent=None):
        super().__init__("killstreak", "Kill Streak", parent)
        self.overlay = overlay_instance
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # Title
        title = QLabel("STREAK")
        title.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['accent'].name()};
                font-size: 14px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
                border: none;
            }}
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Streak value
        self.streak_value = QLabel("0")
        self.streak_value.setStyleSheet(f"""
            QLabel {{
                color: {self.overlay.colors['kill_color'].name()};
                font-size: 32px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                background: transparent;
            }}
        """)
        self.streak_value.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.streak_value)
        
        # Adjust size
        self.adjustSize()
        self.setFixedSize(self.sizeHint())

def create_custom_ui(self):
    """Create custom moveable overlay with detailed stats and faded notifications"""
    # Create main container (invisible)
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    
    # Create a minimal main widget for the mode button
    main_widget = QWidget()
    main_widget.setStyleSheet("background: transparent;")
    main_layout = QHBoxLayout(main_widget)
    main_layout.setContentsMargins(8, 8, 8, 8)
    
    # Mode cycle button
    mode_btn = QPushButton("⚙")
    mode_btn.setFixedSize(24, 24)
    mode_btn.clicked.connect(self.cycle_display_mode)
    mode_btn.setStyleSheet(f"""
        QPushButton {{
            background: rgba(20, 20, 20, 0.9);
            border: 2px solid {self.colors['border'].name()};
            border-radius: 12px;
            color: {self.colors['text_secondary'].name()};
            font-size: 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: {self.colors['accent'].name()};
        }}
    """)
    main_layout.addWidget(mode_btn)
    
    layout.addWidget(main_widget)
    self.setLayout(layout)
    
    # Create moveable components
    self.create_moveable_components()
    
    # Load component positions
    self.load_component_positions()
    
    # Resize main widget to minimal size
    self.setFixedSize(40, 40)

def create_moveable_components(self):
    """Create all moveable components"""
    # Store components
    self.custom_components = {}
    
    # Stats component
    self.stats_component = StatsComponent(self)
    self.stats_component.position_changed.connect(self.save_component_position)
    self.custom_components['stats'] = self.stats_component
    
    # Session info component
    self.session_component = SessionInfoComponent(self)
    self.session_component.position_changed.connect(self.save_component_position)
    self.custom_components['session'] = self.session_component
    
    # Notification component
    self.notification_component = NotificationComponent(self)
    self.notification_component.position_changed.connect(self.save_component_position)
    self.custom_components['notification'] = self.notification_component
    
    # Kill streak component
    self.streak_component = KillStreakComponent(self)
    self.streak_component.position_changed.connect(self.save_component_position)
    self.custom_components['killstreak'] = self.streak_component
    
    # Show all components initially
    for component in self.custom_components.values():
        if component != self.notification_component:  # Notification starts hidden
            component.show()

def load_component_positions(self):
    """Load saved positions for components"""
    positions = self.config.get('custom_component_positions', {})
    
    # Default positions relative to main overlay
    main_pos = self.pos()
    defaults = {
        'stats': QPoint(main_pos.x() + 60, main_pos.y()),
        'session': QPoint(main_pos.x() + 200, main_pos.y()),
        'notification': QPoint(main_pos.x() + 100, main_pos.y() + 100),
        'killstreak': QPoint(main_pos.x() + 60, main_pos.y() + 150)
    }
    
    for component_id, component in self.custom_components.items():
        if component_id in positions:
            pos = QPoint(positions[component_id]['x'], positions[component_id]['y'])
        else:
            pos = defaults.get(component_id, QPoint(100, 100))
        component.move(pos)

def save_component_position(self, component_id: str, position: QPoint):
    """Save component position to config"""
    if 'custom_component_positions' not in self.config:
        self.config['custom_component_positions'] = {}
    
    self.config['custom_component_positions'][component_id] = {
        'x': position.x(),
        'y': position.y()
    }
    self.save_config()

def set_custom_components_locked(self, locked: bool):
    """Set locked state for all components"""
    if hasattr(self, 'custom_components'):
        for component in self.custom_components.values():
            component.set_locked(locked)

def hide_custom_components(self):
    """Hide all custom components"""
    if hasattr(self, 'custom_components'):
        for component in self.custom_components.values():
            component.hide()

def show_custom_components(self):
    """Show all custom components (except notification which shows on events)"""
    if hasattr(self, 'custom_components'):
        for component_id, component in self.custom_components.items():
            if component_id != 'notification':  # Notification shows only on events
                component.show()

def update_custom_stats(self, kills: int, deaths: int, kill_streak: int = 0):
    """Update stats in custom components"""
    if hasattr(self, 'stats_component'):
        self.stats_component.kills_value.setText(str(kills))
        self.stats_component.deaths_value.setText(str(deaths))
        
        # Calculate K/D ratio
        if deaths > 0:
            kd_ratio = kills / deaths
            self.stats_component.kd_value.setText(f"{kd_ratio:.2f}")
        else:
            self.stats_component.kd_value.setText("∞" if kills > 0 else "--")
    
    if hasattr(self, 'streak_component'):
        self.streak_component.streak_value.setText(str(kill_streak))

def update_custom_session_info(self, session_time: str, ship: str, game_mode: str):
    """Update session info in custom components"""
    if hasattr(self, 'session_component'):
        self.session_component.session_time_label.setText(f"Time: {session_time}")
        self.session_component.ship_label.setText(f"Ship: {ship}")
        self.session_component.game_mode_label.setText(f"Mode: {game_mode}")

def show_custom_kill_notification(self, victim: str, weapon: str, zone: str, game_mode: str = "Unknown"):
    """Show kill notification in custom notification component"""
    if hasattr(self, 'notification_component'):
        self.notification_component.show_kill_notification(victim, weapon, zone, game_mode)

def show_custom_death_notification(self, attacker: str, weapon: str, zone: str, game_mode: str = "Unknown"):
    """Show death notification in custom notification component"""
    if hasattr(self, 'notification_component'):
        self.notification_component.show_death_notification(attacker, weapon, zone, game_mode)