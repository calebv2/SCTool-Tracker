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
from language_manager import t
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
        
        header = QLabel(t("GAME OVERLAY"))
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
        
        desc = QLabel(t("Overlay system with multiple display modes, customizable themes, "
                     "and real-time statistics. The overlay shows your kill/death stats, session information, "
                     "and latest kill details while playing Star Citizen."))
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
        self.basic_group = QGroupBox(t("Basic Controls"))
        self.basic_group.setStyleSheet("QGroupBox { color: #f0f0f0; }")
        basic_layout = QVBoxLayout(self.basic_group)
        basic_layout.setSpacing(10)

        self.enable_checkbox = QCheckBox(t("Enable Game Overlay"))
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
        
        self.lock_checkbox = QCheckBox(t("Lock Overlay Position"))
        self.lock_checkbox.setChecked(self.overlay.is_locked)
        self.lock_checkbox.setStyleSheet(self.enable_checkbox.styleSheet())
        self.lock_checkbox.toggled.connect(self.overlay.set_locked)
        basic_layout.addWidget(self.lock_checkbox)
        
        mode_layout = QHBoxLayout()
        self.mode_label_text = QLabel(t("Display Mode") + ":")
        self.mode_label_text.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; }")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([t("Minimal"), t("Compact"), t("Detailed"), t("Horizontal"), t("Faded")])
        
        current_mode = self.overlay.display_mode.lower()
        mode_translations = {
            "minimal": t("Minimal"),
            "compact": t("Compact"), 
            "detailed": t("Detailed"),
            "horizontal": t("Horizontal"),
            "faded": t("Faded")
        }
        current_translated = mode_translations.get(current_mode, t("Compact"))
        self.mode_combo.setCurrentText(current_translated)
        
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
        
        mode_layout.addWidget(self.mode_label_text)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        basic_layout.addLayout(mode_layout)
        
        content_layout.addWidget(self.basic_group)
        
        self.appearance_group = QGroupBox(t("Appearance"))
        self.appearance_group.setStyleSheet("QGroupBox { color: #f0f0f0; }")
        appearance_layout = QVBoxLayout(self.appearance_group)
        appearance_layout.setSpacing(10)
        
        opacity_layout = QHBoxLayout()
        self.opacity_label_text = QLabel(t("Opacity") + ":")
        self.opacity_label_text.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; }")
        
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
        
        opacity_layout.addWidget(self.opacity_label_text)
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        appearance_layout.addLayout(opacity_layout)
        
        theme_layout = QHBoxLayout()
        self.theme_label_text = QLabel(t("Theme:"))
        self.theme_label_text.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; }")
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([t("Default"), t("Dark"), t("Neon")])
        self.theme_combo.setCurrentText(self.overlay.theme.title())
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        self.theme_combo.setStyleSheet(self.mode_combo.styleSheet())
        
        theme_layout.addWidget(self.theme_label_text)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        appearance_layout.addLayout(theme_layout)
        
        self.animations_checkbox = QCheckBox(t("Enable Animations"))
        self.animations_checkbox.setChecked(self.overlay.show_animations)
        self.animations_checkbox.setStyleSheet(self.enable_checkbox.styleSheet())
        self.animations_checkbox.toggled.connect(self.overlay.toggle_animations)
        appearance_layout.addWidget(self.animations_checkbox)
        
        content_layout.addWidget(self.appearance_group)

        self.position_group = QGroupBox(t("Position & Size"))
        self.position_group.setStyleSheet("QGroupBox { color: #f0f0f0; }")
        position_layout = QVBoxLayout(self.position_group)
        position_layout.setSpacing(10)
        
        pos_buttons_layout = QHBoxLayout()
        
        self.pos_tl_btn = QPushButton(t("Top Left"))
        self.pos_tl_btn.clicked.connect(lambda: self.set_position("top-left"))
        
        self.pos_tr_btn = QPushButton(t("Top Right"))
        self.pos_tr_btn.clicked.connect(lambda: self.set_position("top-right"))
        
        self.pos_bl_btn = QPushButton(t("Bottom Left"))
        self.pos_bl_btn.clicked.connect(lambda: self.set_position("bottom-left"))
        
        self.pos_br_btn = QPushButton(t("Bottom Right"))
        self.pos_br_btn.clicked.connect(lambda: self.set_position("bottom-right"))
        
        self.pos_center_btn = QPushButton(t("Center"))
        self.pos_center_btn.clicked.connect(lambda: self.set_position("center"))
        
        for btn in [self.pos_tl_btn, self.pos_tr_btn, self.pos_bl_btn, self.pos_br_btn, self.pos_center_btn]:
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
        
        reset_btn = QPushButton(t("Reset to Default"))
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
        
        content_layout.addWidget(self.position_group)
        
        self.hotkey_group = QGroupBox(t("Global Hotkey"))
        self.hotkey_group.setStyleSheet("QGroupBox { color: #f0f0f0; }")
        hotkey_layout = QVBoxLayout(self.hotkey_group)
        hotkey_layout.setSpacing(10)
        
        self.hotkey_checkbox = QCheckBox(t("Enable Global Hotkey"))
        self.hotkey_checkbox.setChecked(self.overlay.hotkey_enabled)
        self.hotkey_checkbox.setStyleSheet(self.enable_checkbox.styleSheet())
        self.hotkey_checkbox.toggled.connect(self.overlay.set_hotkey_enabled)
        hotkey_layout.addWidget(self.hotkey_checkbox)
        
        current_hotkey_layout = QHBoxLayout()
        self.current_hotkey_label = QLabel(t("Current Hotkey") + ":")
        self.current_hotkey_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; }")
        
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
        
        current_hotkey_layout.addWidget(self.current_hotkey_label)
        current_hotkey_layout.addWidget(self.current_hotkey_display)
        current_hotkey_layout.addStretch()
        hotkey_layout.addLayout(current_hotkey_layout)
        
        self.hotkey_capture = HotkeyCapture()
        self.hotkey_capture.hotkey_captured.connect(self.on_hotkey_captured)
        hotkey_layout.addWidget(self.hotkey_capture)
        
        self.hotkey_info = QLabel(t("Use the capture button to record a key combination"))
        self.hotkey_info.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 12px;
                font-style: italic;
            }
        """)
        self.hotkey_info.setWordWrap(True)
        hotkey_layout.addWidget(self.hotkey_info)
        
        content_layout.addWidget(self.hotkey_group)

        self.instructions = QLabel(f"""
        <b>{t('Instructions:')}</b><br>
        • {t('Left-click and drag to move the overlay')}<br>
        • {t('Ctrl + Mouse wheel to adjust opacity')}<br>
        • {t('Click the mode button (●/◐) on overlay to cycle modes')}<br>
        • {t('Use global hotkey to toggle overlay visibility')}<br>
        • {t('Overlay stays on top of all windows including games')}
        """)
        self.instructions.setStyleSheet("""
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
        self.instructions.setWordWrap(True)
        content_layout.addWidget(self.instructions)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

        self.helper_btn = QPushButton(t("Show Faded Mode Helper"))
        self.helper_btn.clicked.connect(self.show_faded_helper)
        self.helper_btn.setStyleSheet("""
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
        position_layout.addWidget(self.helper_btn)
        
        reset_btn = QPushButton(t("Reset to Default"))
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
        print(t("Captured hotkey: %s") % hotkey_string)
        self.current_hotkey_display.setText(hotkey_string)
        self.overlay.set_hotkey_combination(hotkey_string)

    
    def change_hotkey(self, combination: str):
        """Change global hotkey combination"""
        if combination.strip():
            clean_combo = combination.strip().lower()
            print(t("Changing hotkey to: %s") % clean_combo)
            
            test_thread = GlobalHotkeyThread(clean_combo)
            if test_thread.key_code == 0:
                print(t("Invalid hotkey combination: %s") % clean_combo)
                self.hotkey_capture.status_label.setText(t("Invalid combination! Try again."))
                return
            
            self.current_hotkey_display.setText(clean_combo)
            self.overlay.set_hotkey_combination(clean_combo)
            self.hotkey_capture.status_label.setText(t("Applied") + f": {clean_combo}")

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
        mode_map = {
            t("Minimal"): "minimal",
            t("Compact"): "compact", 
            t("Detailed"): "detailed",
            t("Horizontal"): "horizontal",
            t("Faded"): "faded"
        }
        
        if mode_text.lower() in ["minimal", "compact", "detailed", "horizontal", "faded"]:
            mode = mode_text.lower()
        else:
            mode = mode_map.get(mode_text, mode_text.lower())
        
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
    
    def update_translations(self):
        """Update all translatable text in the overlay control panel"""
        try:
            if hasattr(self, 'header'):
                for child in self.findChildren(QLabel):
                    if child.text() == "GAME OVERLAY":
                        child.setText(t("GAME OVERLAY"))
                        break
            
            if hasattr(self, 'enable_checkbox'):
                self.enable_checkbox.setText(t("Enable Game Overlay"))
            if hasattr(self, 'lock_checkbox'):
                self.lock_checkbox.setText(t("Lock Overlay Position"))
            if hasattr(self, 'animations_checkbox'):
                self.animations_checkbox.setText(t("Enable Animations"))
            if hasattr(self, 'hotkey_checkbox'):
                self.hotkey_checkbox.setText(t("Enable Global Hotkey"))
            
            for group in self.findChildren(QGroupBox):
                if group.title() == "Basic Controls":
                    group.setTitle(t("Basic Controls"))
                elif group.title() == "Controles Básicos":
                    group.setTitle(t("Basic Controls"))
                elif group.title() == "Appearance":
                    group.setTitle(t("Appearance"))
                elif group.title() == "Apariencia":
                    group.setTitle(t("Appearance"))
                elif group.title() == "Hotkey Settings":
                    group.setTitle(t("Hotkey Settings"))
                elif group.title() == "Configuración de Teclas de Acceso Rápido":
                    group.setTitle(t("Hotkey Settings"))
                elif group.title() == "Position":
                    group.setTitle(t("Position"))
                elif group.title() == "Posición":
                    group.setTitle(t("Position"))
            
            for label in self.findChildren(QLabel):
                label_text = label.text()
                if label_text == "Display Mode:":
                    label.setText(t("Display Mode") + ":")
                elif label_text == "Modo de Visualización:":
                    label.setText(t("Display Mode") + ":")
                elif label_text == "Opacity:":
                    label.setText(t("Opacity") + ":")
                elif label_text == "Opacidad:":
                    label.setText(t("Opacity") + ":")
                elif label_text == "Theme:":
                    label.setText(t("Theme") + ":")
                elif label_text == "Tema:":
                    label.setText(t("Theme") + ":")
                elif label_text == "Global Hotkey:":
                    label.setText(t("Global Hotkey") + ":")
                elif label_text == "Tecla Rápida Global:":
                    label.setText(t("Global Hotkey") + ":")
                elif label_text == "Current Hotkey:":
                    label.setText(t("Current Hotkey") + ":")
                elif label_text == "Tecla Rápida Actual:":
                    label.setText(t("Current Hotkey") + ":")
                elif label_text == "Font Size:":
                    label.setText(t("Font Size") + ":")
            
            if hasattr(self, 'mode_combo'):
                current_mode = self.overlay.display_mode.lower()
                self.mode_combo.clear()
                self.mode_combo.addItems([t("Minimal"), t("Compact"), t("Detailed"), t("Horizontal"), t("Faded")])
                mode_translations = {
                    "minimal": t("Minimal"),
                    "compact": t("Compact"), 
                    "detailed": t("Detailed"),
                    "horizontal": t("Horizontal"),
                    "faded": t("Faded")
                }
                current_translated = mode_translations.get(current_mode, t("Compact"))
                self.mode_combo.setCurrentText(current_translated)
            
            if hasattr(self, 'instructions'):
                self.instructions.setText(f"""
        <b>{t('Instructions:')}</b><br>
        • {t('Left-click and drag to move the overlay')}<br>
        • {t('Ctrl + Mouse wheel to adjust opacity')}<br>
        • {t('Click the mode button (●/◐) on overlay to cycle modes')}<br>
        • {t('Use global hotkey to toggle overlay visibility')}<br>
        • {t('Overlay stays on top of all windows including games')}
        """)
            
            if hasattr(self, 'hotkey_info'):
                self.hotkey_info.setText(t("Use the capture button to record a key combination"))
            
            if hasattr(self, 'pos_tl_btn'):
                self.pos_tl_btn.setText(t("Top Left"))
            if hasattr(self, 'pos_tr_btn'):
                self.pos_tr_btn.setText(t("Top Right"))
            if hasattr(self, 'pos_bl_btn'):
                self.pos_bl_btn.setText(t("Bottom Left"))
            if hasattr(self, 'pos_br_btn'):
                self.pos_br_btn.setText(t("Bottom Right"))
            if hasattr(self, 'pos_center_btn'):
                self.pos_center_btn.setText(t("Center"))
            if hasattr(self, 'helper_btn'):
                self.helper_btn.setText(t("Show Faded Mode Helper"))
            if hasattr(self, 'mode_label_text'):
                self.mode_label_text.setText(t("Display Mode") + ":")
            if hasattr(self, 'opacity_label_text'):
                self.opacity_label_text.setText(t("Opacity") + ":")
            if hasattr(self, 'theme_label_text'):
                self.theme_label_text.setText(t("Theme:"))
            if hasattr(self, 'current_hotkey_label'):
                self.current_hotkey_label.setText(t("Current Hotkey") + ":")
            if hasattr(self, 'hotkey_group'):
                self.hotkey_group.setTitle(t("Global Hotkey"))
            if hasattr(self, 'basic_group'):
                self.basic_group.setTitle(t("Basic Controls"))
            if hasattr(self, 'appearance_group'):
                self.appearance_group.setTitle(t("Appearance"))
            if hasattr(self, 'position_group'):
                self.position_group.setTitle(t("Position & Size"))
            
            position_button_texts = ["Top Left", "Top Right", "Bottom Left", "Bottom Right", "Center"]
            spanish_position_texts = ["Arriba Izquierda", "Arriba Derecha", "Abajo Izquierda", "Abajo Derecha", "Centro"]
            
            for button in self.findChildren(QPushButton):
                button_text = button.text()
                
                if button_text == "Reset to Default":
                    button.setText(t("Reset to Default"))
                elif button_text == "Reset Position":
                    button.setText(t("Reset Position"))
                elif button_text == "Show Overlay":
                    button.setText(t("Show Overlay"))
                elif button_text == "Capture":
                    button.setText(t("Capture"))
                elif button_text == "Clear":
                    button.setText(t("Clear"))
                elif button_text == "Save":
                    button.setText(t("Save"))
                elif button_text == "Cancel":
                    button.setText(t("Cancel"))
                elif button_text == "Hide Overlay":
                    button.setText(t("Hide Overlay"))
                elif button_text == "Click to Capture":
                    button.setText(t("Click to Capture"))
                elif button_text == "Show Faded Mode Helper":
                    button.setText(t("Show Faded Mode Helper"))
                elif button_text == "Mostrar Ayuda del Modo Desvanecido":
                    button.setText(t("Show Faded Mode Helper"))
                elif button_text in position_button_texts or button_text in spanish_position_texts:
                    if button_text in ["Top Left", "Arriba Izquierda"]:
                        button.setText(t("Top Left"))
                    elif button_text in ["Top Right", "Arriba Derecha"]:
                        button.setText(t("Top Right"))
                    elif button_text in ["Bottom Left", "Abajo Izquierda"]:
                        button.setText(t("Bottom Left"))
                    elif button_text in ["Bottom Right", "Abajo Derecha"]:
                        button.setText(t("Bottom Right"))
                    elif button_text in ["Center", "Centro"]:
                        button.setText(t("Center"))
        
            if hasattr(self, 'hotkey_capture'):
                self.hotkey_capture.update_translations()
        
        except Exception as e:
            print(t("Error updating overlay control panel translations: %s") % e)