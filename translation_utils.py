# translation_utils.py

import logging
from language_manager import language_manager, t
from kill_parser import VERSION


def setup_auto_translation(main_app, language_selector):
    """
    Setup automatic translation when language changes
    """
    try:
        if hasattr(language_selector, 'language_changed'):
            language_selector.language_changed.connect(
                lambda lang_code: immediate_translate_application(main_app)
            )
            logging.debug("Auto-translation setup completed with immediate refresh")
        else:
            logging.warning("Language selector doesn't have language_changed signal")
    except Exception as e:
        logging.error(f"Failed to setup auto-translation: {e}")


def translate_application(main_app):
    """Perform complete translation of the application UI"""
    try:
        if 'enhanced_translate_application' in globals():
            enhanced_translate_application(main_app)
        else:
            logging.debug(f"Starting translation update for language: {language_manager.current_language}")
            
            if hasattr(main_app, 'language_selector') and main_app.language_selector:
                if hasattr(main_app.language_selector, 'update_text'):
                    main_app.language_selector.update_text()
                    logging.debug("Language selector text updated")
            
            if hasattr(main_app, 'update_all_translations'):
                main_app.update_all_translations()
                logging.debug("Main app translations updated")
            
            update_additional_components(main_app)
            
            force_refresh_ui(main_app)
                
            logging.info(f"Application translation update completed for language: {language_manager.current_language}")
        
    except Exception as e:
        logging.error(f"Failed to translate application: {e}")


def immediate_translate_application(main_app):
    """Perform immediate translation of the application UI with forced refresh"""
    try:
        logging.debug(f"Starting immediate translation update for language: {language_manager.current_language}")
        
        if hasattr(main_app, 'language_selector') and main_app.language_selector:
            if hasattr(main_app.language_selector, 'update_text'):
                main_app.language_selector.update_text()
                logging.debug("Language selector text updated")
        
        if hasattr(main_app, 'update_all_translations'):
            main_app.update_all_translations()
            logging.debug("Main app translations updated")
        
        force_immediate_ui_translation(main_app)
        
        missed_count = find_and_translate_missed_elements(main_app)
        if missed_count > 0:
            logging.debug(f"Found and translated {missed_count} additional missed elements")
        
        update_additional_components(main_app)
        
        force_immediate_ui_refresh(main_app)
        
        logging.info(f"Immediate translation update completed for language: {language_manager.current_language}")
        
    except Exception as e:
        logging.error(f"Failed to perform immediate translation: {e}")


def update_additional_components(main_app):
    """Update additional UI components that might not be covered by the main translation method"""
    try:
        if hasattr(main_app, 'game_overlay') and main_app.game_overlay:
            if hasattr(main_app.game_overlay, 'update_translations'):
                main_app.game_overlay.update_translations()
                logging.debug("Game overlay translations updated")
        
        if hasattr(main_app, 'overlay_settings') and main_app.overlay_settings:
            if hasattr(main_app.overlay_settings, 'update_translations'):
                main_app.overlay_settings.update_translations()
                logging.debug("Overlay settings translations updated")
        
        force_update_overlay_instructions()
        
        if hasattr(main_app, 'kill_clip_window') and main_app.kill_clip_window:
            if hasattr(main_app.kill_clip_window, 'update_translations'):
                main_app.kill_clip_window.update_translations()
                logging.debug("Kill clip window translations updated")
        
        if hasattr(main_app, 'button_automation_widget') and main_app.button_automation_widget:
            if hasattr(main_app.button_automation_widget, 'update_translations'):
                main_app.button_automation_widget.update_translations()
                logging.debug("Button automation widget translations updated")
        
        if hasattr(main_app, 'open_dialogs'):
            for dialog in main_app.open_dialogs:
                if hasattr(dialog, 'update_translations'):
                    dialog.update_translations()
                    logging.debug("Dialog translations updated")
        
    except Exception as e:
        logging.error(f"Failed to update additional components: {e}")


def force_update_overlay_instructions():
    """Force update all overlay instruction text across the entire application"""
    try:
        from PyQt5.QtWidgets import QApplication, QLabel
        from language_manager import t
        
        app = QApplication.instance()
        if not app:
            return
            
        instructions_updated = 0
        
        for widget in app.allWidgets():
            try:
                if isinstance(widget, QLabel) and hasattr(widget, 'text'):
                    text = widget.text()
                    
                    if ("Use global hotkey to toggle overlay visibility" in text or
                        ("Use global hotkey" in text and "overlay" in text) or
                        ("hotkey" in text.lower() and "overlay" in text.lower() and "toggle" in text.lower())):
                        
                        widget.setText(f"""
        <b>{t('Instructions:')}</b><br>
        • {t('Left-click and drag to move the overlay')}<br>
        • {t('Ctrl + Mouse wheel to adjust opacity')}<br>
        • {t('Click the mode button (●/◐) on overlay to cycle modes')}<br>
        • {t('Use global hotkey to toggle overlay visibility')}<br>
        • {t('Overlay stays on top of all windows including games')}
        """)
                        instructions_updated += 1
                        logging.debug(f"Updated overlay instructions in widget: {widget.__class__.__name__}")
            except Exception as e:
                pass
        
        if instructions_updated > 0:
            logging.info(f"Force updated {instructions_updated} overlay instruction labels")
        else:
            logging.debug("No overlay instruction labels found to update")
            
    except Exception as e:
        logging.error(f"Error in force_update_overlay_instructions: {e}")


