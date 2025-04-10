import sys
import os
import shutil
import json
import subprocess
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QMessageBox, 
                            QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                            QStyledItemDelegate, QAbstractItemView, QInputDialog,
                            QFrame, QComboBox, QDialog, QScrollArea, QTabWidget,
                            QTextEdit)
from PyQt6.QtCore import Qt, QSize, QRegularExpression
from PyQt6.QtGui import QFont, QIcon, QSyntaxHighlighter, QTextCharFormat, QColor, QPixmap, QImage
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import io

# --- PFP Caching Setup --- 
CACHE_DIR = Path.home() / ".cache" / "RepoSaveManager"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_PFP_SIZE = 32 # Size for PFPs in pixels

# --- Helper Function for PFP Fetching/Caching --- 
def fetch_steam_profile_picture(player_id):
    """Fetch and cache Steam profile picture, return QPixmap."""
    cached_image_path = CACHE_DIR / f"{player_id}.png"
    
    if cached_image_path.exists():
        try:
            pixmap = QPixmap()
            if pixmap.load(str(cached_image_path)):
                 return pixmap.scaled(DEFAULT_PFP_SIZE, DEFAULT_PFP_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        except Exception as e:
            print(f"Error loading cached PFP for {player_id}: {e}")
            # Fall through to fetch again if cache loading fails

    try:
        # Fetch XML profile data
        xml_url = f"https://steamcommunity.com/profiles/{player_id}/?xml=1"
        response = requests.get(xml_url, timeout=5) # Add timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        tree = ET.fromstring(response.content)
        avatar_icon_tag = tree.find('avatarIcon')
        
        if avatar_icon_tag is not None and avatar_icon_tag.text:
            img_url = avatar_icon_tag.text
            img_response = requests.get(img_url, timeout=10) # Timeout for image download
            img_response.raise_for_status()
            
            # Load image data into QPixmap
            image = QImage()
            image.loadFromData(img_response.content)
            pixmap = QPixmap.fromImage(image)
            
            # Save to cache
            pixmap.save(str(cached_image_path), "PNG")
            print(f"Fetched and cached PFP for {player_id}")
            return pixmap.scaled(DEFAULT_PFP_SIZE, DEFAULT_PFP_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            print(f"Could not find avatarIcon for {player_id} in XML.")
            
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching PFP for {player_id}: {e}")
    except ET.ParseError as e:
        print(f"XML parse error for {player_id}: {e}")
    except Exception as e:
        print(f"Unexpected error fetching PFP for {player_id}: {e}")

    # Fallback to a default/placeholder if anything fails
    # Consider creating a default placeholder image if needed
    # For now, return an empty pixmap or a simple colored one
    fallback_pixmap = QPixmap(DEFAULT_PFP_SIZE, DEFAULT_PFP_SIZE)
    fallback_pixmap.fill(Qt.GlobalColor.gray)
    return fallback_pixmap

class DescriptionDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setStyleSheet("""
            QLineEdit {
                background-color: #2c2c2e;
                color: #ffffff;
                border: 1px solid #3a3a3c;
                border-radius: 6px;
                padding: 6px;
                selection-background-color: #007AFF;
            }
            QLineEdit:focus {
                border: 1px solid #007AFF;
            }
        """)
        return editor

class JsonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.highlighting_rules = []

        # Keywords
        keywords = ["true", "false", "null"]
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#007AFF"))
        for word in keywords:
            pattern = r'\b' + word + r'\b'
            rule = (pattern, keyword_format)
            self.highlighting_rules.append(rule)

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#FF9500"))
        rule = (r'\b[+-]?\d+(\.\d+)?([eE][+-]?\d+)?\b', number_format)
        self.highlighting_rules.append(rule)

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#34C759"))
        rule = (r'"[^"\\]*(\\.[^"\\]*)*"', string_format)
        self.highlighting_rules.append(rule)

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

class SaveEditor(QDialog):
    def __init__(self, save_file_path, parent=None):
        super().__init__(parent)
        self.save_file_path = save_file_path
        self.json_data = None
        self.key = "Why would you want to cheat?... :o It's no fun. :') :'D" # Store key
        
        # Dictionaries to store player-specific widgets
        self.player_widgets = {} # {player_id: {'health': QLineEdit, 'upgrades': {name: QLineEdit}}}

        self.setWindowTitle(f"Editing: {os.path.basename(save_file_path)}")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(parent.styleSheet() if parent else "") # Inherit style
        self.setModal(True) # Ensure it's modal
        
        self.create_widgets()
        self.load_save()

    def create_widgets(self):
        layout = QVBoxLayout(self)
        self.tabview = QTabWidget()
        layout.addWidget(self.tabview)

        # Add tabs
        self.tabview.addTab(self.create_world_tab(), "World")
        self.tabview.addTab(self.create_player_tab(), "Player")
        self.tabview.addTab(self.create_advanced_tab(), "Advanced")

        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Save Changes")
        self.save_btn.setObjectName("primary")
        self.save_btn.clicked.connect(self.save_changes)
        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.clicked.connect(self.reject) # Use reject for cancel
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

    def create_world_tab(self):
        # ... (Keep existing world tab creation logic using create_entry) ...
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.level_entry = self.create_entry("Level:", layout)
        self.currency_entry = self.create_entry("Currency:", layout)
        self.lives_entry = self.create_entry("Lives:", layout)
        self.charging_entry = self.create_entry("Charging Station Charge:", layout)
        self.haul_entry = self.create_entry("Total Haul:", layout)
        self.teamname_entry = self.create_entry("Team Name:", layout)
        layout.addStretch() # Add stretch to push content up
        return widget
        
    def create_player_tab(self):
        # ... (Keep existing player tab creation logic with scroll area) ...
        widget = QWidget()
        layout = QVBoxLayout(widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.player_layout = QVBoxLayout(scroll_content) # This layout will hold player sections
        self.player_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Align sections to top
        scroll_content.setLayout(self.player_layout)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        return widget
        
    def create_advanced_tab(self):
        # ... (Keep existing advanced tab creation logic with JsonHighlighter) ...
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.json_text = QTextEdit()
        self.json_text.setFont(QFont("Courier", 10))
        self.highlighter = JsonHighlighter(self.json_text.document())
        layout.addWidget(self.json_text)
        return widget

    def create_entry(self, label_text, parent_layout):
        # ... (Keep existing entry creation logic) ...
        frame = QFrame()
        frame_layout = QHBoxLayout(frame)
        label_widget = QLabel(label_text)
        entry = QLineEdit()
        frame_layout.addWidget(label_widget)
        frame_layout.addWidget(entry)
        parent_layout.addWidget(frame)
        return entry

    def load_save(self):
        try:
            # Read raw encrypted bytes
            with open(self.save_file_path, 'rb') as f:
                encrypted_content = f.read()
            print(f"[DEBUG] Read {len(encrypted_content)} bytes from {self.save_file_path}") # DEBUG
            
            # Decrypt raw bytes using the PASSWORD
            from lib.decrypt import decrypt_es3
            print(f"[DEBUG] Calling decrypt_es3 with password: {self.key[:10]}...") # DEBUG
            decrypted_data = decrypt_es3(encrypted_content, self.key) # Pass the full password string
            self.json_data = json.loads(decrypted_data)
            
            # --- Populate World Tab --- 
            run_stats = self.json_data.get('dictionaryOfDictionaries', {}).get('value', {}).get('runStats', {})
            self.level_entry.setText(str(run_stats.get('level', 0)))
            self.currency_entry.setText(str(run_stats.get('currency', 0)))
            self.lives_entry.setText(str(run_stats.get('lives', 0)))
            self.charging_entry.setText(str(run_stats.get('chargingStationCharge', 0)))
            self.haul_entry.setText(str(run_stats.get('totalHaul', 0)))
            self.teamname_entry.setText(self.json_data.get('teamName', {}).get('value', ''))
            
            # --- Populate Player Tab --- 
            # Clear previous player widgets first
            while self.player_layout.count():
                 item = self.player_layout.takeAt(0)
                 widget = item.widget()
                 if widget: widget.deleteLater()
            self.player_widgets.clear()
            
            # Get player data safely
            dict_of_dicts = self.json_data.get('dictionaryOfDictionaries', {}).get('value', {})
            player_names = self.json_data.get("playerNames", {}).get("value", {})
            player_health = dict_of_dicts.get('playerHealth', {})
            
            for player_id, player_name in player_names.items():
                player_widget_refs = self.create_player_section(player_id, player_name)
                
                # Populate health
                health = player_health.get(str(player_id), 0) # Ensure player_id is string for JSON keys
                player_widget_refs['health'].setText(str(health))
                
                # Populate upgrades
                for upgrade_name, entry_widget in player_widget_refs['upgrades'].items():
                    upgrade_key = f'playerUpgrade{upgrade_name}'
                    upgrade_value = dict_of_dicts.get(upgrade_key, {}).get(str(player_id), 0) # Ensure player_id is string
                    entry_widget.setText(str(upgrade_value))
                    
            # --- Populate Advanced Tab --- 
            self.json_text.setText(json.dumps(self.json_data, indent=4))
            
        except ImportError:
             QMessageBox.critical(self, "Error", "Failed to load crypto library. Is pycryptodome installed?")
             self.reject()
        except FileNotFoundError:
             QMessageBox.critical(self, "Error", f"Save file not found: {self.save_file_path}")
             self.reject()
        except Exception as e:
            print(f"Error details: {type(e).__name__}: {e}") # Print detailed error
            # Check for padding specifically
            if "padding" in str(e).lower():
                 QMessageBox.critical(self, "Error", f"Failed to load save: Incorrect padding. This might be due to a wrong key or corrupted file.\nDetails: {e}")
            else:
                 QMessageBox.critical(self, "Error", f"Failed to load save: {e}")
            self.reject()

    def create_player_section(self, player_id, player_name):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)
        
        # --- Player Header (PFP + Name) --- 
        header_layout = QHBoxLayout()
        pfp_label = QLabel()
        pfp_pixmap = fetch_steam_profile_picture(player_id)
        pfp_label.setPixmap(pfp_pixmap)
        pfp_label.setFixedSize(DEFAULT_PFP_SIZE, DEFAULT_PFP_SIZE)
        
        name_label = QLabel(f"<b>{player_name}</b>") # Removed ID from here
        name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        header_layout.addWidget(pfp_label)
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Health
        health_frame = QFrame()
        health_layout = QHBoxLayout(health_frame)
        health_label = QLabel("Health:")
        health_entry = QLineEdit()
        health_layout.addWidget(health_label)
        health_layout.addWidget(health_entry)
        layout.addWidget(health_frame)
        
        # Upgrades section
        upgrades_group = QFrame()
        upgrades_layout = QVBoxLayout(upgrades_group)
        upgrades_label = QLabel("<i>Upgrades:</i>")
        upgrades_layout.addWidget(upgrades_label)
        
        upgrade_entries = {} # Local dict for this player's upgrade widgets
        upgrade_list = ['Health', 'Stamina', 'ExtraJump', 'Launch', 'MapPlayerCount', 'Speed', 'Strength', 'Range', 'Throw']
        for upgrade_name in upgrade_list:
            upgrade_frame = QFrame()
            upgrade_layout = QHBoxLayout(upgrade_frame)
            upgrade_label = QLabel(f"{upgrade_name}:")
            entry = QLineEdit()
            upgrade_layout.addWidget(upgrade_label)
            upgrade_layout.addWidget(entry)
            upgrades_layout.addWidget(upgrade_frame)
            upgrade_entries[upgrade_name] = entry # Store widget
            
        layout.addWidget(upgrades_group)
        self.player_layout.addWidget(frame) # Add player frame to the main player layout
        
        # Store references
        self.player_widgets[player_id] = {
            'health': health_entry,
            'upgrades': upgrade_entries
        }
        return self.player_widgets[player_id]

    def save_changes(self):
        try:
            # Ensure base structure exists
            if 'dictionaryOfDictionaries' not in self.json_data: self.json_data['dictionaryOfDictionaries'] = {}
            if 'value' not in self.json_data['dictionaryOfDictionaries']: self.json_data['dictionaryOfDictionaries']['value'] = {}
            dod_value = self.json_data['dictionaryOfDictionaries']['value']
            if 'runStats' not in dod_value: dod_value['runStats'] = {}
            if 'teamName' not in self.json_data: self.json_data['teamName'] = {}

            # --- Update JSON from World Tab --- 
            # Use temporary dict for runStats updates
            run_stats_update = {}
            try: run_stats_update['level'] = int(self.level_entry.text()) 
            except ValueError: print("Invalid value for Level")
            try: run_stats_update['currency'] = int(self.currency_entry.text())
            except ValueError: print("Invalid value for Currency")
            try: run_stats_update['lives'] = int(self.lives_entry.text())
            except ValueError: print("Invalid value for Lives")
            try: run_stats_update['chargingStationCharge'] = int(self.charging_entry.text())
            except ValueError: print("Invalid value for Charging Station")
            try: run_stats_update['totalHaul'] = int(self.haul_entry.text())
            except ValueError: print("Invalid value for Total Haul")
            # Update the main dictionary
            dod_value['runStats'].update(run_stats_update)
            self.json_data['teamName']['value'] = self.teamname_entry.text()
            print("[DEBUG save] Updated World stats in json_data")

            # --- Update JSON from Player Tab --- 
            if 'playerHealth' not in dod_value: dod_value['playerHealth'] = {}
            player_health_update = {} # Use temporary dict for updates
            player_upgrades_update = {} # Use nested temp dicts {upgrade_key: {player_id: value}}

            for player_id_str, widgets in self.player_widgets.items():
                player_id = str(player_id_str) # Ensure key is string
                try:
                    # Save health
                    player_health_update[player_id] = int(widgets['health'].text())
                except ValueError: print(f"Invalid health value for player {player_id}")
                
                # Save upgrades
                for upgrade_name, entry_widget in widgets['upgrades'].items():
                    upgrade_key = f'playerUpgrade{upgrade_name}'
                    if upgrade_key not in player_upgrades_update: player_upgrades_update[upgrade_key] = {}
                    try:
                        player_upgrades_update[upgrade_key][player_id] = int(entry_widget.text())
                    except ValueError: print(f"Invalid {upgrade_name} value for player {player_id}")
            
            # Update the main dictionary
            dod_value['playerHealth'].update(player_health_update)
            for upgrade_key, upgrades in player_upgrades_update.items():
                 if upgrade_key not in dod_value: dod_value[upgrade_key] = {}
                 dod_value[upgrade_key].update(upgrades)
            print("[DEBUG save] Updated Player stats in json_data")

            # --- Process Advanced Tab --- 
            save_data_source = self.json_data # Default to data updated from World/Player tabs
            advanced_tab_modified = self.json_text.document().isModified()
            
            if advanced_tab_modified:
                print("[DEBUG save] Advanced tab was modified. Attempting to use its content.")
                try:
                    advanced_text = self.json_text.toPlainText()
                    advanced_json = json.loads(advanced_text)
                    # If parsing advanced_text succeeds, THIS becomes the data to save.
                    save_data_source = advanced_json 
                    print("[DEBUG save] Using valid JSON from modified Advanced tab.")
                except json.JSONDecodeError:
                    # If JSON in advanced tab is invalid, WARN and DO NOT SAVE.
                    QMessageBox.critical(self, "Error Saving", "Invalid JSON in Advanced tab. Please fix or revert changes before saving.")
                    print("[DEBUG save] Invalid JSON in modified Advanced tab. Save aborted.")
                    return # Stop the save process
            else:
                 print("[DEBUG save] Advanced tab not modified. Using data from World/Player tabs.")
                 
            # --- Encrypt and Save --- 
            from lib.encrypt import encrypt_es3
            # Use the determined save_data_source (either original + GUI edits, or valid Advanced tab edits)
            json_string = json.dumps(save_data_source, indent=4) 
            json_bytes = json_string.encode('utf-8')
            print(f"[DEBUG save] Calling encrypt_es3 with password: {self.key[:10]}... on {len(json_bytes)} json bytes") # DEBUG
            encrypted_data = encrypt_es3(json_bytes, self.key) # Pass the full password string
            print(f"[DEBUG save] Encrypted data length (IV + Ciphertext): {len(encrypted_data)}") # DEBUG
            
            with open(self.save_file_path, 'wb') as f:
                f.write(encrypted_data)
                
            # Mark document as unmodified ONLY after successful save
            self.json_text.document().setModified(False) 
                
            QMessageBox.information(self, "Success", "Save file updated successfully")
            self.accept() # Close dialog on success
            
        except ImportError:
             QMessageBox.critical(self, "Error", "Failed to load crypto library for saving. Is pycryptodome installed?")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save changes: {str(e)}")

class RepoSaveManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Save Backup Manager")
        self.setMinimumSize(800, 600)
        
        self.setup_paths() # Call path setup FIRST
        
        # Initialize descriptions AFTER paths are set
        self.descriptions = self.load_descriptions()

        # Central Widget and Main Layout must be defined before adding other widgets
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout(main_widget) # Use self.layout for clarity
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(24, 24, 24, 24)
        
        self.setup_styling() # Apply styling
        self.setup_ui_elements() # Create and add UI elements to self.layout
        self.connect_signals() # Connect signals AFTER elements are created

        # Initial refresh
        self.refresh_save_list()
        self.update_button_states() # Set initial button states

    def setup_paths(self):
        # Define paths
        self.repo_saves_path = r"C:\Users\aranr\AppData\LocalLow\semiwork\Repo\saves"
        self.backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
        self.descriptions_file = os.path.join(self.backup_path, "descriptions.json")
        self.editor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "editor_temp")
        
        # Create directories if they don't exist
        os.makedirs(self.backup_path, exist_ok=True)
        os.makedirs(self.editor_path, exist_ok=True)

    def setup_styling(self):
         # Set modern dark mode styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1c1c1e;
            }
            QWidget {
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton {
                background-color: #2c2c2e;
                color: #ffffff;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3a3a3c;
            }
            QPushButton:pressed {
                background-color: #48484a;
            }
            QPushButton#primary {
                background-color: #0A84FF;
            }
            QPushButton#primary:hover {
                background-color: #007AFF;
            }
            QPushButton#primary:pressed {
                background-color: #0066CC;
            }
            QPushButton#danger {
                background-color: #ff3b30;
            }
            QPushButton#danger:hover {
                background-color: #ff453a;
            }
            QPushButton#danger:pressed {
                background-color: #ff3b30;
            }
            QLabel {
                color: #ffffff;
            }
            QTableWidget {
                background-color: #2c2c2e;
                border: 1px solid #3a3a3c;
                border-radius: 12px;
                gridline-color: #3a3a3c;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #3a3a3c;
            }
            QTableWidget::item:selected {
                background-color: #0A84FF;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #2c2c2e;
                color: #ffffff;
                padding: 12px;
                border: none;
                border-bottom: 1px solid #3a3a3c;
                font-weight: 600;
                font-size: 14px;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #2c2c2e;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #3a3a3c;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QFrame#separator {
                background-color: #3a3a3c;
            }
        """) # Keep existing styles

    def setup_ui_elements(self):
        # --- Top section - Quick actions --- 
        quick_actions_layout = QHBoxLayout()
        self.backup_btn = QPushButton("⬇️ Backup Current Save")
        self.backup_btn.setObjectName("primary")
        self.restore_btn = QPushButton("⬆️ Restore Selected Save")
        self.open_folder_btn = QPushButton("📂 Open Save Folder")
        
        quick_actions_layout.addWidget(self.backup_btn)
        quick_actions_layout.addWidget(self.restore_btn)
        quick_actions_layout.addWidget(self.open_folder_btn)
        self.layout.addLayout(quick_actions_layout)
        
        # --- Separator --- 
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        self.layout.addWidget(separator)
        
        # --- Save table --- 
        table_label = QLabel("Your Saved Backups")
        table_label.setFont(QFont("SF Pro Text", 16, QFont.Weight.Bold))
        self.layout.addWidget(table_label)
        
        self.save_table = QTableWidget()
        # Columns: Save Name, Players, Day, Notes (Removed Haul)
        self.save_table.setColumnCount(4) 
        self.save_table.setHorizontalHeaderLabels(["Save Name", "Players", "Day", "Notes"])
        # Adjust resize modes
        self.save_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Save Name
        self.save_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Players
        # Removed Haul column (was index 2)
        self.save_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Day (now index 2)
        self.save_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) # Notes (now index 3)
        
        self.save_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.save_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.save_table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        # Ensure delegate is set for the correct column (Notes is now column 3)
        self.save_table.setItemDelegateForColumn(3, DescriptionDelegate()) 
        self.save_table.verticalHeader().setDefaultSectionSize(50) # Set row height
        self.layout.addWidget(self.save_table)
        
        # --- Bottom actions --- 
        bottom_actions = QHBoxLayout()
        # Left group
        left_group = QHBoxLayout()
        self.duplicate_btn = QPushButton("📋 Duplicate")
        self.edit_button = QPushButton("✏️ Edit Save")
        left_group.addWidget(self.duplicate_btn)
        left_group.addWidget(self.edit_button)
        # Right group
        right_group = QHBoxLayout()
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setObjectName("danger")
        right_group.addWidget(self.delete_btn)
        # Add groups to bottom layout
        bottom_actions.addLayout(left_group)
        bottom_actions.addStretch()
        bottom_actions.addLayout(right_group)
        self.layout.addLayout(bottom_actions)

    def connect_signals(self):
        # Connect signals
        self.backup_btn.clicked.connect(self.create_backup)
        self.restore_btn.clicked.connect(self.insert_into_repo)
        self.duplicate_btn.clicked.connect(self.duplicate_save)
        self.delete_btn.clicked.connect(self.delete_save)
        self.edit_button.clicked.connect(self.open_in_editor)
        self.open_folder_btn.clicked.connect(self.open_save_folder)
        self.save_table.itemChanged.connect(self.on_description_changed)
        self.save_table.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self, selected, deselected):
        self.update_button_states()

    def update_button_states(self):
        has_selection = len(self.save_table.selectedItems()) > 0
        self.restore_btn.setEnabled(has_selection)
        self.edit_button.setEnabled(has_selection)
        self.duplicate_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def load_descriptions(self):
        """Load descriptions from file"""
        if os.path.exists(self.descriptions_file):
            try:
                with open(self.descriptions_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_descriptions(self):
        """Save descriptions to file"""
        try:
            with open(self.descriptions_file, 'w') as f:
                json.dump(self.descriptions, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save descriptions: {str(e)}")

    def refresh_save_list(self):
        """Refresh the table with current saves and extracted info (incl PFPs)"""
        self.save_table.setRowCount(0)
        self.save_table.clearContents() # Clear widgets too
        from lib.decrypt import decrypt_es3 
        password = "Why would you want to cheat?... :o It's no fun. :') :'D"
        
        try:
            backup_items = sorted([item for item in os.listdir(self.backup_path) if os.path.isdir(os.path.join(self.backup_path, item)) and item.startswith("REPO_SAVE_")], reverse=True)
            
            for item_name in backup_items:
                row = self.save_table.rowCount()
                self.save_table.insertRow(row)
                
                # --- Column 0: Save Name --- 
                name_item = QTableWidgetItem(item_name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.save_table.setItem(row, 0, name_item)

                # --- Extract data and Create Widgets for other columns --- 
                player_ids = []
                player_names_dict = {} # Store names for tooltip
                day_str = "N/A"
                es3_file_path = None
                item_path = os.path.join(self.backup_path, item_name)
                
                try:
                    # Find the .es3 file
                    for filename in os.listdir(item_path):
                        if filename.endswith('.es3'):
                            es3_file_path = os.path.join(item_path, filename)
                            break
                    
                    if es3_file_path:
                        # Read and decrypt
                        with open(es3_file_path, 'rb') as f:
                            encrypted_content = f.read()
                        decrypted_data = decrypt_es3(encrypted_content, password)
                        json_data = json.loads(decrypted_data)
                        
                        # Extract data safely
                        dict_of_dicts = json_data.get('dictionaryOfDictionaries', {}).get('value', {})
                        run_stats = dict_of_dicts.get('runStats', {})
                        player_names_dict = json_data.get("playerNames", {}).get("value", {}) # Get names dict
                        player_ids = list(player_names_dict.keys()) # Get IDs for PFP fetching
                        
                        day_str = str(run_stats.get('level', 'N/A'))
                    else:
                        print(f"Warning: No .es3 file found in {item_name}")
                        
                except Exception as e:
                    print(f"Error processing save {item_name}: {e}")
                    day_str = "Error"
                    player_ids = [] 
                    player_names_dict = {}

                # --- Column 1: Players (PFPs) --- 
                pfp_widget = QWidget()
                pfp_layout = QHBoxLayout(pfp_widget)
                pfp_layout.setContentsMargins(5, 0, 5, 0) 
                pfp_layout.setSpacing(2) 
                player_names_for_tooltip = [] # List to collect names for container tooltip
                if player_ids:
                    for player_id in player_ids:
                        pfp_label = QLabel()
                        pfp_pixmap = fetch_steam_profile_picture(player_id)
                        pfp_label.setPixmap(pfp_pixmap)
                        pfp_label.setFixedSize(DEFAULT_PFP_SIZE, DEFAULT_PFP_SIZE)
                        player_name = player_names_dict.get(player_id, "Unknown")
                        # pfp_label.setToolTip(player_name) # Remove tooltip from individual label
                        player_names_for_tooltip.append(player_name) # Add name to list
                        pfp_layout.addWidget(pfp_label)
                    pfp_layout.addStretch() 
                    # Set tooltip on the container widget
                    pfp_widget.setToolTip(", ".join(player_names_for_tooltip))
                else:
                     no_players_label = QLabel("N/A" if day_str != "Error" else "Error") 
                     pfp_layout.addWidget(no_players_label)
                     pfp_widget.setToolTip("No players found or error reading save.") # Tooltip for container
                pfp_widget.setLayout(pfp_layout)
                self.save_table.setCellWidget(row, 1, pfp_widget)
                
                # --- Column 2: Day (previously Haul) --- 
                day_item = QTableWidgetItem(day_str)
                day_item.setFlags(day_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.save_table.setItem(row, 2, day_item) # Set item at index 2
                    
                # --- Column 3: Notes (Editable) --- 
                desc = self.descriptions.get(item_name, "") # Gets saved note or empty string
                desc_item = QTableWidgetItem(desc)
                self.save_table.setItem(row, 3, desc_item) # Set item at index 3
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list saves: {str(e)}")

    def on_description_changed(self, item):
        """Handle description changes"""
        # Check if the changed item is in the Notes column (index 3)
        if item.column() == 3: 
            save_name_item = self.save_table.item(item.row(), 0)
            if save_name_item: # Ensure save name item exists
                 save_name = save_name_item.text()
                 self.descriptions[save_name] = item.text()
                 self.save_descriptions()

    def get_selected_save(self):
        selected_items = self.save_table.selectedItems()
        if not selected_items:
            return None
        return selected_items[0].text()
            
    def duplicate_save(self):
        save_name = self.get_selected_save()
        if not save_name:
            QMessageBox.warning(self, "Warning", "Please select a save to duplicate")
            return
            
        source_path = os.path.join(self.backup_path, save_name)
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        new_save_name = f"REPO_SAVE_{timestamp}"
        dest_path = os.path.join(self.backup_path, new_save_name)
        
        try:
            # First copy the entire directory
            shutil.copytree(source_path, dest_path)
            
            # Then rename all .es3 files inside to match the new save name
            for file in os.listdir(dest_path):
                if file.endswith('.es3'):
                    old_path = os.path.join(dest_path, file)
                    new_file = file.replace(save_name, new_save_name)
                    new_path = os.path.join(dest_path, new_file)
                    os.rename(old_path, new_path)
            
            # Copy the description if it exists
            self.descriptions[new_save_name] = f"Copy of {save_name}"
            self.save_descriptions()
            self.refresh_save_list()
            QMessageBox.information(self, "Success", f"Created duplicate save")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to duplicate save: {str(e)}")
            
    def create_backup(self):
        try:
            # Get all saves from the repo saves folder
            saves = [f for f in os.listdir(self.repo_saves_path) 
                    if os.path.isdir(os.path.join(self.repo_saves_path, f)) 
                    and f.startswith("REPO_SAVE_")]
            if not saves:
                QMessageBox.warning(self, "Warning", "No saves found in the game folder")
                return
            
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Select Save to Backup")
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #1c1c1e;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 14px;
                    margin-bottom: 10px;
                }
                QComboBox {
                    background-color: #2c2c2e;
                    color: #ffffff;
                    border: 1px solid #3a3a3c;
                    border-radius: 6px;
                    padding: 8px;
                    min-width: 300px;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid #ffffff;
                    margin-right: 10px;
                }
                QPushButton {
                    background-color: #0A84FF;
                    color: #ffffff;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #007AFF;
                }
                QPushButton#cancel {
                    background-color: #2c2c2e;
                }
                QPushButton#cancel:hover {
                    background-color: #3a3a3c;
                }
            """)
            
            layout = QVBoxLayout(dialog)
            
            # Add label
            label = QLabel("Select a save to backup:")
            layout.addWidget(label)
            
            # Create dropdown
            combo = QComboBox()
            combo.addItem("Latest Save")
            combo.addItems(sorted(saves, reverse=True))
            layout.addWidget(combo)
            
            # Add buttons
            button_layout = QHBoxLayout()
            ok_button = QPushButton("Backup")
            cancel_button = QPushButton("Cancel")
            cancel_button.setObjectName("cancel")
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            # Set dialog properties
            dialog.setLayout(layout)
            dialog.setFixedSize(400, 150)
            dialog.setModal(True)
            
            # Connect buttons
            ok_button.clicked.connect(dialog.accept)
            cancel_button.clicked.connect(dialog.reject)
            
            # Show dialog and get result
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get selected save
                selected_save = combo.currentText()
                if selected_save == "Latest Save":
                    selected_save = max(saves)
                
                source_path = os.path.join(self.repo_saves_path, selected_save)
                dest_path = os.path.join(self.backup_path, selected_save)
                
                if os.path.exists(dest_path):
                    reply = QMessageBox.question(self, "Save Already Exists",
                                              f"A backup of this save already exists. Do you want to overwrite it?",
                                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.No:
                        return
                    shutil.rmtree(dest_path)
                    
                shutil.copytree(source_path, dest_path)
                self.refresh_save_list()
                QMessageBox.information(self, "Success", f"Created backup of {selected_save}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create backup: {str(e)}")
            
    def delete_save(self):
        save_name = self.get_selected_save()
        if not save_name:
            QMessageBox.warning(self, "Warning", "Please select a save to delete")
            return
            
        reply = QMessageBox.question(self, "Confirm Delete",
                                   f"Are you sure you want to delete {save_name}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Delete from backup
                backup_path = os.path.join(self.backup_path, save_name)
                shutil.rmtree(backup_path)
                
                # Ask if user wants to delete from repo
                repo_path = os.path.join(self.repo_saves_path, save_name)
                if os.path.exists(repo_path):
                    reply = QMessageBox.question(self, "Delete from Repo",
                                              "Do you also want to delete this save from the game?",
                                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.Yes:
                        shutil.rmtree(repo_path)
                
                if save_name in self.descriptions:
                    del self.descriptions[save_name]
                    self.save_descriptions()
                self.refresh_save_list()
                QMessageBox.information(self, "Success", "Save deleted successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete save: {str(e)}")
                
    def insert_into_repo(self):
        save_name = self.get_selected_save()
        if not save_name:
            QMessageBox.warning(self, "Warning", "Please select a save to insert")
            return
            
        try:
            source_path = os.path.join(self.backup_path, save_name)
            dest_path = os.path.join(self.repo_saves_path, save_name)
            
            if os.path.exists(dest_path):
                reply = QMessageBox.question(self, "Confirm Overwrite",
                                          f"Save {save_name} already exists in the repo. Overwrite?",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    return
                shutil.rmtree(dest_path)
                
            shutil.copytree(source_path, dest_path)
            QMessageBox.information(self, "Success", f"Save inserted into repo successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to insert save: {str(e)}")

    def open_save_folder(self):
        try:
            subprocess.Popen(f'explorer "{self.backup_path}"')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open save folder: {str(e)}")

    def open_in_editor(self):
        selected_save_name = self.get_selected_save()
        if not selected_save_name:
            # This case should ideally not happen if button is disabled correctly
            QMessageBox.warning(self, "No Save Selected", "Please select a save from the list to edit.")
            return

        backup_save_path = os.path.join(self.backup_path, selected_save_name)
        temp_save_dir = os.path.join(self.editor_path, selected_save_name) # Temp dir for the save

        try:
            # Ensure clean temp directory
            if os.path.exists(temp_save_dir):
                shutil.rmtree(temp_save_dir)
            shutil.copytree(backup_save_path, temp_save_dir)

            # Find the .es3 file within the temp directory
            es3_file_path = None
            for filename in os.listdir(temp_save_dir):
                if filename.endswith('.es3'):
                    es3_file_path = os.path.join(temp_save_dir, filename)
                    break
            
            if not es3_file_path:
                raise FileNotFoundError("No .es3 file found in the temporary save directory.")

            # Open the SaveEditor dialog
            editor_dialog = SaveEditor(es3_file_path, self) 
            result = editor_dialog.exec() # Show the modal dialog

            # If the user saved changes (dialog accepted), copy back from temp
            if result == QDialog.DialogCode.Accepted:
                print(f"Copying changes back from {temp_save_dir} to {backup_save_path}")
                # Copy back the edited save (overwrite existing backup)
                if os.path.exists(backup_save_path):
                     shutil.rmtree(backup_save_path) # Remove old backup before copying new
                shutil.copytree(temp_save_dir, backup_save_path)
                # No need to refresh list unless rename happens (which editor doesn't do)
                QMessageBox.information(self, "Editor", "Changes saved and applied to the backup.")
            else:
                 print("Editor cancelled, changes discarded.")
            
            # Clean up temp directory regardless of outcome
            if os.path.exists(temp_save_dir):
                 shutil.rmtree(temp_save_dir)

        except FileNotFoundError as fnf_error:
             QMessageBox.critical(self, "Error", f"Failed to prepare editor: {fnf_error}")
             if os.path.exists(temp_save_dir): shutil.rmtree(temp_save_dir)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while opening or saving in the editor: {e}")
            # Attempt cleanup even on error
            if os.path.exists(temp_save_dir):
                 try: shutil.rmtree(temp_save_dir)
                 except: print("Failed to clean up temp directory after error.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = RepoSaveManager()
    window.show()
    sys.exit(app.exec()) 