# app/main_window.py

import sys
import os
import json
import re # Import regex for parsing progress
import base64 # Import for decoding data URIs
import threading # Needed for thread references
import traceback # For detailed error logging
import subprocess # For os.startfile alternative / explorer opening
from urllib.parse import urlparse
from webbrowser import open as webopen
from functools import partial # Used for connecting signals with arguments

# Import necessary PySide6 modules
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QStackedLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit, QCheckBox, QFrame,
    QSizePolicy, QFileDialog, QMessageBox, QButtonGroup, QScrollArea, QSpacerItem,
    QProgressBar, QGroupBox, QGraphicsDropShadowEffect
)
from PySide6.QtGui import (
    QPixmap, QIcon, QFont, QPalette, QColor, QGuiApplication, QTextCursor
)
from PySide6.QtCore import (
    Qt, QThread, QObject, Signal, Slot, QSize, QEvent, QCoreApplication, QPoint,
    QByteArray
)

# --- Import App Components ---
from .ui_constants import * # Import colors, styles, SVGs, template
from .workers import DownloadWorker, UpdateCheckWorker # Import worker classes

# --- CustomMessageBox Import ---

try:
    # Assuming messagebox.py is in the same directory (app/)
    from .messagebox import CustomMessageBox
except ImportError:
    print("Warning: CustomMessageBox not found. Using standard QMessageBox.")
    # Fallback logic is handled in show_custom_messagebox method.





# --- Utility and Variable Imports ---
# Group imports from your utils and vars modules
# Add fallback logic here if these imports might fail
try:
    # Assuming utils/__init__.py exports these (or they come from config.py/path.py)
    from utils import (
        CURRENT_VERSION, config_file, DEFAULT_SETTINGS,
        load_config, resource_path
    )
    # windowTheme was imported but not used in the App class, removed for now.
    # If needed, add 'windowTheme' back to the import list.
except ImportError as e:
    print(f"CRITICAL ERROR: Failed importing from 'utils': {e}. Using placeholders.")
    CURRENT_VERSION = "0.0.0-fallback"
    config_file = "config.json"
    DEFAULT_SETTINGS = {
        "theme": "system",
        "download_path": os.path.expanduser("~"),
        "open_folder_after_download": True
    }
    def load_config():
        print("WARNING: Using fallback load_config(). Returning default settings.")
        return DEFAULT_SETTINGS.copy()
    def resource_path(relative_path):
        abs_path = os.path.abspath(relative_path)
        print(f"WARNING: Using fallback resource_path(). Path: {abs_path}")
        # Basic implementation: look relative to this file's dir
        # A better implementation would handle frozen executables (PyInstaller)
        base_path = os.path.dirname(__file__)
        return os.path.join(base_path, relative_path)

try:
    # Assuming vars/__init__.py exports 'filetypes' from vars/filetypes.py
    from vars import filetypes
except ImportError as e:
    print(f"CRITICAL ERROR: Failed importing 'filetypes' from vars: {e}. Using placeholder.")
    filetypes = {
        "mp4": {"fileext": "mp4", "audio": False, "codec": "h264"},
        "mp3": {"fileext": "mp3", "audio": True, "codec": "mp3"}
    }
# --- End Utility/Variable Imports ---


