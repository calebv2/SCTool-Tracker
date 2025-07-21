# language_selector_widget.py

import logging
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QSizePolicy
from PyQt5.QtCore import pyqtSignal
from language_manager import language_manager, t

class LanguageSelector(QWidget):
    """Widget for selecting application language"""
    
    language_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_languages()
        
    def setup_ui(self):
        """Setup the language selector UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        self.language_label = QLabel("Language:")
        self.language_label.setStyleSheet(
            "QLabel { color: #ffffff; font-weight: 500; background: transparent; border: none; font-size: 14px; }"
        )
        self.language_label.setMinimumWidth(80)
        
        self.language_combo = QComboBox()
        self.language_combo.setStyleSheet("""
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
        
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        
        self.language_combo.setMaxVisibleItems(10)
        self.language_combo.view().setMinimumWidth(250)
        
        self.language_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        layout.addWidget(self.language_combo, 1)
        
        self.setMinimumHeight(50)
        self.setMinimumWidth(250)
        
    def load_languages(self):
        """Load available languages into the combo box"""
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        
        available_languages = language_manager.get_available_languages()
        current_language = language_manager.current_language
        
        for code, name in available_languages.items():
            self.language_combo.addItem(name, code)
            if code == current_language:
                self.language_combo.setCurrentText(name)
                
        self.language_combo.blockSignals(False)
        
    def on_language_changed(self, language_name):
        """Handle language selection change"""
        if not language_name:
            return
            
        try:
            print(f"Language selector: changing to '{language_name}'")
            available_languages = language_manager.get_available_languages()
            selected_code = None
            
            for code, name in available_languages.items():
                if name == language_name:
                    selected_code = code
                    break
                    
            if not selected_code:
                print(f"Error: Could not find language code for '{language_name}'")
                return
                
            print(f"Language selector: found code '{selected_code}' for '{language_name}'")
            
            if hasattr(language_manager, 'force_language_change'):
                main_app = None
                try:
                    parent = self.parent()
                    while parent and not hasattr(parent, 'nav_buttons'):
                        parent = parent.parent()
                    if parent and hasattr(parent, 'nav_buttons'):
                        main_app = parent
                except:
                    pass
                
                success = language_manager.force_language_change(selected_code, main_app)
            else:
                success = language_manager.set_language(selected_code)
            
            if success:
                print(f"Language successfully changed to '{selected_code}'")
                
                try:
                    from Kill_form import get_appdata_paths
                    config_file, _, _ = get_appdata_paths()
                    language_manager.save_current_language_preference(config_file)
                    print("Language preference saved to config")
                except Exception as e:
                    logging.error(f"Failed to save language preference: {e}")
                    print(f"Error saving language preference: {e}")
                
                self.update_text()
                
                print(f"Emitting language_changed signal for '{selected_code}'")
                self.language_changed.emit(selected_code)
                
                self.update()
                self.repaint()
                
                print(f"Language change completed for '{selected_code}'")
            else:
                print(f"Failed to change language to '{selected_code}'")
                
        except Exception as e:
            logging.error(f"Error in on_language_changed: {e}")
            print(f"Error in language change: {e}")
                    
    def update_text(self):
        """Update the widget's text for the current language"""
        self.language_label.setText(t("Language:"))
        
    def refresh_languages(self):
        """Refresh the language list (call after adding new languages)"""
        current_selection = self.language_combo.currentData()
        self.load_languages()
        
        if current_selection:
            for i in range(self.language_combo.count()):
                if self.language_combo.itemData(i) == current_selection:
                    self.language_combo.setCurrentIndex(i)
                    break

    def showEvent(self, event):
        """Ensure proper sizing when widget is shown"""
        super().showEvent(event)
        if hasattr(self, 'language_combo'):
            self.language_combo.view().setMinimumWidth(250)
            self.language_combo.view().raise_()
            
    def resizeEvent(self, event):
        """Handle resize events to adjust dropdown width"""
        super().resizeEvent(event)
        if hasattr(self, 'language_combo'):
            dropdown_width = max(self.language_combo.width(), 250)
            self.language_combo.view().setMinimumWidth(dropdown_width)
            
    def force_refresh_translations(self):
        """Force refresh translations when they get stuck"""
        try:
            print("Language selector: Force refreshing translations...")
            
            current_lang_name = self.language_combo.currentText()
            print(f"Current selection: {current_lang_name}")
            
            self.language_combo.blockSignals(True)
            
            language_manager.refresh_translations()
            
            self.load_languages()
            
            for i in range(self.language_combo.count()):
                if self.language_combo.itemText(i) == current_lang_name:
                    self.language_combo.setCurrentIndex(i)
                    break
            
            self.language_combo.blockSignals(False)
            
            self.on_language_changed(current_lang_name)
            
            print("✓ Language selector refresh completed")
            
        except Exception as e:
            logging.error(f"Error in force_refresh_translations: {e}")
            print(f"Error in language selector refresh: {e}")
            
            try:
                self.language_combo.blockSignals(False)
            except:
                pass
