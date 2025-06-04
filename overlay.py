# overlay.py

import json
import os
import re
import base64
from datetime import datetime
import sys
import ctypes
from ctypes import wintypes
import threading
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, 
    QCheckBox, QPushButton, QSlider, QComboBox, QSpinBox,
    QColorDialog, QGroupBox, QGridLayout, QTextEdit, QScrollArea,
    QApplication
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize, QPropertyAnimation, QEasingCurve, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QLinearGradient, 
    QRadialGradient, QPixmap, QPainterPath, QFontMetrics
)

from overlays import GameOverlay, HotkeyCapture, GlobalHotkeyThread

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
        self.mode_combo.addItems(["Minimal", "Compact", "Detailed", "Horizontal", "Faded"])
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
        
        hotkey_group = QGroupBox("Global Hotkey")
        hotkey_group.setStyleSheet("QGroupBox { color: #f0f0f0; }")
        hotkey_layout = QVBoxLayout(hotkey_group)
        hotkey_layout.setSpacing(10)
        
        self.hotkey_checkbox = QCheckBox("Enable Global Hotkey")
        self.hotkey_checkbox.setChecked(self.overlay.hotkey_enabled)
        self.hotkey_checkbox.setStyleSheet(self.enable_checkbox.styleSheet())
        self.hotkey_checkbox.toggled.connect(self.overlay.set_hotkey_enabled)
        hotkey_layout.addWidget(self.hotkey_checkbox)
        
        current_hotkey_layout = QHBoxLayout()
        current_label = QLabel("Current Hotkey:")
        current_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; }")
        
        self.current_hotkey_display = QLabel(self.overlay.hotkey_combination)
        self.current_hotkey_display.setStyleSheet("""
            QLabel {
                color: #00ff41;
                font-size: 14px;
                font-family: 'Consolas', monospace;
                background-color: #2a2a2a;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px;
                min-width: 100px;
            }
        """)
        
        current_hotkey_layout.addWidget(current_label)
        current_hotkey_layout.addWidget(self.current_hotkey_display)
        current_hotkey_layout.addStretch()
        hotkey_layout.addLayout(current_hotkey_layout)
        
        self.hotkey_capture = HotkeyCapture()
        self.hotkey_capture.hotkey_captured.connect(self.on_hotkey_captured)
        hotkey_layout.addWidget(self.hotkey_capture)
        
        hotkey_info = QLabel("Use the capture button to record a key combination. Examples: 'ctrl+`', 'alt+f1', 'ctrl+shift+h'")
        hotkey_info.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 12px;
                font-style: italic;
            }
        """)
        hotkey_info.setWordWrap(True)
        hotkey_layout.addWidget(hotkey_info)
        
        content_layout.addWidget(hotkey_group)

        instructions = QLabel("""
        <b>Instructions:</b><br>
        • Left-click and drag to move the overlay<br>
        • Ctrl + Mouse wheel to adjust opacity<br>
        • Click the mode button (◐/◑) on overlay to cycle modes<br>
        • Use global hotkey to toggle overlay visibility<br>
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

        helper_btn = QPushButton("Show Faded Mode Helper")
        helper_btn.clicked.connect(self.show_faded_helper)
        helper_btn.setStyleSheet("""
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
        position_layout.addWidget(helper_btn)
        
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self.reset_position)
    
    def show_faded_helper(self):
        """Manually show the faded positioning helper"""
        if self.overlay.display_mode == 'faded':
            self.overlay.show_faded_positioning_helper()
        else:
            old_mode = self.overlay.display_mode
            self.overlay.display_mode = 'faded'
            self.overlay.create_ui()
            self.overlay.show_faded_positioning_helper()
            
            def restore_mode():
                self.overlay.display_mode = old_mode
                self.overlay.config['display_mode'] = old_mode
                self.overlay.create_ui()
                self.overlay.update_display()
                if self.overlay.is_enabled:
                    self.overlay.show_overlay()
            
            QTimer.singleShot(6000, restore_mode)

    def on_hotkey_captured(self, hotkey_string):
        """Handle captured hotkey"""
        print(f"Captured hotkey: {hotkey_string}")
        self.current_hotkey_display.setText(hotkey_string)
        self.overlay.set_hotkey_combination(hotkey_string)

    
    def change_hotkey(self, combination: str):
        """Change global hotkey combination"""
        if combination.strip():
            clean_combo = combination.strip().lower()
            print(f"Changing hotkey to: {clean_combo}")
            
            test_thread = GlobalHotkeyThread(clean_combo)
            if test_thread.key_code == 0:
                print(f"Invalid hotkey combination: {clean_combo}")
                self.hotkey_capture.status_label.setText("Invalid combination! Try again.")
                return
            
            self.current_hotkey_display.setText(clean_combo)
            self.overlay.set_hotkey_combination(clean_combo)
            self.hotkey_capture.status_label.setText(f"Applied: {clean_combo}")

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

        if mode == 'faded':
            self.overlay.hide()
            QTimer.singleShot(100, self.overlay.show_faded_positioning_helper)
        elif self.overlay.is_enabled:
            self.overlay.show_overlay()
    
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