def force_refresh_ui(main_app):
    """Force refresh the UI to ensure all translations are properly applied"""
    try:
        try:
            if hasattr(main_app, 'update') and callable(main_app.update):
                main_app.update()
        except Exception as e:
            logging.debug(f"Could not call main_app.update(): {e}")
        
        try:
            if hasattr(main_app, 'repaint') and callable(main_app.repaint):
                main_app.repaint()
        except Exception as e:
            logging.debug(f"Could not call main_app.repaint(): {e}")
        
        from PyQt5.QtWidgets import QApplication
        if QApplication.instance():
            QApplication.instance().processEvents()
            
        if hasattr(main_app, 'setWindowTitle'):
            main_app.setWindowTitle(t(f"SCTool Killfeed {VERSION}"))
        
        logging.debug("UI refresh completed")
        
    except Exception as e:
        logging.error(f"Failed to force refresh UI: {e}")


def force_immediate_ui_translation(main_app):
    """Force immediate translation of all UI elements with visual refresh"""
    try:
        from PyQt5.QtWidgets import QLabel, QPushButton, QCheckBox, QLineEdit, QGroupBox, QTabWidget, QComboBox
        from PyQt5.QtCore import QTimer
        
        total_updated = 0
        
        if hasattr(main_app, 'nav_buttons') and main_app.nav_buttons:
            nav_texts = [
                "Killfeed", "Killfeed Settings", "API Settings", "Sound Settings",
                "Twitch Integration", "Button Automation", "Game Overlay", "Support"
            ]
            
            for i, button in enumerate(main_app.nav_buttons):
                if i < len(nav_texts):
                    old_text = button.text()
                    new_text = t(nav_texts[i])
                    button.setText(new_text)
                    
                    button.setProperty('original_english_text', nav_texts[i])
                    
                    button.update()
                    button.repaint()
                    total_updated += 1
                    
                    if new_text != old_text:
                        logging.debug(f"Nav button updated: '{old_text}' -> '{new_text}'")
        
        all_labels = main_app.findChildren(QLabel)
        updated_labels = 0
        for label in all_labels:
            current_text = label.text()
            if current_text and len(current_text.strip()) > 0 and not current_text.startswith('<'):
                original_english = get_original_english_text(label, current_text)
                new_text = t(original_english)
                if new_text != current_text:
                    label.setText(new_text)
                    updated_labels += 1
                label.setProperty('original_english_text', original_english)
                label.update()
                label.repaint()
                total_updated += 1
        
        logging.debug(f"✓ Updated {updated_labels} labels (out of {len(all_labels)} found)")
        
        all_buttons = main_app.findChildren(QPushButton)
        updated_buttons = 0
        for button in all_buttons:
            current_text = button.text()
            if current_text and len(current_text.strip()) > 0:
                if hasattr(main_app, 'nav_buttons') and button in main_app.nav_buttons:
                    continue
                
                original_english = get_original_english_text(button, current_text)
                new_text = t(original_english)
                if new_text != current_text:
                    button.setText(new_text)
                    updated_buttons += 1
                button.setProperty('original_english_text', original_english)
                button.update()
                button.repaint()
                total_updated += 1
        
        logging.debug(f"✓ Updated {updated_buttons} buttons (out of {len(all_buttons)} found)")
        
        all_checkboxes = main_app.findChildren(QCheckBox)
        updated_checkboxes = 0
        for checkbox in all_checkboxes:
            current_text = checkbox.text()
            if current_text and len(current_text.strip()) > 0:
                original_english = get_original_english_text(checkbox, current_text)
                new_text = t(original_english)
                if new_text != current_text:
                    checkbox.setText(new_text)
                    updated_checkboxes += 1
                checkbox.setProperty('original_english_text', original_english)
                checkbox.update()
                checkbox.repaint()
                total_updated += 1
        
        logging.debug(f"✓ Updated {updated_checkboxes} checkboxes (out of {len(all_checkboxes)} found)")
        
        all_groupboxes = main_app.findChildren(QGroupBox)
        updated_groupboxes = 0
        for groupbox in all_groupboxes:
            current_title = groupbox.title()
            if current_title and len(current_title.strip()) > 0:
                original_english = get_original_english_text(groupbox, current_title)
                new_title = t(original_english)
                if new_title != current_title:
                    groupbox.setTitle(new_title)
                    updated_groupboxes += 1
                groupbox.setProperty('original_english_text', original_english)
                groupbox.update()
                groupbox.repaint()
                total_updated += 1
        
        logging.debug(f"✓ Updated {updated_groupboxes} group boxes (out of {len(all_groupboxes)} found)")
        
        all_lineedits = main_app.findChildren(QLineEdit)
        updated_placeholders = 0
        for lineedit in all_lineedits:
            current_placeholder = lineedit.placeholderText()
            if current_placeholder and len(current_placeholder.strip()) > 0:
                original_english = get_original_english_text(lineedit, current_placeholder, 'placeholderText')
                new_placeholder = t(original_english)
                if new_placeholder != current_placeholder:
                    lineedit.setPlaceholderText(new_placeholder)
                    updated_placeholders += 1
                lineedit.setProperty('original_english_placeholder', original_english)
                lineedit.update()
                total_updated += 1
        
        logging.debug(f"✓ Updated {updated_placeholders} line edit placeholders (out of {len(all_lineedits)} found)")
        
        all_comboboxes = main_app.findChildren(QComboBox)
        updated_combos = 0
        for combobox in all_comboboxes:
            if hasattr(main_app, 'language_selector') and hasattr(main_app.language_selector, 'language_combo'):
                if combobox == main_app.language_selector.language_combo:
                    continue
            
            for i in range(combobox.count()):
                current_text = combobox.itemText(i)
                if current_text and len(current_text.strip()) > 0:
                    stored_english = combobox.property(f'original_english_item_{i}')
                    if not stored_english:
                        combobox.setProperty(f'original_english_item_{i}', current_text)
                        stored_english = current_text
                    
                    new_text = t(stored_english)
                    if new_text != current_text:
                        combobox.setItemText(i, new_text)
                        updated_combos += 1
            
            combobox.update()
        
        if updated_combos > 0:
            logging.debug(f"✓ Updated {updated_combos} combo box items")
        
        all_tabwidgets = main_app.findChildren(QTabWidget)
        updated_tabs = 0
        for tabwidget in all_tabwidgets:
            for i in range(tabwidget.count()):
                current_text = tabwidget.tabText(i)
                if current_text and len(current_text.strip()) > 0:
                    stored_english = tabwidget.property(f'original_english_tab_{i}')
                    if not stored_english:
                        tabwidget.setProperty(f'original_english_tab_{i}', current_text)
                        stored_english = current_text
                    
                    new_text = t(stored_english)
                    if new_text != current_text:
                        tabwidget.setTabText(i, new_text)
                        updated_tabs += 1
            
            tabwidget.update()
        
        if updated_tabs > 0:
            logging.debug(f"✓ Updated {updated_tabs} tab widget labels")
        
        logging.debug(f"Force updated {total_updated} UI elements with immediate refresh")
        
    except Exception as e:
        logging.error(f"Error in force_immediate_ui_translation: {e}")