# --- Main Application Window ---
class App(QWidget):
    # Constants, STYLE_TEMPLATE, ICON_DATA_URIS are now imported from ui_constants

    def __init__(self):
        super().__init__()
        try:
            self._config = load_config()
        except Exception as e:
            print(f"FATAL: Failed to load configuration: {e}. Using defaults.")
            self._config = DEFAULT_SETTINGS.copy()
            error_box = QMessageBox(QMessageBox.Icon.Critical, "Config Error",
                                      f"Failed to load configuration file '{config_file}'.\n"
                                      f"Reason: {e}\n\nApplication will use defaults but may not function correctly.",
                                      QMessageBox.StandardButton.Ok, self)
            error_box.exec()

        self._is_dark_mode = self.detect_dark_mode(self._config.get("theme", "system"))

        # Page Initialization Flags
        self._home_initialized = False
        self._settings_initialized = False
        self._about_initialized = False
        self._console_initialized = False

        self.current_page = "none"
        self.download_thread: QThread | None = None
        self.download_worker: DownloadWorker | None = None
        self.update_thread: QThread | None = None
        self.update_worker: UpdateCheckWorker | None = None

        self.progress_regex = re.compile(r"\[download\]\s+([\d\.]+%)")
        self._last_download_path: str | None = None
        self._error_already_handled = False

        self.init_ui()
        self.create_left_frame()
        self.create_right_frame()
        self.apply_stylesheet(self._config.get("theme", "system"))
        self.show_home()
        self.start_update_check()

        screen_geo = QGuiApplication.primaryScreen().availableGeometry()
        if self.height() > screen_geo.height():
            self.resize(self.width(), screen_geo.height())


    def init_ui(self):
        self.setWindowTitle("ForgeYT")
        try:
            self.setWindowIcon(self.get_icon("ForgeYT"))
        except Exception as e:
            print(f"Warning: Failed to set application icon - {e}")
        self.setMinimumSize(700, 600)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.left_frame = QWidget()
        self.left_frame.setObjectName("leftFrame")
        self.left_frame.setFixedWidth(180)
        main_layout.addWidget(self.left_frame)

        self.right_frame = QWidget()
        self.right_frame.setObjectName("rightFrame")
        main_layout.addWidget(self.right_frame, 1)

        self.setLayout(main_layout)

    def detect_dark_mode(self, theme_setting: str) -> bool:
        """ Detects if dark mode should be used based on setting or system. """
        if theme_setting == "dark":
            return True
        elif theme_setting == "light":
            return False
        else: # System theme detection
            try:
                style_hints = QGuiApplication.styleHints()
                color_scheme = style_hints.colorScheme()
                if color_scheme != Qt.ColorScheme.Unknown:
                    return color_scheme == Qt.ColorScheme.Dark
            except Exception:
                pass # Ignore errors and fallback

            try: # Fallback to palette check
                if self.palette():
                    return self.palette().color(QPalette.ColorRole.Window).lightness() < 128
                else:
                    print("Warning: Invalid palette during dark mode detection.")
                    return False
            except Exception as e:
                print(f"Warning: Could not reliably detect system theme: {e}. Defaulting to light.")
                return False

    def apply_stylesheet(self, theme: str):
        """ Applies the stylesheet based on the selected theme using a template. """
        self._is_dark_mode = self.detect_dark_mode(theme)

        # Define colors based on mode using imported constants from ui_constants
        bg1 = C_BG_DARK_1 if self._is_dark_mode else C_BG_LIGHT_1
        bg2 = C_BG_DARK_2 if self._is_dark_mode else C_BG_LIGHT_2
        btn = C_BTN_DARK if self._is_dark_mode else C_BTN_LIGHT
        btn_h = C_BTN_HOVER_DARK if self._is_dark_mode else C_BTN_HOVER_LIGHT
        text = C_TEXT_DARK if self._is_dark_mode else C_TEXT_LIGHT
        input_bg = bg1
        input_border = C_INPUT_BORDER_DARK if self._is_dark_mode else C_INPUT_BORDER_LIGHT
        theme_btn_unchecked_bg = C_THEME_BTN_UNCHECKED_BG_DARK if self._is_dark_mode else C_THEME_BTN_UNCHECKED_BG_LIGHT
        theme_btn_unchecked_text = text
        scrollbar_bg = C_SCROLLBAR_BG_DARK if self._is_dark_mode else C_SCROLLBAR_BG_LIGHT
        console_bg = C_CONSOLE_BG_DARK if self._is_dark_mode else C_CONSOLE_BG_LIGHT

        # Update internal colors (used by CustomMessageBox etc.)
        self.font_color = text
        self.buttoncolor = btn
        self.buttoncolor_hover = btn_h

        # Get dynamic resource path for combobox arrow
        arrow_icon_path_str = ""
        arrow_icon_key = "down_arrow"  # New key for the down arrow data URI
        if arrow_icon_key in ICON_DATA_URIS:
            arrow_icon_path_str = ICON_DATA_URIS[arrow_icon_key]
        else:
            arrow_icon_name = f"assets/down_arrow_{'dark' if self._is_dark_mode else 'light'}.png"
            try:
                arrow_icon_path = resource_path(arrow_icon_name)  # Use imported resource_path
                if os.path.exists(arrow_icon_path):
                    arrow_icon_path_str = arrow_icon_path.replace('\\', '/')
                else:
                    print(f"Warning: Combobox arrow icon not found: {arrow_icon_name}")
            except Exception as e:
                print(f"Warning: Could not get arrow icon path ({arrow_icon_name}): {e}")

        # Format the template using f-string or .format()
        try:
            # Use imported STYLE_TEMPLATE and S_* style constants
            style = STYLE_TEMPLATE.format(
                text=text, bg1=bg1, bg2=bg2, btn=btn, btn_h=btn_h,
                input_bg=input_bg, input_border=input_border,
                theme_btn_unchecked_bg=theme_btn_unchecked_bg,
                theme_btn_unchecked_text=theme_btn_unchecked_text,
                scrollbar_bg=scrollbar_bg,
                scrollbar_handle=C_SCROLLBAR_HANDLE, # Use imported color constant
                console_bg=console_bg,
                arrow_icon_path=arrow_icon_path_str,
                font_family=S_FONT_FAMILY,
                font_size_default=S_FONT_SIZE_DEFAULT,
                font_size_title=S_FONT_SIZE_TITLE,
                font_size_section=S_FONT_SIZE_SECTION,
                font_size_version=S_FONT_SIZE_VERSION,
                console_font_family=S_CONSOLE_FONT_FAMILY,
                border_radius=S_BORDER_RADIUS,
                input_border_radius=S_INPUT_BORDER_RADIUS,
                nav_btn_padding=S_NAV_BUTTON_PADDING,
                nav_btn_margin=S_NAV_BUTTON_MARGIN,
                action_btn_padding=S_ACTION_BUTTON_PADDING,
            )
            self.setStyleSheet(style)
        except KeyError as e:
            print(f"ERROR: Missing key in STYLE_TEMPLATE formatting: {e}. Stylesheet might be broken.")
        except Exception as e:
            print(f"ERROR: Failed to apply stylesheet: {e}")

        self.update_icons() # Update icons after stylesheet is potentially changed

    def get_icon(self, name: str) -> QIcon:
        """ Loads an icon, preferring data URIs, then themed files, then base files. """
        # This method now uses ICON_DATA_URIS imported from ui_constants
        try:
            # 1. Check Data URIs First
            if name in ICON_DATA_URIS: # Use imported dict
                data_uri = ICON_DATA_URIS[name]
                try:
                    header, encoded_data = data_uri.split(",", 1)
                    if header == "data:image/svg+xml;base64":
                        decoded_svg_bytes = base64.b64decode(encoded_data)
                        byte_array = QByteArray(decoded_svg_bytes)
                        pixmap = QPixmap()
                        if pixmap.loadFromData(byte_array, "SVG"):
                            icon = QIcon()
                            icon.addPixmap(pixmap)
                            return icon
                        else:
                            print(f"Warning: Failed to load SVG data for icon '{name}'. Falling back.")
                    else:
                        print(f"Warning: Unsupported data URI format for icon '{name}'. Falling back.")
                except Exception as e:
                    print(f"Error processing data URI for icon '{name}': {e}. Falling back.")

            # 2. Fallback to File Loading
            icon_suffix = "_dark" if self._is_dark_mode else ""
            try: # Check themed PNG
                themed_path_png = resource_path(f"assets/{name}{icon_suffix}.png")
                if os.path.exists(themed_path_png): return QIcon(themed_path_png)
            except Exception as e: print(f"Warning: Error checking themed PNG for '{name}': {e}")

            try: # Check base PNG
                base_path_png = resource_path(f"assets/{name}.png")
                if os.path.exists(base_path_png): return QIcon(base_path_png)
            except Exception as e: print(f"Warning: Error checking base PNG for '{name}': {e}")

            if name == "ForgeYT": # Fallback for main icon (.ico)
                try:
                    base_path_ico = resource_path(f"assets/{name}.ico")
                    if os.path.exists(base_path_ico): return QIcon(base_path_ico)
                except Exception as e: print(f"Warning: Error checking ICO for '{name}': {e}")

            if name not in ICON_DATA_URIS: # Only warn if file wasn't found AND wasn't a data URI
                 print(f"Warning: Icon asset '{name}' not found (checked data URI, files: .png, {icon_suffix}.png, .ico).")
            return QIcon() # Return empty icon

        except Exception as e:
            print(f"Error loading icon '{name}': {e}")
            return QIcon()

    def update_icons(self):
        nav_icon_size = QSize(20, 20)
        start_icon_size = QSize(28, 28)
        stop_icon_size = QSize(24, 24)

        if hasattr(self, 'home_button'):
            self.home_button.setIcon(self.get_icon("Home"))
            self.home_button.setIconSize(nav_icon_size)
        if hasattr(self, 'settings_button'):
            self.settings_button.setIcon(self.get_icon("Settings"))
            self.settings_button.setIconSize(nav_icon_size)
        if hasattr(self, 'about_button'):
            self.about_button.setIcon(self.get_icon("About"))
            self.about_button.setIconSize(nav_icon_size)
        if hasattr(self, 'console_button'):
            self.console_button.setIcon(self.get_icon("Console"))
            self.console_button.setIconSize(nav_icon_size)
        if hasattr(self, 'start_button'):
            # Use the new "Download" URI SVG
            self.start_button.setIcon(self.get_icon("Download"))
            self.start_button.setIconSize(start_icon_size)
        if hasattr(self, 'stop_button'):
            self.stop_button.setIcon(self.get_icon("stop"))
            self.stop_button.setIconSize(stop_icon_size)
        if hasattr(self, 'update_button') and self.update_button is not None:
            if update_icon := self.get_icon("update"):
                self.update_button.setIcon(update_icon)



    def create_left_frame(self):
        layout = QVBoxLayout(self.left_frame)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.logo_label = QLabel()
        try:
            logo_icon = self.get_icon("ForgeYT")
            if not logo_icon.isNull():
                pixmap = logo_icon.pixmap(QSize(100, 100))
                if not pixmap.isNull():
                    self.logo_label.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                else:
                    raise RuntimeError("Failed to get valid logo pixmap from icon.")
            else:
                raise RuntimeError("Failed to load logo icon.")
        except Exception as e:
            print(f"Warning: Logo 'assets/ForgeYT.*' not found or invalid: {e}")
            self.logo_label.setText("Logo")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.logo_label)

        self.title_label = QLabel("ForgeYT")
        font = QFont("Arial", 18, QFont.Weight.Bold)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        layout.addSpacing(20)

        # Navigation Buttons
        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)

        self.home_button = self._create_nav_button("Home", self.show_home)
        layout.addWidget(self.home_button)
        self.nav_button_group.addButton(self.home_button)

        self.settings_button = self._create_nav_button("Settings", self.show_settings)
        layout.addWidget(self.settings_button)
        self.nav_button_group.addButton(self.settings_button)

        self.about_button = self._create_nav_button("About", self.show_about)
        layout.addWidget(self.about_button)
        self.nav_button_group.addButton(self.about_button)

        self.console_button = self._create_nav_button("Console", self.show_console)
        layout.addWidget(self.console_button)
        self.nav_button_group.addButton(self.console_button)

        layout.addStretch(1)



    def _create_nav_button(self, text: str, slot_func: Slot) -> QPushButton:
        """ Helper to create and configure navigation buttons. """
        button = QPushButton(f" {text}")
        button.setObjectName("navButton")
        button.setCheckable(True)
        button.clicked.connect(slot_func)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return button


    def create_right_frame(self):
        """ Creates the right frame container and QStackedLayout for pages. """
        layout = QVBoxLayout(self.right_frame)
        layout.setContentsMargins(15, 15, 15, 15)

        self.pages_layout = QStackedLayout()
        layout.addLayout(self.pages_layout)

        # Page container widgets
        self.home_page_widget = QWidget()
        self.settings_page_widget = QWidget()
        self.about_page_widget = QWidget()
        self.console_page_widget = QWidget()

        self.pages_layout.addWidget(self.home_page_widget)
        self.pages_layout.addWidget(self.settings_page_widget)
        self.pages_layout.addWidget(self.about_page_widget)
        self.pages_layout.addWidget(self.console_page_widget)

        # -- Shared Widgets --
        self.loading_label = QLabel("Processing...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setObjectName("loadingLabel")
        self.loading_label.hide()

        self.start_button = QPushButton("")
        self.start_button.setObjectName("startButton")
        self.start_button.setToolTip("Start Download")
        self.start_button.clicked.connect(self.start_downloading)
        self.start_button.hide()

        self.stop_button = QPushButton("")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setToolTip("Stop Download")
        self.stop_button.clicked.connect(self.stop_downloading)
        self.stop_button.hide()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.hide()


    # --- Page Creation / Update Methods ---

    def show_home(self):
        """ Creates (if needed) and shows the Home page content with expanded download options. """
        self.current_page = "home"
        if not self._home_initialized:
            # Use a main vertical layout
            main_page_layout = QVBoxLayout(self.home_page_widget)
            main_page_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            main_page_layout.setSpacing(15) # Increased spacing between sections

            # --- Top Section (URL, Basic Format) ---
            top_group = QWidget()
            top_layout = QVBoxLayout(top_group)
            top_layout.setSpacing(10)
            top_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            title = QLabel("ForgeYT"); title.setObjectName("pageTitle")
            top_layout.addWidget(title, 0, Qt.AlignmentFlag.AlignCenter)

            url_label = QLabel("Enter Video/Playlist URL") # Updated label
            top_layout.addWidget(url_label, 0, Qt.AlignmentFlag.AlignCenter)
            self.profile_entry = QLineEdit(); self.profile_entry.setPlaceholderText("Paste YouTube URL here...")
            self.profile_entry.setMinimumWidth(450); top_layout.addWidget(self.profile_entry, 0, Qt.AlignmentFlag.AlignCenter)

            # Basic Format Grid (File Type, Qualities)
            format_grid = QGridLayout()
            format_grid.setColumnStretch(1, 1)
            format_grid.setHorizontalSpacing(10)
            format_grid.setVerticalSpacing(8)
            format_grid.setContentsMargins(0, 5, 0, 5)

            dropdown_label = QLabel("File Type:")
            self.dropdown_menu = QComboBox(); self.dropdown_menu.setMinimumWidth(150)
            # ... (populate dropdown_menu as before) ...
            if isinstance(filetypes, dict):
                self.dropdown_menu.addItems([key.upper() for key in filetypes.keys()])
            else:
                self.dropdown_menu.addItem("Error")
            mp4_index = self.dropdown_menu.findText("MP4", Qt.MatchFlag.MatchFixedString)
            self.dropdown_menu.setCurrentIndex(mp4_index if mp4_index >= 0 else 0)
            self.dropdown_menu.currentIndexChanged.connect(self._update_quality_options_visibility)
            format_grid.addWidget(dropdown_label, 0, 0, Qt.AlignmentFlag.AlignRight)
            format_grid.addWidget(self.dropdown_menu, 0, 1)

            self.video_quality_label = QLabel("Video Quality:")
            self.video_quality_combo = QComboBox(); self.video_quality_combo.setMinimumWidth(150)
            self.video_quality_combo.addItems(["Best", "1080p", "720p", "480p", "360p"])
            format_grid.addWidget(self.video_quality_label, 1, 0, Qt.AlignmentFlag.AlignRight)
            format_grid.addWidget(self.video_quality_combo, 1, 1)

            self.audio_quality_label = QLabel("Audio Quality:")
            self.audio_quality_combo = QComboBox(); self.audio_quality_combo.setMinimumWidth(150)
            self.audio_quality_combo.addItems(["Best (≈192k)", "High (128k)", "Medium (96k)", "Low (64k)"])
            format_grid.addWidget(self.audio_quality_label, 2, 0, Qt.AlignmentFlag.AlignRight)
            format_grid.addWidget(self.audio_quality_combo, 2, 1)

            top_layout.addLayout(format_grid) # Add grid to top section
            main_page_layout.addWidget(top_group) # Add top section to main layout

            # --- Additional Options Sections using GroupBoxes ---
            options_layout = QHBoxLayout() # Layout to hold group boxes side-by-side if space allows
            options_layout.setSpacing(15)

            # --- GroupBox 1: Playlist & Output ---
            playlist_output_group = QGroupBox("Playlist && Output Options")
            po_layout = QVBoxLayout(playlist_output_group)
            po_layout.setSpacing(8)

            self.playlist_range_entry = QLineEdit()
            self.playlist_range_entry.setPlaceholderText("e.g., 2-5, 8, 10-") # Tooltip added below
            self.playlist_range_entry.setToolTip("Specify playlist items (e.g., '2-5, 8, 10-'). Leave empty for single video or full playlist.")
            po_layout.addWidget(QLabel("Playlist Items:"))
            po_layout.addWidget(self.playlist_range_entry)

            self.playlist_reverse_checkbox = QCheckBox("Download playlist items in reverse order")
            po_layout.addWidget(self.playlist_reverse_checkbox)

            po_layout.addSpacing(10) # Separator

            self.filename_template_entry = QLineEdit()
            self.filename_template_entry.setPlaceholderText("%(uploader)s - %(title)s.%(ext)s") # Default
            self.filename_template_entry.setToolTip("Optional: Customize output filename. See yt-dlp docs for placeholders.")
            po_layout.addWidget(QLabel("Custom Filename Template (Optional):"))
            po_layout.addWidget(self.filename_template_entry)

            self.keep_original_checkbox = QCheckBox("Keep original file after conversion")
            self.keep_original_checkbox.setToolTip("Relevant if format conversion occurs (e.g., webm to mp4).")
            po_layout.addWidget(self.keep_original_checkbox)

            self.open_explorer_checkbox = QCheckBox("Open folder after download") # Moved here
            initial_checked_state = self._config.get("open_folder_after_download", True)
            self.open_explorer_checkbox.setChecked(bool(initial_checked_state))
            po_layout.addWidget(self.open_explorer_checkbox)


            po_layout.addStretch(1)
            options_layout.addWidget(playlist_output_group)

            # --- GroupBox 2: Metadata & Network ---
            metadata_network_group = QGroupBox("Metadata && Network Options")
            mn_layout = QVBoxLayout(metadata_network_group)
            mn_layout.setSpacing(8)

            self.embed_metadata_checkbox = QCheckBox("Embed general metadata")
            mn_layout.addWidget(self.embed_metadata_checkbox)

            self.embed_chapters_checkbox = QCheckBox("Embed chapters")
            mn_layout.addWidget(self.embed_chapters_checkbox)

            self.thumbnail_checkbox = QCheckBox("Embed thumbnail") # Kept separate for clarity
            mn_layout.addWidget(self.thumbnail_checkbox)

            self.write_infojson_checkbox = QCheckBox("Save metadata to .info.json file")
            mn_layout.addWidget(self.write_infojson_checkbox)

            mn_layout.addSpacing(10) # Separator (Subtitles)

            self.subtitles_checkbox = QCheckBox("Download subtitles (if available)") # Master switch
            mn_layout.addWidget(self.subtitles_checkbox)

            self.subtitle_langs_entry = QLineEdit()
            self.subtitle_langs_entry.setPlaceholderText("en,es") # Example
            self.subtitle_langs_entry.setToolTip("Comma-separated language codes (e.g., en,es,fr) or 'all'.")
            mn_layout.addWidget(QLabel("Subtitle Languages:"))
            mn_layout.addWidget(self.subtitle_langs_entry)

            self.embed_subs_checkbox = QCheckBox("Embed subtitles in video file")
            mn_layout.addWidget(self.embed_subs_checkbox)

            self.autosubs_checkbox = QCheckBox("Download automatic captions")
            mn_layout.addWidget(self.autosubs_checkbox)

            mn_layout.addSpacing(10) # Separator (Network)

            self.rate_limit_entry = QLineEdit()
            self.rate_limit_entry.setPlaceholderText("e.g., 500K, 1.5M (Optional)")
            self.rate_limit_entry.setToolTip("Limit download speed (e.g., 500K, 1.5M). Leave empty for no limit.")
            mn_layout.addWidget(QLabel("Rate Limit (Optional):"))
            mn_layout.addWidget(self.rate_limit_entry)

            # Cookie file handling
            cookie_layout = QHBoxLayout()
            self.cookie_browse_button = QPushButton("Use Cookie File")
            self.cookie_browse_button.setObjectName("cookieButton")
            self.cookie_browse_button.setToolTip("Select a cookies.txt file for accessing private content.")
            self.cookie_browse_button.clicked.connect(self._browse_cookie_file)
            self.cookie_path_label = QLabel("<i>None selected</i>") # Display selected path
            self.cookie_path_label.setWordWrap(True)
            self._cookie_file_path = None # Internal variable to store path
            cookie_layout.addWidget(self.cookie_browse_button)
            cookie_layout.addWidget(self.cookie_path_label, 1) # Allow label to stretch
            mn_layout.addLayout(cookie_layout)


            mn_layout.addStretch(1)
            options_layout.addWidget(metadata_network_group)

            # --- GroupBox 3: YouTube Specific ---
            youtube_group = QGroupBox("YouTube Options")
            yt_layout = QVBoxLayout(youtube_group)
            yt_layout.setSpacing(8)

            yt_layout.addWidget(QLabel("SponsorBlock:"))
            self.sponsorblock_combo = QComboBox()
            self.sponsorblock_combo.addItems(["None", "Skip Sponsor Segments", "Mark Sponsor Segments"])
            self.sponsorblock_combo.setToolTip("Automatically skip or mark sponsor sections in downloaded video (requires FFmpeg).")
            yt_layout.addWidget(self.sponsorblock_combo)

            yt_layout.addStretch(1)
            options_layout.addWidget(youtube_group) # Add YouTube group


            # Add the options layout (containing group boxes) to the main page layout
            main_page_layout.addLayout(options_layout)

            # --- Status Container (Unchanged) ---
            # ... (add status_container as before) ...
            self.status_container = QWidget()
            status_layout = QVBoxLayout(self.status_container); status_layout.setContentsMargins(0,0,0,0); status_layout.setSpacing(8); status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_layout.addWidget(self.progress_bar)
            button_label_layout = QHBoxLayout(); button_label_layout.setSpacing(10); button_label_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            button_label_layout.addWidget(self.loading_label); button_label_layout.addWidget(self.start_button); button_label_layout.addWidget(self.stop_button)
            status_layout.addLayout(button_label_layout)
            main_page_layout.addWidget(self.status_container)


            # --- Update Button Container (Unchanged) ---
            # ... (add update_button_container as before) ...
            self.update_button_container = QWidget()
            self.update_button_layout = QVBoxLayout(self.update_button_container); self.update_button_layout.setContentsMargins(0, 10, 0, 0); self.update_button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_page_layout.addWidget(self.update_button_container); self.update_button = None

            main_page_layout.addStretch(1)
            self._home_initialized = True
            self._update_quality_options_visibility() # Initial setup

        # --- Update states on showing the page (existing logic) ---
        if hasattr(self, 'open_explorer_checkbox'):
             current_config_state = self._config.get("open_folder_after_download", True)
             self.open_explorer_checkbox.setChecked(bool(current_config_state))
        self._update_quality_options_visibility()

        self.update_download_controls_visibility(is_downloading=(self.download_thread is not None and self.download_thread.isRunning()))
        self.pages_layout.setCurrentWidget(self.home_page_widget)
        if hasattr(self, 'home_button'): self.home_button.setChecked(True)

    @Slot()
    def _update_quality_options_visibility(self):
        """ Shows/hides video/audio quality options based on selected file type. """
        if not self._home_initialized:
            return # Don't run if widgets aren't created yet

        selected_format_key = self.dropdown_menu.currentText().lower()
        format_details = filetypes.get(selected_format_key, {})
        is_audio_only = format_details.get("audio", False)

        # Video quality only makes sense for non-audio-only formats
        self.video_quality_label.setVisible(not is_audio_only)
        self.video_quality_combo.setVisible(not is_audio_only)

        # Audio quality primarily applies to audio-only formats (for bitrate selection)
        # Or could be shown always, but we'll tie it to audio-only for now
        self.audio_quality_label.setVisible(is_audio_only)
        self.audio_quality_combo.setVisible(is_audio_only)

        # Subtitles only make sense for video formats
        self.subtitles_checkbox.setVisible(not is_audio_only)
        # Thumbnails could apply to both, but often associated with video
        self.thumbnail_checkbox.setVisible(not is_audio_only) # Keep visible only for video

    def show_settings(self):
        """ Creates (if needed) and shows the Settings page content. """
        self.current_page = "settings"
        if not self._settings_initialized:
            # Main layout for the settings page
            page_layout = QVBoxLayout(self.settings_page_widget)
            page_layout.setContentsMargins(0, 0, 0, 0) # Let scroll area handle margins

            # --- Scroll Area Setup ---
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setObjectName("settingsScrollArea")
            page_layout.addWidget(scroll_area)

            scroll_content = QWidget()
            scroll_content.setObjectName("settingsScrollContent")
            layout = QVBoxLayout(scroll_content) # Main layout inside scroll area
            layout.setContentsMargins(15, 15, 15, 15)
            layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            layout.setSpacing(20) # Space between group boxes
            scroll_area.setWidget(scroll_content)
            # --- End Scroll Area Setup ---

            config_data = self._config # Use the loaded config

            title = QLabel("Settings")
            title.setObjectName("pageTitle")
            layout.addWidget(title, 0, Qt.AlignmentFlag.AlignCenter)
            layout.addSpacing(10)


            # --- GroupBox 1: General ---
            general_group = QGroupBox("General Application")
            general_layout = QGridLayout(general_group)
            general_layout.setColumnStretch(1, 1)
            general_layout.setSpacing(10)

            # Theme (Existing)
            theme_label = QLabel("Theme:")
            current_theme = config_data.get("theme", DEFAULT_SETTINGS["theme"])
            self.theme_button_group = QButtonGroup(self); self.theme_button_group.setExclusive(True)
            theme_buttons_layout = QHBoxLayout(); theme_buttons_layout.setSpacing(8)
            themes = ["system", "light", "dark"]
            for theme in themes:
                button = QPushButton(theme.capitalize()); button.setObjectName("themeButton"); button.setCheckable(True)
                if theme == current_theme: button.setChecked(True)
                button.clicked.connect(partial(self.apply_stylesheet, theme))
                self.theme_button_group.addButton(button); theme_buttons_layout.addWidget(button)
            theme_buttons_layout.addStretch(1)
            general_layout.addWidget(theme_label, 0, 0, Qt.AlignmentFlag.AlignTop)
            general_layout.addLayout(theme_buttons_layout, 0, 1)

            # Check for Updates
            self.check_updates_checkbox = QCheckBox("Check for updates on startup")
            self.check_updates_checkbox.setChecked(config_data.get("check_for_updates_on_startup", DEFAULT_SETTINGS["check_for_updates_on_startup"]))
            self.check_updates_checkbox.setToolTip("Automatically check for new versions when the application starts.")
            general_layout.addWidget(self.check_updates_checkbox, 1, 0, 1, 2) # Span 2 columns

            # Clear Console
            self.clear_console_checkbox = QCheckBox("Clear console before each download")
            self.clear_console_checkbox.setChecked(config_data.get("clear_console_before_download", DEFAULT_SETTINGS["clear_console_before_download"]))
            self.clear_console_checkbox.setToolTip("Clears the text in the Console tab when a new download begins.")
            general_layout.addWidget(self.clear_console_checkbox, 2, 0, 1, 2)

            layout.addWidget(general_group)


            # --- GroupBox 2: Download Defaults ---
            download_group = QGroupBox("Download Defaults")
            download_layout = QGridLayout(download_group)
            download_layout.setColumnStretch(1, 1)
            download_layout.setSpacing(10)

            # Download Path (Existing)
            download_label = QLabel("Download Path:")
            default_dl_path = DEFAULT_SETTINGS["download_path"]
            self.filepath_entry = QLineEdit(config_data.get("download_path", default_dl_path))
            select_folder_button = QPushButton("Select"); select_folder_button.setObjectName("selectFolderButton"); select_folder_button.setToolTip("Choose default download folder")
            select_folder_button.clicked.connect(self.select_directory)
            download_layout.addWidget(download_label, 0, 0)
            download_layout.addWidget(self.filepath_entry, 0, 1)
            download_layout.addWidget(select_folder_button, 0, 2)

            # Open Folder After Download (Now a dedicated setting)
            self.open_folder_default_checkbox = QCheckBox("Open folder after download by default")
            self.open_folder_default_checkbox.setChecked(config_data.get("open_folder_after_download", DEFAULT_SETTINGS["open_folder_after_download"]))
            self.open_folder_default_checkbox.setToolTip("Sets the initial state of the 'Open folder' checkbox on the Home page.")
            download_layout.addWidget(self.open_folder_default_checkbox, 1, 0, 1, 3) # Span 3 columns

            # Keep Original File
            self.keep_original_default_checkbox = QCheckBox("Keep original file after conversion by default")
            self.keep_original_default_checkbox.setChecked(config_data.get("default_keep_original", DEFAULT_SETTINGS["default_keep_original"]))
            self.keep_original_default_checkbox.setToolTip("Sets the initial state of the 'Keep original' checkbox on the Home page.")
            download_layout.addWidget(self.keep_original_default_checkbox, 2, 0, 1, 3)

            layout.addWidget(download_group)


            # --- GroupBox 3: Metadata & Subtitle Defaults ---
            meta_sub_group = QGroupBox("Metadata && Subtitle Defaults")
            meta_sub_layout = QGridLayout(meta_sub_group)
            meta_sub_layout.setColumnStretch(1, 1)
            meta_sub_layout.setSpacing(10)

            self.embed_meta_default_checkbox = QCheckBox("Embed general metadata by default")
            self.embed_meta_default_checkbox.setChecked(config_data.get("default_embed_metadata", DEFAULT_SETTINGS["default_embed_metadata"]))
            meta_sub_layout.addWidget(self.embed_meta_default_checkbox, 0, 0)

            self.embed_chapters_default_checkbox = QCheckBox("Embed chapters by default")
            self.embed_chapters_default_checkbox.setChecked(config_data.get("default_embed_chapters", DEFAULT_SETTINGS["default_embed_chapters"]))
            meta_sub_layout.addWidget(self.embed_chapters_default_checkbox, 1, 0)

            self.embed_thumb_default_checkbox = QCheckBox("Embed thumbnail by default")
            self.embed_thumb_default_checkbox.setChecked(config_data.get("default_embed_thumbnail", DEFAULT_SETTINGS["default_embed_thumbnail"]))
            meta_sub_layout.addWidget(self.embed_thumb_default_checkbox, 2, 0)

            self.write_infojson_default_checkbox = QCheckBox("Save .info.json file by default")
            self.write_infojson_default_checkbox.setChecked(config_data.get("default_write_infojson", DEFAULT_SETTINGS["default_write_infojson"]))
            meta_sub_layout.addWidget(self.write_infojson_default_checkbox, 3, 0)

            meta_sub_layout.addWidget(QLabel("--- Subtitles ---"), 4, 0, 1, 2, Qt.AlignmentFlag.AlignCenter) # Separator

            self.download_subs_default_checkbox = QCheckBox("Download subtitles by default")
            self.download_subs_default_checkbox.setChecked(config_data.get("default_download_subtitles", DEFAULT_SETTINGS["default_download_subtitles"]))
            meta_sub_layout.addWidget(self.download_subs_default_checkbox, 5, 0)

            self.embed_subs_default_checkbox = QCheckBox("Embed subtitles by default")
            self.embed_subs_default_checkbox.setChecked(config_data.get("default_embed_subs", DEFAULT_SETTINGS["default_embed_subs"]))
            meta_sub_layout.addWidget(self.embed_subs_default_checkbox, 6, 0)

            self.autosubs_default_checkbox = QCheckBox("Download auto-captions by default")
            self.autosubs_default_checkbox.setChecked(config_data.get("default_autosubs", DEFAULT_SETTINGS["default_autosubs"]))
            meta_sub_layout.addWidget(self.autosubs_default_checkbox, 7, 0)

            sub_langs_label = QLabel("Default Subtitle Langs:")
            self.sub_langs_default_entry = QLineEdit(config_data.get("default_subtitle_langs", DEFAULT_SETTINGS["default_subtitle_langs"]))
            self.sub_langs_default_entry.setToolTip("Comma-separated language codes (e.g., en,es) used when downloading subtitles.")
            meta_sub_layout.addWidget(sub_langs_label, 8, 0)
            meta_sub_layout.addWidget(self.sub_langs_default_entry, 8, 1)

            layout.addWidget(meta_sub_group)

            # --- GroupBox 4: Network & YouTube Defaults ---
            net_yt_group = QGroupBox("Network && YouTube Defaults")
            net_yt_layout = QGridLayout(net_yt_group)
            net_yt_layout.setColumnStretch(1, 1)
            net_yt_layout.setSpacing(10)

            rate_limit_label = QLabel("Default Rate Limit:")
            self.rate_limit_default_entry = QLineEdit(config_data.get("default_rate_limit", DEFAULT_SETTINGS["default_rate_limit"]))
            self.rate_limit_default_entry.setPlaceholderText("e.g., 500K, 1.5M (Empty=None)")
            self.rate_limit_default_entry.setToolTip("Default download speed limit. Leave empty for no limit.")
            net_yt_layout.addWidget(rate_limit_label, 0, 0)
            net_yt_layout.addWidget(self.rate_limit_default_entry, 0, 1)

            sponsorblock_label = QLabel("Default SponsorBlock:")
            self.sponsorblock_default_combo = QComboBox()
            sb_options = ["None", "Skip", "Mark"] # Match worker logic if needed
            self.sponsorblock_default_combo.addItems(sb_options)
            current_sb = config_data.get("default_sponsorblock", DEFAULT_SETTINGS["default_sponsorblock"])
            sb_index = self.sponsorblock_default_combo.findText(current_sb, Qt.MatchFlag.MatchFixedString | Qt.MatchFlag.MatchCaseSensitive)
            if sb_index >= 0: self.sponsorblock_default_combo.setCurrentIndex(sb_index)
            self.sponsorblock_default_combo.setToolTip("Default action for SponsorBlock segments (requires FFmpeg for Skip/Mark).")
            net_yt_layout.addWidget(sponsorblock_label, 1, 0)
            net_yt_layout.addWidget(self.sponsorblock_default_combo, 1, 1)

            layout.addWidget(net_yt_group)

            # --- GroupBox 5: Advanced (FFmpeg/FFprobe Path) ---
            advanced_group = QGroupBox("Advanced")
            advanced_layout = QGridLayout(advanced_group)
            advanced_layout.setColumnStretch(1, 1)
            advanced_layout.setSpacing(10)

            ffmpeg_label = QLabel("FFmpeg Path Override:")
            self.ffmpeg_path_entry = QLineEdit(config_data.get("ffmpeg_path_override", DEFAULT_SETTINGS["ffmpeg_path_override"]))
            self.ffmpeg_path_entry.setPlaceholderText("Leave empty to use bundled/system FFmpeg")
            self.ffmpeg_path_entry.setToolTip("Optional: Specify the full path to the ffmpeg executable.")
            ffmpeg_browse_button = QPushButton("Browse")
            ffmpeg_browse_button.setObjectName("ffmpegBrowseButton")
            ffmpeg_browse_button.clicked.connect(lambda: self._browse_executable("ffmpeg"))
            advanced_layout.addWidget(ffmpeg_label, 0, 0)
            advanced_layout.addWidget(self.ffmpeg_path_entry, 0, 1)
            advanced_layout.addWidget(ffmpeg_browse_button, 0, 2)


            ffprobe_label = QLabel("FFprobe Path Override:")
            self.ffprobe_path_entry = QLineEdit(config_data.get("ffprobe_path_override", DEFAULT_SETTINGS["ffprobe_path_override"]))
            self.ffprobe_path_entry.setPlaceholderText("Leave empty to use bundled/system FFprobe")
            self.ffprobe_path_entry.setToolTip("Optional: Specify the full path to the ffprobe executable.")
            ffprobe_browse_button = QPushButton("Browse")
            ffprobe_browse_button.setObjectName("ffprobeBrowseButton")
            ffprobe_browse_button.clicked.connect(lambda: self._browse_executable("ffprobe"))
            advanced_layout.addWidget(ffprobe_label, 1, 0)
            advanced_layout.addWidget(self.ffprobe_path_entry, 1, 1)
            advanced_layout.addWidget(ffprobe_browse_button, 1, 2)

            layout.addWidget(advanced_group)


            # --- Buttons (Save/Reset) ---
            layout.addStretch(1) # Push buttons to bottom

            button_layout = QHBoxLayout(); button_layout.setSpacing(15); button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            save_button = QPushButton("Save Settings"); save_button.setObjectName("saveButton"); save_button.setToolTip("Save current settings")
            save_button.clicked.connect(self.save_and_apply_settings)
            reset_button = QPushButton("Reset to Default"); reset_button.setObjectName("resetButton"); reset_button.setToolTip("Reset all settings to defaults")
            reset_button.clicked.connect(self.reset_to_default)
            button_layout.addWidget(save_button); button_layout.addWidget(reset_button)
            layout.addLayout(button_layout) # Add to the main layout inside scroll area

            self._settings_initialized = True

        # --- End of initialization block ---

        # Update UI elements with current config values every time page is shown (in case config changed elsewhere)
        self._update_settings_ui_from_config()

        self.pages_layout.setCurrentWidget(self.settings_page_widget)
        if hasattr(self, 'settings_button'): self.settings_button.setChecked(True)

    def _update_settings_ui_from_config(self):
        """ Updates the settings page widgets with values from self._config """
        if not self._settings_initialized: return
        config_data = self._config

        # General
        current_theme = config_data.get("theme", DEFAULT_SETTINGS["theme"])
        for button in self.theme_button_group.buttons():
             if button.text().lower() == current_theme: button.setChecked(True); break
        self.check_updates_checkbox.setChecked(config_data.get("check_for_updates_on_startup", DEFAULT_SETTINGS["check_for_updates_on_startup"]))
        self.clear_console_checkbox.setChecked(config_data.get("clear_console_before_download", DEFAULT_SETTINGS["clear_console_before_download"]))

        # Download Defaults
        self.filepath_entry.setText(config_data.get("download_path", DEFAULT_SETTINGS["download_path"]))
        self.open_folder_default_checkbox.setChecked(config_data.get("open_folder_after_download", DEFAULT_SETTINGS["open_folder_after_download"]))
        self.keep_original_default_checkbox.setChecked(config_data.get("default_keep_original", DEFAULT_SETTINGS["default_keep_original"]))

        # Metadata & Subtitle Defaults
        self.embed_meta_default_checkbox.setChecked(config_data.get("default_embed_metadata", DEFAULT_SETTINGS["default_embed_metadata"]))
        self.embed_chapters_default_checkbox.setChecked(config_data.get("default_embed_chapters", DEFAULT_SETTINGS["default_embed_chapters"]))
        self.embed_thumb_default_checkbox.setChecked(config_data.get("default_embed_thumbnail", DEFAULT_SETTINGS["default_embed_thumbnail"]))
        self.write_infojson_default_checkbox.setChecked(config_data.get("default_write_infojson", DEFAULT_SETTINGS["default_write_infojson"]))
        self.download_subs_default_checkbox.setChecked(config_data.get("default_download_subtitles", DEFAULT_SETTINGS["default_download_subtitles"]))
        self.embed_subs_default_checkbox.setChecked(config_data.get("default_embed_subs", DEFAULT_SETTINGS["default_embed_subs"]))
        self.autosubs_default_checkbox.setChecked(config_data.get("default_autosubs", DEFAULT_SETTINGS["default_autosubs"]))
        self.sub_langs_default_entry.setText(config_data.get("default_subtitle_langs", DEFAULT_SETTINGS["default_subtitle_langs"]))

        # Network & YouTube Defaults
        self.rate_limit_default_entry.setText(config_data.get("default_rate_limit", DEFAULT_SETTINGS["default_rate_limit"]))
        current_sb = config_data.get("default_sponsorblock", DEFAULT_SETTINGS["default_sponsorblock"])
        sb_index = self.sponsorblock_default_combo.findText(current_sb, Qt.MatchFlag.MatchFixedString | Qt.MatchFlag.MatchCaseSensitive)
        if sb_index >= 0: self.sponsorblock_default_combo.setCurrentIndex(sb_index)

        # Advanced
        self.ffmpeg_path_entry.setText(config_data.get("ffmpeg_path_override", DEFAULT_SETTINGS["ffmpeg_path_override"]))
        self.ffprobe_path_entry.setText(config_data.get("ffprobe_path_override", DEFAULT_SETTINGS["ffprobe_path_override"]))

    @Slot()
    def _browse_executable(self, executable_type: str):
        """ Opens a file dialog to select an executable (ffmpeg/ffprobe). """
        target_entry = None
        if executable_type == "ffmpeg" and hasattr(self, "ffmpeg_path_entry"):
            target_entry = self.ffmpeg_path_entry
            title = "Select FFmpeg Executable"
        elif executable_type == "ffprobe" and hasattr(self, "ffprobe_path_entry"):
            target_entry = self.ffprobe_path_entry
            title = "Select FFprobe Executable"
        else:
            return # Should not happen

        current_path = target_entry.text()
        start_dir = os.path.dirname(current_path) if current_path and os.path.exists(os.path.dirname(current_path)) else os.path.expanduser("~")

        # Adjust filter based on OS
        if sys.platform == "win32":
            file_filter = "Executables (*.exe);;All files (*)"
        else:
            file_filter = "All files (*)" # Linux/macOS executables often have no extension

        file_path, _ = QFileDialog.getOpenFileName(self, title, start_dir, file_filter)

        if file_path:
            target_entry.setText(file_path)

    def _create_section(self, parent_layout, title_text, body_text):
        # Create a container frame for the card
        card_frame = QFrame()
        card_frame.setObjectName("cardFrame")

        # Optionally add a drop shadow effect
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(10)
        shadow_effect.setXOffset(0)
        shadow_effect.setYOffset(3)
        card_frame.setGraphicsEffect(shadow_effect)

        # Card layout
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(8)

        # Title
        title_label = QLabel(title_text)
        title_label.setObjectName("cardTitle")
        card_layout.addWidget(title_label)

        # Body
        body_label = QLabel(body_text)
        body_label.setObjectName("cardBody")
        body_label.setWordWrap(True)
        card_layout.addWidget(body_label)

        # Add the card to the parent layout
        parent_layout.addWidget(card_frame)

    def show_about(self):
        self.current_page = "about"
        if not self._about_initialized:
            layout = QVBoxLayout(self.about_page_widget)
            layout.setContentsMargins(0, 0, 0, 0)

            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setObjectName("aboutScrollArea")
            layout.addWidget(scroll_area)

            scroll_content = QWidget()
            scroll_content.setObjectName("aboutScrollContent")  # Set a unique name for styling
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_layout.setContentsMargins(20, 20, 20, 20)
            scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            scroll_layout.setSpacing(16)

            scroll_area.setWidget(scroll_content)

            # Page Title
            title = QLabel("About ForgeYT")
            title.setObjectName("pageTitle")
            scroll_layout.addWidget(title, 0, Qt.AlignmentFlag.AlignCenter)

            # --- Updated Card Content ---
            self._create_section(scroll_layout, "Origin:",
                                 "ForgeYT was created because many popular YouTube download websites were blocked at school or seemed untrustworthy. There was a need for a simple, reliable tool.")
            self._create_section(scroll_layout, "Initial Release:",
                                 "The first version launched in February 2023 as a Node.js command-line tool. It has since evolved into the Python GUI application you see today.")
            self._create_section(scroll_layout, "Challenges:",
                                 "Moving from Node.js to Python and integrating `yt-dlp` presented some hurdles, especially making the different technologies work together smoothly.")
            self._create_section(scroll_layout, "Purpose & Usage:",
                                 "Originally built for school use, ForgeYT is a versatile tool for converting YouTube videos easily, wherever you need it.")
            self._create_section(scroll_layout, "Acknowledgments:",
                                 "Special thanks to Mr. Z and DJ Stomp for their valuable input. Also, a shout-out to the helpful Python Discord community.")

            # --- Updated "What's New?" Section ---
            self._create_section(scroll_layout, "What's New (PySide6 Rewrite)?",
                                 "- Complete UI rewrite using PySide6 (Qt) for a modern look and feel.\n"
                                 "- Expanded Download Options: Separate Quality settings, Playlist ranges, Subtitle handling, Metadata embedding, Rate limiting, Cookie support, SponsorBlock integration.\n"
                                 "- Revamped Settings Page: Set defaults for new options, configure FFmpeg paths.\n"
                                 "- Interactive Console: Run shell commands directly within the app.\n"
                                 "- Improved Theming: Better Light/Dark/System theme support.\n"
                                 "- SVG Icons: Scalable icons for a sharper appearance.\n"
                                 "- Cross-Platform Improvements: Better support for Linux and macOS.\n"
                                 "- Codebase Refactor: Modular design using Qt signals/slots for better performance and maintainability."
                                 )
            # --- Removed "Future" Section ---
            # The self._create_section call for "Future" has been deleted.

            version_label = QLabel(f"Current Version: {CURRENT_VERSION}")
            version_label.setObjectName("versionLabel")
            version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll_layout.addWidget(version_label) # Added sequentially
            scroll_layout.addStretch(1)

            self._about_initialized = True

        self.pages_layout.setCurrentWidget(self.about_page_widget)
        if hasattr(self, 'about_button'):
            self.about_button.setChecked(True)


    def show_console(self):
        """ Creates (if needed) and shows the Console Output page. """
        self.current_page = "console"
        if not self._console_initialized:
            layout = QVBoxLayout(self.console_page_widget); layout.setSpacing(10)
            title = QLabel("Console Output"); title.setObjectName("pageTitle")
            layout.addWidget(title, 0, Qt.AlignmentFlag.AlignCenter)
            self.console_output = QTextEdit(); self.console_output.setReadOnly(True); self.console_output.setObjectName("consoleOutput")
            layout.addWidget(self.console_output, 1)
            self._console_initialized = True
            # --- Command Line Section ---
            self.command_input = QLineEdit()
            self.command_input.setPlaceholderText("Enter PowerShell command...")
            self.command_input.returnPressed.connect(self._run_command_from_input)

            self.run_command_button = QPushButton("Run")
            self.run_command_button.clicked.connect(self._run_command_from_input)

            cmd_input_layout = QHBoxLayout()
            cmd_input_layout.addWidget(self.command_input)
            cmd_input_layout.addWidget(self.run_command_button)

            layout.addLayout(cmd_input_layout)


        if hasattr(self, 'console_output'): self.console_output.ensureCursorVisible()
        self.pages_layout.setCurrentWidget(self.console_page_widget)
        if hasattr(self, 'console_button'): self.console_button.setChecked(True)



    @Slot()
    def _run_command_from_input(self):
        if not hasattr(self, 'command_input') or not self.command_input.text().strip():
            return

        cmd = self.command_input.text().strip()
        self.command_input.clear()
        self._append_console_output(f"> {cmd}")
        threading.Thread(target=self._run_pwsh_command, args=(cmd,), daemon=True).start()

    def _run_pwsh_command(self, cmd: str):
        try:
            # Use pwsh for PowerShell Core or powershell for legacy
            shell = "pwsh" if sys.platform != "win32" else "powershell"
            process = subprocess.Popen([shell, "-Command", cmd],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       text=True)
            stdout, stderr = process.communicate()

            if stdout:
                self._append_console_output(stdout.strip())
            if stderr:
                self._append_console_output(stderr.strip())
        except Exception as e:
            self._append_console_output(f"Error: {e}")

    def _append_console_output(self, text: str):
        if hasattr(self, 'console_output') and self._console_initialized:
            self.console_output.append(text)
            self.console_output.ensureCursorVisible()


    # --- Action Methods ---

    def show_custom_messagebox(self, title: str, message: str, icon=QMessageBox.Icon.Information):
        """ Wrapper to use CustomMessageBox or fall back to standard QMessageBox. """
        try:
            # Use imported CustomMessageBox
            CustomMessageBox.show_message(self, title, message, self.buttoncolor, self.buttoncolor_hover, icon=icon)
        except NameError: # Fallback if CustomMessageBox wasn't imported
            print("CustomMessageBox not found, using standard QMessageBox.")
            if icon == QMessageBox.Icon.Warning: QMessageBox.warning(self, title, message)
            elif icon == QMessageBox.Icon.Critical: QMessageBox.critical(self, title, message)
            else: QMessageBox.information(self, title, message)
        except Exception as e: # Catch other errors
            print(f"Error showing message box: {e}. Using standard QMessageBox as fallback.")
            QMessageBox.information(self, title, message) # Safest fallback

    @Slot()
    def start_downloading(self):
        """ Validates input and initiates the download process with ALL selected options. """
        # Check if essential widgets exist (expand this list as needed)
        essential_widgets = [
            'profile_entry', 'dropdown_menu', 'video_quality_combo', 'audio_quality_combo',
            'playlist_range_entry', 'playlist_reverse_checkbox', 'filename_template_entry',
            'keep_original_checkbox', 'open_explorer_checkbox', 'embed_metadata_checkbox',
            'embed_chapters_checkbox', 'thumbnail_checkbox', 'write_infojson_checkbox',
            'subtitles_checkbox', 'subtitle_langs_entry', 'embed_subs_checkbox',
            'autosubs_checkbox', 'rate_limit_entry', 'sponsorblock_combo',
            'cookie_browse_button' # Check button exists, path is handled separately
        ]
        if not self._home_initialized or not all(hasattr(self, w) for w in essential_widgets):
            self.show_custom_messagebox("Error", "UI elements are not ready.", QMessageBox.Icon.Warning); return

        url = self.profile_entry.text().strip()
        filetype_key = self.dropdown_menu.currentText().lower()
        self._last_download_path = None; self._error_already_handled = False
        open_explorer = self.open_explorer_checkbox.isChecked()

        # --- Get Options (Existing & New) ---
        video_quality = self.video_quality_combo.currentText()
        audio_quality = self.audio_quality_combo.currentText()
        embed_thumbnail = self.thumbnail_checkbox.isChecked() # Keep this one
        # Playlist
        playlist_range = self.playlist_range_entry.text().strip()
        playlist_reverse = self.playlist_reverse_checkbox.isChecked()
        # Output
        filename_template = self.filename_template_entry.text().strip() or None # Use None if empty
        keep_original = self.keep_original_checkbox.isChecked()
        # Metadata
        embed_metadata = self.embed_metadata_checkbox.isChecked()
        embed_chapters = self.embed_chapters_checkbox.isChecked()
        write_infojson = self.write_infojson_checkbox.isChecked()
        # Subtitles
        download_subtitles = self.subtitles_checkbox.isChecked() # Master switch
        subtitle_langs = self.subtitle_langs_entry.text().strip() or 'en' # Default to 'en' if empty
        embed_subs = self.embed_subs_checkbox.isChecked()
        autosubs = self.autosubs_checkbox.isChecked()
        # Network
        rate_limit = self.rate_limit_entry.text().strip() or None
        cookie_file = self._cookie_file_path # Get path stored by the browser slot
        # YouTube Specific
        sponsorblock_choice = self.sponsorblock_combo.currentText()


        # --- Basic Validation (existing) ---
        if not url: self.show_custom_messagebox("Error", "Please enter URL.", QMessageBox.Icon.Warning); return
        # ... (rest of URL and thread running validation) ...
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
             self.show_custom_messagebox("Error", "Invalid URL format.", QMessageBox.Icon.Warning); return
        if self.download_thread and self.download_thread.isRunning():
             self.show_custom_messagebox("Info", "Download already in progress.", QMessageBox.Icon.Information); return


        # --- Setup Thread & Worker ---
        if hasattr(self, 'console_output'): self.console_output.clear()
        self.update_download_controls_visibility(is_downloading=True)

        self.download_thread = QThread(self)
        # Pass ALL options to the worker
        self.download_worker = DownloadWorker(
            url=url,
            filetype=filetype_key,
            open_explorer_var=open_explorer,
            # Basic Quality/Format
            video_quality=video_quality,
            audio_quality=audio_quality,
            embed_thumbnail=embed_thumbnail,
            # Playlist
            playlist_range=playlist_range,
            playlist_reverse=playlist_reverse,
            # Output
            filename_template=filename_template,
            keep_original=keep_original,
            # Metadata
            embed_metadata=embed_metadata,
            embed_chapters=embed_chapters,
            write_infojson=write_infojson,
            # Subtitles
            download_subtitles=download_subtitles,
            subtitle_langs=subtitle_langs,
            embed_subs=embed_subs,
            autosubs=autosubs,
            # Network
            rate_limit=rate_limit,
            cookie_file=cookie_file,
            # YouTube
            sponsorblock_choice=sponsorblock_choice
        )
        self.download_worker.moveToThread(self.download_thread)

        # --- Connect Signals & Start (existing logic) ---
        # ... (connect signals, start thread) ...
        self.download_worker.download_complete.connect(self.on_download_complete)
        self.download_worker.progress_update.connect(self.update_console_output)
        self.download_worker.error.connect(self.on_download_error)
        self.download_thread.started.connect(self.download_worker.run)

        self.download_worker.download_complete.connect(self.download_thread.quit, Qt.ConnectionType.QueuedConnection)
        self.download_worker.error.connect(self.download_thread.quit, Qt.ConnectionType.QueuedConnection)
        self.download_thread.finished.connect(self.download_worker.deleteLater)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        self.download_thread.finished.connect(self._cleanup_download_thread_references)

        self.download_thread.start()


    @Slot()
    def _browse_cookie_file(self):
        """ Opens a file dialog to select a cookie file. """
        # Use user's home directory or last known path as starting point
        start_dir = os.path.expanduser("~")
        if self._cookie_file_path and os.path.exists(os.path.dirname(self._cookie_file_path)):
            start_dir = os.path.dirname(self._cookie_file_path)

        file_path, _ = QFileDialog.getOpenFileName(self, "Select Cookie File", start_dir, "Text files (*.txt);;All files (*)")
        if file_path:
            self._cookie_file_path = file_path
            # Display filename or truncated path in the label
            display_text = os.path.basename(file_path)
            self.cookie_path_label.setText(f"<i>{display_text}</i>")
            self.cookie_path_label.setToolTip(file_path) # Show full path on hover
        # Optional: Add a button/action to clear the selection
        # else:
        #     self._cookie_file_path = None
        #     self.cookie_path_label.setText("<i>None selected</i>")
        #     self.cookie_path_label.setToolTip("")

    @Slot()
    def stop_downloading(self):
        """ Requests the download worker to stop and updates UI immediately. """
        print("Stop button clicked.")
        if self.download_worker and self.download_thread and self.download_thread.isRunning():
            print("Requesting worker stop...")
            if hasattr(self, 'stop_button'): self.stop_button.setEnabled(False); self.stop_button.setToolTip("Stopping...")
            if hasattr(self, 'loading_label'): self.loading_label.setText("Stopping download..."); self.loading_label.show()
            if hasattr(self, 'progress_bar') and hasattr(self.progress_bar, 'setFormat'): self.progress_bar.setFormat("Stopping...")
            self.download_worker.request_stop() # Use method on imported worker instance
        else:
            print("No active download to stop.")

    def update_download_controls_visibility(self, is_downloading: bool = False):
        """ Shows/Hides Start, Stop, Loading label, and Progress bar. """
        if not self._home_initialized or not hasattr(self, 'start_button'): return

        if is_downloading:
            self.start_button.hide(); self.loading_label.setText("Processing..."); self.loading_label.show()
            self.stop_button.setEnabled(True); self.stop_button.setToolTip("Stop Download"); self.stop_button.show()
            self.progress_bar.setValue(0); self.progress_bar.setFormat("%p%"); self.progress_bar.show()
        else:
            self.start_button.show(); self.loading_label.hide(); self.stop_button.hide(); self.progress_bar.hide()
            self.progress_bar.setValue(0)
        self.update_icons()


    # --- Slots for Worker Signals ---

    @Slot(str)
    def update_console_output(self, text: str):
        """ Appends text to console, handles progress updates. """

        # --- 1. Update Progress Bar (Always attempt if progress_bar exists) ---
        # Use hasattr to ensure the progress bar widget has been created
        if hasattr(self, 'progress_bar'):
            match = self.progress_regex.search(text)
            if match:
                try:
                    percent_str = match.group(1).replace('%', '').strip() # Group 1 has "xx.x%"
                    percent = float(percent_str)
                    # Clamp value between 0 and 100 just in case
                    percent_int = max(0, min(100, int(percent)))
                    self.progress_bar.setValue(percent_int)
                    # Update format only if parsing succeeded, keep %p% otherwise
                    if hasattr(self.progress_bar, 'setFormat'):
                         self.progress_bar.setFormat("%p%")

                except (ValueError, TypeError, IndexError) as e:
                    # Print more detailed error if parsing fails
                    print(f"Warning: Could not parse progress percentage from '{match.group(1)}'. Raw text: '{text}'. Error: {e}")
                    # Set progress bar to show text indicating issue
                    if hasattr(self.progress_bar, 'setFormat'):
                         self.progress_bar.setFormat("Processing...")
            # Optional: If the line is NOT a progress line, you might want to
            # ensure the format is reset to %p% if it was previously changed
            # else:
            #     if hasattr(self.progress_bar, 'setFormat'):
            #         self.progress_bar.setFormat("%p%")


        # --- 2. Update Console Output (Only if console is initialized) ---
        # Use the _console_initialized flag for a more robust check
        if hasattr(self, 'console_output') and self._console_initialized:
            cursor = self.console_output.textCursor()
            if '\r' in text:
                # Move to the beginning of the last line/block
                cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                 # Select to the end of the block
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText() # Remove the previous line content
                # Insert the new cleaned text (without \r and trailing newline)
                processed_text = text.replace('\r', '').rstrip('\n')
                cursor.insertText(processed_text)
                # No automatic newline for carriage return lines
            else:
                # Just append lines that don't have carriage returns
                self.console_output.append(text.rstrip('\n'))

            # Ensure the latest output is visible
            self.console_output.ensureCursorVisible()

    @Slot(bool, str)
    def on_download_complete(self, success: bool, message_or_path: str):
        """ Handles the download_complete signal from the worker. """
        print(f"Download complete signal: Success={success}, Msg='{message_or_path}'")
        self.cleanup_after_thread() # Reset UI first

        if success:
            self._last_download_path = message_or_path
            base_name = os.path.basename(message_or_path) if message_or_path else "Unknown File"
            self.show_custom_messagebox("Success", f"Download finished!\nFile: {base_name}", QMessageBox.Icon.Information)

            # Open explorer logic (needs worker ref)
            should_open_explorer = False
            if self.download_worker: # Check if worker reference still exists
                 should_open_explorer = self.download_worker.open_explorer_var

            if should_open_explorer and self._last_download_path:
                self._open_file_explorer(self._last_download_path)
        else: # Failure or Cancellation
            if not self._error_already_handled: # Show message only if error signal didn't fire first
                if "cancelled" in message_or_path.lower():
                    self.show_custom_messagebox("Cancelled", message_or_path, QMessageBox.Icon.Warning)
                else:
                    self.show_custom_messagebox("Failed", f"Download failed.\nReason: {message_or_path}", QMessageBox.Icon.Warning)
            else:
                print(f"Completion(Fail) signal, error already handled: {message_or_path}")

    @Slot(str)
    def on_download_error(self, error_message: str):
        """ Handles errors emitted by the download worker's error signal. """
        print(f"Download error signal: {error_message}")
        self.cleanup_after_thread() # Reset UI
        self.show_custom_messagebox("Download Error", error_message, QMessageBox.Icon.Critical)
        self._error_already_handled = True # Prevent duplicate message

    def cleanup_after_thread(self):
        """ Resets UI elements after download finishes/fails/stops. """
        print("Running cleanup_after_thread...")
        self.update_download_controls_visibility(is_downloading=False)
        # Optional: Clear input/dropdown here if desired

    @Slot()
    def _cleanup_download_thread_references(self):
        """ Slot to nullify thread/worker references after thread finishes. """
        self.download_thread = None
        self.download_worker = None
        self._error_already_handled = False


    # --- Settings Actions ---

    @Slot()
    def select_directory(self):
        """ Opens a dialog to select the download directory. """
        current_path = ""
        if self._settings_initialized and hasattr(self, 'filepath_entry'):
            current_path = self.filepath_entry.text()
        else: # Fallback to config
            current_path = self._config.get("download_path", DEFAULT_SETTINGS.get("download_path", os.path.expanduser("~")))

        selected_dir = QFileDialog.getExistingDirectory(self, "Select Download Folder", current_path)

        if selected_dir and self._settings_initialized and hasattr(self, 'filepath_entry'):
            self.filepath_entry.setText(selected_dir)

    @Slot()
    def save_and_apply_settings(self):
        """ Saves current settings from UI to the config file and internal state. """
        if not self._settings_initialized: # Simplified check
            self.show_custom_messagebox("Error", "Settings UI not ready.", QMessageBox.Icon.Warning); return

        try:
            # --- Retrieve values from ALL settings widgets ---
            theme_button = self.theme_button_group.checkedButton()
            if not theme_button: self.show_custom_messagebox("Error", "No theme selected.", QMessageBox.Icon.Warning); return
            theme = theme_button.text().lower()

            check_updates = self.check_updates_checkbox.isChecked()
            clear_console = self.clear_console_checkbox.isChecked()

            filepath = self.filepath_entry.text().strip()
            open_folder_default = self.open_folder_default_checkbox.isChecked()
            keep_original_default = self.keep_original_default_checkbox.isChecked()

            embed_meta_default = self.embed_meta_default_checkbox.isChecked()
            embed_chapters_default = self.embed_chapters_default_checkbox.isChecked()
            embed_thumb_default = self.embed_thumb_default_checkbox.isChecked()
            write_infojson_default = self.write_infojson_default_checkbox.isChecked()
            download_subs_default = self.download_subs_default_checkbox.isChecked()
            embed_subs_default = self.embed_subs_default_checkbox.isChecked()
            autosubs_default = self.autosubs_default_checkbox.isChecked()
            sub_langs_default = self.sub_langs_default_entry.text().strip()

            rate_limit_default = self.rate_limit_default_entry.text().strip()
            sponsorblock_default = self.sponsorblock_default_combo.currentText()

            ffmpeg_path = self.ffmpeg_path_entry.text().strip()
            ffprobe_path = self.ffprobe_path_entry.text().strip()

            # --- Validation ---
            if not filepath: self.show_custom_messagebox("Error", "Download path required.", QMessageBox.Icon.Warning); return

            # Validate Download Path
            try:
                abs_filepath = os.path.abspath(os.path.expanduser(filepath))
                if not os.path.isdir(abs_filepath): os.makedirs(abs_filepath, exist_ok=True)
                if not os.access(abs_filepath, os.W_OK | os.X_OK): raise OSError(f"Directory not writable/accessible: {abs_filepath}")
            except OSError as e: self.show_custom_messagebox("Error", f"Invalid Download Path:\n'{filepath}'\nReason: {e}", QMessageBox.Icon.Warning); return
            except Exception as e: self.show_custom_messagebox("Error", f"Path validation error: {e}", QMessageBox.Icon.Warning); return

            # Optional: Validate FFmpeg/FFprobe paths if provided (check if file exists and is executable)
            if ffmpeg_path and (not os.path.isfile(ffmpeg_path) or not os.access(ffmpeg_path, os.X_OK)):
                 self.show_custom_messagebox("Warning", f"FFmpeg path override is set, but file not found or not executable:\n{ffmpeg_path}", QMessageBox.Icon.Warning)
                 # Decide if this should prevent saving or just be a warning. Warning is usually better.

            if ffprobe_path and (not os.path.isfile(ffprobe_path) or not os.access(ffprobe_path, os.X_OK)):
                 self.show_custom_messagebox("Warning", f"FFprobe path override is set, but file not found or not executable:\n{ffprobe_path}", QMessageBox.Icon.Warning)


            # --- Update internal config ---
            self._config["theme"] = theme
            self._config["check_for_updates_on_startup"] = check_updates
            self._config["clear_console_before_download"] = clear_console

            self._config["download_path"] = abs_filepath # Save absolute path
            self._config["open_folder_after_download"] = open_folder_default
            self._config["default_keep_original"] = keep_original_default

            self._config["default_embed_metadata"] = embed_meta_default
            self._config["default_embed_chapters"] = embed_chapters_default
            self._config["default_embed_thumbnail"] = embed_thumb_default
            self._config["default_write_infojson"] = write_infojson_default
            self._config["default_download_subtitles"] = download_subs_default
            self._config["default_embed_subs"] = embed_subs_default
            self._config["default_autosubs"] = autosubs_default
            self._config["default_subtitle_langs"] = sub_langs_default

            self._config["default_rate_limit"] = rate_limit_default
            self._config["default_sponsorblock"] = sponsorblock_default

            self._config["ffmpeg_path_override"] = ffmpeg_path
            self._config["ffprobe_path_override"] = ffprobe_path

            # --- Write to file ---
            try:
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, indent=4)
                self.show_custom_messagebox("Success", "Settings saved!")
                # Re-apply theme immediately if changed
                self.apply_stylesheet(theme)
                # Update the home page checkboxes to reflect new defaults *if* home page is initialized
                self._initialize_home_page_controls_from_config()

            except IOError as e:
                print(f"Error writing config file: {traceback.format_exc()}")
                self.show_custom_messagebox("Error", f"Failed to write settings file:\n{e}", QMessageBox.Icon.Critical)

        except Exception as e:
            print(f"Error saving settings: {traceback.format_exc()}")
            self.show_custom_messagebox("Error", f"Failed to save settings: {e}", QMessageBox.Icon.Critical)

    @Slot()
    def reset_to_default(self):
        """ Resets UI elements and config file to default settings. """
        if not self._settings_initialized:
            self.show_custom_messagebox("Error", "Settings UI not ready.", QMessageBox.Icon.Warning); return

        reply = QMessageBox.question(self, "Confirm Reset", "Reset all settings to defaults?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._config = DEFAULT_SETTINGS.copy() # Reset internal config

                # Save defaults to file
                try:
                    with open(config_file, "w", encoding="utf-8") as f:
                        json.dump(self._config, f, indent=4)
                except IOError as e:
                    print(f"Error writing config file during reset: {traceback.format_exc()}")
                    self.show_custom_messagebox("Error", f"Failed to write defaults file:\n{e}", QMessageBox.Icon.Critical)
                    return # Abort if cannot save

                # Update UI on settings page
                self._update_settings_ui_from_config() # Use the helper function

                # Update Home page UI if initialized
                self._initialize_home_page_controls_from_config()

                # Apply default theme style
                self.apply_stylesheet(self._config["theme"])
                self.show_custom_messagebox("Success", "Settings reset to default.")

            except Exception as e:
                print(f"Error resetting settings: {traceback.format_exc()}")
                self.show_custom_messagebox("Error", f"Failed to reset settings: {e}", QMessageBox.Icon.Critical)


    def _initialize_home_page_controls_from_config(self):
        """Updates home page controls with the default settings from the config."""
        if not self._home_initialized:
            return
        # Update default checkbox states and entry fields
        self.open_explorer_checkbox.setChecked(bool(self._config.get("open_folder_after_download", True)))
        self.keep_original_checkbox.setChecked(bool(self._config.get("default_keep_original", False)))
        self.embed_metadata_checkbox.setChecked(bool(self._config.get("default_embed_metadata", False)))
        self.embed_chapters_checkbox.setChecked(bool(self._config.get("default_embed_chapters", False)))
        self.thumbnail_checkbox.setChecked(bool(self._config.get("default_embed_thumbnail", False)))
        self.write_infojson_checkbox.setChecked(bool(self._config.get("default_write_infojson", False)))
        self.subtitles_checkbox.setChecked(bool(self._config.get("default_download_subtitles", False)))
        self.embed_subs_checkbox.setChecked(bool(self._config.get("default_embed_subs", False)))
        self.autosubs_checkbox.setChecked(bool(self._config.get("default_autosubs", False)))
        self.subtitle_langs_entry.setText(self._config.get("default_subtitle_langs", "en"))
        self.rate_limit_entry.setText(self._config.get("default_rate_limit", ""))
        current_sb = self._config.get("default_sponsorblock", "None")
        sb_index = self.sponsorblock_combo.findText(current_sb, Qt.MatchFlag.MatchFixedString | Qt.MatchFlag.MatchCaseSensitive)
        if sb_index >= 0:
            self.sponsorblock_combo.setCurrentIndex(sb_index)


    # --- Update Check Actions ---

    @Slot()
    def start_update_check(self):
        """ Initiates the asynchronous update check. """
        if self.update_thread and self.update_thread.isRunning(): print("Update check running."); return
        self._clear_update_button() # Clear previous button

        print("Starting async update check...")
        self.update_thread = QThread(self)
        self.update_worker = UpdateCheckWorker() # Use imported class
        self.update_worker.moveToThread(self.update_thread)

        # Connect signals
        self.update_worker.update_available.connect(self._show_update_button)
        self.update_worker.check_error.connect(self._handle_update_error)
        self.update_worker.check_finished.connect(self.update_thread.quit)
        self.update_thread.started.connect(self.update_worker.run)
        self.update_thread.finished.connect(self.update_worker.deleteLater)
        self.update_thread.finished.connect(self.update_thread.deleteLater)
        self.update_thread.finished.connect(self._cleanup_update_check_thread_references)

        self.update_thread.start()

    def _clear_update_button(self):
        """ Removes the update button widget. """
        if hasattr(self, 'update_button') and self.update_button is not None:
            if hasattr(self, 'update_button_layout') and self.update_button_layout is not None:
                 self.update_button_layout.removeWidget(self.update_button)
            self.update_button.deleteLater()
            self.update_button = None

    @Slot(str)
    def _show_update_button(self, latest_version: str):
        """ Creates and displays the 'New version available' button. """
        if not hasattr(self, 'update_button_container') or not hasattr(self, 'update_button_layout'):
             print("Error: Update button container not ready."); return
        self._clear_update_button()

        print(f"Update available: {latest_version}")
        self.update_button = QPushButton(f" New version available! ({latest_version}) ")
        self.update_button.setObjectName("updateButton")
        self.update_button.setToolTip("Click to go to download page")
        if update_icon := self.get_icon("update"): self.update_button.setIcon(update_icon)
        self.update_button.clicked.connect(self._open_releases_page)
        self.update_button_layout.addWidget(self.update_button) # Add to specific container

    @Slot(str)
    def _handle_update_error(self, error_message: str):
        """ Logs errors from the update check worker. """
        print(f"Update Check Error: {error_message}")

    @Slot()
    def _cleanup_update_check_thread_references(self):
        """ Slot to nullify update thread/worker references. """
        print("Nullifying update check thread/worker references.")
        self.update_thread = None
        self.update_worker = None

    @Slot()
    def _open_releases_page(self):
        """ Opens the GitHub releases page in the default web browser. """
        releases_url = "https://github.com/ForgedCore8/forgeyt/releases/latest"
        try:
            print(f"Opening URL: {releases_url}")
            webopen(releases_url)
        except Exception as e:
            print(f"Error opening web browser: {e}")
            self.show_custom_messagebox("Error", f"Could not open releases page:\n{releases_url}\nReason: {e}", QMessageBox.Icon.Warning)


    # --- Helper for Cross-Platform Explorer ---
    def _open_file_explorer(self, file_path: str):
        """ Opens the file explorer to show the specified file or its directory. """
        try:
            if not isinstance(file_path, str) or not file_path: raise ValueError("Invalid path")
            normalized_path = os.path.normpath(file_path)
            directory = os.path.dirname(normalized_path)
            if not os.path.isdir(directory):
                 self.show_custom_messagebox("Error", f"Directory not found:\n{directory}", QMessageBox.Icon.Warning); return
            file_exists = os.path.isfile(normalized_path)
            print(f"Opening explorer. Path: '{normalized_path}', Dir: '{directory}'")

            if sys.platform == "win32":
                if file_exists: subprocess.run(['explorer', f'/select,"{normalized_path}"'], check=True)
                else: os.startfile(directory) # Fallback to dir
            elif sys.platform == "darwin":
                if file_exists: subprocess.run(['open', '-R', normalized_path], check=True)
                else: subprocess.run(['open', directory], check=True) # Fallback to dir
            else: # Linux/Unix
                subprocess.run(['xdg-open', directory], check=True) # Open dir
                if file_exists: print("(On Linux, opened directory. File selection depends on manager.)")

        except FileNotFoundError: self.show_custom_messagebox("Error", f"Cannot find explorer command for {sys.platform}.", QMessageBox.Icon.Warning)
        except (subprocess.CalledProcessError, ValueError, OSError) as e: self.show_custom_messagebox("Error", f"Failed to open explorer:\n{e}", QMessageBox.Icon.Warning)
        except Exception as e: self.show_custom_messagebox("Error", f"Unexpected error opening folder:\n{e}", QMessageBox.Icon.Warning)


    # --- Event Handling ---
    def closeEvent(self, event: QEvent):
        """ Handles the window close event, ensuring threads are stopped gracefully. """
        print("Close event triggered.")
        download_stopped_ok, update_stopped_ok = True, True

        # Stop Download Thread
        if self.download_thread and self.download_thread.isRunning():
            reply = QMessageBox.question(self, "Confirm Exit", "Download in progress. Exit anyway?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                print("Close cancelled by user."); event.ignore(); return
            else:
                print("Stopping download thread...")
                if self.download_worker: self.download_worker.request_stop()
                if not self.download_thread.wait(1500): # Wait 1.5s
                    print("Warning: Download thread didn't stop gracefully. Terminating."); self.download_thread.terminate(); self.download_thread.wait()
                    download_stopped_ok = False

        # Stop Update Check Thread
        if self.update_thread and self.update_thread.isRunning():
            print("Stopping update check thread...")
            self.update_thread.quit()
            if not self.update_thread.wait(500): # Wait 0.5s
                print("Warning: Update thread didn't stop gracefully. Terminating."); self.update_thread.terminate(); self.update_thread.wait()
                update_stopped_ok = False

        if download_stopped_ok and update_stopped_ok: print("Proceeding with clean close.")
        else: print("Proceeding with close after potential thread termination.")
        event.accept()