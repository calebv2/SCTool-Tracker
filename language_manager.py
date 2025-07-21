# language_manager.py

import json
import os
from typing import Dict, Any, Optional
import logging

_language_manager = None

def get_language_manager():
    """Get or create the global language manager instance"""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager

def t(text: str, context: str = None) -> str:
    """Global translation function - shorthand for translate"""
    return get_language_manager().translate(text, context)

class LanguageManager:
    """Manages translations for the application"""
    
    def __init__(self):
        self.current_language = "en"
        self.translations = {}
        self.language_dir = os.path.join(os.path.dirname(__file__), "languages")
        self.ensure_language_directory()
        self.load_translations()
        
    def ensure_language_directory(self):
        """Create languages directory if it doesn't exist"""
        if not os.path.exists(self.language_dir):
            os.makedirs(self.language_dir)
            
    def load_translations(self):
        """Load all available translation files"""
        if not os.path.exists(self.language_dir):
            return
            
        for filename in os.listdir(self.language_dir):
            if filename.endswith('.json'):
                lang_code = filename[:-5]
                filepath = os.path.join(self.language_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Error loading translation file {filename}: {e}")
                    
    def get_available_languages(self) -> Dict[str, str]:
        """Get list of available languages"""
        languages = {
            "en": "English"
        }
        
        for lang_code in self.translations.keys():
            if lang_code != "en":
                lang_name = self.translations[lang_code].get("language_name", lang_code.upper())
                languages[lang_code] = lang_name
                
        return languages
        
    def set_language(self, language_code: str):
        """Set the current language"""
        old_language = self.current_language
        
        if language_code == "en" or language_code in self.translations:
            self.current_language = language_code
            print(f"Language changed from '{old_language}' to '{language_code}'")
            
            if language_code != "en" and language_code in self.translations:
                translation_count = len(self.translations[language_code])
                print(f"Loaded {translation_count} translations for '{language_code}'")
            
            return True
        else:
            print(f"Failed to set language to '{language_code}' - not available")
            print(f"Available languages: {list(self.translations.keys())}")
            return False
        
    def translate(self, text: str, context: str = None) -> str:
        """Translate text to current language"""
        if not text:
            return text
            
        if self.current_language == "en":
            return text
            
        if self.current_language not in self.translations:
            print(f"Translation warning: Language '{self.current_language}' not loaded")
            return text
            
        translations = self.translations[self.current_language]
        
        if context:
            context_key = f"{context}.{text}"
            if context_key in translations:
                result = translations[context_key]
                return result
                
        if text in translations:
            result = translations[text]
            return result
            
        if text.lower() in translations:
            result = translations[text.lower()]
            return result
            
        for key, value in translations.items():
            if key.lower() == text.lower():
                return value
        
        key_ui_elements = [
            "API Settings", "Button Automation", "Game Overlay", "Support",
            "Killfeed", "Killfeed Settings", "Sound Settings", "Twitch Integration"
        ]
        
        if text in key_ui_elements:
            print(f"Translation missing for key UI element: '{text}' in language '{self.current_language}'")
            print(f"Available keys starting with '{text[:3]}': {[k for k in translations.keys() if k.startswith(text[:3])]}")
            
        return text
        
    def save_current_language_preference(self, config_file: str):
        """Save the current language preference to config file"""
        try:
            config = {}
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['language'] = self.current_language
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            print(f"Error saving language preference: {e}")
            
    def load_language_preference(self, config_file: str):
        """Load language preference from config file"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'language' in config:
                        self.set_language(config['language'])
        except Exception as e:
            print(f"Error loading language preference: {e}")
            
    def debug_translation_state(self):
        """Debug function to print current translation state"""
        print(f"Current language: {self.current_language}")
        print(f"Available languages: {list(self.translations.keys())}")
        if self.current_language in self.translations:
            translations = self.translations[self.current_language]
            print(f"Total translations loaded: {len(translations)}")
            key_ui_elements = ["API Settings", "Button Automation", "Game Overlay", "Support"]
            print("Key UI element translations:")
            for element in key_ui_elements:
                if element in translations:
                    print(f"  '{element}' -> '{translations[element]}'")
                else:
                    print(f"  '{element}' -> MISSING")
        else:
            print(f"No translations loaded for language: {self.current_language}")
    
    def debug_translate(self, text: str) -> str:
        """Debug version of translate that shows what's happening"""
        print(f"DEBUG: Translating '{text}' from language '{self.current_language}'")
        
        if self.current_language == "en":
            print(f"DEBUG: English mode, returning original: '{text}'")
            return text
            
        if self.current_language not in self.translations:
            print(f"DEBUG: Language '{self.current_language}' not in translations!")
            print(f"DEBUG: Available languages: {list(self.translations.keys())}")
            return text
            
        translations = self.translations[self.current_language]
        
        if text in translations:
            result = translations[text]
            print(f"DEBUG: Found translation: '{text}' -> '{result}'")
            return result
        else:
            print(f"DEBUG: Translation missing for: '{text}'")
            print(f"DEBUG: Available keys: {list(translations.keys())[:10]}...")
            return text

    def refresh_translations(self):
        """Refresh translations by reloading all translation files"""
        try:
            print(f"Refreshing translations for current language: {self.current_language}")
            old_translations_count = len(self.translations)
            
            self.translations = {}
            self.load_translations()
            
            new_translations_count = len(self.translations)
            print(f"Translations refreshed: {old_translations_count} -> {new_translations_count} languages loaded")
            
            if self.current_language != "en" and self.current_language not in self.translations:
                print(f"Warning: Current language '{self.current_language}' no longer available, reverting to English")
                self.current_language = "en"
            
        except Exception as e:
            print(f"Error refreshing translations: {e}")
    
    def force_language_change(self, language_code: str, main_app=None):
        """Force a language change with extra validation and refresh"""
        try:
            print(f"Force changing language from '{self.current_language}' to '{language_code}'")
            
            self.clear_translation_cache_and_refresh(main_app)
            
            success = self.set_language(language_code)
            
            if success and language_code == "en" and main_app:
                self.ensure_english_text_storage(main_app)
            
            if success:
                test_translations = ["API Settings", "Button Automation", "Game Overlay"]
                print("Testing translations after language change:")
                for test_text in test_translations:
                    translated = self.translate(test_text)
                    changed = translated != test_text
                    print(f"  '{test_text}' -> '{translated}' (changed: {changed})")
            
            return success
            
        except Exception as e:
            print(f"Error in force_language_change: {e}")
            return False
        
    def clear_translation_cache_and_refresh(self, main_app=None):
        """
        Clear any potential translation caching issues and force a complete refresh
        This method helps fix stuck translations after language switches
        """
        try:
            logging.info("Clearing translation cache and forcing complete refresh")
            
            self.refresh_translations()
            
            logging.info("Translation cache refresh completed (preserved widget English text)")
            return True
            
        except Exception as e:
            logging.error(f"Error clearing translation cache: {e}")
            return False
        
    def ensure_english_text_storage(self, main_app=None):
        """
        Ensure that English text is properly stored when switching back to English
        This helps maintain translation consistency across language switches
        """
        try:
            if self.current_language == "en" and main_app:
                logging.debug("Re-storing English text since we're back to English")
                
                from PyQt5.QtWidgets import QLabel, QPushButton, QCheckBox, QLineEdit, QGroupBox

                needs_init = False
                for widget in main_app.findChildren(QLabel)[:5]:
                    if not widget.property('original_english_text'):
                        needs_init = True
                        break
                
                if needs_init:
                    try:
                        from translation_utils import initialize_widget_english_text
                        initialize_widget_english_text(main_app)
                        logging.debug("English text storage initialized")
                    except ImportError:
                        logging.warning("Could not import initialize_widget_english_text")
                    except Exception as e:
                        logging.error(f"Error refreshing English text storage: {e}")
                else:
                    logging.debug("English text storage already exists, no re-initialization needed")
            
        except Exception as e:
            logging.error(f"Error in ensure_english_text_storage: {e}")

language_manager = get_language_manager()