def force_immediate_ui_refresh(main_app):
    """Force immediate and complete UI refresh"""
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QTimer, QCoreApplication
        
        if hasattr(main_app, 'setWindowTitle'):
            main_app.setWindowTitle(t(f"SCTool Killfeed {VERSION}"))
        
        main_app.update()
        main_app.repaint()
        
        if QApplication.instance():
            QApplication.instance().processEvents()
            QCoreApplication.processEvents()
        
        for child in main_app.findChildren(object):
            try:
                if hasattr(child, 'update') and callable(getattr(child, 'update', None)):
                    child.update()
                if hasattr(child, 'repaint') and callable(getattr(child, 'repaint', None)):
                    child.repaint()
            except:
                pass
        
        def delayed_refresh_pass1():
            try:
                main_app.update()
                main_app.repaint()
                if QApplication.instance():
                    QApplication.instance().processEvents()
            except:
                pass
        
        def delayed_refresh_pass2():
            try:
                for child in main_app.findChildren(object):
                    try:
                        if hasattr(child, 'update') and callable(getattr(child, 'update', None)):
                            child.update()
                    except:
                        pass
                if QApplication.instance():
                    QApplication.instance().processEvents()
                logging.debug("Multi-pass UI refresh completed")
            except:
                pass
        
        QTimer.singleShot(50, delayed_refresh_pass1)
        QTimer.singleShot(150, delayed_refresh_pass2)
        
        logging.debug("Immediate UI refresh completed with scheduled follow-ups")
        
    except Exception as e:
        logging.error(f"Error in force_immediate_ui_refresh: {e}")


def translate_widget_text(widget, text_key):
    """Helper function to translate a specific widget's text"""
    try:
        if hasattr(widget, 'setText'):
            widget.setText(t(text_key))
        elif hasattr(widget, 'setTitle'):
            widget.setTitle(t(text_key))
        elif hasattr(widget, 'setWindowTitle'):
            widget.setWindowTitle(t(text_key))
    except Exception as e:
        logging.debug(f"Failed to translate widget text for key '{text_key}': {e}")


def translate_widget_collection(widgets_dict):
    """Helper function to translate a collection of widgets"""
    try:
        for widget, text_key in widgets_dict.items():
            translate_widget_text(widget, text_key)
    except Exception as e:
        logging.error(f"Failed to translate widget collection: {e}")


def debug_translation_state(main_app):
    """Debug function to print current translation state and identify issues"""
    try:
        print("=== TRANSLATION DEBUG STATE ===")
        print(f"Current language: {language_manager.current_language}")
        print(f"Available languages: {list(language_manager.translations.keys())}")
        
        test_elements = ["API Settings", "Button Automation", "Game Overlay", "Support"]
        print("\n=== Testing Key UI Elements ===")
        for element in test_elements:
            translated = t(element)
            print(f"'{element}' -> '{translated}' (changed: {translated != element})")
        
        print(f"\n=== Main App Translation Methods ===")
        print(f"Has update_all_translations: {hasattr(main_app, 'update_all_translations')}")
        print(f"Has language_selector: {hasattr(main_app, 'language_selector')}")
        
        if hasattr(main_app, 'language_selector') and main_app.language_selector:
            print(f"Language selector has update_text: {hasattr(main_app.language_selector, 'update_text')}")
        
        components = ['game_overlay', 'overlay_settings', 'kill_clip_window', 'button_automation_widget']
        print(f"\n=== Additional Components ===")
        for comp in components:
            has_comp = hasattr(main_app, comp) and getattr(main_app, comp, None) is not None
            has_update = False
            if has_comp:
                comp_obj = getattr(main_app, comp)
                has_update = hasattr(comp_obj, 'update_translations')
            print(f"{comp}: exists={has_comp}, has_update_translations={has_update}")
        
    except Exception as e:
        print(f"Error in debug_translation_state: {e}")


def fix_stuck_translations(main_app):
    """Fix translations that might be stuck or not updating properly"""
    try:
        logging.info("Attempting to fix stuck translations...")
        
        language_manager.load_translations()
        
        if hasattr(main_app, 'repaint'):
            main_app.repaint()
        
        translate_application(main_app)
        
        from PyQt5.QtCore import QTimer
        def delayed_refresh():
            try:
                if hasattr(main_app, 'update'):
                    main_app.update()
                if hasattr(main_app, 'repaint'):
                    main_app.repaint()
                logging.info("Delayed refresh completed")
            except Exception as e:
                logging.error(f"Error in delayed refresh: {e}")
        
        QTimer.singleShot(100, delayed_refresh)
        
        logging.info("Fix stuck translations completed")
        
    except Exception as e:
        logging.error(f"Failed to fix stuck translations: {e}")


def validate_translations():
    """Validate that all required translations are available"""
    try:
        missing_translations = {}
        
        key_elements = [
            "API Settings", "Button Automation", "Game Overlay", "Support",
            "Killfeed", "Killfeed Settings", "Sound Settings", "Twitch Integration",
            "START MONITORING", "STOP MONITORING", "FIND MISSED KILLS",
            "CHECK FOR UPDATES", "EXPORT LOGS", "OPEN DATA FOLDER"
        ]
        
        for lang_code, translations in language_manager.translations.items():
            missing_for_lang = []
            for element in key_elements:
                if element not in translations:
                    missing_for_lang.append(element)
            
            if missing_for_lang:
                missing_translations[lang_code] = missing_for_lang
        
        if missing_translations:
            logging.warning("Missing translations found:")
            for lang, missing in missing_translations.items():
                logging.warning(f"  {lang}: {missing}")
                print(f"Missing translations for {lang}: {missing}")
        else:
            logging.info("All key translations are available")
            print("All key translations are available")
        
        return missing_translations
        
    except Exception as e:
        logging.error(f"Error validating translations: {e}")
        return {}

def create_translation_fix():
    """Create a fix for translation issues"""

    def enhanced_translate_application(main_app):
        """Enhanced version of translate_application with better UI refresh"""
        try:
            print(f"=== TRANSLATION UPDATE START ===")
            print(f"Target language: {language_manager.current_language}")
            
            if hasattr(main_app, 'language_selector') and main_app.language_selector:
                if hasattr(main_app.language_selector, 'update_text'):
                    main_app.language_selector.update_text()
                    print("✓ Language selector updated")
            
            if hasattr(main_app, 'update_all_translations'):
                print("Calling main app update_all_translations...")
                main_app.update_all_translations()
                print("✓ Main translations updated")
            
            update_ui_sections_with_force_refresh(main_app)
            
            update_additional_components(main_app)
            
            force_complete_ui_refresh(main_app)
            
            print(f"=== TRANSLATION UPDATE COMPLETE ===")
            
        except Exception as e:
            logging.error(f"Error in enhanced_translate_application: {e}")
            print(f"Error in translation update: {e}")

    def update_ui_sections_with_force_refresh(main_app):
        """Update UI sections with forced refresh"""
        try:
            print("Updating UI sections with force refresh...")
            
            from PyQt5.QtWidgets import QLabel, QPushButton, QCheckBox, QLineEdit, QGroupBox
            
            if hasattr(main_app, 'nav_buttons') and main_app.nav_buttons:
                nav_texts = [
                    "Killfeed",
                    "Killfeed Settings", 
                    "API Settings",
                    "Sound Settings",
                    "Twitch Integration",
                    "Button Automation",
                    "Game Overlay",
                    "Support"
                ]
                
                for i, button in enumerate(main_app.nav_buttons):
                    if i < len(nav_texts):
                        old_text = button.text()
                        new_text = t(nav_texts[i])
                        button.setText(new_text)
                        
                        try:
                            if hasattr(button, 'update') and callable(button.update):
                                button.update()
                            if hasattr(button, 'repaint') and callable(button.repaint):
                                button.repaint()
                        except:
                            pass
                        
                        print(f"  Nav button {i}: '{old_text}' -> '{new_text}'")
            
            labels_updated = 0
            labels_found = 0
            for label in main_app.findChildren(QLabel):
                labels_found += 1
                old_text = label.text()
                if old_text and len(old_text.strip()) > 0 and not old_text.startswith('<'):
                    new_text = t(old_text)
                    label.setText(new_text)
                    
                    try:
                        if hasattr(label, 'update') and callable(label.update):
                            label.update()
                        if hasattr(label, 'repaint') and callable(label.repaint):
                            label.repaint()
                    except:
                        pass
                    
                    labels_updated += 1
                    
                    if new_text != old_text:
                        print(f"    Label updated: '{old_text}' -> '{new_text}'")
            
            print(f"✓ Updated {labels_updated} labels (out of {labels_found} found)")
            
            buttons_updated = 0
            buttons_found = 0
            for button in main_app.findChildren(QPushButton):
                buttons_found += 1
                old_text = button.text()
                if old_text and len(old_text.strip()) > 0:
                    new_text = t(old_text)
                    button.setText(new_text)
                    
                    try:
                        if hasattr(button, 'update') and callable(button.update):
                            button.update()
                        if hasattr(button, 'repaint') and callable(button.repaint):
                            button.repaint()
                    except:
                        pass
                    
                    buttons_updated += 1
                    
                    if new_text != old_text:
                        print(f"    Button updated: '{old_text}' -> '{new_text}'")
            
            print(f"✓ Updated {buttons_updated} buttons (out of {buttons_found} found)")
            
            checkboxes_updated = 0
            checkboxes_found = 0
            for checkbox in main_app.findChildren(QCheckBox):
                checkboxes_found += 1
                old_text = checkbox.text()
                if old_text and len(old_text.strip()) > 0:
                    new_text = t(old_text)
                    checkbox.setText(new_text)
                    
                    try:
                        if hasattr(checkbox, 'update') and callable(checkbox.update):
                            checkbox.update()
                        if hasattr(checkbox, 'repaint') and callable(checkbox.repaint):
                            checkbox.repaint()
                    except:
                        pass
                    
                    checkboxes_updated += 1
                    
                    if new_text != old_text:
                        print(f"    Checkbox updated: '{old_text}' -> '{new_text}'")
            
            print(f"✓ Updated {checkboxes_updated} checkboxes (out of {checkboxes_found} found)")
            
            groupboxes_updated = 0
            groupboxes_found = 0
            for groupbox in main_app.findChildren(QGroupBox):
                groupboxes_found += 1
                old_text = groupbox.title()
                if old_text and len(old_text.strip()) > 0:
                    new_text = t(old_text)
                    groupbox.setTitle(new_text)
                    
                    try:
                        if hasattr(groupbox, 'update') and callable(groupbox.update):
                            groupbox.update()
                        if hasattr(groupbox, 'repaint') and callable(groupbox.repaint):
                            groupbox.repaint()
                    except:
                        pass
                    
                    groupboxes_updated += 1
                    
                    if new_text != old_text:
                        print(f"    GroupBox updated: '{old_text}' -> '{new_text}'")
            
            print(f"✓ Updated {groupboxes_updated} group boxes (out of {groupboxes_found} found)")
            
            lineedits_updated = 0
            lineedits_found = 0
            for lineedit in main_app.findChildren(QLineEdit):
                lineedits_found += 1
                old_placeholder = lineedit.placeholderText()
                if old_placeholder and len(old_placeholder.strip()) > 0:
                    new_placeholder = t(old_placeholder)
                    lineedit.setPlaceholderText(new_placeholder)
                    lineedits_updated += 1
                    
                    if new_placeholder != old_placeholder:
                        print(f"    LineEdit placeholder updated: '{old_placeholder}' -> '{new_placeholder}'")
            
            print(f"✓ Updated {lineedits_updated} line edit placeholders (out of {lineedits_found} found)")
            checkboxes_updated = 0
            for checkbox in main_app.findChildren(QCheckBox):
                old_text = checkbox.text()
                if old_text and len(old_text.strip()) > 0:
                    new_text = t(old_text)
                    if new_text != old_text:
                        checkbox.setText(new_text)
                        checkbox.update()
                        checkbox.repaint()
                        checkboxes_updated += 1
            
            print(f"✓ Updated {checkboxes_updated} checkboxes")
            
        except Exception as e:
            logging.error(f"Error updating UI sections: {e}")
            print(f"Error updating UI sections: {e}")
    
    def force_complete_ui_refresh(main_app):
        """Force a complete UI refresh"""
        try:
            print("Forcing complete UI refresh...")
            
            if hasattr(main_app, 'setWindowTitle'):
                main_app.setWindowTitle(t(f"SCTool Killfeed {VERSION}"))
            
            try:
                if hasattr(main_app, 'update') and callable(main_app.update):
                    main_app.update()
            except Exception as e:
                logging.debug(f"Could not call main_app.update(): {e}")
                
            try:
                if hasattr(main_app, 'repaint') and callable(main_app.repaint):
                    main_app.repaint()
            except Exception as e:
                logging.debug(f"Could not call main_app.repaint(): {e}")
        
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QCoreApplication
            
            if QApplication.instance():
                QApplication.instance().processEvents()
                QCoreApplication.processEvents()
            
            children_updated = 0
            for child in main_app.findChildren(object):
                try:
                    if hasattr(child, 'update') and callable(getattr(child, 'update', None)):
                        child.update()
                        children_updated += 1
                except Exception:
                    pass
                    
                try:
                    if hasattr(child, 'repaint') and callable(getattr(child, 'repaint', None)):
                        child.repaint()
                except Exception:
                    pass
            
            print(f"✓ Complete UI refresh done (updated {children_updated} children)")
            
        except Exception as e:
            logging.error(f"Error in force_complete_ui_refresh: {e}")
            print(f"Error in complete UI refresh: {e}")
    
    return enhanced_translate_application

enhanced_translate_application = create_translation_fix()

def manual_translation_fix(main_app):
    """Manual translation fix that can be called when translations get stuck"""
    try:
        print("=== MANUAL TRANSLATION FIX ===")
        current_lang = language_manager.current_language
        print(f"Current language: {current_lang}")
        
        print("Step 1: Refreshing language manager...")
        language_manager.refresh_translations()
        
        print(f"Step 2: Re-setting language to {current_lang}...")
        language_manager.force_language_change(current_lang)
        
        print("Step 3: Applying enhanced translation update...")
        enhanced_translate_application(main_app)
        
        print("Step 4: Scheduling delayed refresh...")
        from PyQt5.QtCore import QTimer
        
        def delayed_fix():
            try:
                print("Executing delayed translation fix...")
                enhanced_translate_application(main_app)
                print("✓ Manual translation fix completed!")
            except Exception as e:
                print(f"Error in delayed fix: {e}")
        
        QTimer.singleShot(500, delayed_fix)
        
        return True
        
    except Exception as e:
        print(f"Error in manual_translation_fix: {e}")
        logging.error(f"Error in manual_translation_fix: {e}")
        return False

def get_original_english_text(widget, current_text, property_name='text'):
    """Get the original English text for a widget, either from stored property or by reverse lookup"""
    try:
        if property_name == 'placeholderText':
            stored_english = widget.property('original_english_placeholder')
        else:
            stored_english = widget.property('original_english_text')
        
        if stored_english:
            return stored_english
        
        original_english = reverse_translate_to_english(current_text)
        if original_english and original_english != current_text:
            if property_name == 'placeholderText':
                widget.setProperty('original_english_placeholder', original_english)
            else:
                widget.setProperty('original_english_text', original_english)
            return original_english
        
        if property_name == 'placeholderText':
            widget.setProperty('original_english_placeholder', current_text)
        else:
            widget.setProperty('original_english_text', current_text)
        return current_text
        
    except Exception as e:
        logging.debug(f"Error getting original English text: {e}")
        return current_text


def reverse_translate_to_english(translated_text):
    """Attempt to find the original English text by searching through translation files"""
    try:
        if language_manager.current_language == "en":
            return translated_text
        
        for lang_code, translations in language_manager.translations.items():
            for english_key, translation in translations.items():
                if translation == translated_text:
                    logging.debug(f"Found reverse translation: '{translated_text}' -> '{english_key}' (from {lang_code})")
                    return english_key
        
        nav_translation_map = {
            "Kill-Feed": "Killfeed",
            "Kill-Feed Einstellungen": "Killfeed Settings", 
            "API-Einstellungen": "API Settings",
            "Sound-Einstellungen": "Sound Settings",
            "Twitch-Integration": "Twitch Integration",
            "Button-Automatisierung": "Button Automation",
            "Spiel-Overlay": "Game Overlay",
            
            "Paramètres API": "API Settings",
            "Automatisation des Boutons": "Button Automation",
            "Superposition de Jeu": "Game Overlay",
            
            "API设置": "API Settings",
            "按钮自动化": "Button Automation", 
            "游戏覆盖层": "Game Overlay",
            
            "API設定": "API Settings",
            "ボタン自動化": "Button Automation",
            "ゲームオーバーレイ": "Game Overlay"
        }
        
        if translated_text in nav_translation_map:
            logging.debug(f"Found navigation mapping: '{translated_text}' -> '{nav_translation_map[translated_text]}'")
            return nav_translation_map[translated_text]
        
        logging.debug(f"No reverse translation found for: '{translated_text}'")
        return None
        
    except Exception as e:
        logging.debug(f"Error in reverse translation lookup: {e}")
        return None

def debug_translation_switching_issue(main_app):
    """
    Debug function to help diagnose translation switching issues
    This function prints detailed information about the current state
    """
    try:
        from PyQt5.QtWidgets import QLabel
        
        print("=== TRANSLATION SWITCHING DEBUG ===")
        print(f"Current language: {language_manager.current_language}")
        print(f"Available languages: {list(language_manager.translations.keys())}")
        
        test_strings = ["API Settings", "Button Automation", "Game Overlay", "Support"]
        print("\n=== Translation Tests ===")
        for test_string in test_strings:
            translated = t(test_string)
            print(f"t('{test_string}') = '{translated}' (changed: {translated != test_string})")
        
        if hasattr(main_app, 'nav_buttons') and main_app.nav_buttons:
            print(f"\n=== Navigation Buttons ===")
            nav_texts = [
                "Killfeed", "Killfeed Settings", "API Settings", "Sound Settings",
                "Twitch Integration", "Button Automation", "Game Overlay", "Support"
            ]
            
            for i, button in enumerate(main_app.nav_buttons[:len(nav_texts)]):
                current_text = button.text()
                stored_english = button.property('original_english_text')
                expected_english = nav_texts[i]
                expected_translated = t(expected_english)
                
                print(f"Button {i}:")
                print(f"  Current text: '{current_text}'")
                print(f"  Stored English: '{stored_english}'")
                print(f"  Expected English: '{expected_english}'")
                print(f"  Expected translated: '{expected_translated}'")
                print(f"  Matches expected: {current_text == expected_translated}")
        
        labels = main_app.findChildren(QLabel)[:5]
        print(f"\n=== Sample Labels ===")
        for i, label in enumerate(labels):
            current_text = label.text()
            stored_english = label.property('original_english_text')
            if stored_english:
                expected_translated = t(stored_english)
                print(f"Label {i}:")
                print(f"  Current text: '{current_text}'")
                print(f"  Stored English: '{stored_english}'")
                print(f"  Expected translated: '{expected_translated}'")
                print(f"  Matches expected: {current_text == expected_translated}")
        
        print("=== END DEBUG ===")
        
    except Exception as e:
        print(f"Error in debug_translation_switching_issue: {e}")


if __name__ == "__main__":
    print("Translation Utils - Debug Mode")
    print("Available functions:")
    print("- debug_translation_switching_issue(main_app)")
    print("- immediate_translate_application(main_app)")

def find_and_translate_missed_elements(main_app):
    """Find and translate any UI elements that might have been missed by the main translation function"""
    try:
        from PyQt5.QtWidgets import (QLabel, QPushButton, QCheckBox, QLineEdit, QGroupBox, 
                                   QTabWidget, QComboBox, QToolTip, QStatusBar, QMenuBar, 
                                   QMenu, QAction, QToolBar, QToolButton, QRadioButton)
        
        missed_elements = []
        
        widget_types = [
            (QLabel, 'text', 'setText'),
            (QPushButton, 'text', 'setText'), 
            (QCheckBox, 'text', 'setText'),
            (QRadioButton, 'text', 'setText'),
            (QGroupBox, 'title', 'setTitle'),
            (QToolButton, 'text', 'setText')
        ]
        
        for widget_type, get_method, set_method in widget_types:
            widgets = main_app.findChildren(widget_type)
            for widget in widgets:
                try:
                    if get_method == 'text':
                        current_text = widget.text()
                    elif get_method == 'title':
                        current_text = widget.title()
                    else:
                        continue
                    
                    if not current_text or len(current_text.strip()) == 0:
                        continue
                    
                    if current_text.startswith('<') or len(current_text) < 2:
                        continue
                    
                    original_english = get_original_english_text(widget, current_text)
                    translated_text = t(original_english)
                    
                    if translated_text != current_text:
                        if set_method == 'setText':
                            widget.setText(translated_text)
                        elif set_method == 'setTitle':
                            widget.setTitle(translated_text)
                        
                        missed_elements.append({
                            'type': widget_type.__name__,
                            'original': current_text,
                            'translated': translated_text
                        })
                        
                        widget.update()
                        
                except Exception as e:
                    logging.debug(f"Error translating {widget_type.__name__}: {e}")
        
        try:
            for action in main_app.findChildren(QAction):
                current_text = action.text()
                if current_text and len(current_text.strip()) > 0 and not current_text.startswith('<'):
                    original_english = action.property('original_english_text')
                    if not original_english:
                        original_english = current_text
                        action.setProperty('original_english_text', original_english)
                    
                    translated_text = t(original_english)
                    if translated_text != current_text:
                        action.setText(translated_text)
                        missed_elements.append({
                            'type': 'QAction',
                            'original': current_text,
                            'translated': translated_text
                        })
        except Exception as e:
            logging.debug(f"Error translating actions: {e}")
        
        try:
            status_bars = main_app.findChildren(QStatusBar)
            for status_bar in status_bars:
                current_message = status_bar.currentMessage()
                if current_message and len(current_message.strip()) > 0:
                    original_english = status_bar.property('original_english_message')
                    if not original_english:
                        original_english = current_message
                        status_bar.setProperty('original_english_message', original_english)
                    
                    translated_message = t(original_english)
                    if translated_message != current_message:
                        status_bar.showMessage(translated_message)
                        missed_elements.append({
                            'type': 'QStatusBar',
                            'original': current_message,
                            'translated': translated_message
                        })
        except Exception as e:
            logging.debug(f"Error translating status bar: {e}")
        
        if missed_elements:
            logging.info(f"Found and translated {len(missed_elements)} previously missed elements:")
            for element in missed_elements[:5]:
                logging.debug(f"  {element['type']}: '{element['original']}' -> '{element['translated']}'")
        
        return len(missed_elements)
        
    except Exception as e:
        logging.error(f"Error in find_and_translate_missed_elements: {e}")
        return 0

def debug_untranslated_elements(main_app):
    """
    Debug function to identify UI elements that are not being translated
    This helps find the remaining elements that need translation
    """
    try:
        from PyQt5.QtWidgets import QLabel, QPushButton, QCheckBox, QLineEdit, QGroupBox
        
        print("=== SEARCHING FOR UNTRANSLATED ELEMENTS ===")
        print(f"Current language: {language_manager.current_language}")
        
        untranslated_elements = []
        
        labels = main_app.findChildren(QLabel)
        for i, label in enumerate(labels):
            current_text = label.text()
            if current_text and len(current_text.strip()) > 0 and not current_text.startswith('<'):
                stored_english = label.property('original_english_text')
                
                if stored_english and language_manager.current_language != "en":
                    expected_translation = t(stored_english)
                    if current_text == stored_english and expected_translation != stored_english:
                        untranslated_elements.append({
                            'type': 'QLabel',
                            'index': i,
                            'current_text': current_text,
                            'stored_english': stored_english,
                            'expected_translation': expected_translation
                        })
                elif not stored_english:
                    untranslated_elements.append({
                        'type': 'QLabel',
                        'index': i,
                        'current_text': current_text,
                        'stored_english': None,
                        'expected_translation': 'No stored English'
                    })
        
        buttons = main_app.findChildren(QPushButton)
        for i, button in enumerate(buttons):
            current_text = button.text()
            if current_text and len(current_text.strip()) > 0:
                stored_english = button.property('original_english_text')
                
                if stored_english and language_manager.current_language != "en":
                    expected_translation = t(stored_english)
                    if current_text == stored_english and expected_translation != stored_english:
                        untranslated_elements.append({
                            'type': 'QPushButton',
                            'index': i,
                            'current_text': current_text,
                            'stored_english': stored_english,
                            'expected_translation': expected_translation
                        })
                elif not stored_english:
                    untranslated_elements.append({
                        'type': 'QPushButton',
                        'index': i,
                        'current_text': current_text,
                        'stored_english': None,
                        'expected_translation': 'No stored English'
                    })
        
        lineedits = main_app.findChildren(QLineEdit)
        for i, lineedit in enumerate(lineedits):
            current_placeholder = lineedit.placeholderText()
            if current_placeholder and len(current_placeholder.strip()) > 0:
                stored_english = lineedit.property('original_english_placeholder')
                
                if stored_english and language_manager.current_language != "en":
                    expected_translation = t(stored_english)
                    if current_placeholder == stored_english and expected_translation != stored_english:
                        untranslated_elements.append({
                            'type': 'QLineEdit (placeholder)',
                            'index': i,
                            'current_text': current_placeholder,
                            'stored_english': stored_english,
                            'expected_translation': expected_translation
                        })
                elif not stored_english:
                    untranslated_elements.append({
                        'type': 'QLineEdit (placeholder)',
                        'index': i,
                        'current_text': current_placeholder,
                        'stored_english': None,
                        'expected_translation': 'No stored English'
                    })
        
        if untranslated_elements:
            print(f"\n=== FOUND {len(untranslated_elements)} UNTRANSLATED ELEMENTS ===")
            for i, element in enumerate(untranslated_elements[:10]):
                print(f"{i+1}. {element['type']} #{element['index']}:")
                print(f"   Current: '{element['current_text']}'")
                print(f"   Stored English: {element['stored_english']}")
                print(f"   Expected: '{element['expected_translation']}'")
                print()
            
            if len(untranslated_elements) > 10:
                print(f"... and {len(untranslated_elements) - 10} more")
        else:
            print("✓ All elements appear to be properly translated")
        
        print("=== END UNTRANSLATED ELEMENTS DEBUG ===")
        return untranslated_elements
        
    except Exception as e:
        print(f"Error in debug_untranslated_elements: {e}")
        return []
